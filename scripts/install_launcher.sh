#!/usr/bin/env bash
set -euo pipefail

WORKSPACE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "=== HIT · UMI 无本体数据采集系统 — 安装桌面快捷方式 ==="

# --- 安装 Python GUI 依赖 (customtkinter) ---
# 用 --user 绕过 PEP 668（EXTERNALLY-MANAGED），无需 sudo / --break-system-packages。
# 必须用 /usr/bin/python3（系统 Python 3.12），避免落到 conda 的 python3 3.13。
if ! /usr/bin/python3 -c "import customtkinter" 2>/dev/null; then
  echo "=== 检查 Python GUI 依赖 (customtkinter) ==="
  # --user 落地到 ~/.local/lib/python3.12/site-packages（已在 sys.path）。
  # --break-system-packages：该 pip 版本对 --user 目标也施加 PEP 668 限制，
  # 需显式绕过（仅影响 user site，不污染系统 site-packages）。
  /usr/bin/python3 -m pip install --user --break-system-packages \
    -r "${WORKSPACE_DIR}/scripts/requirements-launcher.txt" || {
    echo "错误：customtkinter 安装失败，界面将无法启动。"
    echo "请检查网络连接后重新运行本脚本。"
    exit 1
  }
else
  echo "=== customtkinter 已安装，跳过依赖安装 ==="
fi

# 设置可执行权限
chmod +x "${WORKSPACE_DIR}/start_act.sh"
chmod +x "${WORKSPACE_DIR}/act-launcher.desktop"
chmod +x "${WORKSPACE_DIR}/scripts/act_launcher_env.sh"
chmod +x "${WORKSPACE_DIR}/scripts/act_launcher.py"

# 安装到应用菜单
mkdir -p "${HOME}/.local/share/applications"
cp "${WORKSPACE_DIR}/act-launcher.desktop" "${HOME}/.local/share/applications/"

# 更新副本中的 Exec 路径（不修改源文件）
sed -i "s|^Exec=.*|Exec=${WORKSPACE_DIR}/start_act.sh|" "${HOME}/.local/share/applications/act-launcher.desktop"

# 安装已去除白边并带透明通道的 UMI 上位机图标。
# .desktop 中 Icon=umi-launcher 会在此解析；可用 LAUNCHER_ICON_SOURCE 覆盖。
ICON_SRC="${LAUNCHER_ICON_SOURCE:-${WORKSPACE_DIR}/assets/umi_launcher_icon_transparent.png}"
if [[ ! -f "${ICON_SRC}" ]]; then
  ICON_SRC="${HOME}/下载/umi上位机图标.png"
fi
if [[ ! -f "${ICON_SRC}" ]]; then
  ICON_SRC="${WORKSPACE_DIR}/assets/umi_launcher_icon.png"
fi
if [[ -f "${ICON_SRC}" ]]; then
  for SIZE in 16 32 48 64 128 256 512; do
    ICON_DIR="${HOME}/.local/share/icons/hicolor/${SIZE}x${SIZE}/apps"
    mkdir -p "${ICON_DIR}"
    /usr/bin/python3 - <<PYEOF
from PIL import Image
img = Image.open("${ICON_SRC}").convert("RGBA")
img = img.resize(($SIZE, $SIZE), Image.LANCZOS)
img.save("${ICON_DIR}/umi-launcher.png")
PYEOF
  done
  echo "  - 应用图标已从 ${ICON_SRC} 安装（umi-launcher）"
fi

# 刷新桌面数据库与图标缓存（如果可用）
if command -v update-desktop-database &>/dev/null; then
  update-desktop-database "${HOME}/.local/share/applications" 2>/dev/null || true
fi
if command -v gtk-update-icon-cache &>/dev/null; then
  gtk-update-icon-cache -f -t "${HOME}/.local/share/icons/hicolor" 2>/dev/null || true
fi

echo "安装完成！"
echo "  - 桌面快捷方式已添加到应用菜单"
echo "  - 在应用列表中搜索「数据采集系统」即可找到"
echo "  - 也可以直接运行：${WORKSPACE_DIR}/start_act.sh"
