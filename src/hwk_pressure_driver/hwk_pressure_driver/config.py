"""Configuration loading and validation for the HWK pressure driver."""

from __future__ import annotations

import os
from glob import glob
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional

import yaml


@dataclass(frozen=True)
class SensorConfig:
    device_addr: int
    rows: int
    cols: int
    poll_rate_hz: float
    hand: str = ""
    gripper: str = ""
    topic: str = ""

    @property
    def label(self) -> str:
        if self.hand and self.gripper:
            return f"{self.hand}/{self.gripper}@addr{self.device_addr}"
        return f"addr{self.device_addr}"


@dataclass(frozen=True)
class IdentityTargetConfig:
    uid: str
    logical_name: str
    hand: str
    gripper: str
    topic: str
    frame_id: str
    required: bool


@dataclass(frozen=True)
class SerialPortConfig:
    name: str
    port: str
    baudrate: int
    sensors: List[SensorConfig]


@dataclass(frozen=True)
class DriverConfig:
    frame_id_prefix: str
    default_baudrate: int
    default_poll_rate_hz: float
    serial_timeout: float
    timeout_warn_sec: float
    identity_map_file: Optional[str]
    strict_identity: bool
    identity_query_timeout: float
    identity_query_package_id: int
    identity_targets: Dict[str, IdentityTargetConfig]
    serial_ports: List[SerialPortConfig]


class ConfigError(ValueError):
    """Raised when the YAML configuration is invalid."""


def load_config(config_file: str, node_name: str = "pressure_driver_node") -> DriverConfig:
    """Load driver config from a ROS-style YAML file."""

    path = Path(os.path.expandvars(config_file)).expanduser()
    if not path.is_file():
        raise ConfigError(f"config_file does not exist: {path}")

    with path.open("r", encoding="utf-8") as stream:
        raw = yaml.safe_load(stream) or {}

    if not isinstance(raw, Mapping):
        raise ConfigError("top-level YAML content must be a mapping")

    params = _extract_ros_params(raw, node_name)
    return _parse_driver_config(params, path.parent)


def _extract_ros_params(raw: Mapping[str, Any], node_name: str) -> Mapping[str, Any]:
    node_block = raw.get(node_name)
    if isinstance(node_block, Mapping) and isinstance(node_block.get("ros__parameters"), Mapping):
        return node_block["ros__parameters"]
    if isinstance(raw.get("ros__parameters"), Mapping):
        return raw["ros__parameters"]
    return raw


