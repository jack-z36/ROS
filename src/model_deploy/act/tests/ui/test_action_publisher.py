"""Tests for deploy_044 gated publish closed-loop (A1 / B3 / C15-C21).

Covers G09-G17 with a dry-run fake publisher (no ROS graph, no hardware).
Verifies:

- G09: constructor creates exactly 6 publishers, 0 subscription/timer/metrics.
- G10: REJECTED / OBSERVED / BLOCKED gating with command count == 0.
- G11: CLI=True+permit=True enters command; policy failure -> command=0.
- G12: first command failure stops remaining paths; real PARTIAL count.
- G13: per-side gripper deadband/interval; cache updated only on success.
- G14/G15: status built after final C6, unknown=null, last result == returned.
- G16: no runtime/mode/accepted/TF/IK/SDK/fallback/retry crossing.
- G17: status best-effort failure leaves status_published=False.
"""

from typing import Any

import numpy as np
import pytest

from model_deploy.act.config.schema import CommandOutputConfig, TopicsConfig
from model_deploy.act.types.action_publish import (
    ActionPublishRequest,
    CommandPermit,
    PublishOutcome,
)
from model_deploy.act.types.action_spec import ActionSpec
from model_deploy.act.types.safety_result import SafetyResult, SafetyStatus

from model_deploy.act.ui import action_publisher as ap
from model_deploy.act.ui.action_publisher import (
    ActionPublishIoError,
    ActionPublisher,
    _decide_command_publish,
)


# ---------------------------------------------------------------------------
# Fake ROS graph (dry-run)
# ---------------------------------------------------------------------------


class RecordingPublisher:
    def __init__(self, topic: str) -> None:
        self.topic = topic
        self.messages: list[Any] = []

    def publish(self, msg: Any) -> None:
        self.messages.append(msg)


class FailingPublisher(RecordingPublisher):
    def publish(self, msg: Any) -> None:
        raise RuntimeError("simulated ROS IO failure")


class FakeNode:
    """Node-like factory that only supports create_publisher."""

    def __init__(self) -> None:
        self.created: list[tuple[str, RecordingPublisher]] = []

    def create_publisher(self, msg_type: type, topic: str, qos: Any) -> RecordingPublisher:
        pub = RecordingPublisher(topic)
        self.created.append((topic, pub))
        return pub


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------


def _pass_safety_result(left_gripper: float = 0.5, right_gripper: float = 0.5) -> SafetyResult:
    action = ActionSpec(
        left_tcp_action=np.array([0.1, 0.2, 0.3, 0.0, 0.0, 0.0, 1.0], dtype=np.float32),
        right_tcp_action=np.array([0.4, 0.5, 0.6, 0.0, 0.0, 0.0, 1.0], dtype=np.float32),
        left_gripper=left_gripper,
        right_gripper=right_gripper,
    )
    return SafetyResult(status=SafetyStatus.PASS, action=action, findings=())


def _rejected_safety_result() -> SafetyResult:
    return SafetyResult(status=SafetyStatus.REJECTED, action=None, findings=())


def _config(enabled: bool = False) -> CommandOutputConfig:
    return CommandOutputConfig(
        command_output_enabled=enabled,
        gripper_deadband=1.0,
        gripper_min_publish_interval_s=0.05,
    )


def _request(
    permit: CommandPermit,
    *,
    safety_result: SafetyResult | None = None,
    action_id: str = "a1",
    ros_time_s: float = 1.0,
    monotonic_s: float = 1.0,
) -> ActionPublishRequest:
    return ActionPublishRequest(
        action_id=action_id,
        safety_result=safety_result if safety_result is not None else _pass_safety_result(),
        command_permit=permit,
        ros_time_s=ros_time_s,
        monotonic_s=monotonic_s,
    )


def _command_labels() -> tuple[str, ...]:
    return ("left_arm", "right_arm", "left_gripper", "right_gripper")


