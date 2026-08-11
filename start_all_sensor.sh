#!/usr/bin/env bash
#./cleanup_ros_residue.sh --dry-run
#./cleanup_ros_residue.sh

set -euo pipefail

WORKSPACE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROS_SETUP="${ROS_SETUP:-/opt/ros/jazzy/setup.bash}"
WORKSPACE_SETUP="${WORKSPACE_SETUP:-${WORKSPACE_DIR}/install/setup.bash}"
STATUS_SCRIPT="${WORKSPACE_DIR}/scripts/all_sensor_status.py"
AUTO_BUILD="${AUTO_BUILD:-1}"
BUILD_PACKAGES="${BUILD_PACKAGES:-}"
STARTUP_WAIT="${STARTUP_WAIT:-20}"
ALL_SENSOR_LOCAL_ONLY="${ALL_SENSOR_LOCAL_ONLY:-1}"
STOP_ON_FAILURE="${STOP_ON_FAILURE:-1}"
LOG_DIR="${LOG_DIR:-${WORKSPACE_DIR}/log/start_all_sensor}"
HARDWARE_IDENTITY_MAP="${HARDWARE_IDENTITY_MAP:-${WORKSPACE_DIR}/config/hardware_identity_map.yaml}"
HARDWARE_IDENTITY_RESOLVED_FILE="${HARDWARE_IDENTITY_RESOLVED_FILE:-${LOG_DIR}/hardware_identity_resolved.yaml}"
OCTOPUS_QT_ROOT="${OCTOPUS_QT_ROOT:-${HOME}/Qt/6.11.0/gcc_64}"
OCTOPUS_FFMPEG_ROOT="${OCTOPUS_FFMPEG_ROOT:-${WORKSPACE_DIR}/src/data_collection/VTLA_octopus-master/.deps/ffmpeg8/usr}"
ROS_PYTHON_EXECUTABLE="${ROS_PYTHON_EXECUTABLE:-/usr/bin/python3}"
CLEANING_UP=0

# 解析命令行参数
SMOKE_TEST=0
PRESSURE_ENABLED=1
VALIDATE_HARDWARE_IDENTITY=1
POSITIONAL_ARGS=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --smoke-test)
      SMOKE_TEST=1
      shift
      ;;
    --no-tactile)
      PRESSURE_ENABLED=0
      VALIDATE_HARDWARE_IDENTITY=0
      shift
      ;;
    *)
      POSITIONAL_ARGS+=("$1")
      shift
      ;;
  esac
done

if [[ "${SMOKE_TEST}" == "1" ]]; then
  CONFIG_FILE="${WORKSPACE_DIR}/config/all_sensor_nodes_smoke_test.yaml"
  echo "=== 冒烟测试模式：使用禁用全部传感器的配置 ==="
  echo "配置文件: ${CONFIG_FILE}"
  echo
else
  CONFIG_FILE="${POSITIONAL_ARGS[0]:-${ALL_SENSOR_CONFIG:-${WORKSPACE_DIR}/config/all_sensor_nodes.yaml}}"
fi

if [[ "${PRESSURE_ENABLED}" == "1" ]]; then
  STARTUP_PROFILE="全部传感器节点"
else
  STARTUP_PROFILE="Baton Mini + GoPro（不含触觉）"
fi

source_setup_file() {
  local setup_file="$1"

  # ROS/ament setup files may read optional unset variables.
  set +u
  # shellcheck source=/dev/null
  source "${setup_file}"
  set -u
}

