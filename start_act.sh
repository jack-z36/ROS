#!/usr/bin/env bash
set -euo pipefail

WORKSPACE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 确保不激活 conda（避免 Python 版本冲突）
if command -v conda &>/dev/null; then
  conda deactivate 2>/dev/null || true
fi

# 检查 DISPLAY 环境变量
if [[ -z "${DISPLAY:-}" ]]; then
  echo "错误：未检测到图形环境（DISPLAY 未设置）。"
  echo "请在图形桌面环境下运行此脚本。"
  exit 1
fi

# 检查工作区是否已编译
if [[ ! -f "${WORKSPACE_DIR}/install/setup.bash" ]]; then
  echo "错误：工作区未编译。请先运行："
  echo "  cd ${WORKSPACE_DIR} && colcon build"
  exit 1
fi

exec /usr/bin/python3 "${WORKSPACE_DIR}/scripts/act_launcher.py"
