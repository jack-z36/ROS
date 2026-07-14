"""Tests for L2-06 RuntimeMetrics (deploy_051).

Covers A2/C4/C6/C11-C12:
  - thread-safe record_event under concurrency.
  - RuntimeMetricsSnapshot is frozen and exposes no mutable reference.
  - normal-eviction drop count and shutdown-clear count stay separate counters.
"""

from __future__ import annotations

import threading
import time

import pytest

from model_deploy.act.runtime.runtime_metrics import (
    RuntimeMetrics,
    RuntimeMetricsSnapshot,
)


def _make_metrics() -> RuntimeMetrics:
    return RuntimeMetrics(clock=time.monotonic)


# ---------------------------------------------------------------------------
# Snapshot immutability / defaults
# ---------------------------------------------------------------------------


class TestSnapshot:
    def test_default_snapshot(self) -> None:
        snap = _make_metrics().snapshot()
        assert isinstance(snap, RuntimeMetricsSnapshot)
        assert snap.runtime_status == "STARTING"
        assert snap.tick_count == 0
        assert snap.request_queue_drop_count == 0
        assert snap.shutdown_queue_cleared_count == 0
        assert snap.publish_outcome_counts == ()
        assert snap.last_safety_finding_codes == ()

    def test_snapshot_is_frozen(self) -> None:
        snap = _make_metrics().snapshot()
        with pytest.raises(Exception):
            snap.tick_count = 5  # type: ignore[misc]

    def test_snapshot_exposes_no_mutable_reference(self) -> None:
        m = _make_metrics()
        m.record_event("publish", value="PUBLISHED")
        m.record_event("last_safety_findings", value=("GRIPPER", "AGE"))
        snap = m.snapshot()
        # dict/list-like fields are delivered as immutable tuple pairs / tuples.
        assert isinstance(snap.publish_outcome_counts, tuple)
        assert isinstance(snap.last_safety_finding_codes, tuple)
        assert dict(snap.publish_outcome_counts) == {"PUBLISHED": 1}
        # Repeated snapshots are independent objects, not aliased internals.
        assert m.snapshot() is not snap

    def test_internal_state_not_exposed(self) -> None:
        m = _make_metrics()
        m.record_event("request_submitted")
        snap1 = m.snapshot()
        m.record_event("request_submitted")
        snap2 = m.snapshot()
        assert snap1.request_submitted_count == 1
        assert snap2.request_submitted_count == 2


# ---------------------------------------------------------------------------
# record_event counters
# ---------------------------------------------------------------------------


class TestRecordEvent:
    def test_increment_counter(self) -> None:
        m = _make_metrics()
        m.record_event("tick")
        m.record_event("tick")
        assert m.snapshot().tick_count == 2

    def test_gauge_set(self) -> None:
        m = _make_metrics()
        m.record_event("status", value="EXECUTING")
        m.record_event("active_cursor", value=3)
        m.record_event("active_chunk_size", value=10)
        snap = m.snapshot()
        assert snap.runtime_status == "EXECUTING"
        assert snap.active_cursor == 3
        assert snap.active_chunk_size == 10

    def test_latency_non_negative(self) -> None:
        m = _make_metrics()
        m.record_event("latency", value=-5.0)
        assert m.snapshot().last_inference_latency_s == 0.0

    def test_publish_outcome_counted(self) -> None:
        m = _make_metrics()
        m.record_event("publish", value="PUBLISHED")
        m.record_event("publish", value="PUBLISHED")
        m.record_event("publish", value="REJECTED")
        assert dict(m.snapshot().publish_outcome_counts) == {
            "PUBLISHED": 2,
            "REJECTED": 1,
        }

    def test_updated_at_s_changes(self) -> None:
        m = _make_metrics()
        before = m.snapshot().updated_at_s
        time.sleep(0.01)
        m.record_event("tick")
        assert m.snapshot().updated_at_s > before

    def test_unknown_event_rejected(self) -> None:
        m = _make_metrics()
        with pytest.raises(ValueError):
            m.record_event("not_a_real_event")


# ---------------------------------------------------------------------------
# Bounded drop classification (normal eviction vs shutdown clear)
# ---------------------------------------------------------------------------


class TestDropClassification:
    def test_normal_drop_vs_shutdown_clear_separate(self) -> None:
        m = _make_metrics()
        # Normal evictions (e.g. queue.put_latest evicted an item):
        m.record_event("request_queue_drop", value=2)
        m.record_event("result_queue_drop", value=1)
        # Shutdown clears (e.g. queue.close cleared pending):
        m.record_event("shutdown_queue_cleared", value=3)
        snap = m.snapshot()
        assert snap.request_queue_drop_count == 2
        assert snap.result_queue_drop_count == 1
        assert snap.shutdown_queue_cleared_count == 3
        # The two classes never merge.
        assert snap.request_queue_drop_count != snap.shutdown_queue_cleared_count


# ---------------------------------------------------------------------------
# Concurrency / lock safety
# ---------------------------------------------------------------------------


class TestConcurrency:
    def test_concurrent_record_event_is_safe(self) -> None:
        m = _make_metrics()
        errors: list[Exception] = []
        barrier = threading.Barrier(6, timeout=5)

        def worker() -> None:
            try:
                barrier.wait()
                for _ in range(200):
                    m.record_event("tick")
                    m.record_event("request_submitted")
                    m.record_event("inference_success")
                    m.record_event("publish", value="PUBLISHED")
                    _ = m.snapshot()
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=worker) for _ in range(6)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == [], f"Concurrent record_event raised: {errors}"
        snap = m.snapshot()
        assert snap.tick_count == 6 * 200
        assert snap.request_submitted_count == 6 * 200
        assert snap.inference_success_count == 6 * 200
        assert dict(snap.publish_outcome_counts) == {"PUBLISHED": 6 * 200}

    def test_concurrent_snapshot_no_race(self) -> None:
        m = _make_metrics()
        errors: list[Exception] = []
        barrier = threading.Barrier(4, timeout=5)

        def reader() -> None:
            try:
                barrier.wait()
                for _ in range(300):
                    s = m.snapshot()
                    assert s.tick_count >= 0
            except Exception as exc:
                errors.append(exc)

        def writer() -> None:
            try:
                barrier.wait()
                for _ in range(300):
                    m.record_event("tick")
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=reader) for _ in range(2)] + [
            threading.Thread(target=writer) for _ in range(2)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == [], f"Concurrent snapshot raised: {errors}"
