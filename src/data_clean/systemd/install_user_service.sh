#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
USER_UNIT_DIR="${XDG_CONFIG_HOME:-${HOME}/.config}/systemd/user"
UNIT_NAME="data-clean-web.service"

mkdir -p "${USER_UNIT_DIR}"
install -m 0644 "${SCRIPT_DIR}/${UNIT_NAME}" "${USER_UNIT_DIR}/${UNIT_NAME}"
systemctl --user daemon-reload
systemctl --user enable "${UNIT_NAME}"
systemctl --user restart "${UNIT_NAME}"

echo "Installed and started ${UNIT_NAME}."
echo "Logs: journalctl --user -u ${UNIT_NAME} -f"
