"""L2-04 Gate integration tests — mock RAM full safety service closed loop.

Covers all verification tags from ``04_L2验收机制.md`` §3:

TYPES-RESULT, INPUT-SHAPE, INPUT-FINITE, QUAT-CANDIDATE,
REFERENCE-ORDER, REFERENCE-BOOTSTRAP, REFERENCE-MISSING,
POSE-TRANSLATION, POSE-ROTATION, GRIPPER-RANGE, GRIPPER-STEP,
BIMANUAL-ASSEMBLY, OUTPUT-INVARIANT, RESULT-STATUS, PURITY-IMPORT.

Uses ``SafetyGuard.filter_action`` (A1) as the sole public entry with mock
``ActionSpec`` / ``ObservationSnapshot`` / ``SafetyConfig``. No ROS, hardware,
repo loader, runtime, or UI.
"""

from __future__ import annotations

import ast
import math
from pathlib import Path

import numpy as np
import pytest

from model_deploy.act.config.schema import SafetyConfig
from model_deploy.act.service import SafetyGuard
from model_deploy.act.types.action_spec import ACTION_DIM, ActionSpec, split_action
from model_deploy.act.types.observation import ObservationSnapshot, ObservationState
from model_deploy.act.types.safety_result import (
    SafetyCode,
    SafetyFinding,
    SafetyResult,
    SafetyStatus,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_IDENTITY_QUAT = np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float64)  # xyzw
_ACT_SRC = Path(__file__).resolve().parents[2]  # src/model_deploy/act


def _unit_quat_about_z(angle_rad: float) -> np.ndarray:
    half = 0.5 * angle_rad
    return np.array([0.0, 0.0, math.sin(half), math.cos(half)], dtype=np.float64)


def _rotation_angle(q0: np.ndarray, q1: np.ndarray) -> float:
    d = min(1.0, abs(float(np.dot(q0, q1))))
    return 2.0 * math.acos(d)


def _tcp(xyz=(0.0, 0.0, 0.0), quat=None) -> np.ndarray:
    q = _IDENTITY_QUAT if quat is None else np.asarray(quat, dtype=np.float64)
    return np.concatenate([np.asarray(xyz, dtype=np.float64), q]).astype(np.float32)


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


def _vector(action: ActionSpec) -> np.ndarray:
    return action.as_vector()


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
    return ObservationSnapshot(
        images={},
        state=state,
        encoded_state=encoded,
        captured_at_s=0.0,
    )


def _default_config(**overrides) -> SafetyConfig:
    base = dict(
        max_translation_step_m=0.03,
        max_rotation_step_rad=0.1,
        gripper_min=0.0,
        gripper_max=1.0,
        max_gripper_step=0.2,
        quaternion_norm_tolerance=1e-3,
    )
    base.update(overrides)
    return SafetyConfig(**base)


# ===================================================================
# TYPES-RESULT (C1-C3/C5)
# ===================================================================


class TestTypesResult:
    """TYPES-RESULT: frozen SafetyResult fields for three status values."""

    def test_three_status_fields_complete(self) -> None:
        action = _action()
        pass_r = SafetyResult(
            status=SafetyStatus.PASS, action=action, findings=()
        )
        adj_r = SafetyResult(
            status=SafetyStatus.ADJUSTED,
            action=action,
            findings=(
                SafetyFinding(
                    code=SafetyCode.TRANSLATION_LIMITED,
                    side="left",
                    before=(0.1, 0.0, 0.0),
                    after=(0.03, 0.0, 0.0),
                    detail="limited",
                ),
            ),
        )
        rej_r = SafetyResult(
            status=SafetyStatus.REJECTED,
            action=None,
            findings=(
                SafetyFinding(
                    code=SafetyCode.NO_REFERENCE,
                    side=None,
                    before=None,
                    after=None,
                    detail="no ref",
                ),
            ),
        )
        for r in (pass_r, adj_r, rej_r):
            assert hasattr(r, "status")
            assert hasattr(r, "action")
            assert hasattr(r, "findings")
            assert isinstance(r.findings, tuple)

        assert pass_r.status is SafetyStatus.PASS and pass_r.action is not None
        assert adj_r.status is SafetyStatus.ADJUSTED and adj_r.action is not None
        assert rej_r.status is SafetyStatus.REJECTED and rej_r.action is None

    def test_rejected_must_not_carry_action(self) -> None:
        with pytest.raises(ValueError):
            SafetyResult(
                status=SafetyStatus.REJECTED,
                action=_action(),
                findings=(),
            )

    def test_pass_must_carry_action(self) -> None:
        with pytest.raises(ValueError):
            SafetyResult(status=SafetyStatus.PASS, action=None, findings=())


