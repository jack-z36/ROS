"""Tests for the supervisor: permit gating, routing and estop."""

import time

from elephant_gripper.config.schema import GripperLinkConfig, NodeConfig
from elephant_gripper.runtime.fake_serial import make_fake_serial_factory
from elephant_gripper.runtime.gripper_supervisor import GripperSupervisor
from elephant_gripper.types.command_permit import CommandPermit
from elephant_gripper.types.gripper_types import (
    GripperCommand,
    GripperSide,
    HealthLevel,
)


def _node_config(**kwargs):
    common = dict(
        poll_hz=100.0,
        enable_wait_s=0.0,
        set_angle_wait_s=0.0,
        serial_timeout_s=0.02,
        reconnect_backoff_min_s=0.02,
        reconnect_backoff_max_s=0.05,
    )
    base = dict(
        left=GripperLinkConfig(side=GripperSide.LEFT, port="fakeL", **common),
        right=GripperLinkConfig(side=GripperSide.RIGHT, port="fakeR", **common),
        permit_timeout_s=0.5,
    )
    base.update(kwargs)
    return NodeConfig(**base)


def _wait_until(predicate, timeout=2.0, interval=0.01):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(interval)
    return predicate()


def _fresh_permit(allowed=True):
    return CommandPermit(
        allowed=allowed,
        reason_code=None if allowed else "denied",
        stamp_monotonic_s=time.monotonic(),
    )


def test_command_dropped_without_permit():
    sup = GripperSupervisor(_node_config(), serial_factory=make_fake_serial_factory())
    sup.start()
    try:
        accepted = sup.route_command(
            GripperCommand(side=GripperSide.LEFT, target_width=0.5)
        )
        assert accepted is False
    finally:
        sup.shutdown()


def test_command_accepted_with_fresh_permit():
    sup = GripperSupervisor(_node_config(), serial_factory=make_fake_serial_factory())
    sup.start()
    try:
        sup.apply_permit(_fresh_permit(True))
        accepted = sup.route_command(
            GripperCommand(side=GripperSide.LEFT, target_width=0.5)
        )
        assert accepted is True
        assert _wait_until(
            lambda: sup.latest_state(GripperSide.LEFT).angle == 50
        )
    finally:
        sup.shutdown()


def test_expired_permit_drops_command():
    sup = GripperSupervisor(_node_config(permit_timeout_s=0.1), serial_factory=make_fake_serial_factory())
    sup.start()
    try:
        stale = CommandPermit(
            allowed=True, reason_code=None, stamp_monotonic_s=time.monotonic() - 1.0
        )
        sup.apply_permit(stale)
        accepted = sup.route_command(
            GripperCommand(side=GripperSide.LEFT, target_width=0.5)
        )
        assert accepted is False
    finally:
        sup.shutdown()


def test_telemetry_continues_without_permit():
    sup = GripperSupervisor(_node_config(), serial_factory=make_fake_serial_factory())
    sup.start()
    try:
        assert _wait_until(lambda: sup.latest_state(GripperSide.LEFT).valid)
        assert _wait_until(lambda: sup.latest_state(GripperSide.RIGHT).valid)
    finally:
        sup.shutdown()


def test_estop_latches_and_blocks_commands():
    sup = GripperSupervisor(_node_config(), serial_factory=make_fake_serial_factory())
    sup.start()
    try:
        sup.apply_permit(_fresh_permit(True))
        sup.estop_all()
        assert sup.estop_latched is True
        accepted = sup.route_command(
            GripperCommand(side=GripperSide.RIGHT, target_width=0.5)
        )
        assert accepted is False
        health = sup.aggregate_health()
        assert health.estop_active is True
    finally:
        sup.shutdown()


def test_clear_estop_reenables_commands():
    sup = GripperSupervisor(_node_config(), serial_factory=make_fake_serial_factory())
    sup.start()
    try:
        sup.apply_permit(_fresh_permit(True))
        sup.estop_all()
        sup.clear_estop()
        assert sup.estop_latched is False
        assert _wait_until(
            lambda: sup.route_command(
                GripperCommand(side=GripperSide.LEFT, target_width=0.3)
            )
        )
    finally:
        sup.shutdown()


def test_health_ok_when_connected():
    sup = GripperSupervisor(_node_config(), serial_factory=make_fake_serial_factory())
    sup.start()
    try:
        assert _wait_until(lambda: sup.latest_state(GripperSide.LEFT).valid)
        health = sup.aggregate_health()
        assert health.status is HealthLevel.OK
        assert health.left.connected is True
        assert health.right.connected is True
    finally:
        sup.shutdown()
