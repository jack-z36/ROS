"""Service orchestration tests for A1 SafetyGuard / B1-B5 (deploy_034).

Covers RESULT-STATUS (PASS / ADJUSTED / REJECTED), reference priority,
statelessness across consecutive calls, and independent left/right projection.
"""

from __future__ import annotations

import ast
import math
from pathlib import Path

import numpy as np
import pytest

from model_deploy.act.config.schema import SafetyConfig
from model_deploy.act.service import SafetyGuard
from model_deploy.act.service.safety_guard import SafetyGuard as SafetyGuardDirect
from model_deploy.act.types.action_spec import ActionSpec, split_action
from model_deploy.act.types.observation import ObservationSnapshot, ObservationState
from model_deploy.act.types.safety_result import (
    SafetyCode,
    SafetyResult,
    SafetyStatus,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_IDENTITY_QUAT = np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float64)  # xyzw


def _unit_quat_about_z(angle_rad: float) -> np.ndarray:
    half = 0.5 * angle_rad
    return np.array([0.0, 0.0, math.sin(half), math.cos(half)], dtype=np.float64)


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


def _vector_from_action(action: ActionSpec) -> np.ndarray:
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


# ---------------------------------------------------------------------------
# Construction / export
# ---------------------------------------------------------------------------


class TestSafetyGuardConstruction:
    def test_requires_safety_config(self):
        with pytest.raises(TypeError):
            SafetyGuard("not-a-config")  # type: ignore[arg-type]

    def test_holds_immutable_config(self):
        cfg = _default_config(max_translation_step_m=0.05)
        guard = SafetyGuard(cfg)
        assert guard.config is cfg
        assert guard.config.max_translation_step_m == 0.05

    def test_export_from_service_package(self):
        assert SafetyGuard is SafetyGuardDirect


# ---------------------------------------------------------------------------
# RESULT-STATUS: PASS
# ---------------------------------------------------------------------------


class TestPassPath:
    def test_small_step_relative_to_previous_is_pass(self):
        guard = SafetyGuard(_default_config())
        previous = _action(left_xyz=(0.0, 0.0, 0.0), right_xyz=(0.0, 0.0, 0.0))
        # 0.01 m << 0.03 m limit; gripper step 0.05 << 0.2
        candidate = _action(
            left_xyz=(0.01, 0.0, 0.0),
            right_xyz=(0.0, 0.01, 0.0),
            left_g=0.55,
            right_g=0.45,
        )
        result = guard.filter_action(
            _vector_from_action(candidate),
            previous_safe_action=previous,
        )
        assert result.status is SafetyStatus.PASS
        assert result.action is not None
        assert result.findings == ()
        np.testing.assert_allclose(
            result.action.left_tcp_action[:3], [0.01, 0.0, 0.0], atol=1e-6
        )

    def test_pass_via_observation_reference(self):
        guard = SafetyGuard(_default_config())
        snap = _snapshot(left_xyz=(0.0, 0.0, 0.0), right_xyz=(0.0, 0.0, 0.0))
        candidate = _action(left_xyz=(0.01, 0.0, 0.0), right_xyz=(0.0, 0.0, 0.0))
        result = guard.filter_action(
            _vector_from_action(candidate),
            latest_observation=snap,
        )
        assert result.status is SafetyStatus.PASS
        assert result.action is not None


# ---------------------------------------------------------------------------
# RESULT-STATUS: ADJUSTED
# ---------------------------------------------------------------------------


