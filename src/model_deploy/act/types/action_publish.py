"""Action publish frozen RAM contracts for L2-05 (deploy_041).

Defines the cross-layer public data language consumed by L2-05 / L2-06:

- C1 ``CommandPermit``        — per-tick safety permit for command output.
- C2 ``ActionPublishRequest`` — one action's publish request (no command flag).
- C3 ``ArmPoseTarget``       — immutable pose target for one arm.
- C4 ``TopicPayloadBundle``  — full command payload bundle (B1 output).
- C5 ``PublishOutcome``      — ``str`` Enum outcome of a publish attempt.
- C6 ``ActionPublishResult`` — frozen delivery object describing what happened.

Types layer only. No ROS import, no YAML/CLI parsing, no topic publish, no
command decision, no runtime state machine, no ``accepted`` / ``mode`` / raw
gate fields. Tuple boundaries are enforced so no mutable ndarray view escapes.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Any, ClassVar, Literal, Optional

from .safety_result import SafetyResult, SafetyStatus


# ---------------------------------------------------------------------------
# Serializability / immutability helpers
# ---------------------------------------------------------------------------


def _is_numpy_array(value: Any) -> bool:
    """Return True if *value* is a numpy ndarray (without importing numpy at module top).

    Duck-typing on the common ndarray attributes so ``types/`` stays free of an
    accidental numpy view being stored inside a frozen tuple boundary.
    """
    try:
        import numpy as np
    except ImportError:  # pragma: no cover - numpy is a project dependency
        return False
    return isinstance(value, np.ndarray)


def _as_float_tuple(name: str, value: Any, length: int) -> tuple[float, ...]:
    """Validate *value* is a sequence of *length* finite floats and return a tuple.

    Rejects numpy ndarrays (mutable views) and non-finite values. Stores as an
    immutable tuple so downstream consumers cannot mutate the RAM contract.
    """
    if _is_numpy_array(value):
        raise ValueError(
            f"{name} must not be a numpy ndarray; store serializable tuples instead"
        )
    if isinstance(value, (str, bytes)) or not isinstance(value, (tuple, list)):
        raise TypeError(
            f"{name} must be a tuple/list of floats, got {type(value).__name__}"
        )
    if len(value) != length:
        raise ValueError(f"{name} must have length {length}, got {len(value)}")
    out: list[float] = []
    for i, item in enumerate(value):
        if isinstance(item, bool) or not isinstance(item, (int, float)):
            raise TypeError(f"{name}[{i}] must be a float, got {type(item).__name__}")
        f = float(item)
        if not math.isfinite(f):
            raise ValueError(f"{name}[{i}] must be finite, got {item!r}")
        out.append(f)
    return tuple(out)


# ---------------------------------------------------------------------------
# C1 CommandPermit
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CommandPermit:
    """Per-tick safety permit controlling command output for one action (C1).

    Invariants (enforced at construction):
    - ``allowed=True``  -> ``reason_code`` must be ``None``.
    - ``allowed=False`` -> ``reason_code`` must be a non-empty stable code.
    """

    allowed: bool
    reason_code: Optional[str] = None

    def __post_init__(self) -> None:
        if not isinstance(self.allowed, bool):
            raise TypeError(
                f"CommandPermit.allowed must be bool, got {type(self.allowed)!r}"
            )
        if self.allowed:
            if self.reason_code is not None:
                raise ValueError(
                    "CommandPermit with allowed=True must have reason_code=None"
                )
        else:
            if not isinstance(self.reason_code, str) or self.reason_code == "":
                raise ValueError(
                    "CommandPermit with allowed=False requires a non-empty reason_code"
                )


# ---------------------------------------------------------------------------
# C2 ActionPublishRequest
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ActionPublishRequest:
    """One action's publish request handed to the L2-05 publisher (C2).

    Invariants (enforced at construction):
    - ``action_id`` must be a non-empty string.
    - ``safety_result`` / ``command_permit`` must be the matching frozen objects.
    - ``ros_time_s`` and ``monotonic_s`` must be finite; ``monotonic_s >= 0``.
    - The request never stores ``command_output_enabled`` (that is a startup flag).
    """

    action_id: str
    safety_result: SafetyResult
    command_permit: CommandPermit
    ros_time_s: float
    monotonic_s: float

    def __post_init__(self) -> None:
        if not isinstance(self.action_id, str) or self.action_id == "":
            raise ValueError(
                "ActionPublishRequest.action_id must be a non-empty string"
            )
        if not isinstance(self.safety_result, SafetyResult):
            raise TypeError(
                f"ActionPublishRequest.safety_result must be SafetyResult, "
                f"got {type(self.safety_result)!r}"
            )
        if not isinstance(self.command_permit, CommandPermit):
            raise TypeError(
                f"ActionPublishRequest.command_permit must be CommandPermit, "
                f"got {type(self.command_permit)!r}"
            )
        for name in ("ros_time_s", "monotonic_s"):
            v = getattr(self, name)
            if isinstance(v, bool) or not isinstance(v, (int, float)):
                raise TypeError(
                    f"ActionPublishRequest.{name} must be a float, got {type(v)!r}"
                )
            if not math.isfinite(v):
                raise ValueError(
                    f"ActionPublishRequest.{name} must be finite, got {v!r}"
                )
        if self.monotonic_s < 0.0:
            raise ValueError(
                f"ActionPublishRequest.monotonic_s must be >= 0, got {self.monotonic_s!r}"
            )


# ---------------------------------------------------------------------------
# C3 ArmPoseTarget
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ArmPoseTarget:
    """Immutable pose target for one arm (C3).

    ``position_xyz`` (m) and ``quaternion_xyzw`` are stored as frozen tuples;
    numpy views are rejected. Left/right arms must share one ``frame_id``.
    """

    frame_id: str
    position_xyz: tuple[float, float, float]
    quaternion_xyzw: tuple[float, float, float, float]

    def __post_init__(self) -> None:
        if not isinstance(self.frame_id, str) or self.frame_id.strip() == "":
            raise ValueError("ArmPoseTarget.frame_id must be a non-empty string")
        object.__setattr__(
            self,
            "position_xyz",
            _as_float_tuple("ArmPoseTarget.position_xyz", self.position_xyz, 3),
        )
        object.__setattr__(
            self,
            "quaternion_xyzw",
            _as_float_tuple("ArmPoseTarget.quaternion_xyzw", self.quaternion_xyzw, 4),
        )


# ---------------------------------------------------------------------------
# C4 TopicPayloadBundle
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TopicPayloadBundle:
    """Full command payload bundle produced by B1 (C4).

    The complete, non-partially-returnable output: a 16D policy action, both
    arm pose targets, and both gripper scalars in the 0..100 output domain.
    No ROS message or status field is carried here.
    """

    POLICY_ACTION_DIM: ClassVar[int] = 16

    policy_action: tuple[float, ...]
    left_arm: ArmPoseTarget
    right_arm: ArmPoseTarget
    left_gripper: float
    right_gripper: float

    def __post_init__(self) -> None:
        pa = _as_float_tuple(
            "TopicPayloadBundle.policy_action",
            self.policy_action,
            self.POLICY_ACTION_DIM,
        )
        object.__setattr__(self, "policy_action", pa)
        if not isinstance(self.left_arm, ArmPoseTarget):
            raise TypeError(
                f"TopicPayloadBundle.left_arm must be ArmPoseTarget, "
                f"got {type(self.left_arm)!r}"
            )
        if not isinstance(self.right_arm, ArmPoseTarget):
            raise TypeError(
                f"TopicPayloadBundle.right_arm must be ArmPoseTarget, "
                f"got {type(self.right_arm)!r}"
            )
        for name in ("left_gripper", "right_gripper"):
            v = getattr(self, name)
            if isinstance(v, bool) or not isinstance(v, (int, float)):
                raise TypeError(
                    f"TopicPayloadBundle.{name} must be a float, got {type(v)!r}"
                )
            f = float(v)
            if not (0.0 <= f <= 100.0):
                raise ValueError(
                    f"TopicPayloadBundle.{name} must be in 0..100, got {f!r}"
                )
            object.__setattr__(self, name, f)


# ---------------------------------------------------------------------------
# C5 PublishOutcome
# ---------------------------------------------------------------------------


class PublishOutcome(str, Enum):
    """Outcome of a single publish attempt (C5). Values are serializable strings."""

    REJECTED = "REJECTED"
    OBSERVED = "OBSERVED"
    BLOCKED = "BLOCKED"
    PUBLISHED = "PUBLISHED"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"


# Stable failure-stage vocabulary (deploy_060 publish-failure provenance).
# Each value names the exact stage where a publish attempt failed, so L2-06
# can attribute a failure without guessing from the outcome.
PublishFailureStage = Literal[
    "safety",          # L2-04 safety gate rejected the action
    "policy_publish",  # ROS write of /act/policy_action failed
    "command_build",   # B1 payload / B2 message construction failed
    "command_publish", # ROS write of a /act/command/* topic failed
]

_PUBLISH_FAILURE_STAGES = frozenset(
    {"safety", "policy_publish", "command_build", "command_publish"}
)
# Stages where the failure is a concrete ROS I/O write and must carry the
# precise public topic that failed.
_PUBLISH_FAILURE_TOPIC_REQUIRED = frozenset({"policy_publish", "command_publish"})


# ---------------------------------------------------------------------------
# C6 ActionPublishResult
# ---------------------------------------------------------------------------

_ZERO_COUNT_OUTCOMES = frozenset(
    {PublishOutcome.REJECTED, PublishOutcome.OBSERVED, PublishOutcome.BLOCKED}
)


@dataclass(frozen=True)
class ActionPublishResult:
    """Frozen delivery object describing what happened for one action (C6).

    Invariants (enforced at construction):
    - ``command_publish_count`` must be in ``0..4``.
    - REJECTED / OBSERVED / BLOCKED require ``command_publish_count == 0``.
    - PUBLISHED requires ``command_plan_completed is True``.
    - PARTIAL requires ``command_publish_count > 0`` and ``command_plan_completed is False``.
    - ``driver_accepted`` / ``hardware_reached`` are always ``None`` in L2-05
      (never rewritten into a success claim).
    - No ``mode`` / ``accepted`` / raw gate fields exist.
    - ``failure_stage`` / ``failed_topic`` (deploy_060 provenance): mechanically
      checkable facts so L2-06 can attribute a failure without guessing from the
      outcome. For REJECTED/FAILED/PARTIAL ``reason_code`` must be a non-empty
      stable code; ``failure_stage`` names the exact failing stage and, for I/O
      failures, ``failed_topic`` carries the precise public topic/label.
    """

    action_id: str
    safety_status: SafetyStatus
    command_output_enabled: bool
    command_permitted: bool
    outcome: PublishOutcome
    policy_action_published: bool
    command_publish_count: int
    gripper_skipped: tuple[str, ...]
    command_plan_completed: bool
    status_published: bool
    reason_code: Optional[str] = None
    failure_stage: Optional[PublishFailureStage] = None
    failed_topic: Optional[str] = None
    driver_accepted: None = None
    hardware_reached: None = None

    def __post_init__(self) -> None:
        if not isinstance(self.action_id, str) or self.action_id == "":
            raise ValueError("ActionPublishResult.action_id must be a non-empty string")
        if not isinstance(self.safety_status, SafetyStatus):
            raise TypeError(
                f"ActionPublishResult.safety_status must be SafetyStatus, "
                f"got {type(self.safety_status)!r}"
            )
        for bname in (
            "command_output_enabled",
            "command_permitted",
            "policy_action_published",
            "command_plan_completed",
            "status_published",
        ):
            if not isinstance(getattr(self, bname), bool):
                raise TypeError(
                    f"ActionPublishResult.{bname} must be bool, "
                    f"got {type(getattr(self, bname))!r}"
                )
        if not isinstance(self.outcome, PublishOutcome):
            raise TypeError(
                f"ActionPublishResult.outcome must be PublishOutcome, "
                f"got {type(self.outcome)!r}"
            )
        count = self.command_publish_count
        if isinstance(count, bool) or not isinstance(count, int):
            raise TypeError(
                f"ActionPublishResult.command_publish_count must be int, got {type(count)!r}"
            )
        if not (0 <= count <= 4):
            raise ValueError(
                f"ActionPublishResult.command_publish_count must be in 0..4, got {count!r}"
            )

        sk = self.gripper_skipped
        if not isinstance(sk, (tuple, list)):
            raise TypeError(
                f"ActionPublishResult.gripper_skipped must be a tuple/list, got {type(sk)!r}"
            )
        for i, label in enumerate(sk):
            if not isinstance(label, str):
                raise TypeError(
                    f"ActionPublishResult.gripper_skipped[{i}] must be a str, "
                    f"got {type(label)!r}"
                )
        object.__setattr__(self, "gripper_skipped", tuple(sk))

        if self.driver_accepted is not None:
            raise ValueError("ActionPublishResult.driver_accepted must be None")
        if self.hardware_reached is not None:
            raise ValueError("ActionPublishResult.hardware_reached must be None")

        if self.outcome in _ZERO_COUNT_OUTCOMES and count != 0:
            raise ValueError(
                f"ActionPublishResult.outcome={self.outcome.value} requires "
                f"command_publish_count==0"
            )
        if self.outcome is PublishOutcome.PUBLISHED and not self.command_plan_completed:
            raise ValueError(
                "ActionPublishResult.outcome=PUBLISHED requires "
                "command_plan_completed=True"
            )
        if self.outcome is PublishOutcome.PARTIAL:
            if not (count > 0 and not self.command_plan_completed):
                raise ValueError(
                    "ActionPublishResult.outcome=PARTIAL requires "
                    "command_publish_count>0 and command_plan_completed=False"
                )

        # --- publish-failure provenance matrix (deploy_060) ---
        # Each negative outcome must carry a precise, mechanically-checkable
        # stage; for I/O failures it must also name the exact public topic.
        stage = self.failure_stage
        topic = self.failed_topic
        if stage is not None and stage not in _PUBLISH_FAILURE_STAGES:
            raise ValueError(
                f"ActionPublishResult.failure_stage must be one of "
                f"{sorted(_PUBLISH_FAILURE_STAGES)}, got {stage!r}"
            )

        if self.outcome in (
            PublishOutcome.REJECTED,
            PublishOutcome.FAILED,
            PublishOutcome.PARTIAL,
        ):
            if not isinstance(self.reason_code, str) or self.reason_code == "":
                raise ValueError(
                    f"ActionPublishResult.outcome={self.outcome.value} requires a "
                    f"non-empty reason_code"
                )

        if self.outcome is PublishOutcome.REJECTED:
            if stage != "safety":
                raise ValueError(
                    "ActionPublishResult.outcome=REJECTED requires "
                    "failure_stage='safety'"
                )
            if topic is not None:
                raise ValueError(
                    "ActionPublishResult.outcome=REJECTED requires failed_topic=None"
                )
        elif self.outcome in (
            PublishOutcome.PUBLISHED,
            PublishOutcome.OBSERVED,
            PublishOutcome.BLOCKED,
        ):
            if stage is not None:
                raise ValueError(
                    f"ActionPublishResult.outcome={self.outcome.value} requires "
                    f"failure_stage=None"
                )
            if topic is not None:
                raise ValueError(
                    f"ActionPublishResult.outcome={self.outcome.value} requires "
                    f"failed_topic=None"
                )
        elif self.outcome is PublishOutcome.FAILED:
            if stage is None:
                raise ValueError(
                    "ActionPublishResult.outcome=FAILED requires a failure_stage"
                )
            if stage in _PUBLISH_FAILURE_TOPIC_REQUIRED:
                if not isinstance(topic, str) or topic == "":
                    raise ValueError(
                        "ActionPublishResult.outcome=FAILED with "
                        f"failure_stage={stage!r} requires a non-empty failed_topic"
                    )
            else:
                if topic is not None:
                    raise ValueError(
                        "ActionPublishResult.outcome=FAILED with "
                        f"failure_stage={stage!r} requires failed_topic=None"
                    )
        elif self.outcome is PublishOutcome.PARTIAL:
            if stage != "command_publish":
                raise ValueError(
                    "ActionPublishResult.outcome=PARTIAL requires "
                    "failure_stage='command_publish'"
                )
            if not isinstance(topic, str) or topic == "":
                raise ValueError(
                    "ActionPublishResult.outcome=PARTIAL requires a non-empty "
                    "failed_topic"
                )


__all__ = [
    "CommandPermit",
    "ActionPublishRequest",
    "ArmPoseTarget",
    "TopicPayloadBundle",
    "PublishOutcome",
    "PublishFailureStage",
    "ActionPublishResult",
]
