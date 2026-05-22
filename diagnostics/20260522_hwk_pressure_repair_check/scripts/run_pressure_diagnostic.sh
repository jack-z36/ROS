#!/usr/bin/env bash
set -u

WORKSPACE_DIR="/home/hit/ROS"
TEST_DIR="/home/hit/ROS/diagnostics/20260522_hwk_pressure_repair_check"
LOG_DIR="${TEST_DIR}/logs"
SNAPSHOT_DIR="${TEST_DIR}/snapshots"
SUMMARY_FILE="${TEST_DIR}/SUMMARY.md"
PRESSURE_CONFIG="${WORKSPACE_DIR}/src/hwk_pressure_driver/config/pressure_sensors.yaml"
IDENTITY_MAP="${WORKSPACE_DIR}/config/hardware_identity_map.yaml"
ROS_SETUP="${ROS_SETUP:-/opt/ros/jazzy/setup.bash}"
WORKSPACE_SETUP="${WORKSPACE_SETUP:-${WORKSPACE_DIR}/install/setup.bash}"
STARTUP_WAIT="${STARTUP_WAIT:-12}"

TOPICS=(
  "/pressure/left_hand/gripper_1"
  "/pressure/left_hand/gripper_2"
  "/pressure/right_hand/gripper_1"
  "/pressure/right_hand/gripper_2"
)

mkdir -p "${LOG_DIR}" "${SNAPSHOT_DIR}" "${LOG_DIR}/ros_log"

reset_outputs() {
  find "${LOG_DIR}" -mindepth 1 -maxdepth 1 -exec rm -rf {} +
  find "${SNAPSHOT_DIR}" -mindepth 1 -maxdepth 1 -exec rm -rf {} +
  mkdir -p "${LOG_DIR}/ros_log"
}

timestamp() {
  date "+%Y-%m-%d %H:%M:%S %z"
}

write_header() {
  {
    echo "# HWK Pressure Repair Diagnostic Summary"
    echo
    echo "- Started: $(timestamp)"
    echo "- Workspace: ${WORKSPACE_DIR}"
    echo "- Test directory: ${TEST_DIR}"
    echo "- Pressure config: ${PRESSURE_CONFIG}"
    echo "- Identity map: ${IDENTITY_MAP}"
    echo
  } > "${SUMMARY_FILE}"
}

append_summary() {
  printf '%s\n' "$*" >> "${SUMMARY_FILE}"
}

run_capture() {
  local name="$1"
  shift
  local outfile="${SNAPSHOT_DIR}/${name}.txt"
  {
    echo "$ $*"
    echo
    "$@"
  } > "${outfile}" 2>&1
  local status=$?
  echo "${status}" > "${SNAPSHOT_DIR}/${name}.status"
  return 0
}

run_shell_capture() {
  local name="$1"
  local cmd="$2"
  local outfile="${SNAPSHOT_DIR}/${name}.txt"
  {
    echo "$ ${cmd}"
    echo
    bash -lc "${cmd}"
  } > "${outfile}" 2>&1
  local status=$?
  echo "${status}" > "${SNAPSHOT_DIR}/${name}.status"
  return 0
}

source_setup_file() {
  local setup_file="$1"
  if [ ! -f "${setup_file}" ]; then
    return 1
  fi
  set +u
  # shellcheck source=/dev/null
  source "${setup_file}"
  set -u
  return 0
}

collect_static_snapshots() {
  run_capture lsusb lsusb
  run_shell_capture tty_nodes "ls -l /dev/ttyUSB* /dev/ttyACM* /dev/hwk_pressure_* 2>/dev/null || true"
  run_shell_capture serial_by_path "find /dev/serial/by-path -maxdepth 1 -type l -printf '%p -> %l\n' 2>/dev/null | sort || true"
  run_shell_capture serial_by_id "find /dev/serial/by-id -maxdepth 1 -type l -printf '%p -> %l\n' 2>/dev/null | sort || true"
  run_shell_capture udev_tty "for dev in /dev/ttyUSB* /dev/ttyACM*; do [ -e \"\$dev\" ] || continue; echo \"===== \$dev =====\"; udevadm info -q property -n \"\$dev\"; echo; done"
  run_shell_capture kernel_usb_today "journalctl -k --since today --no-pager 2>/dev/null | grep -Ei 'ch341|ttyUSB|ttyACM|1a86|device descriptor|over-current|unable to enumerate|USB disconnect' | tail -n 120 || true"
}