# ===================================================================
# INPUT-SHAPE (C6/B2)
# ===================================================================


class TestInputShape:
    def test_non_16_rejected(self) -> None:
        guard = SafetyGuard(_default_config())
        result = guard.filter_action(
            np.zeros(8, dtype=np.float64),
            previous_safe_action=_action(),
        )
        assert result.status is SafetyStatus.REJECTED
        assert result.action is None
        assert any(f.code is SafetyCode.INVALID_SHAPE for f in result.findings)

    def test_2d_not_raveled(self) -> None:
        guard = SafetyGuard(_default_config())
        result = guard.filter_action(
            np.zeros((4, 4), dtype=np.float64),
            previous_safe_action=_action(),
        )
        assert result.status is SafetyStatus.REJECTED
        assert any(f.code is SafetyCode.INVALID_SHAPE for f in result.findings)


# ===================================================================
# INPUT-FINITE (C7/B2)
# ===================================================================


class TestInputFinite:
    def test_nan_rejected(self) -> None:
        guard = SafetyGuard(_default_config())
        vec = _vector(_action()).astype(np.float64)
        vec[0] = np.nan
        result = guard.filter_action(vec, previous_safe_action=_action())
        assert result.status is SafetyStatus.REJECTED
        assert result.action is None
        assert any(f.code is SafetyCode.NON_FINITE for f in result.findings)

    def test_inf_rejected(self) -> None:
        guard = SafetyGuard(_default_config())
        vec = _vector(_action()).astype(np.float64)
        vec[5] = np.inf
        result = guard.filter_action(vec, previous_safe_action=_action())
        assert result.status is SafetyStatus.REJECTED
        assert any(f.code is SafetyCode.NON_FINITE for f in result.findings)


# ===================================================================
# QUAT-CANDIDATE (C8/B2)
# ===================================================================


class TestQuatCandidate:
    def test_zero_norm_rejected(self) -> None:
        guard = SafetyGuard(_default_config())
        bad = _action()
        left = np.asarray(bad.left_tcp_action, dtype=np.float64).copy()
        left[3:7] = 0.0
        bad = ActionSpec(
            left_tcp_action=left.astype(np.float32),
            right_tcp_action=bad.right_tcp_action,
            left_gripper=bad.left_gripper,
            right_gripper=bad.right_gripper,
        )
        result = guard.filter_action(
            _vector(bad), previous_safe_action=_action()
        )
        assert result.status is SafetyStatus.REJECTED
        assert any(f.code is SafetyCode.INVALID_QUATERNION for f in result.findings)

    def test_near_unit_accepted_and_renormalized(self) -> None:
        guard = SafetyGuard(_default_config(quaternion_norm_tolerance=1e-3))
        almost = np.array([0.0, 0.0, 0.0, 1.0004], dtype=np.float64)
        candidate = _action(left_quat=almost, right_quat=almost)
        result = guard.filter_action(
            _vector(candidate), previous_safe_action=_action()
        )
        assert result.status is SafetyStatus.PASS
        assert result.action is not None
        n = float(np.linalg.norm(result.action.left_tcp_action[3:7]))
        assert abs(n - 1.0) < 1e-5


# ===================================================================
# REFERENCE-ORDER / BOOTSTRAP / MISSING (C4/C9/B1)
# ===================================================================


class TestReferenceOrder:
    def test_previous_preferred_over_observation(self) -> None:
        """REFERENCE-ORDER: previous wins when both present."""
        guard = SafetyGuard(_default_config(max_translation_step_m=0.03))
        previous = _action(left_xyz=(0.0, 0.0, 0.0))
        snap = _snapshot(left_xyz=(1.0, 0.0, 0.0))
        # 0.10 m from previous origin → ADJUSTED to 0.03; if obs used, ~0.9 m step
        candidate = _action(left_xyz=(0.10, 0.0, 0.0))
        result = guard.filter_action(
            _vector(candidate),
            previous_safe_action=previous,
            latest_observation=snap,
        )
        assert result.status is SafetyStatus.ADJUSTED
        assert result.action is not None
        left_xyz = np.asarray(result.action.left_tcp_action[:3], dtype=np.float64)
        np.testing.assert_allclose(left_xyz, [0.03, 0.0, 0.0], atol=1e-5)


