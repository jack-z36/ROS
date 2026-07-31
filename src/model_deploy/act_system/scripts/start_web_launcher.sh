#!/usr/bin/env bash
# ACT Web 控制中心启动脚本：拉起外层 web_launcher（浏览器控制面板）。
#
# web_launcher 本身是常驻 Web 服务，不直接做 ROS/spin，但它会用 subprocess
# 启停 act_deploy_node 子进程。子进程通过 env=os.environ.copy() 继承本脚本
# 所在 shell 的环境，因此必须在此 source 好 ROS / DDS 环境——否则子进程会
# 因缺 ROS_DISTRO 或 FASTDDS_BUILTIN_TRANSPORTS 而启动失败（与 start_act_system.sh
# 的环境要求一致）。
#
# 用法：
#   bash src/model_deploy/act_system/scripts/start_web_launcher.sh
#
# 可用环境变量：
#   ROS_SETUP=/opt/ros/jazzy/setup.bash   ROS 环境 setup 文件
#   ACT_CONFIG=<path>                     ACT deploy.yaml（默认包内 deploy.yaml）
#   ACT_PYTHON=<path>                     web_launcher 的 Python（默认自动找
#                                         model_deploy conda 环境，需含 torch/uvicorn）
#   WEB_PORT=8080                         Web 服务端口
#   WEB_HOST=0.0.0.0                      Web 服务监听地址
#   AUTO_START=0                          1 时启动即自动运行推理进程
#   MODE=dry-run                          初始模式（dry-run / real-run）

set -euo pipefail

# 硬件节点与 colcon 构建使用系统 Python（见 src/model_deploy/ENVIRONMENT.md）；
# 前置 /usr/bin 避免 conda base 的 python3 干扰 rclpy/消息绑定。
export PATH="/usr/bin:${PATH}"
# 大图走共享内存，避免默认 UDP 分片在 BEST_EFFORT 下成簇丢帧（相机 30Hz 前提）。
# 与 start_act_system.sh 保持一致：web_launcher 拉起的 act_deploy_node 子进程
# 同样要订阅相机大图，必须继承相同的 DDS 传输参数。
export FASTDDS_BUILTIN_TRANSPORTS="${FASTDDS_BUILTIN_TRANSPORTS:-LARGE_DATA?max_msg_size=1MB&sockets_size=8MB&non_blocking=true}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# scripts/ -> act_system/ -> model_deploy/ -> src/ -> workspace 根
WORKSPACE_DIR="$(cd "${SCRIPT_DIR}/../../../.." && pwd)"
ROS_SETUP="${ROS_SETUP:-/opt/ros/jazzy/setup.bash}"
WORKSPACE_SETUP="${WORKSPACE_SETUP:-${WORKSPACE_DIR}/install/setup.bash}"
ACT_CONFIG="${ACT_CONFIG:-}"
ACT_PYTHON="${ACT_PYTHON:-}"
WEB_PORT="${WEB_PORT:-8080}"
WEB_HOST="${WEB_HOST:-0.0.0.0}"
AUTO_START="${AUTO_START:-0}"
MODE="${MODE:-dry-run}"

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

# workspace install 提供 act_interfaces 等消息绑定；缺则警告但不阻断
# （web_launcher 自身不强依赖它，但 act_deploy_node 子进程需要）。
if [[ -f "${WORKSPACE_SETUP}" ]]; then
  source_setup_file "${WORKSPACE_SETUP}"
else
  echo "WARN workspace 未编译（${WORKSPACE_SETUP} 不存在），act_deploy_node 子进程可能无法 import act_interfaces。" >&2
fi

# 默认 ACT 配置：act 包内 deploy.yaml
if [[ -z "${ACT_CONFIG}" ]]; then
  ACT_CONFIG="${SCRIPT_DIR}/../../act/config_files/deploy.yaml"
fi
if [[ ! -f "${ACT_CONFIG}" ]]; then
  echo "FAIL ACT 配置不存在: ${ACT_CONFIG}" >&2
  exit 1
fi

# 一个 Web 控制中心独占一个端口。若旧 launcher 仍在运行，直接再启动一个新
# launcher 只会得到 uvicorn 的 Errno 98；新进程也无法接管旧 launcher 管理的
# ROS 进程组。提前失败并保留旧进程，避免制造“网页显示停止、节点仍在运行”的
# 误导状态。
if command -v ss >/dev/null 2>&1; then
  if ss -ltn "sport = :${WEB_PORT}" | awk 'NR > 1 { found = 1 } END { exit !found }'; then
    echo "FAIL Web 端口 ${WEB_PORT} 已被占用。请复用已有控制中心，或先停止旧的 web_launcher。" >&2
    exit 1
  fi
fi

# web_launcher 需要 torch / uvicorn / fastapi 等（model_deploy conda 环境）。
# 探测逻辑与 start_act_system.sh 一致；找不到则回退系统 python3。
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

# act 包位于 src/model_deploy，需要把 src/ 加进 sys.path（web_launcher.main 内部
# 也会补，这里双保险）。
SRC_DIR="${WORKSPACE_DIR}/src"
export PYTHONPATH="${SRC_DIR}${PYTHONPATH:+:${PYTHONPATH}}"

LAUNCH_ARGS=(
  -m model_deploy.act.ui.web_launcher
  --config "${ACT_CONFIG}"
  --port "${WEB_PORT}"
  --host "${WEB_HOST}"
  --mode "${MODE}"
)
if [[ "${AUTO_START}" == "1" ]]; then
  LAUNCH_ARGS+=(--auto-start)
fi

echo "ACT Web 控制中心"
echo "  Python : ${ACT_PYTHON}"
echo "  配置   : ${ACT_CONFIG}"
echo "  监听   : http://${WEB_HOST}:${WEB_PORT}"
echo "  模式   : ${MODE}（AUTO_START=${AUTO_START}）"
echo

# web_launcher 常驻前台。Ctrl+C 会触发 FastAPI shutdown handler，由它向自己
# 管理的独立 launch 进程组发送 SIGINT，确保 ROS 子节点不会残留。
exec "${ACT_PYTHON}" "${LAUNCH_ARGS[@]}"