run_existing_diagnostics() {
  run_capture hwk_pressure_usb_recover "${WORKSPACE_DIR}/scripts/hwk_pressure_usb_recover.sh"
  run_capture hardware_identity_validate python3 "${WORKSPACE_DIR}/scripts/hardware_identity_scan.py" validate --map "${IDENTITY_MAP}" --write-resolved "${SNAPSHOT_DIR}/hardware_identity_resolved.yaml"
}

query_candidate_uids() {
  local uid_dir="${SNAPSHOT_DIR}/uid_queries"
  mkdir -p "${uid_dir}"
  run_shell_capture candidate_serial_ports "for dev in /dev/ttyUSB* /dev/ttyACM*; do [ -e \"\$dev\" ] && printf '%s\n' \"\$dev\"; done | sort"
  sed '1,2d' "${SNAPSHOT_DIR}/candidate_serial_ports.txt" > "${SNAPSHOT_DIR}/candidate_serial_ports.raw"

  while IFS= read -r port; do
    [ -n "${port}" ] || continue
    local safe_name
    safe_name="$(basename "${port}")"
    {
      echo "$ python3 ${WORKSPACE_DIR}/scripts/hwk_query_device_info.py --port ${port} --addr 6 --package-id 29 --cmd uid --timeout 1.5 --serial-timeout 0.02"
      echo
      python3 "${WORKSPACE_DIR}/scripts/hwk_query_device_info.py" \
        --port "${port}" \
        --addr 6 \
        --package-id 29 \
        --cmd uid \
        --timeout 1.5 \
        --serial-timeout 0.02
    } > "${uid_dir}/${safe_name}_uid.txt" 2>&1
    echo "$?" > "${uid_dir}/${safe_name}_uid.status"
  done < "${SNAPSHOT_DIR}/candidate_serial_ports.raw"
}

start_pressure_launch() {
  if ! source_setup_file "${ROS_SETUP}"; then
    echo "Missing ROS setup: ${ROS_SETUP}" > "${LOG_DIR}/pressure_driver_launch.log"
    return 1
  fi
  if ! source_setup_file "${WORKSPACE_SETUP}"; then
    echo "Missing workspace setup: ${WORKSPACE_SETUP}" > "${LOG_DIR}/pressure_driver_launch.log"
    return 1
  fi

  export ROS_AUTOMATIC_DISCOVERY_RANGE="LOCALHOST"
  export ROS_STATIC_PEERS=""
  export ROS_LOG_DIR="${LOG_DIR}/ros_log"

  ros2 daemon stop > "${LOG_DIR}/ros2_daemon_stop.log" 2>&1 || true

  setsid ros2 launch hwk_pressure_driver pressure_driver.launch.py \
    config_file:="${PRESSURE_CONFIG}" \
    > "${LOG_DIR}/pressure_driver_launch.log" 2>&1 &
  local launch_pid=$!

  echo "${launch_pid}" > "${LOG_DIR}/pressure_driver_launch.pid"
  sleep "${STARTUP_WAIT}"

  if ! kill -0 "${launch_pid}" >/dev/null 2>&1; then
    echo "launch_exited" > "${LOG_DIR}/pressure_driver_launch.state"
    wait "${launch_pid}" >/dev/null 2>&1 || true
    return 1
  fi

  echo "launch_running" > "${LOG_DIR}/pressure_driver_launch.state"

  ros2 node list --no-daemon --spin-time 5 > "${SNAPSHOT_DIR}/ros2_node_list.txt" 2>&1
  echo "$?" > "${SNAPSHOT_DIR}/ros2_node_list.status"
  ros2 topic list --no-daemon --spin-time 5 > "${SNAPSHOT_DIR}/ros2_topic_list.txt" 2>&1
  echo "$?" > "${SNAPSHOT_DIR}/ros2_topic_list.status"

  for topic in "${TOPICS[@]}"; do
    local safe_topic
    safe_topic="${topic#/}"
    safe_topic="${safe_topic//\//_}"
    ros2 topic info "${topic}" -v > "${SNAPSHOT_DIR}/topic_info_${safe_topic}.txt" 2>&1
    echo "$?" > "${SNAPSHOT_DIR}/topic_info_${safe_topic}.status"
    timeout 8s ros2 topic echo --once "${topic}" > "${LOG_DIR}/topic_echo_${safe_topic}.txt" 2>&1
    echo "$?" > "${LOG_DIR}/topic_echo_${safe_topic}.status"
  done

  kill -INT "-${launch_pid}" >/dev/null 2>&1 || kill -INT "${launch_pid}" >/dev/null 2>&1 || true
  for _ in $(seq 1 8); do
    if ! kill -0 "${launch_pid}" >/dev/null 2>&1; then
      break
    fi
    sleep 1
  done
  if kill -0 "${launch_pid}" >/dev/null 2>&1; then
    kill -TERM "-${launch_pid}" >/dev/null 2>&1 || kill -TERM "${launch_pid}" >/dev/null 2>&1 || true
  fi
  wait "${launch_pid}" >/dev/null 2>&1 || true
  return 0
}

