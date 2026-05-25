#!/usr/bin/env python3
"""Sample raw HWK pressure frames directly from one serial port."""

import argparse
import statistics
import struct
import sys
import time
from pathlib import Path

try:
    import serial
except ImportError as exc:
    print("pyserial is required: python3 -m pip install pyserial", file=sys.stderr)
    raise SystemExit(2) from exc


HEAD = bytes((0x3C, 0x3C))
TAIL = bytes((0x3E, 0x3E))

CHANNEL_DATA = 0x02
TYPE_GET = 0x01
TYPE_ACK = 0x03
MIN_FRAME_LEN = 10
GET_PRESSURE_PAYLOAD = bytes((0x01,))


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


def build_get_data_frame(device_addr: int, package_id: int) -> bytes:
    if not 0 <= device_addr <= 0x0F:
        raise ValueError(f"device_addr must be in range 0..15, got {device_addr}")
    if not 0 <= package_id <= 0x3F:
        raise ValueError(f"package_id must be in range 0..63, got {package_id}")

    id_channel = ((device_addr & 0x0F) << 4) | CHANNEL_DATA
    flags = ((package_id & 0x3F) << 2) | TYPE_GET
    checksum = crc16(GET_PRESSURE_PAYLOAD)
    return b"".join(
        (
            HEAD,
            bytes((id_channel, flags)),
            len(GET_PRESSURE_PAYLOAD).to_bytes(2, byteorder="little", signed=False),
            GET_PRESSURE_PAYLOAD,
            checksum.to_bytes(2, byteorder="little", signed=False),
            TAIL,
        )
    )


def parse_frame(frame: bytes):
    if len(frame) < MIN_FRAME_LEN:
        return None, f"frame too short: {len(frame)}"
    if frame[:2] != HEAD:
        return None, "bad head"

    length = int.from_bytes(frame[4:6], byteorder="little", signed=False)
    expected_len = MIN_FRAME_LEN + length
    if len(frame) != expected_len:
        return None, f"length mismatch: expected {expected_len}, got {len(frame)}"
    if frame[-2:] != TAIL:
        return None, "bad tail"

    payload_start = 6
    payload_end = payload_start + length
    payload = frame[payload_start:payload_end]
    received_crc = int.from_bytes(
        frame[payload_end : payload_end + 2], byteorder="little", signed=False
    )
    actual_crc = crc16(payload)
    if received_crc != actual_crc:
        return None, f"CRC error: received=0x{received_crc:04X}, calculated=0x{actual_crc:04X}"

    id_channel = frame[2]
    flags = frame[3]
    return {
        "device_addr": (id_channel >> 4) & 0x0F,
        "channel": id_channel & 0x0F,
        "frame_type": flags & 0x03,
        "package_id": (flags >> 2) & 0x3F,
        "length": length,
        "payload": bytes(payload),
        "raw_frame": bytes(frame),
    }, None


class FrameReader:
    def __init__(self, serial_obj, max_payload_length: int):
        self.serial_obj = serial_obj
        self.max_payload_length = max_payload_length
        self.rx_buffer = bytearray()
        self.frame_errors = 0

    def read_one_frame(self, timeout_sec: float):
        deadline = time.monotonic() + timeout_sec

        while time.monotonic() < deadline:
            chunk = self.serial_obj.read(512)
            if chunk:
                self.rx_buffer.extend(chunk)

            while True:
                head_index = self.rx_buffer.find(HEAD)
                if head_index < 0:
                    if self.rx_buffer[-1:] == HEAD[:1]:
                        del self.rx_buffer[:-1]
                    else:
                        self.rx_buffer.clear()
                    break
                if head_index > 0:
                    del self.rx_buffer[:head_index]

                if len(self.rx_buffer) < MIN_FRAME_LEN:
                    break

                length = int.from_bytes(self.rx_buffer[4:6], byteorder="little", signed=False)
                if length > self.max_payload_length:
                    self.frame_errors += 1
                    del self.rx_buffer[0]
                    continue

                frame_len = MIN_FRAME_LEN + length
                if len(self.rx_buffer) < frame_len:
                    break

                frame = bytes(self.rx_buffer[:frame_len])
                del self.rx_buffer[:frame_len]
                parsed, error = parse_frame(frame)
                if parsed is not None:
                    return parsed
                self.frame_errors += 1
                print(f"WARN ignored invalid frame: {error}", file=sys.stderr)

        return None


def decode_pressure_payload(payload: bytes):
    if len(payload) < 4:
        return None, "payload shorter than 4-byte pressure header"

    total_packets = payload[0]
    packet_index = payload[1]
    cols = payload[2]
    rows = payload[3]
    sample_bytes = payload[4:]
    usable_len = len(sample_bytes) - (len(sample_bytes) % 2)
    samples = [
        value[0]
        for value in struct.iter_unpack("<H", sample_bytes[:usable_len])
    ]
    expected_samples = rows * cols
    return {
        "total_packets": total_packets,
        "packet_index": packet_index,
        "rows": rows,
        "cols": cols,
        "samples": samples,
        "sample_count": len(samples),
        "expected_samples": expected_samples,
        "payload_len": len(payload),
    }, None


