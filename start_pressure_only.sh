#!/usr/bin/env bash
set -euo pipefail

WORKSPACE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GENERATED_DIR="${WORKSPACE_DIR}/diagnostics/generated"
ROS_SETUP="${ROS_SETUP:-/opt/ros/jazzy/setup.bash}"
WORKSPACE_SETUP="${WORKSPACE_SETUP:-${WORKSPACE_DIR}/install/setup.bash}"
AUTO_BUILD="${AUTO_BUILD:-1}"
PRESSURE_LOCAL_ONLY="${PRESSURE_LOCAL_ONLY:-1}"

usage() {
  cat <<'EOF'
Usage:
  ./start_pressure_only.sh [l1] [l2] [r1] [r2]
  ./start_pressure_only.sh r2,r1,l1

Purpose:
  Start only the HWK pressure/tactile ROS2 driver. Baton Mini, GoPro, and
  launch/all_sensor_nodes.launch.py are not started.

Arguments:
  l1 = /pressure/left_hand/gripper_1
  l2 = /pressure/left_hand/gripper_2
  r1 = /pressure/right_hand/gripper_1
  r2 = /pressure/right_hand/gripper_2

Behavior:
  - Any subset and any order are accepted.
  - Comma-separated and space-separated arguments are accepted.
  - Duplicate selections are ignored.
  - No arguments means all four sensors: l1 l2 r1 r2.

Environment:
  START_PRESSURE_ONLY_GENERATE_ONLY=1  Generate configs without launching.
  AUTO_BUILD=0                         Skip colcon build.
  PRESSURE_LOCAL_ONLY=0                Do not force ROS discovery to localhost.
EOF
}

source_setup_file() {
  local setup_file="$1"

  set +u
  # shellcheck source=/dev/null
  source "${setup_file}"
  set -u
}

