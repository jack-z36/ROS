"""Health aggregation: map per-link telemetry into device/node health.

Pure functions, no ROS. Each link reports connection state, consecutive error
count and time since last successful receive; those are mapped to a
:class:`HealthLevel`, and the node status is the worse of the two.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ..types.gripper_types import (
    DeviceHealth,
    GripperSide,
    HealthLevel,
    NodeHealth,
)


@dataclass(frozen=True)
class LinkHealthInput:
    """Raw per-link signals sampled by the runtime layer."""

    side: GripperSide
    connected: bool
    consecutive_errors: int
    seconds_since_rx: Optional[float]
    last_detail: str = ""


def evaluate_device_health(
    signal: LinkHealthInput,
    error_degraded_threshold: int,
    error_fault_threshold: int,
    rx_stale_s: float,
) -> DeviceHealth:
    """Map one link's signals to a :class:`DeviceHealth`."""

    if not signal.connected:
        return DeviceHealth(
            side=signal.side,
            connected=False,
            status=HealthLevel.FAULT,
            detail=signal.last_detail or "disconnected",
        )

    status = HealthLevel.OK
    detail = ""

    if signal.consecutive_errors >= error_fault_threshold:
        status = HealthLevel.FAULT
        detail = f"{signal.consecutive_errors} consecutive errors"
    elif signal.consecutive_errors >= error_degraded_threshold:
        status = HealthLevel.DEGRADED
        detail = f"{signal.consecutive_errors} consecutive errors"

    if signal.seconds_since_rx is not None and signal.seconds_since_rx > rx_stale_s:
        stale_detail = f"no fresh telemetry for {signal.seconds_since_rx:.2f}s"
        if status < HealthLevel.DEGRADED:
            status = HealthLevel.DEGRADED
        detail = detail or stale_detail

    if not detail and signal.last_detail:
        detail = signal.last_detail

    return DeviceHealth(
        side=signal.side,
        connected=True,
        status=status,
        detail=detail,
    )


def aggregate_node_health(
    left: DeviceHealth,
    right: DeviceHealth,
    hardware_id: str,
    estop_active: bool,
) -> NodeHealth:
    """Combine two device healths into a node health (worse of the two)."""

    status = HealthLevel(max(int(left.status), int(right.status)))
    details = []
    if left.detail:
        details.append(f"left: {left.detail}")
    if right.detail:
        details.append(f"right: {right.detail}")
    if estop_active:
        details.append("estop active")
    return NodeHealth(
        hardware_id=hardware_id,
        status=status,
        left=left,
        right=right,
        estop_active=estop_active,
        detail="; ".join(details),
    )
