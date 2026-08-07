"""16D single-action specification for ACT model deployment.

Defines the dimension, segment layout, field semantics of the 16-dimensional
action vector consumed by the ACT deployment chain.

Segment layout:
    left_tcp_action       : [0:7)   xyz(3) + quaternion(4)
    right_tcp_action      : [7:14)  xyz(3) + quaternion(4)
    left_gripper          : [14:15) float
    right_gripper         : [15:16) float
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

# ---------------------------------------------------------------------------
# Dimension constants
# ---------------------------------------------------------------------------

ACTION_DIM: int = 16

LEFT_TCP_ACTION_DIM: int = 7
RIGHT_TCP_ACTION_DIM: int = 7
LEFT_GRIPPER_DIM: int = 1
RIGHT_GRIPPER_DIM: int = 1


# ---------------------------------------------------------------------------
# ActionSpec
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ActionSpec:
    """Immutable structured representation of a single 16D absolute action.

    The two ``tcp_action`` segments are **absolute base-frame** TCP target
    poses (``xyz`` position + ``xyzw`` quaternion), consumed as-is by the
    control loop, the safety guard and the output adapter.

    Attributes:
        left_tcp_action:  7D absolute TCP target for the left arm
                          (xyz + quaternion) in the base frame.
        right_tcp_action: 7D absolute TCP target for the right arm
                          (xyz + quaternion) in the base frame.
        left_gripper:     Scalar absolute gripper target for the left hand [0, 1].
        right_gripper:    Scalar absolute gripper target for the right hand [0, 1].
    """

    left_tcp_action: np.ndarray  # shape (7,)
    right_tcp_action: np.ndarray  # shape (7,)
    left_gripper: float
    right_gripper: float

    def as_vector(self) -> np.ndarray:
        """Return the action as a flat 16D float32 vector."""
        return np.concatenate(
            [
                np.asarray(self.left_tcp_action, dtype=np.float32).ravel(),
                np.asarray(self.right_tcp_action, dtype=np.float32).ravel(),
                np.asarray([self.left_gripper], dtype=np.float32),
                np.asarray([self.right_gripper], dtype=np.float32),
            ]
        )


# ---------------------------------------------------------------------------
# Pure functions
# ---------------------------------------------------------------------------


def ensure_action_vector(flat: np.ndarray | list | tuple) -> np.ndarray:
    """Validate and normalise a flat action vector to 16D float32.

    Args:
        flat: A list, tuple, or numpy array representing a flat action vector.

    Returns:
        A 1-D float32 ``np.ndarray`` of length ``ACTION_DIM`` (16).

    Raises:
        ValueError: If the input does not have exactly 16 elements.
    """
    arr = np.asarray(flat, dtype=np.float32).ravel()
    if arr.shape[0] != ACTION_DIM:
        raise ValueError(
            f"Expected action vector of length {ACTION_DIM}, got {arr.shape[0]}"
        )
    return arr


def split_action(flat: np.ndarray | list | tuple) -> ActionSpec:
    """Split a flat 16D action vector into structured segments.

    Args:
        flat: A list, tuple, or numpy array of length 16.

    Returns:
        An ``ActionSpec`` with the four structured segments.

    Raises:
        ValueError: If the input does not have exactly 16 elements.
    """
    arr = ensure_action_vector(flat)
    return ActionSpec(
        left_tcp_action=arr[0:7].copy(),
        right_tcp_action=arr[7:14].copy(),
        left_gripper=float(arr[14]),
        right_gripper=float(arr[15]),
    )
