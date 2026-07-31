"""ROS adapter for the fail-closed real-command permit provider."""

from __future__ import annotations

from typing import Any, Callable

from model_deploy.act.config.schema import DeployConfig
from model_deploy.act.runtime.command_permit_provider import CommandPermitProvider
from model_deploy.act.types.action_publish import CommandPermit


PERMIT_TOPIC = "/act/command/permit"
RM65_HEALTH_TOPIC = "/hardware/rm65/health"
GRIPPER_HEALTH_TOPIC = "/hardware/gripper/health"
RM65_ESTOP_SERVICE = "/hardware/rm65/emergency_stop"
GRIPPER_ESTOP_SERVICE = "/hardware/gripper/emergency_stop"
PERMIT_HEARTBEAT_HZ = 20.0
STARTUP_DEPENDENCY_TIMEOUT_S = 5.0


class RosCommandPermitProvider:
    """Own ROS health inputs, permit heartbeat output and E-stop clients."""

    def __init__(
        self,
        *,
        node: Any,
        config: DeployConfig,
        monotonic_clock: Callable[[], float],
    ) -> None:
        from act_interfaces.msg import (
            CommandPermit as CommandPermitMsg,
            GripperHealth,
            HardwareHealth,
        )
        from std_srvs.srv import SetBool

        self._node = node
        self._config = config
        self._clock = monotonic_clock
        self._msg_type = CommandPermitMsg
        self._set_bool_type = SetBool
        self._timer = None
        self._estop_requested = False
        self._provider = CommandPermitProvider(
            mode=config.runtime.mode,
            command_output_enabled=config.command_output.command_output_enabled,
            monotonic_clock=monotonic_clock,
        )
        self._publisher = node.create_publisher(
            CommandPermitMsg, PERMIT_TOPIC, config.command_output.qos_depth
        )
        self._rm65_subscription = node.create_subscription(
            HardwareHealth,
            RM65_HEALTH_TOPIC,
            self._on_rm65_health,
            config.command_output.qos_depth,
        )
        self._gripper_subscription = node.create_subscription(
            GripperHealth,
            GRIPPER_HEALTH_TOPIC,
            self._on_gripper_health,
            config.command_output.qos_depth,
        )
        self._rm65_estop = node.create_client(SetBool, RM65_ESTOP_SERVICE)
        self._gripper_estop = node.create_client(SetBool, GRIPPER_ESTOP_SERVICE)

    def start(self) -> None:
        if self._timer is None:
            self._timer = self._node.create_timer(
                1.0 / PERMIT_HEARTBEAT_HZ, self._publish_heartbeat
            )

    def run_startup_preflight(
        self, timeout_s: float = STARTUP_DEPENDENCY_TIMEOUT_S
    ) -> None:
        """Wait boundedly for the complete real-run driver contract.

        A real-run node does not finish construction until both health streams,
        both permit subscribers, all four command subscribers and both E-stop
        services are discoverable.  Dry-run never waits on hardware.
        """
        if self._config.runtime.mode != "real-run":
            return
        if timeout_s <= 0.0:
            raise ValueError("startup dependency timeout must be positive")

        import rclpy

        deadline = self._clock() + float(timeout_s)
        last_reason = "STARTUP_DEPENDENCIES_NOT_READY"
        while self._clock() < deadline:
            self._update_topology()
            ready, last_reason = self._provider.dependency_status()
            services_ready = (
                self._rm65_estop.service_is_ready()
                and self._gripper_estop.service_is_ready()
            )
            if ready and services_ready:
                return
            if ready and not services_ready:
                last_reason = "EMERGENCY_STOP_SERVICE_MISSING"
            remaining = max(0.0, deadline - self._clock())
            rclpy.spin_once(self._node, timeout_sec=min(0.05, remaining))

        self._provider.latch_denial("STARTUP_DEPENDENCY_TIMEOUT")
        self._publish_heartbeat()
        raise RuntimeError(
            "real-run startup preflight failed: "
            f"{last_reason} after {timeout_s:.1f}s"
        )

    def resolve(self) -> CommandPermit:
        return self._provider.command_permit()

    def update_runtime_ready(self, ready: bool, reason_code: str) -> None:
        self._provider.update_runtime_ready(ready, reason_code)

    def latch_fault(self, reason_code: str, *, emergency_stop: bool = True) -> None:
        self._provider.latch_denial(reason_code)
        self._publish_heartbeat()
        if emergency_stop and self._config.runtime.mode == "real-run":
            self._request_emergency_stop()

    def shutdown(self) -> None:
        self._provider.latch_denial("SHUTDOWN")
        self._publish_heartbeat()
        if self._config.runtime.mode == "real-run":
            self._request_emergency_stop()
        if self._timer is not None:
            self._timer.cancel()
            self._timer = None

    @property
    def state(self) -> str:
        return self._provider.state.value

    @property
    def reason_code(self) -> str:
        return self._provider.reason_code

    @property
    def has_been_allowed(self) -> bool:
        return self._provider.has_been_allowed

    def _on_rm65_health(self, msg: Any) -> None:
        healthy = bool(
            msg.left_connected
            and msg.right_connected
            and not msg.left_estop_active
            and not msg.right_estop_active
            and int(msg.left_sdk_code) == 0
            and int(msg.right_sdk_code) == 0
            and int(msg.left_controller_err) == 0
            and int(msg.right_controller_err) == 0
        )
        reason = "RM65_HEALTH_OK" if healthy else "RM65_HEALTH_FAULT"
        self._provider.update_rm65_health(healthy, reason)
        if not healthy and self._provider.has_been_allowed:
            self.latch_fault(reason)

    def _on_gripper_health(self, msg: Any) -> None:
        healthy = bool(
            msg.left_connected
            and msg.right_connected
            and not msg.estop_active
            and int(msg.status) == 0
        )
        reason = "GRIPPER_HEALTH_OK" if healthy else "GRIPPER_HEALTH_FAULT"
        self._provider.update_gripper_health(healthy, reason)
        if not healthy and self._provider.has_been_allowed:
            self.latch_fault(reason)

    def _publish_heartbeat(self) -> None:
        self._update_topology()
        permit = self._provider.heartbeat_permit()
        if not permit.allowed and self._provider.has_been_allowed:
            self._provider.latch_denial(
                permit.reason_code or "PERMIT_REVOKED"
            )
            permit = self._provider.heartbeat_permit()
            self._request_emergency_stop()
        msg = self._msg_type()
        msg.header.stamp = self._node.get_clock().now().to_msg()
        msg.allowed = permit.allowed
        msg.reason_code = permit.reason_code or ""
        try:
            self._publisher.publish(msg)
        except Exception:
            self._provider.latch_denial("PERMIT_PUBLISH_ERROR")
            return
        self._provider.record_heartbeat_published(permit)

    def _update_topology(self) -> None:
        command_topics = self._config.topics.command
        missing = []
        if self._publisher.get_subscription_count() < 2:
            missing.append(PERMIT_TOPIC)
        for topic in (
            command_topics.left_arm_target,
            command_topics.right_arm_target,
            command_topics.left_gripper_target,
            command_topics.right_gripper_target,
        ):
            if self._node.count_subscribers(topic) < 1:
                missing.append(topic)
        self._provider.update_topology(
            not missing,
            "TOPOLOGY_READY" if not missing else "TOPOLOGY_NOT_READY",
        )

    def _request_emergency_stop(self) -> None:
        if self._estop_requested:
            return
        self._estop_requested = True
        for client in (self._rm65_estop, self._gripper_estop):
            try:
                if client.service_is_ready():
                    request = self._set_bool_type.Request()
                    request.data = True
                    client.call_async(request)
            except Exception:
                # Permit has already been revoked; service calls are best-effort.
                pass


__all__ = ["RosCommandPermitProvider"]
