"""State encoding contract for Pi0.5 bimanual deployment.

TO-BE state semantics (D8/D9):
  16D (first release, no tactile) = left_tcp_pose[7] + right_tcp_pose[7]
                                  + left_gripper_width[1] + right_gripper_width[1]
Segments are grouped "all-left → all-right" (NOT interleaved like action).
TCP pose is absolute target in quaternion xyzw (m + normalized quaternion).
Gripper width is normalized [0,1] (0=closed, 1=fully open).

Tactile reservation (future):
  include_tactile=True appends tactile segments at [16,32), producing 32D total.
  Tactile aggregation (6×15→4D per chip) is implemented in a later version.

See: 数据清洗交付说明.md L11-18 for the authoritative state schema,
     L35-36 for the state/action segment-order warning."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np

from pi05.common.robot.action_spec import STATE_DIM, TCP_POSE_DOF, GRIPPER_WIDTH_DOF


@dataclass(frozen=True)
class BimanualState:
    """Structured state used to build the 16-D (or 32-D with tactile) policy observation vector.

    Segment order is 'all-left → all-right' (NOT interleaved like action):
      left_tcp_pose[7] + right_tcp_pose[7] + left_gripper_width[1] + right_gripper_width[1]
    TCP pose is quaternion xyzw (m + normalized quaternion).
    Gripper width is normalized [0,1] (0=closed, 1=fully open).
    """

    left_tcp_pose: np.ndarray       # 7D: x, y, z, qx, qy, qz, qw
    right_tcp_pose: np.ndarray      # 7D: x, y, z, qx, qy, qz, qw
    left_gripper_width: float       # normalized [0,1], 0=closed, 1=fully open
    right_gripper_width: float      # normalized [0,1]


def encode_bimanual_state(
    state: BimanualState,
    include_tactile: bool = False,
    tactile_segments: tuple[np.ndarray, ...] | None = None,
) -> np.ndarray:
    """Encode a structured bimanual state into the canonical state vector.

    First release (include_tactile=False): 16-D vector.
      Segment order (all-left → all-right):
        left_tcp_pose[7] + right_tcp_pose[7] + left_gripper_width[1] + right_gripper_width[1]

    With tactile (include_tactile=True): 32-D vector.
      Appends tactile segments [16,32) on top of the 16-D base.

    Args:
        state: BimanualState with TCP pose and gripper width fields.
        include_tactile: If True, append tactile segments for 32-D output.
        tactile_segments: Tuple of 4 numpy arrays, each 4-D (aggregated tactile).
                          Required when include_tactile=True.

    Returns:
        np.ndarray: float32 vector of dim STATE_DIM (16) or 32 (with tactile).
    """
    base = np.concatenate(
        [
            _vector(state.left_tcp_pose, TCP_POSE_DOF, "left_tcp_pose"),
            _vector(state.right_tcp_pose, TCP_POSE_DOF, "right_tcp_pose"),
            np.asarray([state.left_gripper_width], dtype=np.float32),
            np.asarray([state.right_gripper_width], dtype=np.float32),
        ]
    )
    if not include_tactile:
        vector = base.astype(np.float32, copy=False)
        if vector.size != STATE_DIM:
            raise ValueError(
                f"Expected encoded state dim {STATE_DIM} (tactile disabled), "
                f"got {vector.size}"
            )
        return vector

    if tactile_segments is None:
        raise ValueError(
            "include_tactile=True requires tactile_segments (4 arrays, each 4-D)"
        )
    tactile_parts = [
        _vector(seg, 4, f"tactile_segment[{i}]") for i, seg in enumerate(tactile_segments)
    ]
    vector = np.concatenate([base.astype(np.float32, copy=False), *tactile_parts])
    TACTILE_DIM = 32
    if vector.size != TACTILE_DIM:
        raise ValueError(
            f"Expected encoded state dim {TACTILE_DIM} (tactile enabled), "
            f"got {vector.size}"
        )
    return vector


def _vector(value: Iterable[float] | np.ndarray, dim: int, name: str) -> np.ndarray:
    vector = np.asarray(value, dtype=np.float32).reshape(-1)
    if vector.size != dim:
        raise ValueError(f"{name} must contain {dim} values, got {vector.size}")
    return vector
