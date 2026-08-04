"""Inference channel: frozen request/result envelopes and LatestQueue.

L2-06 owns the request/result correlation, the latest-only queue, and the
thread-safe RAM channel between the ControlLoop (producer of requests) and the
InferenceWorker (producer of results). This module deliberately contains no
ROS dependency, no policy call, no safety call, and no topic publishing.

Micro-units implemented here (L2-06 agent_context numbering):
  - C1 InferenceRequest  (frozen data)
  - C2 InferenceResult   (frozen data, success/error XOR)
  - A1 LatestQueue        (class packing bounded deque + Condition + closed)
  - C5 queue state        (deque / Condition / closed / dropped)
  - C8 put_latest         (replace + append, return dropped count, wake waiter)
  - C9 take_latest        (non-blocking/blocking/bounded timeout, spurious-safe)
  - C10 close             (idempotent clear + count + wake, forbid later put)
"""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass
from threading import Condition
from typing import Deque, Generic, Optional, TypeVar

from model_deploy.act.types.action_chunk import ActionChunk
from model_deploy.act.types.observation import ObservationSnapshot

T = TypeVar("T")

_QUEUE_CLOSED_MSG = "queue is closed"
_ERROR_MSG_LIMIT = 512


# ---------------------------------------------------------------------------
# C1 InferenceRequest — frozen request envelope
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class InferenceRequest:
    """Frozen request envelope submitted by the ControlLoop to the worker.

    Attributes:
        request_id:     Monotonic positive integer identifying this request.
        observation:    The ObservationSnapshot payload (L2-02, read-only).
        submitted_at_s: Monotonic submit time (seconds), finite and >= 0.
        trigger_cursor: Active cursor at submit time, non-negative integer.
    """

    request_id: int
    observation: ObservationSnapshot
    submitted_at_s: float
    trigger_cursor: int

    def __post_init__(self) -> None:
        if not isinstance(self.request_id, int) or self.request_id <= 0:
            raise ValueError("request_id must be a positive integer")
        if not isinstance(self.submitted_at_s, (int, float)) or self.submitted_at_s < 0:
            raise ValueError("submitted_at_s must be a finite non-negative number")
        if not isinstance(self.trigger_cursor, int) or self.trigger_cursor < 0:
            raise ValueError("trigger_cursor must be a non-negative integer")


# ---------------------------------------------------------------------------
# C2 InferenceResult — frozen result envelope
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class InferenceResult:
    """Frozen result envelope produced by the worker for the ControlLoop.

    success:  ``chunk is not None`` and ``error_type/error_message`` are ``None``.
    failure:  ``chunk is None`` and ``error_type/error_message`` are non-empty.

    Invariants (enforced at construction):
      - success / error are mutually exclusive (XOR).
      - ``observation_captured_at_s <= submitted_at_s <= started_at_s
         <= completed_at_s``.
      - No exception, traceback, policy or ROS object is stored.
    """

    request_id: int
    observation_captured_at_s: float
    submitted_at_s: float
    started_at_s: float
    completed_at_s: float
    chunk: Optional[ActionChunk] = None
    error_type: Optional[str] = None
    error_message: Optional[str] = None

    def __post_init__(self) -> None:
        is_success = self.chunk is not None
        has_error = self.error_type is not None or self.error_message is not None
        if is_success == has_error:
            raise ValueError(
                "InferenceResult must be exactly one of: success (chunk set, "
                "no error) or failure (chunk None, error_type/error_message set)"
            )
        if not is_success and not (self.error_type and self.error_message):
            raise ValueError(
                "failure result requires non-empty error_type and error_message"
            )

        times = (
            self.observation_captured_at_s,
            self.submitted_at_s,
            self.started_at_s,
            self.completed_at_s,
        )
        for t in times:
            if not isinstance(t, (int, float)) or t < 0:
                raise ValueError("all timestamps must be finite non-negative numbers")
        if not (times[0] <= times[1] <= times[2] <= times[3]):
            raise ValueError(
                "timestamps must be ordered: observation_captured_at_s <= "
                "submitted_at_s <= started_at_s <= completed_at_s"
            )

    @property
    def is_success(self) -> bool:
        """True when this is a successful result carrying a chunk."""
        return self.chunk is not None

    @classmethod
    def success(
        cls,
        *,
        request_id: int,
        observation_captured_at_s: float,
        submitted_at_s: float,
        started_at_s: float,
        completed_at_s: float,
        chunk: ActionChunk,
    ) -> "InferenceResult":
        """Build a success envelope from a produced ActionChunk."""
        return cls(
            request_id=request_id,
            observation_captured_at_s=observation_captured_at_s,
            submitted_at_s=submitted_at_s,
            started_at_s=started_at_s,
            completed_at_s=completed_at_s,
            chunk=chunk,
            error_type=None,
            error_message=None,
        )

    @classmethod
    def error(
        cls,
        *,
        request_id: int,
        observation_captured_at_s: float,
        submitted_at_s: float,
        started_at_s: float,
        completed_at_s: float,
        exc: Exception,
    ) -> "InferenceResult":
        """Build a failure envelope from a caught exception.

        Only the stable exception class name and a bounded message are kept;
        the exception object / traceback are never stored.
        """
        error_type = type(exc).__name__
        error_message = str(exc) or error_type
        return cls(
            request_id=request_id,
            observation_captured_at_s=observation_captured_at_s,
            submitted_at_s=submitted_at_s,
            started_at_s=started_at_s,
            completed_at_s=completed_at_s,
            chunk=None,
            error_type=error_type,
            error_message=error_message[:_ERROR_MSG_LIMIT],
        )


