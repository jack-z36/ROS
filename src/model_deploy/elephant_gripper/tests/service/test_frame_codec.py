"""Tests for the frame codec: CRC table equivalence and golden vectors."""

import pytest

from elephant_gripper.service import frame_codec as fc


def _bitloop_crc(payload: bytes) -> bytes:
    crc = 0xFFFF
    for byte in payload:
        crc ^= byte
        for _ in range(8):
            if crc & 0x0001:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return crc.to_bytes(2, "big")


def test_crc_table_matches_bitloop():
    for payload in (b"", b"\x00", b"\xFE\xFE\x08\x0E\x03\x00\x0C\x00\x00", bytes(range(32))):
        assert fc.crc16(payload) == _bitloop_crc(payload)


def _hx(s: str) -> bytes:
    return bytes.fromhex(s.replace(" ", ""))


def test_golden_read_angle_request():
    assert fc.read_angle_frame() == _hx("FE FE 08 0E 03 00 0C 00 00 B1 C0")


def test_golden_enable_frame():
    assert fc.enable_frame() == _hx("FE FE 08 0E 06 00 0A 00 01 70 2D")


def test_golden_stop_frame():
    assert fc.stop_frame() == _hx("FE FE 08 0E 06 00 27 00 00 B9 7C")


def test_parse_golden_read_angle_response():
    parsed, reason = fc.parse_response(
        _hx("FE FE 08 0E 03 00 0C 00 64 5A C1"), expected_reg=fc.REG_READ_ANGLE
    )
    assert reason == ""
    assert parsed is not None
    assert parsed.func_code == fc.FUNC_READ
    assert parsed.reg_addr == fc.REG_READ_ANGLE
    assert parsed.data == 100


def test_build_set_angle_roundtrip():
    frame = fc.build_set_angle_frame(42)
    parsed, reason = fc.parse_response(frame, expected_reg=fc.REG_SET_ANGLE)
    assert reason == ""
    assert parsed is not None
    assert parsed.data == 42


def test_build_set_angle_rejects_out_of_range():
    with pytest.raises(ValueError):
        fc.build_set_angle_frame(101)


def test_parse_short_frame():
    parsed, reason = fc.parse_response(b"\xFE\xFE\x08")
    assert parsed is None
    assert "short" in reason


def test_parse_bad_header():
    good = fc.read_angle_frame()
    bad = b"\x00\x00" + good[2:]
    parsed, reason = fc.parse_response(bad)
    assert parsed is None
    assert "header" in reason


def test_parse_crc_mismatch():
    good = bytearray(fc.read_angle_frame())
    good[-1] ^= 0xFF
    parsed, reason = fc.parse_response(bytes(good))
    assert parsed is None
    assert "crc" in reason


def test_parse_register_echo_mismatch():
    frame = fc.read_angle_frame()
    parsed, reason = fc.parse_response(frame, expected_reg=fc.REG_CLAMP)
    assert parsed is None
    assert "register echo" in reason


def test_parse_wrong_gripper_id():
    frame = fc.build_frame(fc.FUNC_READ, fc.REG_READ_ANGLE, 0, gripper_id=0x0E)
    parsed, reason = fc.parse_response(frame, gripper_id=0x0F)
    assert parsed is None
    assert "gripper_id" in reason
