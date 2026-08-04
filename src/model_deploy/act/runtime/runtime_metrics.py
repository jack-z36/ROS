"""RuntimeMetrics: thread-safe L2-06 runtime metrics and immutable snapshot.

L2-06 owns the worker/loop observable state. This module provides a lock-guarded
mutable metrics store (A2 / C6), a single ``record_event`` mutator (C11), and a
frozen ``RuntimeMetricsSnapshot`` (C4) produced by ``snapshot`` (C12). The
snapshot is a fresh copy — no mutable reference to the internal state is ever
exposed.

The field set matches ``02_implement/.../agent_context/10_runtime层设计.md §3``.
Only L2-06 runtime lifecycle is recorded here; business-language types (ActionChunk,
SafetyResult, ...) are not touched.

Micro-units:
  - A2 RuntimeMetrics            (class packing lock-guarded state + clock)
  - C4 RuntimeMetricsSnapshot    (frozen data)
  - C6 metrics state             (guarded mutable counters/gauges)
  - C11 record_event             (atomic increment / replace under lock)
  - C12 snapshot                 (guarded deep copy -> C4)
"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Callable, Optional, Tuple

# ---------------------------------------------------------------------------
# C4 RuntimeMetricsSnapshot — frozen, immutable copy
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RuntimeMetricsSnapshot:
    """Immutable, cross-thread-safe view of L2-06 runtime metrics.

    dict-like fields (publish_outcome_counts, last_safety_finding_codes) are
    delivered as tuple pairs / tuples so the snapshot carries no mutable alias.
    """

    runtime_status: str = "STARTING"
    tick_count: int = 0
    request_submitted_count: int = 0
    inference_success_count: int = 0
    inference_error_count: int = 0
    result_discarded_count: int = 0
    chunk_activated_count: int = 0
    request_queue_drop_count: int = 0
    result_queue_drop_count: int = 0
    shutdown_queue_cleared_count: int = 0
    action_candidate_count: int = 0
    safety_rejected_count: int = 0
    fallback_count: int = 0
    publish_outcome_counts: Tuple[Tuple[str, int], ...] = ()
    active_request_id: Optional[int] = None
    pending_request_id: Optional[int] = None
    in_flight_request_id: Optional[int] = None
    active_cursor: int = 0
    active_chunk_size: int = 0
    output_fault_latched: bool = False
    runtime_fault_latched: bool = False
    worker_fatal_reason: Optional[str] = None
    last_fallback_reason: Optional[str] = None
    deferred_fallback_reason: Optional[str] = None
    last_action_id: Optional[str] = None
    last_candidate_source: Optional[str] = None
    last_candidate_source_captured_at_s: Optional[float] = None
    last_safety_finding_codes: Tuple[str, ...] = ()
    last_publish_outcome: Optional[str] = None
    last_publish_reason_code: Optional[str] = None
    last_publish_failure_stage: Optional[str] = None
    last_publish_failed_topic: Optional[str] = None
    last_response_detail: Optional[str] = None
    last_error: Optional[str] = None
    last_inference_latency_s: float = 0.0
    updated_at_s: float = 0.0


# ---------------------------------------------------------------------------
# C6 mutable state + A2 RuntimeMetrics
# ---------------------------------------------------------------------------


def _new_state(clock: Callable[[], float]) -> dict:
    return {
        "runtime_status": "STARTING",
        "tick_count": 0,
        "request_submitted_count": 0,
        "inference_success_count": 0,
        "inference_error_count": 0,
        "result_discarded_count": 0,
        "chunk_activated_count": 0,
        "request_queue_drop_count": 0,
        "result_queue_drop_count": 0,
        "shutdown_queue_cleared_count": 0,
        "action_candidate_count": 0,
        "safety_rejected_count": 0,
        "fallback_count": 0,
        "publish_outcome_counts": {},
        "active_request_id": None,
        "pending_request_id": None,
        "in_flight_request_id": None,
        "active_cursor": 0,
        "active_chunk_size": 0,
        "output_fault_latched": False,
        "runtime_fault_latched": False,
        "worker_fatal_reason": None,
        "last_fallback_reason": None,
        "deferred_fallback_reason": None,
        "last_action_id": None,
        "last_candidate_source": None,
        "last_candidate_source_captured_at_s": None,
        "last_safety_finding_codes": (),
        "last_publish_outcome": None,
        "last_publish_reason_code": None,
        "last_publish_failure_stage": None,
        "last_publish_failed_topic": None,
        "last_response_detail": None,
        "last_error": None,
        "last_inference_latency_s": 0.0,
        "updated_at_s": clock(),
    }


# Each handler mutates ``state`` under the caller's lock.
# Counter events ignore ``value``; drop events accept an optional int amount.


def _ev_tick(s, _v): s["tick_count"] += 1


def _ev_request_submitted(s, _v): s["request_submitted_count"] += 1


def _ev_inference_success(s, _v): s["inference_success_count"] += 1


def _ev_inference_error(s, _v): s["inference_error_count"] += 1


def _ev_result_discarded(s, _v): s["result_discarded_count"] += 1


def _ev_chunk_activated(s, _v): s["chunk_activated_count"] += 1


def _ev_request_queue_drop(s, v):
    s["request_queue_drop_count"] += v if isinstance(v, int) else 1


def _ev_result_queue_drop(s, v):
    s["result_queue_drop_count"] += v if isinstance(v, int) else 1


def _ev_shutdown_queue_cleared(s, v):
    s["shutdown_queue_cleared_count"] += v if isinstance(v, int) else 1


def _ev_action_candidate(s, _v): s["action_candidate_count"] += 1


def _ev_safety_rejected(s, _v): s["safety_rejected_count"] += 1


def _ev_fallback(s, _v): s["fallback_count"] += 1


def _ev_publish(s, v):
    if not isinstance(v, str):
        raise ValueError("publish event requires an outcome string")
    counts = dict(s["publish_outcome_counts"])
    counts[v] = counts.get(v, 0) + 1
    s["publish_outcome_counts"] = counts
    s["last_publish_outcome"] = v


def _ev_status(s, v):
    if not isinstance(v, str):
        raise ValueError("status event requires a string")
    s["runtime_status"] = v


def _ev_latency(s, v):
    if not isinstance(v, (int, float)):
        raise ValueError("latency event requires a number")
    s["last_inference_latency_s"] = max(0.0, float(v))


def _ev_last_error(s, v): s["last_error"] = v


def _ev_worker_fatal(s, v): s["worker_fatal_reason"] = v


def _ev_fallback_reason(s, v): s["last_fallback_reason"] = v


def _ev_deferred_fallback(s, v): s["deferred_fallback_reason"] = v


def _ev_active_request_id(s, v): s["active_request_id"] = v


def _ev_pending_request_id(s, v): s["pending_request_id"] = v


def _ev_in_flight_request_id(s, v): s["in_flight_request_id"] = v


def _ev_active_cursor(s, v): s["active_cursor"] = int(v)


def _ev_active_chunk_size(s, v): s["active_chunk_size"] = int(v)


def _ev_last_action_id(s, v): s["last_action_id"] = v


def _ev_last_candidate_source(s, v): s["last_candidate_source"] = v


def _ev_last_candidate_source_time(s, v): s["last_candidate_source_captured_at_s"] = v


def _ev_last_safety_findings(s, v): s["last_safety_finding_codes"] = tuple(v)


def _ev_last_publish_reason_code(s, v): s["last_publish_reason_code"] = v


def _ev_last_publish_failure_stage(s, v): s["last_publish_failure_stage"] = v


def _ev_last_publish_failed_topic(s, v): s["last_publish_failed_topic"] = v


def _ev_last_response_detail(s, v): s["last_response_detail"] = v


def _ev_output_fault_latched(s, v): s["output_fault_latched"] = bool(v)


def _ev_runtime_fault_latched(s, v): s["runtime_fault_latched"] = bool(v)


_EVENT_HANDLERS = {
    "tick": _ev_tick,
    "request_submitted": _ev_request_submitted,
    "inference_success": _ev_inference_success,
    "inference_error": _ev_inference_error,
    "result_discarded": _ev_result_discarded,
    "chunk_activated": _ev_chunk_activated,
    "request_queue_drop": _ev_request_queue_drop,
    "result_queue_drop": _ev_result_queue_drop,
    "shutdown_queue_cleared": _ev_shutdown_queue_cleared,
    "action_candidate": _ev_action_candidate,
    "safety_rejected": _ev_safety_rejected,
    "fallback": _ev_fallback,
    "publish": _ev_publish,
    "status": _ev_status,
    "latency": _ev_latency,
    "last_error": _ev_last_error,
    "worker_fatal_reason": _ev_worker_fatal,
    "fallback_reason": _ev_fallback_reason,
    "deferred_fallback": _ev_deferred_fallback,
    "active_request_id": _ev_active_request_id,
    "pending_request_id": _ev_pending_request_id,
    "in_flight_request_id": _ev_in_flight_request_id,
    "active_cursor": _ev_active_cursor,
    "active_chunk_size": _ev_active_chunk_size,
    "last_action_id": _ev_last_action_id,
    "last_candidate_source": _ev_last_candidate_source,
    "last_candidate_source_time": _ev_last_candidate_source_time,
    "last_safety_findings": _ev_last_safety_findings,
    "last_publish_reason_code": _ev_last_publish_reason_code,
    "last_publish_failure_stage": _ev_last_publish_failure_stage,
    "last_publish_failed_topic": _ev_last_publish_failed_topic,
    "last_response_detail": _ev_last_response_detail,
    "output_fault_latched": _ev_output_fault_latched,
    "runtime_fault_latched": _ev_runtime_fault_latched,
}


class RuntimeMetrics:
    """Thread-safe L2-06 runtime metrics store.

    Args:
        clock: Monotonic callable injected by the UI layer (same source the
            ControlLoop uses). Updated on every ``record_event`` and snapshot.
    """

    def __init__(self, clock: Callable[[], float]) -> None:
        self._clock = clock
        self._lock = threading.Lock()
        self._state = _new_state(clock)

    # ---- C11 record_event ------------------------------------------------

    def record_event(self, event: str, *, value: object = None) -> None:
        """Atomically apply a metrics event under the internal lock.

        Counter events (tick, request_submitted, inference_success, ...) ignore
        ``value``. Drop events accept an optional integer amount. Gauge/string
        events take the new value via ``value``.
        """
        handler = _EVENT_HANDLERS.get(event)
        if handler is None:
            raise ValueError(f"unknown metrics event: {event}")
        with self._lock:
            handler(self._state, value)
            self._state["updated_at_s"] = self._clock()

    # ---- C12 snapshot ----------------------------------------------------

    def snapshot(self) -> RuntimeMetricsSnapshot:
        """Return a fresh frozen copy; never exposes a mutable alias."""
        with self._lock:
            s = self._state
            return RuntimeMetricsSnapshot(
                runtime_status=s["runtime_status"],
                tick_count=s["tick_count"],
                request_submitted_count=s["request_submitted_count"],
                inference_success_count=s["inference_success_count"],
                inference_error_count=s["inference_error_count"],
                result_discarded_count=s["result_discarded_count"],
                chunk_activated_count=s["chunk_activated_count"],
                request_queue_drop_count=s["request_queue_drop_count"],
                result_queue_drop_count=s["result_queue_drop_count"],
                shutdown_queue_cleared_count=s["shutdown_queue_cleared_count"],
                action_candidate_count=s["action_candidate_count"],
                safety_rejected_count=s["safety_rejected_count"],
                fallback_count=s["fallback_count"],
                publish_outcome_counts=tuple(sorted(s["publish_outcome_counts"].items())),
                active_request_id=s["active_request_id"],
                pending_request_id=s["pending_request_id"],
                in_flight_request_id=s["in_flight_request_id"],
                active_cursor=s["active_cursor"],
                active_chunk_size=s["active_chunk_size"],
                output_fault_latched=s["output_fault_latched"],
                runtime_fault_latched=s["runtime_fault_latched"],
                worker_fatal_reason=s["worker_fatal_reason"],
                last_fallback_reason=s["last_fallback_reason"],
                deferred_fallback_reason=s["deferred_fallback_reason"],
                last_action_id=s["last_action_id"],
                last_candidate_source=s["last_candidate_source"],
                last_candidate_source_captured_at_s=s["last_candidate_source_captured_at_s"],
                last_safety_finding_codes=tuple(s["last_safety_finding_codes"]),
                last_publish_outcome=s["last_publish_outcome"],
                last_publish_reason_code=s["last_publish_reason_code"],
                last_publish_failure_stage=s["last_publish_failure_stage"],
                last_publish_failed_topic=s["last_publish_failed_topic"],
                last_response_detail=s["last_response_detail"],
                last_error=s["last_error"],
                last_inference_latency_s=s["last_inference_latency_s"],
                updated_at_s=s["updated_at_s"],
            )
