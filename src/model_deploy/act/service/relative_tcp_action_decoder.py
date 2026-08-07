"""Decode ACT relative TCP actions into the existing absolute action contract."""

from __future__ import annotations

import numpy as np

from model_deploy.act.types.action_chunk import ActionChunk
from model_deploy.act.types.action_representation import ActionRepresentationSpec
from model_deploy.act.types.observation import ObservationState
from model_deploy.act.types.relative_action_chunk import RelativeActionChunk


def _unit_quaternion(value: object, name: str) -> np.ndarray:
    quat = np.asarray(value, dtype=np.float64).ravel()
    if quat.shape != (4,):
        raise ValueError(f"{name} must have shape (4,), got {quat.shape}")
    if not np.isfinite(quat).all():
        raise ValueError(f"{name} contains NaN or Inf")
    norm = float(np.linalg.norm(quat))
    if norm <= 1e-8 or not np.isfinite(norm):
        raise ValueError(f"{name} has invalid norm {norm}")
    return quat / norm


def _quaternion_multiply_xyzw(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    lx, ly, lz, lw = left
    rx, ry, rz, rw = right
    return np.asarray(
        [
            lw * rx + lx * rw + ly * rz - lz * ry,
            lw * ry - lx * rz + ly * rw + lz * rx,
            lw * rz + lx * ry - ly * rx + lz * rw,
            lw * rw - lx * rx - ly * ry - lz * rz,
        ],
        dtype=np.float64,
    )


def _rotate_vector_xyzw(quat: np.ndarray, vector: np.ndarray) -> np.ndarray:
    pure = np.asarray([vector[0], vector[1], vector[2], 0.0], dtype=np.float64)
    conjugate = np.asarray([-quat[0], -quat[1], -quat[2], quat[3]])
    return _quaternion_multiply_xyzw(
        _quaternion_multiply_xyzw(quat, pure), conjugate
    )[:3]


class RelativeTcpActionDecoder:
    """Convert one inference-reference relative chunk to absolute actions."""

    def __init__(
        self,
        representation_spec: ActionRepresentationSpec | None = None,
    ) -> None:
        self._representation_spec = (
            representation_spec or ActionRepresentationSpec.relative_tcp_v1()
        )

    @property
    def representation_spec(self) -> ActionRepresentationSpec:
        return self._representation_spec

    def decode(
        self,
        relative_chunk: RelativeActionChunk,
        reference_state: ObservationState,
    ) -> ActionChunk:
        """Decode every row against the same reference observation state."""
        left_ref_position = np.asarray(
            reference_state.left_tcp_position, dtype=np.float64
        ).ravel()
        right_ref_position = np.asarray(
            reference_state.right_tcp_position, dtype=np.float64
        ).ravel()
        if left_ref_position.shape != (3,) or right_ref_position.shape != (3,):
            raise ValueError("reference TCP positions must have shape (3,)")
        if not np.isfinite(left_ref_position).all() or not np.isfinite(
            right_ref_position
        ).all():
            raise ValueError("reference TCP positions contain NaN or Inf")

        left_ref_quat = _unit_quaternion(
            reference_state.left_tcp_orientation, "left reference quaternion"
        )
        right_ref_quat = _unit_quaternion(
            reference_state.right_tcp_orientation, "right reference quaternion"
        )

        decoded = np.empty(relative_chunk.actions.shape, dtype=np.float32)
        for row_index, row in enumerate(relative_chunk.actions):
            decoded[row_index, 0:7] = self._decode_tcp(
                row[0:7], left_ref_position, left_ref_quat
            )
            decoded[row_index, 7:14] = self._decode_tcp(
                row[7:14], right_ref_position, right_ref_quat
            )
            decoded[row_index, 14:16] = row[14:16]

        return ActionChunk(actions=decoded)

    @staticmethod
    def _decode_tcp(
        relative_tcp: np.ndarray,
        reference_position: np.ndarray,
        reference_quaternion: np.ndarray,
    ) -> np.ndarray:
        relative_position = np.asarray(relative_tcp[0:3], dtype=np.float64)
        relative_quaternion = _unit_quaternion(
            relative_tcp[3:7], "relative quaternion"
        )
        absolute_position = reference_position + _rotate_vector_xyzw(
            reference_quaternion, relative_position
        )
        absolute_quaternion = _unit_quaternion(
            _quaternion_multiply_xyzw(reference_quaternion, relative_quaternion),
            "absolute quaternion",
        )
        return np.concatenate([absolute_position, absolute_quaternion]).astype(
            np.float32
        )
