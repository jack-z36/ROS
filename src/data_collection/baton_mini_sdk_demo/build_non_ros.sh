#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="${BUILD_DIR:-build_non_ros}"

mkdir -p "${SCRIPT_DIR}/${BUILD_DIR}"
cd "${SCRIPT_DIR}/${BUILD_DIR}"

cmake .. -DUSE_ROS=OFF

# 编译
make

echo "Non-ROS build completed in ${SCRIPT_DIR}/${BUILD_DIR}"
