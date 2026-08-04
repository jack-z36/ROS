"""Service pure-function tests for L2-04 C4 / C6-C15 (deploy_033).

Covers Gate algorithm tags except RESULT-STATUS / PURITY-IMPORT orchestration:
INPUT-SHAPE, INPUT-FINITE, QUAT-CANDIDATE, REFERENCE-*, POSE-*, GRIPPER-*,
BIMANUAL-ASSEMBLY, OUTPUT-INVARIANT.
"""

from __future__ import annotations

import ast
import math
from pathlib import Path

import numpy as np
import pytest

from model_deploy.act.service.safety_guard import (
    SafetyContractError,
    _ComparisonReference,
    build_safe_action,
    canonicalize_quaternion,
    clamp_gripper_range,
    limit_gripper_step,
    limit_rotation_step,
    limit_translation_step,
    require_action_vector_16,
    require_finite_action,
    select_comparison_reference,
    validate_safe_action_invariants,
)
from model_deploy.act.types.action_spec import ActionSpec, split_action
from model_deploy.act.types.observation import ObservationSnapshot, ObservationState
from model_deploy.act.types.safety_result import SafetyCode

# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

_IDENTITY_QUAT = np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float64)  # xyzw


def _unit_quat_about_z(angle_rad: float) -> np.ndarray:
    """xyzw quaternion for rotation about +Z by *angle_rad*."""
    half = 0.5 * angle_rad
    return np.array([0.0, 0.0, math.sin(half), math.cos(half)], dtype=np.float64)


def _tcp(xyz=(0.0, 0.0, 0.0), quat=None) -> np.ndarray:
    q = _IDENTITY_QUAT if quat is None else np.asarray(quat, dtype=np.float64)
    return np.concatenate(
        [np.asarray(xyz, dtype=np.float64), q]
    ).astype(np.float32)


def _action(
    left_xyz=(0.0, 0.0, 0.0),
    right_xyz=(0.0, 0.0, 0.0),
    left_quat=None,
    right_quat=None,
    left_g=0.5,
    right_g=0.5,
) -> ActionSpec:
    return ActionSpec(
        left_tcp_action=_tcp(left_xyz, left_quat),
        right_tcp_action=_tcp(right_xyz, right_quat),
        left_gripper=float(left_g),
        right_gripper=float(right_g),
    )


def _snapshot(
    left_xyz=(0.0, 0.0, 0.0),
    right_xyz=(0.0, 0.0, 0.0),
    left_quat=None,
    right_quat=None,
    left_g=0.5,
    right_g=0.5,
) -> ObservationSnapshot:
    lq = _IDENTITY_QUAT if left_quat is None else np.asarray(left_quat, dtype=np.float64)
    rq = (
        _IDENTITY_QUAT if right_quat is None else np.asarray(right_quat, dtype=np.float64)
    )
    state = ObservationState(
        left_tcp_position=np.asarray(left_xyz, dtype=np.float32),
        left_tcp_orientation=lq.astype(np.float32),
        left_gripper_width=float(left_g),
        right_tcp_position=np.asarray(right_xyz, dtype=np.float32),
        right_tcp_orientation=rq.astype(np.float32),
        right_gripper_width=float(right_g),
    )
    encoded = np.concatenate(
        [
            state.left_tcp_position,
            state.left_tcp_orientation,
            [state.left_gripper_width],
            state.right_tcp_position,
            state.right_tcp_orientation,
            [state.right_gripper_width],
        ]
    ).astype(np.float32)
    # encoded_state for ObservationSnapshot must be shape (16,) but ACT observation
    # layout is 3+4+1+3+4+1 = 16 — matches.
    return ObservationSnapshot(
        images={},
        state=state,
        encoded_state=encoded,
        captured_at_s=0.0,
    )


def _rotation_angle(q0: np.ndarray, q1: np.ndarray) -> float:
    d = min(1.0, abs(float(np.dot(q0, q1))))
    return 2.0 * math.acos(d)


# ---------------------------------------------------------------------------
# INPUT-SHAPE (C6)
# ---------------------------------------------------------------------------


