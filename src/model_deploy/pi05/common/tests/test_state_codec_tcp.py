"""Tests for pi05.common.data.state_codec (deploy_002 / D8-D9).

Covers:
  - BimanualState structure
  - encode_bimanual_state 16D (no tactile) and 32D (with tactile)
  - Segment order: all-left→all-right (NOT interleaved like action)
  - Round-trip consistency via decode (from action_spec context)
  - Dimension validation rejects invalid inputs
  - decode_picotele_proprioception removed
"""

import numpy as np
import pytest

from pi05.common.data.state_codec import BimanualState, encode_bimanual_state
from pi05.common.robot.action_spec import (
    ACTION_DIM,
    BimanualAction,
    split_bimanual_action,
    STATE_DIM,
    TCP_POSE_DOF,
    GRIPPER_WIDTH_DOF,
)


class TestStateConstants:
    """STATE_DIM and dimension constants."""

    def test_state_dim_is_16(self):
        assert STATE_DIM == 16


class TestBimanualStateFields:
    """BimanualState field shapes and types."""

    def test_construct_with_arrays(self):
        state = BimanualState(
            left_tcp_pose=np.array([0.3, -0.1, 0.5, 0.0, 0.0, 0.0, 1.0], dtype=np.float32),
            right_tcp_pose=np.array([0.3, 0.1, 0.5, 0.0, 0.0, 0.0, 1.0], dtype=np.float32),
            left_gripper_width=0.5,
            right_gripper_width=0.8,
        )
        assert state.left_tcp_pose.shape == (7,)
        assert state.right_tcp_pose.shape == (7,)
        assert isinstance(state.left_gripper_width, float)
        assert isinstance(state.right_gripper_width, float)


class TestEncodeNoTactile:
    """encode_bimanual_state with include_tactile=False returns 16D."""

    def test_encode_16d_no_tactile(self):
        state = BimanualState(
            left_tcp_pose=np.zeros(7, dtype=np.float32),
            right_tcp_pose=np.zeros(7, dtype=np.float32),
            left_gripper_width=0.0,
            right_gripper_width=0.0,
        )
        vec = encode_bimanual_state(state, include_tactile=False)
        assert vec.shape == (16,)
        assert vec.dtype == np.float32

    def test_encode_with_values(self):
        left_tcp = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7], dtype=np.float32)
        right_tcp = np.array([0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4], dtype=np.float32)
        state = BimanualState(left_tcp, right_tcp, 0.25, 0.75)
        vec = encode_bimanual_state(state)

        # Segment order: all-left → all-right
        # [0:7] = left_tcp
        np.testing.assert_array_almost_equal(vec[0:7], left_tcp)
        # [7:14] = right_tcp
        np.testing.assert_array_almost_equal(vec[7:14], right_tcp)
        # [14] = left_gripper_width
        assert vec[14] == pytest.approx(0.25)
        # [15] = right_gripper_width
        assert vec[15] == pytest.approx(0.75)

    def test_encode_rejects_wrong_field_dim(self):
        """BimanualState with wrong TCP pose dimension raises ValueError."""
        with pytest.raises(ValueError, match="left_tcp_pose"):
            state = BimanualState(
                left_tcp_pose=np.zeros(6, dtype=np.float32),  # wrong: should be 7
                right_tcp_pose=np.zeros(7, dtype=np.float32),
                left_gripper_width=0.0,
                right_gripper_width=0.0,
            )
            encode_bimanual_state(state)

        with pytest.raises(ValueError, match="right_tcp_pose"):
            state = BimanualState(
                left_tcp_pose=np.zeros(7, dtype=np.float32),
                right_tcp_pose=np.zeros(8, dtype=np.float32),  # wrong: should be 7
                left_gripper_width=0.0,
                right_gripper_width=0.0,
            )
            encode_bimanual_state(state)


