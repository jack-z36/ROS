#!/usr/bin/env bash
# 把 vendor 的睿尔曼 libRM_Service.so* 安装到系统库路径并刷新 ld 缓存。
# 用法： sudo bash lib/install_libs.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ "${EUID}" -ne 0 ]]; then
  echo "[install_libs.sh] 需要 root 权限，请用 sudo 运行。" >&2
  exit 1
fi

if ! ls "${SCRIPT_DIR}"/libRM_Service.so* >/dev/null 2>&1; then
  echo "[install_libs.sh] 未在 ${SCRIPT_DIR} 找到 libRM_Service.so*。" >&2
  echo "[install_libs.sh] 请先按 lib/SDK_VENDOR_README.txt 从官方 SDK 拷入库文件。" >&2
  exit 1
fi

DEST="/usr/local/lib"
echo "[install_libs.sh] 拷贝 libRM_Service.so* 到 ${DEST}/ ..."
install -m 0755 "${SCRIPT_DIR}"/libRM_Service.so* "${DEST}/"

echo "[install_libs.sh] 执行 ldconfig ..."
ldconfig

if ldconfig -p | grep -q "libRM_Service.so"; then
  echo "[install_libs.sh] 成功："
  ldconfig -p | grep "libRM_Service.so"
else
  echo "[install_libs.sh] 警告：ldconfig 未列出 libRM_Service.so，检查 /usr/local/lib 是否在搜索路径。" >&2
  exit 1
fi
