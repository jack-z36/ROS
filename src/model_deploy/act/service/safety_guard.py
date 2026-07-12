"""L2-04 safety-check pure computation primitives (C4, C6-C15).

RAM-only geometric projection and input validation for single-step ACT actions.
Does **not** implement A1 ``SafetyGuard`` or B1-B5 orchestration (deploy_034).

Internal quaternion order is fixed ``xyzw``. No ROS / runtime / hardware imports.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Optional, Tuple

import numpy as np

from model_deploy.act.types.action_spec import ACTION_DIM, ActionSpec
from model_deploy.act.types.observation import ObservationSnapshot
from model_deploy.act.types.safety_result import SafetyCode, SafetyFinding

# ---------------------------------------------------------------------------
# Exceptions (contract failures → B1 maps to REJECTED)
# ---------------------------------------------------------------------------


class SafetyContractError(ValueError):
    """Raised when a C-layer contract check fails.

    Attributes:
        code: Stable ``SafetyCode`` for the failure.
    """

    def __init__(self, code: SafetyCode, message: str) -> None:
        super().__init__(message)
        self.code = code


# ---------------------------------------------------------------------------
# C4 _ComparisonReference — internal frozen baseline (not a public API)
# ---------------------------------------------------------------------------

_ReferenceSource = Literal["previous", "observation"]


@dataclass(frozen=True)
class _ComparisonReference:
    """Internal comparison baseline with provenance (C4).

    Holds left/right TCP pose (7D xyz+xyzw) and gripper scalars in the
    deployment ActionDomain. Not exported as a cross-L2 public type.
    """

    source: _ReferenceSource
    left_tcp_action: np.ndarray  # (7,) float
    right_tcp_action: np.ndarray  # (7,) float
    left_gripper: float
    right_gripper: float


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _as_float_vector(value: Any, expected_len: int, name: str) -> np.ndarray:
    arr = np.asarray(value, dtype=np.float64)
    if arr.shape != (expected_len,):
        raise SafetyContractError(
            SafetyCode.INVALID_SHAPE,
            f"{name} must have shape ({expected_len},), got {arr.shape}",
        )
    return arr


def _to_serializable_vec(vec: np.ndarray) -> tuple[float, ...]:
    return tuple(float(x) for x in np.asarray(vec, dtype=np.float64).ravel())


def _quat_dot(q0: np.ndarray, q1: np.ndarray) -> float:
    return float(np.dot(q0, q1))


def _rotation_angle_rad(q_ref: np.ndarray, q_tgt: np.ndarray) -> float:
    """Shortest-path SO(3) angle between two unit quaternions (xyzw)."""
    d = abs(_quat_dot(q_ref, q_tgt))
    d = min(1.0, d)
    return float(2.0 * np.arccos(d))


def _slerp_xyzw(q0: np.ndarray, q1: np.ndarray, t: float) -> np.ndarray:
    """Spherical linear interpolation on unit quaternions (xyzw), shortest arc.

    Parameters
    ----------
    q0, q1:
        Unit quaternions in ``xyzw``.
    t:
        Interpolation factor in ``[0, 1]`` from *q0* toward *q1*.
    """
    q0 = np.asarray(q0, dtype=np.float64).copy()
    q1 = np.asarray(q1, dtype=np.float64).copy()
    dot = _quat_dot(q0, q1)
    # Shortest arc: flip q1 if in opposite hemisphere (q and -q are same pose).
    if dot < 0.0:
        q1 = -q1
        dot = -dot
    # Near-parallel: fall back to normalized linear interpolation.
    if dot > 0.9995:
        result = q0 + t * (q1 - q0)
        n = float(np.linalg.norm(result))
        if n <= 0.0:
            return q0.copy()
        return (result / n).astype(np.float64, copy=False)
    omega = float(np.arccos(np.clip(dot, -1.0, 1.0)))
    sin_omega = float(np.sin(omega))
    s0 = float(np.sin((1.0 - t) * omega) / sin_omega)
    s1 = float(np.sin(t * omega) / sin_omega)
    return (s0 * q0 + s1 * q1).astype(np.float64, copy=False)


# ---------------------------------------------------------------------------
# C6 require_action_vector_16
# ---------------------------------------------------------------------------


def require_action_vector_16(obj: Any) -> np.ndarray:
    """Strict shape check: exact 1-D length-16 action vector (C6).

    Does **not** ravel multi-dimensional inputs — shape must be ``(16,)``.

    Returns
    -------
    np.ndarray
        ``float64`` vector of shape ``(16,)``.

    Raises
    ------
    SafetyContractError
        With ``SafetyCode.INVALID_SHAPE`` when the shape is not exactly ``(16,)``.
    """
    arr = np.asarray(obj, dtype=np.float64)
    if arr.shape != (ACTION_DIM,):
        raise SafetyContractError(
            SafetyCode.INVALID_SHAPE,
            f"action vector must have exact shape ({ACTION_DIM},), got {arr.shape}",
        )
    return arr


# ---------------------------------------------------------------------------
# C7 require_finite_action
# ---------------------------------------------------------------------------


def require_finite_action(vector: Any) -> np.ndarray:
    """Reject NaN / Inf entries (C7).

    Returns
    -------
    np.ndarray
        The same values as a ``float64`` 1-D array (shape preserved).

    Raises
    ------
    SafetyContractError
        With ``SafetyCode.NON_FINITE`` if any element is non-finite.
    """
    arr = np.asarray(vector, dtype=np.float64)
    if not np.all(np.isfinite(arr)):
        raise SafetyContractError(
            SafetyCode.NON_FINITE,
            "action vector contains NaN or Inf",
        )
    return arr


# ---------------------------------------------------------------------------
# C8 canonicalize_quaternion
# ---------------------------------------------------------------------------


def canonicalize_quaternion(
    quat_xyzw: Any,
    tol: float = 1e-3,
) -> np.ndarray:
    """Validate and unit-normalize an internal ``xyzw`` quaternion (C8).

    Near-unit quaternions (``|‖q‖ - 1| <= tol``) are renormalized.
    Zero-norm or far-from-unit quaternions are rejected.

    Parameters
    ----------
    quat_xyzw:
        Length-4 quaternion in ``xyzw`` order (never reordered to ``wxyz``).
    tol:
        Allowed absolute deviation of the Euclidean norm from 1.0.

    Returns
    -------
    np.ndarray
        Unit quaternion ``(4,)`` float64 in ``xyzw``.

    Raises
    ------
    SafetyContractError
        ``INVALID_SHAPE`` or ``INVALID_QUATERNION``.
    """
    if tol <= 0.0:
        raise ValueError(f"tol must be positive, got {tol}")
    q = _as_float_vector(quat_xyzw, 4, "quaternion")
    if not np.all(np.isfinite(q)):
        raise SafetyContractError(
            SafetyCode.INVALID_QUATERNION,
            "quaternion contains NaN or Inf",
        )
    norm = float(np.linalg.norm(q))
    if norm <= 0.0 or not np.isfinite(norm):
        raise SafetyContractError(
            SafetyCode.INVALID_QUATERNION,
            f"quaternion has non-positive norm ({norm})",
        )
    if abs(norm - 1.0) > tol:
        raise SafetyContractError(
            SafetyCode.INVALID_QUATERNION,
            f"quaternion norm {norm} is outside tolerance {tol} of unit length",
        )
    return (q / norm).astype(np.float64, copy=False)


# ---------------------------------------------------------------------------
# C9 select_comparison_reference
# ---------------------------------------------------------------------------


def select_comparison_reference(
    previous: Optional[ActionSpec],
    snapshot: Optional[ObservationSnapshot],
    *,
    quaternion_norm_tolerance: float = 1e-3,
) -> _ComparisonReference:
    """Choose comparison baseline: previous → observation → missing (C9).

    Priority:
    1. ``previous`` safe action (command continuity)
    2. fresh ``ObservationSnapshot`` measured state (bootstrap)
    3. neither → ``NO_REFERENCE`` contract failure

    Raises
    ------
    SafetyContractError
        With ``SafetyCode.NO_REFERENCE`` when both inputs are absent.
        Quaternion validation failures propagate as ``INVALID_QUATERNION``.
    """
    if previous is not None:
        left_tcp = np.asarray(previous.left_tcp_action, dtype=np.float64).copy()
        right_tcp = np.asarray(previous.right_tcp_action, dtype=np.float64).copy()
        if left_tcp.shape != (7,) or right_tcp.shape != (7,):
            raise SafetyContractError(
                SafetyCode.INVALID_SHAPE,
                "previous ActionSpec TCP segments must be shape (7,)",
            )
        left_tcp[3:7] = canonicalize_quaternion(
            left_tcp[3:7], tol=quaternion_norm_tolerance
        )
        right_tcp[3:7] = canonicalize_quaternion(
            right_tcp[3:7], tol=quaternion_norm_tolerance
        )
        return _ComparisonReference(
            source="previous",
            left_tcp_action=left_tcp,
            right_tcp_action=right_tcp,
            left_gripper=float(previous.left_gripper),
            right_gripper=float(previous.right_gripper),
        )

    if snapshot is not None:
        state = snapshot.state
        left_pos = np.asarray(state.left_tcp_position, dtype=np.float64).ravel()
        right_pos = np.asarray(state.right_tcp_position, dtype=np.float64).ravel()
        left_ori = canonicalize_quaternion(
            state.left_tcp_orientation, tol=quaternion_norm_tolerance
        )
        right_ori = canonicalize_quaternion(
            state.right_tcp_orientation, tol=quaternion_norm_tolerance
        )
        if left_pos.shape != (3,) or right_pos.shape != (3,):
            raise SafetyContractError(
                SafetyCode.INVALID_SHAPE,
                "observation TCP positions must be shape (3,)",
            )
        left_tcp = np.concatenate([left_pos, left_ori]).astype(np.float64, copy=False)
        right_tcp = np.concatenate([right_pos, right_ori]).astype(
            np.float64, copy=False
        )
        return _ComparisonReference(
            source="observation",
            left_tcp_action=left_tcp,
            right_tcp_action=right_tcp,
            left_gripper=float(state.left_gripper_width),
            right_gripper=float(state.right_gripper_width),
        )

    raise SafetyContractError(
        SafetyCode.NO_REFERENCE,
        "no comparison reference: previous_safe_action and observation are both missing",
    )


# ---------------------------------------------------------------------------
# C10 limit_translation_step
# ---------------------------------------------------------------------------


def limit_translation_step(
    target_xyz: Any,
    ref_xyz: Any,
    max_step_m: float,
    *,
    side: Optional[Literal["left", "right"]] = None,
) -> Tuple[np.ndarray, Optional[SafetyFinding]]:
    """Project translation by 3-D Euclidean direction scaling (C10).

    When ``‖target - ref‖ > max_step_m``, scales the *entire* displacement
    vector to length ``max_step_m`` (never per-axis clip).
    """
    if max_step_m <= 0.0:
        raise ValueError(f"max_step_m must be positive, got {max_step_m}")
    target = _as_float_vector(target_xyz, 3, "target_xyz")
    ref = _as_float_vector(ref_xyz, 3, "ref_xyz")
    if not (np.all(np.isfinite(target)) and np.all(np.isfinite(ref))):
        raise SafetyContractError(
            SafetyCode.NON_FINITE,
            "translation target/ref contains NaN or Inf",
        )
    delta = target - ref
    dist = float(np.linalg.norm(delta))
    if dist <= max_step_m or dist == 0.0:
        return target.copy(), None
    projected = ref + delta * (max_step_m / dist)
    finding = SafetyFinding(
        code=SafetyCode.TRANSLATION_LIMITED,
        side=side,
        before=_to_serializable_vec(target),
        after=_to_serializable_vec(projected),
        detail=(
            f"translation step {dist:.6f} m limited to {max_step_m:.6f} m "
            f"(euclidean direction scale)"
        ),
    )
    return projected.astype(np.float64, copy=False), finding


# ---------------------------------------------------------------------------
# C11 limit_rotation_step
# ---------------------------------------------------------------------------


def limit_rotation_step(
    target_quat_xyzw: Any,
    ref_quat_xyzw: Any,
    max_step_rad: float,
    *,
    side: Optional[Literal["left", "right"]] = None,
    quaternion_norm_tolerance: float = 1e-3,
) -> Tuple[np.ndarray, Optional[SafetyFinding]]:
    """Project rotation via shortest-arc / Slerp to angular limit (C11).

    ``q`` and ``-q`` are treated as the same orientation (hemisphere flip).
    """
    if max_step_rad <= 0.0:
        raise ValueError(f"max_step_rad must be positive, got {max_step_rad}")
    q_tgt = canonicalize_quaternion(
        target_quat_xyzw, tol=quaternion_norm_tolerance
    )
    q_ref = canonicalize_quaternion(ref_quat_xyzw, tol=quaternion_norm_tolerance)
    angle = _rotation_angle_rad(q_ref, q_tgt)
    if angle <= max_step_rad:
        # Canonicalize sign relative to reference for stable continuity.
        if _quat_dot(q_ref, q_tgt) < 0.0:
            q_tgt = -q_tgt
        return q_tgt.astype(np.float64, copy=False), None
    # t such that SO(3) angle = max_step_rad: omega_quat = angle/2, t = max/angle
    t = max_step_rad / angle
    projected = _slerp_xyzw(q_ref, q_tgt, t)
    # Re-normalize for numerical safety.
    n = float(np.linalg.norm(projected))
    if n > 0.0:
        projected = projected / n
    finding = SafetyFinding(
        code=SafetyCode.ROTATION_LIMITED,
        side=side,
        before=_to_serializable_vec(q_tgt if _quat_dot(q_ref, q_tgt) >= 0 else -q_tgt),
        after=_to_serializable_vec(projected),
        detail=(
            f"rotation step {angle:.6f} rad limited to {max_step_rad:.6f} rad "
            f"(shortest-arc slerp)"
        ),
    )
    return projected.astype(np.float64, copy=False), finding


# ---------------------------------------------------------------------------
# C12 clamp_gripper_range
# ---------------------------------------------------------------------------


def clamp_gripper_range(
    value: float,
    min_v: float,
    max_v: float,
    *,
    side: Optional[Literal["left", "right"]] = None,
) -> Tuple[float, Optional[SafetyFinding]]:
    """Clamp gripper scalar to same-domain absolute min/max (C12)."""
    if min_v > max_v:
        raise ValueError(f"min_v ({min_v}) must be <= max_v ({max_v})")
    v = float(value)
    if not np.isfinite(v):
        raise SafetyContractError(
            SafetyCode.NON_FINITE,
            "gripper value is non-finite",
        )
    if min_v <= v <= max_v:
        return v, None
    projected = min(max(v, min_v), max_v)
    finding = SafetyFinding(
        code=SafetyCode.GRIPPER_RANGE_LIMITED,
        side=side,
        before=v,
        after=float(projected),
        detail=f"gripper {v} clamped to [{min_v}, {max_v}]",
    )
    return float(projected), finding


# ---------------------------------------------------------------------------
# C13 limit_gripper_step
# ---------------------------------------------------------------------------


def limit_gripper_step(
    value: float,
    ref: float,
    max_step: float,
    *,
    side: Optional[Literal["left", "right"]] = None,
) -> Tuple[float, Optional[SafetyFinding]]:
    """Limit same-domain single-step gripper change (C13)."""
    if max_step < 0.0:
        raise ValueError(f"max_step must be >= 0, got {max_step}")
    v = float(value)
    r = float(ref)
    if not (np.isfinite(v) and np.isfinite(r)):
        raise SafetyContractError(
            SafetyCode.NON_FINITE,
            "gripper value/ref is non-finite",
        )
    delta = v - r
    if abs(delta) <= max_step:
        return v, None
    projected = r + float(np.sign(delta)) * max_step
    finding = SafetyFinding(
        code=SafetyCode.GRIPPER_STEP_LIMITED,
        side=side,
        before=v,
        after=float(projected),
        detail=(
            f"gripper step {delta} limited to ±{max_step} around ref {r}"
        ),
    )
    return float(projected), finding


# ---------------------------------------------------------------------------
# C14 build_safe_action
# ---------------------------------------------------------------------------


def build_safe_action(
    left_tcp_action: Any,
    right_tcp_action: Any,
    left_gripper: float,
    right_gripper: float,
) -> ActionSpec:
    """Reassemble left/right fields into fixed 16D ``ActionSpec`` (C14).

    Segment order is invariant:
    ``[left_tcp(7) | right_tcp(7) | left_grip(1) | right_grip(1)]``.
    """
    left = np.asarray(left_tcp_action, dtype=np.float32).ravel()
    right = np.asarray(right_tcp_action, dtype=np.float32).ravel()
    if left.shape != (7,) or right.shape != (7,):
        raise SafetyContractError(
            SafetyCode.INVALID_SHAPE,
            f"TCP actions must be (7,), got left={left.shape} right={right.shape}",
        )
    return ActionSpec(
        left_tcp_action=left.copy(),
        right_tcp_action=right.copy(),
        left_gripper=float(left_gripper),
        right_gripper=float(right_gripper),
    )


# ---------------------------------------------------------------------------
# C15 validate_safe_action_invariants
# ---------------------------------------------------------------------------


def validate_safe_action_invariants(
    action: ActionSpec,
    *,
    quaternion_norm_tolerance: float = 1e-3,
    gripper_min: Optional[float] = None,
    gripper_max: Optional[float] = None,
) -> ActionSpec:
    """Final shape / finite / quaternion / optional domain gate (C15).

    Returns a validated copy with unit quaternions. Does not reorder
    quaternion components (internal ``xyzw`` only).
    """
    if not isinstance(action, ActionSpec):
        raise SafetyContractError(
            SafetyCode.INVARIANT_VIOLATION,
            f"action must be ActionSpec, got {type(action)!r}",
        )
    try:
        vector = require_action_vector_16(action.as_vector())
        vector = require_finite_action(vector)
    except SafetyContractError as exc:
        raise SafetyContractError(
            SafetyCode.INVARIANT_VIOLATION,
            f"safe action invariant failed: {exc}",
        ) from exc

    # Canonicalize both TCP quaternions in-place on a fresh ActionSpec.
    left = np.asarray(action.left_tcp_action, dtype=np.float64).copy()
    right = np.asarray(action.right_tcp_action, dtype=np.float64).copy()
    if left.shape != (7,) or right.shape != (7,):
        raise SafetyContractError(
            SafetyCode.INVARIANT_VIOLATION,
            "TCP segments must remain shape (7,)",
        )
    try:
        left[3:7] = canonicalize_quaternion(
            left[3:7], tol=quaternion_norm_tolerance
        )
        right[3:7] = canonicalize_quaternion(
            right[3:7], tol=quaternion_norm_tolerance
        )
    except SafetyContractError as exc:
        raise SafetyContractError(
            SafetyCode.INVARIANT_VIOLATION,
            f"safe action quaternion invariant failed: {exc}",
        ) from exc

    lg = float(action.left_gripper)
    rg = float(action.right_gripper)
    if gripper_min is not None and gripper_max is not None:
        if not (gripper_min <= lg <= gripper_max and gripper_min <= rg <= gripper_max):
            raise SafetyContractError(
                SafetyCode.INVARIANT_VIOLATION,
                f"gripper values outside domain [{gripper_min}, {gripper_max}]: "
                f"left={lg}, right={rg}",
            )

    validated = ActionSpec(
        left_tcp_action=left.astype(np.float32, copy=False),
        right_tcp_action=right.astype(np.float32, copy=False),
        left_gripper=lg,
        right_gripper=rg,
    )
    # Round-trip vector length must remain 16.
    out_vec = validated.as_vector()
    if out_vec.shape != (ACTION_DIM,):
        raise SafetyContractError(
            SafetyCode.INVARIANT_VIOLATION,
            f"validated action vector shape {out_vec.shape} != ({ACTION_DIM},)",
        )
    return validated


# Public primitive surface (no A1/B orchestration).
__all__ = [
    "SafetyContractError",
    "_ComparisonReference",
    "require_action_vector_16",
    "require_finite_action",
    "canonicalize_quaternion",
    "select_comparison_reference",
    "limit_translation_step",
    "limit_rotation_step",
    "clamp_gripper_range",
    "limit_gripper_step",
    "build_safe_action",
    "validate_safe_action_invariants",
]
