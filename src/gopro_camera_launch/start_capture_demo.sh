#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

ROS_SETUP_DEFAULT="${HOME}/ros2_ws/install/setup.bash"
LOCAL_SETUP_CANDIDATE_1="${REPO_DIR}/install/setup.bash"
LOCAL_SETUP_CANDIDATE_2="$(cd "${REPO_DIR}/.." && pwd)/install/setup.bash"

VIDEO_DEVICE="${VIDEO_DEVICE:-/dev/video4}"

print_help() {
  cat <<'EOF'
Usage:
  ./start_capture_demo.sh <command>

Commands:
  build       Build the ROS 2 package with colcon
  run         Launch only the GoPro camera node
  verify      Print common verification commands

Optional environment variables:
  VIDEO_DEVICE      Default: /dev/video4

Examples:
  ./start_capture_demo.sh build
  ./start_capture_demo.sh run
  VIDEO_DEVICE=/dev/video4 ./start_capture_demo.sh run
EOF
}

source_ros_env() {
  if [[ -f "${LOCAL_SETUP_CANDIDATE_1}" ]]; then
    # Typical workspace layout when this repository is the workspace root.
    # shellcheck disable=SC1090
    source "${LOCAL_SETUP_CANDIDATE_1}"
    return
  fi

  if [[ -f "${LOCAL_SETUP_CANDIDATE_2}" ]]; then
    # Typical workspace layout when this repository lives under src/.
    # shellcheck disable=SC1090
    source "${LOCAL_SETUP_CANDIDATE_2}"
    return
  fi

  if [[ -f "${ROS_SETUP_DEFAULT}" ]]; then
    # shellcheck disable=SC1090
    source "${ROS_SETUP_DEFAULT}"
    return
  fi

  echo "Could not find a ROS 2 setup.bash. Please source your workspace manually."
  exit 1
}

build_package() {
  source_ros_env
  cd "${REPO_DIR}"
  colcon build --packages-select gopro_camera_launch
}

run_capture() {
  source_ros_env
  cd "${REPO_DIR}"
  ros2 launch gopro_camera_launch gopro_pose_record.launch.py \
    video_device:="${VIDEO_DEVICE}" \
    publish_camera_info:=true
}

verify_commands() {
  cat <<EOF
Run these commands in another terminal after the launch is up:

  source /path/to/your/workspace/install/setup.bash
  ros2 topic list
  ros2 topic hz /gopro/image_raw
  ros2 topic echo /gopro/camera_info --once

Expected topics include:
  /gopro/image_raw
  /gopro/camera_info
EOF
}

COMMAND="${1:-help}"

case "${COMMAND}" in
  build)
    build_package
    ;;
  run)
    run_capture
    ;;
  verify)
    verify_commands
    ;;
  help|-h|--help)
    print_help
    ;;
  *)
    echo "Unknown command: ${COMMAND}"
    print_help
    exit 1
    ;;
esac
