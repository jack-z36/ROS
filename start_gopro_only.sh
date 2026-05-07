#!/usr/bin/env bash

set -euo pipefail

WORKSPACE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

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

export ROS_AUTOMATIC_DISCOVERY_RANGE="${ROS_AUTOMATIC_DISCOVERY_RANGE:-LOCALHOST}"
export ROS_STATIC_PEERS="${ROS_STATIC_PEERS:-}"

exec python3 "${WORKSPACE_DIR}/scripts/start_gopro_only.py" "$@"
