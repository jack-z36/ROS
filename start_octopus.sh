#!/usr/bin/env bash
set -euo pipefail

WORKSPACE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROS_SETUP="${ROS_SETUP:-/opt/ros/jazzy/setup.bash}"
WORKSPACE_SETUP="${WORKSPACE_SETUP:-${WORKSPACE_DIR}/install/setup.bash}"
CONFIGURE_SCANNER="${CONFIGURE_SCANNER:-1}"
OCTOPUS_LOCAL_ONLY="${OCTOPUS_LOCAL_ONLY:-1}"
SCANNER_CONFIG="${SCANNER_CONFIG:-${HOME}/.config/scanner.json}"
MCAP_OUTPUT_DIR="${MCAP_OUTPUT_DIR:-${WORKSPACE_DIR}/mcap}"
OCTOPUS_EXECUTABLE="${OCTOPUS_EXECUTABLE:-${WORKSPACE_DIR}/install/octopus/lib/octopus/octopus}"
QT_ROOT="${QT_ROOT:-${HOME}/Qt/6.11.0/gcc_64}"
FFMPEG_ROOT="${FFMPEG_ROOT:-${WORKSPACE_DIR}/src/VTLA_octopus-master/.deps/ffmpeg8/usr}"

source_setup_file() {
  local setup_file="$1"

  set +u
  # shellcheck source=/dev/null
  source "${setup_file}"
  set -u
}

if [[ ! -f "${ROS_SETUP}" ]]; then
  echo "ROS setup file not found: ${ROS_SETUP}" >&2
  exit 1
fi

if [[ ! -f "${WORKSPACE_SETUP}" ]]; then
  echo "Workspace setup file not found: ${WORKSPACE_SETUP}" >&2
  echo "Build first: cd ${WORKSPACE_DIR} && source ${ROS_SETUP} && colcon build" >&2
  exit 1
fi

if [[ ! -x "${OCTOPUS_EXECUTABLE}" ]]; then
  echo "Octopus executable not found or not executable: ${OCTOPUS_EXECUTABLE}" >&2
  exit 1
fi

source_setup_file "${ROS_SETUP}"
source_setup_file "${WORKSPACE_SETUP}"

if [[ -d "${QT_ROOT}" ]]; then
  export Qt6_DIR="${Qt6_DIR:-${QT_ROOT}/lib/cmake/Qt6}"
  export PATH="${QT_ROOT}/bin:${PATH}"
  export LD_LIBRARY_PATH="${QT_ROOT}/lib:${LD_LIBRARY_PATH:-}"
fi

if [[ -d "${FFMPEG_ROOT}" ]]; then
  export FFMPEG_ROOT
  export FFMPEG_PATH="${FFMPEG_PATH:-${FFMPEG_ROOT}}"
  export PKG_CONFIG_PATH="${FFMPEG_ROOT}/lib/x86_64-linux-gnu/pkgconfig:${PKG_CONFIG_PATH:-}"
  export LD_LIBRARY_PATH="${FFMPEG_ROOT}/lib/x86_64-linux-gnu:${LD_LIBRARY_PATH:-}"
fi

if [[ "${OCTOPUS_LOCAL_ONLY}" == "1" ]]; then
  export ROS_AUTOMATIC_DISCOVERY_RANGE="LOCALHOST"
  export ROS_STATIC_PEERS=""
else
  export ROS_AUTOMATIC_DISCOVERY_RANGE="${ROS_AUTOMATIC_DISCOVERY_RANGE:-SUBNET}"
fi

if [[ "${CONFIGURE_SCANNER}" == "1" ]]; then
  python3 "${WORKSPACE_DIR}/scripts/configure_octopus_scanner.py" \
    --config "${SCANNER_CONFIG}" \
    --recording-path "${MCAP_OUTPUT_DIR}"
fi

ros2 daemon stop >/dev/null 2>&1 || true

if [[ -z "${DISPLAY:-}" && -z "${WAYLAND_DISPLAY:-}" ]]; then
  echo "WARN: DISPLAY/WAYLAND_DISPLAY is empty; Octopus GUI may not open in this shell." >&2
fi

echo "ROS discovery scope: ${ROS_AUTOMATIC_DISCOVERY_RANGE}"
echo "Starting Octopus: ${OCTOPUS_EXECUTABLE}"
exec "${OCTOPUS_EXECUTABLE}"
