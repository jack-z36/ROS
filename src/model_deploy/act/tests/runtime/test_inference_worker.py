"""Tests for L2-06 InferenceWorker (deploy_052): serial async execution.

Covers A3/B1/B2/C22:
  - max concurrent forward == 1 (serial policy execution, spy/lock on service)
  - normal policy Exception -> terminal error C2, worker keeps running
  - clock-invalid rule (non-finite / non-decreasing) -> CLOCK_INVALID fatal
  - start-to-start rate-limit math is deterministic via injected clock
  - stop-before / stop-after policy
  - closed result queue handling (shutdown discard + invariant fatal)
  - idempotent stop
  - no live thread after clean shutdown
  - fake blocking / error inference port
"""

from __future__ import annotations

import math
import threading
import time

import pytest

from model_deploy.act.runtime.inference_channel import (
    InferenceRequest,
    InferenceResult,
    LatestQueue,
)
from model_deploy.act.runtime.inference_worker import InferenceWorker
from model_deploy.act.runtime.runtime_metrics import RuntimeMetrics
from model_deploy.act.tests.runtime.test_inference_channel import (  # reuse fixtures
    _make_chunk,
    _make_snapshot,
)
from model_deploy.act.types.action_chunk import ActionChunk
from model_deploy.act.types.observation import ObservationSnapshot


# ---------------------------------------------------------------------------
# Helpers / fakes
# ---------------------------------------------------------------------------


def _wait_until(predicate, timeout: float = 2.0, interval: float = 0.005) -> bool:
    deadline = time.monotonic() + timeout
    while not predicate():
        if time.monotonic() > deadline:
            return False
        time.sleep(interval)
    return True


def _make_request(request_id: int = 1, submitted_at_s: float = 1.0,
                  captured_at_s: float = 1.0) -> InferenceRequest:
    return InferenceRequest(
        request_id=request_id,
        observation=_make_snapshot(captured_at_s=captured_at_s),
        submitted_at_s=submitted_at_s,
        trigger_cursor=0,
    )


def _make_metrics() -> RuntimeMetrics:
    return RuntimeMetrics(clock=time.monotonic)


def _make_worker(*, service, request_queue, result_queue, metrics,
                 inference_hz: float = 10.0, clock=None) -> InferenceWorker:
    return InferenceWorker(
        service=service,
        request_queue=request_queue,
        result_queue=result_queue,
        metrics=metrics,
        inference_hz=inference_hz,
        clock=clock if clock is not None else time.monotonic,
    )


class FakeInferenceService:
    """Simple fake L2-03 port: configurable chunk, latency, failure."""

    def __init__(self, *, chunk: ActionChunk | None = None, latency_s: float = 0.0,
                 fail_with: Exception | None = None, fail_times: int = 0) -> None:
        self._chunk = chunk if chunk is not None else _make_chunk()
        self._latency_s = latency_s
        self._fail_with = fail_with
        self._fail_times = fail_times
        self.call_count = 0

    def predict_action_chunk(self, observation: ObservationSnapshot) -> ActionChunk:
        self.call_count += 1
        if self._latency_s > 0.0:
            time.sleep(self._latency_s)
        if self._fail_with is not None and self.call_count <= self._fail_times:
            raise self._fail_with
        return self._chunk


class SerialProbeService:
    """Fake L2-03 port that records concurrent forward calls (spy + lock)."""

    def __init__(self, *, chunk: ActionChunk | None = None, latency_s: float = 0.0
                 ) -> None:
        self._chunk = chunk if chunk is not None else _make_chunk()
        self._latency_s = latency_s
        self.call_count = 0
        self._lock = threading.Lock()
        self._in_flight = 0
        self._max_in_flight = 0

    def predict_action_chunk(self, observation: ObservationSnapshot) -> ActionChunk:
        self.call_count += 1
        with self._lock:
            self._in_flight += 1
            self._max_in_flight = max(self._max_in_flight, self._in_flight)
            assert self._in_flight <= 1, "service forward called concurrently"
        try:
            if self._latency_s > 0.0:
                time.sleep(self._latency_s)
            return self._chunk
        finally:
            with self._lock:
                self._in_flight -= 1