build_workspace() {
  echo
  echo "编译触觉 ROS 包..."
  (
    cd "${WORKSPACE_DIR}"
    colcon build --packages-select hwk_pressure_interfaces hwk_pressure_driver
  )
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

mkdir -p "${GENERATED_DIR}"

python3 - "$WORKSPACE_DIR" "$GENERATED_DIR" "$@" <<'PY'
import copy
from glob import glob
import os
import sys
import time
from pathlib import Path

import yaml

try:
    import serial
except ImportError as exc:
    raise SystemExit("pyserial is required for pressure identity probing") from exc


workspace = Path(sys.argv[1])
generated_dir = Path(sys.argv[2])
raw_args = sys.argv[3:]

valid_order = ("l1", "l2", "r1", "r2")
topic_by_key = {
    "l1": "/pressure/left_hand/gripper_1",
    "l2": "/pressure/left_hand/gripper_2",
    "r1": "/pressure/right_hand/gripper_1",
    "r2": "/pressure/right_hand/gripper_2",
}
scan_addrs = [int(value) for value in range(16)]
identity_query_timeout = float(os.environ.get("PRESSURE_IDENTITY_QUERY_TIMEOUT", "0.3"))

HEAD = bytes((0x3C, 0x3C))
TAIL = bytes((0x3E, 0x3E))
CHAN_DEVICE_INFO = 0x01
TYPE_GET = 0x01
DEVICE_INFO_RESPONSE_TYPES = (0x02, 0x03)
CMD_CHIP_UID = 0x05
MIN_FRAME_LEN = 10


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


def build_identity_request(device_addr: int, package_id: int) -> bytes:
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
    if len(frame) < MIN_FRAME_LEN or frame[:2] != HEAD:
        return None
    length = int.from_bytes(frame[4:6], byteorder="little", signed=False)
    expected_len = MIN_FRAME_LEN + length
    if len(frame) != expected_len or frame[-2:] != TAIL:
        return None
    payload_start = 6
    payload_end = payload_start + length
    payload = frame[payload_start:payload_end]
    received_crc = int.from_bytes(frame[payload_end : payload_end + 2], "little")
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


def decode_uid(payload: bytes) -> str:
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


def query_uid(serial_obj, device_addr: int, package_id: int, timeout_sec: float):
    request = build_identity_request(device_addr, package_id)
    rx_buffer = bytearray()
    deadline = time.monotonic() + timeout_sec
    serial_obj.reset_input_buffer()
    serial_obj.reset_output_buffer()
    serial_obj.write(request)
    serial_obj.flush()
    while time.monotonic() < deadline:
        chunk = serial_obj.read(512)
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
                return decode_uid(frame["payload"])
            frame = pop_frame(rx_buffer)
    return None

def fail_usage(message: str) -> None:
    print(message, file=sys.stderr)
    print("Usage:", file=sys.stderr)
    print("  ./start_pressure_only.sh [l1] [l2] [r1] [r2]", file=sys.stderr)
    print("  ./start_pressure_only.sh r2,r1,l1", file=sys.stderr)
    print("Valid values: l1, l2, r1, r2", file=sys.stderr)
    raise SystemExit(1)


selected = []
tokens = raw_args or list(valid_order)
for raw in tokens:
    for part in str(raw).replace(",", " ").split():
        key = part.strip().lower()
        if not key:
            continue
        if key not in valid_order:
            fail_usage(f"Unknown pressure sensor '{part}'.")
        if key not in selected:
            selected.append(key)

if not selected:
    selected = list(valid_order)

label = "_".join(selected)
identity_map_path = generated_dir / f"hardware_identity_map_pressure_only_{label}.yaml"
pressure_config_path = generated_dir / f"pressure_sensors_pressure_only_{label}.yaml"
env_path = generated_dir / "pressure_only_latest.env"

with (workspace / "config" / "hardware_identity_map.yaml").open("r", encoding="utf-8") as stream:
    identity_map = yaml.safe_load(stream) or {}
with (workspace / "src" / "hwk_pressure_driver" / "config" / "pressure_sensors.yaml").open(
    "r", encoding="utf-8"
) as stream:
    pressure_config = yaml.safe_load(stream) or {}

source_pressure = identity_map.get("pressure") or {}
missing = [key for key in selected if key not in source_pressure]
if missing:
    raise SystemExit(
        "Selected pressure sensors are missing from config/hardware_identity_map.yaml: "
        + ", ".join(missing)
    )

driver_identity_map = copy.deepcopy(identity_map)
driver_identity_map["pressure"] = {
    key: copy.deepcopy(source_pressure[key])
    for key in valid_order
    if key in selected
}

params = (
    pressure_config.setdefault("pressure_driver_node", {})
    .setdefault("ros__parameters", {})
)
params["identity_map_file"] = str(identity_map_path)
params["strict_identity"] = True
params["identity_query_timeout"] = identity_query_timeout

serial_patterns = params.pop("serial_port_globs", None) or params.pop("candidate_serial_ports", None)
if serial_patterns is None:
    serial_patterns = ["/dev/ttyUSB*", "/dev/ttyACM*"]
if isinstance(serial_patterns, str):
    serial_patterns = [serial_patterns]

ports = []
for pattern in serial_patterns:
    ports.extend(glob(str(pattern)))
ports = sorted(set(ports))
if not ports:
    raise SystemExit("No pressure serial ports found from patterns: " + ", ".join(serial_patterns))

sensor_defaults = params.get("sensor_defaults") or {}
rows = int(sensor_defaults.get("rows", 6))
cols = int(sensor_defaults.get("cols", 15))
poll_rate_hz = float(sensor_defaults.get("poll_rate_hz", params.get("default_poll_rate_hz", 100.0)))
baudrate = int(params.get("default_baudrate", 460800))
serial_timeout = float(params.get("serial_timeout", 0.01))
identity_query_package_id = int(params.get("identity_query_package_id", 29))

uid_to_key = {
    str((source_pressure[key].get("match") or {}).get("HWK_CHIP_UID", "")).strip(): key
    for key in selected
}
uid_to_key = {uid: key for uid, key in uid_to_key.items() if uid}
detected = []
detected_by_key = {}

print("Probing pressure identities before launch...")
for port in ports:
    try:
        with serial.Serial(
            port=port,
            baudrate=baudrate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=serial_timeout,
        ) as serial_obj:
            for addr in scan_addrs:
                uid = query_uid(
                    serial_obj,
                    device_addr=addr,
                    package_id=identity_query_package_id,
                    timeout_sec=identity_query_timeout,
                )
                if not uid:
                    continue
                key = uid_to_key.get(uid)
                label_suffix = f", selected={key}" if key else ", not selected"
                print(f"  OK {port} addr={addr} uid={uid}{label_suffix}")
                if key and key not in detected_by_key:
                    detected_by_key[key] = {
                        "port": port,
                        "addr": addr,
                        "uid": uid,
                    }
                break
    except Exception as exc:
        print(f"  WARN {port}: probe failed: {exc}")

for key in selected:
    match = detected_by_key.get(key)
    if match:
        detected.append((key, match))
    else:
        print(f"  WARN selected sensor {key} was not detected on current serial ports")

if not detected:
    raise SystemExit(
        "No selected pressure sensors responded. Check power, USB, device address, or selection."
    )

params["serial_ports"] = [
    {
        "name": f"pressure_only_{key}_{Path(match['port']).name}_{index}",
        "port": match["port"],
        "baudrate": baudrate,
        "sensors": [
            {
                "device_addr": match["addr"],
                "rows": rows,
                "cols": cols,
                "poll_rate_hz": poll_rate_hz,
            }
        ],
    }
    for index, (key, match) in enumerate(detected)
]

with identity_map_path.open("w", encoding="utf-8") as stream:
    yaml.safe_dump(driver_identity_map, stream, sort_keys=False, allow_unicode=True)
with pressure_config_path.open("w", encoding="utf-8") as stream:
    yaml.safe_dump(pressure_config, stream, sort_keys=False, allow_unicode=True)
with env_path.open("w", encoding="utf-8") as stream:
    stream.write(f"PRESSURE_ONLY_CONFIG={pressure_config_path}\n")
    stream.write(f"PRESSURE_ONLY_IDENTITY_MAP={identity_map_path}\n")
    stream.write(f"PRESSURE_ONLY_SELECTED={','.join(selected)}\n")
    stream.write(
        "PRESSURE_ONLY_TOPICS="
        + ",".join(topic_by_key[key] for key in selected)
        + "\n"
    )

print(f"Generated pressure config: {pressure_config_path}")
print(f"Generated pressure identity map: {identity_map_path}")
print(f"Selected pressure sensors: {', '.join(selected)}")
print("Selected pressure topics: " + ", ".join(topic_by_key[key] for key in selected))
print("Candidate serial ports: " + ", ".join(ports))
print(f"Identity address probe: {scan_addrs[0]}..{scan_addrs[-1]}, timeout={identity_query_timeout}s")
print(
    "Detected selected sensors: "
    + ", ".join(f"{key}@{match['port']}:addr{match['addr']}" for key, match in detected)
)
print(f"Env file: {env_path}")
PY

ENV_FILE="${GENERATED_DIR}/pressure_only_latest.env"
if [[ ! -f "${ENV_FILE}" ]]; then
  echo "Generated env file not found: ${ENV_FILE}" >&2
  exit 1
fi

while IFS='=' read -r key value; do
  case "${key}" in
    PRESSURE_ONLY_CONFIG) export PRESSURE_ONLY_CONFIG="${value}" ;;
    PRESSURE_ONLY_IDENTITY_MAP) export PRESSURE_ONLY_IDENTITY_MAP="${value}" ;;
    PRESSURE_ONLY_SELECTED) export PRESSURE_ONLY_SELECTED="${value}" ;;
    PRESSURE_ONLY_TOPICS) export PRESSURE_ONLY_TOPICS="${value}" ;;
  esac