class TestReferenceBootstrap:
    def test_observation_used_when_no_previous(self) -> None:
        """REFERENCE-BOOTSTRAP: observation is baseline without previous."""
        guard = SafetyGuard(_default_config(max_translation_step_m=0.03))
        snap = _snapshot(left_xyz=(0.5, 0.0, 0.0))
        # 0.01 m from observation → PASS
        candidate = _action(left_xyz=(0.51, 0.0, 0.0))
        result = guard.filter_action(
            _vector(candidate), latest_observation=snap
        )
        assert result.status is SafetyStatus.PASS
        assert result.action is not None
        np.testing.assert_allclose(
            result.action.left_tcp_action[:3], [0.51, 0.0, 0.0], atol=1e-5
        )


class TestReferenceMissing:
    def test_both_missing_rejected(self) -> None:
        """REFERENCE-MISSING: no previous and no observation → NO_REFERENCE."""
        guard = SafetyGuard(_default_config())
        result = guard.filter_action(_vector(_action(left_xyz=(0.01, 0.0, 0.0))))
        assert result.status is SafetyStatus.REJECTED
        assert result.action is None
        assert any(f.code is SafetyCode.NO_REFERENCE for f in result.findings)


# ===================================================================
# POSE-TRANSLATION (C10/B3)
# ===================================================================


class TestPoseTranslation:
    def test_over_limit_euclidean_exactly_threshold(self) -> None:
        guard = SafetyGuard(_default_config(max_translation_step_m=0.03))
        previous = _action()
        candidate = _action(left_xyz=(0.10, 0.0, 0.0))
        result = guard.filter_action(
            _vector(candidate), previous_safe_action=previous
        )
        assert result.status is SafetyStatus.ADJUSTED
        assert result.action is not None
        assert any(f.code is SafetyCode.TRANSLATION_LIMITED for f in result.findings)
        left_xyz = np.asarray(result.action.left_tcp_action[:3], dtype=np.float64)
        dist = float(np.linalg.norm(left_xyz))
        assert dist == pytest.approx(0.03, abs=1e-5)


# ===================================================================
# POSE-ROTATION (C11/B3)
# ===================================================================


class TestPoseRotation:
    def test_over_limit_angle_exactly_threshold(self) -> None:
        guard = SafetyGuard(_default_config(max_rotation_step_rad=0.1))
        previous = _action()
        # 0.5 rad about Z >> 0.1 rad limit
        candidate = _action(left_quat=_unit_quat_about_z(0.5))
        result = guard.filter_action(
            _vector(candidate), previous_safe_action=previous
        )
        assert result.status is SafetyStatus.ADJUSTED
        assert result.action is not None
        assert any(f.code is SafetyCode.ROTATION_LIMITED for f in result.findings)
        q_out = np.asarray(result.action.left_tcp_action[3:7], dtype=np.float64)
        angle = _rotation_angle(_IDENTITY_QUAT, q_out)
        assert angle == pytest.approx(0.1, abs=1e-5)
        assert abs(float(np.linalg.norm(q_out)) - 1.0) < 1e-6


# ===================================================================
# GRIPPER-RANGE (C12/B4)
# ===================================================================


class TestGripperRange:
    def test_over_range_projected_to_domain(self) -> None:
        guard = SafetyGuard(
            _default_config(
                gripper_min=0.0, gripper_max=1.0, max_gripper_step=10.0
            )
        )
        # max_gripper_step large so only range projects
        previous = _action(left_g=0.5)
        candidate = _action(left_g=1.5)
        result = guard.filter_action(
            _vector(candidate), previous_safe_action=previous
        )
        assert result.status is SafetyStatus.ADJUSTED
        assert result.action is not None
        assert any(
            f.code is SafetyCode.GRIPPER_RANGE_LIMITED for f in result.findings
        )
        assert result.action.left_gripper == pytest.approx(1.0)


