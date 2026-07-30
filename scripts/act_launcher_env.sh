#!/usr/bin/env bash
# ACT 数据采集系统 — 环境引导脚本
# 被 act_launcher.py 以 subprocess 调用，输出完整环境变量

set -eo pipefail

# 退出 conda（避免 Python 版本冲突）
if [[ -n "${CONDA_PREFIX:-}" ]]; then
  eval "$(conda deactivate 2>/dev/null)" || true
fi

# ROS2 环境
source /opt/ros/jazzy/setup.bash

# 工作区
WORKSPACE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "${WORKSPACE_DIR}/install/setup.bash"

# ROS2 本地发现
export ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST

# Qt 6.11.0 路径（Octopus 运行时依赖）
export QT_ROOT="$HOME/Qt/6.11.0/gcc_64"
export Qt6_DIR="${QT_ROOT}/lib/cmake/Qt6"
export PATH="${QT_ROOT}/bin:${PATH}"
export LD_LIBRARY_PATH="${QT_ROOT}/lib:${LD_LIBRARY_PATH:-}"

# 输出完整环境供 Python 解析
exec env