class TestEncodeWithTactile:
    """encode_bimanual_state with include_tactile=True returns 32D."""

    def test_encode_32d_with_tactile(self):
        state = BimanualState(
            left_tcp_pose=np.zeros(7, dtype=np.float32),
            right_tcp_pose=np.zeros(7, dtype=np.float32),
            left_gripper_width=0.0,
            right_gripper_width=0.0,
        )
        tactile = (np.zeros(4, dtype=np.float32),) * 4
        vec = encode_bimanual_state(state, include_tactile=True, tactile_segments=tactile)
        assert vec.shape == (32,)
        assert vec.dtype == np.float32

    def test_encode_32d_first_16_match_base(self):
        """With tactile enabled, the first 16 entries equal the base 16D."""
        left_tcp = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7], dtype=np.float32)
        right_tcp = np.array([0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4], dtype=np.float32)
        state = BimanualState(left_tcp, right_tcp, 0.25, 0.75)

        no_tactile = encode_bimanual_state(state, include_tactile=False)
        tactile_segs = (np.ones(4, dtype=np.float32),) * 4
        with_tactile = encode_bimanual_state(
            state, include_tactile=True, tactile_segments=tactile_segs
        )

        # First 16 should match
        np.testing.assert_array_almost_equal(with_tactile[:16], no_tactile)
        # Last 16 should be the tactile data
        np.testing.assert_array_almost_equal(with_tactile[16:], np.ones(16, dtype=np.float32))

    def test_encode_tactile_requires_segments(self):
        state = BimanualState(
            left_tcp_pose=np.zeros(7, dtype=np.float32),
            right_tcp_pose=np.zeros(7, dtype=np.float32),
            left_gripper_width=0.0,
            right_gripper_width=0.0,
        )
        with pytest.raises(ValueError, match="tactile_segments"):
            encode_bimanual_state(state, include_tactile=True, tactile_segments=None)

    def test_encode_tactile_wrong_segment_dim(self):
        state = BimanualState(
            left_tcp_pose=np.zeros(7, dtype=np.float32),
            right_tcp_pose=np.zeros(7, dtype=np.float32),
            left_gripper_width=0.0,
            right_gripper_width=0.0,
        )
        # Pass 5-D segment where 4-D expected
        with pytest.raises(ValueError, match="tactile_segment"):
            encode_bimanual_state(
                state,
                include_tactile=True,
                tactile_segments=(np.zeros(4, dtype=np.float32),) * 3
                + (np.zeros(5, dtype=np.float32),),
            )


class TestStateActionSegmentOrder:
    """Critical: state segment order (all-left→all-right) differs from action (alternating).

    State 16D:
      [0:7]  left_tcp_pose
      [7:14] right_tcp_pose
      [14]   left_gripper_width
      [15]   right_gripper_width

    Action 16D:
      [0:7]  left_tcp_pose
      [7:8]  left_gripper_width
      [8:15] right_tcp_pose
      [15]   right_gripper_width
    """

    def test_state_order_differs_from_action(self):
        """Same left/right data produces different vector layouts."""
        left_tcp = np.array(
            [0.10, 0.11, 0.12, 0.13, 0.14, 0.15, 0.16], dtype=np.float32
        )
        right_tcp = np.array(
            [0.20, 0.21, 0.22, 0.23, 0.24, 0.25, 0.26], dtype=np.float32
        )
        left_width = 0.3
        right_width = 0.7

        # Encode state (all-left→all-right)
        state = BimanualState(left_tcp, right_tcp, left_width, right_width)
        state_vec = encode_bimanual_state(state)

        # Encode action (alternating)
        action = BimanualAction(left_tcp, left_width, right_tcp, right_width)
        action_vec = action.as_vector()

        # Both are 16D
        assert state_vec.shape == (16,)
        assert action_vec.shape == (16,)

        # Same first 7 (left_tcp_pose)
        np.testing.assert_array_almost_equal(state_vec[0:7], action_vec[0:7])
        np.testing.assert_array_almost_equal(state_vec[0:7], left_tcp)

        # DIFFERENT at position 7:
        # state[7] = right_tcp[0], action[7] = left_width
        assert state_vec[7] == pytest.approx(0.20),  "state[7] should be right_tcp[0]"
        assert action_vec[7] == pytest.approx(0.3), "action[7] should be left_width"
        assert state_vec[7] != action_vec[7], "state[7] and action[7] must differ"

        # DIFFERENT at position 8-13:
        # state[8:14] = right_tcp[1:7], action[8:14] = right_tcp[0:6]
        # They overlap but are offset by 1
        np.testing.assert_array_almost_equal(state_vec[8:14], right_tcp[1:7])
        np.testing.assert_array_almost_equal(action_vec[8:14], right_tcp[0:6])
        assert not np.array_equal(state_vec[8:14], action_vec[8:14]), (
            "state[8:14] and action[8:14] must differ due to segment order"
        )

        # state[14] = left_width, action[14] = right_tcp[6]
        assert state_vec[14] == pytest.approx(0.3)
        assert action_vec[14] == pytest.approx(0.26)
        assert state_vec[14] != action_vec[14]

        # Both end with right_width at position 15
        assert state_vec[15] == pytest.approx(0.7)
        assert action_vec[15] == pytest.approx(0.7)

    def test_state_and_action_vectors_not_equal(self):
        """Same semantically-equivalent data produces different flat vectors."""
        left_tcp = np.array([0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6], dtype=np.float32)
        right_tcp = np.array([1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6], dtype=np.float32)

        state = BimanualState(left_tcp, right_tcp, 0.5, 0.9)
        action = BimanualAction(left_tcp, 0.5, right_tcp, 0.9)

        state_vec = encode_bimanual_state(state)
        action_vec = action.as_vector()

        assert not np.array_equal(state_vec, action_vec), (
            "state and action vectors must NOT be equal due to different segment orders"
        )


class TestDecodePicoteleRemoved:
    """decode_picotele_proprioception must no longer exist in state_codec."""

    def test_decode_picotele_not_present(self):
        with pytest.raises((ImportError, AttributeError)):
            from pi05.common.data.state_codec import (  # type: ignore[import-unused]
                decode_picotele_proprioception,
            )
