"""Tests for L2-06 ControlLoop central scheduling state machine (deploy_053).

Covers A4 / B3-B8 / C3 / C7 / C13-C19 / C23-C26:
  - non-blocking tick, at most one outstanding request
  - request/result correlation (success/error terminate; unknown/stale id latch)
  - active/pending/cursor/horizon/continue/age determinable by injected clock
  - candidate/previous/hold deep-copy, original source age not refreshed
  - one safety call per candidate, at-most-one publish, no forged SafetyResult
  - six PublishOutcome fail-closed reducer + PUBLISH_RESULT_INVARIANT echo
  - REJECTED/BLOCKED one-time deferred reason; PARTIAL/FAILED output-fault latch
  - safe-stop recoverable no-output
  - runtime_status single-writer priority + shutdown convergence

Uses a real SafetyGuard, a FakePublisher, fake observation reader, and an
injected monotonic time per tick (dry-run-only, no ROS / real policy).
"""

from __future__ import annotations

import pytest

from model_deploy.act.config.schema import SafetyConfig
from model_deploy.act.runtime.control_loop import (
    ControlLoop,
    ControlLoopConfig,
    FallbackReason,
    is_action_chunk_usable,
    select_candidate,
    select_fallback,
)
from model_deploy.act.runtime.inference_channel import (
    InferenceRequest,
    InferenceResult,
    LatestQueue,
)
from model_deploy.act.runtime.runtime_metrics import RuntimeMetrics
from model_deploy.act.service.safety_guard import SafetyGuard
from model_deploy.act.tests.runtime.test_inference_channel import (
    _make_chunk,
    _make_snapshot,
)
from model_deploy.act.types.action_chunk import ActionChunk
from model_deploy.act.types.action_publish import (
    ActionPublishRequest,
    ActionPublishResult,
    CommandPermit,
    PublishOutcome,
)
from model_deploy.act.types.action_spec import split_action
from model_deploy.act.types.safety_result import SafetyStatus

import numpy as np


# ---------------------------------------------------------------------------
# Fakes / spies
# ---------------------------------------------------------------------------


class SpySafety:
    """Wrap a real SafetyGuard and count filter_action calls."""

    def __init__(self, guard: SafetyGuard) -> None:
        self._guard = guard
        self.calls = 0

    def filter_action(self, *args, **kwargs) -> "object":
        self.calls += 1
        return self._guard.filter_action(*args, **kwargs)


class FakePublisher:
    """Bound publish port double: returns a configured outcome, echoes request."""

    def __init__(
        self,
        outcome: PublishOutcome,
        *,
        reason_code: str | None = None,
        failure_stage: str | None = None,
        failed_topic: str | None = None,
        command_output_enabled: bool = True,
    ) -> None:
        self.outcome = outcome
        self.reason_code = reason_code
        self.failure_stage = failure_stage
        self.failed_topic = failed_topic
        self.command_output_enabled = command_output_enabled
        self.calls: list[ActionPublishRequest] = []
        self.last_request: ActionPublishRequest | None = None

    def __call__(self, request: ActionPublishRequest) -> ActionPublishResult:
        self.calls.append(request)
        self.last_request = request
        return _build_result(
            self.outcome,
            request,
            reason_code=self.reason_code,
            failure_stage=self.failure_stage,
            failed_topic=self.failed_topic,
            command_output_enabled=self.command_output_enabled,
        )


