"""Tests for L2-06 inference channel: envelopes and LatestQueue (deploy_051).

Covers:
  - C1/C2 InferenceRequest / InferenceResult success-error XOR, id and time contract.
  - A1/C5/C8-C10 LatestQueue: capacity=1, put/take, close/timeout/spurious wakeup,
    bounded drop classification (normal eviction vs shutdown clear).
"""

from __future__ import annotations

import threading
import time

import numpy as np
import pytest

from model_deploy.act.runtime.inference_channel import (
    InferenceRequest,
    InferenceResult,
    LatestQueue,
)
from model_deploy.act.types.action_chunk import ActionChunk
from model_deploy.act.types.observation import ObservationSnapshot, ObservationState


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_state() -> ObservationState:
    return ObservationState(
        left_tcp_position=np.array([0.1, 0.2, 0.3], dtype=np.float32),
        left_tcp_orientation=np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float32),
        left_gripper_width=0.05,
        right_tcp_position=np.array([0.4, 0.5, 0.6], dtype=np.float32),
        right_tcp_orientation=np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float32),
        right_gripper_width=0.08,
    )


def _make_snapshot(captured_at_s: float = 1.0) -> ObservationSnapshot:
    return ObservationSnapshot(
        images={"cam_high": np.zeros((2, 2, 3), dtype=np.uint8)},
        state=_make_state(),
        encoded_state=np.zeros(16, dtype=np.float32),
        captured_at_s=captured_at_s,
    )


def _make_chunk() -> ActionChunk:
    return ActionChunk(actions=np.zeros((10, 16), dtype=np.float32))


def _success_result(request_id: int = 1) -> InferenceResult:
    return InferenceResult.success(
        request_id=request_id,
        observation_captured_at_s=1.0,
        submitted_at_s=1.1,
        started_at_s=1.2,
        completed_at_s=1.3,
        chunk=_make_chunk(),
    )


# ---------------------------------------------------------------------------
# C1 / C2 envelope contract
# ---------------------------------------------------------------------------


class TestInferenceRequest:
    def test_valid_request(self) -> None:
        req = InferenceRequest(
            request_id=1,
            observation=_make_snapshot(),
            submitted_at_s=2.0,
            trigger_cursor=0,
        )
        assert req.request_id == 1
        assert req.submitted_at_s == 2.0
        assert req.trigger_cursor == 0

    @pytest.mark.parametrize("request_id", [0, -1, "x"])
    def test_invalid_request_id(self, request_id: object) -> None:
        with pytest.raises(ValueError):
            InferenceRequest(
                request_id=request_id,  # type: ignore[arg-type]
                observation=_make_snapshot(),
                submitted_at_s=2.0,
                trigger_cursor=0,
            )

    def test_negative_submit_time(self) -> None:
        with pytest.raises(ValueError):
            InferenceRequest(
                request_id=1,
                observation=_make_snapshot(),
                submitted_at_s=-2.0,
                trigger_cursor=0,
            )


class TestInferenceResult:
    def test_success_has_chunk_no_error(self) -> None:
        res = _success_result()
        assert res.is_success
        assert res.chunk is not None
        assert res.error_type is None
        assert res.error_message is None

    def test_error_has_no_chunk(self) -> None:
        res = InferenceResult.error(
            request_id=1,
            observation_captured_at_s=1.0,
            submitted_at_s=1.1,
            started_at_s=1.2,
            completed_at_s=1.3,
            exc=RuntimeError("boom"),
        )
        assert not res.is_success
        assert res.chunk is None
        assert res.error_type == "RuntimeError"
        assert "boom" in (res.error_message or "")

    def test_success_and_error_is_invalid(self) -> None:
        with pytest.raises(ValueError):
            InferenceResult(
                request_id=1,
                observation_captured_at_s=1.0,
                submitted_at_s=1.1,
                started_at_s=1.2,
                completed_at_s=1.3,
                chunk=_make_chunk(),
                error_type="X",
                error_message="y",
            )

    def test_neither_success_nor_error_is_invalid(self) -> None:
        with pytest.raises(ValueError):
            InferenceResult(
                request_id=1,
                observation_captured_at_s=1.0,
                submitted_at_s=1.1,
                started_at_s=1.2,
                completed_at_s=1.3,
            )

    def test_failure_requires_nonempty_error(self) -> None:
        with pytest.raises(ValueError):
            InferenceResult(
                request_id=1,
                observation_captured_at_s=1.0,
                submitted_at_s=1.1,
                started_at_s=1.2,
                completed_at_s=1.3,
                error_type="",
                error_message="",
            )

    def test_time_ordering_enforced(self) -> None:
        with pytest.raises(ValueError):
            InferenceResult.success(
                request_id=1,
                observation_captured_at_s=1.0,
                submitted_at_s=2.0,  # submitted after started -> invalid order
                started_at_s=1.2,
                completed_at_s=1.3,
                chunk=_make_chunk(),
            )

    def test_error_message_truncated_to_512(self) -> None:
        long_msg = "e" * 1000
        res = InferenceResult.error(
            request_id=1,
            observation_captured_at_s=1.0,
            submitted_at_s=1.1,
            started_at_s=1.2,
            completed_at_s=1.3,
            exc=RuntimeError(long_msg),
        )
        assert len(res.error_message or "") == 512

    def test_error_factory_uses_exception_name(self) -> None:
        res = InferenceResult.error(
            request_id=7,
            observation_captured_at_s=0.5,
            submitted_at_s=0.6,
            started_at_s=0.7,
            completed_at_s=0.8,
            exc=ValueError("bad shape"),
        )
        assert res.request_id == 7
        assert res.error_type == "ValueError"