# ===================================================================
# GRIPPER-STEP (C13/B4)
# ===================================================================


class TestGripperStep:
    def test_over_step_projected(self) -> None:
        guard = SafetyGuard(
            _default_config(
                gripper_min=0.0, gripper_max=1.0, max_gripper_step=0.1
            )
        )
        previous = _action(left_g=0.5)
        # 0.5 → 0.9 within range, step 0.4 > 0.1
        candidate = _action(left_g=0.9)
        result = guard.filter_action(
            _vector(candidate), previous_safe_action=previous
        )
        assert result.status is SafetyStatus.ADJUSTED
        assert result.action is not None
        assert any(
            f.code is SafetyCode.GRIPPER_STEP_LIMITED for f in result.findings
        )
        assert result.action.left_gripper == pytest.approx(0.6)


# ===================================================================
# BIMANUAL-ASSEMBLY (C14/B5)
# ===================================================================


class TestBimanualAssembly:
    def test_left_right_independent_and_16d_order(self) -> None:
        guard = SafetyGuard(_default_config(max_translation_step_m=0.03))
        previous = _action()
        # Left exceeds translation; right within limit
        candidate = _action(
            left_xyz=(0.20, 0.0, 0.0),
            right_xyz=(0.01, 0.0, 0.0),
            left_g=0.5,
            right_g=0.55,
        )
        result = guard.filter_action(
            _vector(candidate), previous_safe_action=previous
        )
        assert result.status is SafetyStatus.ADJUSTED
        assert result.action is not None
        vec = result.action.as_vector()
        assert vec.shape == (ACTION_DIM,)
        # Segment order: left_tcp(7) | right_tcp(7) | left_g | right_g
        np.testing.assert_allclose(
            vec[0:7], result.action.left_tcp_action.astype(np.float32)
        )
        np.testing.assert_allclose(
            vec[7:14], result.action.right_tcp_action.astype(np.float32)
        )
        assert float(vec[14]) == pytest.approx(result.action.left_gripper)
        assert float(vec[15]) == pytest.approx(result.action.right_gripper)
        # Right arm not translation-limited
        np.testing.assert_allclose(
            result.action.right_tcp_action[:3], [0.01, 0.0, 0.0], atol=1e-5
        )
        left_findings = [f for f in result.findings if f.side == "left"]
        right_findings = [f for f in result.findings if f.side == "right"]
        assert any(f.code is SafetyCode.TRANSLATION_LIMITED for f in left_findings)
        assert not any(
            f.code is SafetyCode.TRANSLATION_LIMITED for f in right_findings
        )
        # split_action round-trip preserves layout
        again = split_action(vec)
        np.testing.assert_allclose(
            again.left_tcp_action, result.action.left_tcp_action
        )


# ===================================================================
# OUTPUT-INVARIANT (C15/B5)
# ===================================================================


class TestOutputInvariant:
    def test_adjusted_action_still_legal(self) -> None:
        guard = SafetyGuard(
            _default_config(
                max_translation_step_m=0.03,
                max_rotation_step_rad=0.1,
                gripper_min=0.0,
                gripper_max=1.0,
                max_gripper_step=0.2,
            )
        )
        previous = _action()
        candidate = _action(
            left_xyz=(0.5, 0.0, 0.0),
            left_quat=_unit_quat_about_z(0.8),
            left_g=1.5,
            right_g=0.5,
        )
        result = guard.filter_action(
            _vector(candidate), previous_safe_action=previous
        )
        assert result.status is SafetyStatus.ADJUSTED
        assert result.action is not None
        out = result.action
        # shape / finite
        vec = out.as_vector()
        assert vec.shape == (ACTION_DIM,)
        assert np.all(np.isfinite(vec))
        # unit quaternions
        for side_tcp in (out.left_tcp_action, out.right_tcp_action):
            n = float(np.linalg.norm(side_tcp[3:7]))
            assert abs(n - 1.0) < 1e-5
        # gripper in domain
        assert 0.0 <= out.left_gripper <= 1.0
        assert 0.0 <= out.right_gripper <= 1.0


# ===================================================================
# RESULT-STATUS (B1/C5)
# ===================================================================


