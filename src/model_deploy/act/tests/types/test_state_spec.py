"""Tests for StateSpec, STATE_DIM, ensure_state_vector, and encode_state."""

import numpy as np
import pytest
from dataclasses import FrozenInstanceError

from model_deploy.act.types.state_spec import (
    STATE_DIM,
    LEFT_TCP_POSE_DIM,
    RIGHT_TCP_POSE_DIM,
    LEFT_GRIPPER_WIDTH_DIM,
    RIGHT_GRIPPER_WIDTH_DIM,
    StateSpec,
    ensure_state_vector,
    encode_state,
)


class TestConstants:
    """Verify dimension constants."""

    def test_state_dim_is_16(self) -> None:
        assert STATE_DIM == 16

    def test_segment_dims(self) -> None:
        assert LEFT_TCP_POSE_DIM == 7
        assert RIGHT_TCP_POSE_DIM == 7
        assert LEFT_GRIPPER_WIDTH_DIM == 1
        assert RIGHT_GRIPPER_WIDTH_DIM == 1
        total = (
            LEFT_TCP_POSE_DIM
            + RIGHT_TCP_POSE_DIM
            + LEFT_GRIPPER_WIDTH_DIM
            + RIGHT_GRIPPER_WIDTH_DIM
        )
        assert total == STATE_DIM


class TestStateSpec:
    """Tests for StateSpec frozen dataclass."""

    def test_default_construction(self) -> None:
        spec = StateSpec()
        assert spec.total_dim == 16
        assert spec.segment_names == (
            "left_tcp_pose",
            "right_tcp_pose",
            "left_gripper_width",
            "right_gripper_width",
        )
        assert spec.segment_dims == (7, 7, 1, 1)
        assert spec.segment_offsets == (0, 7, 14, 15)

    def test_frozen_immutable(self) -> None:
        spec = StateSpec()
        with pytest.raises(FrozenInstanceError):
            spec.segment_names = ("a", "b", "c", "d")  # type: ignore[misc]


class TestEnsureStateVector:
    """Tests for ensure_state_vector."""

    def test_valid_16d_list(self) -> None:
        arr = ensure_state_vector([1.0] * 16)
        assert arr.shape == (16,)
        assert arr.dtype == np.float32

    def test_valid_16d_tuple(self) -> None:
        arr = ensure_state_vector(tuple(range(16)))
        assert arr.shape == (16,)
        assert arr.dtype == np.float32

    def test_valid_16d_ndarray(self) -> None:
        arr = ensure_state_vector(np.ones(16, dtype=np.float64))
        assert arr.shape == (16,)
        assert arr.dtype == np.float32

    def test_too_short_raises(self) -> None:
        with pytest.raises(ValueError, match="Expected state vector of length 16"):
            ensure_state_vector([1.0] * 15)

    def test_too_long_raises(self) -> None:
        with pytest.raises(ValueError, match="Expected state vector of length 16"):
            ensure_state_vector([1.0] * 17)

    def test_empty_raises(self) -> None:
        with pytest.raises(ValueError, match="Expected state vector of length 16"):
            ensure_state_vector([])


class TestEncodeState:
    """Tests for encode_state."""

    def test_output_shape_and_dtype(self) -> None:
        result = encode_state(
            left_tcp_pose=[1.0] * 7,
            right_tcp_pose=[2.0] * 7,
            left_gripper_width=0.5,
            right_gripper_width=0.8,
        )
        assert result.shape == (16,)
        assert result.dtype == np.float32

    def test_segment_offsets(self) -> None:
        """Verify that each segment lands at the correct offset."""
        left = [10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0]
        right = [20.0, 21.0, 22.0, 23.0, 24.0, 25.0, 26.0]
        result = encode_state(
            left_tcp_pose=left,
            right_tcp_pose=right,
            left_gripper_width=5.0,
            right_gripper_width=6.0,
        )
        np.testing.assert_array_equal(result[0:7], left)
        np.testing.assert_array_equal(result[7:14], right)
        assert result[14] == 5.0
        assert result[15] == 6.0

    def test_wrong_left_tcp_pose_dim_raises(self) -> None:
        with pytest.raises(ValueError, match="left_tcp_pose must have 7"):
            encode_state(
                left_tcp_pose=[1.0] * 6,
                right_tcp_pose=[2.0] * 7,
                left_gripper_width=0.5,
                right_gripper_width=0.8,
            )

    def test_wrong_right_tcp_pose_dim_raises(self) -> None:
        with pytest.raises(ValueError, match="right_tcp_pose must have 7"):
            encode_state(
                left_tcp_pose=[1.0] * 7,
                right_tcp_pose=[2.0] * 8,
                left_gripper_width=0.5,
                right_gripper_width=0.8,
            )