# ---------------------------------------------------------------------------
# A1 / C5 / C8-C10 LatestQueue
# ---------------------------------------------------------------------------


class TestLatestQueueBasics:
    def test_capacity_is_one(self) -> None:
        q: LatestQueue[int] = LatestQueue()
        assert q.CAPACITY == 1

    def test_no_arg_constructor(self) -> None:
        q: LatestQueue[int] = LatestQueue()
        assert not q.is_closed

    def test_put_then_take(self) -> None:
        q: LatestQueue[int] = LatestQueue()
        assert q.put_latest(1) == 0
        assert q.take_latest(0) == 1
        assert q.take_latest(0) is None

    def test_capacity_one_evicts(self) -> None:
        q: LatestQueue[int] = LatestQueue()
        assert q.put_latest(1) == 0
        # second put evicts the first -> dropped == 1
        assert q.put_latest(2) == 1
        assert q.take_latest(0) == 2  # only the latest survives
        assert q.take_latest(0) is None

    def test_take_nonblocking_empty_returns_none(self) -> None:
        q: LatestQueue[int] = LatestQueue()
        assert q.take_latest(0) is None

    def test_negative_timeout_rejected(self) -> None:
        q: LatestQueue[int] = LatestQueue()
        with pytest.raises(ValueError):
            q.take_latest(timeout_s=-1.0)


class TestLatestQueueClose:
    def test_put_after_close_raises(self) -> None:
        q: LatestQueue[int] = LatestQueue()
        q.close()
        with pytest.raises(RuntimeError) as exc:
            q.put_latest(1)
        assert "queue is closed" in str(exc.value)

    def test_close_is_idempotent(self) -> None:
        q: LatestQueue[int] = LatestQueue()
        assert q.close() == 0
        assert q.close() == 0  # repeated close counts nothing

    def test_close_clears_and_counts(self) -> None:
        q: LatestQueue[int] = LatestQueue()
        q.put_latest(1)
        q.put_latest(2)  # evict 1, dropped=1
        cleared = q.close()
        assert cleared == 1  # one pending item cleared

    def test_take_after_close_returns_none_no_residual(self) -> None:
        q: LatestQueue[int] = LatestQueue()
        q.put_latest(42)
        q.close()
        assert q.take_latest(0) is None  # closed queue never delivers residual

    def test_drop_sources_are_distinct_return_channels(self) -> None:
        # Normal eviction (via put_latest return) and shutdown clear (via
        # close return) are two distinct counts. The queue tracks them
        # cumulatively in ``dropped_count``; the caller routes each return
        # value to a distinct metrics counter (verified in test_runtime_metrics).
        q: LatestQueue[int] = LatestQueue()
        q.put_latest(1)
        assert q.put_latest(2) == 1  # normal eviction -> request_queue_drop
        assert q.dropped_count == 1
        q.put_latest(3)
        assert q.dropped_count == 2  # two normal evictions so far
        assert q.close() == 1  # shutdown clear -> shutdown_queue_cleared
        assert q.dropped_count == 3  # cumulative: 2 evictions + 1 clear


class TestLatestQueueTimeoutWakeup:
    def test_blocking_take_receives_item(self) -> None:
        q: LatestQueue[int] = LatestQueue()
        result: list[int] = []

        def worker() -> None:
            result.append(q.take_latest(timeout_s=None))  # blocking

        t = threading.Thread(target=worker)
        t.start()
        time.sleep(0.05)
        q.put_latest(99)
        t.join(timeout=2.0)
        assert not t.is_alive()
        assert result == [99]

    def test_bounded_timeout_returns_none(self) -> None:
        q: LatestQueue[int] = LatestQueue()
        start = time.monotonic()
        assert q.take_latest(timeout_s=0.1) is None
        elapsed = time.monotonic() - start
        assert 0.05 <= elapsed < 1.0  # bounded, no busy polling

    def test_spurious_wakeup_does_not_lose_item(self) -> None:
        # A notify without an item (spurious wakeup) must NOT make a blocked
        # take_latest return early; it must keep waiting until a real item/close.
        q: LatestQueue[int] = LatestQueue()
        result: list[object] = []

        def worker() -> None:
            result.append(q.take_latest(timeout_s=None))

        t = threading.Thread(target=worker)
        t.start()
        time.sleep(0.05)
        # Spurious wakeup: notify waiters without placing an item.
        with q._condition:
            q._condition.notify_all()
        time.sleep(0.05)
        assert result == []  # still waiting
        q.put_latest(7)
        t.join(timeout=2.0)
        assert not t.is_alive()
        assert result == [7]
