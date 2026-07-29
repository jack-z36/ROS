"""Tests for ``_width_to_pose`` — the gripper width → Pose packing contract.

The node publishes gripper state as ``geometry_msgs/Pose`` with the normalized
width carried in ``position.x`` so it matches ACT's ``decode_gripper_width``
Pose branch. These tests pin that contract.
"""

import pytest

pytest.importorskip("geometry_msgs", reason="ROS geometry_msgs not sourced")

from elephant_gripper.ui.elephant_gripper_node import _width_to_pose


def test_width_goes_to_position_x():
    pose = _width_to_pose(0.07)
    assert pose.position.x == pytest.approx(0.07)


def test_orientation_is_valid_unit_quaternion():
    pose = _width_to_pose(0.5)
    assert pose.orientation.w == pytest.approx(1.0)
    assert pose.orientation.x == pytest.approx(0.0)
    assert pose.orientation.y == pytest.approx(0.0)
    assert pose.orientation.z == pytest.approx(0.0)


def test_other_position_fields_are_zero():
    pose = _width_to_pose(0.3)
    assert pose.position.y == pytest.approx(0.0)
    assert pose.position.z == pytest.approx(0.0)


@pytest.mark.parametrize("width", [0.0, 0.01, 0.5, 1.0])
def test_act_decoder_reads_back_width(width):
    """Cross-check: ACT's own decoder must read the packed width back.

    Skipped gracefully when the ACT package is not importable (e.g. isolated
    colcon test env without model_deploy.act on the path); the core packing
    contract above is what this package owns.
    """
    decode = pytest.importorskip(
        "model_deploy.act.ui.observation_ros_adapter",
        reason="ACT package not importable in this environment",
    ).decode_gripper_width
    pose = _width_to_pose(width)
    assert decode(pose) == pytest.approx(width)