class RecordingResultQueue(LatestQueue):
    """LatestQueue that records every published result for inspection."""

    def __init__(self) -> None:
        super().__init__()
        self.published: list[InferenceResult] = []

    def put_latest(self, item: InferenceResult) -> int:  # type: ignore[override]
        dropped = super().put_latest(item)
        self.published.append(item)
        return dropped


class ScriptedClock:
    """Returns a predetermined sequence of monotonic values."""

    def __init__(self, values: list[float]) -> None:
        self._values = list(values)
        self._idx = 0

    def __call__(self) -> float:
        if self._idx < len(self._values):
            value = self._values[self._idx]
        else:
            value = self._values[-1]
        self._idx += 1
        return float(value)


class IncrementClock:
    """Returns ever-increasing values starting above request timestamps."""

    def __init__(self, start: float = 2.0, step: float = 0.01) -> None:
        self._t = start
        self._step = step

    def __call__(self) -> float:
        self._t += self._step
        return self._t


# ---------------------------------------------------------------------------
# Happy path + max concurrency
# ---------------------------------------------------------------------------


class TestHappyPathAndConcurrency:
    def test_success_publishes_result(self) -> None:
        req_q: LatestQueue = LatestQueue()
        res_q: LatestQueue = RecordingResultQueue()
        metrics = _make_metrics()
        service = FakeInferenceService()
        worker = _make_worker(
            service=service, request_queue=req_q, result_queue=res_q,
            metrics=metrics, clock=IncrementClock(),
        )
        worker.start()
        req_q.put_latest(_make_request(request_id=1))
        assert _wait_until(lambda: len(res_q.published) >= 1)
        worker.stop()
        req_q.close()
        worker.join(timeout=2.0)
        assert not worker.is_alive()
        assert service.call_count == 1
        result = res_q.published[0]
        assert result.is_success
        assert result.chunk is not None
        assert result.error_type is None
        assert metrics.snapshot().inference_success_count == 1

    def test_max_concurrency_is_one(self) -> None:
        req_q: LatestQueue = LatestQueue()
        res_q: LatestQueue = RecordingResultQueue()
        metrics = _make_metrics()
        service = SerialProbeService(latency_s=0.02)
        worker = _make_worker(
            service=service, request_queue=req_q, result_queue=res_q,
            metrics=metrics, clock=time.monotonic,
        )
        worker.start()
        try:
            # Feed + drain one at a time so the worker never evicts a result
            # (capacity 1); the slow service overlaps feeding with execution.
            for rid in range(1, 8):
                req_q.put_latest(_make_request(request_id=rid))
                assert _wait_until(lambda: len(res_q.published) >= rid)
                res_q.take_latest(timeout_s=0)  # consume so next put is clean
        finally:
            worker.stop()
            req_q.close()
            worker.join(timeout=2.0)
        assert not worker.is_alive()
        assert service.call_count == 7
        # Serial probe guarantees at most one in-flight forward at any time.
        assert service._max_in_flight == 1
        assert metrics.snapshot().inference_success_count == 7


# ---------------------------------------------------------------------------
# Error recovery: normal Exception -> terminal error, worker continues
# ---------------------------------------------------------------------------


