"""Tests for ObservationCollector — mock full snapshot, missing/stale reject, concurrency."""

import threading
import time

import numpy as np
import pytest

from model_deploy.act.service.observation_collector import (
    ObservationCollector,
    _default_state_codec,
)

# ---------------------------------------------------------------------------
# Shared fixtures / helpers
# ---------------------------------------------------------------------------

REQUIRED_IMAGE_KEYS = ["cam_high", "cam_wrist"]
REQUIRED_STATE_FIELDS = [
    "left_tcp_position",
    "left_tcp_orientation",
    "left_gripper_width",
    "right_tcp_position",
    "right_tcp_orientation",
    "right_gripper_width",
]


def _new_collector() -> ObservationCollector:
    return ObservationCollector(
        required_image_keys=REQUIRED_IMAGE_KEYS,
        required_state_fields=REQUIRED_STATE_FIELDS,
    )


def _fill_all_fields(col: ObservationCollector) -> None:
    """Write every required field into *col* so snapshot() succeeds."""
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    col.update_image("cam_high", img)
    col.update_image("cam_wrist", img)
    col.update_tcp_pose("left", [0.1, 0.2, 0.3], [0.0, 0.0, 0.0, 1.0])
    col.update_tcp_pose("right", [0.4, 0.5, 0.6], [0.0, 0.0, 0.0, 1.0])
    col.update_gripper_state("left", 0.05)
    col.update_gripper_state("right", 0.08)


# ---------------------------------------------------------------------------
# Mock full snapshot
# ---------------------------------------------------------------------------


class TestMockFullSnapshot:
    def test_full_fields_snapshot_non_none(self) -> None:
        col = _new_collector()
        _fill_all_fields(col)
        snap = col.snapshot(max_age_s=5.0)
        assert snap is not None
        assert snap.encoded_state.shape == (16,)
        assert snap.state.left_gripper_width == 0.05
        assert snap.state.right_gripper_width == 0.08
        assert "cam_high" in snap.images
        assert "cam_wrist" in snap.images

    def test_encoded_state_dim_is_16(self) -> None:
        col = _new_collector()
        _fill_all_fields(col)
        snap = col.snapshot(max_age_s=5.0)
        assert snap is not None
        assert snap.encoded_state.shape == (16,)
        assert snap.encoded_state.dtype == np.float32


# ---------------------------------------------------------------------------
# Missing-field reject
# ---------------------------------------------------------------------------


class TestMissingReject:
    def test_missing_image_reject(self) -> None:
        col = _new_collector()
        # fill everything except cam_wrist
        col.update_image("cam_high", np.zeros((480, 640, 3), dtype=np.uint8))
        col.update_tcp_pose("left", [0.1, 0.2, 0.3], [0.0, 0.0, 0.0, 1.0])
        col.update_tcp_pose("right", [0.4, 0.5, 0.6], [0.0, 0.0, 0.0, 1.0])
        col.update_gripper_state("left", 0.05)
        col.update_gripper_state("right", 0.08)

        snap = col.snapshot(max_age_s=5.0)
        assert snap is None
        missing = col.missing_fields()
        assert "cam_wrist" in missing

    def test_missing_pose_reject(self) -> None:
        col = _new_collector()
        # fill everything except left TCP pose
        col.update_image("cam_high", np.zeros((480, 640, 3), dtype=np.uint8))
        col.update_image("cam_wrist", np.zeros((480, 640, 3), dtype=np.uint8))
        col.update_tcp_pose("right", [0.4, 0.5, 0.6], [0.0, 0.0, 0.0, 1.0])
        col.update_gripper_state("left", 0.05)
        col.update_gripper_state("right", 0.08)

        snap = col.snapshot(max_age_s=5.0)
        assert snap is None
        missing = col.missing_fields()
        assert "left_tcp_position" in missing or "left_tcp_orientation" in missing

    def test_missing_gripper_reject(self) -> None:
        col = _new_collector()
        col.update_image("cam_high", np.zeros((480, 640, 3), dtype=np.uint8))
        col.update_image("cam_wrist", np.zeros((480, 640, 3), dtype=np.uint8))
        col.update_tcp_pose("left", [0.1, 0.2, 0.3], [0.0, 0.0, 0.0, 1.0])
        col.update_tcp_pose("right", [0.4, 0.5, 0.6], [0.0, 0.0, 0.0, 1.0])
        # missing right gripper

        snap = col.snapshot(max_age_s=5.0)
        assert snap is None
        assert "right_gripper_width" in col.missing_fields()


