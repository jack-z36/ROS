#!/usr/bin/env python3
"""Mock pressure publisher — simulates 4 HWK sensor topics for Octopus display testing.

Publishes /pressure/{left,right}_hand/gripper_{1,2} with sinusoidal pressure patterns.
"""

import math
import sys
import time

import rclpy
from rclpy.node import Node
from hwk_pressure_interfaces.msg import PressureFrame


def make_frame(node, hand, gripper, rows=6, cols=15, t=0.0, base_seed=0):
    """Build a PressureFrame with sinusoidal simulated data."""
    msg = PressureFrame()
    msg.header.stamp = node.get_clock().now().to_msg()
    msg.header.frame_id = f"pressure_sensor/{hand}/{gripper}"
    msg.hand = hand
    msg.gripper = gripper
    msg.device_addr = 6
    msg.package_id = int(t * 100) % 64
    msg.total_packets = 1
    msg.packet_index = 1
    msg.rows = rows
    msg.cols = cols
    msg.raw_payload = []

    n = rows * cols  # 90
    phase = base_seed * 0.7
    # generate a pressure distribution: center higher, edges lower, modulated by sin
    for r in range(rows):
        for c in range(cols):
            # distance from center gives a bell shape
            dist_r = (r - (rows - 1) / 2.0) / (rows / 2.0)
            dist_c = (c - (cols - 1) / 2.0) / (cols / 2.0)
            dist = math.sqrt(dist_r**2 + dist_c**2)
            bell = math.exp(-dist * 1.8)
            # sinusoidal time modulation, slightly offset per unit
            val = bell * (0.6 + 0.4 * math.sin(t * 3.0 + phase + r * 0.3 + c * 0.1))
            msg.data.append(max(0, min(65535, int(val * 8000))))

    return msg


def main():
    rclpy.init(args=sys.argv)
    node = Node("mock_pressure_publisher")

    topics = [
        ("/pressure/left_hand/gripper_1", "left_hand", "gripper_1", 0),
        ("/pressure/left_hand/gripper_2", "left_hand", "gripper_2", 1),
        ("/pressure/right_hand/gripper_1", "right_hand", "gripper_1", 2),
        ("/pressure/right_hand/gripper_2", "right_hand", "gripper_2", 3),
    ]

    pubs = []
    for topic, hand, gripper, seed in topics:
        pub = node.create_publisher(PressureFrame, topic, 10)
        pubs.append((pub, hand, gripper, seed))
        node.get_logger().info(f"Publishing to {topic}")

    rate = 20.0  # Hz — lower than 100Hz for easier observation
    period = 1.0 / rate
    t0 = time.monotonic()

    try:
        while rclpy.ok():
            now = time.monotonic()
            elapsed = now - t0
            for pub, hand, gripper, seed in pubs:
                frame = make_frame(node, hand, gripper, t=elapsed, base_seed=seed)
                pub.publish(frame)
            time.sleep(max(0.0, period - (time.monotonic() - now)))
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
