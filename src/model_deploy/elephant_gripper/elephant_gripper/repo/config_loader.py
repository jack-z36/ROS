"""Load the node configuration from a ROS-style YAML file into RAM.

This is the only place in the driver that touches the filesystem for
configuration. It reads ``<node_name>.ros__parameters`` and produces a
validated :class:`NodeConfig`. No serial and no ROS runtime imports here.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Mapping

import yaml

from ..config.schema import (
    ConfigError,
    GripperLinkConfig,
    NodeConfig,
    WidthAngleCalibration,
)
from ..types.gripper_types import GripperSide

DEFAULT_NODE_NAME = "elephant_gripper_node"


def load_config(config_file: str, node_name: str = DEFAULT_NODE_NAME) -> NodeConfig:
    """Load and validate node config from a ROS-style YAML file."""

    path = Path(os.path.expandvars(config_file)).expanduser()
    if not path.is_file():
        raise ConfigError(f"config_file does not exist: {path}")

    with path.open("r", encoding="utf-8") as stream:
        raw = yaml.safe_load(stream) or {}

    if not isinstance(raw, Mapping):
        raise ConfigError("top-level YAML content must be a mapping")

    params = _extract_ros_params(raw, node_name)
    return parse_node_config(params)


def _extract_ros_params(raw: Mapping[str, Any], node_name: str) -> Mapping[str, Any]:
    node_block = raw.get(node_name)
    if isinstance(node_block, Mapping) and isinstance(node_block.get("ros__parameters"), Mapping):
        return node_block["ros__parameters"]
    if isinstance(raw.get("ros__parameters"), Mapping):
        return raw["ros__parameters"]
    return raw


def parse_node_config(params: Mapping[str, Any]) -> NodeConfig:
    """Build a :class:`NodeConfig` from an already-extracted params mapping."""

    if not isinstance(params, Mapping):
        raise ConfigError("ros__parameters must be a mapping")

    left_port = _required_str(params, "left_port")
    right_port = _required_str(params, "right_port")

    baudrate = _as_int(params.get("baudrate", 115200), "baudrate")
    gripper_id = _as_int(params.get("gripper_id", 0x0E), "gripper_id")
    serial_timeout_s = _as_float(params.get("serial_timeout_s", 0.08), "serial_timeout_s")
    enable_wait_s = _as_float(params.get("enable_wait_s", 0.1), "enable_wait_s")
    set_angle_wait_s = _as_float(params.get("set_angle_wait_s", 0.1), "set_angle_wait_s")
    poll_hz = _as_float(params.get("poll_hz", 30.0), "poll_hz")
    backoff_min = _as_float(
        params.get("reconnect_backoff_min_s", 0.5), "reconnect_backoff_min_s"
    )
    backoff_max = _as_float(
        params.get("reconnect_backoff_max_s", 5.0), "reconnect_backoff_max_s"
    )
    command_min = _as_float(params.get("command_min", 0.0), "command_min")
    command_max = _as_float(params.get("command_max", 1.0), "command_max")
    calibration = _parse_calibration(params.get("calibration"))

    def _link(side: GripperSide, port: str) -> GripperLinkConfig:
        return GripperLinkConfig(
            side=side,
            port=port,
            baudrate=baudrate,
            gripper_id=gripper_id,
            serial_timeout_s=serial_timeout_s,
            enable_wait_s=enable_wait_s,
            set_angle_wait_s=set_angle_wait_s,
            poll_hz=poll_hz,
            reconnect_backoff_min_s=backoff_min,
            reconnect_backoff_max_s=backoff_max,
            command_min=command_min,
            command_max=command_max,
            calibration=calibration,
        )

    return NodeConfig(
        left=_link(GripperSide.LEFT, left_port),
        right=_link(GripperSide.RIGHT, right_port),
        publish_hz=_as_float(params.get("publish_hz", 50.0), "publish_hz"),
        health_publish_hz=_as_float(params.get("health_publish_hz", 5.0), "health_publish_hz"),
        permit_timeout_s=_as_float(params.get("permit_timeout_s", 0.5), "permit_timeout_s"),
        command_timeout_s=_as_float(params.get("command_timeout_s", 0.5), "command_timeout_s"),
        hardware_id=str(params.get("hardware_id", "elephant_gripper")).strip(),
        estop_on_startup=_as_bool(params.get("estop_on_startup", False), "estop_on_startup"),
        use_fake_serial=_as_bool(params.get("use_fake_serial", False), "use_fake_serial"),
    )


def _parse_calibration(raw: Any) -> WidthAngleCalibration:
    if raw is None:
        return WidthAngleCalibration()
    if not isinstance(raw, Mapping):
        raise ConfigError("calibration must be a mapping")
    return WidthAngleCalibration(
        angle_closed=_as_int(raw.get("angle_closed", 0), "calibration.angle_closed"),
        angle_open=_as_int(raw.get("angle_open", 100), "calibration.angle_open"),
    )


def _as_int(value: Any, name: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ConfigError(f"{name} must be an integer, got {value!r}") from exc


def _as_float(value: Any, name: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ConfigError(f"{name} must be a number, got {value!r}") from exc


def _as_bool(value: Any, name: str) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in ("true", "1", "yes"):
            return True
        if lowered in ("false", "0", "no"):
            return False
    raise ConfigError(f"{name} must be a boolean, got {value!r}")


def _required_str(params: Mapping[str, Any], name: str) -> str:
    value = str(params.get(name, "")).strip()
    if not value:
        raise ConfigError(f"{name} is required and must be a non-empty string")
    return value