class TestRequireActionVector16:
    def test_accepts_exact_16(self) -> None:
        v = np.arange(16, dtype=np.float32)
        out = require_action_vector_16(v)
        assert out.shape == (16,)
        np.testing.assert_allclose(out, v.astype(np.float64))

    def test_rejects_wrong_length(self) -> None:
        with pytest.raises(SafetyContractError) as ei:
            require_action_vector_16(np.zeros(15))
        assert ei.value.code is SafetyCode.INVALID_SHAPE

    def test_rejects_2d_without_ravel(self) -> None:
        with pytest.raises(SafetyContractError) as ei:
            require_action_vector_16(np.zeros((4, 4)))
        assert ei.value.code is SafetyCode.INVALID_SHAPE

    def test_rejects_column_vector(self) -> None:
        with pytest.raises(SafetyContractError) as ei:
            require_action_vector_16(np.zeros((16, 1)))
        assert ei.value.code is SafetyCode.INVALID_SHAPE


# ---------------------------------------------------------------------------
# INPUT-FINITE (C7)
# ---------------------------------------------------------------------------


class TestRequireFiniteAction:
    def test_accepts_finite(self) -> None:
        v = np.ones(16)
        np.testing.assert_array_equal(require_finite_action(v), v)

    def test_rejects_nan(self) -> None:
        v = np.ones(16)
        v[3] = np.nan
        with pytest.raises(SafetyContractError) as ei:
            require_finite_action(v)
        assert ei.value.code is SafetyCode.NON_FINITE

    def test_rejects_inf(self) -> None:
        v = np.ones(16)
        v[0] = np.inf
        with pytest.raises(SafetyContractError) as ei:
            require_finite_action(v)
        assert ei.value.code is SafetyCode.NON_FINITE


# ---------------------------------------------------------------------------
# QUAT-CANDIDATE (C8)
# ---------------------------------------------------------------------------


class TestCanonicalizeQuaternion:
    def test_unit_identity(self) -> None:
        q = canonicalize_quaternion(_IDENTITY_QUAT)
        np.testing.assert_allclose(q, _IDENTITY_QUAT, atol=1e-12)
        assert abs(np.linalg.norm(q) - 1.0) < 1e-12

    def test_near_unit_renormalized(self) -> None:
        # Slightly off unit; within default tol=1e-3
        q_in = np.array([0.0, 0.0, 0.0, 1.0005], dtype=np.float64)
        q = canonicalize_quaternion(q_in, tol=1e-3)
        assert abs(np.linalg.norm(q) - 1.0) < 1e-12
        # Still xyzw: w is largest component
        assert abs(q[3]) > abs(q[0])

    def test_zero_norm_rejected(self) -> None:
        with pytest.raises(SafetyContractError) as ei:
            canonicalize_quaternion(np.zeros(4))
        assert ei.value.code is SafetyCode.INVALID_QUATERNION

    def test_far_from_unit_rejected(self) -> None:
        with pytest.raises(SafetyContractError) as ei:
            canonicalize_quaternion(np.array([1.0, 0.0, 0.0, 0.0]) * 2.0, tol=1e-3)
        assert ei.value.code is SafetyCode.INVALID_QUATERNION

    def test_wrong_shape_rejected(self) -> None:
        with pytest.raises(SafetyContractError) as ei:
            canonicalize_quaternion(np.ones(3))
        assert ei.value.code is SafetyCode.INVALID_SHAPE

    def test_internal_order_is_xyzw_not_wxyz(self) -> None:
        # Rotation 90° about Z: xyzw = (0, 0, sin45, cos45); wxyz would swap.
        q = _unit_quat_about_z(math.pi / 2)
        out = canonicalize_quaternion(q)
        np.testing.assert_allclose(out, q, atol=1e-12)
        # w component is index 3 in xyzw
        assert abs(out[3] - math.cos(math.pi / 4)) < 1e-9
        assert abs(out[2] - math.sin(math.pi / 4)) < 1e-9


# ---------------------------------------------------------------------------
# REFERENCE-* (C4 / C9)
# ---------------------------------------------------------------------------


class TestSelectComparisonReference:
    def test_previous_preferred_over_observation(self) -> None:
        prev = _action(left_xyz=(1.0, 0.0, 0.0), left_g=0.1)
        snap = _snapshot(left_xyz=(9.0, 0.0, 0.0), left_g=0.9)
        ref = select_comparison_reference(prev, snap)
        assert isinstance(ref, _ComparisonReference)
        assert ref.source == "previous"
        np.testing.assert_allclose(ref.left_tcp_action[:3], [1.0, 0.0, 0.0])
        assert ref.left_gripper == pytest.approx(0.1)

    def test_bootstrap_uses_observation_when_no_previous(self) -> None:
        snap = _snapshot(left_xyz=(0.2, 0.3, 0.4), left_g=0.7, right_g=0.2)
        ref = select_comparison_reference(None, snap)
        assert ref.source == "observation"
        np.testing.assert_allclose(ref.left_tcp_action[:3], [0.2, 0.3, 0.4])
        assert ref.left_gripper == pytest.approx(0.7)
        assert ref.right_gripper == pytest.approx(0.2)

    def test_missing_both_raises_no_reference(self) -> None:
        with pytest.raises(SafetyContractError) as ei:
            select_comparison_reference(None, None)
        assert ei.value.code is SafetyCode.NO_REFERENCE

    def test_does_not_silently_pass_without_reference(self) -> None:
        # Explicit regression: missing baseline must not return a fake identity.
        with pytest.raises(SafetyContractError):
            select_comparison_reference(None, None)


