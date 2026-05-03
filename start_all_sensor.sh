#!/usr/bin/env bash
#./cleanup_ros_residue.sh --dry-run
#./cleanup_ros_residue.sh

set -euo pipefail

WORKSPACE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROS_SETUP="${ROS_SETUP:-/opt/ros/jazzy/setup.bash}"
WORKSPACE_SETUP="${WORKSPACE_SETUP:-${WORKSPACE_DIR}/install/setup.bash}"
CONFIG_FILE="${1:-${ALL_SENSOR_CONFIG:-${WORKSPACE_DIR}/config/all_sensor_nodes.yaml}}"
STATUS_SCRIPT="${WORKSPACE_DIR}/scripts/all_sensor_status.py"
AUTO_BUILD="${AUTO_BUILD:-1}"
BUILD_PACKAGES="${BUILD_PACKAGES:-}"
STARTUP_WAIT="${STARTUP_WAIT:-20}"
ALL_SENSOR_LOCAL_ONLY="${ALL_SENSOR_LOCAL_ONLY:-1}"
STOP_ON_FAILURE="${STOP_ON_FAILURE:-1}"
LOG_DIR="${WORKSPACE_DIR}/log/start_all_sensor"
HARDWARE_IDENTITY_MAP="${HARDWARE_IDENTITY_MAP:-${WORKSPACE_DIR}/config/hardware_identity_map.yaml}"
HARDWARE_IDENTITY_RESOLVED_FILE="${HARDWARE_IDENTITY_RESOLVED_FILE:-${LOG_DIR}/hardware_identity_resolved.yaml}"
CLEANING_UP=0

source_setup_file() {
  local setup_file="$1"

  # ROS/ament setup files may read optional unset variables.
  set +u
  # shellcheck source=/dev/null
  source "${setup_file}"
  set -u
}

build_workspace() {
  local build_cmd=(colcon build)

  if [[ -n "${BUILD_PACKAGES}" ]]; then
    # shellcheck disable=SC2206
    local packages=(${BUILD_PACKAGES})
    build_cmd+=(--packages-select "${packages[@]}")
  fi

  echo
  if [[ -n "${BUILD_PACKAGES}" ]]; then
    echo "编译指定 ROS 包: ${BUILD_PACKAGES}"
  else
    echo "编译工作区全部 ROS 包..."
  fi
  (
    cd "${WORKSPACE_DIR}"
    "${build_cmd[@]}"
  )
}

if [[ ! -f "${ROS_SETUP}" ]]; then
  echo "ROS setup file not found: ${ROS_SETUP}" >&2
  exit 1
fi

if [[ ! -f "${CONFIG_FILE}" ]]; then
  echo "Sensor config file not found: ${CONFIG_FILE}" >&2
  exit 1
fi

if [[ ! -f "${STATUS_SCRIPT}" ]]; then
  echo "Status helper not found: ${STATUS_SCRIPT}" >&2
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
  echo "Workspace setup file not found after build: ${WORKSPACE_SETUP}" >&2
  echo "Build manually: cd ${WORKSPACE_DIR} && source ${ROS_SETUP} && colcon build" >&2
  exit 1
fi

source_setup_file "${WORKSPACE_SETUP}"

if [[ "${ALL_SENSOR_LOCAL_ONLY}" == "1" ]]; then
  export ROS_AUTOMATIC_DISCOVERY_RANGE="LOCALHOST"
  export ROS_STATIC_PEERS=""
  echo "ROS discovery scope: LOCALHOST"
  echo "另一个终端验证时请先执行: ros2 daemon stop"
  echo "然后使用: ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST ros2 topic list --no-daemon"
fi

ros2 daemon stop >/dev/null 2>&1 || true

mkdir -p "${LOG_DIR}"
rm -f "${HARDWARE_IDENTITY_RESOLVED_FILE}"

IDENTITY_ARGS=()
if [[ -f "${HARDWARE_IDENTITY_MAP}" ]]; then
  IDENTITY_ARGS=(
    --identity-map "${HARDWARE_IDENTITY_MAP}"
    --write-identity-resolved "${HARDWARE_IDENTITY_RESOLVED_FILE}"
  )
fi

python3 "${STATUS_SCRIPT}" preflight --config "${CONFIG_FILE}" "${IDENTITY_ARGS[@]}"

LOG_FILE="${LOG_DIR}/$(date +%Y%m%d_%H%M%S).log"
echo
echo "启动总 launch，日志文件: ${LOG_FILE}"
echo "等待 ${STARTUP_WAIT}s 后检查节点和 topic..."

setsid ros2 launch "${WORKSPACE_DIR}/launch/all_sensor_nodes.launch.py" \
  config_file:="${CONFIG_FILE}" \
  identity_resolved_file:="${HARDWARE_IDENTITY_RESOLVED_FILE}" \
  > >(tee -a "${LOG_FILE}") 2>&1 &
LAUNCH_PID=$!

cleanup() {
  if [[ "${CLEANING_UP}" == "1" ]]; then
    return
  fi
  CLEANING_UP=1
  trap - INT TERM
  if kill -0 "${LAUNCH_PID}" >/dev/null 2>&1; then
    echo
    echo "停止 all sensor launch..."
    kill -INT "-${LAUNCH_PID}" >/dev/null 2>&1 || kill -INT "${LAUNCH_PID}" >/dev/null 2>&1 || true
    for _ in $(seq 1 8); do
      if ! kill -0 "${LAUNCH_PID}" >/dev/null 2>&1; then
        break
      fi
      sleep 1
    done
    if kill -0 "${LAUNCH_PID}" >/dev/null 2>&1; then
      kill -TERM "-${LAUNCH_PID}" >/dev/null 2>&1 || kill -TERM "${LAUNCH_PID}" >/dev/null 2>&1 || true
    fi
    wait "${LAUNCH_PID}" || true
  fi
}
trap cleanup INT TERM

sleep "${STARTUP_WAIT}"

if ! kill -0 "${LAUNCH_PID}" >/dev/null 2>&1; then
  echo
  echo "FAIL 总 launch 已提前退出。最近日志:"
  tail -n 80 "${LOG_FILE}" || true
  wait "${LAUNCH_PID}" || true
  exit 1
fi

set +e
python3 "${STATUS_SCRIPT}" postlaunch \
  --config "${CONFIG_FILE}" \
  --identity-resolved "${HARDWARE_IDENTITY_RESOLVED_FILE}"
STATUS=$?
set -e

if [[ "${STATUS}" -ne 0 ]]; then
  echo
  echo "最近 launch 日志:"
  tail -n 80 "${LOG_FILE}" || true
  if [[ "${STOP_ON_FAILURE}" == "1" ]]; then
    echo
    echo "检测到节点启动失败，停止已启动的相机节点。"
    cleanup
    exit "${STATUS}"
  fi
fi

echo
echo "launch 仍在运行。按 Ctrl+C 停止全部相机节点。"
wait "${LAUNCH_PID}"
