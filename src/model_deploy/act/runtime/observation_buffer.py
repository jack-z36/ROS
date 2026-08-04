"""ObservationBuffer — latest-only observation storage for L2-02.

Provides a thread-safe slot holding the most recent ObservationSnapshot.
L2-06 ControlLoop reads through ``latest_observation(max_age_s)``.
Metrics track counters for ready, replaced, and stale reads.

No ROS dependency, no request/chunk queues, no topic publishing.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Mapping, Optional

from model_deploy.act.types.observation import ObservationSnapshot


def _default_monotonic_clock() -> float:
    """Return the current monotonic time (seconds)."""
    import time

    return time.monotonic


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

    def __init__(
        self,
        monotonic_clock: Callable[[], float] | None = None,
        on_observation: Callable[[object], None] | None = None,
    ) -> None:
        self._latest_observation: ObservationSnapshot | None = None
        self._lock: threading.Lock = threading.Lock()
        self._metrics: ObservationMetrics = ObservationMetrics()
        # Shared clock domain with collector/pipeline so captured_at_s and
        # freshness age are computed with the same monotonic source
        # (deploy_057 / P0-07).
        self._monotonic_clock: Callable[[], float] = (
            monotonic_clock or _default_monotonic_clock()
        )
        # Optional side-channel callback invoked after each set_observation.
        # Used by DebugObserver for Web UI data collection.
        self._on_observation: Callable[[object], None] | None = on_observation

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
            self._metrics.updated_at_s = self._monotonic_clock()
            # Clear last_error on success
            self._metrics.last_error = None
        # Fire side-channel callback outside the lock to avoid blocking.
        if self._on_observation is not None:
            try:
                self._on_observation(observation)
            except Exception:
                pass  # Callback failure must never affect the main pipeline.

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
                       relative to the buffer's monotonic clock.

        Returns:
            The latest ``ObservationSnapshot``, or ``None`` when the buffer
            is empty or the snapshot has expired.
        """
        with self._lock:
            if self._latest_observation is None:
                return None

            if max_age_s is not None:
                age = self._monotonic_clock() - self._latest_observation.captured_at_s
                if age > max_age_s:
                    self._metrics.stale_observation_count += 1
                    return None

            return self._latest_observation

    # ------------------------------------------------------------------
    # Diagnostics
    # ------------------------------------------------------------------

    def set_on_observation_callback(
        self, callback: Callable[[object], None] | None
    ) -> None:
        """Attach (or replace) the side-channel observation callback.

        Used to wire a DebugObserver after the pipeline has been built.
        """
        with self._lock:
            self._on_observation = callback

    def record_missing_fields(self, fields: List[str]) -> None:
        """Record the latest missing-fields diagnostic list."""
        with self._lock:
            self._metrics.last_missing_fields = list(fields)
            self._metrics.updated_at_s = self._monotonic_clock()

    def record_error(self, error: str) -> None:
        """Record the latest error message."""
        with self._lock:
            self._metrics.last_error = error
            self._metrics.updated_at_s = self._monotonic_clock()

    def metrics_snapshot(self) -> Mapping[str, object]:
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