def _parse_driver_config(params: Mapping[str, Any], config_dir: Path) -> DriverConfig:
    default_baudrate = _as_int(params.get("default_baudrate", 460800), "default_baudrate")
    default_poll_rate_hz = _as_float(
        params.get("default_poll_rate_hz", 100.0), "default_poll_rate_hz"
    )
    serial_timeout = _as_float(params.get("serial_timeout", 0.01), "serial_timeout")
    timeout_warn_sec = _as_float(params.get("timeout_warn_sec", 1.0), "timeout_warn_sec")
    frame_id_prefix = str(params.get("frame_id_prefix", "pressure_sensor")).strip()
    identity_query_timeout = _as_float(
        params.get("identity_query_timeout", 1.0), "identity_query_timeout"
    )
    identity_query_package_id = _as_int(
        params.get("identity_query_package_id", 29), "identity_query_package_id"
    )
    strict_identity = _as_bool(params.get("strict_identity", True), "strict_identity")

    identity_map_file_raw = str(params.get("identity_map_file", "")).strip()
    identity_map_file: Optional[str] = None
    identity_targets: Dict[str, IdentityTargetConfig] = {}
    if identity_map_file_raw:
        identity_map_file = str(_resolve_path(identity_map_file_raw, config_dir))
        identity_targets = _load_identity_targets(identity_map_file, strict_identity)

    if not frame_id_prefix:
        raise ConfigError("frame_id_prefix must not be empty")
    if default_baudrate <= 0:
        raise ConfigError("default_baudrate must be positive")
    if default_poll_rate_hz <= 0.0:
        raise ConfigError("default_poll_rate_hz must be positive")
    if serial_timeout <= 0.0:
        raise ConfigError("serial_timeout must be positive")
    if timeout_warn_sec <= 0.0:
        raise ConfigError("timeout_warn_sec must be positive")
    if identity_query_timeout <= 0.0:
        raise ConfigError("identity_query_timeout must be positive")
    if not 0 <= identity_query_package_id <= 0x3F:
        raise ConfigError("identity_query_package_id must be in range 0..63")

    serial_ports: List[SerialPortConfig] = []
    used_serial_names = set()
    used_serial_realpaths = set()
    default_sensor = _parse_default_sensor(
        params.get("sensor_defaults") or {},
        default_poll_rate_hz,
        identity_mode=bool(identity_targets),
    )
    discovered_sensors = _parse_identity_scan_sensors(
        params.get("identity_scan_addrs"),
        default_sensor,
        default_poll_rate_hz,
        identity_mode=bool(identity_targets),
    )

    serial_ports_raw = params.get("serial_ports") or []
    if serial_ports_raw and not isinstance(serial_ports_raw, list):
        raise ConfigError("serial_ports must be a list")

    for index, port_raw in enumerate(serial_ports_raw):
        path = f"serial_ports[{index}]"
        port_map = _as_mapping(port_raw, path)
        name = _required_str(port_map, "name", path)
        port = _required_str(port_map, "port", path)
        baudrate = _as_int(port_map.get("baudrate", default_baudrate), f"{path}.baudrate")

        if name in used_serial_names:
            raise ConfigError(f"duplicate serial port name: {name}")
        used_serial_names.add(name)
        if baudrate <= 0:
            raise ConfigError(f"{path}.baudrate must be positive")

        sensors = _parse_sensors(
            port_map.get("sensors"),
            default_sensor,
            default_poll_rate_hz,
            identity_mode=bool(identity_targets),
            path=path,
            port_name=name,
        )

        serial_ports.append(
            SerialPortConfig(name=name, port=port, baudrate=baudrate, sensors=sensors)
        )
        _remember_realpath(port, used_serial_realpaths)

    for index, port in enumerate(_expand_serial_port_globs(params)):
        if _realpath_key(port) in used_serial_realpaths:
            continue
        name = f"discovered_{Path(port).name}_{index}"
        if name in used_serial_names:
            raise ConfigError(f"duplicate serial port name: {name}")
        used_serial_names.add(name)
        used_serial_realpaths.add(_realpath_key(port))
        serial_ports.append(
            SerialPortConfig(
                name=name,
                port=port,
                baudrate=default_baudrate,
                sensors=discovered_sensors,
            )
        )

    if not serial_ports:
        raise ConfigError("no serial ports configured or discovered")

    return DriverConfig(
        frame_id_prefix=frame_id_prefix,
        default_baudrate=default_baudrate,
        default_poll_rate_hz=default_poll_rate_hz,
        serial_timeout=serial_timeout,
        timeout_warn_sec=timeout_warn_sec,
        identity_map_file=identity_map_file,
        strict_identity=strict_identity,
        identity_query_timeout=identity_query_timeout,
        identity_query_package_id=identity_query_package_id,
        identity_targets=identity_targets,
        serial_ports=serial_ports,
    )


def _parse_default_sensor(
    raw: Any,
    default_poll_rate_hz: float,
    identity_mode: bool,
) -> SensorConfig:
    sensor_map = _as_mapping(raw, "sensor_defaults") if raw else {}
    if not sensor_map:
        sensor_map = {"device_addr": 6, "rows": 6, "cols": 15}
    return _parse_sensor(sensor_map, "sensor_defaults", default_poll_rate_hz, identity_mode)


