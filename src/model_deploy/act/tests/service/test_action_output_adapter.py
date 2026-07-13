"""Tests for deploy_042 B1/C9-C11 action output adapter (G04-G06).

Pure RAM unit tests: no ROS, no hardware, no cross-call mutable state.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from model_deploy.act.config.schema import CommandOutputConfig
from model_deploy.act.types.action_publish import ArmPoseTarget, TopicPayloadBundle
from model_deploy.act.types.action_spec import ActionSpec
from model_deploy.act.types.safety_result import SafetyFinding, SafetyResult, SafetyStatus

from model_deploy.act.service.action_output_adapter import (
    ActionPublishContractError,
    build_arm_pose_target,
    build_topic_payloads,
    map_gripper_command,
    require_publishable_action,
)


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

LEFT_TCP = [0.10, 0.20, 0.30, 0.0, 0.0, 0.0, 1.0]   # xyz(3) + xyzw(4)
RIGHT_TCP = [0.40, 0.50, 0.60, 0.0, 0.0, 0.0, 1.0]


def _make_spec(left_gripper: float = 0.0, right_gripper: float = 1.0) -> ActionSpec:
    return ActionSpec(
        left_tcp_action=np.array(LEFT_TCP, dtype=np.float32),
        right_tcp_action=np.array(RIGHT_TCP, dtype=np.float32),
        left_gripper=left_gripper,
        right_gripper=right_gripper,
    )


def _make_result(status: SafetyStatus, action: ActionSpec | None) -> SafetyResult:
    return SafetyResult(status=status, action=action, findings=(SafetyFinding(
        code=__import__(
            "model_deploy.act.types.safety_result", fromlist=["SafetyCode"]
        ).SafetyCode.TRANSLATION_LIMITED,
        side=None,
        before=0.0,
        after=0.0,
        detail="test finding",
    ),))


def _default_config() -> CommandOutputConfig:
    return CommandOutputConfig()


# ---------------------------------------------------------------------------
# G04 — PASS/ADJUSTED return complete C4; REJECTED/invalid fail stably
# ---------------------------------------------------------------------------


def test_pass_returns_complete_c4():
    result = _make_result(SafetyStatus.PASS, _make_spec(left_gripper=0.0, right_gripper=1.0))
    bundle = build_topic_payloads(result, _default_config())

    assert isinstance(bundle, TopicPayloadBundle)
    assert isinstance(bundle.policy_action, tuple)
    assert len(bundle.policy_action) == 16
    assert bundle.left_gripper == 0.0
    assert bundle.right_gripper == 100.0
    assert isinstance(bundle.left_arm, ArmPoseTarget)
    assert isinstance(bundle.right_arm, ArmPoseTarget)


def test_adjusted_returns_complete_c4():
    result = _make_result(SafetyStatus.ADJUSTED, _make_spec(left_gripper=0.5, right_gripper=0.5))
    bundle = build_topic_payloads(result, _default_config())

    assert len(bundle.policy_action) == 16
    assert bundle.left_gripper == 50.0
    assert bundle.right_gripper == 50.0


def test_rejected_result_raises():
    # REJECTED safety results must carry action=None (frozen invariant).
    result = _make_result(SafetyStatus.REJECTED, None)
    with pytest.raises(ActionPublishContractError):
        build_topic_payloads(result, _default_config())


def test_c9_rejected_raises():
    with pytest.raises(ActionPublishContractError):
        require_publishable_action(_make_result(SafetyStatus.REJECTED, None))


def test_non_finite_vector_raises():
    bad = ActionSpec(
        left_tcp_action=np.array([math.nan, 0.2, 0.3, 0.0, 0.0, 0.0, 1.0], dtype=np.float32),
        right_tcp_action=np.array(RIGHT_TCP, dtype=np.float32),
        left_gripper=0.0,
        right_gripper=1.0,
    )
    with pytest.raises(ActionPublishContractError):
        require_publishable_action(_make_result(SafetyStatus.PASS, bad))


def test_gripper_out_of_domain_raises():
    with pytest.raises(ActionPublishContractError):
        require_publishable_action(
            _make_result(SafetyStatus.PASS, _make_spec(left_gripper=2.0))
        )
    with pytest.raises(ActionPublishContractError):
        require_publishable_action(
            _make_result(SafetyStatus.PASS, _make_spec(right_gripper=-0.5))
        )


def test_wrong_vector_shape_raises():
    bad = ActionSpec(
        left_tcp_action=np.array([0.1, 0.2, 0.3, 0.0, 0.0, 0.0, 1.0, 99.0], dtype=np.float32),
        right_tcp_action=np.array(RIGHT_TCP, dtype=np.float32),
        left_gripper=0.0,
        right_gripper=1.0,
    )
    with pytest.raises(ActionPublishContractError):
        require_publishable_action(_make_result(SafetyStatus.PASS, bad))


# ---------------------------------------------------------------------------
# G05 — gripper mapping 0/0.5/1 -> 0/50/100; 50/100 input fails (no clip)
# ---------------------------------------------------------------------------


def test_gripper_mapping_endpoints():
    cfg = _default_config()
    assert map_gripper_command(0.0, cfg) == 0.0
    assert map_gripper_command(0.5, cfg) == 50.0
    assert map_gripper_command(1.0, cfg) == 100.0


def test_gripper_out_of_domain_fails():
    cfg = _default_config()
    for bad in (50.0, 100.0, -0.1, 1.5):
        with pytest.raises(ActionPublishContractError):
            map_gripper_command(bad, cfg)


def test_gripper_non_finite_fails():
    with pytest.raises(ActionPublishContractError):
        map_gripper_command(math.inf, _default_config())


def test_gripper_custom_range_generalizes():
    cfg = CommandOutputConfig(
        gripper_input_min=0.0,
        gripper_input_max=1.0,
        gripper_output_min=10.0,
        gripper_output_max=90.0,
    )
    assert map_gripper_command(0.0, cfg) == 10.0
    assert map_gripper_command(0.5, cfg) == 50.0
    assert map_gripper_command(1.0, cfg) == 90.0


# ---------------------------------------------------------------------------
# G06 — left/right TCP split, single frame, xyzw/metric unchanged
# ---------------------------------------------------------------------------


def test_tcp_split_and_single_frame():
    result = _make_result(SafetyStatus.PASS, _make_spec(left_gripper=0.25, right_gripper=0.75))
    cfg = _default_config()
    bundle = build_topic_payloads(result, cfg)

    assert bundle.left_arm.frame_id == cfg.pose_frame_id
    assert bundle.right_arm.frame_id == cfg.pose_frame_id
    # single shared frame
    assert bundle.left_arm.frame_id == bundle.right_arm.frame_id
    # values preserved exactly (xyzw + metric xyz unchanged; source is float32)
    left32 = np.array(LEFT_TCP, dtype=np.float32).tolist()
    right32 = np.array(RIGHT_TCP, dtype=np.float32).tolist()
    assert tuple(bundle.left_arm.position_xyz) == tuple(left32[0:3])
    assert tuple(bundle.left_arm.quaternion_xyzw) == tuple(left32[3:7])
    assert tuple(bundle.right_arm.position_xyz) == tuple(right32[0:3])
    assert tuple(bundle.right_arm.quaternion_xyzw) == tuple(right32[3:7])


def test_build_arm_pose_target_direct():
    arm = build_arm_pose_target(LEFT_TCP, "base")
    assert arm.frame_id == "base"
    assert tuple(arm.position_xyz) == tuple(LEFT_TCP[0:3])
    assert tuple(arm.quaternion_xyzw) == tuple(LEFT_TCP[3:7])


def test_build_arm_pose_target_bad_length():
    with pytest.raises(ActionPublishContractError):
        build_arm_pose_target([0.1, 0.2, 0.3], "base")


def test_build_arm_pose_target_non_finite():
    with pytest.raises(ActionPublishContractError):
        build_arm_pose_target([0.1, 0.2, 0.3, 0.0, 0.0, 0.0, math.nan], "base")


def test_build_arm_pose_target_empty_frame():
    with pytest.raises(ActionPublishContractError):
        build_arm_pose_target(LEFT_TCP, "   ")


# ---------------------------------------------------------------------------
# Structural guarantees
# ---------------------------------------------------------------------------


def test_no_partial_c4_on_gripper_failure():
    # A PASS result but with an out-of-domain gripper must raise and never
    # construct a partial C4 (B1 builds C4 only after all helpers succeed).
    result = _make_result(SafetyStatus.PASS, _make_spec(left_gripper=0.5, right_gripper=2.0))
    with pytest.raises(ActionPublishContractError):
        build_topic_payloads(result, _default_config())


def test_module_has_no_ros_import():
    import model_deploy.act.service.action_output_adapter as mod

    forbidden = ("rclpy", "geometry_msgs", "std_msgs", "sensor_msgs")
    for name in forbidden:
        assert not hasattr(mod, name), f"module must not expose {name}"
    # No module-level mutable cross-call state beyond the error class.
    for attr in ("_last_bundle", "_cache", "_state"):
        assert not hasattr(mod, attr)
