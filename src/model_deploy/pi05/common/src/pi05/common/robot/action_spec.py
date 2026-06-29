"""Robot action layout shared by training and deployment.

The Pi0.5 policy emits a flat action vector. This module documents the vector
contract and provides small helpers for splitting or assembling that vector.

TO-BE action semantics (D11):
  16D = left_tcp_pose[7] + left_gripper_width[1]
      + right_tcp_pose[7] + right_gripper_width[1]
Segments are interleaved: left TCP+width, then right TCP+width.
TCP pose is absolute target in quaternion xyzw (m + normalized quaternion).
Gripper width is normalized [0,1] (0=closed, 1=fully open).
See: 数据清洗交付说明.md L25-28 for the authoritative action schema.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np


ARM_DOF = 6
ACTION_DIM = 16
STATE_DIM = 16                      # first release, no tactile; will become 32 later
TCP_POSE_DOF = 7
GRIPPER_WIDTH_DOF = 1
ARM_JOINT_NAMES = tuple(f"joint{i + 1}" for i in range(ARM_DOF))


@dataclass(frozen=True)
class BimanualAction:
    """Structured view of one policy action step.

    Fields represent absolute TCP target poses in arm-base coordinates
    and normalized gripper widths.  Quaternion order is xyzw.
    """

    left_tcp_pose: np.ndarray       # 7D: x, y, z, qx, qy, qz, qw
    left_gripper_width: float       # normalized [0,1], 0=closed, 1=fully open
    right_tcp_pose: np.ndarray      # 7D
    right_gripper_width: float      # normalized [0,1]

    def as_vector(self) -> np.ndarray:
        """Return the canonical 16-D action vector (interleaved order)."""
        return np.concatenate(
            [
                np.asarray(self.left_tcp_pose, dtype=np.float32).reshape(TCP_POSE_DOF),
                np.asarray([self.left_gripper_width], dtype=np.float32),
                np.asarray(self.right_tcp_pose, dtype=np.float32).reshape(TCP_POSE_DOF),
                np.asarray([self.right_gripper_width], dtype=np.float32),
            ]
        )


def split_bimanual_action(action: Iterable[float] | np.ndarray) -> BimanualAction:
    """Split a flat 16-D policy action into TCP pose and gripper width.

    Interleaved segment order:
      [0:7]   left_tcp_pose (xyz + quaternion xyzw)
      [7:8]   left_gripper_width
      [8:15]  right_tcp_pose (xyz + quaternion xyzw)
      [15:16] right_gripper_width
    """
    vector = np.asarray(action, dtype=np.float32).reshape(-1)
    if vector.size != ACTION_DIM:
        raise ValueError(f"Expected {ACTION_DIM} action values, got {vector.size}")
    return BimanualAction(
        left_tcp_pose=vector[0:TCP_POSE_DOF].copy(),
        left_gripper_width=float(vector[TCP_POSE_DOF]),
        right_tcp_pose=vector[
            TCP_POSE_DOF + GRIPPER_WIDTH_DOF : TCP_POSE_DOF + GRIPPER_WIDTH_DOF + TCP_POSE_DOF
        ].copy(),
        right_gripper_width=float(vector[TCP_POSE_DOF + GRIPPER_WIDTH_DOF + TCP_POSE_DOF]),
    )
