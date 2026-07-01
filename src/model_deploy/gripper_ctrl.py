#!/usr/bin/env python3
"""
大象夹爪 myGripper-F100 控制脚本
用法: python3 gripper_ctrl.py <0.0~1.0>
  0.0 = 完全闭合, 1.0 = 完全张开
"""

import sys
import time
import serial

SERIAL_PORT = "/dev/ttyACM0"
BAUDRATE = 115200
GRIPPER_ID = 0x0E
HEADER = b"\xFE\xFE"


def crc16_modbus(data: bytes) -> bytes:
    """计算 CRC-16 MODBUS 校验码"""
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x0001:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return crc.to_bytes(2, "big")


def build_frame(func_code: int, reg_addr: int, reg_data: int) -> bytes:
    """构建自定义协议帧（含 CRC）"""
    length = 0x08
    payload = bytes([length, GRIPPER_ID, func_code,
                     (reg_addr >> 8) & 0xFF, reg_addr & 0xFF,
                     (reg_data >> 8) & 0xFF, reg_data & 0xFF])
    return HEADER + payload + crc16_modbus(HEADER + payload)


def send_cmd(ser: serial.Serial, frame: bytes, label: str):
    """发送指令并打印响应"""
    ser.write(frame)
    print(f"[{label}] 发送: {frame.hex()}")
    resp = ser.read(64)
    if resp:
        print(f"[{label}] 响应: {resp.hex()}")
    else:
        print(f"[{label}] 无响应")
    return resp


def main():
    # 解析参数
    if len(sys.argv) != 2:
        print("用法: python3 gripper_ctrl.py <0.0~1.0>")
        print("  0.0 = 完全闭合, 1.0 = 完全张开")
        sys.exit(1)

    try:
        ratio = float(sys.argv[1])
    except ValueError:
        print("错误: 请输入 0.0 ~ 1.0 之间的数值")
        sys.exit(1)

    if not 0.0 <= ratio <= 1.0:
        print("错误: 数值范围 0.0 ~ 1.0")
        sys.exit(1)

    # 归一化映射: 0.0 -> 角度0(闭合), 1.0 -> 角度100(张开)
    angle = int(round(ratio * 100))

    print(f"目标开合度: {ratio:.2f} → 角度: {angle}")

    # 打开串口
    ser = serial.Serial(SERIAL_PORT, BAUDRATE, timeout=1)

    # 1. 先上使能
    enable_frame = build_frame(func_code=0x06, reg_addr=0x0A, reg_data=0x01)
    send_cmd(ser, enable_frame, "上使能")
    time.sleep(0.1)

    # 2. 设置角度
    angle_frame = build_frame(func_code=0x06, reg_addr=0x0B, reg_data=angle)
    send_cmd(ser, angle_frame, f"设角度={angle}")
    time.sleep(0.5)

    # 3. 读取当前角度（确认）
    read_frame = build_frame(func_code=0x03, reg_addr=0x0C, reg_data=0x00)
    resp = send_cmd(ser, read_frame, "读角度")

    ser.close()


if __name__ == "__main__":
    main()
