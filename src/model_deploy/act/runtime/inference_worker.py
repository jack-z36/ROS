"""InferenceWorker: daemon, single-thread, stop-aware serial inference axis.

L2-06 owns the background inference execution. This module is the A3 / B1 / B2
/ C22 micro-units of the runtime layer:

  - A3 InferenceWorker  (class state: daemon thread holding service + queues)
  - B1 run              (blocking consume latest request, start-to-start rate
                         limit, serial policy call, terminal result publish)
  - B2 _execute_request (synchronous L2-03 call -> success/error C2, never
                         kills the worker on a normal Exception)
  - C22 stop            (idempotent ``_stop_event.set()``)

Hard boundaries (do NOT implement here):
  - no ROS node, no topic publishing, no timer or publisher construction
  - no cursor / active-pending / safety / fallback / permit / publish decisions
  - no killing an in-flight policy; a late result after shutdown is discarded
  - KeyboardInterrupt / SystemExit are never swallowed

The worker consumes deploy_051's public channel (A1/C1/C2) and metrics (A2).
It calls exactly one public method on L2-03: ``ActInferenceService
.predict_action_chunk(observation) -> ActionChunk``.

Rate limiting is start-to-start and uses the injected monotonic clock only;
there is no wall-clock ``sleep`` and no busy polling. The shutdown wait reuses
``_stop_event.wait(remaining)`` which is interruptible by ``stop()``.
"""

from __future__ import annotations

import math
import threading
from typing import Callable, Optional

from model_deploy.act.runtime.inference_channel import (
    InferenceRequest,
    InferenceResult,
    LatestQueue,
)
from model_deploy.act.runtime.runtime_metrics import RuntimeMetrics
from model_deploy.act.types.action_chunk import ActionChunk
from model_deploy.act.types.observation import ObservationSnapshot

# Stable fatal reasons. They MUST map exactly to C3 FallbackReason names so a
# later B9/B3 latch can forward them without re-interpretation.
_WORKER_FATAL_CLOCK_INVALID = "CLOCK_INVALID"
_WORKER_FATAL_QUEUE_INVARIANT = "QUEUE_INVARIANT"


