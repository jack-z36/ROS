#!/usr/bin/env bash
set -euo pipefail

WORKSPACE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GENERATED_DIR="${WORKSPACE_DIR}/diagnostics/generated/pressure_only"
ROS_SETUP="${ROS_SETUP:-/opt/ros/jazzy/setup.bash}"
WORKSPACE_SETUP="${WORKSPACE_SETUP:-${WORKSPACE_DIR}/install/setup.bash}"
AUTO_BUILD="${AUTO_BUILD:-0}"
ALL_SENSOR_LOCAL_ONLY="${ALL_SENSOR_LOCAL_ONLY:-1}"

usage() {
  cat <<'EOF'
Usage:
  ./start_pressure_only.sh l1 [l2|r1|r2 ...]

Examples:
  ./start_pressure_only.sh l1
  ./start_pressure_only.sh l1 l2
  ./start_pressure_only.sh r1 r2
  ./start_pressure_only.sh l1 l2 r1 r2

Targets:
  l1  /pressure/left_hand/gripper_1
  l2  /pressure/left_hand/gripper_2
  r1  /pressure/right_hand/gripper_1
  r2  /pressure/right_hand/gripper_2

Purpose:
  Start only the HWK pressure driver ROS node, with a temporary config limited
  to the selected tactile hardware targets.

Generated runtime-only config files are written under diagnostics/generated/pressure_only.
Project source files and checked-in base configs are not modified.

Environment:
  START_PRESSURE_GENERATE_ONLY=1  Generate configs without launching.
  AUTO_BUILD=1                   Run colcon build before launching.
  PRESSURE_ONLY_PORT=/dev/ttyUSB0 Force all selected targets onto one shared serial port.
  PRESSURE_ONLY_L1_PORT=/dev/ttyUSB0 Override one target serial port.
  PRESSURE_ONLY_L2_PORT=/dev/ttyUSB1 Override one target serial port.
  PRESSURE_ONLY_POLL_RATE=40     Override poll rate in Hz for selected targets.
  PRESSURE_ONLY_DATA_TIMEOUT=0.05 Override one data response timeout in seconds.
  PRESSURE_ONLY_INTER_REQUEST_GAP=0 Override shared-bus request gap in seconds.
  ROS_SETUP=/path/setup.bash     Override ROS setup file.
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if [[ "$#" -eq 0 ]]; then
  usage >&2
  exit 2
fi

mkdir -p "${GENERATED_DIR}"

python3 - "$WORKSPACE_DIR" "$GENERATED_DIR" "$@" <<'PY'
import copy
import glob
import os
import re
import sys
import time
from pathlib import Path

import serial
import yaml


workspace = Path(sys.argv[1])
generated_dir = Path(sys.argv[2])
requested = sys.argv[3:]
valid_targets = ("l1", "l2", "r1", "r2")

seen = set()
targets = []
for raw in requested:
    target = raw.strip().lower()
    if target not in valid_targets:
        raise SystemExit(
            f"Unknown pressure target: {raw}. Expected one of: {', '.join(valid_targets)}"
        )
    if target not in seen:
        seen.add(target)
        targets.append(target)

selection_name = "_".join(targets)
selection_slug = re.sub(r"[^a-z0-9_]+", "_", selection_name)

identity_map_path = workspace / "config" / "hardware_identity_map.yaml"
pressure_config_path = workspace / "src" / "hwk_pressure_driver" / "config" / "pressure_sensors.yaml"
generated_identity_map_path = generated_dir / f"hardware_identity_map_pressure_only_{selection_slug}.yaml"
generated_pressure_config_path = generated_dir / f"pressure_sensors_pressure_only_{selection_slug}.yaml"
env_path = generated_dir / "pressure_only_latest.env"

with identity_map_path.open("r", encoding="utf-8") as stream:
    identity_map = yaml.safe_load(stream) or {}
with pressure_config_path.open("r", encoding="utf-8") as stream:
    pressure_config = yaml.safe_load(stream) or {}

pressure_identity = identity_map.get("pressure") or {}
missing_targets = [target for target in targets if target not in pressure_identity]
if missing_targets:
    raise SystemExit(
        "Missing pressure identity map entries: " + ", ".join(missing_targets)
    )

selected_identity = {}
serial_ports_by_path = {}
params = (
    pressure_config.setdefault("pressure_driver_node", {})
    .setdefault("ros__parameters", {})
)
default_baudrate = int(params.get("default_baudrate", 460800))
default_sensor = copy.deepcopy(params.get("sensor_defaults") or {})
default_sensor.setdefault("device_addr", 6)
default_sensor.setdefault("rows", 6)
default_sensor.setdefault("cols", 15)
port_override = os.environ.get("PRESSURE_ONLY_PORT", "").strip()
auto_ports = sorted(glob.glob("/dev/ttyUSB*") + glob.glob("/dev/ttyACM*"))
auto_detect_timeout = float(os.environ.get("PRESSURE_ONLY_AUTO_DETECT_TIMEOUT", "0.35"))
auto_detect_serial_timeout = float(os.environ.get("PRESSURE_ONLY_AUTO_DETECT_SERIAL_TIMEOUT", "0.02"))

HEAD = bytes((0x3C, 0x3C))
TAIL = bytes((0x3E, 0x3E))
CHAN_DEVICE_INFO = 0x01
TYPE_GET = 0x01
TYPE_DEVICE_INFO_RESPONSE = 0x02
TYPE_ACK = 0x03
DEVICE_INFO_RESPONSE_TYPES = (TYPE_DEVICE_INFO_RESPONSE, TYPE_ACK)
MIN_FRAME_LEN = 10
CMD_CHIP_UID = 0x05


def crc16(payload: bytes) -> int:
    crc = 0
    for byte in payload:
        crc ^= byte
        for _ in range(8):
            if crc & 0x0001:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
            crc &= 0xFFFF
    return crc & 0xFFFF


def build_get_uid_frame(device_addr: int, package_id: int) -> bytes:
    payload = bytes((CMD_CHIP_UID,))
    id_channel = ((device_addr & 0x0F) << 4) | CHAN_DEVICE_INFO
    flags = ((package_id & 0x3F) << 2) | TYPE_GET
    checksum = crc16(payload)
    return b"".join(
        (
            HEAD,
            bytes((id_channel, flags)),
            len(payload).to_bytes(2, byteorder="little", signed=False),
            payload,
            checksum.to_bytes(2, byteorder="little", signed=False),
            TAIL,
        )
    )


def parse_frame(frame: bytes):
    if len(frame) < MIN_FRAME_LEN or frame[:2] != HEAD or frame[-2:] != TAIL:
        return None
    length = int.from_bytes(frame[4:6], byteorder="little", signed=False)
    expected_len = MIN_FRAME_LEN + length
    if len(frame) != expected_len:
        return None
    payload_start = 6
    payload_end = payload_start + length
    payload = frame[payload_start:payload_end]
    received_crc = int.from_bytes(frame[payload_end : payload_end + 2], byteorder="little")
    if received_crc != crc16(payload):
        return None
    id_channel = frame[2]
    flags = frame[3]
    return {
        "device_addr": (id_channel >> 4) & 0x0F,
        "channel": id_channel & 0x0F,
        "frame_type": flags & 0x03,
        "package_id": (flags >> 2) & 0x3F,
        "payload": payload,
    }


def pop_frame(rx_buffer: bytearray):
    while True:
        head_index = rx_buffer.find(HEAD)
        if head_index < 0:
            if rx_buffer[-1:] == HEAD[:1]:
                del rx_buffer[:-1]
            else:
                rx_buffer.clear()
            return None
        if head_index > 0:
            del rx_buffer[:head_index]
        if len(rx_buffer) < MIN_FRAME_LEN:
            return None
        length = int.from_bytes(rx_buffer[4:6], byteorder="little", signed=False)
        if length > 4096:
            del rx_buffer[0]
            continue
        frame_len = MIN_FRAME_LEN + length
        if len(rx_buffer) < frame_len:
            return None
        frame = bytes(rx_buffer[:frame_len])
        del rx_buffer[:frame_len]
        parsed = parse_frame(frame)
        if parsed is not None:
            return parsed


def decode_chip_uid(payload: bytes) -> str:
    text = payload.split(b"\x00", 1)[0]
    if text:
        try:
            decoded = text.decode("ascii")
        except UnicodeDecodeError:
            decoded = ""
        if decoded and all(char.isprintable() for char in decoded):
            return decoded
    raw_hex = payload.hex().upper()
    return "-".join(raw_hex[index : index + 8] for index in range(0, len(raw_hex), 8))


def query_uid(port: str, baudrate: int, device_addr: int, package_id: int):
    request = build_get_uid_frame(device_addr, package_id)
    rx_buffer = bytearray()
    deadline = time.monotonic() + auto_detect_timeout
    try:
        with serial.Serial(
            port=port,
            baudrate=baudrate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=auto_detect_serial_timeout,
        ) as serial_obj:
            serial_obj.reset_input_buffer()
            serial_obj.reset_output_buffer()
            serial_obj.write(request)
            serial_obj.flush()
            while time.monotonic() < deadline:
                waiting = getattr(serial_obj, "in_waiting", 0)
                read_size = min(512, waiting) if waiting else 1
                chunk = serial_obj.read(read_size)
                if chunk:
                    rx_buffer.extend(chunk)
                frame = pop_frame(rx_buffer)
                while frame is not None:
                    if (
                        frame["device_addr"] == device_addr
                        and frame["channel"] == CHAN_DEVICE_INFO
                        and frame["frame_type"] in DEVICE_INFO_RESPONSE_TYPES
                        and frame["package_id"] == package_id
                    ):
                        return decode_chip_uid(frame["payload"])
                    frame = pop_frame(rx_buffer)
    except Exception:
        return None
    return None


def resolve_target_port(target: str, match_cfg: dict, target_cfg: dict) -> str:
    if port_override:
        return port_override

    target_override = os.environ.get(f"PRESSURE_ONLY_{target.upper()}_PORT", "").strip()
    if target_override:
        return target_override

    stable_name = str(target_cfg.get("stable_name", "")).strip()
    if stable_name and Path(stable_name).exists():
        return stable_name

    if len(auto_ports) == 1 and len(targets) == 1:
        return auto_ports[0]

    uid = str(match_cfg.get("HWK_CHIP_UID", "")).strip()
    addr_raw = str(match_cfg.get("HWK_DEVICE_ADDR", "")).strip()
    package_id_raw = str(match_cfg.get("HWK_PACKAGE_ID", "29")).strip()
    if uid and addr_raw and len(auto_ports) > 1:
        device_addr = int(addr_raw, 0)
        package_id = int(package_id_raw, 0)
        matches = []
        for port in auto_ports:
            detected_uid = query_uid(port, default_baudrate, device_addr, package_id)
            if detected_uid == uid:
                matches.append(port)
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            raise SystemExit(
                f"Target {target} matched multiple ports by HWK_CHIP_UID {uid}: "
                + ", ".join(matches)
            )

    if stable_name:
        raise SystemExit(
            f"No usable serial port found for {target}. Stable path does not exist: {stable_name}. "
            f"Auto ports: {', '.join(auto_ports) or '(none)'}. "
            f"Set PRESSURE_ONLY_{target.upper()}_PORT=/dev/ttyUSBx to override, "
            "or install/update config/99-hwk-pressure.rules for stable /dev/hwk_pressure_* links."
        )
    raise SystemExit(
        f"No serial port could be resolved for {target}. "
        f"Auto ports: {', '.join(auto_ports) or '(none)'}. "
        f"Set PRESSURE_ONLY_{target.upper()}_PORT=/dev/ttyUSBx."
    )

for target in targets:
    entry = copy.deepcopy(pressure_identity[target])
    selected_identity[target] = entry
    match_cfg = entry.get("match") or {}
    target_cfg = entry.get("target") or {}
    port = resolve_target_port(target, match_cfg, target_cfg)

    sensor_cfg = copy.deepcopy(default_sensor)
    if str(match_cfg.get("HWK_DEVICE_ADDR", "")).strip():
        sensor_cfg["device_addr"] = int(str(match_cfg["HWK_DEVICE_ADDR"]).strip(), 0)
    sensor_cfg["hand"] = str(target_cfg.get("hand", "")).strip()
    sensor_cfg["gripper"] = str(target_cfg.get("gripper", "")).strip()
    sensor_cfg["topic"] = str(target_cfg.get("topic", "")).strip()

    serial_cfg = serial_ports_by_path.setdefault(
        port,
        {
            "name": str(target_cfg.get("port_config_name", f"{target}_port")),
            "port": port,
            "baudrate": default_baudrate,
            "sensors": [],
        },
    )
    serial_cfg["sensors"].append(sensor_cfg)

serial_ports = list(serial_ports_by_path.values())
for serial_cfg in serial_ports:
    addrs = [sensor["device_addr"] for sensor in serial_cfg["sensors"]]
    duplicate_addrs = sorted({addr for addr in addrs if addrs.count(addr) > 1})
    if duplicate_addrs:
        names = ", ".join(f"addr {addr}" for addr in duplicate_addrs)
        raise SystemExit(
            f"Selected targets share {serial_cfg['port']} but have duplicate {names}. "
            "Sensors on one CH340/UART must use different HWK_DEVICE_ADDR values."
        )
    poll_rate_override = os.environ.get("PRESSURE_ONLY_POLL_RATE", "").strip()
    if poll_rate_override:
        poll_rate_hz = float(poll_rate_override)
    elif len(serial_cfg["sensors"]) > 1:
        poll_rate_hz = 40.0
    else:
        poll_rate_hz = None
    if poll_rate_hz is not None:
        for sensor in serial_cfg["sensors"]:
            sensor["poll_rate_hz"] = poll_rate_hz
    if len(serial_cfg["sensors"]) > 1:
        serial_cfg["serialized_polling"] = True
        serial_cfg["data_response_timeout"] = float(
            os.environ.get("PRESSURE_ONLY_DATA_TIMEOUT", "0.05")
        )
        serial_cfg["inter_request_gap_sec"] = float(
            os.environ.get("PRESSURE_ONLY_INTER_REQUEST_GAP", "0")
        )

driver_identity_map = copy.deepcopy(identity_map)
driver_identity_map["pressure"] = selected_identity

params["identity_map_file"] = str(generated_identity_map_path)
params["strict_identity"] = True
params["identity_query_timeout"] = float(os.environ.get("PRESSURE_ONLY_IDENTITY_TIMEOUT", "3.0"))
params["serial_timeout"] = float(os.environ.get("PRESSURE_ONLY_SERIAL_TIMEOUT", "0.02"))
params["data_response_timeout"] = float(os.environ.get("PRESSURE_ONLY_DATA_TIMEOUT", "0.05"))
params["inter_request_gap_sec"] = float(os.environ.get("PRESSURE_ONLY_INTER_REQUEST_GAP", "0"))
params["serial_port_globs"] = []
params["serial_ports"] = serial_ports

with generated_identity_map_path.open("w", encoding="utf-8") as stream:
    yaml.safe_dump(driver_identity_map, stream, sort_keys=False, allow_unicode=True)
with generated_pressure_config_path.open("w", encoding="utf-8") as stream:
    yaml.safe_dump(pressure_config, stream, sort_keys=False, allow_unicode=True)
with env_path.open("w", encoding="utf-8") as stream:
    stream.write(f"PRESSURE_ONLY_TARGETS={' '.join(targets)}\n")
    stream.write(f"PRESSURE_ONLY_CONFIG={generated_pressure_config_path}\n")
    stream.write(f"PRESSURE_ONLY_IDENTITY_MAP={generated_identity_map_path}\n")

print(f"Selected pressure targets: {' '.join(targets)}")
print(f"Generated pressure config: {generated_pressure_config_path}")
print(f"Generated pressure identity map: {generated_identity_map_path}")
print(f"Env file: {env_path}")
PY

ENV_FILE="${GENERATED_DIR}/pressure_only_latest.env"
if [[ ! -f "${ENV_FILE}" ]]; then
  echo "Generated env file not found: ${ENV_FILE}" >&2
  exit 1
fi

while IFS='=' read -r key value; do
  case "${key}" in
    PRESSURE_ONLY_TARGETS) PRESSURE_ONLY_TARGETS="${value}" ;;
    PRESSURE_ONLY_CONFIG) PRESSURE_ONLY_CONFIG="${value}" ;;
    PRESSURE_ONLY_IDENTITY_MAP) PRESSURE_ONLY_IDENTITY_MAP="${value}" ;;
  esac