def _build_result(
    outcome: PublishOutcome,
    request: ActionPublishRequest,
    *,
    reason_code: str | None,
    failure_stage: str | None,
    failed_topic: str | None,
    command_output_enabled: bool,
) -> ActionPublishResult:
    """Construct a valid ActionPublishResult for the given outcome (echoes id/status)."""
    safety_status = request.safety_result.status
    base = dict(
        action_id=request.action_id,
        safety_status=safety_status,
        command_output_enabled=command_output_enabled,
        command_permitted=request.command_permit.allowed,
        outcome=outcome,
    )
    if outcome == PublishOutcome.PUBLISHED:
        return ActionPublishResult(
            **base, policy_action_published=True, command_publish_count=4,
            gripper_skipped=(), command_plan_completed=True, status_published=True,
            reason_code=None, failure_stage=None, failed_topic=None,
        )
    if outcome == PublishOutcome.OBSERVED:
        return ActionPublishResult(
            **base, policy_action_published=True, command_publish_count=0,
            gripper_skipped=(), command_plan_completed=True, status_published=True,
            reason_code=None, failure_stage=None, failed_topic=None,
        )
    if outcome == PublishOutcome.BLOCKED:
        return ActionPublishResult(
            **base, policy_action_published=True, command_publish_count=0,
            gripper_skipped=(), command_plan_completed=True, status_published=True,
            reason_code=reason_code or "PERMIT_DENIED", failure_stage=None, failed_topic=None,
        )
    if outcome == PublishOutcome.REJECTED:
        return ActionPublishResult(
            **base, policy_action_published=False, command_publish_count=0,
            gripper_skipped=(), command_plan_completed=False,
            status_published=False,
            reason_code=reason_code or "SAFETY_REJECTED", failure_stage="safety",
            failed_topic=None,
        )
    if outcome == PublishOutcome.PARTIAL:
        return ActionPublishResult(
            **base, policy_action_published=True, command_publish_count=2,
            gripper_skipped=("left",), command_plan_completed=False,
            status_published=True,
            reason_code=reason_code or "COMMAND_PUBLISH_IO_ERROR",
            failure_stage="command_publish",
            failed_topic=failed_topic or "/act/command/left_arm_target",
        )
    if outcome == PublishOutcome.FAILED:
        return ActionPublishResult(
            **base, policy_action_published=False, command_publish_count=0,
            gripper_skipped=(), command_plan_completed=False,
            status_published=False,
            reason_code=reason_code or "POLICY_PUBLISH_IO_ERROR",
            failure_stage=failure_stage or "policy_publish",
            failed_topic=failed_topic or "/act/policy_action",
        )
    raise AssertionError(f"unknown outcome {outcome}")


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------


def _matching_vector(snapshot) -> np.ndarray:
    """16D vector equal to the snapshot's state -> safety PASSES (no projection).

    Segment order MUST match ``ActionSpec.as_vector``:
    ``[left_tcp(7) | right_tcp(7) | left_grip(1) | right_grip(1)]``.
    """
    s = snapshot.state
    return np.concatenate(
        [
            np.asarray(s.left_tcp_position, dtype=np.float32),
            np.asarray(s.left_tcp_orientation, dtype=np.float32),
            np.asarray(s.right_tcp_position, dtype=np.float32),
            np.asarray(s.right_tcp_orientation, dtype=np.float32),
            [float(s.left_gripper_width)],
            [float(s.right_gripper_width)],
        ]
    ).astype(np.float32)


def _make_matching_chunk(snapshot, chunk_size: int = 10) -> ActionChunk:
    vec = _matching_vector(snapshot)
    return ActionChunk(actions=np.tile(vec, (chunk_size, 1)).astype(np.float32))


def _success_result(
    request_id: int = 1, captured_at_s: float = 0.0, chunk_size: int = 10
) -> InferenceResult:
    snapshot = _make_snapshot(captured_at_s=captured_at_s)
    return InferenceResult.success(
        request_id=request_id,
        observation_captured_at_s=captured_at_s,
        submitted_at_s=captured_at_s + 0.01,
        started_at_s=captured_at_s + 0.02,
        completed_at_s=captured_at_s + 0.03,
        chunk=_make_matching_chunk(snapshot, chunk_size),
    )


def _error_result(request_id: int = 1, captured_at_s: float = 0.0) -> InferenceResult:
    return InferenceResult.error(
        request_id=request_id,
        observation_captured_at_s=captured_at_s,
        submitted_at_s=captured_at_s + 0.01,
        started_at_s=captured_at_s + 0.02,
        completed_at_s=captured_at_s + 0.03,
        exc=RuntimeError("boom"),
    )


