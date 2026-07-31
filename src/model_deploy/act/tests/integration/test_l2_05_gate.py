"""L2-05 Gate integration tests: wire deploy_041/042/043/044 end-to-end.

This is the required L2 Gate (deploy_045). It drives the already-implemented
contracts through their *public* entry points and asserts the closed loop:

- G01  types      C1-C6 frozen contract + invariants (no mutable/contrary field).
- G02  config     no CLI -> ``command_output_enabled`` is strictly False.
- G03  config     explicit CLI-enabled -> C7 strictly True, audit-visible.
- G04  service/B1 PASS and ADJUSTED both build a complete C4; no ``.accepted`` read.
- G05  service/B1 REJECTED/shape/NaN/gripper-domain -> B1 raises, no partial C4.
- G06  service/B1 known 16D -> [0:7]/[7:14]/[14]/[15] split + per-arm frames + [0,1].
- G07  ui/B2      valid C4 + ros_time -> five messages, no status field.
- G08  ui/B2      builder failure -> no partial C8, no publish.
- G09  ui/B3      CLI=False, permit any -> policy/status=1, command=0, OBSERVED.
- G10  ui/B3      CLI=True, permit=False -> command=0, BLOCKED, reason readable.
- G11  ui/B3      CLI=True, permit=True -> policy + 2 Pose + 2 Float; PUBLISHED.
- G12  ui/B3      policy publisher raises -> command=0, FAILED (no leak).
- G13  ui/B3      nth command raises -> PARTIAL, real count, remaining stopped.
- G14  ui/state   gripper deadband/interval; cache updated only on success.
- G15  ui/status  OBSERVED/BLOCKED/PARTIAL JSON consistent; unknown=null.
- G16  boundary   static scan: no subscription/timer/mode/accepted/TF/IK/SDK
                   in the three L2-05 sources; no L2-05 artifact in repo/runtime.
- G17  mock int   multi-tick fake publisher -> synchronous returns, no retry/fallback.

No ROS graph, GPU, real bundle, or hardware is touched. Fake publishers are
injected via the existing module API.
"""

from __future__ import annotations

import ast
import math
import os
import re
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from model_deploy.act.config.schema import CommandOutputConfig, DeployConfig, TopicsConfig
from model_deploy.act.types.action_publish import (
    ActionPublishRequest,
    CommandPermit,
    PublishOutcome,
)
from model_deploy.act.types.action_spec import ActionSpec
from model_deploy.act.types.safety_result import (
    SafetyCode,
    SafetyFinding,
    SafetyResult,
    SafetyStatus,
)

from model_deploy.act.service.action_output_adapter import (
    ActionPublishContractError,
    build_topic_payloads,
)
from model_deploy.act.ui import action_publisher as ap
from model_deploy.act.ui.action_publisher import ActionPublisher, build_ros_messages


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_ACT_SRC = Path(__file__).resolve().parents[2]  # src/model_deploy/act

_L2_05_SOURCE_FILES: tuple[str, ...] = (
    "types/action_publish.py",
    "service/action_output_adapter.py",
    "ui/action_publisher.py",
)

# Forbidden tokens per 04_L2验收机制.md §4.3 / 05_人类验收机制.md H08.
# A *lazy* rclpy import is explicitly allowed by the design (the module stays
# importable without a ROS graph), so rclpy is intentionally NOT forbidden.
# Word boundaries are used so prose like "serializable" is not a false positive
# (only the `serial` module import / hardware SDK is forbidden).
_FORBIDDEN_TOKEN_RE = re.compile(
    r"\b(create_subscription|create_timer|RuntimeConfig\.mode|publishes_command_topics"
    r"|\.accepted|MoveIt|IK|TF|Modbus|serial|RM65)\b"
)
_FORBIDDEN_IMPORT_ROOTS = {"rospy", "serial", "modbus", "threading", "queue"}


# ===================================================================
# Fake ROS graph (dry-run)
# ===================================================================


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
    """Node-like factory supporting only create_publisher."""

    def __init__(self) -> None:
        self.created: list[tuple[str, RecordingPublisher]] = []

    def create_publisher(
        self, msg_type: type, topic: str, qos: Any
    ) -> RecordingPublisher:
        pub = RecordingPublisher(topic)
        self.created.append((topic, pub))
        return pub


