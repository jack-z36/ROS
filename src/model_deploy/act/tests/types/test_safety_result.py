"""TYPES-RESULT: tests for SafetyStatus, SafetyCode, SafetyFinding, SafetyResult."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import numpy as np
import pytest

from model_deploy.act.types.action_spec import ActionSpec
from model_deploy.act.types.safety_result import (
    SafetyCode,
    SafetyFinding,
    SafetyResult,
    SafetyStatus,
)


def _sample_action() -> ActionSpec:
    return ActionSpec(
        left_tcp_action=np.zeros(7, dtype=np.float32),
        right_tcp_action=np.zeros(7, dtype=np.float32),
        left_gripper=0.0,
        right_gripper=0.0,
    )


def _finding(
    code: SafetyCode = SafetyCode.TRANSLATION_LIMITED,
    side: str | None = "left",
) -> SafetyFinding:
    return SafetyFinding(
        code=code,
        side=side,  # type: ignore[arg-type]
        before=(0.0, 0.0, 0.0),
        after=(0.01, 0.0, 0.0),
        detail="limited",
    )


# ---------------------------------------------------------------------------
# C1 SafetyStatus
# ---------------------------------------------------------------------------


class TestSafetyStatus:
    def test_members(self) -> None:
        assert SafetyStatus.PASS.value == "PASS"
        assert SafetyStatus.ADJUSTED.value == "ADJUSTED"
        assert SafetyStatus.REJECTED.value == "REJECTED"

    def test_is_str_enum(self) -> None:
        assert isinstance(SafetyStatus.PASS, str)
        assert SafetyStatus("PASS") is SafetyStatus.PASS
        assert set(SafetyStatus) == {
            SafetyStatus.PASS,
            SafetyStatus.ADJUSTED,
            SafetyStatus.REJECTED,
        }


# ---------------------------------------------------------------------------
# C2 SafetyCode
# ---------------------------------------------------------------------------


class TestSafetyCode:
    def test_required_members_present(self) -> None:
        required = {
            "INVALID_SHAPE",
            "NON_FINITE",
            "INVALID_QUATERNION",
            "NO_REFERENCE",
            "TRANSLATION_LIMITED",
            "ROTATION_LIMITED",
            "GRIPPER_RANGE_LIMITED",
            "GRIPPER_STEP_LIMITED",
            "INVARIANT_VIOLATION",
        }
        names = {c.name for c in SafetyCode}
        assert required.issubset(names)

    def test_is_str_enum(self) -> None:
        assert isinstance(SafetyCode.NO_REFERENCE, str)
        assert SafetyCode("NO_REFERENCE") is SafetyCode.NO_REFERENCE
        assert SafetyCode.INVALID_SHAPE.value == "INVALID_SHAPE"


# ---------------------------------------------------------------------------
# C3 SafetyFinding
# ---------------------------------------------------------------------------


class TestSafetyFinding:
    def test_construct_valid(self) -> None:
        f = SafetyFinding(
            code=SafetyCode.ROTATION_LIMITED,
            side="right",
            before=(1.0, 0.0, 0.0, 0.0),
            after=(0.999, 0.001, 0.0, 0.0),
            detail="rotation step limited",
        )
        assert f.code is SafetyCode.ROTATION_LIMITED
        assert f.side == "right"
        assert f.before == (1.0, 0.0, 0.0, 0.0)
        assert f.after == (0.999, 0.001, 0.0, 0.0)
        assert f.detail == "rotation step limited"

    def test_side_none_allowed(self) -> None:
        f = SafetyFinding(
            code=SafetyCode.INVALID_SHAPE,
            side=None,
            before=None,
            after=None,
            detail="bad shape",
        )
        assert f.side is None

    def test_scalar_before_after(self) -> None:
        f = SafetyFinding(
            code=SafetyCode.GRIPPER_RANGE_LIMITED,
            side="left",
            before=1.5,
            after=1.0,
            detail="clamped",
        )
        assert f.before == 1.5
        assert f.after == 1.0

    def test_frozen_immutable(self) -> None:
        f = _finding()
        with pytest.raises(FrozenInstanceError):
            f.detail = "changed"  # type: ignore[misc]

    def test_invalid_side_raises(self) -> None:
        with pytest.raises(ValueError, match="side"):
            SafetyFinding(
                code=SafetyCode.NON_FINITE,
                side="middle",  # type: ignore[arg-type]
                before=None,
                after=None,
                detail="bad",
            )

    def test_numpy_before_rejected(self) -> None:
        with pytest.raises(ValueError, match="before"):
            SafetyFinding(
                code=SafetyCode.TRANSLATION_LIMITED,
                side="left",
                before=np.array([0.0, 0.0, 0.0]),
                after=(0.0, 0.0, 0.0),
                detail="view",
            )

    def test_numpy_after_rejected(self) -> None:
        with pytest.raises(ValueError, match="after"):
            SafetyFinding(
                code=SafetyCode.TRANSLATION_LIMITED,
                side="left",
                before=(0.0, 0.0, 0.0),
                after=np.array([0.0, 0.0, 0.0]),
                detail="view",
            )

    def test_code_type_enforced(self) -> None:
        with pytest.raises(TypeError, match="SafetyCode"):
            SafetyFinding(
                code="INVALID_SHAPE",  # type: ignore[arg-type]
                side=None,
                before=None,
                after=None,
                detail="str code",
            )


# ---------------------------------------------------------------------------
# C5 SafetyResult
# ---------------------------------------------------------------------------


class TestSafetyResult:
    def test_pass_with_action(self) -> None:
        action = _sample_action()
        result = SafetyResult(
            status=SafetyStatus.PASS,
            action=action,
            findings=(),
        )
        assert result.status is SafetyStatus.PASS
        assert result.action is action
        assert result.findings == ()
        assert isinstance(result.findings, tuple)

    def test_adjusted_with_findings(self) -> None:
        action = _sample_action()
        findings = (_finding(SafetyCode.TRANSLATION_LIMITED, "left"),)
        result = SafetyResult(
            status=SafetyStatus.ADJUSTED,
            action=action,
            findings=findings,
        )
        assert result.status is SafetyStatus.ADJUSTED
        assert result.action is action
        assert result.findings == findings
        assert len(result.findings) == 1

    def test_rejected_with_none_action(self) -> None:
        findings = (
            SafetyFinding(
                code=SafetyCode.NO_REFERENCE,
                side=None,
                before=None,
                after=None,
                detail="no previous or observation",
            ),
        )
        result = SafetyResult(
            status=SafetyStatus.REJECTED,
            action=None,
            findings=findings,
        )
        assert result.status is SafetyStatus.REJECTED
        assert result.action is None
        assert result.findings[0].code is SafetyCode.NO_REFERENCE

    def test_rejected_with_action_raises(self) -> None:
        with pytest.raises(ValueError, match="REJECTED"):
            SafetyResult(
                status=SafetyStatus.REJECTED,
                action=_sample_action(),
                findings=(),
            )

    def test_pass_without_action_raises(self) -> None:
        with pytest.raises(ValueError, match="PASS"):
            SafetyResult(
                status=SafetyStatus.PASS,
                action=None,
                findings=(),
            )

    def test_adjusted_without_action_raises(self) -> None:
        with pytest.raises(ValueError, match="ADJUSTED"):
            SafetyResult(
                status=SafetyStatus.ADJUSTED,
                action=None,
                findings=(_finding(),),
            )

    def test_findings_must_be_tuple(self) -> None:
        with pytest.raises(TypeError, match="tuple"):
            SafetyResult(
                status=SafetyStatus.PASS,
                action=_sample_action(),
                findings=[],  # type: ignore[arg-type]
            )

    def test_findings_elements_must_be_safety_finding(self) -> None:
        with pytest.raises(TypeError, match="SafetyFinding"):
            SafetyResult(
                status=SafetyStatus.ADJUSTED,
                action=_sample_action(),
                findings=("not-a-finding",),  # type: ignore[arg-type]
            )

    def test_frozen_immutable(self) -> None:
        result = SafetyResult(
            status=SafetyStatus.PASS,
            action=_sample_action(),
            findings=(),
        )
        with pytest.raises(FrozenInstanceError):
            result.status = SafetyStatus.REJECTED  # type: ignore[misc]
        with pytest.raises(FrozenInstanceError):
            result.action = None  # type: ignore[misc]

    def test_status_type_enforced(self) -> None:
        with pytest.raises(TypeError, match="SafetyStatus"):
            SafetyResult(
                status="PASS",  # type: ignore[arg-type]
                action=_sample_action(),
                findings=(),
            )


# ---------------------------------------------------------------------------
# Package export surface
# ---------------------------------------------------------------------------


class TestExports:
    def test_package_exports(self) -> None:
        from model_deploy.act import types as types_pkg

        assert types_pkg.SafetyStatus is SafetyStatus
        assert types_pkg.SafetyCode is SafetyCode
        assert types_pkg.SafetyFinding is SafetyFinding
        assert types_pkg.SafetyResult is SafetyResult
        for name in (
            "SafetyStatus",
            "SafetyCode",
            "SafetyFinding",
            "SafetyResult",
        ):
            assert name in types_pkg.__all__
