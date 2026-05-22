#!/usr/bin/env bash
set -euo pipefail

WORKSPACE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GENERATED_DIR="${WORKSPACE_DIR}/diagnostics/generated"

usage() {
  cat <<'EOF'
Usage:
  ./start_right_hand_only.sh

Purpose:
  Start only right-hand sensor nodes:
    - Baton Mini right
    - GoPro right
    - HWK pressure right gripper 1 and 2

Generated runtime-only config files are written under diagnostics/generated.
Project source files and checked-in base configs are not modified.

Environment:
  START_RIGHT_HAND_GENERATE_ONLY=1  Generate configs without launching.
  AUTO_BUILD=0                     Skip colcon build in start_all_sensor.sh.
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

mkdir -p "${GENERATED_DIR}"

python3 - "$WORKSPACE_DIR" "$GENERATED_DIR" <<'PY'
import copy
import sys
from pathlib import Path

import yaml


workspace = Path(sys.argv[1])
generated_dir = Path(sys.argv[2])

all_sensor_path = generated_dir / "all_sensor_nodes_right_hand_only.yaml"
driver_identity_map_path = generated_dir / "hardware_identity_map_right_hand_pressure.yaml"
pressure_config_path = generated_dir / "pressure_sensors_right_hand_only.yaml"
disabled_identity_map_path = generated_dir / "disabled_hardware_identity_map.yaml"

with (workspace / "config" / "all_sensor_nodes.yaml").open("r", encoding="utf-8") as stream:
    all_sensor = yaml.safe_load(stream) or {}
with (workspace / "config" / "hardware_identity_map.yaml").open("r", encoding="utf-8") as stream:
    identity_map = yaml.safe_load(stream) or {}
with (workspace / "src" / "hwk_pressure_driver" / "config" / "pressure_sensors.yaml").open(
    "r", encoding="utf-8"
) as stream:
    pressure_config = yaml.safe_load(stream) or {}

for section in ("baton_mini", "gopro"):
    section_cfg = all_sensor.setdefault(section, {})
    if "right" in section_cfg:
        section_cfg["right"]["enabled"] = True
    if "left" in section_cfg:
        section_cfg["left"]["enabled"] = False

pressure_cfg = all_sensor.setdefault("pressure", {})
pressure_cfg["enabled"] = True
pressure_cfg["config_file"] = str(pressure_config_path)

pressure_topics = pressure_cfg.setdefault("topics", {})
for key in ("left_gripper_1", "left_gripper_2"):
    pressure_topics.setdefault(key, {})["enabled"] = False
for key in ("right_gripper_1", "right_gripper_2"):
    pressure_topics.setdefault(key, {})["enabled"] = True

# Disable the global preflight identity validator for this partial-hardware
# launcher. The pressure driver still receives a strict right-hand-only
# identity map below.
all_sensor["hardware_identity"] = {"enabled": False}

driver_identity_map = copy.deepcopy(identity_map)
pressure_identity = driver_identity_map.get("pressure") or {}
driver_identity_map["pressure"] = {
    key: pressure_identity[key]
    for key in ("r1", "r2")
    if key in pressure_identity
}

params = (
    pressure_config.setdefault("pressure_driver_node", {})
    .setdefault("ros__parameters", {})
)
params["identity_map_file"] = str(driver_identity_map_path)
params["strict_identity"] = True

with all_sensor_path.open("w", encoding="utf-8") as stream:
    yaml.safe_dump(all_sensor, stream, sort_keys=False, allow_unicode=True)
with driver_identity_map_path.open("w", encoding="utf-8") as stream:
    yaml.safe_dump(driver_identity_map, stream, sort_keys=False, allow_unicode=True)
with pressure_config_path.open("w", encoding="utf-8") as stream:
    yaml.safe_dump(pressure_config, stream, sort_keys=False, allow_unicode=True)

# start_all_sensor.sh only runs identity validation when this env path exists.
if disabled_identity_map_path.exists():
    disabled_identity_map_path.unlink()

env_path = generated_dir / "right_hand_only_latest.env"
with env_path.open("w", encoding="utf-8") as stream:
    stream.write(f"ALL_SENSOR_CONFIG={all_sensor_path}\n")
    stream.write(f"HARDWARE_IDENTITY_MAP={disabled_identity_map_path}\n")
    stream.write(f"RIGHT_HAND_PRESSURE_CONFIG={pressure_config_path}\n")
    stream.write(f"RIGHT_HAND_PRESSURE_IDENTITY_MAP={driver_identity_map_path}\n")

print(f"Generated right-hand config: {all_sensor_path}")
print(f"Generated pressure config: {pressure_config_path}")
print(f"Generated pressure identity map: {driver_identity_map_path}")
print(f"Env file: {env_path}")
PY

ENV_FILE="${GENERATED_DIR}/right_hand_only_latest.env"
if [[ ! -f "${ENV_FILE}" ]]; then
  echo "Generated env file not found: ${ENV_FILE}" >&2
  exit 1
fi

while IFS='=' read -r key value; do
  case "${key}" in
    ALL_SENSOR_CONFIG) export ALL_SENSOR_CONFIG="${value}" ;;
    HARDWARE_IDENTITY_MAP) export HARDWARE_IDENTITY_MAP="${value}" ;;
    RIGHT_HAND_PRESSURE_CONFIG) export RIGHT_HAND_PRESSURE_CONFIG="${value}" ;;
    RIGHT_HAND_PRESSURE_IDENTITY_MAP) export RIGHT_HAND_PRESSURE_IDENTITY_MAP="${value}" ;;
  esac
done < "${ENV_FILE}"

echo "使用右手专用配置: ${ALL_SENSOR_CONFIG}"
echo "右手触觉配置: ${RIGHT_HAND_PRESSURE_CONFIG}"
echo "右手触觉身份映射: ${RIGHT_HAND_PRESSURE_IDENTITY_MAP}"
echo "生成文件目录: ${GENERATED_DIR}"

if [[ "${START_RIGHT_HAND_GENERATE_ONLY:-0}" == "1" ]]; then
  echo "仅生成配置，不启动传感器: START_RIGHT_HAND_GENERATE_ONLY=1"
  exit 0
fi

exec "${WORKSPACE_DIR}/start_all_sensor.sh"