# ---------------------------------------------------------------------------
# A1 LatestQueue — bounded latest-only channel (capacity fixed at 1)
# ---------------------------------------------------------------------------


class LatestQueue(Generic[T]):
    """Bounded latest-only channel owned by L2-06.

    Contract (mirrors the Pi0.5 LatestQueue structure but adds a stable close /
    wakeup / drop contract):

        put_latest(item) -> int
            Replace-and-append the newest item, wake any waiter, and return the
            number of items evicted by this call (0 or 1 at capacity 1).
            Raises ``RuntimeError("queue is closed")`` once closed.

        take_latest(timeout_s=0) -> T | None
            - ``timeout_s is None``: block until an item is available or the
              queue is closed (then returns ``None``).
            - ``timeout_s == 0``: non-blocking; return the item or ``None``.
            - ``timeout_s > 0``: bounded monotonic wait.
            A closed queue never delivers a residual (pre-close) item.
            Uses a ``while`` loop so spurious wakeups are handled.

        close() -> int
            Idempotent. Under the same Condition critical section: set
            ``_closed=True``, clear all pending items, add the cleared count to
            the dropped total, ``notify_all()`` and return the cleared count.
            Repeated close returns 0 and does not double-count.

    The drop classification is left to the caller: ``put_latest``'s return value
    is the normal-eviction count, ``close``'s return value is the shutdown-clear
    count. They are routed to distinct metrics counters by the ControlLoop.
    """

    CAPACITY: int = 1

    def __init__(self) -> None:
        self._items: Deque[T] = deque(maxlen=self.CAPACITY)
        self._condition: Condition = Condition()
        self._closed: bool = False
        self._dropped_count: int = 0

    # ---- C8 put_latest ---------------------------------------------------

    def put_latest(self, item: T) -> int:
        """Insert the latest item; evict the old one at capacity, return dropped."""
        with self._condition:
            if self._closed:
                raise RuntimeError(_QUEUE_CLOSED_MSG)
            dropped = 0
            if len(self._items) == self._items.maxlen:
                self._items.popleft()
                dropped = 1
                self._dropped_count += 1
            self._items.append(item)
            self._condition.notify_all()
            return dropped

    # ---- C9 take_latest --------------------------------------------------

    def take_latest(self, timeout_s: Optional[float] = 0.0) -> Optional[T]:
        """Return the unique item, or ``None`` when empty/closed/timed out."""
        if timeout_s is not None and timeout_s < 0:
            raise ValueError("timeout_s must be >= 0 (or None to block)")

        with self._condition:
            if timeout_s is None:
                while True:
                    if self._closed:
                        return None
                    if self._items:
                        return self._pop_unique()
                    self._condition.wait()
            else:
                deadline = time.monotonic() + timeout_s
                while True:
                    if self._closed:
                        return None
                    if self._items:
                        return self._pop_unique()
                    if timeout_s == 0:
                        return None
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        return None
                    self._condition.wait(timeout=remaining)

    # ---- C10 close -------------------------------------------------------

    def close(self) -> int:
        """Mark closed, clear pending items, count and wake; idempotent."""
        with self._condition:
            if self._closed:
                return 0
            cleared = len(self._items)
            if cleared:
                self._items.clear()
                self._dropped_count += cleared
            self._closed = True
            self._condition.notify_all()
            return cleared

    # ---- introspection (read-only) --------------------------------------

    @property
    def is_closed(self) -> bool:
        with self._condition:
            return self._closed

    @property
    def dropped_count(self) -> int:
        """Cumulative drops: normal evictions + shutdown clears."""
        with self._condition:
            return self._dropped_count

    # ---- helpers ---------------------------------------------------------

    def _pop_unique(self) -> T:
        item = self._items.pop()
        self._items.clear()
        return item
