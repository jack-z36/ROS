#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
CONFIG_PATH="${PROJECT_DIR}/train/config/lora.yaml"
PYTHON_BIN="${PYTHON_BIN:-python}"
EXTRA_ARGS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --config)
      if [[ $# -lt 2 ]]; then
        printf 'ERROR: --config requires a path argument\n' >&2
        exit 2
      fi
      CONFIG_PATH="$2"
      shift 2
      ;;
    --config=*)
      CONFIG_PATH="${1#--config=}"
      shift
      ;;
    *)
      EXTRA_ARGS+=("$1")
      shift
      ;;
  esac
done

# Keep user-site packages such as ~/.local/lib/python3.12/site-packages from
# shadowing the active conda environment. This avoids version conflicts like
# huggingface-hub>=1.0 being imported ahead of the env's transformers-compatible
# huggingface-hub<1.0.
export PYTHONNOUSERSITE="${PYTHONNOUSERSITE:-1}"

PYTHONPATH_ENTRIES=(
  "${PROJECT_DIR}/common/src"
  "${PROJECT_DIR}/train/src"
  "${PROJECT_DIR}/deploy/src"
)

for CANDIDATE in   "${PROJECT_DIR}/third_party/lerobot/src"   "${PROJECT_DIR}/../third_party/lerobot/src"   "${PROJECT_DIR}/../../third_party/lerobot/src"
do
  if [[ -d "${CANDIDATE}" ]]; then
    PYTHONPATH_ENTRIES+=("${CANDIDATE}")
    break
  fi
done

export PYTHONPATH="$(IFS=:; printf '%s' "${PYTHONPATH_ENTRIES[*]}")${PYTHONPATH:+:${PYTHONPATH}}"

CMD=(
  "${PYTHON_BIN}"
  -m
  pi05.train.cli.train
  --config
  "${CONFIG_PATH}"
)

if [[ ${#EXTRA_ARGS[@]} -gt 0 ]]; then
  CMD+=("${EXTRA_ARGS[@]}")
fi

printf 'Launching PI05 trainer with config %s\n' "${CONFIG_PATH}"
"${CMD[@]}"
