"""Tests for health aggregation."""

from elephant_gripper.service.health_aggregator import (
    LinkHealthInput,
    aggregate_node_health,
    evaluate_device_health,
)
from elephant_gripper.types.gripper_types import GripperSide, HealthLevel

_DEGRADED = 3
_FAULT = 10
_STALE_S = 0.5


def _signal(**kwargs):
    base = dict(
        side=GripperSide.LEFT,
        connected=True,
        consecutive_errors=0,
        seconds_since_rx=0.0,
        last_detail="",
    )
    base.update(kwargs)
    return LinkHealthInput(**base)


def test_disconnected_is_fault():
    health = evaluate_device_health(
        _signal(connected=False), _DEGRADED, _FAULT, _STALE_S
    )
    assert health.status is HealthLevel.FAULT
    assert health.connected is False


def test_healthy_is_ok():
    health = evaluate_device_health(_signal(), _DEGRADED, _FAULT, _STALE_S)
    assert health.status is HealthLevel.OK


def test_degraded_error_threshold():
    health = evaluate_device_health(
        _signal(consecutive_errors=3), _DEGRADED, _FAULT, _STALE_S
    )
    assert health.status is HealthLevel.DEGRADED


def test_fault_error_threshold():
    health = evaluate_device_health(
        _signal(consecutive_errors=10), _DEGRADED, _FAULT, _STALE_S
    )
    assert health.status is HealthLevel.FAULT


def test_stale_rx_is_degraded():
    health = evaluate_device_health(
        _signal(seconds_since_rx=2.0), _DEGRADED, _FAULT, _STALE_S
    )
    assert health.status is HealthLevel.DEGRADED


def test_node_status_is_worse_of_two():
    left = evaluate_device_health(_signal(), _DEGRADED, _FAULT, _STALE_S)
    right = evaluate_device_health(
        _signal(side=GripperSide.RIGHT, connected=False), _DEGRADED, _FAULT, _STALE_S
    )
    node = aggregate_node_health(left, right, "elephant_gripper", estop_active=False)
    assert node.status is HealthLevel.FAULT
    assert node.hardware_id == "elephant_gripper"
    assert node.estop_active is False


def test_node_detail_reports_estop():
    left = evaluate_device_health(_signal(), _DEGRADED, _FAULT, _STALE_S)
    right = evaluate_device_health(
        _signal(side=GripperSide.RIGHT), _DEGRADED, _FAULT, _STALE_S
    )
    node = aggregate_node_health(left, right, "elephant_gripper", estop_active=True)
    assert node.estop_active is True
    assert "estop" in node.detail