# ---------------------------------------------------------------------------
# Stale reject
# ---------------------------------------------------------------------------


class TestStaleReject:
    def test_stale_rejects_with_small_max_age(self) -> None:
        col = _new_collector()
        _fill_all_fields(col)

        # With a very small max_age_s, fields should be stale.
        time.sleep(0.05)
        snap = col.snapshot(max_age_s=0.001)
        assert snap is None
        stale = col.stale_fields(time.monotonic(), max_age_s=0.001)
        assert len(stale) > 0

    def test_stale_fields_empty_when_fresh(self) -> None:
        col = _new_collector()
        _fill_all_fields(col)
        stale = col.stale_fields(time.monotonic(), max_age_s=30.0)
        assert stale == []

    def test_all_fresh_snapshot_succeeds(self) -> None:
        col = _new_collector()
        _fill_all_fields(col)
        snap = col.snapshot(max_age_s=30.0)
        assert snap is not None
        assert snap.encoded_state.shape == (16,)


# ---------------------------------------------------------------------------
# Freshness Result diagnostic
# ---------------------------------------------------------------------------


class TestFreshnessResult:
    def test_freshness_ready_when_all_present(self) -> None:
        col = _new_collector()
        _fill_all_fields(col)
        result = col.freshness_result(max_age_s=30.0)
        assert result.ready is True
        assert result.missing_fields == []
        assert result.stale_fields == []

    def test_freshness_not_ready_when_missing(self) -> None:
        col = _new_collector()
        # only fill images
        col.update_image("cam_high", np.zeros((480, 640, 3), dtype=np.uint8))
        col.update_image("cam_wrist", np.zeros((480, 640, 3), dtype=np.uint8))
        result = col.freshness_result(max_age_s=5.0)
        assert result.ready is False
        assert len(result.missing_fields) > 0


# ---------------------------------------------------------------------------
# Concurrency
# ---------------------------------------------------------------------------


class TestConcurrentUpdate:
    def test_concurrent_update_no_exception(self) -> None:
        col = _new_collector()
        errors: list[Exception] = []
        barrier = threading.Barrier(4, timeout=5)

        def updater() -> None:
            try:
                barrier.wait()
                for _ in range(50):
                    col.update_image("cam_high", np.zeros((480, 640, 3), dtype=np.uint8))
                    col.update_tcp_pose("left", [0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 1.0])
                    col.update_gripper_state("left", 0.0)
            except Exception as exc:
                errors.append(exc)

        threads = [
            threading.Thread(target=updater) for _ in range(4)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0, f"Concurrent updates raised: {errors}"

    def test_concurrent_snapshot_does_not_corrupt(self) -> None:
        col = _new_collector()
        _fill_all_fields(col)

        results: list[bool] = []
        barrier = threading.Barrier(4, timeout=5)

        def reader() -> None:
            barrier.wait()
            for _ in range(50):
                snap = col.snapshot(max_age_s=30.0)
                results.append(snap is not None)

        threads = [threading.Thread(target=reader) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert all(results), "All snapshots should be non-None with fresh data"
        assert len(results) == 200


# ---------------------------------------------------------------------------
# State codec
# ---------------------------------------------------------------------------


class TestDefaultStateCodec:
    def test_output_dim(self) -> None:
        from model_deploy.act.types.observation import ObservationState

        state = ObservationState(
            left_tcp_position=np.array([0.1, 0.2, 0.3], dtype=np.float32),
            left_tcp_orientation=np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float32),
            left_gripper_width=0.05,
            right_tcp_position=np.array([0.4, 0.5, 0.6], dtype=np.float32),
            right_tcp_orientation=np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float32),
            right_gripper_width=0.08,
        )
        encoded = _default_state_codec(state)
        assert encoded.shape == (16,)
        assert encoded.dtype == np.float32
