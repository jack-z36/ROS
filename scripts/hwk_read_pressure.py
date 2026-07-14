#!/usr/bin/env python3
"""Real-time HWK pressure sensor data reader.

Usage:
  python3 scripts/hwk_read_pressure.py                          # defaults
  python3 scripts/hwk_read_pressure.py --port /dev/ttyUSB0 --baud 921600 --addr 1
  python3 scripts/hwk_read_pressure.py --raw                     # raw hex dump
"""

import argparse
import struct
import sys
import time

import serial

HEAD = bytes((0x3C, 0x3C))
TAIL = bytes((0x3E, 0x3E))
CHAN_DATA = 0x02
TYPE_GET = 0x01
MIN_FRAME_LEN = 10


def crc16(payload: bytes) -> int:
    crc = 0
    for byte in payload:
        crc ^= byte
        for _ in range(8):
            if crc & 0x0001:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
            crc &= 0xFFFF
    return crc & 0xFFFF


def build_get_frame(dev_addr: int, pkg_id: int) -> bytes:
    payload = bytes((0x01,))
    id_ch = ((dev_addr & 0x0F) << 4) | CHAN_DATA
    flags = ((pkg_id & 0x3F) << 2) | TYPE_GET
    cs = crc16(payload)
    return b"".join([
        HEAD,
        bytes((id_ch, flags)),
        len(payload).to_bytes(2, "little"),
        payload,
        cs.to_bytes(2, "little"),
        TAIL,
    ])


def read_one_frame(ser, timeout=1.0, max_payload=4096):
    """Read one valid ACK frame on data channel, return ParsedFrame or None."""
    buf = bytearray()
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        chunk = ser.read(512)
        if chunk:
            buf.extend(chunk)
        while True:
            idx = buf.find(HEAD)
            if idx < 0:
                if buf[-1:] == HEAD[:1]:
                    del buf[:-1]
                else:
                    buf.clear()
                break
            if idx > 0:
                del buf[:idx]
            if len(buf) < MIN_FRAME_LEN:
                break
            length = int.from_bytes(buf[4:6], "little")
            if length > max_payload:
                del buf[0]
                continue
            flen = MIN_FRAME_LEN + length
            if len(buf) < flen:
                break
            raw = bytes(buf[:flen])
            del buf[:flen]
            if raw[-2:] != TAIL:
                continue
            p = raw[6:6+length]
            exp_crc = int.from_bytes(raw[6+length:8+length], "little")
            if crc16(p) != exp_crc:
                continue
            id_ch = raw[2]
            flags = raw[3]
            return {
                "addr": (id_ch >> 4) & 0x0F,
                "channel": id_ch & 0x0F,
                "type": flags & 0x03,
                "pkg_id": (flags >> 2) & 0x3F,
                "payload": bytes(p),
                "raw": raw,
            }
    return None


def main():
    parser = argparse.ArgumentParser(description="Real-time HWK pressure sensor reader")
    parser.add_argument("--port", default="/dev/ttyUSB0")
    parser.add_argument("--baud", type=int, default=921600)
    parser.add_argument("--addr", type=int, default=1, help="sensor device address, 0..15")
    parser.add_argument("--package-id", type=int, default=29, help="frame package ID, 0..63")
    parser.add_argument("--rate", type=float, default=20, help="poll rate in Hz")
    parser.add_argument("--raw", action="store_true", help="raw hex dump instead of matrix")
    parser.add_argument("--count", type=int, default=0, help="number of frames (0 = infinite)")
    args = parser.parse_args()

    if not 0 <= args.addr <= 0x0F:
        print(f"ERROR: addr must be 0..15", file=sys.stderr)
        return 2
    if not 0 <= args.package_id <= 0x3F:
        print(f"ERROR: package-id must be 0..63", file=sys.stderr)
        return 2

    print(f"Connecting: port={args.port}  baud={args.baud}  addr={args.addr}  pkg_id={args.package_id}")
    ser = serial.Serial(args.port, baudrate=args.baud, timeout=0.02)
    ser.reset_input_buffer()
    ser.reset_output_buffer()

    poll_interval = 1.0 / max(args.rate, 1.0)
    cycle = 0
    last_req_time = 0.0

    try:
        while args.count == 0 or cycle < args.count:
            # Poll at target rate
            now = time.monotonic()
            if now - last_req_time < poll_interval:
                time.sleep(0.001)
                continue
            last_req_time = now

            req = build_get_frame(args.addr, args.package_id)
            ser.write(req)
            ser.flush()

            frame = read_one_frame(ser, timeout=max(0.5, poll_interval * 2))

            if frame is None:
                print(f"[{cycle:4d}] timeout")
                continue

            payload = frame["payload"]

            if args.raw:
                print(f"[{cycle:4d}] pkg_id={frame['pkg_id']} type=0x{frame['type']:02X} "
                      f"len={len(payload)} raw={payload.hex(' ').upper()}")
                cycle += 1
                continue

            if len(payload) < 4:
                print(f"[{cycle:4d}] short payload: {len(payload)}B")
                cycle += 1
                continue

            total_pkts = payload[0]
            pkt_idx = payload[1]
            cols = payload[2]
            rows = payload[3]
            data_bytes = payload[4:]
            n = len(data_bytes) // 2
            values = list(struct.unpack_from(f"<{n}H", data_bytes, 0)) if data_bytes else []

            print(f"[{cycle:4d}] pkt={pkt_idx}/{total_pkts}  {rows}×{cols}  "
                  f"min={min(values):4d}  max={max(values):4d}  "
                  f"mean={sum(values)//len(values):4d}  n={len(values)}")

            if rows > 0 and cols > 0 and len(values) >= rows * cols:
                for r in range(rows):
                    row_vals = values[r * cols : (r + 1) * cols]
                    line = " ".join(f"{v:5d}" for v in row_vals)
                    print(f"  [{r:2d}] {line}")

            cycle += 1

    except KeyboardInterrupt:
        print("\nInterrupted.")
    finally:
        ser.close()
        print("Closed.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
