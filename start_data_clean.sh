#!/usr/bin/env bash

set -euo pipefail

# Keep user-level packages out of the pinned data-clean and LeRobot runtimes.
export PYTHONNOUSERSITE=1

WORKSPACE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_ROOT="${DATA_CLEAN_ENV_ROOT:-/home/hit/.conda-envs}"
CONDA_ENV_DIR="${DATA_CLEAN_CONDA_ENV:-${ENV_ROOT}/data-clean}"
PYTHON_BIN="${DATA_CLEAN_PYTHON:-${CONDA_ENV_DIR}/bin/python}"
SMOKE_CONFIG="${WORKSPACE_DIR}/config/data_clean/data_clean_smoke_test.yaml"
CALIBRATED_CONFIG="${WORKSPACE_DIR}/config/data_clean/data_clean_calibrated.yaml"
if [[ -n "${DATA_CLEAN_CONFIG:-}" ]]; then
  DEFAULT_CONFIG="${DATA_CLEAN_CONFIG}"
  DEFAULT_CONFIG_KIND="environment override"
elif [[ -f "${CALIBRATED_CONFIG}" ]]; then
  DEFAULT_CONFIG="${CALIBRATED_CONFIG}"
  DEFAULT_CONFIG_KIND="calibrated"
else
  DEFAULT_CONFIG="${SMOKE_CONFIG}"
  DEFAULT_CONFIG_KIND="smoke test"
fi
DATA_CLEAN_SOURCE="${WORKSPACE_DIR}/src/data_clean"
LEROBOT_PYTHON="${DATA_CLEAN_LEROBOT_PYTHON:-${ENV_ROOT}/lerobot-export/bin/python}"
WEB_HOST="${DATA_CLEAN_WEB_HOST:-127.0.0.1}"
WEB_PORT="${DATA_CLEAN_WEB_PORT:-0}"
# mcap / mcap-ros2-support are installed into the data-clean conda env from the
# official wheels. Do NOT prepend the in-tree 3rdparty copy under VTLA_octopus:
# that checkout is incomplete (missing mcap/_chunk_builder.py) and would shadow
# the working env install, breaking `from mcap.writer import ...`.
FORGE_SOURCE="${DATA_CLEAN_FORGE_SOURCE:-/home/hit/forge}"
FORGE_VENV="${DATA_CLEAN_FORGE_VENV:-${FORGE_SOURCE}/.venv}"

if [[ -f /opt/ros/jazzy/setup.bash ]]; then
  # shellcheck source=/opt/ros/jazzy/setup.bash
  set +u
  source /opt/ros/jazzy/setup.bash
  set -u
fi

if [[ -f "${WORKSPACE_DIR}/install/setup.bash" ]]; then
  # shellcheck source=/home/hit/ROS/install/setup.bash
  set +u
  source "${WORKSPACE_DIR}/install/setup.bash"
  set -u
fi

usage() {
  cat <<EOF
Usage:
  ./start_data_clean.sh [options]

Examples:
  ./start_data_clean.sh
  ./start_data_clean.sh --cli
  ./start_data_clean.sh --cli --calibrate
  ./start_data_clean.sh --dev
  ./start_data_clean.sh --cli --latest 5
  ./start_data_clean.sh --cli --all --workers auto
  ./start_data_clean.sh --cli --dry-run --latest 5
  ./start_data_clean.sh --cli --input-dir /home/hit/ROS/mcap --output-dir /home/hit/ROS/mcap_cleaned

Environment overrides:
  DATA_CLEAN_ENV_ROOT    Shared environment root. Defaults to /home/hit/.conda-envs.
  DATA_CLEAN_CONFIG       Default config file path.
  DATA_CLEAN_CONDA_ENV    Conda environment directory.
  DATA_CLEAN_PYTHON       Python executable path.
  DATA_CLEAN_LEROBOT_PYTHON
                          Official LeRobot 0.5.2 exporter Python. Defaults to
                          /home/hit/.conda-envs/lerobot-export/bin/python.
  DATA_CLEAN_WEB_HOST     Web bind host. Defaults to 127.0.0.1.
  DATA_CLEAN_WEB_PORT     Web bind port. Defaults to 0 (automatic).
  DATA_CLEAN_FORGE_SOURCE Forge source checkout. Defaults to /home/hit/forge.
  DATA_CLEAN_FORGE_VENV   Forge virtualenv. Defaults to DATA_CLEAN_FORGE_SOURCE/.venv.

Default config:
  ${DEFAULT_CONFIG} (${DEFAULT_CONFIG_KIND})

Config priority:
  --config / DATA_CLEAN_CONFIG > config/data_clean/data_clean_calibrated.yaml > config/data_clean/data_clean_smoke_test.yaml

Notes:
  No arguments starts the local web UI at 127.0.0.1 and opens a browser.
  Use --cli for the legacy terminal cleaning launcher.
  Use --dev for the developer terminal menu.
  The CLI launcher prints a human-readable summary. Set DATA_CLEAN_RAW_JSON=1 to print raw JSON lines.
EOF
}

has_arg() {
  local expected="$1"
  shift
  local arg
  for arg in "$@"; do
    if [[ "${arg}" == "${expected}" || "${arg}" == "${expected}="* ]]; then
      return 0
    fi
  done
  return 1
}

if [[ ! -x "${PYTHON_BIN}" ]]; then
  echo "Data clean Python not found or not executable: ${PYTHON_BIN}" >&2
  echo "Expected conda env: ${CONDA_ENV_DIR}" >&2
  exit 1
