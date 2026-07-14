"""Tests for ObservationBuffer and ObservationMetrics."""

import threading
import time

import numpy as np
import pytest

from model_deploy.act.runtime.observation_buffer import (
    ObservationBuffer,
    ObservationMetrics,
)
from model_deploy.act.types.observation import (
    ObservationState,
    ObservationSnapshot,
)


# ---------------------------------------------------------------------------
# Shared helpers
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


def _make_snapshot(captured_at_s: float | None = None) -> ObservationSnapshot:
    return ObservationSnapshot(
        images={"cam_high": np.zeros((480, 640, 3), dtype=np.uint8)},
        state=_make_state(),
        encoded_state=np.zeros(16, dtype=np.float32),
        captured_at_s=captured_at_s if captured_at_s is not None else time.time(),
    )


class FakeClock:
    """Controllable monotonic clock for deterministic freshness tests."""

    def __init__(self, t: float = 1000.0) -> None:
        self.t = t

    def __call__(self) -> float:
        return self.t

    def advance(self, dt: float) -> None:
        self.t += dt


# ---------------------------------------------------------------------------
# ObservationMetrics
# ---------------------------------------------------------------------------


class TestObservationMetrics:
    def test_default_values(self) -> None:
        m = ObservationMetrics()
        assert m.observation_ready_count == 0
        assert m.replaced_observation_count == 0
        assert m.stale_observation_count == 0
        assert m.last_missing_fields == []
        assert m.last_error is None

    def test_field_assignment(self) -> None:
        m = ObservationMetrics(
            observation_ready_count=5,
            replaced_observation_count=2,
            stale_observation_count=1,
            last_missing_fields=["cam_wrist"],
            last_error="timeout",
            updated_at_s=123.0,
        )
        assert m.observation_ready_count == 5
        assert m.replaced_observation_count == 2
        assert m.stale_observation_count == 1
        assert m.last_missing_fields == ["cam_wrist"]
        assert m.last_error == "timeout"


# ---------------------------------------------------------------------------
# set_observation + latest_observation
# ---------------------------------------------------------------------------


class TestSetAndGet:
    def test_set_and_get(self) -> None:
        buf = ObservationBuffer()
        snap = _make_snapshot()
        buf.set_observation(snap)
        result = buf.latest_observation()
        assert result is snap

    def test_empty_returns_none(self) -> None:
        buf = ObservationBuffer()
        assert buf.latest_observation() is None

    def test_latest_only_semantics(self) -> None:
        """Overwrite: B replaces A."""
        buf = ObservationBuffer()
        snap_a = _make_snapshot()
        snap_b = _make_snapshot()
        buf.set_observation(snap_a)
        buf.set_observation(snap_b)
        result = buf.latest_observation()
        assert result is snap_b
        assert result is not snap_a

    def test_max_age_not_expired(self) -> None:
        clock = FakeClock(1000.0)
        buf = ObservationBuffer(monotonic_clock=clock)
        snap = _make_snapshot(captured_at_s=clock())
        buf.set_observation(snap)
        result = buf.latest_observation(max_age_s=5.0)
        assert result is snap

    def test_max_age_expired(self) -> None:
        clock = FakeClock(1000.0)
        buf = ObservationBuffer(monotonic_clock=clock)
        snap = _make_snapshot(captured_at_s=clock())
        buf.set_observation(snap)
        clock.advance(10.0)
        result = buf.latest_observation(max_age_s=1.0)
        assert result is None


# ---------------------------------------------------------------------------
# Metrics counters
# ---------------------------------------------------------------------------


class TestMetricsCounters:
    def test_ready_count(self) -> None:
        buf = ObservationBuffer()
        for _ in range(3):
            buf.set_observation(_make_snapshot())
        metrics = buf.metrics_snapshot()
        assert metrics["observation_ready_count"] == 3
        # Each write after the first replaces the prior
        assert metrics["replaced_observation_count"] == 2

    def test_stale_count(self) -> None:
        clock = FakeClock(1000.0)
        buf = ObservationBuffer(monotonic_clock=clock)
        snap = _make_snapshot(captured_at_s=clock())
        buf.set_observation(snap)
        clock.advance(10.0)
        assert buf.latest_observation(max_age_s=1.0) is None
        assert buf.latest_observation(max_age_s=1.0) is None
        metrics = buf.metrics_snapshot()
        assert metrics["stale_observation_count"] == 2

    def test_record_missing_fields(self) -> None:
        buf = ObservationBuffer()
        buf.record_missing_fields(["cam_high", "left_tcp_position"])
        metrics = buf.metrics_snapshot()
        assert "cam_high" in metrics["last_missing_fields"]
        assert "left_tcp_position" in metrics["last_missing_fields"]

    def test_record_error(self) -> None:
        buf = ObservationBuffer()
        buf.record_error("decode failed")
        metrics = buf.metrics_snapshot()
        assert metrics["last_error"] == "decode failed"

    def test_metrics_updated_at_s(self) -> None:
        buf = ObservationBuffer()
        before = time.monotonic()
        buf.set_observation(_make_snapshot())
        metrics = buf.metrics_snapshot()
        assert metrics["updated_at_s"] >= before


# ---------------------------------------------------------------------------
# Concurrency
# ---------------------------------------------------------------------------


class TestConcurrentAccess:
    def test_concurrent_read_write(self) -> None:
        buf = ObservationBuffer()
        errors: list[Exception] = []
        barrier = threading.Barrier(4, timeout=5)

        def writer() -> None:
            try:
                barrier.wait()
                for _ in range(50):
                    buf.set_observation(_make_snapshot())
            except Exception as exc:
                errors.append(exc)

        def reader() -> None:
            try:
                barrier.wait()
                for _ in range(50):
                    # Don't assert — just exercise the lock
                    _ = buf.latest_observation(max_age_s=30.0)
            except Exception as exc:
                errors.append(exc)

        threads = [
            threading.Thread(target=writer),
            threading.Thread(target=writer),
            threading.Thread(target=reader),
            threading.Thread(target=reader),
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0, f"Concurrent access raised: {errors}"

    def test_concurrent_metrics_snapshot(self) -> None:
        buf = ObservationBuffer()
        buf.set_observation(_make_snapshot())
        errors: list[Exception] = []
        barrier = threading.Barrier(4, timeout=5)

        def worker() -> None:
            try:
                barrier.wait()
                for _ in range(50):
                    buf.metrics_snapshot()
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=worker) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