class TestErrorRecovery:
    def test_exception_becomes_terminal_error_and_worker_continues(self) -> None:
        req_q: LatestQueue = LatestQueue()
        res_q: RecordingResultQueue = RecordingResultQueue()
        metrics = _make_metrics()
        # First call raises, every later call succeeds.
        service = FakeInferenceService(fail_with=ValueError("bad shape"), fail_times=1)
        worker = _make_worker(
            service=service, request_queue=req_q, result_queue=res_q,
            metrics=metrics, clock=IncrementClock(),
        )
        worker.start()
        try:
            # request 1 -> error
            req_q.put_latest(_make_request(request_id=1))
            assert _wait_until(lambda: len(res_q.published) >= 1)
            # worker must still be alive after a normal exception
            assert worker.is_alive()
            # consume the error result so the next put does not evict
            res_q.take_latest(timeout_s=0)

            # request 2 -> success (worker continued)
            req_q.put_latest(_make_request(request_id=2))
            assert _wait_until(lambda: len(res_q.published) >= 2)
            res_q.take_latest(timeout_s=0)
        finally:
            worker.stop()
            req_q.close()
            worker.join(timeout=2.0)

        assert not worker.is_alive()
        assert service.call_count == 2
        err, ok = res_q.published[0], res_q.published[1]
        assert not err.is_success
        assert err.error_type == "ValueError"
        assert "bad shape" in (err.error_message or "")
        assert ok.is_success
        snap = metrics.snapshot()
        assert snap.inference_error_count == 1
        assert snap.inference_success_count == 1

    def test_keyboard_interrupt_not_swallowed(self) -> None:
        req_q: LatestQueue = LatestQueue()
        res_q: LatestQueue = RecordingResultQueue()
        metrics = _make_metrics()

        class RaiseKI(FakeInferenceService):
            def predict_action_chunk(self, observation):
                raise KeyboardInterrupt()

        service = RaiseKI()
        worker = _make_worker(
            service=service, request_queue=req_q, result_queue=res_q,
            metrics=metrics, clock=IncrementClock(),
        )
        worker.start()
        req_q.put_latest(_make_request(request_id=1))
        # The worker must not silently absorb KeyboardInterrupt; it should exit
        # (the thread dies from the uncaught exception).
        assert _wait_until(lambda: not worker.is_alive(), timeout=2.0)
        assert metrics.snapshot().worker_fatal_reason is None


# ---------------------------------------------------------------------------
# Clock-invalid rule
# ---------------------------------------------------------------------------


class TestClockInvalid:
    def test_non_finite_clock_is_fatal(self) -> None:
        req_q: LatestQueue = LatestQueue()
        res_q: LatestQueue = RecordingResultQueue()
        metrics = _make_metrics()
        service = FakeInferenceService()
        worker = _make_worker(
            service=service, request_queue=req_q, result_queue=res_q,
            metrics=metrics, clock=ScriptedClock([float("nan")]),
        )
        worker.start()
        req_q.put_latest(_make_request(request_id=1))
        assert _wait_until(lambda: not worker.is_alive(), timeout=2.0)
        assert metrics.snapshot().worker_fatal_reason == "CLOCK_INVALID"
        assert service.call_count == 0

    def test_backwards_clock_is_fatal(self) -> None:
        req_q: LatestQueue = LatestQueue()
        res_q: LatestQueue = RecordingResultQueue()
        metrics = _make_metrics()
        service = FakeInferenceService(latency_s=0.0)
        # now=10.0 (ok), started=10.0 (ok), completed=5.0 (< 10.0 -> invalid)
        worker = _make_worker(
            service=service, request_queue=req_q, result_queue=res_q,
            metrics=metrics, clock=ScriptedClock([10.0, 10.0, 5.0]),
        )
        worker.start()
        req_q.put_latest(_make_request(request_id=1, submitted_at_s=9.0,
                                       captured_at_s=9.0))
        assert _wait_until(lambda: not worker.is_alive(), timeout=2.0)
        assert metrics.snapshot().worker_fatal_reason == "CLOCK_INVALID"
        assert service.call_count == 1  # started the call, failed on completed read


# ---------------------------------------------------------------------------
# Rate-limit math (deterministic via fake clock)
# ---------------------------------------------------------------------------


