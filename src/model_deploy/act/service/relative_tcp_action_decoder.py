"""RelativeTcpActionDecoder: relative action chunk → absolute action chunk.

L2-03-internal service that decodes the ACT model output (relative TCP arm
action + absolute gripper targets) into an absolute base-frame ``ActionChunk``
using the inference-moment ``ObservationState`` as the fixed reference.

Fixed math contract (per row, per arm):

    T_absolute[k] = T_reference @ T_relative[k]

expressed as:

    p_abs = p_ref + R(q_ref) @ p_rel        # translation
    q_abs = q_ref ⊗ q_rel                    # rotation (quaternion product)

The *entire* chunk shares the single inference-moment reference — no step-wise
accumulation, no use of the latest TCP.  The two gripper fields are absolute
targets and pass through unchanged.

Pure computation function — does not call the model, does not normalize, does
not read ROS topics or the latest observation, and manages no chunk state.
"""

from __future__ import annotations

import numpy as np

from model_deploy.act.types.action_chunk import ActionChunk
from model_deploy.act.types.action_representation import (
    ActionRepresentationSpec,
    EXPECTED_ARM_ACTION_TYPE,
    EXPECTED_CHUNK_REFERENCE,
    EXPECTED_TRANSLATION_FRAME,
    EXPECTED_ROTATION_REPRESENTATION,
    EXPECTED_GRIPPER_ACTION_TYPE,
    is_expected_relative_spec,
)
from model_deploy.act.types.observation import ObservationState
from model_deploy.act.types.relative_action_chunk import RelativeActionChunk

_QUAT_NORM_EPS: float = 1e-8


# ---------------------------------------------------------------------------
# Quaternion helpers (xyzw, pure numpy)
# ---------------------------------------------------------------------------


def _normalize_quaternion(q: np.ndarray) -> np.ndarray:
    """Return a unit-length copy of an ``xyzw`` quaternion.

    Raises:
        ValueError: norm is NaN/Inf or below ``_QUAT_NORM_EPS``.
    """
    norm = float(np.linalg.norm(q))
    if not np.isfinite(norm):
        raise ValueError("quaternion norm is NaN or Inf")
    if norm <= _QUAT_NORM_EPS:
        raise ValueError(
            f"quaternion norm must be greater than {_QUAT_NORM_EPS}, got {norm}"
        )
    return (q / norm).astype(np.float32, copy=False)


def _quaternion_to_rotation_matrix(q_xyzw: np.ndarray) -> np.ndarray:
    """Return the (3, 3) rotation matrix for a unit ``xyzw`` quaternion."""
    x, y, z, w = (float(v) for v in q_xyzw)
    # Standard xyzw -> rotation matrix.
    return np.array(
        [
            [1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y)],
            [2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x)],
            [2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)],
        ],
        dtype=np.float64,
    )


def _quaternion_multiply(q1_xyzw: np.ndarray, q2_xyzw: np.ndarray) -> np.ndarray:
    """Hamilton product of two ``xyzw`` quaternions (``q1 ⊗ q2``)."""
    x1, y1, z1, w1 = (float(v) for v in q1_xyzw)
    x2, y2, z2, w2 = (float(v) for v in q2_xyzw)
    return np.array(
        [
            w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2,
            w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
            w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2,
            w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2,
        ],
        dtype=np.float64,
    )


# ---------------------------------------------------------------------------
# RelativeTcpActionDecoder
# ---------------------------------------------------------------------------