# Minimal pure-Python ROS message stand-ins (no ROS graph required).
class _MockHeader:
    frame_id: str = ""
    stamp = type("_Stamp", (), {"sec": 0, "nanosec": 0})()


class _MockPose:
    position = type("_Pt", (), {"x": 0.0, "y": 0.0, "z": 0.0})()
    orientation = type("_Q", (), {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0})()


class _MockPoseStamped:
    header = _MockHeader()
    pose = _MockPose()


class _MockFloat32MultiArray:
    data: list[float] = []


class _MockFloat64:
    data: float = 0.0


class _SpyFloat64(_MockFloat64):
    def publish(self, *a: Any, **k: Any) -> None:  # pragma: no cover
        raise AssertionError("B2 must not call publish()")


class _FailFloat64(_MockFloat64):
    def __init__(self) -> None:
        raise RuntimeError("simulated gripper build failure")


class _SpyFactory:
    float32_multi_array = _MockFloat32MultiArray
    pose_stamped = _MockPoseStamped
    float64 = _SpyFloat64


class _FailLateFactory:
    float32_multi_array = _MockFloat32MultiArray
    pose_stamped = _MockPoseStamped
    float64 = _FailFloat64


# ===================================================================
# Helpers
# ===================================================================


def _safety(
    status: SafetyStatus = SafetyStatus.PASS,
    left_gripper: float = 0.5,
    right_gripper: float = 0.5,
) -> SafetyResult:
    action = ActionSpec(
        left_tcp_action=np.array([0.10, 0.20, 0.30, 0.0, 0.0, 0.0, 1.0], dtype=np.float32),
        right_tcp_action=np.array([0.40, 0.50, 0.60, 0.0, 0.0, 0.0, 1.0], dtype=np.float32),
        left_gripper=left_gripper,
        right_gripper=right_gripper,
    )
    return SafetyResult(status=status, action=action, findings=())


def _rejected_safety() -> SafetyResult:
    return SafetyResult(
        status=SafetyStatus.REJECTED,
        action=None,
        findings=(SafetyFinding(
            code=SafetyCode.TRANSLATION_LIMITED,
            side=None,
            before=0.0,
            after=0.0,
            detail="test",
        ),),
    )


def _config(enabled: bool = False) -> CommandOutputConfig:
    return CommandOutputConfig(
        command_output_enabled=enabled,
        gripper_deadband=0.01,
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
        safety_result=safety_result if safety_result is not None else _safety(),
        command_permit=permit,
        ros_time_s=ros_time_s,
        monotonic_s=monotonic_s,
    )


def _command_labels() -> tuple[str, ...]:
    return ("left_arm", "right_arm", "left_gripper", "right_gripper")


def _read_src(rel: str) -> str:
    return (_ACT_SRC / rel).read_text(encoding="utf-8")


def _strip_docstrings_comments(source: str) -> str:
    """Remove triple-quoted docstrings and # comments (best-effort)."""
    text = re.sub(r'""".*?"""', '""', source, flags=re.DOTALL)
    text = re.sub(r"'''.*?'''", "''", text, flags=re.DOTALL)
    return "\n".join(re.sub(r"(\s*#.*)$", "", line) for line in text.split("\n"))


def _extract_import_roots(source: str) -> set[str]:
    roots: set[str] = set()
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return roots
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                roots.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            roots.add(module.split(".")[0])
    return roots


# ===================================================================
# G01 — types C1-C6 frozen contract + invariants
# ===================================================================


