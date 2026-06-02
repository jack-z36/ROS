"""Arm-base TCP pose schema definitions.

Defines the code-level contract for:
- ArmBaseTcpPose: TCP pose in left/right arm base coordinate frame
- WorkFrameInArmBasePose: Work frame pose in arm base coordinates
- McapAArmBasePoseChannel: MCAP_A channel config for arm-base pose topics

These types replace the legacy common_frame → robot_base pipeline with a
direct left/right arm-base coordinate semantic. The official transform API
is rmdk.Algo.rm_algo_workframe2base().
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class HandType(str, Enum):
    """Left or right hand identifier matching the dual-arm setup."""

    LEFT = "left"
    RIGHT = "right"


class FrameIdType(str, Enum):
    """Coordinate frame identifiers for arm-base TCP poses."""

    LEFT_ARM_BASE = "left_arm_base"
    RIGHT_ARM_BASE = "right_arm_base"


@dataclass
class ArmBaseTcpPose:
    """TCP pose in the corresponding arm base coordinate frame.

    Describes the end-effector (TCP) pose in either the left or right
    mechanical arm's base coordinate system.  This is the primary output
    of the workframe-to-base transform chain and the input to Scene 2
    pose filtering and MCAP_A export.

    Official API trace:
        Algo.rm_algo_workframe2base() via the RealMan rmdk Python SDK.
    """

    hand: HandType | str
    """Left or right hand indicator."""

    frame_id: FrameIdType | str
    """Output coordinate frame: left_arm_base or right_arm_base."""

    position_m: dict[str, float]
    """TCP position in metres, with keys {'x', 'y', 'z'}."""

    orientation: dict[str, float]
    """TCP orientation as quaternion with keys {'x', 'y', 'z', 'w'}.

    Quaternion order: (x, y, z, w) following ROS geometry_msgs convention.
    """

    official_api: str = "Algo.rm_algo_workframe2base"
    """Official RealMan SDK function name used to compute this pose."""

    # -- optional traceability fields -------------------------------------------
    source_camera_pose_ref: str | None = None
    """Optional reference to the source camera-frame pose identifier."""

    source_tcp_in_camera_ref: str | None = None
    """Optional reference to the TCP-in-camera extrinsic or pose identifier."""

    source_work_frame_in_base_ref: str | None = None
    """Optional reference to the work-frame-in-base pose identifier."""

    timestamp_ns: int | None = None
    """Sample timestamp in nanoseconds, if available."""

    def __post_init__(self) -> None:
        if self.hand not in (HandType.LEFT, HandType.RIGHT):
            raise ValueError(
                f"Invalid hand: {self.hand!r}. Must be HandType.LEFT or HandType.RIGHT."
            )
        if self.frame_id not in (FrameIdType.LEFT_ARM_BASE, FrameIdType.RIGHT_ARM_BASE):
            raise ValueError(
                f"Invalid frame_id: {self.frame_id!r}. "
                "Must be FrameIdType.LEFT_ARM_BASE or FrameIdType.RIGHT_ARM_BASE."
            )
        if not isinstance(self.position_m, dict):
            raise TypeError("position_m must be a dict")
        if not isinstance(self.orientation, dict):
            raise TypeError("orientation must be a dict")


@dataclass
class WorkFrameInArmBasePose:
    """Work frame pose in the corresponding arm base coordinate frame.

    Describes the user-defined work coordinate system origin and orientation
    relative to either the left or right mechanical arm's base frame.
    This is one of the two inputs to the official transform function
    (the other being TCP-in-camera pose).
    """

    hand: HandType | str
    """Left or right hand indicator."""

    base_frame_id: FrameIdType | str
    """Base coordinate frame: left_arm_base or right_arm_base."""

    position_m: dict[str, float]
    """Work frame origin in metres, with keys {'x', 'y', 'z'}."""

    rotation_euler_rad: dict[str, float] | None = None
    """Work frame Euler rotation in radians, with keys {'rx', 'ry', 'rz'}."""

    orientation: dict[str, float] | None = None
    """Deprecated read compatibility for legacy quaternion configuration."""

    work_frame_id: str = "work"
    """User-assigned work frame name for traceability."""

    source: str = "user_input"
    """Provenance: user_input, calibration_file, or external_config."""

    valid_from: str | None = None
    """Optional data batch or collection task identifier."""

    def __post_init__(self) -> None:
        if self.hand not in (HandType.LEFT, HandType.RIGHT):
            raise ValueError(
                f"Invalid hand: {self.hand!r}. Must be HandType.LEFT or HandType.RIGHT."
            )
        if self.base_frame_id not in (FrameIdType.LEFT_ARM_BASE, FrameIdType.RIGHT_ARM_BASE):
            raise ValueError(
                f"Invalid base_frame_id: {self.base_frame_id!r}. "
                "Must be FrameIdType.LEFT_ARM_BASE or FrameIdType.RIGHT_ARM_BASE."
            )
        if not isinstance(self.position_m, dict):
            raise TypeError("position_m must be a dict")
        if not isinstance(self.rotation_euler_rad, dict) and not isinstance(self.orientation, dict):
            raise TypeError("rotation_euler_rad must be a dict")


@dataclass
class McapAArmBasePoseChannel:
    """MCAP_A channel definition for left/right arm-base TCP poses.

    Constrains the MCAP_A output channel names, ROS message schema,
    timestamp policy and frame-id policy for the left and right
    arm-base TCP pose topics.  These channels are required for
    downstream LeRobot v3 dataset export.
    """

    left_tcp_pose_channel: str = "/left_arm_base_tcp_pose"
    """ROS topic for the left arm-base TCP pose in MCAP_A output."""

    right_tcp_pose_channel: str = "/right_arm_base_tcp_pose"
    """ROS topic for the right arm-base TCP pose in MCAP_A output."""

    message_schema: str = "geometry_msgs/Pose"
    """ROS message schema for both arm-base pose channels."""

    timestamp_policy: str = "preserve_original"
    """Timestamp handling: preserve_original, rewrite_to_log_time, etc."""

    frame_id_policy: str = "use_arm_base_frame"
    """Frame-id assignment: use_arm_base_frame, inherit_from_source, etc."""

    required_for_lerobot_v3_export: bool = True
    """Whether these channels are mandatory for LeRobot v3 export."""

    def __post_init__(self) -> None:
        if not self.left_tcp_pose_channel:
            raise ValueError("left_tcp_pose_channel is required and must not be empty")
        if not self.right_tcp_pose_channel:
            raise ValueError("right_tcp_pose_channel is required and must not be empty")