class TestAdjustedPath:
    def test_large_translation_is_adjusted_with_findings(self):
        guard = SafetyGuard(_default_config(max_translation_step_m=0.03))
        previous = _action()
        # 0.10 m >> 0.03 m
        candidate = _action(left_xyz=(0.10, 0.0, 0.0))
        result = guard.filter_action(
            _vector_from_action(candidate),
            previous_safe_action=previous,
        )
        assert result.status is SafetyStatus.ADJUSTED
        assert result.action is not None
        assert len(result.findings) >= 1
        assert any(f.code is SafetyCode.TRANSLATION_LIMITED for f in result.findings)
        left_xyz = np.asarray(result.action.left_tcp_action[:3], dtype=np.float64)
        assert abs(float(np.linalg.norm(left_xyz)) - 0.03) < 1e-5

    def test_gripper_range_and_step_adjust(self):
        guard = SafetyGuard(
            _default_config(gripper_min=0.0, gripper_max=1.0, max_gripper_step=0.1)
        )
        previous = _action(left_g=0.5, right_g=0.5)
        candidate = _action(left_g=1.5, right_g=0.5)  # out of range + large step
        result = guard.filter_action(
            _vector_from_action(candidate),
            previous_safe_action=previous,
        )
        assert result.status is SafetyStatus.ADJUSTED
        assert result.action is not None
        codes = {f.code for f in result.findings}
        assert SafetyCode.GRIPPER_RANGE_LIMITED in codes or SafetyCode.GRIPPER_STEP_LIMITED in codes
        assert 0.0 <= result.action.left_gripper <= 1.0

    def test_left_and_right_arms_adjust_independently(self):
        guard = SafetyGuard(_default_config(max_translation_step_m=0.03))
        previous = _action()
        # Only left exceeds translation limit; right stays within.
        candidate = _action(
            left_xyz=(0.20, 0.0, 0.0),
            right_xyz=(0.01, 0.0, 0.0),
        )
        result = guard.filter_action(
            _vector_from_action(candidate),
            previous_safe_action=previous,
        )
        assert result.status is SafetyStatus.ADJUSTED
        assert result.action is not None
        left_findings = [f for f in result.findings if f.side == "left"]
        right_findings = [f for f in result.findings if f.side == "right"]
        assert any(f.code is SafetyCode.TRANSLATION_LIMITED for f in left_findings)
        assert not any(f.code is SafetyCode.TRANSLATION_LIMITED for f in right_findings)
        np.testing.assert_allclose(
            result.action.right_tcp_action[:3], [0.01, 0.0, 0.0], atol=1e-6
        )


# ---------------------------------------------------------------------------
# RESULT-STATUS: REJECTED
# ---------------------------------------------------------------------------


class TestRejectedPath:
    def test_invalid_shape_rejected(self):
        guard = SafetyGuard(_default_config())
        previous = _action()
        result = guard.filter_action(
            np.zeros(8, dtype=np.float64),
            previous_safe_action=previous,
        )
        assert result.status is SafetyStatus.REJECTED
        assert result.action is None
        assert any(f.code is SafetyCode.INVALID_SHAPE for f in result.findings)

    def test_non_finite_rejected(self):
        guard = SafetyGuard(_default_config())
        previous = _action()
        vec = _vector_from_action(_action()).astype(np.float64)
        vec[0] = np.nan
        result = guard.filter_action(vec, previous_safe_action=previous)
        assert result.status is SafetyStatus.REJECTED
        assert result.action is None
        assert any(f.code is SafetyCode.NON_FINITE for f in result.findings)

    def test_no_reference_rejected(self):
        guard = SafetyGuard(_default_config())
        candidate = _action(left_xyz=(0.01, 0.0, 0.0))
        result = guard.filter_action(_vector_from_action(candidate))
        assert result.status is SafetyStatus.REJECTED
        assert result.action is None
        assert any(f.code is SafetyCode.NO_REFERENCE for f in result.findings)

    def test_invalid_quaternion_rejected(self):
        guard = SafetyGuard(_default_config())
        previous = _action()
        bad = _action()
        left = np.asarray(bad.left_tcp_action, dtype=np.float64).copy()
        left[3:7] = np.array([0.0, 0.0, 0.0, 0.0], dtype=np.float64)  # zero quat
        bad = ActionSpec(
            left_tcp_action=left.astype(np.float32),
            right_tcp_action=bad.right_tcp_action,
            left_gripper=bad.left_gripper,
            right_gripper=bad.right_gripper,
        )
        result = guard.filter_action(
            _vector_from_action(bad),
            previous_safe_action=previous,
        )
        assert result.status is SafetyStatus.REJECTED
        assert result.action is None
        assert any(f.code is SafetyCode.INVALID_QUATERNION for f in result.findings)


# ---------------------------------------------------------------------------
# Reference priority + statelessness
# ---------------------------------------------------------------------------


