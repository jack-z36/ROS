#!/usr/bin/env bash
# act_system 一键启动脚本：一条命令拉起 ACT 运行所需的全部节点。
#
# 用法：
#   bash src/model_deploy/act_system/scripts/start_act_system.sh
#
# 可用环境变量：
#   ROS_SETUP=/opt/ros/jazzy/setup.bash   ROS 环境 setup 文件
#   AUTO_BUILD=1                          缺包时自动 colcon build（0 跳过）
#   STARTUP_WAIT=15                       launch 后等待秒数再做组件核对
#   ACT_CONFIG=<path>                     ACT deploy.yaml（默认包内 deploy.yaml）
#   ACT_PYTHON=<path>                     ACT 节点的 Python（默认自动找 model_deploy conda 环境）
#   ENABLE_COMMAND_OUTPUT=0               1 时给 ACT 节点开真实命令输出（默认关，fail-closed）

set -euo pipefail

# 硬件节点与 colcon 构建使用系统 Python（见 src/model_deploy/ENVIRONMENT.md）；
# 前置 /usr/bin 避免 conda base 的 python3 干扰 rclpy/消息绑定。
export PATH="/usr/bin:${PATH}"
# 大图(921KB/帧)走共享内存，避免默认 UDP 分片在 BEST_EFFORT 下成簇丢帧（相机 30Hz 前提）
export FASTDDS_BUILTIN_TRANSPORTS="${FASTDDS_BUILTIN_TRANSPORTS:-LARGE_DATA?max_msg_size=1MB&sockets_size=8MB&non_blocking=true}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# scripts/ -> act_system/ -> model_deploy/ -> src/ -> workspace 根
WORKSPACE_DIR="$(cd "${SCRIPT_DIR}/../../../.." && pwd)"
ROS_SETUP="${ROS_SETUP:-/opt/ros/jazzy/setup.bash}"
WORKSPACE_SETUP="${WORKSPACE_SETUP:-${WORKSPACE_DIR}/install/setup.bash}"
AUTO_BUILD="${AUTO_BUILD:-1}"
STARTUP_WAIT="${STARTUP_WAIT:-15}"
ACT_CONFIG="${ACT_CONFIG:-}"
ACT_PYTHON="${ACT_PYTHON:-}"
ENABLE_COMMAND_OUTPUT="${ENABLE_COMMAND_OUTPUT:-0}"
LOG_DIR="${WORKSPACE_DIR}/log/act_system"
REQUIRED_PACKAGES=(act_interfaces rm65_dual_arm elephant_gripper dual_fisheye_camera act_system)
CLEANING_UP=0

source_setup_file() {
  local setup_file="$1"
  # ROS/ament setup 文件会读取可选的未定义变量
  set +u
  # shellcheck source=/dev/null
  source "${setup_file}"
  set -u
}

if [[ ! -f "${ROS_SETUP}" ]]; then
  echo "FAIL ROS setup 文件不存在: ${ROS_SETUP}" >&2
  exit 1
fi
source_setup_file "${ROS_SETUP}"

# --- 编译检查：缺失的包按需 colcon build ---------------------------------
if [[ -f "${WORKSPACE_SETUP}" ]]; then
  source_setup_file "${WORKSPACE_SETUP}"
fi

MISSING_PACKAGES=()
for pkg in "${REQUIRED_PACKAGES[@]}"; do
  if ! ros2 pkg prefix "${pkg}" >/dev/null 2>&1; then
    MISSING_PACKAGES+=("${pkg}")
  fi
done

# act_interfaces 可用性校验：旧 install 可能用其它 Python 版本编译或缺新消息，
# 导致硬件节点 import/typesupport 失败；不可用时强制重编。
if [[ ! " ${MISSING_PACKAGES[*]-} " == *" act_interfaces "* ]]; then
  if ! python3 -c "from rosidl_generator_py.import_type_support_impl import import_type_support; import_type_support('act_interfaces'); from act_interfaces.msg import CommandPermit, GripperHealth, HardwareHealth" >/dev/null 2>&1; then
    echo "act_interfaces 安装不可用（Python 版本不匹配或消息缺失），将重新编译。"
    MISSING_PACKAGES+=("act_interfaces")
  fi
fi