# ---------------------------------------------------------------------------
# POSE-TRANSLATION (C10)
# ---------------------------------------------------------------------------


class TestLimitTranslationStep:
    def test_within_limit_unchanged(self) -> None:
        target = np.array([0.01, 0.0, 0.0])
        ref = np.zeros(3)
        out, finding = limit_translation_step(target, ref, max_step_m=0.03)
        np.testing.assert_allclose(out, target)
        assert finding is None

    def test_over_limit_euclidean_scale_not_axis_clip(self) -> None:
        # Displacement along equal xyz; limit 0.03 m.
        target = np.array([0.1, 0.1, 0.1])
        ref = np.zeros(3)
        max_step = 0.03
        out, finding = limit_translation_step(
            target, ref, max_step_m=max_step, side="left"
        )
        dist = float(np.linalg.norm(out - ref))
        assert dist == pytest.approx(max_step, rel=0, abs=1e-9)
        # Direction preserved (unit direction of target-ref).
        expected_dir = target / np.linalg.norm(target)
        actual_dir = (out - ref) / dist
        np.testing.assert_allclose(actual_dir, expected_dir, atol=1e-9)
        # Must NOT be per-axis clip which would yield [0.03, 0.03, 0.03].
        axis_clip = np.clip(target - ref, -max_step, max_step) + ref
        assert not np.allclose(out, axis_clip)
        assert finding is not None
        assert finding.code is SafetyCode.TRANSLATION_LIMITED
        assert finding.side == "left"
        assert isinstance(finding.before, tuple)
        assert isinstance(finding.after, tuple)

    def test_projected_distance_exactly_limit(self) -> None:
        target = np.array([0.0, 0.0, 1.0])
        ref = np.zeros(3)
        out, _ = limit_translation_step(target, ref, max_step_m=0.05)
        assert float(np.linalg.norm(out - ref)) == pytest.approx(0.05)


# ---------------------------------------------------------------------------
# POSE-ROTATION (C11)
# ---------------------------------------------------------------------------


class TestLimitRotationStep:
    def test_within_limit_unchanged(self) -> None:
        q_ref = _IDENTITY_QUAT
        q_tgt = _unit_quat_about_z(0.05)  # 0.05 rad < 0.1
        out, finding = limit_rotation_step(q_tgt, q_ref, max_step_rad=0.1)
        assert finding is None
        assert _rotation_angle(q_ref, out) == pytest.approx(0.05, abs=1e-6)

    def test_over_limit_angle_exactly_limit(self) -> None:
        q_ref = _IDENTITY_QUAT
        q_tgt = _unit_quat_about_z(0.5)  # 0.5 rad
        max_step = 0.1
        out, finding = limit_rotation_step(
            q_tgt, q_ref, max_step_rad=max_step, side="right"
        )
        angle = _rotation_angle(q_ref, out)
        assert angle == pytest.approx(max_step, abs=1e-6)
        assert finding is not None
        assert finding.code is SafetyCode.ROTATION_LIMITED
        assert finding.side == "right"
        # Unit quaternion preserved
        assert abs(np.linalg.norm(out) - 1.0) < 1e-9

    def test_q_and_neg_q_same_pose_no_long_arc(self) -> None:
        q_ref = _IDENTITY_QUAT
        # Same orientation as small rotation, represented with opposite sign.
        q_small = _unit_quat_about_z(0.05)
        q_neg = -q_small
        out_pos, f_pos = limit_rotation_step(q_small, q_ref, max_step_rad=0.1)
        out_neg, f_neg = limit_rotation_step(q_neg, q_ref, max_step_rad=0.1)
        assert f_pos is None and f_neg is None
        # Both should land near the short-arc result (same SO(3) pose as q_small).
        assert _rotation_angle(out_pos, out_neg) == pytest.approx(0.0, abs=1e-6)
        assert _rotation_angle(q_ref, out_neg) == pytest.approx(0.05, abs=1e-6)

    def test_negated_large_rotation_still_shortest_arc(self) -> None:
        q_ref = _IDENTITY_QUAT
        q_tgt = _unit_quat_about_z(0.8)
        max_step = 0.1
        out_pos, _ = limit_rotation_step(q_tgt, q_ref, max_step_rad=max_step)
        out_neg, _ = limit_rotation_step(-q_tgt, q_ref, max_step_rad=max_step)
        assert _rotation_angle(q_ref, out_pos) == pytest.approx(max_step, abs=1e-6)
        assert _rotation_angle(q_ref, out_neg) == pytest.approx(max_step, abs=1e-6)
        assert _rotation_angle(out_pos, out_neg) == pytest.approx(0.0, abs=1e-5)