class TestReferenceAndStateless:
    def test_observation_is_physical_baseline(self):
        """A stale previous target cannot override the measured baseline."""
        guard = SafetyGuard(_default_config(max_translation_step_m=0.03))
        # Previous at origin; observation far away at x=1.0.  The two
        # 3cm safety envelopes do not intersect, so fail closed instead of
        # accumulating from the previous target.
        previous = _action(left_xyz=(0.0, 0.0, 0.0))
        snap = _snapshot(left_xyz=(1.0, 0.0, 0.0))
        candidate = _action(left_xyz=(0.10, 0.0, 0.0))
        result = guard.filter_action(
            _vector_from_action(candidate),
            previous_safe_action=previous,
            latest_observation=snap,
        )
        assert result.status is SafetyStatus.REJECTED
        assert result.action is None
        assert any(f.code is SafetyCode.REFERENCE_INCONSISTENT for f in result.findings)

    def test_stalled_robot_does_not_accumulate_targets(self):
        """Repeated calls stay within the measured 1cm envelope."""
        guard = SafetyGuard(_default_config(max_translation_step_m=0.01))
        previous = _action(left_xyz=(0.01, 0.0, 0.0))
        snap = _snapshot(left_xyz=(0.0, 0.0, 0.0))
        candidate = _action(left_xyz=(0.20, 0.0, 0.0))
        result = guard.filter_action(
            _vector_from_action(candidate),
            previous_safe_action=previous,
            latest_observation=snap,
        )
        assert result.action is not None
        assert float(np.linalg.norm(result.action.left_tcp_action[:3] - snap.state.left_tcp_position)) <= 0.01 + 1e-6

    def test_consecutive_calls_do_not_remember_previous(self):
        """Guard has no cross-tick memory of previous_safe_action."""
        guard = SafetyGuard(_default_config(max_translation_step_m=0.03))
        # Call 1: large step with previous at origin → ADJUSTED
        previous = _action(left_xyz=(0.0, 0.0, 0.0))
        big = _action(left_xyz=(0.20, 0.0, 0.0))
        r1 = guard.filter_action(
            _vector_from_action(big),
            previous_safe_action=previous,
        )
        assert r1.status is SafetyStatus.ADJUSTED
        assert r1.action is not None

        # Call 2: same candidate, but no previous/observation provided.
        # If Guard silently remembered r1.action as previous, this would ADJUSTED/PASS.
        # Correct behavior: REJECTED NO_REFERENCE.
        r2 = guard.filter_action(_vector_from_action(big))
        assert r2.status is SafetyStatus.REJECTED
        assert r2.action is None
        assert any(f.code is SafetyCode.NO_REFERENCE for f in r2.findings)

        # Call 3: still no implicit state — providing observation only works as bootstrap.
        snap = _snapshot(left_xyz=(0.0, 0.0, 0.0))
        r3 = guard.filter_action(
            _vector_from_action(_action(left_xyz=(0.01, 0.0, 0.0))),
            latest_observation=snap,
        )
        assert r3.status is SafetyStatus.PASS

    def test_accepts_action_spec_candidate(self):
        guard = SafetyGuard(_default_config())
        previous = _action()
        candidate = _action(left_xyz=(0.01, 0.0, 0.0))
        result = guard.filter_action(
            candidate,
            previous_safe_action=previous,
        )
        assert result.status is SafetyStatus.PASS


# ---------------------------------------------------------------------------
# Purity / no forbidden imports
# ---------------------------------------------------------------------------


