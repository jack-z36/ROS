"""One serial link + one transaction worker thread per gripper.

The worker owns all serial I/O so ROS callbacks never block. ROS callbacks
only write the latest-command slot (``submit_command``) or read snapshots
(``latest_state`` / ``health_signal``), all O(1) and non-blocking.

Safety:
- All serial exceptions are caught inside the loop; the link marks itself
  disconnected, backs off exponentially and retries. It never raises into the
  worker loop.
- ``trigger_estop`` preempts the worker: it takes the write lock and sends
  stop + disable immediately, and blocks any further set-angle until cleared.
"""

from __future__ import annotations

import threading
import time
from typing import Any, Callable, Optional

from ..config.schema import GripperLinkConfig
from ..service import frame_codec as fc
from ..service.health_aggregator import LinkHealthInput
from ..service.mapping import angle_to_width, width_to_angle
from ..types.gripper_types import (
    ClampStatus,
    GripperCommand,
    GripperStateSample,
)

# Signature: (port, baudrate, timeout, gripper_id) -> serial-like object.
SerialFactory = Callable[[str, int, float, int], Any]


def _default_serial_factory(port: str, baudrate: int, timeout: float, gripper_id: int) -> Any:
    import serial  # local import so pure layers never require pyserial

    return serial.Serial(
        port=port,
        baudrate=baudrate,
        bytesize=serial.EIGHTBITS,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        timeout=timeout,
    )


