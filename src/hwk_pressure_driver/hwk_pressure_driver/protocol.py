"""Frame helpers for the HWK pressure sensor serial protocol."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple


HEAD = bytes((0x3C, 0x3C))
TAIL = bytes((0x3E, 0x3E))

CHAN_DEVICE_INFO = 0x01
CHAN_DATA = 0x02
TYPE_GET = 0x01
TYPE_DEVICE_INFO_RESPONSE = 0x02
TYPE_ACK = 0x03
DEVICE_INFO_RESPONSE_TYPES = (TYPE_DEVICE_INFO_RESPONSE, TYPE_ACK)

MIN_FRAME_LEN = 10
GET_PRESSURE_PAYLOAD = bytes((0x01,))
CMD_CHIP_UID = 0x05


@dataclass(frozen=True)
class ParsedFrame:
    """A syntactically valid protocol frame."""

    device_addr: int
    channel: int
    frame_type: int
    package_id: int
    length: int
    payload: bytes
    checksum: int
    raw_frame: bytes


def crc16(payload: bytes) -> int:
    """Calculate CRC16 over payload bytes only."""

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
    """Build a GET pressure-data request frame."""

    if not 0 <= device_addr <= 0x0F:
        raise ValueError(f"device_addr must be in range 0..15, got {device_addr}")
    if not 0 <= package_id <= 0x3F:
        raise ValueError(f"package_id must be in range 0..63, got {package_id}")

    id_channel = ((device_addr & 0x0F) << 4) | CHAN_DATA
    flags = ((package_id & 0x3F) << 2) | TYPE_GET
    payload = GET_PRESSURE_PAYLOAD
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


def build_get_device_info_frame(device_addr: int, package_id: int, cmd: int) -> bytes:
    """Build a GET request on the device-info channel."""

    if not 0 <= device_addr <= 0x0F:
        raise ValueError(f"device_addr must be in range 0..15, got {device_addr}")
    if not 0 <= package_id <= 0x3F:
        raise ValueError(f"package_id must be in range 0..63, got {package_id}")
    if not 0 <= cmd <= 0xFF:
        raise ValueError(f"cmd must be in range 0..255, got {cmd}")

    id_channel = ((device_addr & 0x0F) << 4) | CHAN_DEVICE_INFO
    flags = ((package_id & 0x3F) << 2) | TYPE_GET
    payload = bytes((cmd,))
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


def decode_chip_uid_payload(payload: bytes) -> str:
    """Decode a chip UID payload into the canonical string used by config files."""

    text = payload.split(b"\x00", 1)[0]
    if text:
        try:
            decoded = text.decode("ascii")
        except UnicodeDecodeError:
            decoded = ""
        if decoded and all(char.isprintable() for char in decoded):
            return decoded

    raw_hex = payload.hex().upper()
    groups = [raw_hex[index : index + 8] for index in range(0, len(raw_hex), 8)]
    return "-".join(groups)


def parse_frame(frame: bytes) -> Tuple[Optional[ParsedFrame], Optional[str]]:
    """Parse one complete frame.

    The function returns ``(ParsedFrame, None)`` on success and
    ``(None, reason)`` on failure, so caller threads can keep running safely.
    """

    if len(frame) < MIN_FRAME_LEN:
        return None, f"frame too short: {len(frame)} bytes"
    if frame[:2] != HEAD:
        return None, "frame head error"

    length = int.from_bytes(frame[4:6], byteorder="little", signed=False)
    expected_len = MIN_FRAME_LEN + length
    if len(frame) != expected_len:
        return None, f"frame length mismatch: expected {expected_len}, got {len(frame)}"
    if frame[-2:] != TAIL:
        return None, "frame tail error"

    id_channel = frame[2]
    flags = frame[3]
    payload_start = 6
    payload_end = payload_start + length
    payload = frame[payload_start:payload_end]
    expected_crc = int.from_bytes(
        frame[payload_end : payload_end + 2], byteorder="little", signed=False
    )
    actual_crc = crc16(payload)
    if expected_crc != actual_crc:
        return (
            None,
            f"CRC error: received=0x{expected_crc:04X}, calculated=0x{actual_crc:04X}",
        )

    return (
        ParsedFrame(
            device_addr=(id_channel >> 4) & 0x0F,
            channel=id_channel & 0x0F,
            frame_type=flags & 0x03,
            package_id=(flags >> 2) & 0x3F,
            length=length,
            payload=bytes(payload),
            checksum=expected_crc,
            raw_frame=bytes(frame),
        ),
        None,
    )
