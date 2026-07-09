"""Tests for ObservationState, ObservationSnapshot, and ObservationFreshnessResult."""

import numpy as np
import pytest
from dataclasses import FrozenInstanceError

from model_deploy.act.types.observation import (
    EXPECTED_STATE_DIM,
    ObservationState,
    ObservationSnapshot,
    ObservationFreshnessResult,
)


# ---------------------------------------------------------------------------
# Shared test helpers
# ---------------------------------------------------------------------------


def _make_state() -> ObservationState:
    """Return a valid ObservationState for test use."""
    return ObservationState(
        left_tcp_position=np.array([0.1, 0.2, 0.3], dtype=np.float32),
        left_tcp_orientation=np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float32),
        left_gripper_width=0.05,
        right_tcp_position=np.array([0.4, 0.5, 0.6], dtype=np.float32),
        right_tcp_orientation=np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float32),
        right_gripper_width=0.08,
    )


def _make_encoded_state() -> np.ndarray:
    """Return a valid 16D encoded_state for test use."""
    return np.arange(EXPECTED_STATE_DIM, dtype=np.float32)


def _make_snapshot() -> ObservationSnapshot:
    """Return a valid ObservationSnapshot for test use."""
    return ObservationSnapshot(
        images={"cam_high": np.zeros((480, 640, 3), dtype=np.uint8)},
        state=_make_state(),
        encoded_state=_make_encoded_state(),
        captured_at_s=1234567890.5,
    )


# ---------------------------------------------------------------------------
# ObservationState
# ---------------------------------------------------------------------------


class TestObservationState:
    """Tests for ObservationState frozen dataclass."""

    def test_observation_state_creation(self) -> None:
        """Legal field construction succeeds."""
        state = _make_state()
        assert state.left_gripper_width == 0.05
        assert state.right_gripper_width == 0.08
        assert state.left_tcp_position.shape == (3,)
        assert state.left_tcp_orientation.shape == (4,)
        assert state.right_tcp_position.shape == (3,)
        assert state.right_tcp_orientation.shape == (4,)

    def test_frozen_modification_raises(self) -> None:
        """Modifying a frozen field raises FrozenInstanceError."""
        state = _make_state()
        with pytest.raises(FrozenInstanceError):
            state.left_gripper_width = 0.99  # type: ignore[misc]


# ---------------------------------------------------------------------------
# ObservationSnapshot
# ---------------------------------------------------------------------------


class TestObservationSnapshot:
    """Tests for ObservationSnapshot frozen dataclass."""

    def test_observation_snapshot_creation(self) -> None:
        """Legal 16D encoded_state construction succeeds."""
        snapshot = _make_snapshot()
        assert snapshot.encoded_state.shape == (EXPECTED_STATE_DIM,)
        assert isinstance(snapshot.state, ObservationState)
        assert snapshot.captured_at_s == 1234567890.5

    def test_observation_snapshot_invalid_dim(self) -> None:
        """Invalid-dimension encoded_state raises ValueError."""
        invalid = np.zeros(26, dtype=np.float32)
        with pytest.raises(ValueError, match="encoded_state must have shape"):
            ObservationSnapshot(
                images={"cam_high": np.zeros((480, 640, 3), dtype=np.uint8)},
                state=_make_state(),
                encoded_state=invalid,
                captured_at_s=0.0,
            )

    def test_observation_snapshot_frozen(self) -> None:
        """Modifying a frozen field raises FrozenInstanceError."""
        snapshot = _make_snapshot()
        with pytest.raises(FrozenInstanceError):
            snapshot.captured_at_s = 999.0  # type: ignore[misc]


# ---------------------------------------------------------------------------
# ObservationFreshnessResult
# ---------------------------------------------------------------------------


class TestObservationFreshnessResult:
    """Tests for ObservationFreshnessResult frozen dataclass."""

    def test_freshness_result_creation(self) -> None:
        """Legal field construction succeeds."""
        result = ObservationFreshnessResult(
            missing_fields=[],
            stale_fields=[],
            field_ages_s={},
            ready=True,
        )
        assert result.ready is True
        assert result.missing_fields == []
        assert result.stale_fields == []

    def test_not_ready_with_missing(self) -> None:
        """When fields are missing, ready is False and diagnostics are populated."""
        result = ObservationFreshnessResult(
            missing_fields=["cam_high"],
            stale_fields=[],
            field_ages_s={"cam_high": 999.0},
            ready=False,
        )
        assert result.ready is False
        assert "cam_high" in result.missing_fields
        assert result.field_ages_s["cam_high"] == 999.0

    def test_stale_fields_diagnostic(self) -> None:
        """Stale fields are reported separately from missing fields."""
        result = ObservationFreshnessResult(
            missing_fields=[],
            stale_fields=["left_tcp_position"],
            field_ages_s={"left_tcp_position": 5.0},
            ready=False,
        )
        assert "left_tcp_position" in result.stale_fields
        assert result.missing_fields == []

    def test_frozen_modification_raises(self) -> None:
        """Modifying a frozen field raises FrozenInstanceError."""
        result = ObservationFreshnessResult(
            missing_fields=[], stale_fields=[], field_ages_s={}, ready=True
        )
        with pytest.raises(FrozenInstanceError):
            result.ready = False  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Import without ROS
# ---------------------------------------------------------------------------


class TestImportWithoutROS:
    """Verify the observation types module does not pull in ROS dependencies."""

    def test_import_without_ros(self) -> None:
        """Import must succeed without ROS packages available."""
        from model_deploy.act.types import observation as obs

        assert obs.ObservationState is ObservationState
        assert obs.ObservationSnapshot is ObservationSnapshot
        assert obs.ObservationFreshnessResult is ObservationFreshnessResult
        assert obs.EXPECTED_STATE_DIM == 16