def sample_pressure(args) -> int:
    port_path = Path(args.port)
    if not port_path.exists():
        print(f"serial port does not exist: {args.port}", file=sys.stderr)
        return 2

    request_period = 1.0 / args.rate if args.rate > 0 else 0.0
    samples_per_frame = []
    frame_peaks = []
    nonzero_frames = 0
    first_nonzero_index = None
    frames_ok = 0
    timeouts = 0
    ignored_frames = 0
    payload_errors = 0
    first_payload_header = None
    started = time.monotonic()

    with serial.Serial(
        port=args.port,
        baudrate=args.baudrate,
        bytesize=serial.EIGHTBITS,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        timeout=args.serial_timeout,
    ) as serial_obj:
        serial_obj.reset_input_buffer()
        serial_obj.reset_output_buffer()
        reader = FrameReader(serial_obj, max_payload_length=args.max_payload_length)

        for index in range(args.frames):
            package_id = (args.package_id_start + index) & 0x3F
            request = build_get_data_frame(args.addr, package_id)
            request_started = time.monotonic()
            serial_obj.write(request)
            serial_obj.flush()

            matched = None
            deadline = time.monotonic() + args.timeout
            while time.monotonic() < deadline:
                frame = reader.read_one_frame(max(0.0, deadline - time.monotonic()))
                if frame is None:
                    break
                if frame["device_addr"] != args.addr:
                    ignored_frames += 1
                    continue
                if frame["channel"] != CHANNEL_DATA:
                    ignored_frames += 1
                    continue
                if frame["frame_type"] != TYPE_ACK:
                    ignored_frames += 1
                    continue
                if frame["package_id"] != package_id:
                    ignored_frames += 1
                    continue
                matched = frame
                break

            if matched is None:
                timeouts += 1
            else:
                decoded, error = decode_pressure_payload(matched["payload"])
                if decoded is None:
                    payload_errors += 1
                else:
                    frames_ok += 1
                    if first_payload_header is None:
                        first_payload_header = (
                            decoded["total_packets"],
                            decoded["packet_index"],
                            decoded["cols"],
                            decoded["rows"],
                            decoded["payload_len"],
                        )
                    samples = decoded["samples"]
                    samples_per_frame.append(decoded["sample_count"])
                    peak = max(samples, default=0)
                    frame_peaks.append(peak)
                    if peak > 0:
                        nonzero_frames += 1
                        if first_nonzero_index is None:
                            first_nonzero_index = index

            elapsed = time.monotonic() - request_started
            if request_period > elapsed:
                time.sleep(request_period - elapsed)

        frame_errors = reader.frame_errors

    finished = time.monotonic()
    elapsed = finished - started
    peak_max = max(frame_peaks, default=0)
    peak_mean = statistics.fmean(frame_peaks) if frame_peaks else 0.0
    avg_hz = frames_ok / elapsed if elapsed > 0 else 0.0
    sample_count_min = min(samples_per_frame, default=0)
    sample_count_max = max(samples_per_frame, default=0)

    print(f"label: {args.label or '-'}")
    print(f"port: {args.port}")
    print(f"baudrate: {args.baudrate}")
    print(f"addr: {args.addr}")
    print(f"frames_requested: {args.frames}")
    print(f"target_rate_hz: {args.rate}")
    print(f"timeout_sec: {args.timeout}")
    print(f"frames_ok: {frames_ok}")
    print(f"timeouts: {timeouts}")
    print(f"frame_errors: {frame_errors}")
    print(f"ignored_frames: {ignored_frames}")
    print(f"payload_errors: {payload_errors}")
    print(f"peak_max: {peak_max}")
    print(f"peak_mean: {peak_mean:.2f}")
    print(f"nonzero_frames: {nonzero_frames}")
    print(f"first_nonzero_index: {first_nonzero_index if first_nonzero_index is not None else '-'}")
    print(f"sample_count_min: {sample_count_min}")
    print(f"sample_count_max: {sample_count_max}")
    if first_payload_header is None:
        print("first_payload_header: -")
    else:
        total_packets, packet_index, cols, rows, payload_len = first_payload_header
        print(
            "first_payload_header: "
            f"total_packets={total_packets}, packet_index={packet_index}, "
            f"cols={cols}, rows={rows}, payload_len={payload_len}"
        )
    print(f"avg_hz: {avg_hz:.2f}")

    if frames_ok == 0:
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Directly sample HWK pressure data frames and print compact metrics."
    )
    parser.add_argument("--port", default="/dev/ttyUSB0")
    parser.add_argument("--baudrate", type=int, default=460800)
    parser.add_argument("--addr", type=int, default=6, help="sensor device address, 0..15")
    parser.add_argument("--frames", type=int, default=100)
    parser.add_argument("--rate", type=float, default=50.0, help="request rate in Hz")
    parser.add_argument("--timeout", type=float, default=0.05, help="per-frame response timeout")
    parser.add_argument("--serial-timeout", type=float, default=0.005)
    parser.add_argument("--package-id-start", type=int, default=0)
    parser.add_argument("--max-payload-length", type=int, default=4096)
    parser.add_argument("--label", default="")
    args = parser.parse_args()

    if args.frames <= 0:
        print("--frames must be positive", file=sys.stderr)
        return 2
    if args.rate < 0:
        print("--rate must be non-negative", file=sys.stderr)
        return 2
    if args.timeout <= 0:
        print("--timeout must be positive", file=sys.stderr)
        return 2
    if args.serial_timeout <= 0:
        print("--serial-timeout must be positive", file=sys.stderr)
        return 2
    if not 0 <= args.package_id_start <= 0x3F:
        print("--package-id-start must be in range 0..63", file=sys.stderr)
        return 2

    try:
        return sample_pressure(args)
    except serial.SerialException as exc:
        print(f"serial error: {exc}", file=sys.stderr)
        return 2
    except ValueError as exc:
        print(f"argument error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
