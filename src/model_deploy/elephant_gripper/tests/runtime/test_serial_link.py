"""Tests for the serial link worker using an injected FakeSerial."""

import inspect
import time

from elephant_gripper.config.schema import GripperLinkConfig
from elephant_gripper.runtime.fake_serial import FakeSerial
from elephant_gripper.runtime.serial_link import GripperSerialLink
from elephant_gripper.types.gripper_types import GripperCommand, GripperSide


def _link_config(side=GripperSide.LEFT, **kwargs):
    base = dict(
        side=side,
        port="fake",
        poll_hz=100.0,
        enable_wait_s=0.0,
        set_angle_wait_s=0.0,
        serial_timeout_s=0.02,
        reconnect_backoff_min_s=0.02,
        reconnect_backoff_max_s=0.05,
    )
    base.update(kwargs)
    return GripperLinkConfig(**base)


def _wait_until(predicate, timeout=2.0, interval=0.01):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(interval)
    return predicate()


def test_telemetry_updates_from_fake():
    fakes = []

    def factory(port, baudrate, timeout, gripper_id):
        fake = FakeSerial(
            port=port, baudrate=baudrate, timeout=timeout,
            gripper_id=gripper_id, initial_angle=100,
        )
        fakes.append(fake)
        return fake

    link = GripperSerialLink(_link_config(), serial_factory=factory)
    link.start()
    try:
        assert _wait_until(lambda: link.latest_state().valid)
        state = link.latest_state()
        assert abs(state.width - 1.0) < 1e-6
        assert state.angle == 100
    finally:
        link.stop()


def test_command_writes_set_angle():
    holder = {}

    def factory(port, baudrate, timeout, gripper_id):
        fake = FakeSerial(port=port, baudrate=baudrate, timeout=timeout, gripper_id=gripper_id)
        holder["fake"] = fake
        return fake

    link = GripperSerialLink(_link_config(), serial_factory=factory)
    link.start()
    try:
        assert _wait_until(lambda: "fake" in holder and link.latest_state().valid)
        link.submit_command(GripperCommand(side=GripperSide.LEFT, target_width=0.5))
        assert _wait_until(lambda: holder["fake"].set_angle_count >= 1)
        assert _wait_until(lambda: link.latest_state().angle == 50)
    finally:
        link.stop()


def test_estop_blocks_set_angle_and_sends_stop_disable():
    holder = {}

    def factory(port, baudrate, timeout, gripper_id):
        fake = FakeSerial(port=port, baudrate=baudrate, timeout=timeout, gripper_id=gripper_id)
        holder["fake"] = fake
        return fake

    link = GripperSerialLink(_link_config(), serial_factory=factory)
    link.start()
    try:
        assert _wait_until(lambda: "fake" in holder and link.latest_state().valid)
        link.trigger_estop()
        assert _wait_until(lambda: holder["fake"].stop_count >= 1)
        assert holder["fake"].disable_count >= 1
        before = holder["fake"].set_angle_count
        link.submit_command(GripperCommand(side=GripperSide.LEFT, target_width=0.9))
        time.sleep(0.2)
        assert holder["fake"].set_angle_count == before
    finally:
        link.stop()


def test_disconnect_marks_unhealthy():
    def factory(port, baudrate, timeout, gripper_id):
        raise OSError("cannot open")

    link = GripperSerialLink(_link_config(), serial_factory=factory)
    link.start()
    try:
        assert _wait_until(
            lambda: link.health_signal(time.monotonic()).connected is False
        )
        signal = link.health_signal(time.monotonic())
        assert signal.consecutive_errors >= 1
    finally:
        link.stop()


class _RclpyLikeLogger:
    """Mimics rclpy's per-call-site severity caching: calling a different
    severity from the same source line raises, exactly like rcutils_logger."""

    def __init__(self):
        self._site_severity = {}
        self.severities = []

    def _check(self, severity):
        frame = inspect.stack()[2]
        site = (frame.filename, frame.lineno)
        cached = self._site_severity.setdefault(site, severity)
        if cached != severity:
            raise ValueError("Logger severity cannot be changed between calls.")
        self.severities.append(severity)

    def info(self, message):
        self._check("info")

    def warn(self, message):
        self._check("warn")

    def error(self, message):
        self._check("error")


def test_reconnect_logging_survives_call_site_severity_caching():
    # Regression: open failure logs warn, then a successful open logs info.
    # With an rclpy-like logger both must come from distinct call sites or
    # the worker thread dies on ValueError right after connecting.
    logger = _RclpyLikeLogger()
    attempts = {"n": 0}

    def factory(port, baudrate, timeout, gripper_id):
        attempts["n"] += 1
        if attempts["n"] == 1:
            raise OSError("cannot open yet")
        return FakeSerial(port=port, baudrate=baudrate, timeout=timeout, gripper_id=gripper_id)

    link = GripperSerialLink(_link_config(), logger=logger, serial_factory=factory)
    link.start()
    try:
        assert _wait_until(lambda: link.latest_state().valid)
        assert "warn" in logger.severities
        assert "info" in logger.severities
        # The link must stay connected after logging the success message.
        assert link.health_signal(time.monotonic()).connected is True
    finally:
        link.stop()
