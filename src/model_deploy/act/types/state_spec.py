"""16D observation state specification for ACT model deployment.

Defines the dimension, segment layout, field semantics, and value-domain
of the 16-dimensional observation state vector used by the ACT policy.

Segment layout:
    left_tcp_pose        : [0:7)   xyz(3) + quaternion(4)
    right_tcp_pose       : [7:14)  xyz(3) + quaternion(4)
    left_gripper_width   : [14:15) float
    right_gripper_width  : [15:16) float
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

# ---------------------------------------------------------------------------
# Dimension constants
# ---------------------------------------------------------------------------

STATE_DIM: int = 16

LEFT_TCP_POSE_DIM: int = 7
RIGHT_TCP_POSE_DIM: int = 7
LEFT_GRIPPER_WIDTH_DIM: int = 1
RIGHT_GRIPPER_WIDTH_DIM: int = 1

_SEGMENT_NAMES: tuple[str, str, str, str] = (
    "left_tcp_pose",
    "right_tcp_pose",
    "left_gripper_width",
    "right_gripper_width",
)

_SEGMENT_DIMS: tuple[int, int, int, int] = (
    LEFT_TCP_POSE_DIM,
    RIGHT_TCP_POSE_DIM,
    LEFT_GRIPPER_WIDTH_DIM,
    RIGHT_GRIPPER_WIDTH_DIM,
)

_SEGMENT_OFFSETS: tuple[int, int, int, int] = (0, 7, 14, 15)


# ---------------------------------------------------------------------------
# StateSpec
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class StateSpec:
    """Immutable specification of the 16D observation state layout.

    Carries segment names, dimensions, and offsets so downstream code
    can interpret flat state vectors without guessing.
    """

    segment_names: tuple[str, str, str, str] = field(default=_SEGMENT_NAMES)
    segment_dims: tuple[int, int, int, int] = field(default=_SEGMENT_DIMS)
    segment_offsets: tuple[int, int, int, int] = field(default=_SEGMENT_OFFSETS)

    @property
    def total_dim(self) -> int:
        """Total state dimension (always 16 for ACT)."""
        return STATE_DIM


# ---------------------------------------------------------------------------
# Pure functions
# ---------------------------------------------------------------------------


def ensure_state_vector(flat: np.ndarray | list | tuple) -> np.ndarray:
    """Validate and normalise a flat state vector to 16D float32.

    Args:
        flat: A list, tuple, or numpy array representing a flat state vector.

    Returns:
        A 1-D float32 ``np.ndarray`` of length ``STATE_DIM`` (16).

    Raises:
        ValueError: If the input does not have exactly 16 elements.
    """
    arr = np.asarray(flat, dtype=np.float32).ravel()
    if arr.shape[0] != STATE_DIM:
        raise ValueError(
            f"Expected state vector of length {STATE_DIM}, got {arr.shape[0]}"
        )
    return arr


def encode_state(
    left_tcp_pose: np.ndarray | list | tuple,
    right_tcp_pose: np.ndarray | list | tuple,
    left_gripper_width: float,
    right_gripper_width: float,
) -> np.ndarray:
    """Encode structured observation fields into a 16D float32 vector.

    Args:
        left_tcp_pose:  7-element array (xyz + quaternion).
        right_tcp_pose: 7-element array (xyz + quaternion).
        left_gripper_width:  Scalar gripper width [0, 1].
        right_gripper_width: Scalar gripper width [0, 1].

    Returns:
        A 1-D float32 ``np.ndarray`` of length 16.

    Raises:
        ValueError: If any segment has an unexpected dimension.
    """
    left_tcp = np.asarray(left_tcp_pose, dtype=np.float32).ravel()
    right_tcp = np.asarray(right_tcp_pose, dtype=np.float32).ravel()
    left_grip = np.asarray([left_gripper_width], dtype=np.float32).ravel()
    right_grip = np.asarray([right_gripper_width], dtype=np.float32).ravel()

    if left_tcp.shape[0] != LEFT_TCP_POSE_DIM:
        raise ValueError(
            f"left_tcp_pose must have {LEFT_TCP_POSE_DIM} elements, "
            f"got {left_tcp.shape[0]}"
        )
    if right_tcp.shape[0] != RIGHT_TCP_POSE_DIM:
        raise ValueError(
            f"right_tcp_pose must have {RIGHT_TCP_POSE_DIM} elements, "
            f"got {right_tcp.shape[0]}"
        )

    encoded = np.concatenate([left_tcp, right_tcp, left_grip, right_grip])
    return ensure_state_vector(encoded)