class InferenceWorker(threading.Thread):
    """Background serial inference worker (A3).

    A single daemon thread that consumes the latest request, calls the L2-03
    service synchronously (max concurrent forward == 1, always), and produces a
    terminal ``InferenceResult`` (success or error) into the result queue.

    Lifecycle is the standard ``threading.Thread`` contract: the owner calls
    ``start()`` after preflight, ``stop()`` to request shutdown, and ``join`` to
    wait for exit. ``daemon=True`` only guarantees the process can exit bounded
    after a ``join`` timeout; a timeout does NOT turn into a PASS.
    """

    def __init__(
        self,
        *,
        service: object,
        request_queue: LatestQueue[InferenceRequest],
        result_queue: LatestQueue[InferenceResult],
        metrics: RuntimeMetrics,
        inference_hz: float,
        clock: Callable[[], float],
    ) -> None:
        """Construct the worker with injected dependencies.

        Args:
            service: Constructed L2-03 ``ActInferenceService`` (read-only use).
            request_queue: A1 queue the ControlLoop writes requests into.
            result_queue: A1 queue the worker writes terminal results into.
            metrics: A2 runtime metrics store (worker writes only a few events).
            inference_hz: Target inference rate; period is ``1 / inference_hz``.
            clock: Injected monotonic callable (same source the ControlLoop uses).

        Raises:
            ValueError: ``inference_hz`` is not a positive finite number.
        """
        super().__init__(daemon=True, name="act_inference_worker")

        if not isinstance(inference_hz, (int, float)) or isinstance(inference_hz, bool):
            raise ValueError("inference_hz must be a positive number")
        if not math.isfinite(inference_hz) or inference_hz <= 0.0:
            raise ValueError("inference_hz must be a positive finite number")

        self._service = service
        self._request_queue = request_queue
        self._result_queue = result_queue
        self._metrics = metrics
        self._period_s = 1.0 / float(inference_hz)
        self._clock = clock

        self._stop_event = threading.Event()
        self._last_inference_start_s: Optional[float] = None
        self._last_clock_s: Optional[float] = None

    # ------------------------------------------------------------------
    # C22 stop — idempotent
    # ------------------------------------------------------------------

    def stop(self) -> None:
        """Request shutdown. Idempotent; only sets the stop event."""
        self._stop_event.set()

    # ------------------------------------------------------------------
    # B1 run — main loop
    # ------------------------------------------------------------------

    def run(self) -> None:
        """Consume requests, execute serially, publish terminal results.

        Exits when: stop is requested and observed, the request queue is closed
        (shutdown wakeup), a clock-invariant violation is detected, or a result
        queue invariant violation is detected. The worker never raises out of
        ``run`` on a normal policy exception.
        """
        while not self._stop_event.is_set():
            # C9 blocking take. A closed queue returns None -> shutdown.
            request = self._request_queue.take_latest(timeout_s=None)
            if request is None:
                return

            # Stop-aware: do not start a policy run after stop was requested.
            if self._stop_event.is_set():
                return

            now = self._read_clock()
            if now is None:
                return  # fatal reason already recorded (CLOCK_INVALID)

            remaining = self._rate_limit_remaining(now)
            self._last_inference_start_s = now
            if remaining > 0.0:
                self._stop_event.wait(remaining)
                if self._stop_event.is_set():
                    return

            # Re-check stop before committing to a (non-killable) policy call.
            if self._stop_event.is_set():
                return

            result = self._execute_request(request)
            if result is None:
                return  # fatal clock reason already recorded

            # Policy finished; if stop landed during execution, discard and exit.
            if self._stop_event.is_set():
                return

            if self._publish_result(result):
                return  # fatal queue-invariant recorded; terminate the loop

    # ------------------------------------------------------------------
    # B2 execute — synchronous policy call -> terminal C2
    # ------------------------------------------------------------------

    def _execute_request(self, request: InferenceRequest) -> Optional[InferenceResult]:
        """Run the L2-03 service synchronously and build a terminal result.

        A normal ``Exception`` becomes an ``InferenceResult.error``; the worker
        keeps running. ``KeyboardInterrupt`` / ``SystemExit`` are re-raised.

        Returns ``None`` only when a clock read failed (fatal reason recorded);
        the caller must exit the run loop.
        """
        started_at_s = self._read_clock()
        if started_at_s is None:
            return None

        try:
            chunk: ActionChunk = self._service.predict_action_chunk(
                request.observation
            )
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception as exc:
            completed_at_s = self._read_clock()
            if completed_at_s is None:
                return None
            self._metrics.record_event("inference_error")
            return InferenceResult.error(
                request_id=request.request_id,
                observation_captured_at_s=request.observation.captured_at_s,
                submitted_at_s=request.submitted_at_s,
                started_at_s=started_at_s,
                completed_at_s=completed_at_s,
                exc=exc,
            )
        else:
            completed_at_s = self._read_clock()
            if completed_at_s is None:
                return None
            self._metrics.record_event("inference_success")
            self._metrics.record_event(
                "latency", value=completed_at_s - started_at_s
            )
            return InferenceResult.success(
                request_id=request.request_id,
                observation_captured_at_s=request.observation.captured_at_s,
                submitted_at_s=request.submitted_at_s,
                started_at_s=started_at_s,
                completed_at_s=completed_at_s,
                chunk=chunk,
            )

    # ------------------------------------------------------------------
    # Result publishing + closed-queue / late-result handling
    # ------------------------------------------------------------------

    def _publish_result(self, result: InferenceResult) -> bool:
        """Put the terminal result; discard on shutdown close, fatal otherwise.

        A ``RuntimeError`` from ``put_latest`` means the result queue was closed.
        During shutdown (stop set) the late result is simply discarded and the
        worker exits cleanly via the stop check. Outside shutdown an unexpected
        close is an invariant violation that terminates the worker.

        A normal eviction (``dropped > 0``) of an unconsumed result at capacity
        1 + single outstanding is also an invariant violation in normal
        operation and terminates the worker.

        Returns ``True`` when the run loop must terminate (fatal recorded).
        """
        try:
            dropped = self._result_queue.put_latest(result)
        except RuntimeError:
            # Closed result queue: never raise, never hang.
            if self._stop_event.is_set():
                return False  # shutdown discard; loop exits via stop check
            self._metrics.record_event("result_queue_drop", value=1)
            self._fatal(_WORKER_FATAL_QUEUE_INVARIANT)
            return True

        if dropped and not self._stop_event.is_set():
            self._metrics.record_event("result_queue_drop", value=dropped)
            self._fatal(_WORKER_FATAL_QUEUE_INVARIANT)
            return True

        return False

    # ------------------------------------------------------------------
    # Clock validation (finite / non-negative / non-decreasing)
    # ------------------------------------------------------------------

    def _read_clock(self) -> Optional[float]:
        """Read the injected clock, validating the worker timestamp contract.

        Any non-finite, negative, or backwards read records a stable
        ``CLOCK_INVALID`` fatal reason and returns ``None`` (caller exits).
        """
        try:
            value = self._clock()
        except Exception:
            self._fatal(_WORKER_FATAL_CLOCK_INVALID)
            return None

        if value is None or isinstance(value, bool) or not isinstance(value, (int, float)):
            self._fatal(_WORKER_FATAL_CLOCK_INVALID)
            return None
        if not math.isfinite(value) or value < 0.0:
            self._fatal(_WORKER_FATAL_CLOCK_INVALID)
            return None
        if self._last_clock_s is not None and value < self._last_clock_s:
            self._fatal(_WORKER_FATAL_CLOCK_INVALID)
            return None

        self._last_clock_s = float(value)
        return self._last_clock_s

    # ------------------------------------------------------------------
    # Rate-limit helper (deterministic, clock-driven)
    # ------------------------------------------------------------------

    def _rate_limit_remaining(self, now: float) -> float:
        """Start-to-start remaining wait before the next policy run.

        ``max(0, last_start + period - now)``. The first request (no previous
        start) waits zero — it runs immediately.
        """
        if self._last_inference_start_s is None:
            return 0.0
        return max(0.0, self._last_inference_start_s + self._period_s - now)

    # ------------------------------------------------------------------
    # Fatal reason writer (worker-fatal only; never writes runtime_status)
    # ------------------------------------------------------------------

    def _fatal(self, reason: str) -> None:
        """Record a stable worker fatal reason via A2 (cross-thread safe)."""
        self._metrics.record_event("worker_fatal_reason", value=reason)