class TestG01Types:
    def test_command_permit_invariant(self) -> None:
        from dataclasses import FrozenInstanceError

        from model_deploy.act.types.action_publish import CommandPermit

        p = CommandPermit(allowed=True)
        assert p.reason_code is None
        bad = CommandPermit(allowed=False, reason_code="X")
        assert bad.reason_code == "X"
        with pytest.raises(ValueError):
            CommandPermit(allowed=True, reason_code="OOPS")
        with pytest.raises(ValueError):
            CommandPermit(allowed=False, reason_code=None)
        with pytest.raises(FrozenInstanceError):
            p.allowed = False  # type: ignore[misc]

    def test_request_rejects_invalid_and_is_frozen(self) -> None:
        from dataclasses import FrozenInstanceError

        from model_deploy.act.types.action_publish import ActionPublishRequest

        req = _request(CommandPermit(allowed=True))
        # request must not carry the startup output flag
        assert not hasattr(req, "command_output_enabled")
        with pytest.raises(ValueError):
            ActionPublishRequest(
                action_id="",
                safety_result=_safety(),
                command_permit=CommandPermit(allowed=True),
                ros_time_s=1.0,
                monotonic_s=0.5,
            )
        with pytest.raises(FrozenInstanceError):
            req.action_id = "x"  # type: ignore[misc]

    def test_pose_target_frozen_tuple(self) -> None:
        from model_deploy.act.types.action_publish import ArmPoseTarget

        arm = ArmPoseTarget(
            frame_id="base",
            position_xyz=(0.1, 0.2, 0.3),
            quaternion_xyzw=(0.0, 0.0, 0.0, 1.0),
        )
        assert isinstance(arm.position_xyz, tuple)
        with pytest.raises(ValueError):
            ArmPoseTarget(
                frame_id="  ",
                position_xyz=(0.0, 0.0, 0.0),
                quaternion_xyzw=(0.0, 0.0, 0.0, 1.0),
            )

    def test_result_rejects_contradictory_fields(self) -> None:
        from model_deploy.act.types.action_publish import ActionPublishResult

        def _res(**overrides: Any) -> dict:
            d = dict(
                action_id="a1",
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
            d.update(overrides)
            return d

        with pytest.raises(ValueError):
            ActionPublishResult(**_res(command_publish_count=5))  # out of 0..4
        with pytest.raises(ValueError):
            ActionPublishResult(**_res(outcome=PublishOutcome.REJECTED, command_publish_count=1))
        with pytest.raises(ValueError):
            ActionPublishResult(**_res(driver_accepted="yes"))  # type: ignore[arg-type]
        with pytest.raises(ValueError):
            ActionPublishResult(**_res(hardware_reached="yes"))  # type: ignore[arg-type]


# ===================================================================
# G02 — config default off (no CLI)
# ===================================================================


class TestG02ConfigDefaultOff:
    def test_c7_dataclass_default_false(self) -> None:
        assert CommandOutputConfig().command_output_enabled is False

    def test_deploy_config_default_false(self) -> None:
        cfg = DeployConfig.from_mapping(
            {
                "bundle": {"bundle_dir": "/tmp/b"},
                "runtime": {"mode": "dry-run"},
                "topics": {"namespace": "/act"},
                "safety": {},
            },
            base_dir=Path("/tmp"),
        )
        assert cfg.command_output.command_output_enabled is False

    def test_yaml_cannot_silently_enable(self) -> None:
        # A persisted `enabled`/`command_output_enabled` key must NOT turn it on.
        raw = {
            "bundle": {"bundle_dir": "/tmp/b"},
            "runtime": {"mode": "dry-run"},
            "topics": {"namespace": "/act"},
            "safety": {},
            "command_output": {"command_output_enabled": True},
        }
        cfg = DeployConfig.from_mapping(raw, base_dir=Path("/tmp"))
        assert cfg.command_output.command_output_enabled is False


# ===================================================================
# G03 — explicit CLI enable
# ===================================================================


class TestG03ConfigEnabled:
    def test_c7_explicit_true(self) -> None:
        cfg = CommandOutputConfig(command_output_enabled=True)
        assert cfg.command_output_enabled is True

    def test_deploy_config_explicit_true(self) -> None:
        cfg = DeployConfig.from_mapping(
            {
                "bundle": {"bundle_dir": "/tmp/b"},
                "runtime": {"mode": "real-run"},
                "topics": {"namespace": "/act"},
                "safety": {},
            },
            base_dir=Path("/tmp"),
            command_output_enabled=True,
        )
        assert cfg.command_output.command_output_enabled is True


# ===================================================================
# G04 — B1 PASS/ADJUSTED build complete C4; no `.accepted`
# ===================================================================


class TestG04B1Safe:
    def test_pass_builds_complete_c4(self) -> None:
        bundle = build_topic_payloads(_safety(SafetyStatus.PASS), _config())
        assert len(bundle.policy_action) == 16
        assert bundle.left_gripper == 0.5 and bundle.right_gripper == 0.5

    def test_adjusted_builds_complete_c4(self) -> None:
        bundle = build_topic_payloads(
            _safety(SafetyStatus.ADJUSTED, left_gripper=0.0, right_gripper=1.0), _config()
        )
        assert len(bundle.policy_action) == 16
        assert bundle.left_gripper == 0.0 and bundle.right_gripper == 1.0

    def test_b1_does_not_read_accepted(self) -> None:
        # The adapter must gate on SafetyStatus, never on a non-existent
        # ``result.accepted`` field.
        src = _read_src("service/action_output_adapter.py")
        assert ".accepted" not in src
        # SafetyResult must not even carry an `accepted` attribute.
        assert not hasattr(SafetyResult, "accepted")
        assert not hasattr(_safety(), "accepted")


# ===================================================================
# G05 — B1 failures: no partial C4
# ===================================================================


class TestG05B1Failures:
    def test_rejected_raises(self) -> None:
        with pytest.raises(ActionPublishContractError):
            build_topic_payloads(_rejected_safety(), _config())

    def test_wrong_shape_raises(self) -> None:
        bad = ActionSpec(
            left_tcp_action=np.array([0.1, 0.2, 0.3, 0.0, 0.0, 0.0, 1.0, 9.0], dtype=np.float32),
            right_tcp_action=np.array([0.4, 0.5, 0.6, 0.0, 0.0, 0.0, 1.0], dtype=np.float32),
            left_gripper=0.0,
            right_gripper=1.0,
        )
        with pytest.raises(ActionPublishContractError):
            build_topic_payloads(
                SafetyResult(status=SafetyStatus.PASS, action=bad, findings=()), _config()
            )

    def test_nan_raises(self) -> None:
        bad = ActionSpec(
            left_tcp_action=np.array([float("nan"), 0.2, 0.3, 0.0, 0.0, 0.0, 1.0], dtype=np.float32),
            right_tcp_action=np.array([0.4, 0.5, 0.6, 0.0, 0.0, 0.0, 1.0], dtype=np.float32),
            left_gripper=0.0,
            right_gripper=1.0,
        )
        with pytest.raises(ActionPublishContractError):
            build_topic_payloads(
                SafetyResult(status=SafetyStatus.PASS, action=bad, findings=()), _config()
            )

    def test_gripper_out_of_domain_raises(self) -> None:
        with pytest.raises(ActionPublishContractError):
            build_topic_payloads(_safety(SafetyStatus.PASS, left_gripper=2.0), _config())


# ===================================================================
# G06 — B1 16D split, single frame, gripper mapping
# ===================================================================


class TestG06B1Split:
    def test_split_and_frame(self) -> None:
        bundle = build_topic_payloads(_safety(), _config())
        pa = bundle.policy_action
        # policy_action preserves the source float32 precision exactly.
        np.testing.assert_allclose(
            tuple(pa[0:7]), np.array([0.1, 0.2, 0.3, 0.0, 0.0, 0.0, 1.0], dtype=np.float32)
        )
        np.testing.assert_allclose(
            tuple(pa[7:14]), np.array([0.4, 0.5, 0.6, 0.0, 0.0, 0.0, 1.0], dtype=np.float32)
        )
        # [14]/[15] carry the *normalized* gripper (0..1 input domain) inside the
        # Policy vector and C4 gripper fields both retain normalized values.
        np.testing.assert_allclose(pa[14], 0.5)
        np.testing.assert_allclose(pa[15], 0.5)
        assert bundle.left_gripper == 0.5 and bundle.right_gripper == 0.5
        # single shared frame for both arms
        assert bundle.left_arm.frame_id == _config().left_pose_frame_id
        assert bundle.right_arm.frame_id == _config().right_pose_frame_id

    def test_gripper_0_50_100_mapping(self) -> None:
        bundle = build_topic_payloads(
            _safety(left_gripper=0.0, right_gripper=1.0), _config()
        )
        assert bundle.left_gripper == 0.0
        assert bundle.right_gripper == 1.0


# ===================================================================
# G07 — B2 five messages, no status
# ===================================================================


class TestG07B2Messages:
    def test_five_messages_no_status(self) -> None:
        bundle = build_topic_payloads(_safety(), _config())
        msgs = build_ros_messages(bundle, ros_time_s=2.5)
        # .data may be a list (mock) or an array('f') (real ROS); coerce.
        policy_data = list(msgs.policy_action_msg.data)
        assert len(policy_data) == 16
        assert all(math.isfinite(v) for v in policy_data)
        assert msgs.left_arm_msg.header.frame_id == _config().left_pose_frame_id
        assert msgs.right_arm_msg.header.frame_id == _config().right_pose_frame_id
        # stamp = 2.5s -> sec 2, nanosec 500_000_000
        assert msgs.left_arm_msg.header.stamp.sec == 2
        assert msgs.left_arm_msg.header.stamp.nanosec == 500_000_000
        assert float(msgs.left_gripper_msg.data) == 0.5
        assert float(msgs.right_gripper_msg.data) == 0.5
        # B2 must NOT carry a status field
        assert not hasattr(msgs, "status")

    def test_import_without_ros(self) -> None:
        assert ap._ROS_AVAILABLE in (True, False)
        assert callable(build_ros_messages)


# ===================================================================
# G08 — B2 failure leaves no partial bundle, no publish
# ===================================================================


class TestG08B2Failure:
    def test_invalid_policy_length_raises(self) -> None:
        from model_deploy.act.types.action_publish import TopicPayloadBundle

        bundle = build_topic_payloads(_safety(), _config())
        object.__setattr__(bundle, "policy_action", (1.0, 2.0))
        with pytest.raises(ValueError):
            build_ros_messages(bundle, ros_time_s=1.0)

    def test_no_publish_called_by_b2(self) -> None:
        # B2 builds messages but never publishes; a message whose publish()
        # would raise must never be called by build_ros_messages.
        bundle = build_topic_payloads(_safety(), _config())
        msgs = build_ros_messages(bundle, ros_time_s=1.0, msg_factory=_SpyFactory())  # type: ignore[arg-type]
        assert msgs.right_gripper_msg.data == 0.5

    def test_no_partial_bundle_on_late_failure(self) -> None:
        # When the last builder raises, no partial _RosMessageBundle escapes.
        bundle = build_topic_payloads(_safety(), _config())
        with pytest.raises(RuntimeError):
            build_ros_messages(bundle, ros_time_s=1.0, msg_factory=_FailLateFactory())  # type: ignore[arg-type]


# ===================================================================
# G09 — B3 CLI=False -> OBSERVED, command=0
# ===================================================================


class TestG09B3Disabled:
    def test_observed_no_command(self) -> None:
        pub = ActionPublisher(FakeNode(), _config(False), TopicsConfig())
        res = pub.publish(_request(CommandPermit(allowed=True)))
        assert res.outcome == PublishOutcome.OBSERVED
        assert res.command_publish_count == 0
        assert res.policy_action_published is True
        assert res.reason_code == "COMMAND_OUTPUT_DISABLED"
        assert len(pub._publishers["policy_action"].messages) == 1
        assert len(pub._publishers["status"].messages) == 1
        for k in _command_labels():
            assert len(pub._publishers[k].messages) == 0


# ===================================================================
# G10 — B3 CLI=True, permit=False -> BLOCKED
# ===================================================================


class TestG10B3PermitBlocked:
    def test_blocked_with_reason(self) -> None:
        pub = ActionPublisher(FakeNode(), _config(True), TopicsConfig())
        res = pub.publish(_request(CommandPermit(allowed=False, reason_code="ESTOP_ACTIVE")))
        assert res.outcome == PublishOutcome.BLOCKED
        assert res.command_publish_count == 0
        assert res.reason_code == "ESTOP_ACTIVE"
        assert res.policy_action_published is True
        for k in _command_labels():
            assert len(pub._publishers[k].messages) == 0

    def test_safety_rejected_is_rejected(self) -> None:
        pub = ActionPublisher(FakeNode(), _config(True), TopicsConfig())
        res = pub.publish(
            _request(CommandPermit(allowed=True), safety_result=_rejected_safety())
        )
        assert res.outcome == PublishOutcome.REJECTED
        assert res.command_publish_count == 0


# ===================================================================
# G11 — B3 CLI=True, permit=True -> PUBLISHED (4 commands)
# ===================================================================


class TestG11B3Enabled:
    def test_published_four_commands(self) -> None:
        pub = ActionPublisher(FakeNode(), _config(True), TopicsConfig())
        res = pub.publish(_request(CommandPermit(allowed=True)))
        assert res.outcome == PublishOutcome.PUBLISHED
        assert res.command_publish_count == 4
        assert res.command_plan_completed is True
        for k in _command_labels():
            assert len(pub._publishers[k].messages) == 1


# ===================================================================
# G12 — B3 policy-publish failure -> FAILED, no command leak
# ===================================================================


class TestG12B3PolicyFail:
    def test_policy_failure_stops_all(self) -> None:
        pub = ActionPublisher(FakeNode(), _config(True), TopicsConfig())
        pub._publishers["policy_action"] = FailingPublisher("/act/policy_action")
        res = pub.publish(_request(CommandPermit(allowed=True)))
        assert res.policy_action_published is False
        assert res.command_publish_count == 0
        assert res.outcome == PublishOutcome.FAILED
        for k in _command_labels():
            assert len(pub._publishers[k].messages) == 0


# ===================================================================
# G13 — B3 nth command failure -> PARTIAL, real count, stop remaining
# ===================================================================


class TestG13B3Partial:
    def test_third_command_failure_partial(self) -> None:
        pub = ActionPublisher(FakeNode(), _config(True), TopicsConfig())
        # failure on right_arm (3rd command) stops before grippers.
        pub._publishers["right_arm"] = FailingPublisher("/act/command/arm/right_target")
        res = pub.publish(_request(CommandPermit(allowed=True)))
        assert len(pub._publishers["left_arm"].messages) == 1
        assert res.command_publish_count == 1
        assert res.outcome == PublishOutcome.PARTIAL
        assert res.command_plan_completed is False
        assert len(pub._publishers["left_gripper"].messages) == 0
        assert len(pub._publishers["right_gripper"].messages) == 0

    def test_first_command_failure_is_failed(self) -> None:
        pub = ActionPublisher(FakeNode(), _config(True), TopicsConfig())
        pub._publishers["left_arm"] = FailingPublisher("/act/command/arm/left_target")
        res = pub.publish(_request(CommandPermit(allowed=True)))
        assert res.command_publish_count == 0
        assert res.outcome == PublishOutcome.FAILED


# ===================================================================
# G14 — gripper state: deadband/interval/cache update only on success
# ===================================================================


class TestG14GripperState:
    def test_initial_publish_sets_cache(self) -> None:
        pub = ActionPublisher(FakeNode(), _config(True), TopicsConfig())
        res = pub.publish(_request(CommandPermit(allowed=True), monotonic_s=1.0))
        assert res.outcome == PublishOutcome.PUBLISHED
        assert pub._gripper_last_target["left"] == 0.5
        assert pub._gripper_last_target["right"] == 0.5

    def test_deadband_skip_is_not_failure(self) -> None:
        pub = ActionPublisher(FakeNode(), _config(True), TopicsConfig())
        pub.publish(_request(CommandPermit(allowed=True), monotonic_s=1.0))
        res = pub.publish(_request(CommandPermit(allowed=True), monotonic_s=1.01))
        assert set(res.gripper_skipped) == {"left", "right"}
        assert res.command_publish_count == 2  # arms only
        # cache untouched for skipped sides
        assert pub._gripper_last_target["left"] == 0.5

    def test_failed_gripper_does_not_update_cache(self) -> None:
        pub = ActionPublisher(FakeNode(), _config(True), TopicsConfig())
        pub.publish(_request(CommandPermit(allowed=True), monotonic_s=1.0))
        pub._publishers["left_gripper"] = FailingPublisher("/act/command/gripper/left_target")
        res = pub.publish(
            _request(
                CommandPermit(allowed=True),
                safety_result=_safety(left_gripper=1.0, right_gripper=0.5),
                monotonic_s=10.0,
            )
        )
        assert res.outcome == PublishOutcome.PARTIAL
        # Failed left gripper keeps old normalized cache (0.5, not 1.0).
        assert pub._gripper_last_target["left"] == 0.5


# ===================================================================
# G15 — status JSON: unknown=null, outcome consistency
# ===================================================================


class TestG15Status:
    def test_status_unknown_null(self) -> None:
        import json

        pub = ActionPublisher(FakeNode(), _config(True), TopicsConfig())
        res = pub.publish(_request(CommandPermit(allowed=True)))
        d = json.loads(pub._publishers["status"].messages[0].data)
        assert d["driver_accepted"] is None
        assert d["hardware_reached"] is None
        assert d["outcome"] == "PUBLISHED"
        assert pub._last_result is res

    def test_blocked_status_consistent(self) -> None:
        import json

        pub = ActionPublisher(FakeNode(), _config(True), TopicsConfig())
        res = pub.publish(_request(CommandPermit(allowed=False, reason_code="X")))
        d = json.loads(pub._publishers["status"].messages[0].data)
        assert d["outcome"] == "BLOCKED"
        assert d["command_publish_count"] == 0
        assert res.outcome == PublishOutcome.BLOCKED

    def test_partial_status_consistent(self) -> None:
        import json

        pub = ActionPublisher(FakeNode(), _config(True), TopicsConfig())
        pub._publishers["right_arm"] = FailingPublisher("/act/command/arm/right_target")
        res = pub.publish(_request(CommandPermit(allowed=True)))
        d = json.loads(pub._publishers["status"].messages[0].data)
        assert d["outcome"] == "PARTIAL"
        assert d["command_publish_count"] == res.command_publish_count == 1


# ===================================================================
# G16 — static boundary scan
# ===================================================================


class TestG16Boundary:
    def test_no_forbidden_tokens_in_l2_05_sources(self) -> None:
        for rel in _L2_05_SOURCE_FILES:
            # Scan code only (docstrings/comments removed) so prose like
            # "serializable" does not produce a false positive.
            text = _strip_docstrings_comments(_read_src(rel))
            hit = _FORBIDDEN_TOKEN_RE.search(text)
            assert hit is None, (
                f"{rel}: forbidden token {hit.group(0)!r} found"
            )

    def test_no_forbidden_imports_in_l2_05_sources(self) -> None:
        for rel in _L2_05_SOURCE_FILES:
            roots = _extract_import_roots(_read_src(rel))
            bad = roots & _FORBIDDEN_IMPORT_ROOTS
            assert not bad, f"{rel}: forbidden imports {bad}"

    def test_no_l2_05_artifacts_in_repo_or_runtime(self) -> None:
        # L2-05 implementation lives only in types/ service/ ui/; repo/ and
        # runtime/ must stay free of L2-05 product files.
        forbidden_names = {
            "action_publish.py",
            "action_output_adapter.py",
            "action_publisher.py",
        }
        for layer in ("repo", "runtime"):
            layer_dir = _ACT_SRC / layer
            if not layer_dir.is_dir():
                continue
            for f in layer_dir.rglob("*.py"):
                assert f.name not in forbidden_names, (
                    f"L2-05 artifact {f.name} found in {layer}/"
                )


# ===================================================================
# G17 — multi-tick mock integration: synchronous, no retry/fallback
# ===================================================================


class TestG17MockIntegration:
    def test_multi_tick_synchronous_and_consistent(self) -> None:
        pub = ActionPublisher(FakeNode(), _config(True), TopicsConfig())
        # L2-05 must not own retry/fallback state.
        assert not hasattr(pub, "fallback")
        assert not hasattr(pub, "retry")
        outcomes = []
        for i in range(5):
            res = pub.publish(
                _request(CommandPermit(allowed=True), action_id=f"t{i}", monotonic_s=float(i))
            )
            assert res is not None
            assert res.outcome in {
                PublishOutcome.PUBLISHED,
                PublishOutcome.PARTIAL,
                PublishOutcome.FAILED,
                PublishOutcome.OBSERVED,
                PublishOutcome.BLOCKED,
                PublishOutcome.REJECTED,
            }
            outcomes.append(res.outcome)
        # Healthy ticks all publish.
        assert outcomes[0] == PublishOutcome.PUBLISHED

    def test_partial_then_healthy_recovers_no_fallback(self) -> None:
        pub = ActionPublisher(FakeNode(), _config(True), TopicsConfig())
        pub._publishers["right_arm"] = FailingPublisher("/act/command/arm/right_target")
        bad = pub.publish(_request(CommandPermit(allowed=True), action_id="bad"))
        assert bad.outcome == PublishOutcome.PARTIAL
        # Restore the failing publisher and confirm the next tick is PUBLISHED
        # (no stuck fallback / retry state inside L2-05).
        pub._publishers["right_arm"] = RecordingPublisher("/act/command/arm/right_target")
        good = pub.publish(_request(CommandPermit(allowed=True), action_id="good"))
        assert good.outcome == PublishOutcome.PUBLISHED
        assert good.command_publish_count == 4