def _make_loop(
    *,
    publisher,
    fallback_policy: str = "hold_last_action",
    chunk_size: int = 10,
    execute_horizon: int = 8,
    max_observation_age_s: float = 0.05,
    command_output_enabled: bool = True,
    observation_port=None,
    continue_to_chunk_size: bool = False,
):
    config = ControlLoopConfig(
        chunk_size=chunk_size,
        action_dim=16,
        execute_horizon=execute_horizon,
        max_observation_age_s=max_observation_age_s,
        command_output_enabled=command_output_enabled,
        continue_to_chunk_size=continue_to_chunk_size,
        fallback_policy=fallback_policy,
        prefetch_steps=1,
    )
    req_q: LatestQueue = LatestQueue()
    res_q: LatestQueue = LatestQueue()
    metrics = RuntimeMetrics(clock=lambda: 0.0)
    safety = SpySafety(SafetyGuard(SafetyConfig()))
    obs = observation_port if observation_port is not None else (
        lambda: _make_snapshot(captured_at_s=0.0)
    )
    loop = ControlLoop(
        config=config,
        request_queue=req_q,
        result_queue=res_q,
        metrics=metrics,
        safety_port=safety,
        publish_port=publisher,
        observation_port=obs,
    )
    return loop, req_q, res_q, safety


def _prime_published(loop: ControlLoop, res_q: LatestQueue) -> None:
    """Drive one full submit->result->publish so a last safe action exists."""
    loop.tick(0.0, 0.0, CommandPermit(allowed=True))  # submit rid=1
    res_q.put_latest(_success_result(request_id=1, captured_at_s=0.0))
    loop.tick(0.01, 0.01, CommandPermit(allowed=True))  # collect + publish


# ---------------------------------------------------------------------------
# C13 is_action_chunk_usable (pure)
# ---------------------------------------------------------------------------


class TestChunkUsable:
    def test_shape_and_age(self) -> None:
        chunk = _make_chunk()
        ok, _ = is_action_chunk_usable(
            chunk, captured_at_s=1.0, now=1.02, max_action_age_s=0.5, action_dim=16
        )
        assert ok
        bad, reason = is_action_chunk_usable(
            chunk, captured_at_s=1.0, now=2.0, max_action_age_s=0.5, action_dim=16
        )
        assert not bad and reason is not None

    def test_wrong_dim(self) -> None:
        chunk = np.zeros((10, 8), dtype=np.float32)  # bare ndarray (raw C13)
        ok, _ = is_action_chunk_usable(
            chunk, captured_at_s=1.0, now=1.02, max_action_age_s=0.5, action_dim=16
        )
        assert not ok

    def test_non_finite(self) -> None:
        arr = np.zeros((10, 16), dtype=np.float32)
        arr[0, 0] = float("nan")
        ok, _ = is_action_chunk_usable(
            arr, captured_at_s=1.0, now=1.02, max_action_age_s=0.5, action_dim=16
        )
        assert not ok


# ---------------------------------------------------------------------------
# C3 / C26 fallback selection (pure)
# ---------------------------------------------------------------------------


class TestFallbackSelection:
    def test_rejected_reasons_are_safe_stop(self) -> None:
        for reason in (
            FallbackReason.SAFETY_REJECTED,
            FallbackReason.PUBLISH_REJECTED,
            FallbackReason.PUBLISH_PARTIAL,
            FallbackReason.PUBLISH_FAILED,
            FallbackReason.RUNTIME_FAULT,
        ):
            sel = select_fallback(
                reason, hold_action=None, hold_source_captured_at_s=None,
                fallback_policy="hold_last_action",
            )
            assert sel.mode == "safe_stop"
            assert sel.action is None

    def test_hold_when_policy_and_action_present(self) -> None:
        snap = _make_snapshot()
        vec = _matching_vector(snap)
        spec = split_action(vec)
        sel = select_fallback(
            FallbackReason.NO_ACTIVE_ACTION, hold_action=spec,
            hold_source_captured_at_s=1.23, fallback_policy="hold_last_action",
        )
        assert sel.mode == "hold"
        assert sel.action is not None
        # deep copy: the selection is an owned copy (ActionSpec is frozen, so
        # we prove independence via identity + equal value, not mutation).
        assert sel.action is not spec
        assert sel.action.left_gripper == spec.left_gripper

    def test_safe_stop_policy_ignores_hold(self) -> None:
        snap = _make_snapshot()
        spec = split_action(_matching_vector(snap))
        sel = select_fallback(
            FallbackReason.NO_ACTIVE_ACTION, hold_action=spec,
            hold_source_captured_at_s=1.23, fallback_policy="safe_stop",
        )
        assert sel.mode == "safe_stop"


