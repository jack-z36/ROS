"""ROS 2 node for publishing HWK pressure sensor frames."""

from __future__ import annotations

import struct
import time
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Deque, Dict, Optional, Tuple

import rclpy
from rclpy._rclpy_pybind11 import RCLError
from ament_index_python.packages import PackageNotFoundError, get_package_share_directory
from hwk_pressure_interfaces.msg import PressureFrame
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node

from .config import DriverConfig, IdentityTargetConfig, SensorConfig, load_config
from .protocol import ParsedFrame
from .serial_worker import SerialWorker


SensorKey = Tuple[str, int]


@dataclass
class SensorRuntime:
    serial_name: str
    config: SensorConfig
    publisher: object
    identity_uid: str = ""
    target: Optional[IdentityTargetConfig] = None
    next_poll_time: float = 0.0
    next_package_id: int = 0
    last_rx_time: Optional[float] = None
    last_timeout_warn_time: float = 0.0
    first_rx_logged: bool = False
    recent_package_ids: Deque[int] = field(default_factory=lambda: deque(maxlen=8))


class PressureDriverNode(Node):
    """Manage all configured serial ports and publish pressure frames by sensor."""

    def __init__(self) -> None:
        super().__init__("pressure_driver_node")
        self.declare_parameter("config_file", "")

        config_file = self.get_parameter("config_file").value
        if not config_file:
            config_file = self._default_config_file()

        try:
            self._config = load_config(str(config_file), node_name=self.get_name())
        except Exception as exc:
            self.get_logger().fatal(f"Failed to load pressure driver config: {exc}")
            raise

        self._start_time = time.monotonic()
        self._stopping = False
        self._workers: Dict[str, SerialWorker] = {}
        self._sensors: Dict[SensorKey, SensorRuntime] = {}
        self._publishers_by_uid: Dict[str, object] = {}
        self._bound_identity_uids = set()
        self._timer = None

        self._create_publishers(self._config)
        self._create_workers(self._config)
        if not self._sensors:
            self.shutdown_driver()
            raise RuntimeError(
                "No HWK pressure sensors were bound to publishers. "
                "Check serial devices and HWK_CHIP_UID mappings."
            )
        self._log_startup_summary(str(config_file))

        max_poll_rate = max(runtime.config.poll_rate_hz for runtime in self._sensors.values())
        timer_period = max(0.001, 1.0 / max_poll_rate)
        self._timer = self.create_timer(timer_period, self._poll_timer_callback)

    def destroy_node(self) -> bool:
        self.shutdown_driver()
        return super().destroy_node()

    def shutdown_driver(self) -> None:
        if self._stopping:
            return
        self._stopping = True

        if self._timer is not None:
            self._timer.cancel()
            self._timer = None

        for worker in list(self._workers.values()):
            worker.stop()
        self._workers.clear()

    def _default_config_file(self) -> str:
        try:
            package_share = Path(get_package_share_directory("hwk_pressure_driver"))
            return str(package_share / "config" / "pressure_sensors.yaml")
        except PackageNotFoundError:
            source_config = Path(__file__).resolve().parents[1] / "config" / "pressure_sensors.yaml"
            return str(source_config)

    def _create_publishers(self, config: DriverConfig) -> None:
        if config.identity_targets:
            for uid, target in config.identity_targets.items():
                self._publishers_by_uid[uid] = self.create_publisher(
                    PressureFrame, target.topic, 10
                )
            return

        for serial_cfg in config.serial_ports:
            for sensor_cfg in serial_cfg.sensors:
                key = (serial_cfg.name, sensor_cfg.device_addr)
                publisher = self.create_publisher(PressureFrame, sensor_cfg.topic, 10)
                self._sensors[key] = SensorRuntime(
                    serial_name=serial_cfg.name,
                    config=sensor_cfg,
                    publisher=publisher,
                )

    def _create_workers(self, config: DriverConfig) -> None:
        for serial_cfg in config.serial_ports:
            worker = SerialWorker(
                config=serial_cfg,
                serial_timeout=config.serial_timeout,
                frame_callback=self._handle_frame,
                logger=self.get_logger(),
                identity_query_timeout=config.identity_query_timeout,
                identity_query_package_id=config.identity_query_package_id,
            )
            self._workers[serial_cfg.name] = worker
            if not worker.start():
                continue
            if config.identity_targets:
                self._bind_identity_sensors(serial_cfg.name, serial_cfg.sensors, worker)

    def _bind_identity_sensors(
        self,
        serial_name: str,
        sensor_configs: list[SensorConfig],
        worker: SerialWorker,
    ) -> None:
        for sensor_cfg in sensor_configs:
            uid = worker.identity_by_addr.get(sensor_cfg.device_addr)
            if not uid:
                continue

            target = self._config.identity_targets.get(uid)
            if target is None:
                self.get_logger().error(
                    f"Unknown HWK_CHIP_UID ignored: serial={serial_name}, "
                    f"device_addr={sensor_cfg.device_addr}, HWK_CHIP_UID={uid}; "
                    "add it to hardware_identity_map.yaml before publishing"
                )
                continue
            if uid in self._bound_identity_uids:
                raise RuntimeError(
                    f"Duplicate HWK_CHIP_UID detected across serial ports: {uid}"
                )

            publisher = self._publishers_by_uid[uid]
            key = (serial_name, sensor_cfg.device_addr)
            self._sensors[key] = SensorRuntime(
                serial_name=serial_name,
                config=sensor_cfg,
                publisher=publisher,
                identity_uid=uid,
                target=target,
            )
            self._bound_identity_uids.add(uid)
            self.get_logger().info(
                f"Bound HWK sensor by UID: serial={serial_name}, "
                f"device_addr={sensor_cfg.device_addr}, HWK_CHIP_UID={uid}, "
                f"logical={target.logical_name}, topic={target.topic}"
            )

    def _log_startup_summary(self, config_file: str) -> None:
        sensor_count = sum(len(port.sensors) for port in self._config.serial_ports)
        self.get_logger().info(
            "pressure_driver_node started: "
            f"config_file={config_file}, serial_ports={len(self._config.serial_ports)}, "
            f"sensors={sensor_count}, frame_id_prefix={self._config.frame_id_prefix}, "
            f"default_baudrate={self._config.default_baudrate}, "
            f"default_poll_rate_hz={self._config.default_poll_rate_hz}, "
            f"serial_timeout={self._config.serial_timeout}, "
            f"timeout_warn_sec={self._config.timeout_warn_sec}, "
            f"identity_map_file={self._config.identity_map_file}, "
            f"identity_targets={len(self._config.identity_targets)}"
        )
        for port in self._config.serial_ports:
            sensor_summary = ", ".join(
                f"addr={sensor.device_addr}:rows={sensor.rows}:cols={sensor.cols}:"
                f"poll={sensor.poll_rate_hz}Hz"
                for sensor in port.sensors
            )
            self.get_logger().info(
                f"Configured serial port: name={port.name}, port={port.port}, "
                f"baudrate={port.baudrate}, sensors=[{sensor_summary}]"
            )

    def _poll_timer_callback(self) -> None:
        if self._stopping:
            return

        now = time.monotonic()
        for key, runtime in self._sensors.items():
            if now >= runtime.next_poll_time:
                worker = self._workers.get(runtime.serial_name)
                if worker is not None:
                    package_id = runtime.next_package_id
                    if worker.send_get_data(runtime.config.device_addr, package_id):
                        runtime.recent_package_ids.append(package_id)
                    runtime.next_package_id = (package_id + 1) & 0x3F
                runtime.next_poll_time = now + (1.0 / runtime.config.poll_rate_hz)

            self._check_sensor_timeout(now, key, runtime)

    def _check_sensor_timeout(
        self,
        now: float,
        key: SensorKey,
        runtime: SensorRuntime,
    ) -> None:
        last_rx = runtime.last_rx_time
        reference_time = last_rx if last_rx is not None else self._start_time
        elapsed = now - reference_time
        if elapsed < self._config.timeout_warn_sec:
            return
        if now - runtime.last_timeout_warn_time < self._config.timeout_warn_sec:
            return

        runtime.last_timeout_warn_time = now
        serial_name, _ = key
        if last_rx is None:
            self.get_logger().warn(
                f"Sensor timeout: serial={serial_name}, sensor={runtime.config.label}, "
                f"uid={runtime.identity_uid or 'legacy'}, topic={self._runtime_topic(runtime)}, "
                "no valid ACK received since startup"
            )
        else:
            self.get_logger().warn(
                f"Sensor timeout: serial={serial_name}, sensor={runtime.config.label}, "
                f"uid={runtime.identity_uid or 'legacy'}, topic={self._runtime_topic(runtime)}, "
                f"no valid ACK for {elapsed:.3f}s"
            )

    def _handle_frame(self, serial_name: str, frame: ParsedFrame) -> None:
        if self._stopping:
            return

        key = (serial_name, frame.device_addr)
        runtime = self._sensors.get(key)
        if runtime is None:
            self.get_logger().warn(
                f"Valid ACK for unconfigured sensor ignored: serial={serial_name}, "
                f"device_addr={frame.device_addr}"
            )
            return

        if runtime.recent_package_ids and frame.package_id not in runtime.recent_package_ids:
            self.get_logger().debug(
                f"ACK package_id not in recent requests: serial={serial_name}, "
                f"sensor={runtime.config.label}, ack_package_id={frame.package_id}, "
                f"recent={list(runtime.recent_package_ids)}"
            )

        parsed_payload = self._parse_payload(runtime, frame)
        if parsed_payload is None:
            return

        total_packets, packet_index, rows, cols, data = parsed_payload
        hand = self._runtime_hand(runtime)
        gripper = self._runtime_gripper(runtime)
        msg = PressureFrame()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = self._runtime_frame_id(runtime, hand, gripper)
        msg.hand = hand
        msg.gripper = gripper
        msg.device_addr = frame.device_addr
        msg.package_id = frame.package_id
        msg.total_packets = total_packets
        msg.packet_index = packet_index
        msg.rows = rows
        msg.cols = cols
        msg.data = data
        msg.raw_payload = list(frame.payload)

        try:
            runtime.publisher.publish(msg)
        except RCLError:
            return
        runtime.last_rx_time = time.monotonic()
        if not runtime.first_rx_logged:
            runtime.first_rx_logged = True
            self.get_logger().info(
                f"First valid pressure frame received: serial={serial_name}, "
                f"sensor={runtime.config.label}, uid={runtime.identity_uid or 'legacy'}, "
                f"topic={self._runtime_topic(runtime)}, "
                f"rows={rows}, cols={cols}, samples={len(data)}"
            )

    def _runtime_hand(self, runtime: SensorRuntime) -> str:
        if runtime.target is not None:
            return runtime.target.hand
        return runtime.config.hand

    def _runtime_gripper(self, runtime: SensorRuntime) -> str:
        if runtime.target is not None:
            return runtime.target.gripper
        return runtime.config.gripper

    def _runtime_topic(self, runtime: SensorRuntime) -> str:
        if runtime.target is not None:
            return runtime.target.topic
        return runtime.config.topic

    def _runtime_frame_id(self, runtime: SensorRuntime, hand: str, gripper: str) -> str:
        if runtime.target is not None and runtime.target.frame_id:
            return runtime.target.frame_id
        return f"{self._config.frame_id_prefix}/{hand}/{gripper}"

    def _parse_payload(
        self,
        runtime: SensorRuntime,
        frame: ParsedFrame,
    ) -> Optional[Tuple[int, int, int, int, list]]:
        payload = frame.payload
        if len(payload) < 4:
            self.get_logger().warn(
                f"Payload length too short: serial={runtime.serial_name}, "
                f"sensor={runtime.config.label}, length={len(payload)}; frame ignored"
            )
            return None

        total_packets = payload[0]
        packet_index = payload[1]
        payload_cols = payload[2]
        payload_rows = payload[3]

        rows = payload_rows
        cols = payload_cols
        if payload_rows == 0 or payload_cols == 0:
            rows = runtime.config.rows
            cols = runtime.config.cols
            self.get_logger().warn(
                f"Payload rows/cols invalid, using config dimensions: "
                f"serial={runtime.serial_name}, sensor={runtime.config.label}, "
                f"payload_rows={payload_rows}, payload_cols={payload_cols}, "
                f"config_rows={rows}, config_cols={cols}"
            )

        data_bytes = payload[4:]
        if len(data_bytes) < 2:
            self.get_logger().warn(
                f"Payload contains no uint16 pressure data: serial={runtime.serial_name}, "
                f"sensor={runtime.config.label}, payload_length={len(payload)}; frame ignored"
            )
            return None
        if len(data_bytes) % 2 != 0:
            self.get_logger().warn(
                f"Payload pressure data length is odd: serial={runtime.serial_name}, "
                f"sensor={runtime.config.label}, data_bytes={len(data_bytes)}; trailing byte ignored"
            )

        sample_count = len(data_bytes) // 2
        data = list(struct.unpack_from(f"<{sample_count}H", data_bytes, 0))
        expected_count = rows * cols
        if expected_count != sample_count:
            self.get_logger().warn(
                f"Pressure data length mismatch: serial={runtime.serial_name}, "
                f"sensor={runtime.config.label}, rows={rows}, cols={cols}, "
                f"expected_samples={expected_count}, parsed_samples={sample_count}; "
                "publishing parsed data and preserving raw_payload"
            )

        return total_packets, packet_index, rows, cols, data


def main(args: Optional[list] = None) -> None:
    rclpy.init(args=args)
    node: Optional[PressureDriverNode] = None
    try:
        node = PressureDriverNode()
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        if node is not None:
            try:
                node.shutdown_driver()
                node.destroy_node()
            except (KeyboardInterrupt, ExternalShutdownException):
                pass
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
