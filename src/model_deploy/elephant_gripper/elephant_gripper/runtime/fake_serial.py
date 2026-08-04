"""A scripted in-memory serial stand-in for tests and ``use_fake_serial``.

Implements just the subset of ``serial.Serial`` used by
:class:`~elephant_gripper.runtime.serial_link.GripperSerialLink`:
``write``, ``read``, ``reset_input_buffer``, ``reset_output_buffer``,
``close`` and the ``is_open`` attribute.

The fake answers read-angle and read-clamp requests from a small internal
state, and echoes write acknowledgements. It lets the runtime and supervisor
be exercised with no hardware.
"""

from __future__ import annotations

import threading
from typing import Optional

from ..service import frame_codec as fc


class FakeSerial:
    """Deterministic loopback that emulates the gripper's request/response."""

    def __init__(
        self,
        port: str = "fake",
        baudrate: int = 115200,
        timeout: float = 0.05,
        gripper_id: int = fc.DEFAULT_GRIPPER_ID,
        initial_angle: int = 0,
        initial_clamp: int = 1,
        fail_open: bool = False,
        **_: object,
    ) -> None:
        if fail_open:
            raise OSError(f"FakeSerial configured to fail opening port={port}")
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self._gripper_id = gripper_id
        self.is_open = True
        self._lock = threading.Lock()
        self._angle = max(0, min(100, initial_angle))
        self._clamp = initial_clamp
        self._enabled = False
        self._pending = bytearray()
        # Counters exposed for test assertions.
        self.set_angle_count = 0
        self.stop_count = 0
        self.disable_count = 0
        self.enable_count = 0

    # -- serial.Serial subset -------------------------------------------------
    def write(self, frame: bytes) -> int:
        with self._lock:
            self._pending.extend(self._respond(bytes(frame)))
        return len(frame)

    def read(self, size: int = 1) -> bytes:
        with self._lock:
            chunk = bytes(self._pending[:size])
            del self._pending[:size]
        return chunk

    def reset_input_buffer(self) -> None:
        with self._lock:
            self._pending.clear()

    def reset_output_buffer(self) -> None:
        return None

    def flush(self) -> None:
        return None

    def close(self) -> None:
        self.is_open = False

    # -- helpers --------------------------------------------------------------
    def _respond(self, frame: bytes) -> bytes:
        parsed, _ = fc.parse_response(frame, gripper_id=self._gripper_id)
        if parsed is None:
            return b""
        reg = parsed.reg_addr
        func = parsed.func_code
        data = parsed.data

        if func == fc.FUNC_WRITE:
            if reg == fc.REG_ENABLE:
                self._enabled = bool(data)
                if data:
                    self.enable_count += 1
                else:
                    self.disable_count += 1
                return fc.build_frame(func, reg, data, self._gripper_id)
            if reg == fc.REG_SET_ANGLE:
                self.set_angle_count += 1
                self._angle = max(0, min(100, data))
                return fc.build_frame(func, reg, data, self._gripper_id)
            if reg == fc.REG_STOP:
                self.stop_count += 1
                return fc.build_frame(func, reg, data, self._gripper_id)
            return fc.build_frame(func, reg, data, self._gripper_id)

        if func == fc.FUNC_READ:
            if reg == fc.REG_READ_ANGLE:
                return fc.build_frame(func, reg, self._angle, self._gripper_id)
            if reg == fc.REG_CLAMP:
                return fc.build_frame(func, reg, self._clamp, self._gripper_id)
        return b""

    # -- test-only mutators ---------------------------------------------------
    def set_reported_angle(self, angle: int) -> None:
        with self._lock:
            self._angle = max(0, min(100, angle))

    def set_reported_clamp(self, clamp: int) -> None:
        with self._lock:
            self._clamp = clamp


def make_fake_serial_factory(
    initial_angle: int = 0,
    initial_clamp: int = 1,
) -> "FakeSerialFactory":
    """Return a callable usable as the serial factory injected into the link."""

    def factory(port: str, baudrate: int, timeout: float, gripper_id: int) -> FakeSerial:
        return FakeSerial(
            port=port,
            baudrate=baudrate,
            timeout=timeout,
            gripper_id=gripper_id,
            initial_angle=initial_angle,
            initial_clamp=initial_clamp,
        )

    return factory


# Type alias for readability.
FakeSerialFactory = Optional[object]