class TestResultStatus:
    def test_pass_adjusted_rejected(self) -> None:
        guard = SafetyGuard(_default_config(max_translation_step_m=0.03))
        previous = _action()

        # PASS: small step
        r_pass = guard.filter_action(
            _vector(_action(left_xyz=(0.01, 0.0, 0.0))),
            previous_safe_action=previous,
        )
        assert r_pass.status is SafetyStatus.PASS
        assert r_pass.action is not None
        assert r_pass.findings == ()

        # ADJUSTED: large step
        r_adj = guard.filter_action(
            _vector(_action(left_xyz=(0.20, 0.0, 0.0))),
            previous_safe_action=previous,
        )
        assert r_adj.status is SafetyStatus.ADJUSTED
        assert r_adj.action is not None
        assert len(r_adj.findings) >= 1

        # REJECTED: no reference
        r_rej = guard.filter_action(_vector(_action(left_xyz=(0.01, 0.0, 0.0))))
        assert r_rej.status is SafetyStatus.REJECTED
        assert r_rej.action is None
        assert len(r_rej.findings) >= 1


# ===================================================================
# PURITY-IMPORT (boundary)
# ===================================================================


class TestPurityImport:
    def test_safety_guard_no_forbidden_imports(self) -> None:
        path = _ACT_SRC / "service" / "safety_guard.py"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        forbidden_prefixes = (
            "rclpy",
            "rospy",
            "sensor_msgs",
            "std_msgs",
            "geometry_msgs",
            "model_deploy.act.runtime",
            "model_deploy.act.ui",
            "model_deploy.act.repo",
            "model_deploy.pi05",
        )
        imported: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                imported.append(node.module or "")
        for name in imported:
            for prefix in forbidden_prefixes:
                assert not name.startswith(prefix), f"forbidden import {name!r}"
            lowered = name.lower()
            assert "hardware" not in lowered, f"forbidden import {name!r}"
            assert "pi05" not in lowered, f"forbidden import {name!r}"

        # Positive: types + config schema expected
        assert any("safety_result" in n or "action_spec" in n for n in imported)
        assert any("schema" in n or "config" in n for n in imported)

    def test_guard_stateless_no_previous_storage(self) -> None:
        guard = SafetyGuard(_default_config())
        guard.filter_action(
            _vector(_action()), previous_safe_action=_action()
        )
        assert not hasattr(guard, "previous_safe_action")
        assert not hasattr(guard, "_previous_safe_action")
        assert not hasattr(guard, "metrics")
        assert not hasattr(guard, "_metrics")


# ===================================================================
# PUBLIC-PORT FREEZE (deploy_059): exact seam consumed by L2-06
# ===================================================================


class TestPublicPortFreeze:
    """Gate-level freeze of the exact public seam and result contract.

    Mirrors the service-level contract freeze so the integration gate also
    rejects any silent drift back to ``accepted`` / ``observation=`` double-track.
    """

    def test_filter_action_exact_signature(self) -> None:
        import inspect

        sig = inspect.signature(SafetyGuard.filter_action, eval_str=True)
        params = list(sig.parameters)
        assert params == [
            "self",
            "candidate",
            "previous_safe_action",
            "latest_observation",
        ]
        assert sig.parameters["candidate"].default is inspect.Parameter.empty
        assert sig.parameters["previous_safe_action"].default is None
        assert sig.parameters["latest_observation"].default is None
        assert sig.return_annotation is SafetyResult

    def test_safety_result_has_no_accepted_or_reason(self) -> None:
        fields = set(SafetyResult.__dataclass_fields__)
        assert fields == {"status", "action", "findings"}
        assert "accepted" not in fields
        assert "reason" not in fields

    def test_guard_has_only_frozen_config_state(self) -> None:
        guard = SafetyGuard(_default_config())
        assert set(guard.__dict__.keys()) == {"_config"}
        guard.filter_action(
            _vector(_action()), previous_safe_action=_action()
        )
        for attr in (
            "previous_safe_action",
            "_previous_safe_action",
            "fallback",
            "_fallback",
            "publish",
            "_publish",
            "permission",
            "metrics",
            "_metrics",
        ):
            assert not hasattr(guard, attr), f"unexpected state field {attr!r}"

