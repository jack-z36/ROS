# HWK Pressure Repair Diagnostic Summary

- Started: 2026-05-22 10:20:49 +0800
- Workspace: /home/hit/ROS
- Test directory: /home/hit/ROS/diagnostics/20260522_hwk_pressure_repair_check
- Pressure config: /home/hit/ROS/src/hwk_pressure_driver/config/pressure_sensors.yaml
- Identity map: /home/hit/ROS/config/hardware_identity_map.yaml

## Result

- CH340 count: 1 / expected 4
- Hardware identity validation exit status: 1
- Pressure launch state after 12s: launch_exited

## UID Query Results

- ttyUSB1: status=1, value=no UID

## Topic Samples

- /pressure/left_hand/gripper_1: FAIL/WARN, echo status=missing
- /pressure/left_hand/gripper_2: FAIL/WARN, echo status=missing
- /pressure/right_hand/gripper_1: FAIL/WARN, echo status=missing
- /pressure/right_hand/gripper_2: FAIL/WARN, echo status=missing

## Failure Triage Hints

- USB enumeration layer failed: expected 4 CH340 devices. Check tactile USB cables, hub branches, and power before changing software.
- Identity mapping layer failed: inspect snapshots/hardware_identity_validate.txt and uid_queries/*.txt for missing or changed HWK_CHIP_UID values.
- ROS launch layer failed before graph checks: inspect logs/pressure_driver_launch.log.
- If udev rule differences are reported, do not edit repository files; install/reload rules only after explicit sudo approval.

## Manual Review

- Current visible tactile serial device is only `/dev/ttyUSB1`, linked as `/dev/hwk_pressure_left_gripper_1`.
- Missing expected by-path devices:
  - `/dev/serial/by-path/pci-0000:00:14.0-usb-0:2.4.3.2.4:1.0-port0`
  - `/dev/serial/by-path/pci-0000:00:14.0-usb-0:2.4.1.1:1.0-port0`
  - `/dev/serial/by-path/pci-0000:00:14.0-usb-0:2.4.4.2:1.0-port0`
- The one visible CH340 opens as a serial port, but `HWK_CHIP_UID` query times out with `result: timeout/no matching ACK`.
- Kernel log shows another CH340 was previously attached as `ttyUSB0` at `10:08:19`, then disconnected at `10:12:32`.
- `/etc/udev/rules.d/99-hwk-pressure.rules` differs from the repository rule file, but that is secondary right now; first restore all four CH340 devices and at least one valid UID response.
- Recommended next physical checks: tactile sensor power, repaired connector continuity, USB hub branch, and whether the board attached to `/dev/ttyUSB1` is powered and speaking HWK protocol at addr `6`, package id `29`, baud `460800`.

## Important Files

- Static snapshots: snapshots/
- Launch log: logs/pressure_driver_launch.log
- Topic samples: logs/topic_echo_*.txt
- ROS internal logs: logs/ros_log/

- Finished: 2026-05-22 10:21:12 +0800
