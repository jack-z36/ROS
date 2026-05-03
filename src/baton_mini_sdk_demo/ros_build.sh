#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"

if [[ "${ROS_VERSION:-}" == "2" ]]; then
    if ! command -v colcon >/dev/null 2>&1; then
        echo "ROS2 environment not found. Please source your ROS2 setup.bash."
        exit 1
    fi

    cd "${WORKSPACE_DIR}"
    colcon build --cmake-args -DUSE_ROS=ON
elif [[ "${ROS_VERSION:-}" == "1" ]]; then
    if ! command -v catkin_make >/dev/null 2>&1; then
        echo "ROS1 environment not found. Please source your ROS1 setup.bash."
        exit 1
    fi

    cd "${WORKSPACE_DIR}"
    if [[ ! -e src/CMakeLists.txt ]]; then
        catkin_init_workspace src
    fi

    catkin_make --cmake-args -DUSE_ROS=ON
else
    echo "ROS_VERSION is not set. Please source a ROS1 or ROS2 setup.bash first."
    exit 1
fi

echo "ROS build completed in ${WORKSPACE_DIR}"