def _parse_sensors(
    sensors_raw: Any,
    default_sensor: SensorConfig,
    default_poll_rate_hz: float,
    identity_mode: bool,
    path: str,
    port_name: str,
) -> List[SensorConfig]:
    if sensors_raw is None:
        return [default_sensor]
    if not isinstance(sensors_raw, list) or not sensors_raw:
        raise ConfigError(f"{path}.sensors must be a non-empty list when configured")

    sensors: List[SensorConfig] = []
    used_addrs = set()
    for sensor_index, sensor_raw in enumerate(sensors_raw):
        sensor_path = f"{path}.sensors[{sensor_index}]"
        sensor = _parse_sensor(
            _as_mapping(sensor_raw, sensor_path),
            sensor_path,
            default_poll_rate_hz,
            identity_mode,
        )
        if sensor.device_addr in used_addrs:
            raise ConfigError(
                f"{sensor_path}.device_addr {sensor.device_addr} is duplicated on "
                f"serial port {port_name}"
            )
        used_addrs.add(sensor.device_addr)
        sensors.append(sensor)
    return sensors


def _parse_identity_scan_sensors(
    raw: Any,
    default_sensor: SensorConfig,
    default_poll_rate_hz: float,
    identity_mode: bool,
) -> List[SensorConfig]:
    if raw in (None, "") or not identity_mode:
        return [default_sensor]
    if not isinstance(raw, list) or not raw:
        raise ConfigError("identity_scan_addrs must be a non-empty list when configured")

    sensors: List[SensorConfig] = []
    used_addrs = set()
    for index, item in enumerate(raw):
        device_addr = _as_int(item, f"identity_scan_addrs[{index}]")
        if not 0 <= device_addr <= 0x0F:
            raise ConfigError(f"identity_scan_addrs[{index}] must be in range 0..15")
        if device_addr in used_addrs:
            raise ConfigError(f"identity_scan_addrs[{index}] duplicates device_addr {device_addr}")
        used_addrs.add(device_addr)
        sensors.append(
            SensorConfig(
                device_addr=device_addr,
                rows=default_sensor.rows,
                cols=default_sensor.cols,
                poll_rate_hz=default_poll_rate_hz,
            )
        )
    return sensors


def _parse_sensor(
    sensor_map: Mapping[str, Any],
    path: str,
    default_poll_rate_hz: float,
    identity_mode: bool,
) -> SensorConfig:
    device_addr = _as_int(_required(sensor_map, "device_addr", path), f"{path}.device_addr")
    if not 0 <= device_addr <= 0x0F:
        raise ConfigError(f"{path}.device_addr must be in range 0..15")

    rows = _as_int(_required(sensor_map, "rows", path), f"{path}.rows")
    cols = _as_int(_required(sensor_map, "cols", path), f"{path}.cols")
    poll_rate_hz = _as_float(
        sensor_map.get("poll_rate_hz", default_poll_rate_hz),
        f"{path}.poll_rate_hz",
    )
    if not 1 <= rows <= 0xFF:
        raise ConfigError(f"{path}.rows must be in range 1..255")
    if not 1 <= cols <= 0xFF:
        raise ConfigError(f"{path}.cols must be in range 1..255")
    if poll_rate_hz <= 0.0:
        raise ConfigError(f"{path}.poll_rate_hz must be positive")

    if identity_mode:
        hand = str(sensor_map.get("hand", "")).strip()
        gripper = str(sensor_map.get("gripper", "")).strip()
        topic = str(sensor_map.get("topic", "")).strip()
    else:
        hand = _required_str(sensor_map, "hand", path)
        gripper = _required_str(sensor_map, "gripper", path)
        topic = _required_str(sensor_map, "topic", path)

    return SensorConfig(
        device_addr=device_addr,
        rows=rows,
        cols=cols,
        poll_rate_hz=poll_rate_hz,
        hand=hand,
        gripper=gripper,
        topic=topic,
    )


def _expand_serial_port_globs(params: Mapping[str, Any]) -> List[str]:
    patterns = params.get("serial_port_globs") or params.get("candidate_serial_ports") or []
    if isinstance(patterns, str):
        patterns = [patterns]
    if not isinstance(patterns, list):
        raise ConfigError("serial_port_globs must be a list")

    ports: List[str] = []
    for index, pattern_raw in enumerate(patterns):
        pattern = str(pattern_raw).strip()
        if not pattern:
            raise ConfigError(f"serial_port_globs[{index}] must not be empty")
        ports.extend(glob(os.path.expandvars(os.path.expanduser(pattern))))
    return sorted(set(ports))