# ---------------------------------------------------------------------------
# GRIPPER-RANGE (C12) / GRIPPER-STEP (C13)
# ---------------------------------------------------------------------------


class TestGripperProjection:
    def test_range_within_no_finding(self) -> None:
        v, f = clamp_gripper_range(0.5, 0.0, 1.0)
        assert v == 0.5 and f is None

    def test_range_over_max(self) -> None:
        v, f = clamp_gripper_range(1.5, 0.0, 1.0, side="left")
        assert v == 1.0
        assert f is not None
        assert f.code is SafetyCode.GRIPPER_RANGE_LIMITED
        assert f.side == "left"
        assert f.before == 1.5
        assert f.after == 1.0

    def test_range_under_min(self) -> None:
        v, f = clamp_gripper_range(-0.2, 0.0, 1.0)
        assert v == 0.0
        assert f is not None
        assert f.code is SafetyCode.GRIPPER_RANGE_LIMITED

    def test_step_within(self) -> None:
        v, f = limit_gripper_step(0.55, ref=0.5, max_step=0.2)
        assert v == 0.55 and f is None

    def test_step_over_limit(self) -> None:
        v, f = limit_gripper_step(1.0, ref=0.5, max_step=0.2, side="right")
        assert v == pytest.approx(0.7)
        assert f is not None
        assert f.code is SafetyCode.GRIPPER_STEP_LIMITED
        assert f.side == "right"

    def test_step_negative_direction(self) -> None:
        v, f = limit_gripper_step(0.0, ref=0.5, max_step=0.1)
        assert v == pytest.approx(0.4)
        assert f is not None

    def test_same_domain_not_f100(self) -> None:
        # Domain is 0~1 normalized; thresholds applied in same units.
        v, _ = clamp_gripper_range(0.95, min_v=0.0, max_v=1.0)
        assert v == 0.95
        v2, f2 = clamp_gripper_range(1.2, min_v=0.0, max_v=1.0)
        assert v2 == 1.0 and f2 is not None


# ---------------------------------------------------------------------------
# BIMANUAL-ASSEMBLY (C14)
# ---------------------------------------------------------------------------


class TestBuildSafeAction:
    def test_segment_order_invariant(self) -> None:
        left = _tcp((0.1, 0.2, 0.3))
        right = _tcp((0.4, 0.5, 0.6))
        spec = build_safe_action(left, right, 0.11, 0.22)
        vec = spec.as_vector()
        assert vec.shape == (16,)
        np.testing.assert_allclose(vec[0:7], left.astype(np.float32))
        np.testing.assert_allclose(vec[7:14], right.astype(np.float32))
        assert float(vec[14]) == pytest.approx(0.11)
        assert float(vec[15]) == pytest.approx(0.22)
        # split_action round-trip preserves layout
        again = split_action(vec)
        np.testing.assert_allclose(again.left_tcp_action, left.astype(np.float32))
        np.testing.assert_allclose(again.right_tcp_action, right.astype(np.float32))

    def test_left_right_independence(self) -> None:
        left = _tcp((1.0, 0.0, 0.0))
        right = _tcp((0.0, 1.0, 0.0))
        spec = build_safe_action(left, right, 0.0, 1.0)
        assert float(spec.left_gripper) == 0.0
        assert float(spec.right_gripper) == 1.0
        np.testing.assert_allclose(spec.left_tcp_action[:3], [1.0, 0.0, 0.0])
        np.testing.assert_allclose(spec.right_tcp_action[:3], [0.0, 1.0, 0.0])