class TestRateLimit:
    def test_first_request_immediate(self) -> None:
        metrics = _make_metrics()
        worker = _make_worker(
            service=FakeInferenceService(), request_queue=LatestQueue(),
            result_queue=LatestQueue(), metrics=metrics, inference_hz=10.0,
            clock=IncrementClock(),
        )
        worker._last_inference_start_s = None
        assert worker._rate_limit_remaining(now=5.0) == 0.0

    def test_respects_period(self) -> None:
        metrics = _make_metrics()
        worker = _make_worker(
            service=FakeInferenceService(), request_queue=LatestQueue(),
            result_queue=LatestQueue(), metrics=metrics, inference_hz=10.0,
            clock=IncrementClock(),
        )
        worker._last_inference_start_s = 5.0
        # period = 0.1; now ahead -> 0; now behind -> positive
        assert worker._rate_limit_remaining(now=6.0) == 0.0
        assert math.isclose(worker._rate_limit_remaining(now=5.03), 0.07)
        assert math.isclose(worker._rate_limit_remaining(now=5.0), 0.1)

    def test_rate_limit_does_not_cause_errors(self) -> None:
        req_q: LatestQueue = LatestQueue()
        res_q: RecordingResultQueue = RecordingResultQueue()
        metrics = _make_metrics()
        service = FakeInferenceService()
        # Tight clock so remaining computes to ~0 each iteration.
        worker = _make_worker(
            service=service, request_queue=req_q, result_queue=res_q,
            metrics=metrics, inference_hz=100.0,
            clock=ScriptedClock([1.0, 1.0, 1.0, 2.0, 2.0, 2.0, 3.0, 3.0, 3.0]),
        )
        worker.start()
        try:
            for rid in range(1, 4):
                req_q.put_latest(_make_request(request_id=rid))
                assert _wait_until(lambda: len(res_q.published) >= rid)
                res_q.take_latest(timeout_s=0)
        finally:
            worker.stop()
            req_q.close()
            worker.join(timeout=2.0)
        assert not worker.is_alive()
        assert service.call_count == 3
        assert metrics.snapshot().worker_fatal_reason is None


# ---------------------------------------------------------------------------
# Stop semantics
# ---------------------------------------------------------------------------


class TestStop:
    def test_stop_before_policy_idle_worker_never_calls_policy(self) -> None:
        req_q: LatestQueue = LatestQueue()
        res_q: LatestQueue = RecordingResultQueue()
        metrics = _make_metrics()
        service = FakeInferenceService()
        worker = _make_worker(
            service=service, request_queue=req_q, result_queue=res_q,
            metrics=metrics, clock=IncrementClock(),
        )
        worker.start()
        # Shutdown while idle: stop + close request queue wakes the blocked take.
        worker.stop()
        req_q.close()
        assert _wait_until(lambda: not worker.is_alive(), timeout=2.0)
        assert service.call_count == 0
        assert metrics.snapshot().worker_fatal_reason is None

    def test_stop_after_policy_discards_result_and_exits(self) -> None:
        req_q: LatestQueue = LatestQueue()
        res_q: LatestQueue = RecordingResultQueue()
        metrics = _make_metrics()
        service = FakeInferenceService(latency_s=0.05)
        worker = _make_worker(
            service=service, request_queue=req_q, result_queue=res_q,
            metrics=metrics, clock=IncrementClock(),
        )
        worker.start()
        req_q.put_latest(_make_request(request_id=1))
        # Stop lands while the (slow) policy is running.
        time.sleep(0.01)
        worker.stop()
        assert _wait_until(lambda: not worker.is_alive(), timeout=2.0)
        assert service.call_count == 1
        # Late result was discarded; nothing was published.
        assert len(res_q.published) == 0
        assert metrics.snapshot().worker_fatal_reason is None

    def test_idempotent_stop(self) -> None:
        req_q: LatestQueue = LatestQueue()
        res_q: LatestQueue = RecordingResultQueue()
        metrics = _make_metrics()
        service = FakeInferenceService(latency_s=0.05)
        worker = _make_worker(
            service=service, request_queue=req_q, result_queue=res_q,
            metrics=metrics, clock=IncrementClock(),
        )
        worker.start()
        req_q.put_latest(_make_request(request_id=1))
        time.sleep(0.01)
        worker.stop()
        worker.stop()  # second call must be harmless
        assert worker._stop_event.is_set()
        req_q.close()
        assert _wait_until(lambda: not worker.is_alive(), timeout=2.0)
        assert service.call_count == 1

    def test_no_live_thread_after_clean_shutdown(self) -> None:
        req_q: LatestQueue = LatestQueue()
        res_q: LatestQueue = RecordingResultQueue()
        metrics = _make_metrics()
        service = FakeInferenceService()
        worker = _make_worker(
            service=service, request_queue=req_q, result_queue=res_q,
            metrics=metrics, clock=IncrementClock(),
        )
        worker.start()
        for rid in range(1, 4):
            req_q.put_latest(_make_request(request_id=rid))
            assert _wait_until(lambda: len(res_q.published) >= rid)
            res_q.take_latest(timeout_s=0)
        worker.stop()
        req_q.close()
        worker.join(timeout=2.0)
        assert not worker.is_alive()
        assert service.call_count == 3


