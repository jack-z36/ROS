"""L2-05 action output adapter (deploy_042).

Pure RAM conversion from a PASS / ADJUSTED ``SafetyResult`` into a complete C4
``TopicPayloadBundle``. Implements:

- B1 ``build_topic_payloads`` — orchestration (C9 -> C10 x2 -> C11 x2 -> C4).
- C9 ``require_publishable_action`` — re-validate the publishable contract.
- C10 ``build_arm_pose_target`` — one TCP7 + frame -> frozen C3.
- C11 ``map_gripper_command`` — one gripper [0,1] -> 0..100 output domain.

No ROS import, no mutable cross-call state, no TF, no publish. The output is
transport-neutral RAM; deploy_043 / deploy_044 consume it downstream.
"""

from __future__ import annotations

import math
from typing import Sequence

import numpy as np

from model_deploy.act.config.schema import CommandOutputConfig
from model_deploy.act.types.action_publish import ArmPoseTarget, TopicPayloadBundle
from model_deploy.act.types.action_spec import ActionSpec
from model_deploy.act.types.safety_result import SafetyResult, SafetyStatus


# ---------------------------------------------------------------------------
# Contract error (stable; downstream B3 treats it like a safety REJECTED)
# ---------------------------------------------------------------------------


class ActionPublishContractError(ValueError):
    """Raised when a frozen publish-contract invariant is violated.

    B3 (deploy_044) maps this to a REJECTED publish outcome and never enters
    B2 packing. It is a subclass of ``ValueError`` so naive callers still see a
    plain failure rather than a swallowed attribute error.
    """


# ---------------------------------------------------------------------------
# C9 require_publishable_action
# ---------------------------------------------------------------------------


def require_publishable_action(result: SafetyResult) -> ActionSpec:
    """Re-validate a RAM ``SafetyResult`` and return its ``ActionSpec``.

    Raises ``ActionPublishContractError`` when:

    - status is REJECTED (or otherwise not PASS / ADJUSTED);
    - the action is not a non-None ``ActionSpec``;
    - the flat action vector is not exactly 16D or contains non-finite values;
    - either gripper value leaves the ``[0, 1]`` training domain.
    """
    if result.status not in (SafetyStatus.PASS, SafetyStatus.ADJUSTED):
        raise ActionPublishContractError(
            f"require_publishable_action: status must be PASS/ADJUSTED, "
            f"got {result.status.value}"
        )
    action = result.action
    if not isinstance(action, ActionSpec):
        raise ActionPublishContractError(
            "require_publishable_action: PASS/ADJUSTED result must carry an ActionSpec"
        )
    vector = action.as_vector()
    if vector.shape != (16,):
        raise ActionPublishContractError(
            f"require_publishable_action: action vector must have shape (16,), "
            f"got {tuple(vector.shape)}"
        )
    if not np.all(np.isfinite(vector)):
        raise ActionPublishContractError(
            "require_publishable_action: action vector contains non-finite values"
        )
    if not (0.0 <= float(action.left_gripper) <= 1.0):
        raise ActionPublishContractError(
            f"require_publishable_action: left_gripper must be in [0,1], "
            f"got {action.left_gripper!r}"
        )
    if not (0.0 <= float(action.right_gripper) <= 1.0):
        raise ActionPublishContractError(
            f"require_publishable_action: right_gripper must be in [0,1], "
            f"got {action.right_gripper!r}"
        )
    return action


# ---------------------------------------------------------------------------
# C10 build_arm_pose_target
# ---------------------------------------------------------------------------


