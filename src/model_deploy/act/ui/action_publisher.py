"""Action publisher — ROS candidate message packing (deploy_043) + gated publish (deploy_044).

This module implements:

- deploy_043 — B2 / C8 / C12-C14 (ROS candidate message packing):
  - C8 ``_RosMessageBundle``: module-private five-message container (no status).
  - C12 ``_build_policy_msg`` / C13 ``_build_arm_msg`` / C14 ``_build_gripper_msg``.
  - B2 ``build_ros_messages``: C4 ``TopicPayloadBundle`` -> five ROS messages.
- deploy_044 — A1 / B3 / C15-C21 (gated publish closed-loop):
  - A1 ``ActionPublisher``: long-lived holder of exactly six publishers + gripper
    anti-flutter RAM state + last result.
  - B3 ``ActionPublisher.publish``: the single public business entry; orders
    B1 -> B2 -> C15 -> policy -> optional commands -> C19 -> C20/status -> C21.
  - C15 gate decision, C16/C18 gripper anti-flutter, C17 ROS write, C19 result,
    C20 status, C21 last-result record.

The module performs a lazy ROS import so it stays importable and unit-testable
without a ROS graph. Command topics are written only when BOTH the CLI master
switch (C7 ``command_output_enabled``) AND the per-tick ``CommandPermit`` allow
it; otherwise only ``/act/policy_action`` and ``/act/command/status`` are written.

Dependency surface: ``model_deploy.act.types.action_publish`` (C1-C7),
``model_deploy.act.config.schema`` (C7), ``model_deploy.act.service.action_output_adapter``
(B1). It does not import the runtime or repo layers, nor any hardware-driver
packages; it performs no coordinate-transform or kinematics computation.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from typing import Any, Callable, Optional

from model_deploy.act.config.schema import CommandOutputConfig, TopicsConfig
from model_deploy.act.service.action_output_adapter import (
    ActionPublishContractError,
    build_topic_payloads,
)
from model_deploy.act.types.action_publish import (
    ActionPublishRequest,
    ActionPublishResult,
    CommandPermit,
    PublishOutcome,
    TopicPayloadBundle,
)

# ---------------------------------------------------------------------------
# Lazy ROS detection (importable without rclpy installed)
# ---------------------------------------------------------------------------

_ROS_AVAILABLE: bool = False
try:
    import rclpy  # noqa: F401
    from geometry_msgs.msg import PoseStamped  # noqa: F401
    from std_msgs.msg import Float32MultiArray, Float64, String  # noqa: F401

    _ROS_AVAILABLE = True
except ImportError:  # pragma: no cover - ROS optional for import/test
    pass


# ---------------------------------------------------------------------------
# Lightweight pure-Python message stand-ins (used when ROS is absent)
# ---------------------------------------------------------------------------


class _MockTime:
    def __init__(self) -> None:
        self.sec: int = 0
        self.nanosec: int = 0


class _MockHeader:
    def __init__(self) -> None:
        self.frame_id: str = ""
        self.stamp = _MockTime()


class _MockPoint:
    def __init__(self) -> None:
        self.x = 0.0
        self.y = 0.0
        self.z = 0.0


class _MockQuaternion:
    def __init__(self) -> None:
        self.x = 0.0
        self.y = 0.0
        self.z = 0.0
        self.w = 1.0


class _MockPose:
    def __init__(self) -> None:
        self.position = _MockPoint()
        self.orientation = _MockQuaternion()


class _MockFloat32MultiArray:
    def __init__(self) -> None:
        self.data: list[float] = []

    @property
    def __name__(self) -> str:  # pragma: no cover - helps debug only
        return "Float32MultiArray"


class _MockPoseStamped:
    def __init__(self) -> None:
        self.header = _MockHeader()
        self.pose = _MockPose()


class _MockFloat64:
    def __init__(self) -> None:
        self.data: float = 0.0


class _MockString:
    """Pure-Python stand-in for ``std_msgs.msg.String`` (no ROS required)."""

    def __init__(self, data: str = "") -> None:
        self.data: str = data


def _resolve_status_msg_class() -> type:
    """Return the String message class (real ROS when available, else mock)."""
    if _ROS_AVAILABLE:
        return String  # type: ignore[name-defined]  # noqa: F821
    return _MockString


@dataclass(frozen=True)
class _MessageFactory:
    """Bundle of ROS message classes used to build candidate messages.

    Injectable so unit tests can supply mock message classes without a ROS
    graph. The default factory selects real ROS messages when available and
    the pure-Python stand-ins otherwise.
    """

    float32_multi_array: type
    pose_stamped: type
    float64: type


def _default_message_factory() -> _MessageFactory:
    """Return the default message factory based on ROS availability."""
    if _ROS_AVAILABLE:
        return _MessageFactory(Float32MultiArray, PoseStamped, Float64)  # type: ignore[name-defined]  # noqa: F821
    return _MessageFactory(_MockFloat32MultiArray, _MockPoseStamped, _MockFloat64)


# ---------------------------------------------------------------------------
# C8 — module-private five-message bundle
# ---------------------------------------------------------------------------


@dataclass
class _RosMessageBundle:
    """Module-private container for the five candidate ROS messages (C8).

    Short-lived and used only inside this module. Holds no status field. The
    referenced ROS messages are themselves mutable, so this is intentionally
    NOT a frozen cross-layer contract (it must not be exported from
    ``ui/__init__.py``).
    """

    policy_action_msg: Any
    left_arm_msg: Any
    right_arm_msg: Any
    left_gripper_msg: Any
    right_gripper_msg: Any


# ---------------------------------------------------------------------------
# Finite-tuple helper
# ---------------------------------------------------------------------------


def _as_finite_tuple(name: str, value: Any, length: int) -> tuple[float, ...]:
    """Validate *value* is a sequence of *length* finite floats; return tuple."""
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
# C12 — policy 16D -> Float32MultiArray
# ---------------------------------------------------------------------------


def _build_policy_msg(policy_action: Any, factory: _MessageFactory) -> Any:
    """C12: 16D policy tuple -> ``Float32MultiArray``.

    Raises ``TypeError``/``ValueError`` on wrong type, wrong length, or
    non-finite entries. Does not touch any process-external resource.
    """
    if isinstance(policy_action, (str, bytes)) or not isinstance(
        policy_action, (tuple, list)
    ):
        raise TypeError(
            f"policy_action must be a tuple/list of floats, "
            f"got {type(policy_action).__name__}"
        )
    if len(policy_action) != 16:
        raise ValueError(
            f"policy_action must have length 16, got {len(policy_action)}"
        )
    data: list[float] = []
    for i, item in enumerate(policy_action):
        if isinstance(item, bool) or not isinstance(item, (int, float)):
            raise TypeError(
                f"policy_action[{i}] must be a float, got {type(item).__name__}"
            )
        f = float(item)
        if not math.isfinite(f):
            raise ValueError(f"policy_action[{i}] must be finite, got {item!r}")
        data.append(f)
    msg = factory.float32_multi_array()
    msg.data = list(data)
    return msg


# ---------------------------------------------------------------------------
# C13 — ArmPoseTarget + ROS time -> PoseStamped
# ---------------------------------------------------------------------------


def _build_arm_msg(arm: Any, ros_time_s: float, factory: _MessageFactory) -> Any:
    """C13: ``ArmPoseTarget`` + finite ROS time -> ``PoseStamped``.

    Sets header ``frame_id`` + ``stamp`` and pose ``position`` (xyz) and
    ``orientation`` (xyzw). Raises on non-finite time, empty frame, or invalid
    pose tuple. Performs no coordinate transform and reads no external resource.
    """
    if isinstance(ros_time_s, bool) or not isinstance(ros_time_s, (int, float)):
        raise TypeError(f"ros_time_s must be a float, got {type(ros_time_s).__name__}")
    if not math.isfinite(ros_time_s):
        raise ValueError(f"ros_time_s must be finite, got {ros_time_s!r}")

    frame_id = getattr(arm, "frame_id", None)
    if not isinstance(frame_id, str) or frame_id.strip() == "":
        raise ValueError(f"arm.frame_id must be a non-empty string, got {frame_id!r}")

    pos = getattr(arm, "position_xyz", None)
    quat = getattr(arm, "quaternion_xyzw", None)
    pos_list = _as_finite_tuple("position_xyz", pos, 3)
    quat_list = _as_finite_tuple("quaternion_xyzw", quat, 4)

    sec = int(ros_time_s)
    nanosec = int(round((ros_time_s - sec) * 1_000_000_000))
    if nanosec >= 1_000_000_000:
        nanosec -= 1_000_000_000
        sec += 1
    elif nanosec < 0:
        nanosec += 1_000_000_000
        sec -= 1

    msg = factory.pose_stamped()
    msg.header.frame_id = frame_id
    msg.header.stamp.sec = sec
    msg.header.stamp.nanosec = nanosec
    (msg.pose.position.x, msg.pose.position.y, msg.pose.position.z) = pos_list
    (
        msg.pose.orientation.x,
        msg.pose.orientation.y,
        msg.pose.orientation.z,
        msg.pose.orientation.w,
    ) = quat_list
    return msg


# ---------------------------------------------------------------------------
# C14 — normalized gripper width -> Float64
# ---------------------------------------------------------------------------


def _build_gripper_msg(gripper: Any, factory: _MessageFactory) -> Any:
    """C14: normalized [0,1] gripper width -> ``Float64``.

    Raises on non-finite or out-of-range input. Does not read/write any
    external resource.
    """
    if isinstance(gripper, bool) or not isinstance(gripper, (int, float)):
        raise TypeError(f"gripper must be a float, got {type(gripper).__name__}")
    f = float(gripper)
    if not math.isfinite(f):
        raise ValueError(f"gripper must be finite, got {gripper!r}")
    if not (0.0 <= f <= 1.0):
        raise ValueError(f"gripper must be in [0,1], got {f!r}")
    msg = factory.float64()
    msg.data = f
    return msg


# ---------------------------------------------------------------------------
# B2 — pack full C4 into a five-message C8
# ---------------------------------------------------------------------------


def build_ros_messages(
    payloads: TopicPayloadBundle,
    ros_time_s: float,
    msg_factory: Optional[_MessageFactory] = None,
) -> _RosMessageBundle:
    """B2: pack a complete C4 ``TopicPayloadBundle`` into a five-message C8.

    Order: C12 -> C13 x2 -> C14 x2. If any builder raises, the exception
    propagates and no partial C8 is returned. Performs no publish and builds
    no status. The optional ``msg_factory`` lets callers inject mock message
    classes for testing without a ROS graph.
    """
    if not isinstance(payloads, TopicPayloadBundle):
        raise TypeError(
            f"payloads must be TopicPayloadBundle, got {type(payloads).__name__}"
        )
    factory = msg_factory if msg_factory is not None else _default_message_factory()

    policy_msg = _build_policy_msg(payloads.policy_action, factory)
    left_arm_msg = _build_arm_msg(payloads.left_arm, ros_time_s, factory)
    right_arm_msg = _build_arm_msg(payloads.right_arm, ros_time_s, factory)
    left_gripper_msg = _build_gripper_msg(payloads.left_gripper, factory)
    right_gripper_msg = _build_gripper_msg(payloads.right_gripper, factory)

    return _RosMessageBundle(
        policy_action_msg=policy_msg,
        left_arm_msg=left_arm_msg,
        right_arm_msg=right_arm_msg,
        left_gripper_msg=left_gripper_msg,
        right_gripper_msg=right_gripper_msg,
    )


# ---------------------------------------------------------------------------
# deploy_044 — A1 / B3 / C15-C21 gated publish closed-loop
# ---------------------------------------------------------------------------


class ActionPublishIoError(Exception):
    """Raised by C17 when a single publisher write fails.

    Carries the topic ``label`` so B3 can record the real failure and stop the
    remaining command path without pretending the write succeeded.
    """

    def __init__(self, label: str) -> None:
        super().__init__(f"publish failed for topic label {label!r}")
        self.label = label


def _decide_command_publish(
    command_output_enabled: bool,
    permit: CommandPermit,
) -> tuple[bool, Optional[str]]:
    """C15: decide whether command topics may be written (pure computation).

    Returns ``(allow, reason_code)``:

    - ``enabled=False``        -> ``(False, "COMMAND_OUTPUT_DISABLED")``
    - ``enabled=True, deny``   -> ``(False, permit.reason_code)``
    - ``enabled=True, allow``  -> ``(True, None)``

    Does not read argv/topic, does not mutate state, does not write ROS.
    """
    if not command_output_enabled:
        return False, "COMMAND_OUTPUT_DISABLED"
    if not permit.allowed:
        return False, permit.reason_code
    return True, None


def _decide_gripper_publish(
    side: str,
    target: float,
    last_target: Optional[float],
    last_time: Optional[float],
    monotonic_s: float,
    deadband: float,
    min_interval_s: float,
) -> tuple[bool, Optional[str]]:
    """C16: per-side gripper anti-flutter decision (pure computation).

    Publish iff there is no previous successful target, or both the deadband
    and the minimum publish interval are satisfied. Returns
    ``(publish, skip_reason)``; ``skip_reason`` is ``None`` when publishing.
    """
    if last_target is None or last_time is None:
        return True, None
    deadband_ok = abs(target - last_target) >= deadband
    interval_ok = (monotonic_s - last_time) >= min_interval_s
    if deadband_ok and interval_ok:
        return True, None
    return False, "GRIPPER_DEADBAND_SKIP"


class ActionPublisher:
    """A1: long-lived ROS command publisher with gated write policy (deploy_044).

    Holds exactly six publishers (policy, left/right arm, left/right gripper,
    status) and the minimal RAM state needed for gripper anti-flutter and the
    last delivery result. The only public business entry is ``publish`` (B3).
    """

    _PUBLISHER_LABELS = (
        "policy_action",
        "left_arm",
        "right_arm",
        "left_gripper",
        "right_gripper",
        "status",
    )

    def __init__(
        self,
        node: Any,
        command_output_config: CommandOutputConfig,
        topics_config: TopicsConfig,
        msg_factory: Optional[_MessageFactory] = None,
        on_publish_result: Optional[Callable] = None,
    ) -> None:
        if not isinstance(command_output_config, CommandOutputConfig):
            raise TypeError(
                "ActionPublisher requires a CommandOutputConfig, got "
                f"{type(command_output_config).__name__}"
            )
        if not isinstance(topics_config, TopicsConfig):
            raise TypeError(
                "ActionPublisher requires a TopicsConfig, got "
                f"{type(topics_config).__name__}"
            )

        self._config = command_output_config
        self._topics = topics_config
        self._msg_factory = (
            msg_factory if msg_factory is not None else _default_message_factory()
        )
        self._status_msg_class = _resolve_status_msg_class()

        # Minimal RAM state.
        self._gripper_last_target: dict[str, Optional[float]] = {
            "left": None,
            "right": None,
        }
        self._gripper_last_time: dict[str, Optional[float]] = {
            "left": None,
            "right": None,
        }
        self._last_result: Optional[ActionPublishResult] = None
        self._available = False
        self._on_publish_result = on_publish_result
        self._current_step_id: Optional[int] = None  # set by ControlLoop before publish

        # Create exactly six publishers; no subscription / timer / metrics.
        cmd = topics_config.command
        specs = [
            ("policy_action", self._msg_factory.float32_multi_array, cmd.policy_action),
            ("left_arm", self._msg_factory.pose_stamped, cmd.left_arm_target),
            ("right_arm", self._msg_factory.pose_stamped, cmd.right_arm_target),
            ("left_gripper", self._msg_factory.float64, cmd.left_gripper_target),
            ("right_gripper", self._msg_factory.float64, cmd.right_gripper_target),
            ("status", self._status_msg_class, cmd.status),
        ]
        self._publishers: dict[str, Any] = {}
        for label, msg_cls, topic in specs:
            # rclpy expects a QoSProfile; a depth int is accepted by the
            # dry-run fake node and by callers that adapt the qos arg. Here we
            # pass the configured depth and let a real node adapt it.
            self._publishers[label] = node.create_publisher(
                msg_cls, topic, self._config.qos_depth
            )
        self._available = True

    # -- C17 ROS data write -------------------------------------------------

    def _try_publish(self, label: str, publisher: Any, message: Any) -> None:
        """C17: write one fully-constructed ROS message; raise on failure."""
        try:
            publisher.publish(message)
        except Exception as exc:  # noqa: BLE001 - we re-wrap any IO error
            raise ActionPublishIoError(label) from exc

    # -- C18 / C21 internal RAM state update --------------------------------

    def _update_gripper_cache(self, side: str, target: float, monotonic_s: float) -> None:
        """C18: update one side's gripper cache only after a successful publish."""
        self._gripper_last_target[side] = float(target)
        self._gripper_last_time[side] = float(monotonic_s)

    def _record_last_result(self, result: ActionPublishResult) -> None:
        """C21: replace the last result reference exactly once per B3 call."""
        self._last_result = result

    def _fire_publish_callback(self, request: ActionPublishRequest, result: ActionPublishResult) -> None:
        """Fire the on_publish_result debug callback (best-effort)."""
        try:
            if self._on_publish_result is not None:
                step_id = self._current_step_id
                if step_id is not None:
                    _cmd_values = (
                        list(request.safety_result.action.as_vector().tolist())
                        if request.safety_result.action is not None
                        else []
                    )
                    self._on_publish_result(step_id, result.outcome.value, _cmd_values)
        except Exception:
            pass

    # -- C19 result assembly ------------------------------------------------

    def _topic_for_label(self, label: str) -> str:
        """Resolve a publisher label to its configured public ROS topic."""
        cmd = self._topics.command
        return {
            "policy_action": cmd.policy_action,
            "left_arm": cmd.left_arm_target,
            "right_arm": cmd.right_arm_target,
            "left_gripper": cmd.left_gripper_target,
            "right_gripper": cmd.right_gripper_target,
            "status": cmd.status,
        }[label]

    def _build_publish_result(
        self,
        request: ActionPublishRequest,
        policy_published: bool,
        command_count: int,
        outcome: PublishOutcome,
        reason_code: Optional[str],
        gripper_skipped: tuple[str, ...],
        command_plan_completed: bool,
        status_published: bool,
        *,
        failure_stage: Optional[str] = None,
        failed_topic: Optional[str] = None,
    ) -> ActionPublishResult:
        """C19: assemble the frozen C6 from observed facts (pure computation).

        ``failure_stage`` / ``failed_topic`` (deploy_060) carry the precise
        publish-failure provenance; ``None`` on success paths.
        """
        return ActionPublishResult(
            action_id=request.action_id,
            safety_status=request.safety_result.status,
            command_output_enabled=self._config.command_output_enabled,
            command_permitted=request.command_permit.allowed,
            outcome=outcome,
            policy_action_published=policy_published,
            command_publish_count=command_count,
            gripper_skipped=tuple(gripper_skipped),
            command_plan_completed=command_plan_completed,
            status_published=status_published,
            reason_code=reason_code,
            failure_stage=failure_stage,
            failed_topic=failed_topic,
        )

    # -- C20 status message -------------------------------------------------

    def _build_status_msg(self, result: ActionPublishResult) -> Any:
        """C20: build the status ``String(JSON)`` from the final C6."""
        payload = {
            "action_id": result.action_id,
            "safety_status": result.safety_status.value,
            "command_output_enabled": result.command_output_enabled,
            "command_permitted": result.command_permitted,
            "outcome": result.outcome.value,
            "policy_action_published": result.policy_action_published,
            "command_publish_count": result.command_publish_count,
            "gripper_skipped": list(result.gripper_skipped),
            "command_plan_completed": result.command_plan_completed,
            "reason_code": result.reason_code,
            "failure_stage": result.failure_stage,
            "failed_topic": result.failed_topic,
            "driver_accepted": None,
            "hardware_reached": None,
        }
        return self._status_msg_class(data=json.dumps(payload, sort_keys=True))

    def _publish_status_best_effort(self, result: ActionPublishResult) -> bool:
        """Best-effort C17 write of the status message; never raises."""
        try:
            msg = self._build_status_msg(result)
            self._try_publish("status", self._publishers["status"], msg)
            return True
        except Exception:  # noqa: BLE001 - status is best-effort
            return False

    # -- finalize helper ----------------------------------------------------

    def _finalize(
        self,
        request: ActionPublishRequest,
        *,
        policy_published: bool,
        command_count: int,
        outcome: PublishOutcome,
        reason_code: Optional[str],
        gripper_skipped: tuple[str, ...],
        command_plan_completed: bool,
        failure_stage: Optional[str] = None,
        failed_topic: Optional[str] = None,
    ) -> ActionPublishResult:
        """Assemble C6, publish status best-effort, record and return C6 (C21)."""
        base = self._build_publish_result(
            request,
            policy_published,
            command_count,
            outcome,
            reason_code,
            gripper_skipped,
            command_plan_completed,
            status_published=False,
            failure_stage=failure_stage,
            failed_topic=failed_topic,
        )
        status_published = self._publish_status_best_effort(base)
        final = self._build_publish_result(
            request,
            policy_published,
            command_count,
            outcome,
            reason_code,
            gripper_skipped,
            command_plan_completed,
            status_published=status_published,
            failure_stage=failure_stage,
            failed_topic=failed_topic,
        )
        self._record_last_result(final)
        # Fire debug callback on all return paths via _finalize
        self._fire_publish_callback(request, final)
        return final

    # -- B3 orchestration ---------------------------------------------------

    def publish(self, request: ActionPublishRequest) -> ActionPublishResult:
        """B3: the single public business entry (deploy_044).

        Order: B1 -> B2 -> C15 -> C17 policy -> optional commands ->
        C19 -> C20/status -> C21. Command topics are written only when both
        the CLI master switch and the per-tick permit allow it.
        """
        if not self._available:
            raise RuntimeError("ActionPublisher is not available (publisher init failed)")

        # 1. B1 — build the full C4 payload bundle.
        try:
            payloads = build_topic_payloads(request.safety_result, self._config)
        except ActionPublishContractError:
            # Safety REJECTED / contract violation: never build messages.
            return self._finalize(
                request,
                policy_published=False,
                command_count=0,
                outcome=PublishOutcome.REJECTED,
                reason_code="SAFETY_REJECTED",
                gripper_skipped=(),
                command_plan_completed=False,
                failure_stage="safety",
                failed_topic=None,
            )
        except Exception:
            return self._finalize(
                request,
                policy_published=False,
                command_count=0,
                outcome=PublishOutcome.FAILED,
                reason_code="PAYLOAD_BUILD_ERROR",
                gripper_skipped=(),
                command_plan_completed=False,
                failure_stage="command_build",
                failed_topic=None,
            )

        # 2. B2 — pack five ROS candidate messages.
        try:
            bundle = build_ros_messages(payloads, request.ros_time_s, self._msg_factory)
        except Exception:
            return self._finalize(
                request,
                policy_published=False,
                command_count=0,
                outcome=PublishOutcome.FAILED,
                reason_code="MESSAGE_BUILD_ERROR",
                gripper_skipped=(),
                command_plan_completed=False,
                failure_stage="command_build",
                failed_topic=None,
            )

        # 3. C15 — gate decision.
        allow_command, cmd_reason = _decide_command_publish(
            self._config.command_output_enabled, request.command_permit
        )

        # 4. C17 — publish policy; failure stops all command writes.
        try:
            self._try_publish(
                "policy_action", self._publishers["policy_action"], bundle.policy_action_msg
            )
            policy_published = True
        except ActionPublishIoError:
            return self._finalize(
                request,
                policy_published=False,
                command_count=0,
                outcome=PublishOutcome.FAILED,
                reason_code="POLICY_PUBLISH_IO_ERROR",
                gripper_skipped=(),
                command_plan_completed=False,
                failure_stage="policy_publish",
                failed_topic=self._topic_for_label("policy_action"),
            )

        # 5. optional command path.
        if not allow_command:
            outcome = (
                PublishOutcome.OBSERVED
                if not self._config.command_output_enabled
                else PublishOutcome.BLOCKED
            )
            return self._finalize(
                request,
                policy_published=policy_published,
                command_count=0,
                outcome=outcome,
                reason_code=cmd_reason,
                gripper_skipped=(),
                command_plan_completed=True,
            )

        # Build the command target list (arms always; grippers per C16).
        targets: list[tuple[str, Any, Optional[str], Optional[float]]] = [
            ("left_arm", bundle.left_arm_msg, None, None),
            ("right_arm", bundle.right_arm_msg, None, None),
        ]
        skipped: list[str] = []
        for side in ("left", "right"):
            target_val = getattr(payloads, f"{side}_gripper")
            do_publish, _ = _decide_gripper_publish(
                side,
                target_val,
                self._gripper_last_target[side],
                self._gripper_last_time[side],
                request.monotonic_s,
                self._config.gripper_deadband,
                self._config.gripper_min_publish_interval_s,
            )
            if do_publish:
                msg = getattr(bundle, f"{side}_gripper_msg")
                targets.append((f"{side}_gripper", msg, side, target_val))
            else:
                skipped.append(side)

        command_count = 0
        plan_broken = False
        failed_label: Optional[str] = None
        for label, msg, side, target_val in targets:
            try:
                self._try_publish(label, self._publishers[label], msg)
                command_count += 1
                if side is not None:
                    self._update_gripper_cache(side, target_val, request.monotonic_s)
            except ActionPublishIoError as eio:
                # Stop the remaining command path; record the exact failing
                # topic so L2-06 can attribute the failure.
                plan_broken = True
                failed_label = eio.label
                break

        plan_completed = (
            (not plan_broken)
            and (len(targets) > 0)
            and (command_count == len(targets))
        )
        if plan_completed:
            outcome = PublishOutcome.PUBLISHED
        elif command_count > 0:
            outcome = PublishOutcome.PARTIAL
        else:
            outcome = PublishOutcome.FAILED

        failure_stage: Optional[str] = None
        failed_topic: Optional[str] = None
        if plan_broken:
            failure_stage = "command_publish"
            failed_topic = (
                self._topic_for_label(failed_label) if failed_label is not None else None
            )
            reason_code = "COMMAND_PUBLISH_IO_ERROR"
        else:
            reason_code = None

        result = self._finalize(
            request,
            policy_published=policy_published,
            command_count=command_count,
            outcome=outcome,
            reason_code=reason_code,
            gripper_skipped=tuple(skipped),
            command_plan_completed=plan_completed,
            failure_stage=failure_stage,
            failed_topic=failed_topic,
        )

        return result


__all__ = [
    "build_ros_messages",
    "_build_policy_msg",
    "_build_arm_msg",
    "_build_gripper_msg",
    "_RosMessageBundle",
    "_MessageFactory",
    "_ROS_AVAILABLE",
    "ActionPublisher",
    "ActionPublishIoError",
    "_decide_command_publish",
    "_decide_gripper_publish",
]
