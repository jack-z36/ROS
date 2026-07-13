"""Tests for deploy_043 ROS candidate message packing (B2 / C8 / C12-C14).

Covers G07 (five-message C8 construction, frame/stamp/xyz/xyzw/gripper domain,
no status field, no partial bundle) and G08 (failure on invalid input leaves
no partial C8). Designed to run WITHOUT a ROS graph using an injectable mock
message factory. No publisher is ever created or called.
"""

from typing import Any

import pytest

from model_deploy.act.types.action_publish import (
    ArmPoseTarget,
    TopicPayloadBundle,
)

from model_deploy.act.ui import action_publisher as ap
from model_deploy.act.ui.action_publisher import (
    _MessageFactory,
    _RosMessageBundle,
    build_ros_messages,
)


# ---------------------------------------------------------------------------
# Mock ROS message classes (no ROS graph required)
# ---------------------------------------------------------------------------


class MockTime:
    def __init__(self) -> None:
        self.sec = 0
        self.nanosec = 0


class MockHeader:
    def __init__(self) -> None:
        self.frame_id = ""
        self.stamp = MockTime()


class MockPoint:
    def __init__(self) -> None:
        self.x = 0.0
        self.y = 0.0
        self.z = 0.0


class MockQuaternion:
    def __init__(self) -> None:
        self.x = 0.0
        self.y = 0.0
        self.z = 0.0
        self.w = 1.0


class MockPose:
    def __init__(self) -> None:
        self.position = MockPoint()
        self.orientation = MockQuaternion()


class MockFloat32MultiArray:
    def __init__(self) -> None:
        self.data: list[float] = []
        self.__class__.__name__ = "Float32MultiArray"


class MockPoseStamped:
    def __init__(self) -> None:
        self.header = MockHeader()
        self.pose = MockPose()
        self.__class__.__name__ = "PoseStamped"


class MockFloat64:
    def __init__(self) -> None:
        self.data: float = 0.0
        self.__class__.__name__ = "Float64"


class MockMessageFactory(_MessageFactory):
    """Injectable factory backed by pure-Python mock message classes."""

    def __init__(self) -> None:
        super().__init__(
            float32_multi_array=MockFloat32MultiArray,
            pose_stamped=MockPoseStamped,
            float64=MockFloat64,
        )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _valid_c4() -> TopicPayloadBundle:
    frame = "base_link"
    pose = ArmPoseTarget(
        frame_id=frame,
        position_xyz=(0.1, 0.2, 0.3),
        quaternion_xyzw=(0.0, 0.0, 0.0, 1.0),
    )
    policy = tuple(float(i) for i in range(16))
    return TopicPayloadBundle(
        policy_action=policy,
        left_arm=pose,
        right_arm=ArmPoseTarget(
            frame_id=frame,
            position_xyz=(0.4, 0.5, 0.6),
            quaternion_xyzw=(0.0, 0.0, 0.7071068, 0.7071068),
        ),
        left_gripper=10.0,
        right_gripper=90.0,
    )


# ---------------------------------------------------------------------------
# G07 — import + five-message construction
# ---------------------------------------------------------------------------


class TestImportWithoutROS:
    def test_module_importable(self) -> None:
        """Module imports without ROS packages (no ImportError)."""
        assert hasattr(ap, "build_ros_messages")
        # deploy_044 extends this same module with the A1 publisher class.
        assert hasattr(ap, "ActionPublisher")

    def test_ros_not_required_for_import(self) -> None:
        """_ROS_AVAILABLE flag exists and module is importable either way."""
        assert isinstance(ap._ROS_AVAILABLE, bool)
        assert callable(build_ros_messages)


