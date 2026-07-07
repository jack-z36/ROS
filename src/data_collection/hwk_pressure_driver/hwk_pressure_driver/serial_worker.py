"""Serial-port worker for one configured HWK pressure sensor bus."""

from __future__ import annotations

import threading
import time
import traceback
from typing import Any, Callable, Dict, Optional

import serial

from .config import SerialPortConfig
from .protocol import (
    CHAN_DATA,
    CHAN_DEVICE_INFO,
    CMD_CHIP_UID,
    DEVICE_INFO_RESPONSE_TYPES,
    HEAD,
    MIN_FRAME_LEN,
    TAIL,
    TYPE_ACK,
    ParsedFrame,
)
from .protocol import (
    build_get_data_frame,
    build_get_device_info_frame,
    decode_chip_uid_payload,
    parse_frame,
)


FrameCallback = Callable[[str, ParsedFrame], None]


class SerialWorker:
    """Owns one serial port, one reader thread, and one RX parser buffer."""

    def __init__(
        self,
        config: SerialPortConfig,
        serial_timeout: float,
        frame_callback: FrameCallback,
        logger: Any,
        identity_query_timeout: float = 1.0,
        identity_query_package_id: int = 29,
        max_payload_length: int = 4096,
    ) -> None:
        self.config = config
        self.name = config.name
        self._serial_timeout = serial_timeout
        self._frame_callback = frame_callback
        self._logger = logger
        self._identity_query_timeout = identity_query_timeout
        self._identity_query_package_id = identity_query_package_id
        self._max_payload_length = max_payload_length

        self._known_addrs = {sensor.device_addr for sensor in config.sensors}
        self.identity_by_addr: Dict[int, str] = {}
        self._rx_buffer = bytearray()
        self._write_lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._serial: Optional[serial.Serial] = None

    @property
    def is_open(self) -> bool:
        return self._serial is not None and self._serial.is_open

    def add_identity_addrs(self, addrs: set[int]) -> None:
        """Add extra device addresses to probe during identity discovery."""
        self._known_addrs |= addrs

    def start(self) -> bool:
        """Open the serial port and start the reader thread."""

        if self._thread is not None:
            return self.is_open

        try:
            self._serial = serial.Serial(
                port=self.config.port,
                baudrate=self.config.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=self._serial_timeout,
            )
        except Exception as exc:
            self._logger.error(
                f"Serial port open failed: name={self.name}, port={self.config.port}, "
                f"baudrate={self.config.baudrate}, error={exc}"
            )
            return False

        self._logger.info(
            f"Serial port opened: name={self.name}, port={self.config.port}, "
            f"baudrate={self.config.baudrate}, timeout={self._serial_timeout}"
        )

        self._query_configured_identities()

        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._reader_loop,
            name=f"pressure-reader-{self.name}",
            daemon=True,
        )
        self._thread.start()
        return True

    def stop(self, join_timeout: float = 1.0) -> None:
        """Stop the reader thread and close the serial port."""

        self._stop_event.set()
        thread = self._thread
        if thread is not None and thread.is_alive():
            thread.join(timeout=join_timeout)
            if thread.is_alive():
                self._logger.warn(f"Reader thread did not stop in time: name={self.name}")
        self._thread = None

        serial_obj = self._serial
        self._serial = None
        if serial_obj is not None:
            try:
                if serial_obj.is_open:
                    serial_obj.close()
                    self._logger.info(f"Serial port closed: name={self.name}, port={self.config.port}")
            except Exception as exc:
                self._logger.error(
                    f"Serial port close error: name={self.name}, port={self.config.port}, error={exc}"
                )

    def send_get_data(self, device_addr: int, package_id: int) -> bool:
        """Send a pressure-data GET request to one device address."""

        serial_obj = self._serial
        if serial_obj is None or not serial_obj.is_open:
            return False

        try:
            frame = build_get_data_frame(device_addr=device_addr, package_id=package_id)
        except ValueError as exc:
            self._logger.error(
                f"Failed to build GET frame: serial={self.name}, device_addr={device_addr}, "
                f"package_id={package_id}, error={exc}"
            )
            return False

        try:
            with self._write_lock:
                serial_obj.write(frame)
        except Exception as exc:
            self._logger.error(
                f"Serial write error: name={self.name}, port={self.config.port}, "
                f"device_addr={device_addr}, package_id={package_id}, error={exc}"
            )
            return False
        return True

    def _query_configured_identities(self) -> None:
        self.identity_by_addr.clear()
        for device_addr in sorted(self._known_addrs):
            uid = self._query_chip_uid(device_addr)
            if uid:
                self.identity_by_addr[device_addr] = uid
                self._logger.info(
                    f"HWK identity detected: serial={self.name}, port={self.config.port}, "
                    f"device_addr={device_addr}, HWK_CHIP_UID={uid}"
                )
            else:
                self._logger.error(
                    f"HWK identity query failed: serial={self.name}, port={self.config.port}, "
                    f"device_addr={device_addr}; this sensor will not be bound to a topic"
                )

    def _query_chip_uid(self, device_addr: int) -> Optional[str]:
        serial_obj = self._serial
        if serial_obj is None or not serial_obj.is_open:
            return None

        try:
            request = build_get_device_info_frame(
                device_addr=device_addr,
                package_id=self._identity_query_package_id,
                cmd=CMD_CHIP_UID,
            )
        except ValueError as exc:
            self._logger.error(
                f"Failed to build identity GET frame: serial={self.name}, "
                f"device_addr={device_addr}, error={exc}"
            )
            return None

        local_buffer = bytearray()
        deadline = time.monotonic() + self._identity_query_timeout

        try:
            with self._write_lock:
                serial_obj.reset_input_buffer()
                serial_obj.reset_output_buffer()
                serial_obj.write(request)
                serial_obj.flush()
        except Exception as exc:
            self._logger.error(
                f"Serial identity query write error: name={self.name}, port={self.config.port}, "
                f"device_addr={device_addr}, error={exc}"
            )
            return None

        while time.monotonic() < deadline:
            try:
                chunk = serial_obj.read(512)
            except Exception as exc:
                self._logger.error(
                    f"Serial identity query read error: name={self.name}, port={self.config.port}, "
                    f"device_addr={device_addr}, error={exc}"
                )
                return None

            if chunk:
                local_buffer.extend(chunk)

            frame = self._pop_identity_frame(local_buffer)
            while frame is not None:
                if (
                    frame.device_addr == device_addr
                    and frame.channel == CHAN_DEVICE_INFO
                    and frame.frame_type in DEVICE_INFO_RESPONSE_TYPES
                    and frame.package_id == self._identity_query_package_id
                ):
                    return decode_chip_uid_payload(frame.payload)
                frame = self._pop_identity_frame(local_buffer)

        return None

    def _pop_identity_frame(self, rx_buffer: bytearray) -> Optional[ParsedFrame]:
        while True:
            head_index = rx_buffer.find(HEAD)
            if head_index < 0:
                if rx_buffer[-1:] == HEAD[:1]:
                    del rx_buffer[:-1]
                else:
                    rx_buffer.clear()
                return None
            if head_index > 0:
                del rx_buffer[:head_index]

            if len(rx_buffer) < MIN_FRAME_LEN:
                return None

            length = int.from_bytes(rx_buffer[4:6], byteorder="little", signed=False)
            if length > self._max_payload_length:
                self._logger.warn(
                    f"Identity payload length too large on serial={self.name}: "
                    f"length={length}, max={self._max_payload_length}; resyncing"
                )
                del rx_buffer[0]
                continue

            frame_len = MIN_FRAME_LEN + length
            if len(rx_buffer) < frame_len:
                return None

            frame_bytes = bytes(rx_buffer[:frame_len])
            del rx_buffer[:frame_len]
            parsed, error = parse_frame(frame_bytes)
            if parsed is None:
                self._logger.warn(f"Identity frame parse error on serial={self.name}: {error}")
                continue
            return parsed

    def _reader_loop(self) -> None:
        while not self._stop_event.is_set():
            serial_obj = self._serial
            if serial_obj is None or not serial_obj.is_open:
                time.sleep(0.05)
                continue

            try:
                chunk = serial_obj.read(512)
                if chunk:
                    self._rx_buffer.extend(chunk)
                    self._process_rx_buffer()
            except Exception as exc:
                self._logger.error(
                    f"Serial read error: name={self.name}, port={self.config.port}, "
                    f"error={exc}\n{traceback.format_exc()}"
                )
                time.sleep(0.05)

    def _process_rx_buffer(self) -> None:
        while True:
            head_index = self._rx_buffer.find(HEAD)
            if head_index < 0:
                self._drop_until_possible_head()
                return
            if head_index > 0:
                del self._rx_buffer[:head_index]

            if len(self._rx_buffer) < MIN_FRAME_LEN:
                return

            length = int.from_bytes(self._rx_buffer[4:6], byteorder="little", signed=False)
            if length > self._max_payload_length:
                self._logger.warn(
                    f"Payload length too large on serial={self.name}: length={length}, "
                    f"max={self._max_payload_length}; resyncing"
                )
                del self._rx_buffer[0]
                continue

            frame_len = MIN_FRAME_LEN + length
            if len(self._rx_buffer) < frame_len:
                return

            frame = bytes(self._rx_buffer[:frame_len])
            if frame[-2:] != TAIL:
                self._logger.warn(
                    f"Frame tail error on serial={self.name}: dropping current frame head"
                )
                del self._rx_buffer[0]
                continue

            del self._rx_buffer[:frame_len]
            parsed, error = parse_frame(frame)
            if parsed is None:
                if error and "CRC" in error:
                    self._logger.warn(f"CRC error on serial={self.name}: {error}")
                else:
                    self._logger.warn(f"Frame parse error on serial={self.name}: {error}")
                continue

            if parsed.channel != CHAN_DATA:
                self._logger.debug(
                    f"Ignoring non-data channel frame on serial={self.name}: "
                    f"channel=0x{parsed.channel:02X}, addr={parsed.device_addr}"
                )
                continue
            if parsed.frame_type != TYPE_ACK:
                self._logger.debug(
                    f"Ignoring non-ACK frame on serial={self.name}: "
                    f"type=0x{parsed.frame_type:02X}, addr={parsed.device_addr}"
                )
                continue
            if parsed.device_addr not in self._known_addrs:
                self._logger.warn(
                    f"Unknown device_addr on serial={self.name}: addr={parsed.device_addr}; "
                    "frame ignored"
                )
                continue

            try:
                self._frame_callback(self.name, parsed)
            except Exception as exc:
                self._logger.error(
                    f"Frame callback error on serial={self.name}: error={exc}\n"
                    f"{traceback.format_exc()}"
                )

    def _drop_until_possible_head(self) -> None:
        if not self._rx_buffer:
            return
        if self._rx_buffer[-1] == HEAD[0]:
            del self._rx_buffer[:-1]
        else:
            self._rx_buffer.clear()