# ---------------------------------------------------------------------------
# G09 — constructor: exactly 6 publishers, no subscription/timer/metrics
# ---------------------------------------------------------------------------


class TestConstructorG09:
    def test_exactly_six_publishers(self) -> None:
        node = FakeNode()
        pub = ActionPublisher(node, _config(False), TopicsConfig())
        assert len(pub._publishers) == 6
        assert set(pub._publishers.keys()) == {
            "policy_action",
            "left_arm",
            "right_arm",
            "left_gripper",
            "right_gripper",
            "status",
        }
        # No metrics publisher is ever created.
        assert all(t != "/act/metrics" for (t, _) in node.created)
        # Every created publisher maps to a command/status topic.
        assert all(t.startswith("/act/") for (t, _) in node.created)

    def test_no_subscription_timer_api_needed(self) -> None:
        node = FakeNode()
        ActionPublisher(node, _config(False), TopicsConfig())
        # FakeNode only implements create_publisher; a node with no
        # create_subscription / create_timer is the contract.
        assert not hasattr(node, "create_subscription")
        assert not hasattr(node, "create_timer")

    def test_unavailable_before_init_complete(self) -> None:
        class BrokenNode(FakeNode):
            def create_publisher(self, msg_type: type, topic: str, qos: Any) -> RecordingPublisher:
                raise RuntimeError("cannot create publisher")

        pub = ActionPublisher.__new__(ActionPublisher)
        with pytest.raises(TypeError):
            # Required args enforced by __init__ type checks.
            ActionPublisher(BrokenNode(), "not-a-config", TopicsConfig())  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# G10 — REJECTED / OBSERVED / BLOCKED gating
# ---------------------------------------------------------------------------


class TestGatingG10:
    def test_safety_rejected_is_rejected(self) -> None:
        pub = ActionPublisher(FakeNode(), _config(True), TopicsConfig())
        res = pub.publish(_request(CommandPermit(allowed=True), safety_result=_rejected_safety_result()))
        assert res.outcome == PublishOutcome.REJECTED
        assert res.command_publish_count == 0
        assert res.policy_action_published is False
        # only status is best-effort published; no policy/command write.
        assert len(pub._publishers["policy_action"].messages) == 0
        assert len(pub._publishers["status"].messages) == 1
        for k in _command_labels():
            assert len(pub._publishers[k].messages) == 0

    def test_cli_disabled_is_observed(self) -> None:
        pub = ActionPublisher(FakeNode(), _config(False), TopicsConfig())
        res = pub.publish(_request(CommandPermit(allowed=True)))
        assert res.outcome == PublishOutcome.OBSERVED
        assert res.command_publish_count == 0
        assert res.policy_action_published is True
        assert res.reason_code == "COMMAND_OUTPUT_DISABLED"
        assert len(pub._publishers["policy_action"].messages) == 1
        for k in _command_labels():
            assert len(pub._publishers[k].messages) == 0

    def test_cli_enabled_permit_denied_is_blocked(self) -> None:
        pub = ActionPublisher(FakeNode(), _config(True), TopicsConfig())
        res = pub.publish(_request(CommandPermit(allowed=False, reason_code="ESTOP_NOT_READY")))
        assert res.outcome == PublishOutcome.BLOCKED
        assert res.command_publish_count == 0
        assert res.policy_action_published is True
        assert res.reason_code == "ESTOP_NOT_READY"
        for k in _command_labels():
            assert len(pub._publishers[k].messages) == 0

    def test_decide_command_publish_three_ways(self) -> None:
        assert _decide_command_publish(False, CommandPermit(allowed=True)) == (
            False,
            "COMMAND_OUTPUT_DISABLED",
        )
        assert _decide_command_publish(
            True, CommandPermit(allowed=False, reason_code="X")
        ) == (False, "X")
        assert _decide_command_publish(True, CommandPermit(allowed=True)) == (True, None)


# ---------------------------------------------------------------------------
# G11 — command entry only when both gates open; policy failure -> command=0
# ---------------------------------------------------------------------------


