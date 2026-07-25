"""Custom Modbus-style frame codec for the Elephant myGripper-F100.

Ported from ``src/model_deploy/gripper_ctrl.py``. Pure functions only: no
serial, no ROS. A frame is::

    FE FE | len(0x08) | gripper_id | func | reg_hi reg_lo | data_hi data_lo | crc_hi crc_lo

CRC is CRC-16/MODBUS over everything before the CRC, emitted big-endian (to
match the reference implementation and captured golden vectors).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

HEADER = b"\xFE\xFE"
FRAME_LENGTH_BYTE = 0x08
FULL_FRAME_LEN = 11  # 2 header + 7 payload + 2 crc

# Function codes.
FUNC_READ = 0x03
FUNC_WRITE = 0x06

# Register addresses.
REG_ENABLE = 0x0A
REG_SET_ANGLE = 0x0B
REG_READ_ANGLE = 0x0C
REG_CLAMP = 0x0E
REG_STOP = 0x27

# Default gripper id (protocol id, same on both physical grippers).
DEFAULT_GRIPPER_ID = 0x0E


def _build_crc_table() -> Tuple[int, ...]:
    table = []
    for byte in range(256):
        crc = byte
        for _ in range(8):
            if crc & 0x0001:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
        table.append(crc)
    return tuple(table)


_CRC_TABLE = _build_crc_table()


def crc16(payload: bytes) -> bytes:
    """CRC-16/MODBUS over ``payload``, returned big-endian (2 bytes).

    Uses a precomputed 256-entry table; equivalent to the reference bit-loop.
    """

    crc = 0xFFFF
    for byte in payload:
        crc = (crc >> 8) ^ _CRC_TABLE[(crc ^ byte) & 0xFF]
    return crc.to_bytes(2, "big")


def build_frame(
    func_code: int,
    reg_addr: int,
    reg_data: int,
    gripper_id: int = DEFAULT_GRIPPER_ID,
) -> bytes:
    """Build a complete protocol frame including CRC."""

    payload = bytes(
        [
            FRAME_LENGTH_BYTE,
            gripper_id & 0xFF,
            func_code & 0xFF,
            (reg_addr >> 8) & 0xFF,
            reg_addr & 0xFF,
            (reg_data >> 8) & 0xFF,
            reg_data & 0xFF,
        ]
    )
    body = HEADER + payload
    return body + crc16(body)


def enable_frame(gripper_id: int = DEFAULT_GRIPPER_ID) -> bytes:
    """Frame that energizes the gripper (register 0x0A = 1)."""

    return build_frame(FUNC_WRITE, REG_ENABLE, 0x01, gripper_id)


def disable_frame(gripper_id: int = DEFAULT_GRIPPER_ID) -> bytes:
    """Frame that de-energizes the gripper (register 0x0A = 0)."""

    return build_frame(FUNC_WRITE, REG_ENABLE, 0x00, gripper_id)


def stop_frame(gripper_id: int = DEFAULT_GRIPPER_ID) -> bytes:
    """Frame that stops motion immediately (register 0x27 = 0)."""

    return build_frame(FUNC_WRITE, REG_STOP, 0x00, gripper_id)


def read_angle_frame(gripper_id: int = DEFAULT_GRIPPER_ID) -> bytes:
    """Frame that requests the current angle (read register 0x0C)."""

    return build_frame(FUNC_READ, REG_READ_ANGLE, 0x00, gripper_id)


def read_clamp_frame(gripper_id: int = DEFAULT_GRIPPER_ID) -> bytes:
    """Frame that requests the clamp status (read register 0x0E)."""

    return build_frame(FUNC_READ, REG_CLAMP, 0x00, gripper_id)


def build_set_angle_frame(angle: int, gripper_id: int = DEFAULT_GRIPPER_ID) -> bytes:
    """Frame that commands a target angle in [0, 100] (write register 0x0B)."""

    if not 0 <= angle <= 100:
        raise ValueError(f"angle must be in [0, 100], got {angle}")
    return build_frame(FUNC_WRITE, REG_SET_ANGLE, angle, gripper_id)


@dataclass(frozen=True)
class ParsedResponse:
    """A validated response frame."""

    func_code: int
    reg_addr: int
    data: int


def parse_response(
    resp: bytes,
    expected_reg: Optional[int] = None,
    gripper_id: int = DEFAULT_GRIPPER_ID,
) -> Tuple[Optional[ParsedResponse], str]:
    """Validate and decode a response frame.

    Returns ``(ParsedResponse, "")`` on success, or ``(None, reason)`` when the
    frame is too short, mis-headed, CRC-invalid, from the wrong id, or (when
    ``expected_reg`` is given) does not echo the expected register.
    """

    if resp is None or len(resp) < FULL_FRAME_LEN:
        return None, f"short frame: len={0 if resp is None else len(resp)}"
    frame = bytes(resp[:FULL_FRAME_LEN])

    if frame[0:2] != HEADER:
        return None, f"bad header: {frame[0:2].hex()}"
    if frame[2] != FRAME_LENGTH_BYTE:
        return None, f"bad length byte: {frame[2]:#04x}"
    if frame[3] != (gripper_id & 0xFF):
        return None, f"unexpected gripper_id: {frame[3]:#04x}"

    body = frame[:-2]
    if crc16(body) != frame[-2:]:
        return None, "crc mismatch"

    func_code = frame[4]
    reg_addr = (frame[5] << 8) | frame[6]
    data = (frame[7] << 8) | frame[8]

    if expected_reg is not None and reg_addr != expected_reg:
        return None, f"register echo mismatch: got {reg_addr:#06x}, want {expected_reg:#06x}"

    return ParsedResponse(func_code=func_code, reg_addr=reg_addr, data=data), ""