class RelativeTcpActionDecoder:
    """Decode a ``RelativeActionChunk`` into an absolute ``ActionChunk``.

    Constructed once at startup with the frozen ``ActionRepresentationSpec``
    read from the bundle manifest.  The constructor rejects any spec that does
    not match the first-version relative-action contract.

    The single public method ``decode`` converts one chunk against the
    inference-moment reference state; it is pure and stateless across calls.
    """

    def __init__(self, action_representation_spec: ActionRepresentationSpec) -> None:
        if not isinstance(action_representation_spec, ActionRepresentationSpec):
            raise TypeError(
                "action_representation_spec must be an ActionRepresentationSpec"
            )
        if not is_expected_relative_spec(action_representation_spec):
            raise ValueError(
                "RelativeTcpActionDecoder requires the relative-action "
                "representation contract; got "
                f"{action_representation_spec.as_mapping()}. "
                "The first-version deployment only supports "
                f"arm_action_type={EXPECTED_ARM_ACTION_TYPE!r}, "
                f"chunk_reference={EXPECTED_CHUNK_REFERENCE!r}, "
                f"translation_frame={EXPECTED_TRANSLATION_FRAME!r}, "
                f"rotation_representation={EXPECTED_ROTATION_REPRESENTATION!r}, "
                f"gripper_action_type={EXPECTED_GRIPPER_ACTION_TYPE!r}."
            )
        self._spec = action_representation_spec

    @property
    def action_representation_spec(self) -> ActionRepresentationSpec:
        """The frozen representation contract this decoder was built with."""
        return self._spec

    def decode(
        self,
        relative_chunk: RelativeActionChunk,
        reference_state: ObservationState,
    ) -> ActionChunk:
        """Decode one relative chunk into an absolute chunk.

        Args:
            relative_chunk:   Relative action chunk from the postprocess stage.
            reference_state:  The inference-moment observation state used as the
                              fixed reference for *every* row in the chunk.

        Returns:
            Absolute ``ActionChunk`` with the same shape ``(chunk_size, 16)``.

        Raises:
            TypeError:  Wrong input types.
            ValueError: Reference TCP orientation is degenerate, or the decoded
                        result is non-finite.
        """
        if not isinstance(relative_chunk, RelativeActionChunk):
            raise TypeError(
                "relative_chunk must be a RelativeActionChunk"
            )
        if not isinstance(reference_state, ObservationState):
            raise TypeError(
                "reference_state must be an ObservationState"
            )

        rel = relative_chunk.actions  # (N, 16) float32
        n = rel.shape[0]

        # --- reference TCP poses (unit-normalized orientation) ---
        left_ref_pos = np.asarray(reference_state.left_tcp_position, dtype=np.float64)
        left_ref_quat = _normalize_quaternion(
            np.asarray(reference_state.left_tcp_orientation, dtype=np.float64)
        )
        right_ref_pos = np.asarray(reference_state.right_tcp_position, dtype=np.float64)
        right_ref_quat = _normalize_quaternion(
            np.asarray(reference_state.right_tcp_orientation, dtype=np.float64)
        )
        left_ref_rot = _quaternion_to_rotation_matrix(left_ref_quat)
        right_ref_rot = _quaternion_to_rotation_matrix(right_ref_quat)

        out = np.empty((n, 16), dtype=np.float32)
        for k in range(n):
            row = rel[k]

            # --- left arm [0:7]: relative pose -> absolute pose ---
            out[k, 0:7] = self._decode_arm(
                row[0:3],
                row[3:7],
                left_ref_pos,
                left_ref_quat,
                left_ref_rot,
            )

            # --- right arm [7:14]: relative pose -> absolute pose ---
            out[k, 7:14] = self._decode_arm(
                row[7:10],
                row[10:14],
                right_ref_pos,
                right_ref_quat,
                right_ref_rot,
            )

            # --- grippers [14:16]: absolute targets pass through ---
            out[k, 14] = row[14]
            out[k, 15] = row[15]

        if not np.isfinite(out).all():
            raise ValueError("decoded absolute action contains NaN or Inf values")

        return ActionChunk(actions=out)

    @staticmethod
    def _decode_arm(
        rel_pos: np.ndarray,
        rel_quat: np.ndarray,
        ref_pos: np.ndarray,
        ref_quat: np.ndarray,
        ref_rot: np.ndarray,
    ) -> np.ndarray:
        """Decode one arm's 7D relative TCP into 7D absolute TCP.

        ``p_abs = p_ref + R(q_ref) @ p_rel`` and ``q_abs = q_ref ⊗ q_rel``,
        with the absolute quaternion renormalized to unit length.
        """
        rel_pos = np.asarray(rel_pos, dtype=np.float64)
        rel_quat = np.asarray(rel_quat, dtype=np.float64)

        p_abs = ref_pos + ref_rot @ rel_pos
        q_abs = _quaternion_multiply(ref_quat, rel_quat)
        q_abs = _normalize_quaternion(q_abs)

        arm = np.empty(7, dtype=np.float32)
        arm[0:3] = p_abs.astype(np.float32, copy=False)
        arm[3:7] = q_abs.astype(np.float32, copy=False)
        return arm
