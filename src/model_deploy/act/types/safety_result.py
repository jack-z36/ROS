"""Safety-check result contract objects for ACT model deployment (L2-04).

Defines the frozen cross-module data language consumed by L2-06 / L2-05:

- C1 ``SafetyStatus`` — PASS / ADJUSTED / REJECTED
- C2 ``SafetyCode`` — stable problem / adjustment reason codes
- C3 ``SafetyFinding`` — one side/code/before/after record
- C5 ``SafetyResult`` — frozen delivery object for the control loop

Types layer only. No safety algorithm, config, ROS, or runtime decisions.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Literal, Optional

from .action_spec import ActionSpec

# ---------------------------------------------------------------------------
# C1 SafetyStatus
# ---------------------------------------------------------------------------


class SafetyStatus(str, Enum):
    """Tri-state outcome of a single-step safety check."""

    PASS = "PASS"
    ADJUSTED = "ADJUSTED"
    REJECTED = "REJECTED"


# ---------------------------------------------------------------------------
# C2 SafetyCode
# ---------------------------------------------------------------------------


class SafetyCode(str, Enum):
    """Stable reason codes for findings and rejections.

    Values are serializable strings; do not rename without a contract bump.
    """

    INVALID_SHAPE = "INVALID_SHAPE"
    NON_FINITE = "NON_FINITE"
    INVALID_QUATERNION = "INVALID_QUATERNION"
    NO_REFERENCE = "NO_REFERENCE"
    TRANSLATION_LIMITED = "TRANSLATION_LIMITED"
    ROTATION_LIMITED = "ROTATION_LIMITED"
    GRIPPER_RANGE_LIMITED = "GRIPPER_RANGE_LIMITED"
    GRIPPER_STEP_LIMITED = "GRIPPER_STEP_LIMITED"
    INVARIANT_VIOLATION = "INVARIANT_VIOLATION"


# ---------------------------------------------------------------------------
# C3 SafetyFinding
# ---------------------------------------------------------------------------

_Side = Optional[Literal["left", "right"]]


def _is_numpy_array(value: Any) -> bool:
    """Return True if *value* is a numpy ndarray without requiring numpy import at module top for type-only use.

    Uses duck-typing on the common ndarray attributes so types/ stays free of
    accidental numpy view storage while still allowing optional numpy usage
    elsewhere in the deployment stack.
    """
    # Avoid hard import cycle; only reject real ndarray instances.
    try:
        import numpy as np
    except ImportError:  # pragma: no cover - numpy is a project dependency
        return False
    return isinstance(value, np.ndarray)


def _assert_serializable_snapshot(name: str, value: Any) -> None:
    """Reject mutable numpy views for before/after snapshots."""
    if _is_numpy_array(value):
        raise ValueError(
            f"SafetyFinding.{name} must not be a numpy ndarray; "
            "store serializable scalars or tuples instead"
        )


@dataclass(frozen=True)
class SafetyFinding:
    """One atomic safety-check record (C3).

    Attributes:
        code: Stable reason code for this finding.
        side: Arm/gripper side (``\"left\"`` / ``\"right\"``) or ``None`` for
            whole-action findings.
        before: Serializable snapshot of the value before projection (scalar or
            tuple; never a numpy view).
        after: Serializable snapshot of the value after projection.
        detail: Human-readable explanation.
    """

    code: SafetyCode
    side: _Side
    before: Any
    after: Any
    detail: str

    def __post_init__(self) -> None:
        if not isinstance(self.code, SafetyCode):
            raise TypeError(
                f"SafetyFinding.code must be SafetyCode, got {type(self.code)!r}"
            )
        if self.side is not None and self.side not in ("left", "right"):
            raise ValueError(
                f"SafetyFinding.side must be 'left', 'right', or None, got {self.side!r}"
            )
        if not isinstance(self.detail, str):
            raise TypeError(
                f"SafetyFinding.detail must be str, got {type(self.detail)!r}"
            )
        _assert_serializable_snapshot("before", self.before)
        _assert_serializable_snapshot("after", self.after)


# ---------------------------------------------------------------------------
# C5 SafetyResult
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SafetyResult:
    """Frozen safety-check result delivered to L2-06 / L2-05 (C5).

    Combination rules enforced in ``__post_init__``:

    - ``REJECTED`` requires ``action is None``.
    - ``PASS`` / ``ADJUSTED`` require a non-None ``ActionSpec`` action.
    - ``findings`` must be a ``tuple`` of ``SafetyFinding``.
    """

    status: SafetyStatus
    action: Optional[ActionSpec]
    findings: tuple[SafetyFinding, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.status, SafetyStatus):
            raise TypeError(
                f"SafetyResult.status must be SafetyStatus, got {type(self.status)!r}"
            )
        if not isinstance(self.findings, tuple):
            raise TypeError(
                f"SafetyResult.findings must be tuple, got {type(self.findings)!r}"
            )
        for i, finding in enumerate(self.findings):
            if not isinstance(finding, SafetyFinding):
                raise TypeError(
                    f"SafetyResult.findings[{i}] must be SafetyFinding, "
                    f"got {type(finding)!r}"
                )
        if self.status is SafetyStatus.REJECTED:
            if self.action is not None:
                raise ValueError(
                    "SafetyResult with status REJECTED must have action=None"
                )
        else:
            # PASS or ADJUSTED
            if self.action is None:
                raise ValueError(
                    f"SafetyResult with status {self.status.value} must have a non-None action"
                )
            if not isinstance(self.action, ActionSpec):
                raise TypeError(
                    f"SafetyResult.action must be ActionSpec or None, "
                    f"got {type(self.action)!r}"
                )
