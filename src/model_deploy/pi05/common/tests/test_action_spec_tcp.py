"""Tests for pi05.common.robot.action_spec (deploy_001 / D11).

Covers:
  - ACTION_DIM and related constants
  - BimanualAction field structure and as_vector segment order
  - split_bimanual_action segment order
  - round-trip consistency
  - dimension validation
"""

import numpy as np
import pytest

from pi05.common.robot.action_spec import (
    ACTION_DIM,
    BimanualAction,
    split_bimanual_action,
    TCP_POSE_DOF,
    GRIPPER_WIDTH_DOF,
    STATE_DIM,
)


class TestActionDim:
    """ACTION_DIM must be 16 (TO-BE D11)."""

    def test_action_dim_is_16(self):
        assert ACTION_DIM == 16

    def test_state_dim_is_16(self):
        assert STATE_DIM == 16

    def test_tcp_pose_dof_is_7(self):
        assert TCP_POSE_DOF == 7

    def test_gripper_width_dof_is_1(self):
        assert GRIPPER_WIDTH_DOF == 1


class TestBimanualActionFields:
    """BimanualAction dataclass field shapes and types."""

    def test_construct_with_arrays(self):
        left_tcp = np.array([0.3, -0.1, 0.5, 0.0, 0.0, 0.0, 1.0], dtype=np.float32)
        right_tcp = np.array([0.3, 0.1, 0.5, 0.0, 0.0, 0.0, 1.0], dtype=np.float32)
        action = BimanualAction(
            left_tcp_pose=left_tcp,
            left_gripper_width=0.5,
            right_tcp_pose=right_tcp,
            right_gripper_width=0.8,
        )
        assert action.left_tcp_pose.shape == (7,)
        assert action.right_tcp_pose.shape == (7,)
        assert isinstance(action.left_gripper_width, float)
        assert isinstance(action.right_gripper_width, float)
        np.testing.assert_array_equal(action.left_tcp_pose, left_tcp)
        np.testing.assert_array_equal(action.right_tcp_pose, right_tcp)


class TestAsVector:
    """as_vector must return 16D in alternating (interleaved) segment order.

    Alternating order:
      [0:7]   left_tcp_pose
      [7:8]   left_gripper_width
      [8:15]  right_tcp_pose
      [15:16] right_gripper_width
    """

    def test_as_vector_is_16d(self):
        left_tcp = np.arange(7, dtype=np.float32)
        right_tcp = np.arange(7, dtype=np.float32) + 10.0
        action = BimanualAction(left_tcp, 0.25, right_tcp, 0.75)
        vec = action.as_vector()
        assert vec.shape == (16,)
        assert vec.dtype == np.float32

    def test_as_vector_alternating_order(self):
        """Verify segment positions in the flat vector."""
        left_tcp = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0], dtype=np.float32)
        right_tcp = np.array([11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0], dtype=np.float32)
        action = BimanualAction(left_tcp, 99.0, right_tcp, -1.0)
        vec = action.as_vector()

        # [0:7] = left_tcp
        np.testing.assert_array_equal(vec[0:7], left_tcp)
        # [7:8] = left_gripper_width
        assert vec[7] == 99.0
        # [8:15] = right_tcp
        np.testing.assert_array_equal(vec[8:15], right_tcp)
        # [15] = right_gripper_width
        assert vec[15] == -1.0

    def test_as_vector_not_left_grouped(self):
        """Negative check: as_vector does NOT use all-left→all-right grouping."""
        left_tcp = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0], dtype=np.float32)
        right_tcp = np.array([8.0, 9.0, 10.0, 11.0, 12.0, 13.0, 14.0], dtype=np.float32)
        action = BimanualAction(left_tcp, 0.5, right_tcp, 0.5)
        vec = action.as_vector()

        # If it were all-left→all-right: vec[7:14] would be right_tcp.
        # In alternating order vec[7:14] = [left_width, right_tcp[0:6]]
        assert not np.array_equal(vec[7:14], right_tcp), (
            "as_vector should NOT use all-left→all-right grouping"
        )


class TestSplit:
    """split_bimanual_action reverses as_vector."""

    def test_split_alternating_order(self):
        """Split recovers fields in the correct alternating segment order."""
        vector = np.array(
            [
                0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7,  # left_tcp_pose [0:7]
                0.8,  # left_gripper_width [7]
                0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5,  # right_tcp_pose [8:15]
                1.6,  # right_gripper_width [15]
            ],
            dtype=np.float32,
        )
        action = split_bimanual_action(vector)

        np.testing.assert_array_almost_equal(action.left_tcp_pose, vector[0:7])
        assert action.left_gripper_width == pytest.approx(0.8)
        np.testing.assert_array_almost_equal(action.right_tcp_pose, vector[8:15])
        assert action.right_gripper_width == pytest.approx(1.6)

    def test_split_rejects_wrong_dim(self):
        with pytest.raises(ValueError, match="Expected 16 action values"):
            split_bimanual_action(np.zeros(14, dtype=np.float32))
        with pytest.raises(ValueError, match="Expected 16 action values"):
            split_bimanual_action(np.zeros(15, dtype=np.float32))
        with pytest.raises(ValueError, match="Expected 16 action values"):
            split_bimanual_action(np.zeros(17, dtype=np.float32))

    def test_split_rejects_empty(self):
        with pytest.raises(ValueError, match="Expected 16 action values"):
            split_bimanual_action([])


class TestRoundTrip:
    """BimanualAction ↔ as_vector ↔ split_bimanual_action ↔ fields match."""

    def test_round_trip(self):
        left_tcp = np.array([0.3, -0.2, 0.6, 0.0, 0.0, 0.0, 1.0], dtype=np.float32)
        right_tcp = np.array([0.3, 0.2, 0.6, 0.0, 0.0, 0.0, 1.0], dtype=np.float32)
        original = BimanualAction(
            left_tcp_pose=left_tcp,
            left_gripper_width=0.3,
            right_tcp_pose=right_tcp,
            right_gripper_width=0.7,
        )
        vector = original.as_vector()
        reconstructed = split_bimanual_action(vector)

        np.testing.assert_array_almost_equal(
            reconstructed.left_tcp_pose, original.left_tcp_pose
        )
        assert reconstructed.left_gripper_width == pytest.approx(
            original.left_gripper_width
        )
        np.testing.assert_array_almost_equal(
            reconstructed.right_tcp_pose, original.right_tcp_pose
        )
        assert reconstructed.right_gripper_width == pytest.approx(
            original.right_gripper_width
        )

    def test_round_trip_many_random(self):
        """Round-trip holds for random 16-D vectors."""
        rng = np.random.default_rng(42)
        for _ in range(20):
            vec = rng.uniform(-1, 1, size=16).astype(np.float32)
            action = split_bimanual_action(vec)
            reconstructed = action.as_vector()
            np.testing.assert_array_almost_equal(reconstructed, vec)