def build_arm_pose_target(tcp7: Sequence[float], pose_frame_id: str) -> ArmPoseTarget:
    """Build a frozen C3 ``ArmPoseTarget`` from a RAM TCP7 and single frame.

    ``tcp7`` is ``xyz(3) + quaternion(4)``. The same ``pose_frame_id`` is used
    for left and right arms (no per-arm fake frame, no TF).

    Raises ``ActionPublishContractError`` on a wrong length, non-finite value,
    or empty/whitespace frame.
    """
    if not isinstance(pose_frame_id, str) or pose_frame_id.strip() == "":
        raise ActionPublishContractError(
            "build_arm_pose_target: pose_frame_id must be a non-empty string"
        )
    if len(tcp7) != 7:
        raise ActionPublishContractError(
            f"build_arm_pose_target: tcp7 must have length 7, got {len(tcp7)}"
        )
    values: tuple[float, ...] = tuple(float(x) for x in tcp7)
    for i, v in enumerate(values):
        if not math.isfinite(v):
            raise ActionPublishContractError(
                f"build_arm_pose_target: tcp7[{i}] must be finite, got {v!r}"
            )
    return ArmPoseTarget(
        frame_id=pose_frame_id,
        position_xyz=tuple(values[0:3]),
        quaternion_xyzw=tuple(values[3:7]),
    )


# ---------------------------------------------------------------------------
# C11 map_gripper_command
# ---------------------------------------------------------------------------


def map_gripper_command(value: float, config: CommandOutputConfig) -> float:
    """Map one gripper value from the input domain to the output domain.

    Linearly maps ``[gripper_input_min, gripper_input_max]`` to
    ``[gripper_output_min, gripper_output_max]``:

        out = out_min + (value - in_min) / (in_max - in_min) * (out_max - out_min)

    Default C7 config maps ``0 -> 0``, ``0.5 -> 50``, ``1 -> 100``.

    Raises ``ActionPublishContractError`` (never clips) when the value is out of
    the input domain, non-finite, or the configured range is invalid. Compat
    with already-scaled 50/100 inputs is deliberately rejected.
    """
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ActionPublishContractError(
            f"map_gripper_command: value must be a float, got {type(value).__name__}"
        )
    if not math.isfinite(value):
        raise ActionPublishContractError(
            f"map_gripper_command: value must be finite, got {value!r}"
        )
    in_min = float(config.gripper_input_min)
    in_max = float(config.gripper_input_max)
    out_min = float(config.gripper_output_min)
    out_max = float(config.gripper_output_max)
    if not (math.isfinite(in_min) and math.isfinite(in_max) and in_min < in_max):
        raise ActionPublishContractError(
            "map_gripper_command: invalid gripper input range in config"
        )
    if not (math.isfinite(out_min) and math.isfinite(out_max) and out_min < out_max):
        raise ActionPublishContractError(
            "map_gripper_command: invalid gripper output range in config"
        )
    if value < in_min or value > in_max:
        raise ActionPublishContractError(
            f"map_gripper_command: value {value!r} out of input domain "
            f"[{in_min}, {in_max}]; refusing to clip"
        )
    ratio = (value - in_min) / (in_max - in_min)
    return out_min + ratio * (out_max - out_min)


# ---------------------------------------------------------------------------
# B1 build_topic_payloads (orchestration)
# ---------------------------------------------------------------------------


def build_topic_payloads(
    safety_result: SafetyResult,
    config: CommandOutputConfig,
) -> TopicPayloadBundle:
    """Convert a publishable ``SafetyResult`` into a complete C4 payload bundle.

    Order: C9 -> 16D tuple -> C10 x2 with ``config.pose_frame_id`` -> C11 x2
    -> construct C4 exactly once. Any sub-step exception propagates, so a
    partial C4 is never returned.
    """
    action = require_publishable_action(safety_result)
    policy_vector: tuple[float, ...] = tuple(float(x) for x in action.as_vector())

    left_arm = build_arm_pose_target(action.left_tcp_action, config.pose_frame_id)
    right_arm = build_arm_pose_target(action.right_tcp_action, config.pose_frame_id)

    left_gripper = map_gripper_command(float(action.left_gripper), config)
    right_gripper = map_gripper_command(float(action.right_gripper), config)

    return TopicPayloadBundle(
        policy_action=policy_vector,
        left_arm=left_arm,
        right_arm=right_arm,
        left_gripper=left_gripper,
        right_gripper=right_gripper,
    )


__all__ = [
    "ActionPublishContractError",
    "build_topic_payloads",
    "require_publishable_action",
    "build_arm_pose_target",
    "map_gripper_command",
]
