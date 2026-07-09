"""ObservationBuffer — latest-only observation storage for L2-02.

Provides a thread-safe slot holding the most recent ObservationSnapshot.
L2-06 ControlLoop reads through ``latest_observation(max_age_s)``.
Metrics track counters for ready, replaced, and stale reads.

No ROS dependency, no request/chunk queues, no topic publishing.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from model_deploy.act.types.observation import ObservationSnapshot


# ---------------------------------------------------------------------------
# ObservationMetrics
# ---------------------------------------------------------------------------


@dataclass
class ObservationMetrics:
    """Observation-side counters and diagnostics.

    Fields:
        observation_ready_count:   Total snapshots accepted via set_observation.
        replaced_observation_count: How many times an existing snapshot was
                                   overwritten before being consumed.
        stale_observation_count:   How many times latest_observation returned
                                   None because the snapshot exceeded max_age_s.
        last_missing_fields:       Most recent missing-fields list (diagnostic).
        last_error:                Most recent error message or None.
        updated_at_s:              Monotonic timestamp of last metrics change.
    """

    observation_ready_count: int = 0
    replaced_observation_count: int = 0
    stale_observation_count: int = 0
    last_missing_fields: List[str] = field(default_factory=list)
    last_error: Optional[str] = None
    updated_at_s: float = 0.0


# ---------------------------------------------------------------------------
# ObservationBuffer
# ---------------------------------------------------------------------------


class ObservationBuffer:
    """Thread-safe latest-only observation buffer.

    Holds the single most-recent ``ObservationSnapshot``.  Overwrite
    semantics — each ``set_observation`` replaces the prior slot entirely
    (no history queue).

    Typical usage::

        buffer = ObservationBuffer()
        buffer.set_observation(snapshot)          # ui layer callback
        latest = buffer.latest_observation(0.5)   # L2-06 ControlLoop tick
    """

    def __init__(self) -> None:
        self._latest_observation: ObservationSnapshot | None = None
        self._lock: threading.Lock = threading.Lock()
        self._metrics: ObservationMetrics = ObservationMetrics()

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def set_observation(self, observation: ObservationSnapshot) -> None:
        """Store *observation* as the latest slot, overwriting any prior."""
        with self._lock:
            if self._latest_observation is not None:
                self._metrics.replaced_observation_count += 1
            self._latest_observation = observation
            self._metrics.observation_ready_count += 1
            self._metrics.updated_at_s = time.monotonic()
            # Clear last_error on success
            self._metrics.last_error = None

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def latest_observation(
        self, max_age_s: float | None = None
    ) -> ObservationSnapshot | None:
        """Return the latest snapshot, or ``None``.

        Args:
            max_age_s: If set, the snapshot is rejected (returns ``None``)
                       when its ``captured_at_s`` is older than this age
                       relative to ``time.time()``.

        Returns:
            The latest ``ObservationSnapshot``, or ``None`` when the buffer
            is empty or the snapshot has expired.
        """
        with self._lock:
            if self._latest_observation is None:
                return None

            if max_age_s is not None:
                age = time.time() - self._latest_observation.captured_at_s
                if age > max_age_s:
                    self._metrics.stale_observation_count += 1
                    return None

            return self._latest_observation

    # ------------------------------------------------------------------
    # Diagnostics
    # ------------------------------------------------------------------

    def record_missing_fields(self, fields: List[str]) -> None:
        """Record the latest missing-fields diagnostic list."""
        with self._lock:
            self._metrics.last_missing_fields = list(fields)
            self._metrics.updated_at_s = time.monotonic()

    def record_error(self, error: str) -> None:
        """Record the latest error message."""
        with self._lock:
            self._metrics.last_error = error
            self._metrics.updated_at_s = time.monotonic()

    def metrics_snapshot(self) -> Dict[str, object]:
        """Return a dict copy of current metrics (safe for external readers)."""
        with self._lock:
            return {
                "observation_ready_count": self._metrics.observation_ready_count,
                "replaced_observation_count": self._metrics.replaced_observation_count,
                "stale_observation_count": self._metrics.stale_observation_count,
                "last_missing_fields": list(self._metrics.last_missing_fields),
                "last_error": self._metrics.last_error,
                "updated_at_s": self._metrics.updated_at_s,
            }