# ---------------------------------------------------------------------------
# At most one outstanding request; tick never blocks
# ---------------------------------------------------------------------------


class TestOutstandingRequest:
    def test_only_one_outstanding_across_ticks(self) -> None:
        publisher = FakePublisher(PublishOutcome.PUBLISHED)
        loop, req_q, res_q, _ = _make_loop(publisher=publisher)
        loop.tick(0.0, 0.0, CommandPermit(allowed=True))  # submit rid=1
        # No result provided; next tick must NOT submit a second request.
        loop.tick(0.01, 0.01, CommandPermit(allowed=True))
        assert loop._outstanding_request_id == 1
        assert loop._request_id_counter == 1

    def test_tick_returns_none_when_no_chunk(self) -> None:
        publisher = FakePublisher(PublishOutcome.PUBLISHED)
        loop, _, _, _ = _make_loop(publisher=publisher)
        result = loop.tick(0.0, 0.0, CommandPermit(allowed=True))
        assert result is None


# ---------------------------------------------------------------------------
# Correlation (B4 / C15)
# ---------------------------------------------------------------------------


class TestCorrelation:
    def test_matched_success_terminates_request_and_activates(self) -> None:
        publisher = FakePublisher(PublishOutcome.PUBLISHED)
        loop, _, res_q, _ = _make_loop(publisher=publisher)
        loop.tick(0.0, 0.0, CommandPermit(allowed=True))  # submit rid=1
        assert loop._outstanding_request_id == 1
        res_q.put_latest(_success_result(request_id=1, captured_at_s=0.0))
        result = loop.tick(0.01, 0.01, CommandPermit(allowed=True))
        assert loop._outstanding_request_id is None
        assert loop._active_chunk is not None
        assert result is not None
        assert result.outcome == PublishOutcome.PUBLISHED

    def test_matched_error_triggers_fallback_no_latch(self) -> None:
        publisher = FakePublisher(PublishOutcome.PUBLISHED)
        loop, _, res_q, _ = _make_loop(publisher=publisher)
        loop.tick(0.0, 0.0, CommandPermit(allowed=True))  # submit rid=1
        res_q.put_latest(_error_result(request_id=1, captured_at_s=0.0))
        result = loop.tick(0.01, 0.01, CommandPermit(allowed=True))
        snap = loop.metrics_snapshot()
        assert loop._outstanding_request_id is None
        assert result is None
        assert not snap.runtime_fault_latched

    def test_unknown_result_id_latches_runtime_fault(self) -> None:
        publisher = FakePublisher(PublishOutcome.PUBLISHED)
        loop, _, res_q, _ = _make_loop(publisher=publisher)
        # result arrives with no outstanding request -> unknown id
        res_q.put_latest(_success_result(request_id=5, captured_at_s=0.0))
        loop.tick(1.0, 1.0, CommandPermit(allowed=True))
        snap = loop.metrics_snapshot()
        assert snap.runtime_fault_latched
        assert snap.result_discarded_count >= 1

    def test_stale_result_id_latches_runtime_fault(self) -> None:
        publisher = FakePublisher(PublishOutcome.PUBLISHED)
        loop, _, res_q, _ = _make_loop(publisher=publisher)
        loop.tick(0.0, 0.0, CommandPermit(allowed=True))  # submit rid=1
        # stale id (lower than outstanding) arrives
        res_q.put_latest(_success_result(request_id=0, captured_at_s=0.0))
        loop.tick(0.01, 0.01, CommandPermit(allowed=True))
        assert loop.metrics_snapshot().runtime_fault_latched


# ---------------------------------------------------------------------------
# Cursor / horizon / age / continue (B6)
# ---------------------------------------------------------------------------


