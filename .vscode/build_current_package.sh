#!/usr/bin/env bash

set -eo pipefail

active_path="${1:-}"

if [[ -z "${active_path}" ]]; then
    echo "Usage: $0 <active-file-or-directory>"
    exit 1
fi

if [[ -d "${active_path}" ]]; then
    search_dir="$(readlink -f "${active_path}")"
else
    search_dir="$(dirname "$(readlink -f "${active_path}")")"
fi

find_package_dir() {
    local dir="$1"

    while [[ "${dir}" != "/" ]]; do
        if [[ -f "${dir}/package.xml" ]]; then
            readlink -f "${dir}"
            return 0
        fi
        dir="$(dirname "${dir}")"
    done

    return 1
}

find_workspace_root() {
    local package_dir="$1"
    local dir="${package_dir}"

    while [[ "${dir}" != "/" ]]; do
        if [[ "$(basename "$(dirname "${dir}")")" == "src" ]]; then
            echo "$(dirname "$(dirname "${dir}")")"
            return 0
        fi
        dir="$(dirname "${dir}")"
    done

    return 1
}

extract_package_name() {
    local package_xml="$1"
    sed -n 's:.*<name>\(.*\)</name>.*:\1:p' "${package_xml}" | head -n 1
}

package_dir="$(find_package_dir "${search_dir}" || true)"

if [[ -z "${package_dir}" ]]; then
    echo "No ROS package found from: ${active_path}"
    exit 1
fi

workspace_root="$(find_workspace_root "${package_dir}" || true)"

if [[ -z "${workspace_root}" ]]; then
    echo "Could not determine workspace root for package: ${package_dir}"
    exit 1
fi

package_name="$(extract_package_name "${package_dir}/package.xml")"

if [[ -z "${package_name}" ]]; then
    echo "Could not read package name from: ${package_dir}/package.xml"
    exit 1
fi

set +u
source /opt/ros/jazzy/setup.bash
set -u
cd "${workspace_root}"

echo "Workspace: ${workspace_root}"
echo "Package:   ${package_name}"

colcon build --packages-select "${package_name}" --cmake-args -DUSE_ROS=ON
