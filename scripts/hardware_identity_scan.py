#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
import sys
import time
from collections import defaultdict
from glob import glob
from pathlib import Path

import yaml


WORKSPACE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_MAP_FILE = WORKSPACE_DIR / "config" / "hardware_identity_map.yaml"
HWK_QUERY_SCRIPT = WORKSPACE_DIR / "scripts" / "hwk_query_device_info.py"

SERIAL_GLOBS = ("/dev/ttyUSB*", "/dev/ttyACM*")
VIDEO_GLOBS = ("/dev/video*",)
HWK_DEFAULT_BAUDRATE = 460800
HWK_DEFAULT_ADDR = 6
HWK_DEFAULT_PACKAGE_ID = 29
HWK_QUERY_ATTEMPTS = 2
HWK_QUERY_RETRY_DELAY_SEC = 0.1
ROS_PYTHON_EXECUTABLE = os.environ.get("ROS_PYTHON_EXECUTABLE", "/usr/bin/python3")
HWK_PROTOCOL_KEYS = {
    "HWK_CHIP_UID",
    "HWK_DEVICE_ADDR",
    "HWK_APP_VERSION",
    "HWK_PACKAGE_ID",
}
STRONG_IDENTITY_KEYS = {
    "ID_SERIAL",
    "ID_SERIAL_SHORT",
    "ID_USB_SERIAL",
    "ID_USB_SERIAL_SHORT",
    "HWK_CHIP_UID",
}
PATH_FALLBACK_KEYS = {"ID_PATH", "ID_PATH_TAG", "DEVPATH", "DEVLINKS"}
DISPLAY_KEYS = (
    "DEVNAME",
    "ID_SERIAL",
    "ID_SERIAL_SHORT",
    "ID_VENDOR_ID",
    "ID_MODEL_ID",
    "ID_VENDOR",
    "ID_MODEL",
    "ID_V4L_PRODUCT",
    "ID_V4L_CAPABILITIES",
    "ID_USB_INTERFACE_NUM",
    "ID_PATH",
    "HWK_CHIP_UID",
    "HWK_DEVICE_ADDR",
    "HWK_APP_VERSION",
)


