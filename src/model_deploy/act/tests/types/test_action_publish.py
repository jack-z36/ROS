"""Tests for types/action_publish.py — deploy_041 C1-C6 (G01).

Covers legal construction, illegal field-combination rejection, frozen
immutability, tuple boundaries, and the C1/C2/C6 composite invariants.
"""

from dataclasses import FrozenInstanceError

import pytest

from model_deploy.act.types.action_publish import (
    ActionPublishRequest,
    ActionPublishResult,
    ArmPoseTarget,
    CommandPermit,
    PublishOutcome,
    TopicPayloadBundle,
)
from model_deploy.act.types.safety_result import SafetyResult, SafetyStatus


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _safety(status: SafetyStatus = SafetyStatus.PASS) -> SafetyResult:
    # A passing safety result needs an ActionSpec action (PASS requires non-None).
    from model_deploy.act.types.action_spec import ActionSpec

    action = ActionSpec(
        left_tcp_action=[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
        right_tcp_action=[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
        left_gripper=0.0,
        right_gripper=0.0,
    )
    return SafetyResult(status=status, action=action, findings=())


def _permit(allowed: bool = True, reason: str | None = None) -> CommandPermit:
    return CommandPermit(allowed=allowed, reason_code=reason)


def _arm(frame: str = "base") -> ArmPoseTarget:
    return ArmPoseTarget(
        frame_id=frame,
        position_xyz=(0.1, 0.2, 0.3),
        quaternion_xyzw=(0.0, 0.0, 0.0, 1.0),
    )


# ---------------------------------------------------------------------------
# C1 CommandPermit
# ---------------------------------------------------------------------------


class TestCommandPermit:
    def test_allowed_true_requires_none_reason(self) -> None:
        p = CommandPermit(allowed=True)
        assert p.allowed is True
        assert p.reason_code is None

    def test_allowed_false_requires_nonempty_reason(self) -> None:
        p = CommandPermit(allowed=False, reason_code="SAFETY_REJECTED")
        assert p.reason_code == "SAFETY_REJECTED"

    def test_allowed_true_with_reason_rejected(self) -> None:
        with pytest.raises(ValueError):
            CommandPermit(allowed=True, reason_code="OOPS")

    def test_allowed_false_with_empty_reason_rejected(self) -> None:
        with pytest.raises(ValueError):
            CommandPermit(allowed=False, reason_code="")

    def test_allowed_false_with_none_reason_rejected(self) -> None:
        with pytest.raises(ValueError):
            CommandPermit(allowed=False, reason_code=None)

    def test_frozen(self) -> None:
        p = CommandPermit(allowed=True)
        with pytest.raises(FrozenInstanceError):
            p.allowed = False  # type: ignore[misc]


# ---------------------------------------------------------------------------
# C2 ActionPublishRequest
# ---------------------------------------------------------------------------


class TestActionPublishRequest:
    def test_legal(self) -> None:
        req = ActionPublishRequest(
            action_id="act-1",
            safety_result=_safety(),
            command_permit=_permit(),
            ros_time_s=1.0,
            monotonic_s=0.5,
        )
        assert req.action_id == "act-1"
        assert req.monotonic_s == 0.5

    def test_empty_action_id_rejected(self) -> None:
        with pytest.raises(ValueError):
            ActionPublishRequest(
                action_id="",
                safety_result=_safety(),
                command_permit=_permit(),
                ros_time_s=1.0,
                monotonic_s=0.5,
            )

    def test_negative_monotonic_rejected(self) -> None:
        with pytest.raises(ValueError):
            ActionPublishRequest(
                action_id="a",
                safety_result=_safety(),
                command_permit=_permit(),
                ros_time_s=1.0,
                monotonic_s=-1.0,
            )

    def test_nonfinite_time_rejected(self) -> None:
        with pytest.raises(ValueError):
            ActionPublishRequest(
                action_id="a",
                safety_result=_safety(),
                command_permit=_permit(),
                ros_time_s=float("nan"),
                monotonic_s=0.5,
            )

    def test_wrong_types_rejected(self) -> None:
        with pytest.raises(TypeError):
            ActionPublishRequest(
                action_id="a",
                safety_result=_permit(),  # not a SafetyResult
                command_permit=_permit(),
                ros_time_s=1.0,
                monotonic_s=0.5,
            )

    def test_request_does_not_carry_output_flag(self) -> None:
        req = ActionPublishRequest(
            action_id="a",
            safety_result=_safety(),
            command_permit=_permit(),
            ros_time_s=1.0,
            monotonic_s=0.5,
        )
        assert not hasattr(req, "command_output_enabled")

    def test_frozen(self) -> None:
        req = ActionPublishRequest(
            action_id="a",
            safety_result=_safety(),
            command_permit=_permit(),
            ros_time_s=1.0,
            monotonic_s=0.5,
        )
        with pytest.raises(FrozenInstanceError):
            req.action_id = "x"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# C3 ArmPoseTarget
# ---------------------------------------------------------------------------


class TestArmPoseTarget:
    def test_legal(self) -> None:
        a = _arm()
        assert a.position_xyz == (0.1, 0.2, 0.3)
        assert a.quaternion_xyzw == (0.0, 0.0, 0.0, 1.0)
        assert isinstance(a.position_xyz, tuple)

    def test_empty_frame_rejected(self) -> None:
        with pytest.raises(ValueError):
            ArmPoseTarget(
                frame_id="  ",
                position_xyz=(0.0, 0.0, 0.0),
                quaternion_xyzw=(0.0, 0.0, 0.0, 1.0),
            )

    def test_bad_length_rejected(self) -> None:
        with pytest.raises(ValueError):
            ArmPoseTarget(
                frame_id="base",
                position_xyz=(0.0, 0.0),
                quaternion_xyzw=(0.0, 0.0, 0.0, 1.0),
            )

    def test_nonfinite_rejected(self) -> None:
        with pytest.raises(ValueError):
            ArmPoseTarget(
                frame_id="base",
                position_xyz=(float("inf"), 0.0, 0.0),
                quaternion_xyzw=(0.0, 0.0, 0.0, 1.0),
            )

    def test_list_is_converted_to_immutable_tuple(self) -> None:
        a = ArmPoseTarget(
            frame_id="base",
            position_xyz=[0.0, 0.0, 0.0],
            quaternion_xyzw=[0.0, 0.0, 0.0, 1.0],
        )
        assert isinstance(a.position_xyz, tuple)

    def test_frozen(self) -> None:
        a = _arm()
        with pytest.raises(FrozenInstanceError):
            a.frame_id = "other"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# C4 TopicPayloadBundle
# ---------------------------------------------------------------------------


class TestTopicPayloadBundle:
    def test_legal(self) -> None:
        b = TopicPayloadBundle(
            policy_action=tuple(float(i) for i in range(16)),
            left_arm=_arm(),
            right_arm=_arm(),
            left_gripper=50.0,
            right_gripper=50.0,
        )
        assert len(b.policy_action) == 16
        assert b.left_gripper == 50.0

    def test_wrong_policy_length_rejected(self) -> None:
        with pytest.raises(ValueError):
            TopicPayloadBundle(
                policy_action=tuple(float(i) for i in range(15)),
                left_arm=_arm(),
                right_arm=_arm(),
                left_gripper=0.0,
                right_gripper=0.0,
            )

    def test_gripper_out_of_range_rejected(self) -> None:
        with pytest.raises(ValueError):
            TopicPayloadBundle(
                policy_action=tuple(float(i) for i in range(16)),
                left_arm=_arm(),
                right_arm=_arm(),
                left_gripper=120.0,
                right_gripper=0.0,
            )

    def test_bad_arm_type_rejected(self) -> None:
        with pytest.raises(TypeError):
            TopicPayloadBundle(
                policy_action=tuple(float(i) for i in range(16)),
                left_arm=_arm(),
                right_arm="not_an_arm",  # type: ignore[arg-type]
                left_gripper=0.0,
                right_gripper=0.0,
            )

    def test_frozen(self) -> None:
        b = TopicPayloadBundle(
            policy_action=tuple(float(i) for i in range(16)),
            left_arm=_arm(),
            right_arm=_arm(),
            left_gripper=0.0,
            right_gripper=0.0,
        )
        with pytest.raises(FrozenInstanceError):
            b.left_gripper = 10.0  # type: ignore[misc]


# ---------------------------------------------------------------------------
# C5 PublishOutcome
# ---------------------------------------------------------------------------


class TestPublishOutcome:
    def test_values_are_strings(self) -> None:
        assert PublishOutcome.PUBLISHED == "PUBLISHED"
        assert {o.value for o in PublishOutcome} == {
            "REJECTED",
            "OBSERVED",
            "BLOCKED",
            "PUBLISHED",
            "PARTIAL",
            "FAILED",
        }

    def test_no_mode_or_accepted(self) -> None:
        assert not hasattr(PublishOutcome, "MODE")
        assert not hasattr(PublishOutcome, "ACCEPTED")


# ---------------------------------------------------------------------------
# C6 ActionPublishResult
# ---------------------------------------------------------------------------


class TestActionPublishResult:
    def _base(self, **kwargs) -> dict:
        base = dict(
            action_id="act-1",
            safety_status=SafetyStatus.PASS,
            command_output_enabled=False,
            command_permitted=True,
            outcome=PublishOutcome.PUBLISHED,
            policy_action_published=True,
            command_publish_count=4,
            gripper_skipped=(),
            command_plan_completed=True,
            status_published=True,
        )
        base.update(kwargs)
        return base

    def test_legal_published(self) -> None:
        r = ActionPublishResult(**self._base())
        assert r.outcome is PublishOutcome.PUBLISHED
        assert r.command_publish_count == 4

    def test_legal_rejected_zero_count(self) -> None:
        r = ActionPublishResult(
            **self._base(
                outcome=PublishOutcome.REJECTED,
                command_publish_count=0,
                command_permitted=False,
                policy_action_published=False,
                command_plan_completed=False,
                status_published=False,
                reason_code="SAFETY_REJECTED",
                failure_stage="safety",
                failed_topic=None,
            )
        )
        assert r.reason_code == "SAFETY_REJECTED"
        assert r.failure_stage == "safety"
        assert r.failed_topic is None

    def test_legal_partial(self) -> None:
        r = ActionPublishResult(
            **self._base(
                outcome=PublishOutcome.PARTIAL,
                command_publish_count=2,
                command_plan_completed=False,
                reason_code="COMMAND_PUBLISH_IO_ERROR",
                failure_stage="command_publish",
                failed_topic="/act/command/arm/right_target",
            )
        )
        assert r.outcome is PublishOutcome.PARTIAL
        assert r.failure_stage == "command_publish"
        assert r.failed_topic == "/act/command/arm/right_target"

    def test_count_out_of_range_rejected(self) -> None:
        with pytest.raises(ValueError):
            ActionPublishResult(**self._base(command_publish_count=5))

    def test_rejected_with_nonzero_count_rejected(self) -> None:
        with pytest.raises(ValueError):
            ActionPublishResult(
                **self._base(outcome=PublishOutcome.REJECTED, command_publish_count=2)
            )

    def test_observed_with_nonzero_count_rejected(self) -> None:
        with pytest.raises(ValueError):
            ActionPublishResult(
                **self._base(outcome=PublishOutcome.OBSERVED, command_publish_count=1)
            )

    def test_blocked_with_nonzero_count_rejected(self) -> None:
        with pytest.raises(ValueError):
            ActionPublishResult(
                **self._base(outcome=PublishOutcome.BLOCKED, command_publish_count=1)
            )

    def test_published_requires_plan_completed(self) -> None:
        with pytest.raises(ValueError):
            ActionPublishResult(
                **self._base(command_plan_completed=False)
            )

    def test_partial_requires_count_and_not_completed(self) -> None:
        with pytest.raises(ValueError):
            ActionPublishResult(
                **self._base(outcome=PublishOutcome.PARTIAL, command_publish_count=0)
            )
        with pytest.raises(ValueError):
            ActionPublishResult(
                **self._base(
                    outcome=PublishOutcome.PARTIAL,
                    command_publish_count=2,
                    command_plan_completed=True,
                )
            )

    def test_driver_accepted_must_be_none(self) -> None:
        with pytest.raises(ValueError):
            ActionPublishResult(**self._base(driver_accepted="yes"))  # type: ignore[arg-type]

    def test_hardware_reached_must_be_none(self) -> None:
        with pytest.raises(ValueError):
            ActionPublishResult(**self._base(hardware_reached="yes"))  # type: ignore[arg-type]

    def test_gripper_skipped_stored_as_tuple(self) -> None:
        r = ActionPublishResult(**self._base(gripper_skipped=["left"]))
        assert r.gripper_skipped == ("left",)
        assert isinstance(r.gripper_skipped, tuple)

    def test_frozen(self) -> None:
        r = ActionPublishResult(**self._base())
        with pytest.raises(FrozenInstanceError):
            r.action_id = "x"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# deploy_060 — publish-failure provenance matrix (failure_stage / failed_topic)
# ---------------------------------------------------------------------------


class TestPublishProvenance:
    def _neg(self, outcome: PublishOutcome, **over) -> dict:
        d = dict(
            action_id="a1",
            safety_status=SafetyStatus.PASS,
            command_output_enabled=False,
            command_permitted=True,
            outcome=outcome,
            policy_action_published=False,
            command_publish_count=0,
            gripper_skipped=(),
            command_plan_completed=False,
            status_published=False,
            reason_code="ERR",
        )
        d.update(over)
        return d

    def test_rejected_requires_safety_stage(self) -> None:
        with pytest.raises(ValueError):
            ActionPublishResult(**self._neg(PublishOutcome.REJECTED, reason_code="SAFETY_REJECTED"))
        r = ActionPublishResult(
            **self._neg(PublishOutcome.REJECTED, reason_code="SAFETY_REJECTED", failure_stage="safety")
        )
        assert r.failure_stage == "safety"
        assert r.failed_topic is None

    def test_rejected_must_not_carry_topic(self) -> None:
        with pytest.raises(ValueError):
            ActionPublishResult(
                **self._neg(
                    PublishOutcome.REJECTED,
                    reason_code="SAFETY_REJECTED",
                    failure_stage="safety",
                    failed_topic="/act/command/status",
                )
            )

    def test_failed_requires_reason_and_stage(self) -> None:
        with pytest.raises(ValueError):
            ActionPublishResult(**self._neg(PublishOutcome.FAILED))
        with pytest.raises(ValueError):
            ActionPublishResult(**self._neg(PublishOutcome.FAILED, reason_code="X"))
        # Any valid stage is accepted as long as the outcome invariants hold.
        ok = ActionPublishResult(
            **self._neg(PublishOutcome.FAILED, reason_code="X", failure_stage="safety")
        )
        assert ok.failure_stage == "safety"

    def test_failed_policy_publish_requires_topic(self) -> None:
        with pytest.raises(ValueError):
            ActionPublishResult(
                **self._neg(PublishOutcome.FAILED, reason_code="X", failure_stage="policy_publish")
            )
        r = ActionPublishResult(
            **self._neg(
                PublishOutcome.FAILED,
                reason_code="POLICY_PUBLISH_IO_ERROR",
                failure_stage="policy_publish",
                failed_topic="/act/policy_action",
            )
        )
        assert r.failure_stage == "policy_publish"
        assert r.failed_topic == "/act/policy_action"

    def test_failed_command_build_forbids_topic(self) -> None:
        with pytest.raises(ValueError):
            ActionPublishResult(
                **self._neg(
                    PublishOutcome.FAILED,
                    reason_code="MESSAGE_BUILD_ERROR",
                    failure_stage="command_build",
                    failed_topic="/act/policy_action",
                )
            )
        r = ActionPublishResult(
            **self._neg(
                PublishOutcome.FAILED,
                reason_code="MESSAGE_BUILD_ERROR",
                failure_stage="command_build",
            )
        )
        assert r.failed_topic is None

    def test_partial_requires_command_publish_stage_and_topic(self) -> None:
        with pytest.raises(ValueError):
            ActionPublishResult(
                **self._neg(PublishOutcome.PARTIAL, reason_code="X", command_publish_count=2)
            )
        with pytest.raises(ValueError):
            ActionPublishResult(
                **self._neg(
                    PublishOutcome.PARTIAL,
                    reason_code="X",
                    command_publish_count=2,
                    failure_stage="policy_publish",
                    failed_topic="/act/policy_action",
                )
            )
        r = ActionPublishResult(
            **self._neg(
                PublishOutcome.PARTIAL,
                reason_code="COMMAND_PUBLISH_IO_ERROR",
                command_publish_count=1,
                failure_stage="command_publish",
                failed_topic="/act/command/arm/right_target",
            )
        )
        assert r.failure_stage == "command_publish"
        assert r.failed_topic == "/act/command/arm/right_target"

    def test_success_outcomes_forbid_provenance(self) -> None:
        for outcome in (PublishOutcome.PUBLISHED, PublishOutcome.OBSERVED, PublishOutcome.BLOCKED):
            with pytest.raises(ValueError):
                ActionPublishResult(
                    **self._neg(outcome, reason_code=None, failure_stage="policy_publish")
                )
            with pytest.raises(ValueError):
                ActionPublishResult(
                    **self._neg(outcome, reason_code=None, failed_topic="/act/x")
                )

    def test_invalid_stage_rejected(self) -> None:
        with pytest.raises(ValueError):
            ActionPublishResult(
                **self._neg(
                    PublishOutcome.FAILED,
                    reason_code="X",
                    failure_stage="not_a_stage",
                )
            )