done < "${ENV_FILE}"

echo "启用触觉目标: ${PRESSURE_ONLY_TARGETS}"
echo "实际启动 ROS 节点: /pressure_driver_node"
echo "触觉配置: ${PRESSURE_ONLY_CONFIG}"
echo "触觉身份映射: ${PRESSURE_ONLY_IDENTITY_MAP}"
echo "生成文件目录: ${GENERATED_DIR}"

if [[ "${START_PRESSURE_GENERATE_ONLY:-0}" == "1" ]]; then
  echo "仅生成配置，不启动触觉节点: START_PRESSURE_GENERATE_ONLY=1"
  exit 0
fi

if [[ ! -f "${ROS_SETUP}" ]]; then
  echo "ROS setup file not found: ${ROS_SETUP}" >&2
  exit 1
fi

set +u
# shellcheck source=/dev/null
source "${ROS_SETUP}"
set -u

if [[ "${AUTO_BUILD}" == "1" ]]; then
  (
    cd "${WORKSPACE_DIR}"
    colcon build --packages-select hwk_pressure_interfaces hwk_pressure_driver
  )
fi

if [[ ! -f "${WORKSPACE_SETUP}" ]]; then
  echo "Workspace setup file not found: ${WORKSPACE_SETUP}" >&2
  echo "Build manually or run: AUTO_BUILD=1 $0 $*" >&2
  exit 1
fi

set +u
# shellcheck source=/dev/null
source "${WORKSPACE_SETUP}"
set -u

if [[ "${ALL_SENSOR_LOCAL_ONLY}" == "1" ]]; then
  export ROS_AUTOMATIC_DISCOVERY_RANGE="LOCALHOST"
  export ROS_STATIC_PEERS=""
  echo "ROS discovery scope: LOCALHOST"
  echo "另一个终端验证时请先执行: ros2 daemon stop"
  echo "然后使用: ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST ros2 topic list --no-daemon"
fi

ros2 daemon stop >/dev/null 2>&1 || true

exec ros2 launch hwk_pressure_driver pressure_driver.launch.py \
  config_file:="${PRESSURE_ONLY_CONFIG}"