def run(cmd, timeout=4):
    try:
        return subprocess.run(
            cmd,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return subprocess.CompletedProcess(
            cmd, 124, exc.stdout or "", exc.stderr or "timeout"
        )


def parse_properties(text):
    props = {}
    for line in text.splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        props[key] = value
    return props


def udev_properties(device):
    proc = run(["udevadm", "info", "-q", "property", "-n", device])
    props = parse_properties(proc.stdout)
    props.setdefault("DEVNAME", device)
    return props


def parse_key_value_output(text):
    values = {}
    for line in text.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        values[key.strip()] = value.strip()
    return values


def query_hwk_info(
    device,
    cmd,
    addr=HWK_DEFAULT_ADDR,
    package_id=HWK_DEFAULT_PACKAGE_ID,
    baudrate=HWK_DEFAULT_BAUDRATE,
    attempts=HWK_QUERY_ATTEMPTS,
):
    query_command = [
        ROS_PYTHON_EXECUTABLE
        if Path(ROS_PYTHON_EXECUTABLE).is_file()
        else sys.executable,
        str(HWK_QUERY_SCRIPT),
        "--port",
        device,
        "--baudrate",
        str(baudrate),
        "--addr",
        str(addr),
        "--package-id",
        str(package_id),
        "--cmd",
        cmd,
        "--timeout",
        "0.8",
    ]
    for attempt in range(max(1, attempts)):
        proc = run(query_command, timeout=3)
        if proc.returncode == 0:
            value = parse_key_value_output(proc.stdout).get("value")
            if value:
                return value
        if attempt + 1 < attempts:
            time.sleep(HWK_QUERY_RETRY_DELAY_SEC)
    return None


def enrich_hwk_protocol_identity(device, match, baudrate=HWK_DEFAULT_BAUDRATE):
    props = device["properties"]
    if "HWK_CHIP_UID" in props:
        return

    addr = int(match.get("HWK_DEVICE_ADDR", HWK_DEFAULT_ADDR))
    package_id = int(match.get("HWK_PACKAGE_ID", HWK_DEFAULT_PACKAGE_ID))
    uid = query_hwk_info(
        device["path"],
        "uid",
        addr=addr,
        package_id=package_id,
        baudrate=baudrate,
    )
    if uid:
        props["HWK_CHIP_UID"] = uid
    if "HWK_DEVICE_ADDR" in match:
        queried_addr = query_hwk_info(
            device["path"],
            "addr",
            addr=addr,
            package_id=package_id,
            baudrate=baudrate,
        )
        if queried_addr:
            props["HWK_DEVICE_ADDR"] = queried_addr
    if "HWK_APP_VERSION" in match:
        version = query_hwk_info(
            device["path"],
            "version",
            addr=addr,
            package_id=package_id,
            baudrate=baudrate,
        )
        if version:
            props["HWK_APP_VERSION"] = version


def split_devlinks(props):
    return sorted(link for link in props.get("DEVLINKS", "").split() if link)


def is_video_capture(device, props):
    capabilities = props.get("ID_V4L_CAPABILITIES", "")
    if ":capture:" in capabilities:
        return True
    if capabilities and ":capture:" not in capabilities:
        return False
    proc = run(["v4l2-ctl", f"--device={device}", "--all"], timeout=4)
    if proc.returncode != 0:
        return None
    output = proc.stdout + proc.stderr
    if "Format Video Capture:" in output or "\n\t\tVideo Capture\n" in output:
        return True
    if "Format Metadata Capture:" in output or "\n\t\tMetadata Capture\n" in output:
        return False
    return None


def sorted_devices(patterns):
    paths = []
    for pattern in patterns:
        paths.extend(glob(pattern))
    return sorted(set(paths))


def collect_devices():
    devices = {"serial": [], "video": []}

    for device in sorted_devices(SERIAL_GLOBS):
        props = udev_properties(device)
        devices["serial"].append(
            {
                "kind": "serial",
                "path": device,
                "realpath": os.path.realpath(device),
                "links": split_devlinks(props),
                "properties": props,
            }
        )

    for device in sorted_devices(VIDEO_GLOBS):
        props = udev_properties(device)
        devices["video"].append(
            {
                "kind": "video",
                "path": device,
                "realpath": os.path.realpath(device),
                "links": split_devlinks(props),
                "properties": props,
                "video_capture": is_video_capture(device, props),
            }
        )

    return devices


def compact_devices(devices):
    compact = {}
    for kind, entries in devices.items():
        compact[kind] = []
        for device in entries:
            props = device["properties"]
            item = {
                "path": device["path"],
                "realpath": device["realpath"],
                "links": device["links"],
                "properties": {key: props[key] for key in DISPLAY_KEYS if key in props},
            }
            if kind == "video":
                item["video_capture"] = device.get("video_capture")
            compact[kind].append(item)
    return compact


def print_device(device):
    props = device["properties"]
    suffix = ""
    if device["kind"] == "video":
        capture = device.get("video_capture")
        if capture is True:
            suffix = " [capture]"
        elif capture is False:
            suffix = " [metadata/non-capture]"
        else:
            suffix = " [capture unknown]"

    print(f"- {device['path']}{suffix}")
    for key in DISPLAY_KEYS:
        if key in props:
            print(f"    {key}: {props[key]}")
    if device["links"]:
        print("    DEVLINKS:")
        for link in device["links"]:
            print(f"      {link}")


def print_duplicate_notes(kind, devices):
    grouped = defaultdict(list)
    for device in devices:
        serial = device["properties"].get("ID_SERIAL")
        if serial:
            grouped[serial].append(device["path"])

    for serial, paths in sorted(grouped.items()):
        if len(paths) > 1:
            joined = ", ".join(paths)
            print(f"  note: repeated ID_SERIAL={serial} on {joined}")


def print_scan(devices):
    for kind in ("serial", "video"):
        entries = devices[kind]
        print(f"\n[{kind}] {len(entries)} candidate device(s)")
        if not entries:
            print("  none")
            continue
        for device in entries:
            print_device(device)
        print_duplicate_notes(kind, entries)


def load_map(path):
    with Path(path).expanduser().open("r", encoding="utf-8") as stream:
        return yaml.safe_load(stream) or {}


def bool_value(value, default=False):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("1", "true", "yes", "on")
    return bool(value)


def iter_map_entries(mapping):
    for group_name in ("pressure", "gopro"):
        group = mapping.get(group_name) or {}
        if not isinstance(group, dict):
            continue
        for logical_name, entry in group.items():
            if not isinstance(entry, dict):
                continue
            default_kind = "serial" if group_name == "pressure" else "video"
            yield {
                "group": group_name,
                "logical_name": logical_name,
                "label": f"{group_name}.{logical_name}",
                "device_type": entry.get("device_type", default_kind),
                "required": bool_value(entry.get("required"), True),
                "require_video_capture": bool_value(
                    entry.get("require_video_capture"), group_name == "gopro"
                ),
                "match": entry.get("match") or {},
                "target": entry.get("target") or {},
            }


def match_value(actual, expected):
    if isinstance(expected, list):
        return any(match_value(actual, item) for item in expected)
    return str(actual) == str(expected)


def device_matches(device, match, hwk_baudrate=HWK_DEFAULT_BAUDRATE):
    props = device["properties"]
    if device["kind"] == "serial" and any(key in match for key in HWK_PROTOCOL_KEYS):
        enrich_hwk_protocol_identity(device, match, baudrate=hwk_baudrate)

    for key, expected in match.items():
        if expected in (None, ""):
            return False
        if key == "HWK_PACKAGE_ID":
            continue
        if key == "DEVLINKS":
            if isinstance(expected, list):
                expected_links = [str(item) for item in expected]
            else:
                expected_links = [str(expected)]
            if not all(link in device["links"] for link in expected_links):
                return False
            continue
        if key == "DEVNAME":
            actual = device["path"]
        else:
            actual = props.get(key)
        if actual is None or not match_value(actual, expected):
            return False
    return True


def strong_identity(match):
    return any(key in match and match[key] not in (None, "") for key in STRONG_IDENTITY_KEYS)


def path_only_identity(match):
    keys = {key for key, value in match.items() if value not in (None, "")}
    return bool(keys) and keys.issubset(PATH_FALLBACK_KEYS | {"DEVNAME"})


def preferred_path(device, match=None):
    match = match or {}
    id_path = match.get("ID_PATH")
    if id_path:
        by_path = [
            link
            for link in device["links"]
            if "/by-path/" in link and str(id_path) in link
        ]
        if by_path:
            return sorted(by_path)[0]

    by_id = [link for link in device["links"] if "/by-id/" in link]
    if by_id:
        return sorted(by_id)[0]
    devlinks = device["links"]
    if devlinks:
        return sorted(devlinks)[0]
    return device["path"]


def validate_mapping(mapping, devices, hwk_baudrate=HWK_DEFAULT_BAUDRATE):
    failures = 0
    warnings = 0
    resolved = {"pressure": {}, "gopro": {}}
    used_realpaths = {}
    configured_hwk_uids = set()

    print("\n[mapping validation]")
    entries = list(iter_map_entries(mapping))
    if not entries:
        print("FAIL no pressure/gopro mapping entries found")
        return 1, resolved

    for entry in entries:
        label = entry["label"]
        if not entry["required"]:
            print(f"SKIP {label}: required=false")
            continue

        match = entry["match"]
        if not match:
            failures += 1
            print(f"FAIL {label}: no match fields configured; run scan and calibrate it")
            continue
        if entry["group"] == "pressure" and match.get("HWK_CHIP_UID"):
            configured_hwk_uids.add(str(match["HWK_CHIP_UID"]))

        candidates = []
        for device in devices.get(entry["device_type"], []):
            if entry["require_video_capture"] and device.get("video_capture") is False:
                continue
            if device_matches(device, match, hwk_baudrate=hwk_baudrate):
                candidates.append(device)

        if not candidates:
            failures += 1
            print(f"FAIL {label}: no current {entry['device_type']} device matches {match}")
            continue
        if len(candidates) > 1:
            failures += 1
            paths = ", ".join(device["path"] for device in candidates)
            print(f"FAIL {label}: match is not unique: {paths}")
            continue

        device = candidates[0]
        realpath = device["realpath"]
        if realpath in used_realpaths:
            failures += 1
            print(
                f"FAIL {label}: resolves to same hardware node as {used_realpaths[realpath]} "
                f"({device['path']})"
            )
            continue
        used_realpaths[realpath] = label

        if path_only_identity(match):
            warnings += 1
            print(f"WARN {label}: mapping uses path/topology fallback only")
        elif not strong_identity(match):
            warnings += 1
            print(f"WARN {label}: mapping has no serial-like identity key")

        print(f"OK   {label}: {preferred_path(device, match)}")
        target = entry["target"]
        if target.get("topic"):
            print(f"     topic: {target['topic']}")

        resolved[entry["group"]][entry["logical_name"]] = {
            "device": preferred_path(device, match),
            "devname": device["path"],
            "realpath": realpath,
            "links": device["links"],
            "target": target,
            "matched": match,
        }

    failures += validate_unknown_hwk_devices(devices, configured_hwk_uids, resolved)

    if failures:
        print(f"\nvalidation failed: {failures} failure(s), {warnings} warning(s)")
        return 1, resolved

    print(f"\nvalidation passed: {warnings} warning(s)")
    return 0, resolved


def validate_unknown_hwk_devices(devices, configured_hwk_uids, resolved):
    if not configured_hwk_uids:
        return 0

    failures = 0
    resolved_pressure_realpaths = {
        item["realpath"] for item in (resolved.get("pressure") or {}).values()
    }
    for device in devices.get("serial", []):
        props = device["properties"]
        is_hwk_ch340 = props.get("ID_VENDOR_ID") == "1a86" and props.get("ID_MODEL_ID") == "7523"
        if not is_hwk_ch340:
            continue
        if device["realpath"] in resolved_pressure_realpaths:
            continue

        enrich_hwk_protocol_identity(
            device,
            {
                "HWK_DEVICE_ADDR": str(HWK_DEFAULT_ADDR),
                "HWK_PACKAGE_ID": str(HWK_DEFAULT_PACKAGE_ID),
            },
        )
        uid = props.get("HWK_CHIP_UID")
        if uid and uid in configured_hwk_uids:
            continue
        if uid:
            print(
                f"FAIL pressure.unknown: {preferred_path(device)} has unconfigured "
                f"HWK_CHIP_UID={uid}"
            )
        else:
            print(
                f"FAIL pressure.unknown: {preferred_path(device)} is a HWK CH340 candidate "
                "but did not return HWK_CHIP_UID"
            )
        failures += 1
    return failures


def write_resolved(path, resolved):
    output_path = Path(path).expanduser()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as stream:
        yaml.safe_dump(resolved, stream, sort_keys=False)
    print(f"wrote resolved mapping: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Scan and validate serial/video hardware identity mappings."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan_parser = subparsers.add_parser("scan", help="print current hardware candidates")
    scan_parser.add_argument("--json", action="store_true", help="print compact JSON")

    validate_parser = subparsers.add_parser(
        "validate", help="validate a hardware identity map against current devices"
    )
    validate_parser.add_argument("--map", default=str(DEFAULT_MAP_FILE))
    validate_parser.add_argument("--write-resolved")
    validate_parser.add_argument(
        "--hwk-baudrate",
        type=int,
        default=HWK_DEFAULT_BAUDRATE,
        help="baudrate used when querying HWK protocol identity",
    )

    args = parser.parse_args()
    devices = collect_devices()

    if args.command == "scan":
        if args.json:
            print(json.dumps(compact_devices(devices), indent=2, sort_keys=True))
        else:
            print_scan(devices)
        return 0

    mapping = load_map(args.map)
    status, resolved = validate_mapping(
        mapping, devices, hwk_baudrate=args.hwk_baudrate
    )
    if status == 0 and args.write_resolved:
        write_resolved(args.write_resolved, resolved)
    return status


if __name__ == "__main__":
    sys.exit(main())
