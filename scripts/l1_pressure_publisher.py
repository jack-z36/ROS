#!/usr/bin/env python3
"""Single-sensor L1 pressure publisher for Octopus display testing.

Reads from ONE real HWK sensor via serial, publishes to ONE PressureFrame topic.

Usage:
  python3 scripts/l1_pressure_publisher.py
  python3 scripts/l1_pressure_publisher.py --port /dev/ttyUSB0 --baud 921600 --addr 6 --rate 20
"""

import argparse
import struct
import sys
import time

import rclpy
from rclpy.node import Node
from hwk_pressure_interfaces.msg import PressureFrame


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
    id_ch = ((dev_addr & 0x0F) << 4) | CHAN_DATA
    flags = ((pkg_id & 0x3F) << 2) | TYPE_GET
    payload = bytes((0x01,))
    cs = crc16(payload)
    return b"".join([HEAD, bytes((id_ch, flags)),
                     len(payload).to_bytes(2, "little"),
                     payload, cs.to_bytes(2, "little"), TAIL])


def read_one_frame(ser, timeout=1.0, max_payload_len=4096):
    """Read a single valid data-channel ACK frame. Returns dict or None."""
    import serial as _serial
    buf = bytearray()
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            chunk = ser.read(max(1, ser.in_waiting or 512))
        except _serial.SerialException:
            return None
        if chunk:
            buf.extend(chunk)
        while True:
            idx = buf.find(HEAD)
            if idx < 0:
                if buf[:1] != HEAD[:1]:
                    buf.clear()
                else:
                    del buf[:-1]
                break
            if idx > 0:
                del buf[:idx]
            if len(buf) < MIN_FRAME_LEN:
                break
            length = int.from_bytes(buf[4:6], "little")
            if length > max_payload_len:
                del buf[:1]
                continue
            flen = MIN_FRAME_LEN + length
            if len(buf) < flen:
                break
            raw = bytes(buf[:flen])
            del buf[:flen]
            if raw[-2:] != TAIL:
                continue
            id_ch = raw[2]
            flags = raw[3]
            ch = id_ch & 0x0F
            ft = flags & 0x03
            if ch != CHAN_DATA or ft not in (0x02, 0x03):
                continue  # skip non-data frames
            p = raw[6:6 + length]
            exp_crc = int.from_bytes(raw[6 + length:8 + length], "little")
            if crc16(p) != exp_crc:
                continue
            return {
                "addr": (id_ch >> 4) & 0x0F,
                "pkg_id": (flags >> 2) & 0x3F,
                "payload": bytes(p),
            }
    return None


class L1PressurePublisher(Node):
    def __init__(self, port, baud, addr, topic, rate):
        super().__init__("l1_pressure_publisher")
        self._addr = addr
        self._rate = rate
        self._pkg_id = 0

        self._pub = self.create_publisher(PressureFrame, topic, 10)

        import serial
        self._ser = serial.Serial(port, baudrate=baud, timeout=0.02)
        self._ser.reset_input_buffer()
        self._ser.reset_output_buffer()
        self.get_logger().info(f"Opened {port} @ {baud} baud, addr={addr}, topic={topic}")

    def spin_once(self):
        req = build_get_frame(self._addr, self._pkg_id)
        self._ser.write(req)
        self._ser.flush()

        frame = read_one_frame(self._ser, timeout=max(0.5, 1.5 / max(self._rate, 1.0)))
        if frame is None:
            return False

        payload = frame["payload"]
        self._pkg_id = (self._pkg_id + 1) % 64

        if len(payload) < 4:
            return False

        total_pkts = payload[0]
        pkt_idx = payload[1]
        cols = payload[2]
        rows = payload[3]
        data_bytes = payload[4:]
        n = len(data_bytes) // 2
        values = list(struct.unpack_from(f"<{n}H", data_bytes, 0)) if data_bytes else []

        if not values:
            return False

        msg = PressureFrame()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = "pressure_sensor/left_hand/gripper_1"
        msg.hand = "left_hand"
        msg.gripper = "gripper_1"
        msg.device_addr = frame["addr"]
        msg.package_id = frame["pkg_id"]
        msg.total_packets = total_pkts
        msg.packet_index = pkt_idx
        msg.rows = max(rows, 1) if rows > 0 else 6
        msg.cols = max(cols, 1) if cols > 0 else 15
        msg.data = values
        msg.raw_payload = list(payload)

        self._pub.publish(msg)
        return True

    def close(self):
        self._ser.close()


def main():
    parser = argparse.ArgumentParser(description="L1 single-sensor pressure publisher")
    parser.add_argument("--port", default="/dev/ttyUSB0")
    parser.add_argument("--baud", type=int, default=921600)
    parser.add_argument("--addr", type=int, default=6, help="sensor device address, 0..15")
    parser.add_argument("--rate", type=float, default=20, help="poll rate in Hz")
    parser.add_argument("--topic", default="/pressure/left_hand/gripper_1")
    args = parser.parse_args()

    rclpy.init(args=sys.argv)
    node = L1PressurePublisher(args.port, args.baud, args.addr, args.topic, args.rate)

    period = 1.0 / max(args.rate, 1.0)
    try:
        while rclpy.ok():
            t0 = time.monotonic()
            ok = node.spin_once()
            elapsed = time.monotonic() - t0
            time.sleep(max(0.0, period - elapsed))
    except KeyboardInterrupt:
        pass
    finally:
        node.close()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
