#!/usr/bin/env bash

set -euo pipefail

WORKSPACE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Keep one implementation of the sensor startup lifecycle.  The shared entry
# point disables both the pressure launch and the pressure-only identity scan.
export LOG_DIR="${LOG_DIR:-${WORKSPACE_DIR}/log/start_baton_gopro}"
exec bash "${WORKSPACE_DIR}/start_all_sensor.sh" --no-tactile "$@"