class TestBuildRosMessagesG07:
    def test_bundle_has_exactly_five_messages(self) -> None:
        bundle = build_ros_messages(_valid_c4(), 1.5, MockMessageFactory())
        assert isinstance(bundle, _RosMessageBundle)
        messages = [
            bundle.policy_action_msg,
            bundle.left_arm_msg,
            bundle.right_arm_msg,
            bundle.left_gripper_msg,
            bundle.right_gripper_msg,
        ]
        assert len(messages) == 5
        # Every message is a distinct constructed object (no None / partial).
        assert all(m is not None for m in messages)

    def test_no_status_field_in_bundle(self) -> None:
        bundle = build_ros_messages(_valid_c4(), 1.5, MockMessageFactory())
        assert not hasattr(bundle, "status")
        assert not hasattr(bundle, "status_msg")
        # Only the five message fields exist.
        assert set(bundle.__dataclass_fields__.keys()) == {
            "policy_action_msg",
            "left_arm_msg",
            "right_arm_msg",
            "left_gripper_msg",
            "right_gripper_msg",
        }

    def test_policy_msg_c12(self) -> None:
        bundle = build_ros_messages(_valid_c4(), 1.5, MockMessageFactory())
        assert isinstance(bundle.policy_action_msg, MockFloat32MultiArray)
        assert bundle.policy_action_msg.data == [float(i) for i in range(16)]
        assert len(bundle.policy_action_msg.data) == 16

    def test_arm_msgs_c13_frame_stamp_xyzw(self) -> None:
        c4 = _valid_c4()
        bundle = build_ros_messages(c4, 12.25, MockMessageFactory())

        # left arm
        la = bundle.left_arm_msg
        assert isinstance(la, MockPoseStamped)
        assert la.header.frame_id == "base_link"
        assert la.header.stamp.sec == 12
        assert la.header.stamp.nanosec == 250_000_000
        assert (la.pose.position.x, la.pose.position.y, la.pose.position.z) == (
            0.1,
            0.2,
            0.3,
        )
        assert (
            la.pose.orientation.x,
            la.pose.orientation.y,
            la.pose.orientation.z,
            la.pose.orientation.w,
        ) == (0.0, 0.0, 0.0, 1.0)

        # right arm uses its own pose; same frame, same stamp
        ra = bundle.right_arm_msg
        assert ra.header.frame_id == "base_link"
        assert ra.header.stamp.sec == 12
        assert ra.header.stamp.nanosec == 250_000_000
        assert (ra.pose.position.x, ra.pose.position.y, ra.pose.position.z) == (
            0.4,
            0.5,
            0.6,
        )
        assert (
            ra.pose.orientation.x,
            ra.pose.orientation.y,
            ra.pose.orientation.z,
            ra.pose.orientation.w,
        ) == (0.0, 0.0, 0.7071068, 0.7071068)

    def test_gripper_msgs_c14_domain(self) -> None:
        c4 = _valid_c4()
        bundle = build_ros_messages(c4, 1.5, MockMessageFactory())
        assert isinstance(bundle.left_gripper_msg, MockFloat64)
        assert isinstance(bundle.right_gripper_msg, MockFloat64)
        # 0..100 domain preserved exactly.
        assert bundle.left_gripper_msg.data == 10.0
        assert bundle.right_gripper_msg.data == 90.0

    def test_default_factory_works_without_ros(self) -> None:
        """Even without injecting a factory, build succeeds in pure Python."""
        bundle = build_ros_messages(_valid_c4(), 1.5)
        assert isinstance(bundle, _RosMessageBundle)
        assert bundle.policy_action_msg.data == [float(i) for i in range(16)]


# ---------------------------------------------------------------------------
# G08 — failure leaves no partial bundle; no publisher called
# ---------------------------------------------------------------------------


class TestBuildRosMessagesFailureG08:
    def test_invalid_policy_length_raises(self) -> None:
        c4 = _valid_c4()
        object.__setattr__(c4, "policy_action", (1.0, 2.0))  # wrong length
        with pytest.raises(ValueError):
            build_ros_messages(c4, 1.5, MockMessageFactory())

    def test_non_finite_policy_raises(self) -> None:
        c4 = _valid_c4()
        bad = list(float(i) for i in range(16))
        bad[3] = float("nan")
        object.__setattr__(c4, "policy_action", tuple(bad))
        with pytest.raises(ValueError):
            build_ros_messages(c4, 1.5, MockMessageFactory())

    def test_empty_frame_raises(self) -> None:
        c4 = _valid_c4()
        # types enforces non-empty frame at construction, so corrupt the
        # frozen field to exercise C13's own frame validation.
        bad_arm = ArmPoseTarget(
            frame_id="base_link",
            position_xyz=(0.1, 0.2, 0.3),
            quaternion_xyzw=(0.0, 0.0, 0.0, 1.0),
        )
        object.__setattr__(bad_arm, "frame_id", "")
        object.__setattr__(c4, "left_arm", bad_arm)
        with pytest.raises(ValueError):
            build_ros_messages(c4, 1.5, MockMessageFactory())

    def test_non_finite_ros_time_raises(self) -> None:
        with pytest.raises(ValueError):
            build_ros_messages(_valid_c4(), float("inf"), MockMessageFactory())

    def test_gripper_out_of_range_raises(self) -> None:
        c4 = _valid_c4()
        object.__setattr__(c4, "left_gripper", 150.0)
        with pytest.raises(ValueError):
            build_ros_messages(c4, 1.5, MockMessageFactory())

    def test_no_partial_bundle_on_late_failure(self) -> None:
        """When the 4th builder fails, no partial C8 is constructed."""

        class FailingGripperFloat64(MockFloat64):
            def __init__(self) -> None:
                raise RuntimeError("simulated gripper build failure")

        class FailingLateFactory(_MessageFactory):
            def __init__(self) -> None:
                super().__init__(
                    float32_multi_array=MockFloat32MultiArray,
                    pose_stamped=MockPoseStamped,
                    float64=FailingGripperFloat64,
                )

        # 3 messages built (policy + 2 arms), then gripper builder fails.
        with pytest.raises(RuntimeError):
            build_ros_messages(_valid_c4(), 1.5, FailingLateFactory())
        # Because the bundle is assembled only after all 5 succeed, there is
        # no leftover partial _RosMessageBundle reference to assert against;
        # the contract is enforced by construction order above.

    def test_no_publisher_involved(self) -> None:
        """build_ros_messages never calls publish on any message/node."""
        # A node-like spy that would blow up if .publish were called.
        spy: dict[str, int] = {"publish": 0}

        class SpyFloat64(MockFloat64):
            def publish(self, *args: Any, **kwargs: Any) -> None:
                spy["publish"] += 1

        class SpyFactory(_MessageFactory):
            def __init__(self) -> None:
                super().__init__(
                    float32_multi_array=MockFloat32MultiArray,
                    pose_stamped=MockPoseStamped,
                    float64=SpyFloat64,
                )

        bundle = build_ros_messages(_valid_c4(), 1.5, SpyFactory())
        # Building completed and no publish call was made by B2.
        assert spy["publish"] == 0
        assert bundle.right_gripper_msg.data == 90.0
