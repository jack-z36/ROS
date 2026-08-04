"""ControlLoop: L2-06 central scheduling state machine (deploy_053).

Implements the non-blocking ``ControlLoop.tick`` that is the heart of l2-06.
It owns:

- request/result correlation against a single outstanding inference request
- active / pending chunk bookkeeping and the per-step cursor
- prefetch / horizon / continue policy for chunk consumption
- fallback selection (hold / continue / safe-stop) and fail-closed latches
- the once-per-tick safety call and the at-most-once publish call
- the six-outcome fail-closed reducer with publish-result echo checks
- ``runtime_status`` single-writer priority and shutdown convergence

The ControlLoop does NOT implement policy loading, ACT batch construction,
ROS publishing internals, or hardware I/O. It calls three injected public
ports only:

- ``safety_port``  — an object exposing ``filter_action(candidate,
  previous_safe_action=, latest_observation=) -> SafetyResult`` (L2-04).
- ``publish_port`` — a callable ``ActionPublishRequest -> ActionPublishResult``
  (L2-05 bound publisher).
- ``observation_port`` — a callable ``() -> Optional[ObservationSnapshot]``
  (L2-02 latest-observation reader).

It consumes the deploy_051 frozen envelopes (``InferenceRequest`` /
``InferenceResult`` / ``LatestQueue``), the deploy_052 worker's single serial
inference axis, and the deploy_056 canonical ``PolicyInputSpec`` (for
``chunk_size`` / ``action_dim``). It writes only to the injected
``RuntimeMetrics`` (deploy_052) — the single owner of runtime_status.

Micro-units implemented here (L2-06 agent_context numbering):
  - A4  ControlLoop            (class: cross-tick state + tick orchestration)
  - B3  tick                   (fixed total order)
  - B4  _collect_chunk_result   (correlation)
  - B5  _maybe_submit_inference (prefetch / horizon decision)
  - B6  _select_raw_action      (cursor / horizon / age recheck)
  - B7  _run_safety             (one safety call per candidate)
  - B8  _run_fallback           (exclusive hold / continue / safe-stop)
  - C3  FallbackReason / select_fallback / select_candidate (data + selection)
  - C7  ControlLoopConfig       (cross-tick state init data)
  - C13 is_action_chunk_usable  (pure age/shape calc)
  - C14 _should_submit_inference (pure submit decision)
  - C15-C17/C19/C23-C25 internal state update + reducer + latches
  - C18 build_inference_request (request contract)
  - C26 FALLBACK_MATRIX         (fallback reason -> mode mapping)
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Optional, Tuple

import numpy as np

from model_deploy.act.runtime.inference_channel import (
    InferenceRequest,
    InferenceResult,
    LatestQueue,
)
from model_deploy.act.runtime.runtime_metrics import RuntimeMetrics
from model_deploy.act.runtime.action_response_verifier import (
    ActionResponseVerifier,
    ResponseState,
)
from model_deploy.act.types.action_chunk import ActionChunk
from model_deploy.act.types.action_spec import ActionSpec, split_action
from model_deploy.act.types.action_publish import (
    ActionPublishRequest,
    ActionPublishResult,
    CommandPermit,
    PublishOutcome,
)
from model_deploy.act.types.observation import ObservationSnapshot
from model_deploy.act.types.safety_result import SafetyResult, SafetyStatus


# ---------------------------------------------------------------------------
# Port / provider type aliases (no public class names imported here)
# ---------------------------------------------------------------------------

#: L2-04 port: object exposing ``filter_action``.
SafetyPort = Any
#: L2-05 bound publisher: request -> frozen result.
PublishPort = Callable[[ActionPublishRequest], ActionPublishResult]
#: L2-02 latest-observation reader.
ObservationPort = Callable[[], Optional[ObservationSnapshot]]


# ---------------------------------------------------------------------------
# C3 / C26 — fallback reason + frozen selection
# ---------------------------------------------------------------------------


class FallbackReason(str, Enum):
    """Stable fallback reason codes owned by L2-06 (C3)."""

    OBSERVATION_MISSING = "OBSERVATION_MISSING"
    OBSERVATION_STALE = "OBSERVATION_STALE"
    NO_ACTIVE_ACTION = "NO_ACTIVE_ACTION"
    INFERENCE_ERROR = "INFERENCE_ERROR"
    CHUNK_DISCARDED = "CHUNK_DISCARDED"
    SAFETY_REJECTED = "SAFETY_REJECTED"
    PUBLISH_REJECTED = "PUBLISH_REJECTED"
    PUBLISH_BLOCKED = "PUBLISH_BLOCKED"
    PUBLISH_PARTIAL = "PUBLISH_PARTIAL"
    PUBLISH_FAILED = "PUBLISH_FAILED"
    RUNTIME_FAULT = "RUNTIME_FAULT"


#: Reasons that must NOT trigger a hold output (fail-closed latched / rejected).
_NO_HOLD_REASONS = frozenset(
    {
        FallbackReason.SAFETY_REJECTED,
        FallbackReason.PUBLISH_REJECTED,
        FallbackReason.PUBLISH_PARTIAL,
        FallbackReason.PUBLISH_FAILED,
        FallbackReason.RUNTIME_FAULT,
    }
)


@dataclass(frozen=True)
class FallbackSelection:
    """Frozen fallback decision produced by ``select_fallback`` (C3/C26).

    ``action`` is a deep copy of the hold action and is non-None only for the
    ``hold`` mode. ``source_captured_at_s`` is the ORIGINAL capture time of the
    held action and is never refreshed to the current publish time.
    """

    reason: FallbackReason
    mode: str  # "hold" or "safe_stop"
    action: Optional[ActionSpec]
    source_captured_at_s: Optional[float]


def select_fallback(
    reason: FallbackReason,
    *,
    hold_action: Optional[ActionSpec],
    hold_source_captured_at_s: Optional[float],
    fallback_policy: str,
) -> FallbackSelection:
    """Map a fallback reason to a frozen selection (C3 / C26 FALLBACK_MATRIX).

    Rejected / fail-closed reasons always resolve to ``safe_stop`` with no
    output. Otherwise, when the configured policy is ``hold_last_action`` and a
    hold action is available, the deep-copied hold action is returned for the
    ``hold`` mode; otherwise ``safe_stop`` (no output).
    """
    if reason in _NO_HOLD_REASONS:
        return FallbackSelection(reason, "safe_stop", None, None)
    if fallback_policy != "hold_last_action":
        return FallbackSelection(reason, "safe_stop", None, None)
    if hold_action is not None:
        return FallbackSelection(
            reason,
            "hold",
            _deep_copy_spec(hold_action),
            hold_source_captured_at_s,
        )
    return FallbackSelection(reason, "safe_stop", None, None)


#: Documentation matrix (C26): reason -> resolved mode under ``hold_last_action``.
FALLBACK_MATRIX = {
    FallbackReason.OBSERVATION_MISSING: "hold-or-safe_stop",
    FallbackReason.OBSERVATION_STALE: "hold-or-safe_stop",
    FallbackReason.NO_ACTIVE_ACTION: "hold-or-safe_stop",
    FallbackReason.INFERENCE_ERROR: "hold-or-safe_stop",
    FallbackReason.CHUNK_DISCARDED: "hold-or-safe_stop",
    FallbackReason.SAFETY_REJECTED: "safe_stop (no output)",
    FallbackReason.PUBLISH_REJECTED: "safe_stop (no output)",
    FallbackReason.PUBLISH_BLOCKED: "deferred-reason (output observed)",
    FallbackReason.PUBLISH_PARTIAL: "safe_stop + output_fault latch",
    FallbackReason.PUBLISH_FAILED: "safe_stop + output_fault latch",
    FallbackReason.RUNTIME_FAULT: "safe_stop + runtime_fault latch",
}


# ---------------------------------------------------------------------------
# CandidateSelection — deep-copied candidate / previous / hold (C3)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CandidateSelection:
    """Deep-copied per-tick candidate bundle handed to the safety call (C3).

    All array-backed fields are owned copies so the safety port and the
    held-action path can never mutate the ControlLoop's stored references. The
    ``source_captured_at_s`` keeps the ORIGINAL capture time and is never
    refreshed by the publish time (avoids infinite stale-target repeats).
    """

    candidate_action: ActionSpec
    previous_safe_action: Optional[ActionSpec]
    hold_action: Optional[ActionSpec]
    source: str
    source_captured_at_s: float


def select_candidate(
    candidate_vector: np.ndarray,
    *,
    previous_safe_action: Optional[ActionSpec],
    hold_action: Optional[ActionSpec],
    source: str,
    source_captured_at_s: float,
) -> CandidateSelection:
    """Build a deep-copied candidate selection from a raw 16D vector (C3)."""
    candidate = _deep_copy_spec(split_action(candidate_vector))
    prev = _deep_copy_spec(previous_safe_action) if previous_safe_action is not None else None
    hold = _deep_copy_spec(hold_action) if hold_action is not None else None
    return CandidateSelection(
        candidate_action=candidate,
        previous_safe_action=prev,
        hold_action=hold,
        source=source,
        source_captured_at_s=float(source_captured_at_s),
    )


# ---------------------------------------------------------------------------
# C7 — control-loop configuration (injected at construction)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ControlLoopConfig:
    """Frozen runtime config injected into the ControlLoop (C7).

    Attributes:
        chunk_size:              Active chunk length (from PolicyInputSpec).
        action_dim:              Physical action dimension (16).
        execute_horizon:         Normal-mode cursor horizon (prefix of chunk).
        max_observation_age_s:   Max age for chunk / observation freshness.
        command_output_enabled:  Startup command switch (L2-01 CLI keyword).
        continue_to_chunk_size:  B6: ``continue`` policy lets cursor reach
                                 ``chunk_size``; normal stops at execute_horizon.
        fallback_policy:         ``"hold_last_action"`` or ``"safe_stop"``.
        prefetch_steps:          Margin before chunk end to trigger prefetch.
    """

    chunk_size: int
    action_dim: int
    execute_horizon: int
    max_observation_age_s: float
    command_output_enabled: bool
    continue_to_chunk_size: bool = False
    fallback_policy: str = "hold_last_action"
    prefetch_steps: int = 1
    response_verification_enabled: bool = False


# ---------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------


def _deep_copy_spec(spec: ActionSpec) -> ActionSpec:
    """Return an owned deep copy of an ActionSpec (frozen ndarray fields)."""
    if spec is None:
        raise TypeError("cannot deep-copy a None ActionSpec")
    return ActionSpec(
        left_tcp_action=np.array(spec.left_tcp_action, dtype=np.float32, copy=True),
        right_tcp_action=np.array(spec.right_tcp_action, dtype=np.float32, copy=True),
        left_gripper=float(spec.left_gripper),
        right_gripper=float(spec.right_gripper),
    )


def _actions_of(chunk: Any) -> np.ndarray:
    """Accept an ``ActionChunk`` or a bare action ndarray (defensive C13)."""
    actions = getattr(chunk, "actions", chunk)
    return np.asarray(actions, dtype=np.float32)


def is_action_chunk_usable(
    chunk: Any,
    *,
    captured_at_s: float,
    now: float,
    max_action_age_s: float,
    action_dim: int,
) -> Tuple[bool, Optional[str]]:
    """Validate chunk shape / finiteness / age (C13, pure).

    Accepts either a frozen ``ActionChunk`` or a bare ``(N, action_dim)``
    ndarray so the pure helper can be exercised without constructing an
    ``ActionChunk`` (whose own post-init rejects malformed input).
    """
    actions = _actions_of(chunk)
    if actions.ndim != 2:
        return False, f"invalid rank {actions.ndim}"
    if actions.shape[1] != action_dim:
        return False, f"invalid action_dim {actions.shape[1]}"
    if not np.all(np.isfinite(actions)):
        return False, "chunk contains NaN or Inf"
    age_s = float(now) - float(captured_at_s)
    if age_s > float(max_action_age_s):
        return False, f"chunk too old age_s={age_s:.3f}"
    return True, None


def _check_chunk_shape(chunk: Any, action_dim: int) -> Tuple[bool, Optional[str]]:
    """Shape/finiteness only (used when a fresh result arrives)."""
    actions = _actions_of(chunk)
    if actions.ndim != 2:
        return False, f"invalid rank {actions.ndim}"
    if actions.shape[1] != action_dim:
        return False, f"invalid action_dim {actions.shape[1]}"
    if not np.all(np.isfinite(actions)):
        return False, "chunk contains NaN or Inf"
    return True, None


def build_inference_request(
    request_id: int,
    observation: ObservationSnapshot,
    monotonic_s: float,
    trigger_cursor: int,
) -> InferenceRequest:
    """Build the frozen request envelope for the worker (C18 contract)."""
    return InferenceRequest(
        request_id=request_id,
        observation=observation,
        submitted_at_s=float(monotonic_s),
        trigger_cursor=int(trigger_cursor),
    )


# ---------------------------------------------------------------------------
# A4 — ControlLoop
# ---------------------------------------------------------------------------


class ControlLoop:
    """Central scheduling state machine for L2-06 (A4).

    Holds all cross-tick scheduling state. ``tick`` is non-blocking: it reads
    the latest result without waiting, keeps at most one outstanding inference
    request, and returns an ``ActionPublishResult`` (or ``None`` when the tick
    produced no output / entered fallback).

    Lifecycle: construct with injected ports/queues/metrics, drive ``tick``
    from an external timer, then ``request_shutdown`` to converge.
    """

    def __init__(
        self,
        *,
        config: ControlLoopConfig,
        request_queue: LatestQueue,
        result_queue: LatestQueue,
        metrics: RuntimeMetrics,
        safety_port: SafetyPort,
        publish_port: PublishPort,
        observation_port: ObservationPort,
        on_inference_result: Optional[Callable] = None,
        on_safety_result: Optional[Callable] = None,
        response_verifier: Optional[ActionResponseVerifier] = None,
    ) -> None:
        if not isinstance(config, ControlLoopConfig):
            raise TypeError("config must be a ControlLoopConfig")
        if config.execute_horizon <= 0:
            raise ValueError("execute_horizon must be positive")
        if config.execute_horizon > config.chunk_size:
            raise ValueError("execute_horizon must not exceed chunk_size")

        self._config = config
        self._request_queue = request_queue
        self._result_queue = result_queue
        self._metrics = metrics
        self._safety_port = safety_port
        self._publish_port = publish_port
        self._observation_port = observation_port
        self._response_verifier = response_verifier
        if response_verifier is not None and not isinstance(
            response_verifier, ActionResponseVerifier
        ):
            raise TypeError("response_verifier must be ActionResponseVerifier or None")

        # --- cross-tick chunk state ---
        self._active_chunk: Optional[ActionChunk] = None
        self._active_chunk_request_id: Optional[int] = None
        self._active_chunk_captured_at_s: Optional[float] = None
        self._active_cursor: int = 0
        self._pending_chunk: Optional[ActionChunk] = None
        self._pending_chunk_request_id: Optional[int] = None
        self._pending_chunk_captured_at_s: Optional[float] = None

        # --- correlation / request id ---
        self._outstanding_request_id: Optional[int] = None
        self._last_submitted_request_id: Optional[int] = None
        self._request_id_counter: int = 0
        self._action_seq: int = 0

        # --- safety / hold tracking ---
        self._last_safe_action: Optional[ActionSpec] = None
        self._last_safe_source_captured_at_s: Optional[float] = None

        # --- fallback / latch bookkeeping ---
        self._pending_fallback_reason: Optional[FallbackReason] = None
        self._deferred_delivered: bool = False
        self._tick_status: str = "NORMAL"

        # --- debug callbacks ---
        self._on_inference_result = on_inference_result
        self._on_safety_result = on_safety_result
        self._debug_step_counter: int = 0
        self._current_debug_step_id: Optional[int] = None

        # --- shutdown ---
        self._shutdown_requested: bool = False

        # Single writer of runtime_status.
        self._metrics.record_event("status", value="STARTING")

    # ------------------------------------------------------------------
    # Public surface
    # ------------------------------------------------------------------

    def tick(
        self,
        monotonic_s: float,
        ros_time_s: float,
        command_permit: CommandPermit,
    ) -> Optional[ActionPublishResult]:
        """Run one non-blocking scheduling step (B3 fixed order).

        Returns the published ``ActionPublishResult``, or ``None`` when this
        tick produced no output (fallback / safe-stop / shutdown).
        """
        self._tick_status = "NORMAL"
        self._metrics.record_event("tick")

        # Shutdown convergence: no further output, status frozen.
        if self._shutdown_requested:
            self._finalize_runtime_status()
            return None

        # A real command is issued only when the preceding command has either
        # demonstrated progress or completed its hold window.  This keeps the
        # response window meaningful and prevents a stalled actuator from
        # being hidden by a stream of newer targets.
        latest_observation = self._observation_port()
        if (
            self._response_verifier is not None
            and command_permit.allowed
            and latest_observation is None
        ):
            # An allowed real command without a physical baseline is a
            # contract violation.  Do not fall back to the previous target.
            self._latch_runtime_fault("RESPONSE_BASELINE_MISSING")
            self._tick_status = "RUNTIME_FAULT"
            self._finalize_runtime_status()
            return None
        if self._response_verifier is not None:
            response = self._response_verifier.observe(latest_observation, monotonic_s)
            if response.state is ResponseState.FAULT:
                self._metrics.record_event(
                    "last_response_detail", value=response.detail
                )
                self._latch_runtime_fault(response.reason_code or "RESPONSE_FAULT")
                self._tick_status = "RUNTIME_FAULT"
                self._finalize_runtime_status()
                return None
            if response.state is ResponseState.WAITING:
                self._metrics.record_event(
                    "last_error", value=response.reason_code or "RESPONSE_WAITING"
                )
                self._tick_status = "RESPONSE_WAITING"
                self._finalize_runtime_status()
                return None

        # 1. correlate latest result (may activate pending / mark fallback)
        self._collect_chunk_result(monotonic_s, command_permit, ros_time_s)
        # 2. prefetch / submit a new inference request if needed
        self._maybe_submit_inference(monotonic_s, command_permit)
        # 3. select raw single action by cursor / horizon / age
        vector = self._select_raw_action(monotonic_s)
        reason = self._pending_fallback_reason
        self._pending_fallback_reason = None

        if vector is None:
            if reason is None:
                reason = FallbackReason.NO_ACTIVE_ACTION
            result = self._run_fallback(reason, command_permit, ros_time_s, monotonic_s)
            self._finalize_runtime_status()
            return result

        # --- debug: 阶段 1 推理结果回调 ---
        try:
            if self._on_inference_result is not None:
                self._debug_step_counter += 1
                step_id = self._on_inference_result(list(vector.tolist()))
                self._current_debug_step_id = step_id
        except Exception:
            pass

        # Candidate selection: deep copy so safety / hold cannot mutate state.
        selection = select_candidate(
            vector,
            previous_safe_action=self._last_safe_action,
            hold_action=self._last_safe_action,
            source=self._candidate_source(),
            source_captured_at_s=(
                self._active_chunk_captured_at_s
                if self._active_chunk_captured_at_s is not None
                else 0.0
            ),
        )
        self._metrics.record_event("action_candidate")
        self._metrics.record_event("last_candidate_source", value=selection.source)
        self._metrics.record_event(
            "last_candidate_source_time", value=selection.source_captured_at_s
        )

        # 4. safety — exactly one call per candidate (B7)
        # Read one coherent physical baseline for this candidate.  The safety
        # guard must compare against this observation, not against an older
        # command that may never have reached the robot.
        safety_result = self._safety_port.filter_action(
            selection.candidate_action,
            previous_safe_action=(
                selection.previous_safe_action
                if (command_permit.allowed and self._config.command_output_enabled)
                else None
            ),
            latest_observation=latest_observation,
        )
        self._metrics.record_event(
            "last_safety_findings",
            value=tuple(f.code.value for f in safety_result.findings),
        )

        # --- debug: 阶段 2 安全过滤回调 ---
        try:
            if self._on_safety_result is not None and self._current_debug_step_id is not None:
                _verdict = safety_result.status.value
                _filtered = (
                    list(safety_result.action.as_vector().tolist())
                    if safety_result.action is not None
                    else []
                )
                _details = {
                    "findings": [
                        {"code": f.code.value, "side": f.side, "detail": f.detail}
                        for f in safety_result.findings
                    ]
                } if safety_result.findings else None
                self._on_safety_result(
                    self._current_debug_step_id, _verdict, _filtered, _details
                )
        except Exception:
            pass

        if safety_result.status == SafetyStatus.REJECTED or safety_result.action is None:
            # Do NOT also emit a fallback in the same tick (per task rule).
            self._metrics.record_event("safety_rejected")
            self._deliver_deferred_reason("SAFETY_REJECTED")
            self._tick_status = "FALLBACK"
            self._finalize_runtime_status()
            return None

        # 5. publish — at most once per candidate (B8 publish)
        result = self._call_publish(safety_result, command_permit, ros_time_s, monotonic_s)
        # 6. reduce outcome + latches (C17/C19/C23/C24/C25)
        self._reduce_publish_outcome(result, safety_result, monotonic_s)
        # Only a real, complete command publication may become the next
        # inter-command reference.  OBSERVED (dry-run) and BLOCKED (permit
        # denied) are not hardware execution and must not advance the
        # reference chain.
        if (
            result.outcome is PublishOutcome.PUBLISHED
            and result.command_permitted
            and result.command_publish_count > 0
            and safety_result.action is not None
        ):
            self._store_safe_action(safety_result.action, refresh_source=True)
            self._record_physical_command(
                action_id=result.action_id,
                action=safety_result.action,
                baseline=latest_observation,
                issued_at_s=monotonic_s,
            )
        self._set_tick_status_for_outcome(result.outcome)
        self._finalize_runtime_status()
        return result

    def request_shutdown(self) -> None:
        """Converge: close both queues and latch the shutdown status."""
        if self._shutdown_requested:
            return
        self._shutdown_requested = True
        cleared = 0
        cleared += self._request_queue.close()
        cleared += self._result_queue.close()
        self._metrics.record_event("shutdown_queue_cleared", value=cleared)
        self._metrics.record_event("status", value="SHUTDOWN")

    def metrics_snapshot(self):
        """Return a frozen metrics snapshot (read-only cross-thread view)."""
        return self._metrics.snapshot()

    # ------------------------------------------------------------------
    # B4 — result correlation (C15)
    # ------------------------------------------------------------------

    def _collect_chunk_result(
        self,
        monotonic_s: float,
        command_permit: CommandPermit,
        ros_time_s: float,
    ) -> None:
        """Non-blocking correlation of the latest result (B4 / C15)."""
        result = self._result_queue.take_latest(timeout_s=0)
        if result is None:
            return

        outstanding = self._outstanding_request_id
        if outstanding is None:
            # No in-flight request -> protocol violation / unknown id.
            self._metrics.record_event("result_discarded")
            if (
                self._last_submitted_request_id is None
                or result.request_id > self._last_submitted_request_id
            ):
                self._latch_runtime_fault("UNKNOWN_RESULT_ID")
            else:
                self._latch_runtime_fault("STALE_RESULT_ID")
            return

        if result.request_id != outstanding:
            # Not the outstanding request -> discard, latch invariant.
            self._metrics.record_event("result_discarded")
            if result.request_id > outstanding:
                self._latch_runtime_fault("UNKNOWN_RESULT_ID")
            else:
                self._latch_runtime_fault("STALE_RESULT_ID")
            return

        # Matched the outstanding request -> terminate in-flight.
        self._outstanding_request_id = None
        self._metrics.record_event("in_flight_request_id", value=None)

        if result.is_success:
            self._accept_pending_chunk(result)
        else:
            # Inference failure -> fallback (recoverable, no latch).
            self._pending_fallback_reason = FallbackReason.INFERENCE_ERROR

    def _accept_pending_chunk(self, result: InferenceResult) -> None:
        """Validate and stage a successful chunk as the pending chunk (C15)."""
        chunk = result.chunk
        ok, reason = _check_chunk_shape(chunk, self._config.action_dim)
        if not ok:
            self._metrics.record_event("result_discarded")
            self._latch_runtime_fault(f"CHUNK_SHAPE_INVALID:{reason}")
            return
        self._set_pending_chunk(
            chunk, result.request_id, result.observation_captured_at_s
        )

    # ------------------------------------------------------------------
    # B5 — prefetch / submit decision (C14)
    # ------------------------------------------------------------------

    def _should_submit_inference(self, observation: Optional[ObservationSnapshot]) -> bool:
        """Pure submit decision (C14): no double-prefetch, horizon trigger."""
        if observation is None:
            return False
        if self._pending_chunk is not None:
            return False  # do not double-prefetch
        if self._active_chunk is None:
            return True  # bootstrap the first chunk
        horizon = (
            self._config.chunk_size
            if self._config.continue_to_chunk_size
            else self._config.execute_horizon
        )
        trigger = max(0, horizon - self._config.prefetch_steps)
        return self._active_cursor >= trigger

    def _maybe_submit_inference(
        self, monotonic_s: float, command_permit: CommandPermit
    ) -> None:
        """Submit at most one outstanding request (B5).

        A pending fallback reason (e.g. an inference error collected this tick)
        means this tick is already committed to a fallback; do not also issue a
        new request in the same tick. Recovery happens on the next tick.
        """
        if self._outstanding_request_id is not None:
            return  # at most one outstanding request
        if self._pending_fallback_reason is not None:
            return  # this tick resolves a fallback instead of prefetching
        observation = self._observation_port()
        if observation is None:
            if self._pending_fallback_reason is None:
                self._pending_fallback_reason = FallbackReason.OBSERVATION_MISSING
            return
        if not self._should_submit_inference(observation):
            return
        self._request_id_counter += 1
        rid = self._request_id_counter
        request = build_inference_request(
            rid, observation, monotonic_s, self._active_cursor
        )
        dropped = self._request_queue.put_latest(request)
        if dropped:
            self._metrics.record_event("request_queue_drop", value=dropped)
        self._outstanding_request_id = rid
        self._last_submitted_request_id = rid
        self._metrics.record_event("request_submitted")
        self._metrics.record_event("in_flight_request_id", value=rid)

    # ------------------------------------------------------------------
    # B6 — raw action selection (cursor / horizon / age recheck)
    # ------------------------------------------------------------------

    def _select_raw_action(self, monotonic_s: float) -> Optional[np.ndarray]:
        """Select the next raw single action by cursor (B6). Returns vector or None."""
        # Activate a ready pending chunk when no active chunk exists.
        if self._active_chunk is None and self._pending_chunk is not None:
            self._activate_pending(monotonic_s)
            if self._active_chunk is None:
                return None

        if self._active_chunk is None:
            return None

        horizon = (
            self._config.chunk_size
            if self._config.continue_to_chunk_size
            else self._config.execute_horizon
        )
        if self._active_cursor >= horizon:
            # pending does not truncate active; switch only at the boundary
            if self._pending_chunk is not None:
                self._activate_pending(monotonic_s)
                if self._active_chunk is None:
                    return None
            else:
                return None

        # Age recheck against the chunk's source observation capture time.
        if (
            self._active_chunk_captured_at_s is not None
            and (monotonic_s - self._active_chunk_captured_at_s)
            > self._config.max_observation_age_s
        ):
            self._discard_active_chunk(FallbackReason.OBSERVATION_STALE)
            return None

        if self._active_cursor >= self._active_chunk.actions.shape[0]:
            return None

        row = self._active_chunk.actions[self._active_cursor]
        self._active_cursor += 1
        self._metrics.record_event("active_cursor", value=self._active_cursor)
        return np.array(row, dtype=np.float32).copy()  # deep-copied candidate

    # ------------------------------------------------------------------
    # Chunk activation helpers
    # ------------------------------------------------------------------

    def _set_active_chunk(
        self,
        chunk: ActionChunk,
        request_id: Optional[int],
        captured_at_s: Optional[float],
    ) -> None:
        self._active_chunk = chunk
        self._active_chunk_request_id = request_id
        self._active_chunk_captured_at_s = captured_at_s
        self._active_cursor = 0
        self._metrics.record_event("active_request_id", value=request_id)
        self._metrics.record_event("active_cursor", value=0)
        self._metrics.record_event(
            "active_chunk_size", value=int(chunk.actions.shape[0])
        )
        self._metrics.record_event("chunk_activated")

    def _set_pending_chunk(
        self,
        chunk: ActionChunk,
        request_id: Optional[int],
        captured_at_s: Optional[float],
    ) -> None:
        self._pending_chunk = chunk
        self._pending_chunk_request_id = request_id
        self._pending_chunk_captured_at_s = captured_at_s
        self._metrics.record_event("pending_request_id", value=request_id)

    def _activate_pending(self, monotonic_s: float) -> None:
        """Switch pending -> active, rechecking age (C16)."""
        chunk = self._pending_chunk
        rid = self._pending_chunk_request_id
        captured = self._pending_chunk_captured_at_s
        if (
            captured is not None
            and (monotonic_s - captured) > self._config.max_observation_age_s
        ):
            self._metrics.record_event("result_discarded")
            self._pending_chunk = None
            self._pending_chunk_request_id = None
            self._pending_chunk_captured_at_s = None
            self._metrics.record_event("pending_request_id", value=None)
            self._latch_runtime_fault("PENDING_CHUNK_STALE")
            return
        self._set_active_chunk(chunk, rid, captured)
        self._pending_chunk = None
        self._pending_chunk_request_id = None
        self._pending_chunk_captured_at_s = None
        self._metrics.record_event("pending_request_id", value=None)

    def _discard_active_chunk(self, reason: FallbackReason) -> None:
        """Drop the active chunk and request a fallback (C16)."""
        self._metrics.record_event("result_discarded")
        self._active_chunk = None
        self._active_chunk_request_id = None
        self._active_chunk_captured_at_s = None
        self._active_cursor = 0
        self._metrics.record_event("active_request_id", value=None)
        self._metrics.record_event("active_cursor", value=0)
        self._metrics.record_event("active_chunk_size", value=0)
        self._pending_fallback_reason = reason

    # ------------------------------------------------------------------
    # B7 — safety (one call per candidate)
    # ------------------------------------------------------------------

    # (safety call inlined in tick / fallback to keep exactly one call)

    # ------------------------------------------------------------------
    # Publish + echo check (C18 / C19)
    # ------------------------------------------------------------------

    def _call_publish(
        self,
        safety_result: SafetyResult,
        command_permit: CommandPermit,
        ros_time_s: float,
        monotonic_s: float,
    ) -> ActionPublishResult:
        """Build the publish request, call the port once, echo-check (C19)."""
        self._action_seq += 1
        action_id = f"act-{self._action_seq}"
        # Propagate debug step_id to the publisher for the phase-3 callback.
        try:
            publisher_obj = getattr(self._publish_port, "__self__", None)
            if publisher_obj is not None and self._current_debug_step_id is not None:
                publisher_obj._current_step_id = self._current_debug_step_id
        except Exception:
            pass
        request = ActionPublishRequest(
            action_id=action_id,
            safety_result=safety_result,
            command_permit=command_permit,
            ros_time_s=float(ros_time_s),
            monotonic_s=float(monotonic_s),
        )
        result = self._publish_port(request)
        # PUBLISH_RESULT_INVARIANT: the port must echo our request facts.
        if result.action_id != request.action_id or result.safety_status != safety_result.status:
            self._latch_runtime_fault("PUBLISH_RESULT_INVARIANT")
        return result

    # ------------------------------------------------------------------
    # B8 — fallback (exclusive hold / continue / safe-stop)
    # ------------------------------------------------------------------

    def _run_fallback(
        self,
        reason: FallbackReason,
        command_permit: CommandPermit,
        ros_time_s: float,
        monotonic_s: float,
    ) -> Optional[ActionPublishResult]:
        """Resolve and apply a fallback (B8)."""
        self._metrics.record_event("fallback")
        self._metrics.record_event("fallback_reason", value=reason.value)

        # Fail-closed latched reasons: latch + safe-stop, no output.
        if reason in (FallbackReason.PUBLISH_PARTIAL, FallbackReason.PUBLISH_FAILED):
            self._latch_output_fault()
            self._tick_status = "OUTPUT_FAULT"
            return None
        if reason == FallbackReason.RUNTIME_FAULT:
            self._tick_status = "RUNTIME_FAULT"
            return None

        selection = select_fallback(
            reason,
            hold_action=self._last_safe_action,
            hold_source_captured_at_s=self._last_safe_source_captured_at_s,
            fallback_policy=self._config.fallback_policy,
        )
        if selection.mode == "hold" and selection.action is not None:
            # Re-run safety on the held action (one call per candidate).
            hold_selection = select_candidate(
                selection.action.as_vector(),
                previous_safe_action=self._last_safe_action,
                hold_action=self._last_safe_action,
                source="hold",
                source_captured_at_s=(
                    selection.source_captured_at_s
                    if selection.source_captured_at_s is not None
                    else 0.0
                ),
            )
            safety_result = self._safety_port.filter_action(
                hold_selection.candidate_action,
                previous_safe_action=(
                    hold_selection.previous_safe_action
                    if (command_permit.allowed and self._config.command_output_enabled)
                    else None
                ),
                latest_observation=self._observation_port(),
            )
            if safety_result.status == SafetyStatus.REJECTED or safety_result.action is None:
                self._tick_status = "FALLBACK_SAFE_STOP"
                return None
            result = self._call_publish(
                safety_result, command_permit, ros_time_s, monotonic_s
            )
            self._reduce_publish_outcome(result, safety_result, monotonic_s)
            if (
                result.outcome is PublishOutcome.PUBLISHED
                and result.command_permitted
                and result.command_publish_count > 0
                and safety_result.action is not None
            ):
                # Hold keeps the ORIGINAL source age (do not refresh).
                self._store_safe_action(safety_result.action, refresh_source=False)
                self._record_physical_command(
                    action_id=result.action_id,
                    action=safety_result.action,
                    baseline=self._observation_port(),
                    issued_at_s=monotonic_s,
                )
            self._set_tick_status_for_outcome(result.outcome)
            return result

        # safe-stop: no output this tick, recoverable (no latch).
        self._tick_status = "FALLBACK_SAFE_STOP"
        return None

    # ------------------------------------------------------------------
    # C17 / C19 / C23 / C24 / C25 — reducer + latches
    # ------------------------------------------------------------------

    def _reduce_publish_outcome(
        self,
        result: ActionPublishResult,
        safety_result: SafetyResult,
        monotonic_s: float,
    ) -> None:
        """Six-outcome fail-closed reducer (C17)."""
        self._metrics.record_event("publish", value=result.outcome.value)
        self._metrics.record_event("last_action_id", value=result.action_id)
        if result.reason_code is not None:
            self._metrics.record_event(
                "last_publish_reason_code", value=result.reason_code
            )
        if result.failure_stage is not None:
            self._metrics.record_event(
                "last_publish_failure_stage", value=result.failure_stage
            )
        if result.failed_topic is not None:
            self._metrics.record_event(
                "last_publish_failed_topic", value=result.failed_topic
            )

        outcome = result.outcome
        if outcome in (PublishOutcome.PUBLISHED, PublishOutcome.OBSERVED):
            self._clear_deferred()  # recover: allow a future delivery
        elif outcome == PublishOutcome.BLOCKED:
            self._deliver_deferred_reason(result.reason_code)
        elif outcome == PublishOutcome.REJECTED:
            self._deliver_deferred_reason(result.reason_code)
        elif outcome in (PublishOutcome.PARTIAL, PublishOutcome.FAILED):
            self._latch_output_fault()  # separate latch from runtime fault

    def _deliver_deferred_reason(self, reason: Optional[str]) -> None:
        """REJECTED/BLOCKED deferred reason, delivered exactly once (C25)."""
        if reason is None:
            return
        if self._deferred_delivered:
            return
        self._metrics.record_event("deferred_fallback", value=reason)
        self._deferred_delivered = True

    def _clear_deferred(self) -> None:
        """Successful output consumes the deferred reason (C25)."""
        self._deferred_delivered = False
        self._metrics.record_event("deferred_fallback", value=None)

    def _latch_output_fault(self) -> None:
        """PARTIAL/FAILED -> output fault latch (C23, sticky)."""
        self._metrics.record_event("output_fault_latched", value=True)

    def _latch_runtime_fault(self, reason: str) -> None:
        """Invariant violation -> runtime fault latch (C24, sticky)."""
        self._metrics.record_event("runtime_fault_latched", value=True)
        self._metrics.record_event("last_error", value=reason)

    def _record_physical_command(
        self,
        *,
        action_id: str,
        action: ActionSpec,
        baseline: Optional[ObservationSnapshot],
        issued_at_s: float,
    ) -> None:
        """Start a physical response window after a complete real publish."""
        if self._response_verifier is None:
            return
        if baseline is None:
            self._latch_runtime_fault("RESPONSE_BASELINE_MISSING")
            return
        try:
            self._response_verifier.on_published(
                action_id, action, baseline, issued_at_s
            )
        except Exception as exc:  # defensive boundary around the verifier
            self._latch_runtime_fault(f"RESPONSE_TRACKING_ERROR:{exc}")

    # ------------------------------------------------------------------
    # Safe-action bookkeeping
    # ------------------------------------------------------------------

    def _store_safe_action(self, spec: ActionSpec, *, refresh_source: bool) -> None:
        """Record the last safe action; refresh source age only on fresh output."""
        self._last_safe_action = _deep_copy_spec(spec)
        if refresh_source:
            self._last_safe_source_captured_at_s = (
                self._active_chunk_captured_at_s
                if self._active_chunk_captured_at_s is not None
                else 0.0
            )

    def _candidate_source(self) -> str:
        rid = self._active_chunk_request_id
        return f"chunk-{rid}:cursor-{self._active_cursor}"

    def _set_tick_status_for_outcome(self, outcome: PublishOutcome) -> None:
        if outcome in (PublishOutcome.PUBLISHED, PublishOutcome.OBSERVED, PublishOutcome.BLOCKED):
            self._tick_status = "NORMAL"
        elif outcome == PublishOutcome.REJECTED:
            self._tick_status = "FALLBACK"
        elif outcome in (PublishOutcome.PARTIAL, PublishOutcome.FAILED):
            self._tick_status = "OUTPUT_FAULT"

    def _finalize_runtime_status(self) -> None:
        """Single-writer priority: shutdown > runtime_fault > output_fault > tick.

        Shutdown is the highest-priority, sticky status: once requested the
        runtime_status must remain ``SHUTDOWN`` and must not be overwritten by a
        per-tick status recomputation.
        """
        if self._shutdown_requested:
            self._metrics.record_event("status", value="SHUTDOWN")
            return
        snap = self._metrics.snapshot()
        if snap.runtime_fault_latched:
            self._metrics.record_event("status", value="RUNTIME_FAULT")
        elif snap.output_fault_latched:
            self._metrics.record_event("status", value="OUTPUT_FAULT")
        else:
            self._metrics.record_event("status", value=self._tick_status)


__all__ = [
    "FallbackReason",
    "FallbackSelection",
    "select_fallback",
    "FALLBACK_MATRIX",
    "CandidateSelection",
    "select_candidate",
    "ControlLoopConfig",
    "is_action_chunk_usable",
    "build_inference_request",
    "ControlLoop",
]