# ---------------------------------------------------------------------------
# Closed result queue handling
# ---------------------------------------------------------------------------


class TestClosedResultQueue:
    def test_late_result_after_shutdown_is_discarded(self) -> None:
        req_q: LatestQueue = LatestQueue()
        res_q: LatestQueue = RecordingResultQueue()
        metrics = _make_metrics()
        service = FakeInferenceService(latency_s=0.05)
        worker = _make_worker(
            service=service, request_queue=req_q, result_queue=res_q,
            metrics=metrics, clock=IncrementClock(),
        )
        worker.start()
        req_q.put_latest(_make_request(request_id=1))
        # Close the result queue (shutdown) while policy is still running.
        time.sleep(0.01)
        res_q.close()
        worker.stop()
        # Must exit cleanly: no raise, no hang.
        assert _wait_until(lambda: not worker.is_alive(), timeout=2.0)
        assert service.call_count == 1
        assert metrics.snapshot().worker_fatal_reason is None

    def test_unexpected_closed_result_queue_is_queue_invariant(self) -> None:
        req_q: LatestQueue = LatestQueue()
        res_q: LatestQueue = RecordingResultQueue()
        metrics = _make_metrics()
        service = FakeInferenceService(latency_s=0.05)
        worker = _make_worker(
            service=service, request_queue=req_q, result_queue=res_q,
            metrics=metrics, clock=IncrementClock(),
        )
        worker.start()
        req_q.put_latest(_make_request(request_id=1))
        # Close the result queue but do NOT request stop -> invariant violation.
        time.sleep(0.01)
        res_q.close()
        assert _wait_until(lambda: not worker.is_alive(), timeout=2.0)
        assert service.call_count == 1
        snap = metrics.snapshot()
        assert snap.worker_fatal_reason == "QUEUE_INVARIANT"
        assert snap.result_queue_drop_count >= 1


# ---------------------------------------------------------------------------
# Fake blocking / error port contract
# ---------------------------------------------------------------------------


class TestFakePorts:
    def test_blocking_port_reports_latency(self) -> None:
        req_q: LatestQueue = LatestQueue()
        res_q: RecordingResultQueue = RecordingResultQueue()
        metrics = _make_metrics()
        service = FakeInferenceService(latency_s=0.05)
        worker = _make_worker(
            service=service, request_queue=req_q, result_queue=res_q,
            metrics=metrics, clock=IncrementClock(),
        )
        worker.start()
        req_q.put_latest(_make_request(request_id=1))
        assert _wait_until(lambda: len(res_q.published) >= 1)
        worker.stop()
        req_q.close()
        worker.join(timeout=2.0)
        assert res_q.published[0].is_success
        assert metrics.snapshot().last_inference_latency_s > 0.0

    def test_error_port_produces_error_result(self) -> None:
        req_q: LatestQueue = LatestQueue()
        res_q: RecordingResultQueue = RecordingResultQueue()
        metrics = _make_metrics()
        service = FakeInferenceService(fail_with=RuntimeError("boom"), fail_times=1)
        worker = _make_worker(
            service=service, request_queue=req_q, result_queue=res_q,
            metrics=metrics, clock=IncrementClock(),
        )
        worker.start()
        req_q.put_latest(_make_request(request_id=1))
        assert _wait_until(lambda: len(res_q.published) >= 1)
        worker.stop()
        req_q.close()
        worker.join(timeout=2.0)
        result = res_q.published[0]
        assert not result.is_success
        assert result.error_type == "RuntimeError"
        assert "boom" in (result.error_message or "")