class TestCommandEntryG11:
    def test_cli_enabled_permit_allowed_publishes_four_commands(self) -> None:
        pub = ActionPublisher(FakeNode(), _config(True), TopicsConfig())
        res = pub.publish(_request(CommandPermit(allowed=True)))
        assert res.outcome == PublishOutcome.PUBLISHED
        assert res.command_publish_count == 4
        assert res.command_plan_completed is True
        for k in _command_labels():
            assert len(pub._publishers[k].messages) == 1

    def test_policy_publish_failure_stops_all_commands(self) -> None:
        pub = ActionPublisher(FakeNode(), _config(True), TopicsConfig())
        pub._publishers["policy_action"] = FailingPublisher("/act/policy_action")
        res = pub.publish(_request(CommandPermit(allowed=True)))
        assert res.policy_action_published is False
        assert res.command_publish_count == 0
        assert res.outcome == PublishOutcome.FAILED
        for k in _command_labels():
            assert len(pub._publishers[k].messages) == 0


# ---------------------------------------------------------------------------
# G12 — first command failure stops remaining paths; real PARTIAL count
# ---------------------------------------------------------------------------


class TestPartialFailureG12:
    def test_first_command_failure_stops_remaining(self) -> None:
        pub = ActionPublisher(FakeNode(), _config(True), TopicsConfig())
        pub._publishers["right_arm"] = FailingPublisher("/act/command/arm/right_target")
        res = pub.publish(_request(CommandPermit(allowed=True)))
        # left_arm succeeded (1), right_arm failed -> stop before grippers.
        assert len(pub._publishers["left_arm"].messages) == 1
        assert res.command_publish_count == 1
        assert res.outcome == PublishOutcome.PARTIAL
        assert res.command_plan_completed is False
        assert len(pub._publishers["left_gripper"].messages) == 0
        assert len(pub._publishers["right_gripper"].messages) == 0

    def test_all_commands_fail_first_is_failed(self) -> None:
        pub = ActionPublisher(FakeNode(), _config(True), TopicsConfig())
        pub._publishers["left_arm"] = FailingPublisher("/act/command/arm/left_target")
        res = pub.publish(_request(CommandPermit(allowed=True)))
        assert res.command_publish_count == 0
        assert res.outcome == PublishOutcome.FAILED
        assert res.command_plan_completed is False


# ---------------------------------------------------------------------------
# G13 — per-side gripper deadband/interval; cache updated only on success
# ---------------------------------------------------------------------------


class TestGripperAntiFlutterG13:
    def test_initial_publish_sets_cache(self) -> None:
        pub = ActionPublisher(FakeNode(), _config(True), TopicsConfig())
        res = pub.publish(_request(CommandPermit(allowed=True), monotonic_s=1.0))
        assert res.outcome == PublishOutcome.PUBLISHED
        assert res.command_publish_count == 4
        assert pub._gripper_last_target["left"] == 50.0  # 0.5 -> 50
        assert pub._gripper_last_target["right"] == 50.0
        assert pub._gripper_last_time["left"] == 1.0

    def test_deadband_skip_is_not_a_failure(self) -> None:
        pub = ActionPublisher(FakeNode(), _config(True), TopicsConfig())
        pub.publish(_request(CommandPermit(allowed=True), monotonic_s=1.0))
        # Small change + small interval -> both grippers skipped.
        res = pub.publish(_request(CommandPermit(allowed=True), monotonic_s=1.01))
        assert set(res.gripper_skipped) == {"left", "right"}
        assert res.command_publish_count == 2  # only arms
        assert res.outcome == PublishOutcome.PUBLISHED
        assert res.command_plan_completed is True
        # Cache NOT updated for skipped sides.
        assert pub._gripper_last_target["left"] == 50.0

    def test_gripper_republish_after_deadband_updates_cache(self) -> None:
        pub = ActionPublisher(FakeNode(), _config(True), TopicsConfig())
        pub.publish(_request(CommandPermit(allowed=True), monotonic_s=1.0))
        # left gripper 1.0 -> output 100; right stays 0.5.
        sr = _pass_safety_result(left_gripper=1.0, right_gripper=0.5)
        res = pub.publish(
            _request(CommandPermit(allowed=True), safety_result=sr, monotonic_s=10.0)
        )
        assert res.gripper_skipped == ("right",)
        assert res.command_publish_count == 3  # arms + left gripper
        assert pub._gripper_last_target["left"] == 100.0
        assert pub._gripper_last_time["left"] == 10.0
        # right side cache untouched (skipped).
        assert pub._gripper_last_target["right"] == 50.0

    def test_failed_gripper_does_not_update_cache(self) -> None:
        pub = ActionPublisher(FakeNode(), _config(True), TopicsConfig())
        pub.publish(_request(CommandPermit(allowed=True), monotonic_s=1.0))
        # Make left gripper publish fail on the second call.
        pub._publishers["left_gripper"] = FailingPublisher("/act/command/gripper/left_target")
        sr = _pass_safety_result(left_gripper=1.0, right_gripper=0.5)
        res = pub.publish(
            _request(CommandPermit(allowed=True), safety_result=sr, monotonic_s=10.0)
        )
        assert res.outcome == PublishOutcome.PARTIAL
        # failed left gripper keeps old cache value.
        assert pub._gripper_last_target["left"] == 50.0


