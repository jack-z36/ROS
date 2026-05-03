#!/usr/bin/env python3
import argparse
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

CHANNEL_DEVICE_INFO = 0x01
TYPE_GET = 0x01
TYPE_DEVICE_INFO_RESPONSE = 0x02
TYPE_ACK = 0x03
DEVICE_INFO_RESPONSE_TYPES = (TYPE_DEVICE_INFO_RESPONSE, TYPE_ACK)
MIN_FRAME_LEN = 10

CMD_APP_VERSION = 0x01
CMD_CHIP_UID = 0x05
CMD_DEVICE_ADDR = 0x06

CMD_NAMES = {
    CMD_APP_VERSION: "app_version",
    CMD_CHIP_UID: "chip_uid",
    CMD_DEVICE_ADDR: "device_addr",
}


def crc16(payload):
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


def build_get_frame(device_addr, package_id, cmd):
    if not 0 <= device_addr <= 0x0F:
        raise ValueError(f"device_addr must be in range 0..15, got {device_addr}")
    if not 0 <= package_id <= 0x3F:
        raise ValueError(f"package_id must be in range 0..63, got {package_id}")
    if not 0 <= cmd <= 0xFF:
        raise ValueError(f"cmd must be in range 0..255, got {cmd}")

    payload = bytes((cmd,))
    id_channel = ((device_addr & 0x0F) << 4) | CHANNEL_DEVICE_INFO
    flags = ((package_id & 0x3F) << 2) | TYPE_GET
    checksum = crc16(payload)
    return b"".join(
        (
            HEAD,
            bytes((id_channel, flags)),
            len(payload).to_bytes(2, byteorder="little", signed=False),
            payload,
            checksum.to_bytes(2, byteorder="little", signed=False),
            TAIL,
        )
    )


def parse_frame(frame):
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
        "checksum": received_crc,
        "raw_frame": bytes(frame),
    }, None


def read_one_frame(serial_obj, timeout_sec, max_payload_length):
    rx_buffer = bytearray()
    deadline = time.monotonic() + timeout_sec

    while time.monotonic() < deadline:
        chunk = serial_obj.read(512)
        if chunk:
            rx_buffer.extend(chunk)

        while True:
            head_index = rx_buffer.find(HEAD)
            if head_index < 0:
                if rx_buffer[-1:] == HEAD[:1]:
                    del rx_buffer[:-1]
                else:
                    rx_buffer.clear()
                break
            if head_index > 0:
                del rx_buffer[:head_index]

            if len(rx_buffer) < MIN_FRAME_LEN:
                break

            length = int.from_bytes(rx_buffer[4:6], byteorder="little", signed=False)
            if length > max_payload_length:
                del rx_buffer[0]
                continue

            frame_len = MIN_FRAME_LEN + length
            if len(rx_buffer) < frame_len:
                break

            frame = bytes(rx_buffer[:frame_len])
            del rx_buffer[:frame_len]
            parsed, error = parse_frame(frame)
            if parsed is not None:
                return parsed
            print(f"WARN ignored invalid frame: {error}", file=sys.stderr)

    return None


def format_chip_uid(payload):
    raw_hex = payload.hex().upper()
    groups = [raw_hex[index : index + 8] for index in range(0, len(raw_hex), 8)]
    return "-".join(groups)


def decode_nul_terminated_ascii(payload):
    text = payload.split(b"\x00", 1)[0]
    if not text:
        return None
    try:
        decoded = text.decode("ascii")
    except UnicodeDecodeError:
        return None
    if all(char.isprintable() for char in decoded):
        return decoded
    return None


def decode_payload(cmd, payload):
    if cmd == CMD_APP_VERSION:
        return decode_nul_terminated_ascii(payload) or payload.decode("ascii", errors="replace")
    if cmd == CMD_DEVICE_ADDR:
        if len(payload) != 1:
            return f"unexpected length={len(payload)} raw=0x{payload.hex().upper()}"
        return str(payload[0])
    if cmd == CMD_CHIP_UID:
        return decode_nul_terminated_ascii(payload) or format_chip_uid(payload)
    return f"0x{payload.hex().upper()}"