# ---------------------------------------------------------------------------
# OUTPUT-INVARIANT (C15)
# ---------------------------------------------------------------------------


class TestValidateSafeActionInvariants:
    def test_valid_action_passes(self) -> None:
        action = _action()
        out = validate_safe_action_invariants(action)
        assert isinstance(out, ActionSpec)
        assert out.as_vector().shape == (16,)

    def test_non_finite_rejected(self) -> None:
        action = _action()
        bad_left = action.left_tcp_action.copy()
        bad_left[0] = np.nan
        bad = ActionSpec(
            left_tcp_action=bad_left,
            right_tcp_action=action.right_tcp_action,
            left_gripper=action.left_gripper,
            right_gripper=action.right_gripper,
        )
        with pytest.raises(SafetyContractError) as ei:
            validate_safe_action_invariants(bad)
        assert ei.value.code is SafetyCode.INVARIANT_VIOLATION

    def test_bad_quaternion_rejected(self) -> None:
        action = _action(left_quat=np.zeros(4))
        with pytest.raises(SafetyContractError) as ei:
            validate_safe_action_invariants(action)
        assert ei.value.code is SafetyCode.INVARIANT_VIOLATION

    def test_gripper_domain_gate(self) -> None:
        action = _action(left_g=1.5)
        with pytest.raises(SafetyContractError) as ei:
            validate_safe_action_invariants(
                action, gripper_min=0.0, gripper_max=1.0
            )
        assert ei.value.code is SafetyCode.INVARIANT_VIOLATION

    def test_near_unit_quat_accepted(self) -> None:
        almost = np.array([0.0, 0.0, 0.0, 1.0004], dtype=np.float32)
        action = _action(left_quat=almost, right_quat=almost)
        out = validate_safe_action_invariants(action, quaternion_norm_tolerance=1e-3)
        n = float(np.linalg.norm(out.left_tcp_action[3:7]))
        assert abs(n - 1.0) < 1e-6


# ---------------------------------------------------------------------------
# Integrated primitive chain (not full B1 orchestration)
# ---------------------------------------------------------------------------


class TestPrimitiveChainSmoke:
    def test_project_then_build_then_validate(self) -> None:
        prev = _action(left_xyz=(0.0, 0.0, 0.0), right_xyz=(0.0, 0.0, 0.0))
        ref = select_comparison_reference(prev, None)
        left_xyz, f_t = limit_translation_step(
            np.array([0.2, 0.0, 0.0]),
            ref.left_tcp_action[:3],
            max_step_m=0.03,
            side="left",
        )
        assert f_t is not None
        left_q, f_r = limit_rotation_step(
            _unit_quat_about_z(0.5),
            ref.left_tcp_action[3:7],
            max_step_rad=0.1,
            side="left",
        )
        assert f_r is not None
        lg, f_g = clamp_gripper_range(1.5, 0.0, 1.0, side="left")
        assert f_g is not None
        lg, f_s = limit_gripper_step(lg, ref.left_gripper, max_step=0.2, side="left")
        assert f_s is not None  # 1.0 vs 0.5 ref → step limited
        left_tcp = np.concatenate([left_xyz, left_q])
        right_tcp = ref.right_tcp_action.copy()
        spec = build_safe_action(left_tcp, right_tcp, lg, ref.right_gripper)
        validated = validate_safe_action_invariants(
            spec, gripper_min=0.0, gripper_max=1.0
        )
        assert validated.as_vector().shape == (16,)
        assert float(np.linalg.norm(left_xyz - ref.left_tcp_action[:3])) == pytest.approx(
            0.03, abs=1e-9
        )


# ---------------------------------------------------------------------------
# PURITY-IMPORT (static scan of this module's implementation file)
# ---------------------------------------------------------------------------


class TestPurityImport:
    def test_no_runtime_ui_ros_hardware_imports(self) -> None:
        path = (
            Path(__file__).resolve().parents[2]
            / "service"
            / "safety_guard.py"
        )
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        forbidden_substrings = (
            "runtime",
            "model_deploy.act.ui",
            "rospy",
            "rclpy",
            "sensor_msgs",
            "geometry_msgs",
            "hardware",
            "pi05",
        )
        imported: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                imported.append(mod)
        for name in imported:
            lowered = name.lower()
            for bad in forbidden_substrings:
                assert bad not in lowered, f"forbidden import {name!r} contains {bad!r}"
        # Positive: only types / numpy / stdlib expected
        assert any("action_spec" in n or "safety_result" in n for n in imported)