class TestCursorHorizonAge:
    def test_cursor_advances_within_horizon_normal_mode(self) -> None:
        publisher = FakePublisher(PublishOutcome.PUBLISHED)
        loop, _, res_q, _ = _make_loop(
            publisher=publisher, chunk_size=10, execute_horizon=3
        )
        loop.tick(0.0, 0.0, CommandPermit(allowed=True))
        res_q.put_latest(_success_result(request_id=1, captured_at_s=0.0))
        # consume 3 steps within horizon=3
        for t in (0.01, 0.02, 0.03):
            loop.tick(t, t, CommandPermit(allowed=True))
        assert loop._active_cursor == 3

    def test_continue_mode_reaches_chunk_size(self) -> None:
        publisher = FakePublisher(PublishOutcome.PUBLISHED)
        loop, _, res_q, _ = _make_loop(
            publisher=publisher, chunk_size=10, execute_horizon=3,
            continue_to_chunk_size=True,
        )
        loop.tick(0.0, 0.0, CommandPermit(allowed=True))
        res_q.put_latest(_success_result(request_id=1, captured_at_s=0.0))
        # with continue, cursor can advance past horizon up to chunk_size
        for i in range(5):
            loop.tick(0.01 + i * 0.01, 0.01 + i * 0.01, CommandPermit(allowed=True))
        assert loop._active_cursor == 5  # beyond execute_horizon=3

    def test_stale_active_chunk_discards_and_falls_back(self) -> None:
        publisher = FakePublisher(PublishOutcome.PUBLISHED)
        loop, _, res_q, _ = _make_loop(
            publisher=publisher, chunk_size=10, execute_horizon=8,
            max_observation_age_s=0.05,
        )
        loop.tick(0.0, 0.0, CommandPermit(allowed=True))
        res_q.put_latest(_success_result(request_id=1, captured_at_s=0.0))
        loop.tick(0.01, 0.01, CommandPermit(allowed=True))  # publish, last safe set
        # far future -> active chunk age exceeds max -> discard -> fallback
        result = loop.tick(10.0, 10.0, CommandPermit(allowed=True))
        snap = loop.metrics_snapshot()
        assert loop._active_chunk is None
        assert snap.result_discarded_count >= 1
        # hold fallback publishes a result (last safe action present)
        assert result is not None


# ---------------------------------------------------------------------------
# Safety / publish call contract (B7 / one-call invariants)
# ---------------------------------------------------------------------------


class TestSafetyPublishContract:
    def test_one_safety_and_one_publish_per_candidate(self) -> None:
        publisher = FakePublisher(PublishOutcome.PUBLISHED)
        loop, _, res_q, safety = _make_loop(publisher=publisher)
        loop.tick(0.0, 0.0, CommandPermit(allowed=True))
        res_q.put_latest(_success_result(request_id=1, captured_at_s=0.0))
        loop.tick(0.01, 0.01, CommandPermit(allowed=True))
        assert safety.calls == 1
        assert len(publisher.calls) == 1

    def test_safety_rejected_returns_none_no_fallback_same_tick(self) -> None:
        publisher = FakePublisher(PublishOutcome.PUBLISHED)
        loop, _, res_q, _ = _make_loop(publisher=publisher)
        loop.tick(0.0, 0.0, CommandPermit(allowed=True))
        res_q.put_latest(_success_result(request_id=1, captured_at_s=0.0))
        # Force a bad candidate: replace active chunk rows with non-unit quaternion.
        loop._active_chunk = ActionChunk(
            actions=np.tile(
                np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], dtype=np.float32),
                (10, 1),
            )
        )
        loop._active_chunk_captured_at_s = 0.0
        loop._active_cursor = 0
        result = loop.tick(0.02, 0.02, CommandPermit(allowed=True))
        snap = loop.metrics_snapshot()
        assert result is None
        assert snap.safety_rejected_count >= 1
        assert snap.deferred_fallback_reason == "SAFETY_REJECTED"


# ---------------------------------------------------------------------------
# Six-outcome fail-closed reducer (C17 / C19 / C23-C25)
# ---------------------------------------------------------------------------