class TestPurity:
    def test_safety_guard_module_has_no_forbidden_imports(self):
        path = (
            Path(__file__).resolve().parents[2]
            / "service"
            / "safety_guard.py"
        )
        tree = ast.parse(path.read_text(encoding="utf-8"))
        forbidden_prefixes = (
            "rclpy",
            "rospy",
            "sensor_msgs",
            "std_msgs",
            "geometry_msgs",
            "model_deploy.act.runtime",
            "model_deploy.act.ui",
            "model_deploy.pi05",
        )
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    for prefix in forbidden_prefixes:
                        assert not alias.name.startswith(prefix), alias.name
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                for prefix in forbidden_prefixes:
                    assert not mod.startswith(prefix), mod

    def test_guard_has_no_previous_or_metrics_instance_attrs(self):
        guard = SafetyGuard(_default_config())
        # Only config policy may be held; no business state fields.
        assert not hasattr(guard, "previous_safe_action")
        assert not hasattr(guard, "_previous_safe_action")
        assert not hasattr(guard, "metrics")
        assert not hasattr(guard, "_metrics")
        # After a call, still no hidden previous storage.
        guard.filter_action(
            _vector_from_action(_action()),
            previous_safe_action=_action(),
        )
        assert not hasattr(guard, "previous_safe_action")
        assert not hasattr(guard, "_previous_safe_action")
        assert not hasattr(guard, "metrics")


# ---------------------------------------------------------------------------
# Public port freeze (deploy_059): exact signature + contract + statelessness
# ---------------------------------------------------------------------------


class TestPublicPortContract:
    """Mechanical freeze of the L2-06-consumed public seam.

    These tests pin the exact ``filter_action`` signature, the
    ``SafetyResult`` field contract (no ``accepted`` legacy alias), and the
    statelessness of ``SafetyGuard`` so the design projection cannot silently
    drift back to the old ``accepted`` boolean / ``observation=`` keyword.
    """

    def test_filter_action_exact_signature(self):
        """Exact public signature consumed by L2-06 ControlLoop."""
        import inspect

        sig = inspect.signature(SafetyGuard.filter_action, eval_str=True)
        params = list(sig.parameters)
        assert params == [
            "self",
            "candidate",
            "previous_safe_action",
            "latest_observation",
        ]
        # candidate is required (no default).
        assert sig.parameters["candidate"].default is inspect.Parameter.empty
        # reference inputs are explicit keyword-optional.
        assert sig.parameters["previous_safe_action"].default is None
        assert sig.parameters["latest_observation"].default is None
        # Frozen return contract.
        assert sig.return_annotation is SafetyResult

    def test_filter_action_called_with_frozen_keywords(self):
        """L2-06 calls exactly once with the frozen keyword names."""
        guard = SafetyGuard(_default_config())
        previous = _action()
        result = guard.filter_action(
            _vector_from_action(_action(left_xyz=(0.01, 0.0, 0.0))),
            previous_safe_action=previous,
            latest_observation=None,
        )
        assert result.status is SafetyStatus.PASS

    def test_safety_result_has_only_status_action_findings(self):
        """SafetyResult contract: status/action/findings, no accepted alias."""
        from model_deploy.act.types.safety_result import SafetyResult as SR

        fields = set(SR.__dataclass_fields__)
        assert fields == {"status", "action", "findings"}
        # No legacy accepted/reason compatibility property.
        assert "accepted" not in fields
        assert "reason" not in fields
        # Instance also exposes none of the legacy attributes.
        result = SR(status=SafetyStatus.REJECTED, action=None, findings=())
        assert not hasattr(result, "accepted")
        assert not hasattr(result, "reason")

    def test_safety_result_is_frozen(self):
        from model_deploy.act.types.safety_result import SafetyResult as SR

        result = SR(status=SafetyStatus.PASS, action=_action(), findings=())
        with pytest.raises(Exception):
            result.status = SafetyStatus.REJECTED  # type: ignore[misc]

    def test_guard_has_no_cross_tick_or_permission_state(self):
        """SafetyGuard holds only frozen config — no fallback/publish/permission."""
        guard = SafetyGuard(_default_config())
        # Construction stores exactly the injected policy.
        assert set(guard.__dict__.keys()) == {"_config"}
        # None of the forbidden state fields may exist, before or after a call.
        forbidden = [
            "previous_safe_action",
            "_previous_safe_action",
            "last_command",
            "_last_command",
            "fallback",
            "_fallback",
            "publish",
            "_publish",
            "permission",
            "_permission",
            "metrics",
            "_metrics",
            "policy",
            "_policy",
        ]
        guard.filter_action(
            _vector_from_action(_action()),
            previous_safe_action=_action(),
        )
        for attr in forbidden:
            assert not hasattr(guard, attr), f"unexpected state field {attr!r}"