def parse_cmd(value):
    aliases = {
        "version": CMD_APP_VERSION,
        "app_version": CMD_APP_VERSION,
        "uid": CMD_CHIP_UID,
        "chip_uid": CMD_CHIP_UID,
        "serial": CMD_CHIP_UID,
        "addr": CMD_DEVICE_ADDR,
        "address": CMD_DEVICE_ADDR,
        "device_addr": CMD_DEVICE_ADDR,
    }
    lowered = value.lower()
    if lowered in aliases:
        return aliases[lowered]
    return int(value, 0)


def query(port, baudrate, device_addr, package_id, cmd, timeout, serial_timeout):
    request = build_get_frame(device_addr, package_id, cmd)
    with serial.Serial(
        port=port,
        baudrate=baudrate,
        bytesize=serial.EIGHTBITS,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        timeout=serial_timeout,
    ) as serial_obj:
        serial_obj.reset_input_buffer()
        serial_obj.reset_output_buffer()
        serial_obj.write(request)
        serial_obj.flush()

        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            frame = read_one_frame(
                serial_obj,
                timeout_sec=max(0.0, deadline - time.monotonic()),
                max_payload_length=4096,
            )
            if frame is None:
                break
            if frame["device_addr"] != device_addr:
                continue
            if frame["channel"] != CHANNEL_DEVICE_INFO:
                continue
            if frame["frame_type"] not in DEVICE_INFO_RESPONSE_TYPES:
                continue
            if frame["package_id"] != package_id:
                continue
            return request, frame

    return request, None


def main():
    parser = argparse.ArgumentParser(
        description="Query HWK pressure sensor device information on CHANNEL 0x01."
    )
    parser.add_argument("--port", default="/dev/ttyUSB0")
    parser.add_argument("--baudrate", type=int, default=460800)
    parser.add_argument("--addr", type=int, default=6, help="sensor device address, 0..15")
    parser.add_argument("--package-id", type=int, default=0, help="frame package ID, 0..63")
    parser.add_argument(
        "--cmd",
        type=parse_cmd,
        default=CMD_CHIP_UID,
        help="query command: uid/chip_uid/serial, version, addr, or numeric value",
    )
    parser.add_argument("--timeout", type=float, default=1.0)
    parser.add_argument("--serial-timeout", type=float, default=0.02)
    parser.add_argument(
        "--gripper-id",
        help="Optional real-world gripper id, for example l1/l2/r1/r2, printed with the result.",
    )
    args = parser.parse_args()

    port_path = Path(args.port)
    if not port_path.exists():
        print(f"serial port does not exist: {args.port}", file=sys.stderr)
        return 2

    try:
        request, frame = query(
            port=args.port,
            baudrate=args.baudrate,
            device_addr=args.addr,
            package_id=args.package_id,
            cmd=args.cmd,
            timeout=args.timeout,
            serial_timeout=args.serial_timeout,
        )
    except serial.SerialException as exc:
        print(f"serial error: {exc}", file=sys.stderr)
        return 2

    cmd_name = CMD_NAMES.get(args.cmd, f"cmd_0x{args.cmd:02X}")
    print(f"port: {args.port}")
    print(f"baudrate: {args.baudrate}")
    print(f"addr: {args.addr}")
    print(f"package_id: {args.package_id}")
    if args.gripper_id:
        print(f"gripper_id: {args.gripper_id}")
    print(f"cmd: 0x{args.cmd:02X} ({cmd_name})")
    print(f"request_hex: {request.hex(' ').upper()}")

    if frame is None:
        print("result: timeout/no matching ACK")
        return 1

    payload = frame["payload"]
    print("result: OK")
    print(f"response_hex: {frame['raw_frame'].hex(' ').upper()}")
    print(f"response_type: 0x{frame['frame_type']:02X}")
    print(f"payload_len: {len(payload)}")
    print(f"payload_hex: {payload.hex(' ').upper()}")
    value = decode_payload(args.cmd, payload)
    print(f"value: {value}")
    if args.gripper_id and args.cmd == CMD_CHIP_UID:
        print(f"binding_hint: {args.gripper_id} -> {value}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
