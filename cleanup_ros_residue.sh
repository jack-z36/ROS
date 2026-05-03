#!/usr/bin/env bash
set -euo pipefail

WORKSPACE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DRY_RUN=0
SKIP_DAEMON=0
GRACE_SECONDS="${GRACE_SECONDS:-8}"

usage() {
  cat <<EOF
Usage: $(basename "$0") [--dry-run] [--skip-daemon]

Clean leftover ROS processes started by this workspace's all-sensor launch.

Options:
  --dry-run       Only print matched processes.
  --skip-daemon   Do not run "ros2 daemon stop".

Environment:
  GRACE_SECONDS   Seconds to wait after SIGINT/SIGTERM. Default: ${GRACE_SECONDS}
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    --skip-daemon)
      SKIP_DAEMON=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

print_matches() {
  local title="$1"
  shift
  echo
  echo "${title}"
  if [[ "$#" -eq 0 ]]; then
    echo "  none"
    return
  fi
  ps -o pid=,pgid=,stat=,cmd= -p "$@" 2>/dev/null | sed 's/^/  /' || true
}

unique_pids() {
  awk '!seen[$1]++ { print $1 }'
}

all_sensor_launch_pids() {
  pgrep -af "ros2 launch ${WORKSPACE_DIR}/launch/all_sensor_nodes.launch.py|ros2 launch .*/launch/all_sensor_nodes.launch.py" \
    | awk -v self="$$" '$1 != self { print $1 }' \
    | unique_pids
}

all_sensor_child_pids() {
  pgrep -af "baton_mini|v4l2_camera_node|pressure_driver_node" \
    | awk -v self="$$" -v ws="${WORKSPACE_DIR}" '
        $1 == self { next }
        /baton_mini/ && index($0, ws "/install/baton_mini/") { print $1; next }
        /pressure_driver_node/ && index($0, ws "/install/hwk_pressure_driver/") { print $1; next }
        /v4l2_camera_node/ && index($0, ws "/install/gopro_camera_launch/") { print $1; next }
      ' \
    | unique_pids
}

ros_daemon_pids() {
  pgrep -af "ros2-daemon" | awk -v self="$$" '$1 != self { print $1 }' | unique_pids
}

wait_for_exit() {
  local pid
  local deadline=$((SECONDS + GRACE_SECONDS))
  while [[ "${SECONDS}" -lt "${deadline}" ]]; do
    local alive=0
    for pid in "$@"; do
      if kill -0 "${pid}" >/dev/null 2>&1; then
        alive=1
        break
      fi
    done
    [[ "${alive}" -eq 0 ]] && return 0
    sleep 1
  done
  return 1
}

send_to_process_groups() {
  local signal="$1"
  shift
  local pid
  local pgid
  for pid in "$@"; do
    if ! kill -0 "${pid}" >/dev/null 2>&1; then
      continue
    fi
    pgid="$(ps -o pgid= -p "${pid}" 2>/dev/null | tr -d '[:space:]' || true)"
    if [[ -n "${pgid}" ]]; then
      echo "send ${signal} to process group ${pgid} (from pid ${pid})"
      kill "-${signal}" "-${pgid}" >/dev/null 2>&1 || true
    else
      echo "send ${signal} to pid ${pid}"
      kill "-${signal}" "${pid}" >/dev/null 2>&1 || true
    fi
  done
}

send_to_pids() {
  local signal="$1"
  shift
  local pid
  for pid in "$@"; do
    if kill -0 "${pid}" >/dev/null 2>&1; then
      echo "send ${signal} to pid ${pid}"
      kill "-${signal}" "${pid}" >/dev/null 2>&1 || true
    fi
  done
}

mapfile -t launch_pids < <(all_sensor_launch_pids)
mapfile -t child_pids < <(all_sensor_child_pids)
mapfile -t daemon_pids < <(ros_daemon_pids)

print_matches "Matched all-sensor launch processes:" "${launch_pids[@]}"
print_matches "Matched all-sensor child processes:" "${child_pids[@]}"
if [[ "${SKIP_DAEMON}" != "1" ]]; then
  print_matches "Matched ROS daemon processes:" "${daemon_pids[@]}"
fi

if [[ "${DRY_RUN}" == "1" ]]; then
  echo
  echo "Dry run only; no processes were stopped."
  exit 0
fi

if [[ "${#launch_pids[@]}" -gt 0 ]]; then
  echo
  echo "Stopping launch process groups with SIGINT..."
  send_to_process_groups INT "${launch_pids[@]}"
  wait_for_exit "${launch_pids[@]}" || true
fi

mapfile -t child_pids < <(all_sensor_child_pids)
if [[ "${#child_pids[@]}" -gt 0 ]]; then
  echo
  echo "Stopping remaining child processes with SIGTERM..."
  send_to_pids TERM "${child_pids[@]}"
  wait_for_exit "${child_pids[@]}" || true
fi

mapfile -t child_pids < <(all_sensor_child_pids)
if [[ "${#child_pids[@]}" -gt 0 ]]; then
  echo
  echo "Force-stopping remaining child processes with SIGKILL..."
  send_to_pids KILL "${child_pids[@]}"
fi

if [[ "${SKIP_DAEMON}" != "1" ]]; then
  echo
  echo "Stopping ros2 daemon..."
  ros2 daemon stop >/dev/null 2>&1 || true
fi

mapfile -t launch_pids < <(all_sensor_launch_pids)
mapfile -t child_pids < <(all_sensor_child_pids)
mapfile -t daemon_pids < <(ros_daemon_pids)

print_matches "Remaining all-sensor launch processes:" "${launch_pids[@]}"
print_matches "Remaining all-sensor child processes:" "${child_pids[@]}"
if [[ "${SKIP_DAEMON}" != "1" ]]; then
  print_matches "Remaining ROS daemon processes:" "${daemon_pids[@]}"
fi

if [[ "${#launch_pids[@]}" -gt 0 || "${#child_pids[@]}" -gt 0 ]]; then
  echo
  echo "Some matched processes are still alive." >&2
  exit 1
fi

echo
echo "ROS residue cleanup complete."