if [[ ${#MISSING_PACKAGES[@]} -gt 0 ]]; then
  if [[ "${AUTO_BUILD}" == "1" ]]; then
    if ! command -v colcon >/dev/null 2>&1; then
      echo "FAIL 缺少包 ${MISSING_PACKAGES[*]} 且找不到 colcon，请手动编译后重试。" >&2
      exit 1
    fi
    echo "检测到未编译的包: ${MISSING_PACKAGES[*]}"
    # --base-paths src：只扫 src/，避免 worktrees/ 里的同名包冲突
    # --cmake-clean-cache：丢弃旧 CMake 缓存（可能记录了 conda Python）
    # -DPython3_EXECUTABLE：CMake FindPython3 默认按版本优先，会选中 conda 的更高
    # 版本 Python（如 3.13），必须显式钉死系统 Python
    SYSTEM_PYTHON="$(command -v python3)"
    echo "开始编译: colcon build --base-paths src --cmake-clean-cache --packages-select ${MISSING_PACKAGES[*]} (Python: ${SYSTEM_PYTHON})"
    (
      cd "${WORKSPACE_DIR}"
      colcon build --base-paths src --cmake-clean-cache \
        --packages-select "${MISSING_PACKAGES[@]}" \
        --cmake-args "-DPython3_EXECUTABLE=${SYSTEM_PYTHON}"
    )
  else
    echo "FAIL 缺少包: ${MISSING_PACKAGES[*]}（AUTO_BUILD=0，已跳过自动编译）" >&2
    echo "请手动执行: cd ${WORKSPACE_DIR} && colcon build --base-paths src --packages-select ${MISSING_PACKAGES[*]}" >&2
    exit 1
  fi
fi

if [[ ! -f "${WORKSPACE_SETUP}" ]]; then
  echo "FAIL 编译后仍找不到 workspace setup: ${WORKSPACE_SETUP}" >&2
  exit 1
fi
source_setup_file "${WORKSPACE_SETUP}"

# --- 启动总 launch ---------------------------------------------------------
mkdir -p "${LOG_DIR}"
LOG_FILE="${LOG_DIR}/$(date +%Y%m%d_%H%M%S).log"

# ACT 节点需要 torch（model_deploy conda 环境，见 src/model_deploy/requirements.txt）；
# 未显式指定 ACT_PYTHON 时自动探测常见 conda 安装位置，找不到则回退系统 python3。
if [[ -z "${ACT_PYTHON}" ]]; then
  for cand in \
    "${HOME}/miniforge3/envs/model_deploy/bin/python3" \
    "${HOME}/miniconda3/envs/model_deploy/bin/python3" \
    "${HOME}/anaconda3/envs/model_deploy/bin/python3"; do
    if [[ -x "${cand}" ]]; then
      ACT_PYTHON="${cand}"
      break
    fi
  done
fi
ACT_PYTHON="${ACT_PYTHON:-python3}"
echo "ACT 节点 Python: ${ACT_PYTHON}"

LAUNCH_ARGS=("act_python:=${ACT_PYTHON}")
if [[ -n "${ACT_CONFIG}" ]]; then
  LAUNCH_ARGS+=("act_config:=${ACT_CONFIG}")
fi
if [[ "${ENABLE_COMMAND_OUTPUT}" == "1" ]]; then
  LAUNCH_ARGS+=("enable_command_output:=true")
fi

echo
echo "启动 act_system 总 launch，日志文件: ${LOG_FILE}"
echo "等待 ${STARTUP_WAIT}s 后核对各组件节点..."

setsid ros2 launch act_system act_system.launch.py "${LAUNCH_ARGS[@]}" \
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
    echo "停止 act_system launch..."
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
  tail -n 60 "${LOG_FILE}" || true
  wait "${LAUNCH_PID}" || true
  exit 1
fi

# --- 组件核对：按节点名逐组件报告 OK/FAIL -----------------------------------
# 不依赖 ros2 daemon 缓存；daemon 被显式停止后也必须发现当前运行图。
NODE_LIST="$(ros2 node list --no-daemon --spin-time 5 2>/dev/null || true)"

check_component() {
  local label="$1"
  shift
  local missing=()
  for node in "$@"; do
    if ! grep -qx "${node}" <<<"${NODE_LIST}"; then
      missing+=("${node}")
    fi
  done
  if [[ ${#missing[@]} -eq 0 ]]; then
    echo "OK   ${label}"
    return 0
  fi
  echo "FAIL ${label}（缺少节点: ${missing[*]}）"
  return 1
}

echo
echo "===== act_system 组件启动核对 ====="
FAILED=0
check_component "RM65 双臂节点"   "/rm65_dual_arm_node" || FAILED=1
check_component "大象夹爪节点"     "/elephant_gripper_node" || FAILED=1
check_component "双鱼眼相机节点"   "/dual_fisheye_left/left_fisheye_camera" \
                                   "/dual_fisheye_right/right_fisheye_camera" \
                                   "/camera_health_node" || FAILED=1
check_component "ACT 部署节点"     "/act_deploy_node" || FAILED=1
echo "==================================="

if [[ "${FAILED}" == "1" ]]; then
  echo
  echo "存在启动失败的组件，最近 launch 日志:"
  tail -n 60 "${LOG_FILE}" || true
  echo
  echo "完整日志: ${LOG_FILE}"
fi

echo
echo "launch 仍在运行。按 Ctrl+C 停止全部节点。"
wait "${LAUNCH_PID}"
