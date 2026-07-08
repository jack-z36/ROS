"""Tests for ActionSpec, ACTION_DIM, ensure_action_vector, and split_action."""

import numpy as np
import pytest
from dataclasses import FrozenInstanceError

from model_deploy.act.types.action_spec import (
    ACTION_DIM,
    LEFT_TCP_ACTION_DIM,
    RIGHT_TCP_ACTION_DIM,
    LEFT_GRIPPER_DIM,
    RIGHT_GRIPPER_DIM,
    ActionSpec,
    ensure_action_vector,
    split_action,
)


class TestConstants:
    """Verify dimension constants."""

    def test_action_dim_is_16(self) -> None:
        assert ACTION_DIM == 16

    def test_segment_dims(self) -> None:
        assert LEFT_TCP_ACTION_DIM == 7
        assert RIGHT_TCP_ACTION_DIM == 7
        assert LEFT_GRIPPER_DIM == 1
        assert RIGHT_GRIPPER_DIM == 1
        total = (
            LEFT_TCP_ACTION_DIM
            + RIGHT_TCP_ACTION_DIM
            + LEFT_GRIPPER_DIM
            + RIGHT_GRIPPER_DIM
        )
        assert total == ACTION_DIM


class TestActionSpec:
    """Tests for ActionSpec frozen dataclass."""

    def test_construction(self) -> None:
        spec = ActionSpec(
            left_tcp_action=np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0], dtype=np.float32),
            right_tcp_action=np.array([8.0, 9.0, 10.0, 11.0, 12.0, 13.0, 14.0], dtype=np.float32),
            left_gripper=0.5,
            right_gripper=0.8,
        )
        assert spec.left_gripper == 0.5
        assert spec.right_gripper == 0.8
        assert len(spec.left_tcp_action) == 7
        assert len(spec.right_tcp_action) == 7

    def test_as_vector(self) -> None:
        left = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0], dtype=np.float32)
        right = np.array([8.0, 9.0, 10.0, 11.0, 12.0, 13.0, 14.0], dtype=np.float32)
        spec = ActionSpec(
            left_tcp_action=left,
            right_tcp_action=right,
            left_gripper=0.5,
            right_gripper=0.8,
        )
        vec = spec.as_vector()
        assert vec.shape == (16,)
        assert vec.dtype == np.float32
        np.testing.assert_array_equal(vec[0:7], left)
        np.testing.assert_array_equal(vec[7:14], right)
        assert abs(float(vec[14]) - 0.5) < 1e-6
        assert abs(float(vec[15]) - 0.8) < 1e-6

    def test_frozen_immutable(self) -> None:
        spec = ActionSpec(
            left_tcp_action=np.zeros(7, dtype=np.float32),
            right_tcp_action=np.zeros(7, dtype=np.float32),
            left_gripper=0.0,
            right_gripper=0.0,
        )
        with pytest.raises(FrozenInstanceError):
            spec.left_gripper = 1.0  # type: ignore[misc]


class TestEnsureActionVector:
    """Tests for ensure_action_vector."""

    def test_valid_16d_list(self) -> None:
        arr = ensure_action_vector([1.0] * 16)
        assert arr.shape == (16,)
        assert arr.dtype == np.float32

    def test_valid_16d_ndarray(self) -> None:
        arr = ensure_action_vector(np.ones(16, dtype=np.float64))
        assert arr.shape == (16,)
        assert arr.dtype == np.float32

    def test_too_short_raises(self) -> None:
        with pytest.raises(ValueError, match="Expected action vector of length 16"):
            ensure_action_vector([1.0] * 15)

    def test_too_long_raises(self) -> None:
        with pytest.raises(ValueError, match="Expected action vector of length 16"):
            ensure_action_vector([1.0] * 17)

    def test_empty_raises(self) -> None:
        with pytest.raises(ValueError, match="Expected action vector of length 16"):
            ensure_action_vector([])


class TestSplitAction:
    """Tests for split_action."""

    def test_split_returns_action_spec(self) -> None:
        flat = list(range(16))
        result = split_action(flat)
        assert isinstance(result, ActionSpec)
        np.testing.assert_array_equal(result.left_tcp_action, np.array([0, 1, 2, 3, 4, 5, 6], dtype=np.float32))
        np.testing.assert_array_equal(result.right_tcp_action, np.array([7, 8, 9, 10, 11, 12, 13], dtype=np.float32))
        assert result.left_gripper == 14.0
        assert result.right_gripper == 15.0

    def test_split_invalid_dim_raises(self) -> None:
        with pytest.raises(ValueError, match="Expected action vector of length 16"):
            split_action([1.0] * 15)

    def test_roundtrip(self) -> None:
        """split_action -> as_vector should be identity."""
        original = np.array(
            [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7,
             0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4,
             0.55, 0.85],
            dtype=np.float32,
        )
        spec = split_action(original)
        reconstructed = spec.as_vector()
        np.testing.assert_array_almost_equal(reconstructed, original)
