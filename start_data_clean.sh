#!/usr/bin/env bash

set -euo pipefail

WORKSPACE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONDA_ENV_DIR="${DATA_CLEAN_CONDA_ENV:-${WORKSPACE_DIR}/src/data_clean/.conda-envs/data-clean}"
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
MCAP_PYTHON_SOURCE="${WORKSPACE_DIR}/src/VTLA_octopus-master/octopus/3rdparty/mcap/python/mcap"
MCAP_ROS2_SOURCE="${WORKSPACE_DIR}/src/VTLA_octopus-master/octopus/3rdparty/mcap/python/mcap-ros2-support"

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
  ./start_data_clean.sh --calibrate
  ./start_data_clean.sh --dev
  ./start_data_clean.sh --latest 5
  ./start_data_clean.sh --all --workers auto
  ./start_data_clean.sh --dry-run --latest 5
  ./start_data_clean.sh --input-dir /home/hit/ROS/mcap --output-dir /home/hit/ROS/mcap_cleaned

Environment overrides:
  DATA_CLEAN_CONFIG       Default config file path.
  DATA_CLEAN_CONDA_ENV    Conda environment directory.
  DATA_CLEAN_PYTHON       Python executable path.

Default config:
  ${DEFAULT_CONFIG} (${DEFAULT_CONFIG_KIND})

Config priority:
  --config / DATA_CLEAN_CONFIG > config/data_clean/data_clean_calibrated.yaml > config/data_clean/data_clean_smoke_test.yaml

Notes:
  The script prints a human-readable summary. Set DATA_CLEAN_RAW_JSON=1 to print raw JSON lines.
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

PYTHONPATH_ENTRIES=("${DATA_CLEAN_SOURCE}")
if [[ -d "${MCAP_PYTHON_SOURCE}" ]]; then
  PYTHONPATH_ENTRIES+=("${MCAP_PYTHON_SOURCE}")
fi
if [[ -d "${MCAP_ROS2_SOURCE}" ]]; then
  PYTHONPATH_ENTRIES+=("${MCAP_ROS2_SOURCE}")
fi
export PYTHONPATH="$(IFS=:; echo "${PYTHONPATH_ENTRIES[*]}"):${PYTHONPATH:-}"

if has_arg "--help" "$@" || has_arg "-h" "$@"; then
  usage
  echo
  exec "${PYTHON_BIN}" -m runtime.mcap_clean_launcher --help
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

ARGS=("$@")
if ! has_arg "--config" "${ARGS[@]}"; then
  if [[ ! -f "${DEFAULT_CONFIG}" ]]; then
    echo "Default config file not found: ${DEFAULT_CONFIG}" >&2
    echo "Pass a config explicitly: ./start_data_clean.sh --config /path/to/config.yaml" >&2
    exit 1
  fi
  ARGS=(--config "${DEFAULT_CONFIG}" "${ARGS[@]}")
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
