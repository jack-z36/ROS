---
name: read-hwk-tactile-uid
description: Read the HWK tactile pressure sensor chip UID and protocol device address from a connected serial port, then safely update the requested l1/l2/r1/r2 entry in config/hardware_identity_map.yaml. Use when the user connects or replaces a tactile sensor and asks to read, identify, bind, register, or refresh its UID.
---

# Read HWK Tactile UID

Read the physical `HWK_CHIP_UID`; never infer identity from `/dev/ttyUSB*` numbering.

## Workflow

1. Read the repository `AGENTS.md` and follow the ordinary-code-maintenance loading route unless the request includes a bug or Git operation.
2. Confirm the requested logical position is exactly one of `l1`, `l2`, `r1`, or `r2`. If the user has already stated it, do not ask again.
3. List current candidates:

   ```bash
   ls -l /dev/ttyUSB* /dev/ttyACM* /dev/hwk_pressure_* 2>/dev/null
   ```

4. Scan the connected device with the bundled wrapper. It reuses the repository protocol implementation in `scripts/hwk_query_device_info.py` and tries protocol addresses `0..15` at `921600`, then `460800` baud:

   ```bash
   python3 skills/read-hwk-tactile-uid/scripts/scan_hwk_uid.py \
     --port /dev/ttyUSB0 --logical-id l2
   ```

5. Require `result: OK`. Record the returned `uid`, `device_addr`, and `baudrate`. A timeout is not an empty UID; do not edit configuration after a failed scan.
6. Update only these fields in `config/hardware_identity_map.yaml` under the requested logical position:
   - `HWK_CHIP_UID`
   - `HWK_DEVICE_ADDR`

   Preserve the other three logical positions and keep `HWK_PACKAGE_ID` unchanged unless the hardware query explicitly establishes a different value.
7. Verify the target semantics:

   | Position | Hand | Gripper | Topic |
   |---|---|---|---|
   | `l1` | `left_hand` | `gripper_1` | `/pressure/left_hand/gripper_1` |
   | `l2` | `left_hand` | `gripper_2` | `/pressure/left_hand/gripper_2` |
   | `r1` | `right_hand` | `gripper_1` | `/pressure/right_hand/gripper_1` |
   | `r2` | `right_hand` | `gripper_2` | `/pressure/right_hand/gripper_2` |

8. Run `git diff --check` and load the driver configuration through `hwk_pressure_driver.config.load_config`. Assert that the new UID resolves to the requested hand, gripper, topic, and device address.
9. Report the UID, address, baudrate, configuration path, validation result, and Git commit status. Do not commit unless the user asks.

## Safety Rules

- Treat the user's stated logical position as authoritative; a UID cannot reveal l1/l2/r1/r2 by itself.
- If more than one serial device is connected, scan each explicit port and do not guess which physical sensor the user means.
- If the scan finds multiple identities on one port, stop and report the ambiguity instead of updating the map.
- Preserve unrelated user changes in the configuration file.