class TestSixOutcomeReducer:
    @pytest.mark.parametrize(
        "outcome,reason_code,failure_stage,failed_topic,expect_status",
        [
            (PublishOutcome.PUBLISHED, None, None, None, "NORMAL"),
            (PublishOutcome.OBSERVED, None, None, None, "NORMAL"),
            (PublishOutcome.BLOCKED, "PERMIT_DENIED", None, None, "NORMAL"),
            (PublishOutcome.REJECTED, "SAFETY_REJECTED", "safety", None, "FALLBACK"),
            (PublishOutcome.PARTIAL, "COMMAND_PUBLISH_IO_ERROR", "command_publish", "/act/command/left_arm_target", "OUTPUT_FAULT"),
            (PublishOutcome.FAILED, "POLICY_PUBLISH_IO_ERROR", "policy_publish", "/act/policy_action", "OUTPUT_FAULT"),
        ],
    )
    def test_outcome_status_and_latch(
        self, outcome, reason_code, failure_stage, failed_topic, expect_status
    ) -> None:
        publisher = FakePublisher(
            outcome, reason_code=reason_code, failure_stage=failure_stage,
            failed_topic=failed_topic,
        )
        loop, _, res_q, _ = _make_loop(publisher=publisher)
        _prime_published(loop, res_q)
        result = loop.tick(0.02, 0.02, CommandPermit(allowed=True))
        snap = loop.metrics_snapshot()
        assert result is not None
        assert result.outcome == outcome
        # echo check: publisher echoes our action id
        assert result.action_id == publisher.last_request.action_id
        if outcome in (PublishOutcome.PARTIAL, PublishOutcome.FAILED):
            assert snap.output_fault_latched
        else:
            assert not snap.output_fault_latched
        if outcome in (PublishOutcome.REJECTED, PublishOutcome.BLOCKED):
            assert snap.deferred_fallback_reason is not None
        else:
            assert snap.deferred_fallback_reason is None

    def test_deferred_reason_delivered_once_then_recoverable(self) -> None:
        publisher = FakePublisher(PublishOutcome.REJECTED, reason_code="SAFETY_REJECTED")
        loop, _, res_q, _ = _make_loop(publisher=publisher)
        _prime_published(loop, res_q)
        loop.tick(0.02, 0.02, CommandPermit(allowed=True))
        first_deferred = loop.metrics_snapshot().deferred_fallback_reason
        assert first_deferred == "SAFETY_REJECTED"
        # second reject must NOT re-deliver
        loop.tick(0.03, 0.03, CommandPermit(allowed=True))
        assert loop.metrics_snapshot().deferred_fallback_reason == first_deferred
        # a successful observe clears the deferred reason (recoverable)
        publisher2 = FakePublisher(PublishOutcome.OBSERVED)
        loop._publish_port = publisher2  # type: ignore[assignment]
        loop.tick(0.04, 0.04, CommandPermit(allowed=True))
        assert loop.metrics_snapshot().deferred_fallback_reason is None

    def test_publish_result_invariant_on_echo_mismatch(self) -> None:
        # A malicious publish port that changes the action id must latch a fault.
        class BadPublisher(FakePublisher):
            def __call__(self, request):
                res = super().__call__(request)
                from dataclasses import replace
                return replace(res, action_id="TAMPERED")

        loop, _, res_q, _ = _make_loop(publisher=BadPublisher(PublishOutcome.PUBLISHED))
        loop.tick(0.0, 0.0, CommandPermit(allowed=True))
        res_q.put_latest(_success_result(request_id=1, captured_at_s=0.0))
        loop.tick(0.01, 0.01, CommandPermit(allowed=True))
        assert loop.metrics_snapshot().runtime_fault_latched


# ---------------------------------------------------------------------------
# Fallback modes (B8): hold vs safe-stop
# ---------------------------------------------------------------------------