def _load_identity_targets(
    identity_map_file: str,
    strict_identity: bool,
) -> Dict[str, IdentityTargetConfig]:
    path = Path(identity_map_file)
    if not path.is_file():
        raise ConfigError(f"identity_map_file does not exist: {path}")

    with path.open("r", encoding="utf-8") as stream:
        raw = yaml.safe_load(stream) or {}
    pressure = raw.get("pressure") or {}
    if not isinstance(pressure, Mapping):
        raise ConfigError("identity_map_file pressure section must be a mapping")

    targets: Dict[str, IdentityTargetConfig] = {}
    used_topics = set()
    for logical_name, entry_raw in pressure.items():
        if not isinstance(entry_raw, Mapping):
            raise ConfigError(f"pressure.{logical_name} must be a mapping")
        match = entry_raw.get("match") or {}
        target = entry_raw.get("target") or {}
        if not isinstance(match, Mapping):
            raise ConfigError(f"pressure.{logical_name}.match must be a mapping")
        if not isinstance(target, Mapping):
            raise ConfigError(f"pressure.{logical_name}.target must be a mapping")

        uid = str(match.get("HWK_CHIP_UID", "")).strip()
        if not uid:
            continue

        topic = str(target.get("topic", "")).strip()
        hand = str(target.get("hand", "")).strip()
        gripper = str(target.get("gripper", "")).strip()
        if not topic:
            raise ConfigError(f"pressure.{logical_name}.target.topic is required for {uid}")
        if not hand or not gripper:
            inferred_hand, inferred_gripper = _infer_hand_gripper_from_topic(topic)
            hand = hand or inferred_hand
            gripper = gripper or inferred_gripper
        if not hand or not gripper:
            raise ConfigError(
                f"pressure.{logical_name}.target.hand and target.gripper are required for {uid}"
            )
        if uid in targets:
            raise ConfigError(f"duplicate HWK_CHIP_UID in identity map: {uid}")
        if topic in used_topics:
            raise ConfigError(f"duplicate pressure topic in identity map: {topic}")
        used_topics.add(topic)

        targets[uid] = IdentityTargetConfig(
            uid=uid,
            logical_name=str(logical_name),
            hand=hand,
            gripper=gripper,
            topic=topic,
            frame_id=str(target.get("frame_id", "")).strip(),
            required=_as_bool(entry_raw.get("required", True), f"pressure.{logical_name}.required"),
        )

    if strict_identity and not targets:
        raise ConfigError("identity_map_file has no configured pressure HWK_CHIP_UID targets")
    return targets


def _infer_hand_gripper_from_topic(topic: str) -> tuple[str, str]:
    parts = topic.strip("/").split("/")
    if len(parts) >= 3 and parts[-3] == "pressure":
        return parts[-2], parts[-1]
    return "", ""


def _resolve_path(value: str, base_dir: Path) -> Path:
    path = Path(os.path.expandvars(value)).expanduser()
    if path.is_absolute():
        return path
    return base_dir / path


def _realpath_key(port: str) -> str:
    try:
        return str(Path(port).resolve())
    except OSError:
        return port


def _remember_realpath(port: str, used_realpaths: set) -> None:
    used_realpaths.add(_realpath_key(port))


def _as_mapping(value: Any, path: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ConfigError(f"{path} must be a mapping")
    return value


def _required(mapping: Mapping[str, Any], key: str, path: str) -> Any:
    if key not in mapping:
        raise ConfigError(f"{path}.{key} is required")
    return mapping[key]


def _required_str(mapping: Mapping[str, Any], key: str, path: str) -> str:
    value = str(_required(mapping, key, path)).strip()
    if not value:
        raise ConfigError(f"{path}.{key} must not be empty")
    return value


def _as_int(value: Any, path: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ConfigError(f"{path} must be an integer") from exc


def _as_float(value: Any, path: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ConfigError(f"{path} must be a number") from exc


def _as_bool(value: Any, path: str) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in ("1", "true", "yes", "on"):
            return True
        if lowered in ("0", "false", "no", "off"):
            return False
    if isinstance(value, int):
        return bool(value)
    raise ConfigError(f"{path} must be a boolean")