build_workspace() {
  local build_cmd=(
    colcon build
    --cmake-args
    "-DPython3_EXECUTABLE=${ROS_PYTHON_EXECUTABLE}"
  )

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

    # ROS Jazzy on Ubuntu 24.04 uses system Python 3.12.  An active Conda
    # environment may otherwise make rosidl compile Python 3.13 bindings,
    # which cannot be loaded by rclpy at runtime.
    if [[ ! -x "${ROS_PYTHON_EXECUTABLE}" ]]; then
      echo "ROS Python executable not found: ${ROS_PYTHON_EXECUTABLE}" >&2
      exit 1
    fi

    # Octopus uses a locally installed Qt and may use the workspace-local
    # FFmpeg bundle.  Export their build paths here so a clean CMake cache
    # behaves the same as start_octopus.sh at runtime.
    if [[ -d "${OCTOPUS_QT_ROOT}" ]]; then
      export Qt6_DIR="${Qt6_DIR:-${OCTOPUS_QT_ROOT}/lib/cmake/Qt6}"
      export CMAKE_PREFIX_PATH="${OCTOPUS_QT_ROOT}:${CMAKE_PREFIX_PATH:-}"
      export PATH="${OCTOPUS_QT_ROOT}/bin:${PATH}"
      export LD_LIBRARY_PATH="${OCTOPUS_QT_ROOT}/lib:${LD_LIBRARY_PATH:-}"
    fi

    if [[ -d "${OCTOPUS_FFMPEG_ROOT}" ]]; then
      export FFMPEG_ROOT="${OCTOPUS_FFMPEG_ROOT}"
      export FFMPEG_PATH="${FFMPEG_PATH:-${OCTOPUS_FFMPEG_ROOT}}"
      export CMAKE_PREFIX_PATH="${OCTOPUS_FFMPEG_ROOT}:${CMAKE_PREFIX_PATH:-}"
      export PKG_CONFIG_PATH="${OCTOPUS_FFMPEG_ROOT}/lib/x86_64-linux-gnu/pkgconfig:${PKG_CONFIG_PATH:-}"
      export LD_LIBRARY_PATH="${OCTOPUS_FFMPEG_ROOT}/lib/x86_64-linux-gnu:${LD_LIBRARY_PATH:-}"
      export LIBRARY_PATH="${OCTOPUS_FFMPEG_ROOT}/lib/x86_64-linux-gnu:${LIBRARY_PATH:-}"
    fi

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
if [[ "${SMOKE_TEST}" == "1" ]]; then
  echo "冒烟测试模式：跳过硬件身份映射校验"
  echo
elif [[ "${VALIDATE_HARDWARE_IDENTITY}" == "1" && -f "${HARDWARE_IDENTITY_MAP}" ]]; then
  IDENTITY_ARGS=(
    --identity-map "${HARDWARE_IDENTITY_MAP}"
    --write-identity-resolved "${HARDWARE_IDENTITY_RESOLVED_FILE}"
  )
else
  echo "当前启动模式：跳过硬件身份映射校验"
  echo
fi

STATUS_MODE_ARGS=()
if [[ "${PRESSURE_ENABLED}" == "0" ]]; then
  STATUS_MODE_ARGS+=(--no-pressure --skip-hardware-identity)
fi

"${ROS_PYTHON_EXECUTABLE}" "${STATUS_SCRIPT}" preflight \
  --config "${CONFIG_FILE}" \
  "${STATUS_MODE_ARGS[@]}" \
  "${IDENTITY_ARGS[@]}"

LOG_FILE="${LOG_DIR}/$(date +%Y%m%d_%H%M%S).log"
echo
echo "启动总 launch（${STARTUP_PROFILE}），日志文件: ${LOG_FILE}"
echo "等待 ${STARTUP_WAIT}s 后检查节点和 topic..."

setsid ros2 launch "${WORKSPACE_DIR}/launch/all_sensor_nodes.launch.py" \
  config_file:="${CONFIG_FILE}" \
  identity_resolved_file:="${HARDWARE_IDENTITY_RESOLVED_FILE}" \
  enable_pressure:="${PRESSURE_ENABLED}" \
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
  if [[ "${SMOKE_TEST}" == "1" ]]; then
    wait "${LAUNCH_PID}" 2>/dev/null
    LAUNCH_EXIT=$?
    if [[ "${LAUNCH_EXIT}" -eq 0 ]]; then
      echo
      echo "=== 冒烟测试通过 ==="
      echo "launch 正常完成（无传感器节点需要运行）。"
      echo "脚本流程验证成功。"
      exit 0
    else
      echo
      echo "FAIL 冒烟测试：launch 异常退出 (exit code: ${LAUNCH_EXIT})。最近日志:"
      tail -n 80 "${LOG_FILE}" || true
      exit "${LAUNCH_EXIT}"
    fi
  fi
  echo
  echo "FAIL 总 launch 已提前退出。最近日志:"
  tail -n 80 "${LOG_FILE}" || true
  wait "${LAUNCH_PID}" || true
  exit 1
fi

set +e
"${ROS_PYTHON_EXECUTABLE}" "${STATUS_SCRIPT}" postlaunch \
  --config "${CONFIG_FILE}" \
  "${STATUS_MODE_ARGS[@]}" \
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