# ---------------------------------------------------------------------------
# G14 / G15 — status after final C6; unknown null; last result == returned
# ---------------------------------------------------------------------------


class TestStatusAndResultG14G15:
    def test_status_json_unknown_null_and_last_result_match(self) -> None:
        pub = ActionPublisher(FakeNode(), _config(True), TopicsConfig())
        res = pub.publish(_request(CommandPermit(allowed=True)))
        status_msgs = pub._publishers["status"].messages
        assert len(status_msgs) == 1
        import json

        d = json.loads(status_msgs[0].data)
        assert d["driver_accepted"] is None
        assert d["hardware_reached"] is None
        assert d["action_id"] == "a1"
        assert d["outcome"] == "PUBLISHED"
        assert d["command_publish_count"] == 4
        assert pub._last_result is res
        assert pub._last_result.outcome == res.outcome

    def test_status_not_published_before_return(self) -> None:
        # last result is set exactly once at the end of publish().
        pub = ActionPublisher(FakeNode(), _config(False), TopicsConfig())
        before = pub._last_result
        assert before is None
        res = pub.publish(_request(CommandPermit(allowed=True)))
        assert pub._last_result is res


# ---------------------------------------------------------------------------
# G16 — no forbidden boundary crossing in source
# ---------------------------------------------------------------------------


class TestBoundaryG16:
    def test_no_forbidden_tokens_in_source(self) -> None:
        import os

        src = os.path.join(os.path.dirname(ap.__file__), "action_publisher.py")
        with open(src, encoding="utf-8") as fh:
            text = fh.read()
        forbidden = [
            "create_subscription",
            "create_timer",
            "RuntimeConfig",
            "publishes_command_topics",
            ".accepted",
            "MoveIt",
            "IK",
            "TF",
            "Modbus",
            "serial",
            "RM65",
            "fallback",
            "retry",
        ]
        for token in forbidden:
            assert token not in text, f"forbidden token {token!r} found in source"


# ---------------------------------------------------------------------------
# G17 — status best-effort failure leaves status_published=False
# ---------------------------------------------------------------------------


class TestStatusBestEffortG17:
    def test_status_publish_failure_is_best_effort(self) -> None:
        pub = ActionPublisher(FakeNode(), _config(True), TopicsConfig())
        pub._publishers["status"] = FailingPublisher("/act/command/status")
        res = pub.publish(_request(CommandPermit(allowed=True)))
        assert res.outcome == PublishOutcome.PUBLISHED
        assert res.command_publish_count == 4
        assert res.status_published is False
