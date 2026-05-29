#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
CALL_DIR="$(pwd -P)"

fail() {
  echo "[init:data-clean] ERROR: $*" >&2
  exit 1
}

info() {
  echo "[init:data-clean] $*"
}

usage() {
  cat <<'EOF'
Usage:
  bash scripts/init_data_clean_dev.sh [--full]

Purpose:
  Lightweight Stage 2 data-clean development preflight for Ubuntu L3 execution.

Notes:
  Default mode does not install dependencies, run rosdep, run colcon build, or execute heavy data flows.
  --full is reserved for future heavier checks and currently runs the same lightweight checks.
EOF
}

FULL=0
for arg in "$@"; do
  case "${arg}" in
    --full)
      FULL=1
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      fail "Unknown argument: ${arg}"
      ;;
  esac
done

if [[ "${CALL_DIR}" != "${REPO_ROOT}" ]]; then
  fail "Run this preflight from repository root: ${REPO_ROOT}"
fi

cd "${REPO_ROOT}"

info "Repository root: ${REPO_ROOT}"

[[ -d ".git" ]] || fail "Current script is not inside a Git repository root: ${REPO_ROOT}"
[[ -f "start_data_clean.sh" ]] || fail "Missing start_data_clean.sh at repository root"
[[ -x "start_data_clean.sh" ]] || fail "start_data_clean.sh exists but is not executable"
[[ -d "src/data_clean" ]] || fail "Missing src/data_clean"

if [[ -z "${BASH_VERSION:-}" ]]; then
  fail "This preflight must run under bash"
fi

if [[ "$(uname -s)" != "Linux" ]]; then
  fail "This preflight is for Ubuntu/Linux execution, not $(uname -s)"
fi

if [[ -f "/etc/os-release" ]]; then
  # shellcheck source=/dev/null
  source /etc/os-release
  if [[ "${ID:-}" != "ubuntu" ]]; then
    fail "Expected Ubuntu environment; detected ID=${ID:-unknown}"
  fi
else
  fail "Cannot verify Ubuntu environment: /etc/os-release not found"
fi

command -v git >/dev/null 2>&1 || fail "git command not found"
command -v python3 >/dev/null 2>&1 || fail "python3 command not found"

CURRENT_BRANCH="$(git symbolic-ref --quiet --short HEAD || true)"
[[ -n "${CURRENT_BRANCH}" ]] || fail "Cannot determine current Git branch"

case "${CURRENT_BRANCH}" in
  runtime-mvp|service-s1|service-s2|service-s3|service-s4|service-s5)
    info "Git branch OK: ${CURRENT_BRANCH}"
    ;;
  debug-common_frame|debug：common_frame)
    info "Git branch OK (debug): ${CURRENT_BRANCH}"
    ;;
  main)
    fail "Do not execute Stage 2 L3 tasks on main"
    ;;
  *)
    fail "Unexpected Stage 2 execution branch: ${CURRENT_BRANCH}"
    ;;
esac

CONDA_ENV_DIR="${DATA_CLEAN_CONDA_ENV:-${REPO_ROOT}/src/data_clean/.conda-envs/data-clean}"
PYTHON_BIN="${DATA_CLEAN_PYTHON:-${CONDA_ENV_DIR}/bin/python}"

[[ -x "${PYTHON_BIN}" ]] || fail "Data clean Python not found or not executable: ${PYTHON_BIN}"

SMOKE_CONFIG="${REPO_ROOT}/config/data_clean/data_clean_smoke_test.yaml"
CALIBRATED_CONFIG="${REPO_ROOT}/config/data_clean/data_clean_calibrated.yaml"

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

[[ -f "${DEFAULT_CONFIG}" ]] || fail "Default data clean config not found: ${DEFAULT_CONFIG}"
info "Default config OK: ${DEFAULT_CONFIG} (${DEFAULT_CONFIG_KIND})"

DATA_CLEAN_SOURCE="${REPO_ROOT}/src/data_clean"
export PYTHONPATH="${DATA_CLEAN_SOURCE}:${PYTHONPATH:-}"

"${PYTHON_BIN}" - <<'PY'
import importlib

modules = [
    "runtime.mcap_clean_launcher",
    "runtime.runtime_init",
    "schemas.runtime_context",
    "repo.config.runtime_config_loader",
]

for module in modules:
    importlib.import_module(module)

print("Python imports OK")
PY

DATA_CLEAN_RAW_JSON=1 "${REPO_ROOT}/start_data_clean.sh" --help >/dev/null
info "start_data_clean.sh --help OK"

if [[ "${FULL}" == "1" ]]; then
  info "--full requested: no additional heavy checks are defined yet"
fi

info "Data clean dev environment OK"
