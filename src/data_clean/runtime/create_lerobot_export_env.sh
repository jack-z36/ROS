#!/usr/bin/env bash

set -euo pipefail

# The exporter lock is authoritative; never allow ~/.local packages to shadow
# packages installed in the dedicated environment during setup or preflight.
export PYTHONNOUSERSITE=1

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKTREE_DIR="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
DATA_CLEAN_SOURCE="${WORKTREE_DIR}/src/data_clean"
LEROBOT_SOURCE="${DATA_CLEAN_LEROBOT_SOURCE:-${WORKTREE_DIR}/src/model_deploy/third_party/lerobot}"
ENV_ROOT="${DATA_CLEAN_ENV_ROOT:-/home/hit/.conda-envs}"
TARGET_ENV="${DATA_CLEAN_LEROBOT_ENV:-${ENV_ROOT}/lerobot-export}"
BASE_ENV="${DATA_CLEAN_LEROBOT_BASE_ENV:-/home/hit/miniforge3/envs/lerobot}"
CONDA_BIN="${DATA_CLEAN_CONDA_BIN:-/home/hit/miniforge3/bin/conda}"

if [[ -x "${TARGET_ENV}/bin/python" ]]; then
  if PYTHONPATH="${DATA_CLEAN_SOURCE}:${LEROBOT_SOURCE}/src:${PYTHONPATH:-}" \
    "${TARGET_ENV}/bin/python" -c \
    "from service.lerobot_official_exporter import assert_official_exporter_runtime; assert_official_exporter_runtime()"; then
    echo "Pinned LeRobot exporter environment is already valid: ${TARGET_ENV}"
    exit 0
  fi
  echo "Existing target environment failed the pinned runtime check: ${TARGET_ENV}" >&2
  echo "Move it aside explicitly before recreating; this script will not overwrite environments." >&2
  exit 1
fi

if [[ ! -x "${CONDA_BIN}" ]]; then
  echo "Conda executable not found: ${CONDA_BIN}" >&2
  exit 1
fi
if [[ ! -x "${BASE_ENV}/bin/python" ]]; then
  echo "Clone source environment not found: ${BASE_ENV}" >&2
  exit 1
fi
if [[ ! -f "${LEROBOT_SOURCE}/pyproject.toml" ]]; then
  echo "Pinned in-repository LeRobot source not found: ${LEROBOT_SOURCE}" >&2
  exit 1
fi

"${CONDA_BIN}" create --yes --clone "${BASE_ENV}" --prefix "${TARGET_ENV}"
PIP_BIN="${TARGET_ENV}/bin/pip"
"${PIP_BIN}" install --upgrade \
  --index-url https://download.pytorch.org/whl/cu128 \
  "torch==2.11.0" \
  "torchvision==0.26.0" \
  "torchcodec==0.11.1"
"${PIP_BIN}" install --upgrade \
  "datasets==4.8.5" \
  "numpy==2.2.6" \
  "pyarrow==25.0.0" \
  "av==15.1.0" \
  "opencv-python-headless==4.13.0.92" \
  "mcap==1.3.1" \
  "mcap-ros2-support==0.5.7" \
  "pillow==12.2.0" \
  "huggingface-hub==1.24.0" \
  "imageio==2.37.0" \
  "imageio-ffmpeg==0.6.0" \
  "diffusers==0.35.2" \
  "deepdiff==8.6.1" \
  "pynput==1.8.1" \
  "pyserial==3.5" \
  "rerun-sdk==0.26.2"
"${PIP_BIN}" install --no-deps --editable "${LEROBOT_SOURCE}"

PYTHONPATH="${DATA_CLEAN_SOURCE}:${LEROBOT_SOURCE}/src:${PYTHONPATH:-}" \
  "${TARGET_ENV}/bin/python" -c \
  "from service.lerobot_official_exporter import assert_official_exporter_runtime; print(assert_official_exporter_runtime())"

echo "Created pinned LeRobot exporter environment: ${TARGET_ENV}"
