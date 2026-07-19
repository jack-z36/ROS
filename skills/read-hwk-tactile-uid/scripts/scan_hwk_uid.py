#!/usr/bin/env python3
"""Scan one serial port for an HWK tactile sensor chip UID."""

import argparse
import importlib.util
import sys
from pathlib import Path


def load_query_module(path: Path):
    spec = importlib.util.spec_from_file_location("hwk_query_device_info", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load query module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    repo_root = Path(__file__).resolve().parents[3]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", default="/dev/ttyUSB0")
    parser.add_argument("--logical-id", choices=("l1", "l2", "r1", "r2"))
    parser.add_argument("--baudrate", type=int, action="append", dest="baudrates")
    parser.add_argument("--package-id", type=int, default=29)
    parser.add_argument("--timeout", type=float, default=0.3)
    parser.add_argument("--serial-timeout", type=float, default=0.01)
    parser.add_argument(
        "--query-script",
        type=Path,
        default=repo_root / "scripts" / "hwk_query_device_info.py",
    )
    args = parser.parse_args()

    port = Path(args.port)
    if not port.exists():
        print(f"result: ERROR\nreason: serial port does not exist: {port}", file=sys.stderr)
        return 2

    query_module = load_query_module(args.query_script)
    baudrates = args.baudrates or [921600, 460800]
    matches = []

    try:
        for baudrate in baudrates:
            for device_addr in range(16):
                _, frame = query_module.query(
                    port=str(port),
                    baudrate=baudrate,
                    device_addr=device_addr,
                    package_id=args.package_id,
                    cmd=query_module.CMD_CHIP_UID,
                    timeout=args.timeout,
                    serial_timeout=args.serial_timeout,
                )
                if frame is None:
                    continue
                uid = query_module.decode_payload(
                    query_module.CMD_CHIP_UID, frame["payload"]
                )
                matches.append((uid, device_addr, baudrate))
    except query_module.serial.SerialException as exc:
        print(f"result: ERROR\nreason: serial error: {exc}", file=sys.stderr)
        return 2

    unique_matches = list(dict.fromkeys(matches))
    if not unique_matches:
        print("result: TIMEOUT\nreason: no matching UID response")
        return 1
    if len(unique_matches) != 1:
        print("result: AMBIGUOUS", file=sys.stderr)
        for uid, device_addr, baudrate in unique_matches:
            print(
                f"match: uid={uid} device_addr={device_addr} baudrate={baudrate}",
                file=sys.stderr,
            )
        return 2

    uid, device_addr, baudrate = unique_matches[0]
    print("result: OK")
    print(f"port: {port}")
    print(f"baudrate: {baudrate}")
    print(f"device_addr: {device_addr}")
    print(f"uid: {uid}")
    if args.logical_id:
        print(f"binding_hint: {args.logical_id} -> {uid}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
