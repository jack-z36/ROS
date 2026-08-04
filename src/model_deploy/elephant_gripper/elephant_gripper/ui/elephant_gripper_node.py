"""ROS 2 node for the dual Elephant myGripper-F100 grippers.

This is the only layer that imports rclpy and ``act_interfaces`` messages. ROS
message <-> RAM type conversion happens here; all serial I/O is delegated to
the supervisor's worker threads. Callbacks are O(1): they validate and write
the latest-command slot or read snapshots, never blocking on serial.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Optional

import rclpy
from ament_index_python.packages import PackageNotFoundError, get_package_share_directory
from rclpy.callback_groups import MutuallyExclusiveCallbackGroup, ReentrantCallbackGroup
from rclpy.executors import ExternalShutdownException, MultiThreadedExecutor
from rclpy.node import Node
from std_msgs.msg import Float64
from std_srvs.srv import SetBool

from act_interfaces.msg import CommandPermit as CommandPermitMsg
from act_interfaces.msg import GripperHealth as GripperHealthMsg

from ..config.schema import ConfigError
from ..repo.config_loader import DEFAULT_NODE_NAME, load_config
from ..runtime.fake_serial import make_fake_serial_factory
from ..runtime.gripper_supervisor import GripperSupervisor
from ..types.command_permit import CommandPermit
from ..types.gripper_types import GripperCommand, GripperSide

_PACKAGE = "elephant_gripper"
_CONFIG_FILE = "elephant_gripper.yaml"


class ElephantGripperNode(Node):
    """ROS adapter around :class:`GripperSupervisor`."""

    def __init__(self) -> None:
        super().__init__(DEFAULT_NODE_NAME)
        self.declare_parameter("config_file", "")

        config_file = self.get_parameter("config_file").value
        if not config_file:
            config_file = self._default_config_file()

        try:
            self._config = load_config(str(config_file), node_name=self.get_name())
        except ConfigError as exc:
            self.get_logger().fatal(f"Failed to load elephant_gripper config: {exc}")
            raise

        serial_factory = None
        if self._config.use_fake_serial:
            self.get_logger().warn("use_fake_serial=True: running without real hardware")
            serial_factory = make_fake_serial_factory()

        self._supervisor = GripperSupervisor(
            self._config,
            logger=self.get_logger(),
            serial_factory=serial_factory,
        )

        # Callback groups: commands/permit are mutually exclusive (O(1) slot
        # writes); estop service is reentrant so it can preempt at any time;
        # publish/health timers each run in their own group reading snapshots.
        self._cmd_group = MutuallyExclusiveCallbackGroup()
        self._estop_group = ReentrantCallbackGroup()
        self._publish_group = MutuallyExclusiveCallbackGroup()
        self._health_group = MutuallyExclusiveCallbackGroup()

        # Publishers.
        self._left_state_pub = self.create_publisher(Float64, "/gripper/left_state", 10)
        self._right_state_pub = self.create_publisher(Float64, "/gripper/right_state", 10)
        self._health_pub = self.create_publisher(
            GripperHealthMsg, "/hardware/gripper/health", 10
        )

        # Subscribers.
        self.create_subscription(
            Float64,
            "/act/command/gripper/left_target",
            lambda msg: self._on_target(GripperSide.LEFT, msg),
            10,
            callback_group=self._cmd_group,
        )
        self.create_subscription(
            Float64,
            "/act/command/gripper/right_target",
            lambda msg: self._on_target(GripperSide.RIGHT, msg),
            10,
            callback_group=self._cmd_group,
        )
        self.create_subscription(
            CommandPermitMsg,
            "/act/command/permit",
            self._on_permit,
            10,
            callback_group=self._cmd_group,
        )

        # Emergency-stop service.
        self.create_service(
            SetBool,
            "/hardware/gripper/emergency_stop",
            self._on_emergency_stop,
            callback_group=self._estop_group,
        )

        # Timers.
        self._publish_timer = self.create_timer(
            1.0 / self._config.publish_hz,
            self._publish_states,
            callback_group=self._publish_group,
        )
        self._health_timer = self.create_timer(
            1.0 / self._config.health_publish_hz,
            self._publish_health,
            callback_group=self._health_group,
        )

        self._supervisor.start()
        self.get_logger().info(
            f"elephant_gripper_node started: config_file={config_file}, "
            f"left_port={self._config.left.port}, right_port={self._config.right.port}, "
            f"publish_hz={self._config.publish_hz}, use_fake_serial={self._config.use_fake_serial}"
        )

    # -- shutdown -------------------------------------------------------------
    def destroy_node(self) -> bool:
        self.shutdown_driver()
        return super().destroy_node()

    def shutdown_driver(self) -> None:
        try:
            self._supervisor.shutdown()
        except Exception as exc:  # noqa: BLE001
            self.get_logger().error(f"supervisor shutdown error: {exc}")

    # -- callbacks ------------------------------------------------------------
    def _on_target(self, side: GripperSide, msg: Float64) -> None:
        try:
            command = GripperCommand(side=side, target_width=float(msg.data))
        except ValueError as exc:
            self.get_logger().warn(f"ignoring invalid {side.value} target {msg.data}: {exc}")
            return
        self._supervisor.route_command(command)

    def _on_permit(self, msg: CommandPermitMsg) -> None:
        permit = CommandPermit(
            allowed=bool(msg.allowed),
            reason_code=msg.reason_code or None,
            stamp_monotonic_s=time.monotonic(),
        )
        self._supervisor.apply_permit(permit)

    def _on_emergency_stop(
        self, request: SetBool.Request, response: SetBool.Response
    ) -> SetBool.Response:
        if request.data:
            self._supervisor.estop_all()
            response.success = True
            response.message = "emergency stop engaged"
            self.get_logger().warn("emergency stop ENGAGED via service")
        else:
            self._supervisor.clear_estop()
            response.success = True
            response.message = "emergency stop released"
            self.get_logger().info("emergency stop released via service")
        return response

    # -- timers ---------------------------------------------------------------
    def _publish_states(self) -> None:
        left = self._supervisor.latest_state(GripperSide.LEFT)
        right = self._supervisor.latest_state(GripperSide.RIGHT)
        if left.valid:
            self._left_state_pub.publish(Float64(data=float(left.width)))
        if right.valid:
            self._right_state_pub.publish(Float64(data=float(right.width)))

    def _publish_health(self) -> None:
        health = self._supervisor.aggregate_health()
        msg = GripperHealthMsg()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.hardware_id = health.hardware_id
        msg.status = int(health.status)
        msg.left_connected = health.left.connected
        msg.right_connected = health.right.connected
        msg.left_status = int(health.left.status)
        msg.right_status = int(health.right.status)
        msg.estop_active = health.estop_active
        msg.detail = health.detail
        self._health_pub.publish(msg)

    # -- helpers --------------------------------------------------------------
    def _default_config_file(self) -> str:
        try:
            package_share = Path(get_package_share_directory(_PACKAGE))
            return str(package_share / "config" / _CONFIG_FILE)
        except PackageNotFoundError:
            source_config = Path(__file__).resolve().parents[2] / "config" / _CONFIG_FILE
            return str(source_config)


def main(args: Optional[list] = None) -> None:
    rclpy.init(args=args)
    node: Optional[ElephantGripperNode] = None
    executor: Optional[MultiThreadedExecutor] = None
    try:
        node = ElephantGripperNode()
        executor = MultiThreadedExecutor()
        executor.add_node(node)
        executor.spin()
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        if executor is not None:
            executor.shutdown()
        if node is not None:
            try:
                node.destroy_node()
            except (KeyboardInterrupt, ExternalShutdownException):
                pass
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