done < "${ENV_FILE}"

echo "使用触觉专用配置: ${PRESSURE_ONLY_CONFIG}"
echo "触觉身份映射: ${PRESSURE_ONLY_IDENTITY_MAP}"
echo "本次启动触觉: ${PRESSURE_ONLY_SELECTED}"
echo "本次发布 topic: ${PRESSURE_ONLY_TOPICS}"
echo "生成文件目录: ${GENERATED_DIR}"

if [[ "${START_PRESSURE_ONLY_GENERATE_ONLY:-0}" == "1" ]]; then
  echo "仅生成配置，不启动触觉节点: START_PRESSURE_ONLY_GENERATE_ONLY=1"
  exit 0
fi

if [[ ! -f "${ROS_SETUP}" ]]; then
  echo "ROS setup file not found: ${ROS_SETUP}" >&2
  exit 1
fi

source_setup_file "${ROS_SETUP}"

if [[ "${AUTO_BUILD}" == "1" ]]; then
  if ! command -v colcon >/dev/null 2>&1; then
    echo "colcon not found. Install colcon or run with AUTO_BUILD=0 after building manually." >&2
    exit 1
  fi
  build_workspace
else
  echo "跳过自动编译: AUTO_BUILD=0"
fi

if [[ ! -f "${WORKSPACE_SETUP}" ]]; then
  echo "Workspace setup file not found: ${WORKSPACE_SETUP}" >&2
  echo "Build manually: cd ${WORKSPACE_DIR} && source ${ROS_SETUP} && colcon build --packages-select hwk_pressure_interfaces hwk_pressure_driver" >&2
  exit 1
fi

source_setup_file "${WORKSPACE_SETUP}"

if [[ "${PRESSURE_LOCAL_ONLY}" == "1" ]]; then
  export ROS_AUTOMATIC_DISCOVERY_RANGE="LOCALHOST"
  export ROS_STATIC_PEERS=""
  echo "ROS discovery scope: LOCALHOST"
  echo "另一个终端验证时请先执行: ros2 daemon stop"
  echo "然后使用: ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST ros2 topic list --no-daemon"
fi

ros2 daemon stop >/dev/null 2>&1 || true

exec ros2 launch hwk_pressure_driver pressure_driver.launch.py \
  config_file:="${PRESSURE_ONLY_CONFIG}"