class TestFallbackModes:
    def test_safe_stop_policy_no_output(self) -> None:
        publisher = FakePublisher(PublishOutcome.PUBLISHED)
        loop, _, _, _ = _make_loop(publisher=publisher, fallback_policy="safe_stop")
        result = loop.tick(0.0, 0.0, CommandPermit(allowed=True))
        snap = loop.metrics_snapshot()
        assert result is None
        assert snap.runtime_status == "FALLBACK_SAFE_STOP"
        assert not snap.runtime_fault_latched

    def test_hold_policy_publishes_held_action(self) -> None:
        publisher = FakePublisher(PublishOutcome.PUBLISHED)
        loop, _, res_q, _ = _make_loop(publisher=publisher, fallback_policy="hold_last_action")
        loop.tick(0.0, 0.0, CommandPermit(allowed=True))
        res_q.put_latest(_success_result(request_id=1, captured_at_s=0.0))
        loop.tick(0.01, 0.01, CommandPermit(allowed=True))  # publish -> last safe set
        # Cause a stale-chunk fallback; hold should re-publish the held action.
        result = loop.tick(10.0, 10.0, CommandPermit(allowed=True))
        snap = loop.metrics_snapshot()
        assert result is not None
        assert result.outcome == PublishOutcome.PUBLISHED
        assert snap.runtime_status == "NORMAL"

    def test_hold_does_not_refresh_source_age(self) -> None:
        publisher = FakePublisher(PublishOutcome.PUBLISHED)
        loop, _, res_q, _ = _make_loop(publisher=publisher)
        loop.tick(0.0, 0.0, CommandPermit(allowed=True))
        res_q.put_latest(_success_result(request_id=1, captured_at_s=0.0))
        loop.tick(0.01, 0.01, CommandPermit(allowed=True))
        held_source = loop._last_safe_source_captured_at_s
        # fallback hold keeps the original source age
        loop.tick(10.0, 10.0, CommandPermit(allowed=True))
        assert loop._last_safe_source_captured_at_s == held_source


# ---------------------------------------------------------------------------
# runtime_status single-writer priority + shutdown convergence
# ---------------------------------------------------------------------------


class TestStatusAndShutdown:
    def test_runtime_fault_overrides_tick_status(self) -> None:
        publisher = FakePublisher(PublishOutcome.PUBLISHED)
        loop, _, res_q, _ = _make_loop(publisher=publisher)
        # unknown id -> runtime fault
        res_q.put_latest(_success_result(request_id=9, captured_at_s=0.0))
        loop.tick(1.0, 1.0, CommandPermit(allowed=True))
        snap = loop.metrics_snapshot()
        assert snap.runtime_fault_latched
        assert snap.runtime_status == "RUNTIME_FAULT"

    def test_shutdown_converges_no_output(self) -> None:
        publisher = FakePublisher(PublishOutcome.PUBLISHED)
        loop, _, res_q, safety = _make_loop(publisher=publisher)
        loop.tick(0.0, 0.0, CommandPermit(allowed=True))
        res_q.put_latest(_success_result(request_id=1, captured_at_s=0.0))
        loop.tick(0.01, 0.01, CommandPermit(allowed=True))
        loop.request_shutdown()
        # After shutdown: no safety / publish calls, status frozen.
        safety_before = safety.calls
        pub_before = len(publisher.calls)
        result = loop.tick(0.02, 0.02, CommandPermit(allowed=True))
        assert result is None
        assert safety.calls == safety_before
        assert len(publisher.calls) == pub_before
        assert loop.metrics_snapshot().runtime_status == "SHUTDOWN"


# ---------------------------------------------------------------------------
# CandidateSelection deep-copy (C3)
# ---------------------------------------------------------------------------


class TestCandidateSelection:
    def test_candidate_is_owned_copy(self) -> None:
        snap = _make_snapshot()
        spec = split_action(_matching_vector(snap))
        sel = select_candidate(
            spec.as_vector(), previous_safe_action=spec, hold_action=spec,
            source="x", source_captured_at_s=1.0,
        )
        # ActionSpec is frozen: prove the candidate is an owned copy via
        # identity (and equal value), not via mutation of the source.
        assert sel.candidate_action is not spec
        assert sel.candidate_action.left_gripper == spec.left_gripper
        assert sel.previous_safe_action is not spec
        assert sel.hold_action is not spec