class GripperSerialLink:
    """Owns one serial port and one transaction thread for one gripper."""

    def __init__(
        self,
        config: GripperLinkConfig,
        logger: Any = None,
        serial_factory: Optional[SerialFactory] = None,
        error_degraded_threshold: int = 3,
        error_fault_threshold: int = 10,
    ) -> None:
        self._config = config
        self._logger = logger
        self._serial_factory = serial_factory or _default_serial_factory
        self._error_degraded_threshold = error_degraded_threshold
        self._error_fault_threshold = error_fault_threshold

        self._serial: Optional[Any] = None
        self._write_lock = threading.Lock()
        self._state_lock = threading.Lock()
        self._stop_event = threading.Event()
        self._estop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

        # Latest-command-wins slot.
        self._pending_command: Optional[GripperCommand] = None
        # Latest telemetry snapshot.
        self._latest_state = GripperStateSample.placeholder(config.side)

        # Health bookkeeping (guarded by _state_lock).
        self._connected = False
        self._consecutive_errors = 0
        self._last_rx_monotonic: Optional[float] = None
        self._last_detail = ""

    @property
    def side(self):
        return self._config.side

    # -- lifecycle ------------------------------------------------------------
    def start(self) -> None:
        if self._thread is not None:
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run,
            name=f"gripper-{self._config.side.value}",
            daemon=True,
        )
        self._thread.start()

    def stop(self, join_timeout: float = 2.0) -> None:
        self._stop_event.set()
        thread = self._thread
        if thread is not None and thread.is_alive():
            thread.join(timeout=join_timeout)
        self._thread = None
        # Best-effort disable + close on shutdown.
        with self._write_lock:
            self._safe_disable_locked()
            self._close_serial_locked()

    # -- ROS-callback-facing API (non-blocking) -------------------------------
    def submit_command(self, command: GripperCommand) -> None:
        """Store the newest target (latest-command-wins). O(1), non-blocking."""

        with self._state_lock:
            self._pending_command = command

    def latest_state(self) -> GripperStateSample:
        with self._state_lock:
            return self._latest_state

    def health_signal(self, now_monotonic_s: float) -> LinkHealthInput:
        with self._state_lock:
            since_rx = (
                None
                if self._last_rx_monotonic is None
                else now_monotonic_s - self._last_rx_monotonic
            )
            return LinkHealthInput(
                side=self._config.side,
                connected=self._connected,
                consecutive_errors=self._consecutive_errors,
                seconds_since_rx=since_rx,
                last_detail=self._last_detail,
            )

    # -- estop ----------------------------------------------------------------
    def trigger_estop(self) -> None:
        """Preempt the worker and immediately stop + disable the gripper."""

        self._estop_event.set()
        with self._write_lock:
            serial_obj = self._serial
            if serial_obj is None:
                return
            try:
                serial_obj.write(fc.stop_frame(self._config.gripper_id))
                serial_obj.write(fc.disable_frame(self._config.gripper_id))
            except Exception as exc:  # noqa: BLE001 - never raise from estop
                self._log("error", f"estop write failed on {self._config.side.value}: {exc}")

    def clear_estop(self) -> None:
        self._estop_event.clear()

    @property
    def estop_active(self) -> bool:
        return self._estop_event.is_set()

    # -- worker loop ----------------------------------------------------------
    def _run(self) -> None:
        backoff = self._config.reconnect_backoff_min_s
        while not self._stop_event.is_set():
            if self._serial is None:
                if not self._open_serial():
                    self._interruptible_sleep(backoff)
                    backoff = min(backoff * 2.0, self._config.reconnect_backoff_max_s)
                    continue
                backoff = self._config.reconnect_backoff_min_s

            try:
                self._transaction_cycle()
            except Exception as exc:  # noqa: BLE001 - loop must never die
                self._record_error(f"transaction error: {exc}")
                with self._write_lock:
                    self._close_serial_locked()
                self._interruptible_sleep(backoff)
                backoff = min(backoff * 2.0, self._config.reconnect_backoff_max_s)
                continue

            period = 1.0 / self._config.poll_hz
            self._interruptible_sleep(period)

    def _open_serial(self) -> bool:
        try:
            serial_obj = self._serial_factory(
                self._config.port,
                self._config.baudrate,
                self._config.serial_timeout_s,
                self._config.gripper_id,
            )
        except Exception as exc:  # noqa: BLE001
            self._record_error(f"open failed: {exc}")
            self._set_connected(False)
            return False

        self._serial = serial_obj
        self._set_connected(True)
        self._reset_errors()
        self._log("info", f"serial opened: side={self._config.side.value}, port={self._config.port}")
        # Energize unless an estop is latched.
        if not self._estop_event.is_set():
            with self._write_lock:
                try:
                    serial_obj.write(fc.enable_frame(self._config.gripper_id))
                except Exception as exc:  # noqa: BLE001
                    self._record_error(f"enable failed: {exc}")
        if self._config.enable_wait_s > 0:
            self._interruptible_sleep(self._config.enable_wait_s)
        return True

    def _transaction_cycle(self) -> None:
        serial_obj = self._serial
        if serial_obj is None:
            return

        # 1) Apply the newest command if allowed (not estopped).
        command = self._take_pending_command()
        if command is not None and not self._estop_event.is_set():
            angle = width_to_angle(command.target_width, self._config.calibration)
            with self._write_lock:
                if not self._estop_event.is_set():
                    serial_obj.write(fc.build_set_angle_frame(angle, self._config.gripper_id))
            if self._config.set_angle_wait_s > 0:
                self._interruptible_sleep(self._config.set_angle_wait_s)

        # 2) Poll current angle.
        angle_resp = self._request(
            fc.read_angle_frame(self._config.gripper_id), fc.REG_READ_ANGLE
        )
        if angle_resp is None:
            self._record_error("no/invalid angle response")
            return

        # 3) Poll clamp status (best-effort; failure does not fault the link).
        clamp_status = ClampStatus.MOVING
        clamp_resp = self._request(
            fc.read_clamp_frame(self._config.gripper_id), fc.REG_CLAMP
        )
        if clamp_resp is not None:
            clamp_status = ClampStatus.from_raw(clamp_resp.data)

        width = angle_to_width(angle_resp.data, self._config.calibration)
        now = time.monotonic()
        sample = GripperStateSample(
            side=self._config.side,
            width=width,
            angle=max(0, min(100, angle_resp.data)),
            clamp_status=clamp_status,
            monotonic_s=now,
            valid=True,
        )
        with self._state_lock:
            self._latest_state = sample
            self._last_rx_monotonic = now
            self._consecutive_errors = 0
            self._last_detail = ""

    def _request(self, frame: bytes, expected_reg: int) -> Optional[fc.ParsedResponse]:
        serial_obj = self._serial
        if serial_obj is None:
            return None
        with self._write_lock:
            serial_obj.reset_input_buffer()
            serial_obj.write(frame)
        resp = serial_obj.read(fc.FULL_FRAME_LEN)
        parsed, reason = fc.parse_response(
            resp, expected_reg=expected_reg, gripper_id=self._config.gripper_id
        )
        if parsed is None:
            self._last_detail = reason
            return None
        return parsed

    # -- internal helpers -----------------------------------------------------
    def _take_pending_command(self) -> Optional[GripperCommand]:
        with self._state_lock:
            command = self._pending_command
            self._pending_command = None
            return command

    def _safe_disable_locked(self) -> None:
        serial_obj = self._serial
        if serial_obj is None:
            return
        try:
            serial_obj.write(fc.disable_frame(self._config.gripper_id))
        except Exception as exc:  # noqa: BLE001
            self._log("warn", f"disable-on-close failed: {exc}")

    def _close_serial_locked(self) -> None:
        serial_obj = self._serial
        self._serial = None
        self._set_connected(False)
        if serial_obj is None:
            return
        try:
            if getattr(serial_obj, "is_open", False):
                serial_obj.close()
        except Exception as exc:  # noqa: BLE001
            self._log("warn", f"serial close failed: {exc}")

    def _record_error(self, detail: str) -> None:
        with self._state_lock:
            self._consecutive_errors += 1
            self._last_detail = detail
        self._log("warn", f"{self._config.side.value}: {detail}")

    def _reset_errors(self) -> None:
        with self._state_lock:
            self._consecutive_errors = 0
            self._last_detail = ""

    def _set_connected(self, connected: bool) -> None:
        with self._state_lock:
            self._connected = connected

    def _interruptible_sleep(self, seconds: float) -> None:
        if seconds <= 0:
            return
        self._stop_event.wait(timeout=seconds)

    def _log(self, level: str, message: str) -> None:
        if self._logger is None:
            return
        getattr(self._logger, level, self._logger.info)(message)
