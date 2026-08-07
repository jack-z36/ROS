"""Tests for inference-reference relative TCP action decoding."""

import numpy as np
import pytest

from model_deploy.act.service.relative_tcp_action_decoder import (
    RelativeTcpActionDecoder,
)
from model_deploy.act.types.action_chunk import ActionChunk
from model_deploy.act.types.observation import ObservationState
from model_deploy.act.types.relative_action_chunk import RelativeActionChunk


def _state() -> ObservationState:
    return ObservationState(
        left_tcp_position=np.array([1.0, 2.0, 3.0], dtype=np.float32),
        left_tcp_orientation=np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float32),
        left_gripper_width=0.2,
        right_tcp_position=np.array([-1.0, -2.0, -3.0], dtype=np.float32),
        right_tcp_orientation=np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float32),
        right_gripper_width=0.8,
    )


def _row(left_tcp, right_tcp, left_gripper=0.4, right_gripper=0.6):
    return np.asarray(
        [*left_tcp, *right_tcp, left_gripper, right_gripper], dtype=np.float32
    )


def test_identity_relative_pose_returns_reference_pose():
    identity_tcp = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0]
    result = RelativeTcpActionDecoder().decode(
        RelativeActionChunk(_row(identity_tcp, identity_tcp)[None, :]), _state()
    )

    assert isinstance(result, ActionChunk)
    np.testing.assert_allclose(result.actions[0, 0:7], [1.0, 2.0, 3.0, 0, 0, 0, 1])
    np.testing.assert_allclose(result.actions[0, 7:14], [-1.0, -2.0, -3.0, 0, 0, 0, 1])
    np.testing.assert_allclose(result.actions[0, 14:16], [0.4, 0.6])


def test_local_translation_is_rotated_by_reference_orientation():
    angle = np.pi / 2.0
    state = _state()
    state = ObservationState(
        left_tcp_position=state.left_tcp_position,
        left_tcp_orientation=np.array([0, 0, np.sin(angle / 2), np.cos(angle / 2)], dtype=np.float32),
        left_gripper_width=state.left_gripper_width,
        right_tcp_position=state.right_tcp_position,
        right_tcp_orientation=state.right_tcp_orientation,
        right_gripper_width=state.right_gripper_width,
    )
    tcp = [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0]
    result = RelativeTcpActionDecoder().decode(
        RelativeActionChunk(_row(tcp, [0, 0, 0, 0, 0, 0, 1])[None, :]), state
    )

    np.testing.assert_allclose(result.actions[0, 0:3], [1.0, 3.0, 3.0], atol=1e-6)


def test_every_row_uses_same_reference_and_is_not_cumulative():
    identity = [0, 0, 0, 0, 0, 0, 1]
    row_a = _row([1, 0, 0, *identity[3:]], [0, 0, 0, *identity[3:]])
    row_b = _row([2, 0, 0, *identity[3:]], [0, 0, 0, *identity[3:]])
    result = RelativeTcpActionDecoder().decode(
        RelativeActionChunk(np.stack([row_a, row_b])), _state()
    )

    np.testing.assert_allclose(result.actions[:, 0], [2.0, 3.0])


def test_non_unit_relative_quaternion_is_normalized():
    identity = [0, 0, 0, 0, 0, 0, 2]
    result = RelativeTcpActionDecoder().decode(
        RelativeActionChunk(_row(identity, identity)[None, :]), _state()
    )

    np.testing.assert_allclose(result.actions[0, 3:7], [0, 0, 0, 1])
    np.testing.assert_allclose(result.actions[0, 10:14], [0, 0, 0, 1])


@pytest.mark.parametrize(
    "bad",
    [
        np.full((1, 16), np.nan, dtype=np.float32),
    ],
)
def test_invalid_relative_chunk_is_rejected(bad):
    with pytest.raises((ValueError, TypeError)):
        RelativeActionChunk(bad)


def test_zero_relative_quaternion_is_rejected_by_decoder():
    row = _row(
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
    )[None, :]
    with pytest.raises(ValueError, match="invalid norm"):
        RelativeTcpActionDecoder().decode(RelativeActionChunk(row), _state())