summarize_results() {
  local ch340_count
  ch340_count="$(grep -c '1a86:7523' "${SNAPSHOT_DIR}/lsusb.txt" 2>/dev/null || true)"
  local identity_status
  identity_status="$(cat "${SNAPSHOT_DIR}/hardware_identity_validate.status" 2>/dev/null || echo "missing")"
  local launch_state
  launch_state="$(cat "${LOG_DIR}/pressure_driver_launch.state" 2>/dev/null || echo "not_started")"

  append_summary "## Result"
  append_summary
  append_summary "- CH340 count: ${ch340_count} / expected 4"
  append_summary "- Hardware identity validation exit status: ${identity_status}"
  append_summary "- Pressure launch state after ${STARTUP_WAIT}s: ${launch_state}"
  append_summary

  append_summary "## UID Query Results"
  append_summary
  if compgen -G "${SNAPSHOT_DIR}/uid_queries/*_uid.txt" >/dev/null; then
    for file in "${SNAPSHOT_DIR}"/uid_queries/*_uid.txt; do
      local port_name
      local status
      local value
      port_name="$(basename "${file}" _uid.txt)"
      status="$(cat "${file%.txt}.status" 2>/dev/null || echo "missing")"
      value="$(sed -n 's/^value: //p' "${file}" | tail -n 1)"
      if [ -z "${value}" ]; then
        value="no UID"
      fi
      append_summary "- ${port_name}: status=${status}, value=${value}"
    done
  else
    append_summary "- No candidate serial ports were found."
  fi
  append_summary

  append_summary "## Topic Samples"
  append_summary
  for topic in "${TOPICS[@]}"; do
    local safe_topic
    local status
    safe_topic="${topic#/}"
    safe_topic="${safe_topic//\//_}"
    status="$(cat "${LOG_DIR}/topic_echo_${safe_topic}.status" 2>/dev/null || echo "missing")"
    if [ "${status}" = "0" ]; then
      append_summary "- ${topic}: OK, sample captured"
    else
      append_summary "- ${topic}: FAIL/WARN, echo status=${status}"
    fi
  done
  append_summary

  append_summary "## Failure Triage Hints"
  append_summary
  if [ "${ch340_count}" != "4" ]; then
    append_summary "- USB enumeration layer failed: expected 4 CH340 devices. Check tactile USB cables, hub branches, and power before changing software."
  fi
  if [ "${identity_status}" != "0" ]; then
    append_summary "- Identity mapping layer failed: inspect snapshots/hardware_identity_validate.txt and uid_queries/*.txt for missing or changed HWK_CHIP_UID values."
  fi
  if [ "${launch_state}" != "launch_running" ]; then
    append_summary "- ROS launch layer failed before graph checks: inspect logs/pressure_driver_launch.log."
  fi
  append_summary "- If udev rule differences are reported, do not edit repository files; install/reload rules only after explicit sudo approval."
  append_summary
  append_summary "## Important Files"
  append_summary
  append_summary "- Static snapshots: snapshots/"
  append_summary "- Launch log: logs/pressure_driver_launch.log"
  append_summary "- Topic samples: logs/topic_echo_*.txt"
  append_summary "- ROS internal logs: logs/ros_log/"
  append_summary
  append_summary "- Finished: $(timestamp)"
}

reset_outputs
write_header
collect_static_snapshots
run_existing_diagnostics
query_candidate_uids
start_pressure_launch
summarize_results

echo "Diagnostic complete: ${SUMMARY_FILE}"