fi

if [[ ! -d "${DATA_CLEAN_SOURCE}" ]]; then
  echo "Data clean source directory not found: ${DATA_CLEAN_SOURCE}" >&2
  exit 1
fi

export DATA_CLEAN_FORGE_SOURCE="${FORGE_SOURCE}"
export DATA_CLEAN_FORGE_VENV="${FORGE_VENV}"
export DATA_CLEAN_LEROBOT_PYTHON="${LEROBOT_PYTHON}"

PYTHONPATH_ENTRIES=("${DATA_CLEAN_SOURCE}")
if [[ -d "${FORGE_SOURCE}/forge" ]]; then
  PYTHONPATH_ENTRIES+=("${FORGE_SOURCE}")
fi
export PYTHONPATH="$(IFS=:; echo "${PYTHONPATH_ENTRIES[*]}"):${PYTHONPATH:-}"

if has_arg "--help" "$@" || has_arg "-h" "$@"; then
  usage
  echo
  echo "Legacy CLI help:"
  "${PYTHON_BIN}" -m runtime.mcap_clean_launcher --help
  exit 0
fi

if has_arg "--dev" "$@"; then
  DEV_ARGS=()
  for arg in "$@"; do
    if [[ "${arg}" != "--dev" ]]; then
      DEV_ARGS+=("${arg}")
    fi
  done
  if ! has_arg "--config" "${DEV_ARGS[@]}"; then
    if [[ ! -f "${DEFAULT_CONFIG}" ]]; then
      echo "Default config file not found: ${DEFAULT_CONFIG}" >&2
      echo "Pass a config explicitly: ./start_data_clean.sh --dev --config /path/to/config.yaml" >&2
      exit 1
    fi
    DEV_ARGS=(--config "${DEFAULT_CONFIG}" "${DEV_ARGS[@]}")
  fi
  if [[ "${DATA_CLEAN_RAW_JSON:-0}" != "1" ]]; then
    echo "Data clean developer menu"
    echo "Workspace: ${WORKSPACE_DIR}"
    echo "Python: ${PYTHON_BIN}"
    echo "Default config: ${DEFAULT_CONFIG} (${DEFAULT_CONFIG_KIND})"
    echo
  fi
  exec "${PYTHON_BIN}" -m ui.dev_menu "${DEV_ARGS[@]}"
fi

if ! has_arg "--cli" "$@" && [[ "$#" -gt 0 ]]; then
  echo "Normal mode now starts the local web UI with no extra arguments." >&2
  echo "Use --cli for legacy terminal options, for example: ./start_data_clean.sh --cli --latest 1" >&2
  echo "Use --dev for the developer terminal menu." >&2
  exit 2
fi

ARGS=("$@")
if has_arg "--cli" "${ARGS[@]}"; then
  CLI_ARGS=()
  for arg in "${ARGS[@]}"; do
    if [[ "${arg}" != "--cli" ]]; then
      CLI_ARGS+=("${arg}")
    fi
  done
  ARGS=("${CLI_ARGS[@]}")
fi

if ! has_arg "--config" "${ARGS[@]}"; then
  if [[ ! -f "${DEFAULT_CONFIG}" ]]; then
    echo "Default config file not found: ${DEFAULT_CONFIG}" >&2
    echo "Pass a config explicitly: ./start_data_clean.sh --cli --config /path/to/config.yaml" >&2
    exit 1
  fi
  ARGS=(--config "${DEFAULT_CONFIG}" "${ARGS[@]}")
fi

if [[ "$#" -eq 0 ]]; then
  if [[ ! -x "${LEROBOT_PYTHON}" ]]; then
    echo "Official LeRobot exporter Python not found or not executable: ${LEROBOT_PYTHON}" >&2
    echo "Set DATA_CLEAN_LEROBOT_PYTHON to the pinned LeRobot 0.5.2 environment." >&2
    exit 1
  fi
  if ! "${LEROBOT_PYTHON}" -c \
    "from service.lerobot_official_exporter import assert_official_exporter_runtime; assert_official_exporter_runtime()" \
    >/dev/null; then
    echo "Official LeRobot exporter preflight failed; refusing to start production Web mode." >&2
    exit 1
  fi
  if [[ "${DATA_CLEAN_RAW_JSON:-0}" != "1" ]]; then
    echo "Data clean web UI"
    echo "Workspace: ${WORKSPACE_DIR}"
    echo "Python: ${PYTHON_BIN}"
    echo "LeRobot exporter Python: ${LEROBOT_PYTHON}"
    echo "Default config: ${DEFAULT_CONFIG} (${DEFAULT_CONFIG_KIND})"
    echo
  fi
  exec "${PYTHON_BIN}" -m ui.web_launcher \
    --config "${DEFAULT_CONFIG}" \
    --host "${WEB_HOST}" \
    --port "${WEB_PORT}"
fi

if [[ "${DATA_CLEAN_RAW_JSON:-0}" != "1" ]]; then
  echo "Data clean workspace: ${WORKSPACE_DIR}"
  echo "Python: ${PYTHON_BIN}"
  echo "PYTHONPATH: ${PYTHONPATH}"
  echo "Default config: ${DEFAULT_CONFIG} (${DEFAULT_CONFIG_KIND})"
  echo "Command: ${PYTHON_BIN} -m runtime.mcap_clean_launcher ${ARGS[*]}"
  echo
fi

exec "${PYTHON_BIN}" -m runtime.mcap_clean_launcher "${ARGS[@]}"
