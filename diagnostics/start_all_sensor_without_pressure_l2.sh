#!/usr/bin/env bash
set -euo pipefail

WORKSPACE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIAGNOSTICS_DIR="${WORKSPACE_DIR}/diagnostics"
GENERATED_DIR="${DIAGNOSTICS_DIR}/generated"

usage() {
  cat <<'EOF'
Usage:
  diagnostics/start_all_sensor_without_pressure_l2.sh [l1] [l2] [r1] [r2]

Purpose:
  Start the normal all-sensor launcher, but exclude selected HWK pressure
  sensors for this run. All generated files stay under diagnostics/generated.

Examples:
  diagnostics/start_all_sensor_without_pressure_l2.sh
      Default: exclude l2 only.

  diagnostics/start_all_sensor_without_pressure_l2.sh l1 l2
      Exclude left-hand pressure sensors l1 and l2.

  diagnostics/start_all_sensor_without_pressure_l2.sh l1 l2 r1 r2
      Exclude all pressure sensors; start Baton Mini and GoPro only.

Aliases:
  l1 = /pressure/left_hand/gripper_1
  l2 = /pressure/left_hand/gripper_2
  r1 = /pressure/right_hand/gripper_1
  r2 = /pressure/right_hand/gripper_2
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

mkdir -p "${GENERATED_DIR}"

python3 - "$WORKSPACE_DIR" "$GENERATED_DIR" "$@" <<'PY'
import copy
import sys
from pathlib import Path

import yaml


workspace = Path(sys.argv[1])
generated_dir = Path(sys.argv[2])
raw_excludes = sys.argv[3:] or ["l2"]

aliases = {
    "l1": "left_gripper_1",
    "l2": "left_gripper_2",
    "r1": "right_gripper_1",
    "r2": "right_gripper_2",
}

exclude_keys = []
for raw in raw_excludes:
    for part in str(raw).replace(",", " ").split():
        key = part.strip().lower()
        if not key:
            continue
        if key not in aliases:
            valid = ", ".join(sorted(aliases))
            raise SystemExit(f"Unknown pressure sensor '{part}'. Valid values: {valid}")
        if key not in exclude_keys:
            exclude_keys.append(key)

label = "_".join(exclude_keys) if exclude_keys else "none"
all_sensor_path = generated_dir / f"all_sensor_nodes_without_{label}.yaml"
driver_identity_map_path = generated_dir / f"hardware_identity_map_without_{label}_driver.yaml"
pressure_config_path = generated_dir / f"pressure_sensors_without_{label}.yaml"
disabled_identity_map_path = generated_dir / "disabled_hardware_identity_map.yaml"

with (workspace / "config" / "all_sensor_nodes.yaml").open("r", encoding="utf-8") as stream:
    all_sensor = yaml.safe_load(stream) or {}
with (workspace / "config" / "hardware_identity_map.yaml").open("r", encoding="utf-8") as stream:
    identity_map = yaml.safe_load(stream) or {}
with (workspace / "src" / "hwk_pressure_driver" / "config" / "pressure_sensors.yaml").open(
    "r", encoding="utf-8"
) as stream:
    pressure_config = yaml.safe_load(stream) or {}

pressure_cfg = all_sensor.setdefault("pressure", {})
pressure_topics = pressure_cfg.setdefault("topics", {})
driver_identity_map = copy.deepcopy(identity_map)
driver_pressure = driver_identity_map.get("pressure") or {}

for key in exclude_keys:
    pressure_topics.setdefault(aliases[key], {})["enabled"] = False
    driver_pressure.pop(key, None)

enabled_pressure_keys = [
    key for key in ("l1", "l2", "r1", "r2")
    if key not in exclude_keys and key in driver_pressure
]

# Do not run the original preflight hardware-identity validation in this
# diagnostics launcher. It treats unconfigured CH340 devices as hard failures,
# which conflicts with "exclude this broken/unstable pressure sensor for now".
all_sensor.setdefault("hardware_identity", {})["enabled"] = False
all_sensor["hardware_identity"].pop("map_file", None)

if enabled_pressure_keys:
    driver_identity_map["pressure"] = {
        key: driver_pressure[key]
        for key in ("l1", "l2", "r1", "r2")
        if key in driver_pressure
    }

    params = (
        pressure_config.setdefault("pressure_driver_node", {})
        .setdefault("ros__parameters", {})
    )
    params["identity_map_file"] = str(driver_identity_map_path)

    pressure_cfg["enabled"] = True
    pressure_cfg["config_file"] = str(pressure_config_path)

    with driver_identity_map_path.open("w", encoding="utf-8") as stream:
        yaml.safe_dump(driver_identity_map, stream, sort_keys=False, allow_unicode=True)
    with pressure_config_path.open("w", encoding="utf-8") as stream:
        yaml.safe_dump(pressure_config, stream, sort_keys=False, allow_unicode=True)
else:
    pressure_cfg["enabled"] = False

with all_sensor_path.open("w", encoding="utf-8") as stream:
    yaml.safe_dump(all_sensor, stream, sort_keys=False, allow_unicode=True)

# The base start_all_sensor.sh only invokes identity validation if this file
# exists. Keep this path non-existent on purpose.
if disabled_identity_map_path.exists():
    disabled_identity_map_path.unlink()

env_path = generated_dir / "without_pressure_latest.env"
with env_path.open("w", encoding="utf-8") as stream:
    stream.write(f"ALL_SENSOR_CONFIG={all_sensor_path}\n")
    stream.write(f"HARDWARE_IDENTITY_MAP={disabled_identity_map_path}\n")
    stream.write(f"PRESSURE_EXCLUDED={','.join(exclude_keys)}\n")

print(f"Generated config: {all_sensor_path}")
print(f"Excluded pressure sensors: {', '.join(exclude_keys)}")
print(f"Env file: {env_path}")
PY

ENV_FILE="${GENERATED_DIR}/without_pressure_latest.env"
if [[ ! -f "${ENV_FILE}" ]]; then
  echo "Generated env file not found: ${ENV_FILE}" >&2
  exit 1
fi

while IFS='=' read -r key value; do
  case "${key}" in
    ALL_SENSOR_CONFIG) export ALL_SENSOR_CONFIG="${value}" ;;
    HARDWARE_IDENTITY_MAP) export HARDWARE_IDENTITY_MAP="${value}" ;;
    PRESSURE_EXCLUDED) export PRESSURE_EXCLUDED="${value}" ;;
  esac
done < "${ENV_FILE}"

echo "使用诊断降级配置: ${ALL_SENSOR_CONFIG}"
echo "本次不启动触觉传感器: ${PRESSURE_EXCLUDED}"
echo "生成文件目录: ${GENERATED_DIR}"

if [[ "${START_ALL_SENSOR_GENERATE_ONLY:-0}" == "1" ]]; then
  echo "仅生成配置，不启动传感器: START_ALL_SENSOR_GENERATE_ONLY=1"
  exit 0
fi

exec "${WORKSPACE_DIR}/start_all_sensor.sh"
