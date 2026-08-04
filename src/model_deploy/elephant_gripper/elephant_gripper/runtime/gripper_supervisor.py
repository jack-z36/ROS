"""Supervisor: orchestrates the two gripper links and permit gating.

Holds the current permit and applies it when routing commands. All serial I/O
lives in the link worker threads; this class only makes O(1) decisions and
snapshots. No ROS imports here.
"""

from __future__ import annotations

import threading
import time
from typing import Any, Optional

from ..config.schema import NodeConfig
from ..service.health_aggregator import aggregate_node_health, evaluate_device_health
from ..service.permit_gate import evaluate_permit
from ..types.command_permit import CommandPermit
from ..types.gripper_types import (
    GripperCommand,
    GripperSide,
    GripperStateSample,
    NodeHealth,
)
from .serial_link import GripperSerialLink, SerialFactory

# Health thresholds shared by both links.
_ERROR_DEGRADED_THRESHOLD = 3
_ERROR_FAULT_THRESHOLD = 10


class GripperSupervisor:
    """Coordinate left/right links, permit state and estop."""

    def __init__(
        self,
        config: NodeConfig,
        logger: Any = None,
        serial_factory: Optional[SerialFactory] = None,
    ) -> None:
        self._config = config
        self._logger = logger
        self._permit_lock = threading.Lock()
        self._permit: Optional[CommandPermit] = CommandPermit.denied("no_permit_yet")
        self._estop_latched = config.estop_on_startup

        self._links = {
            GripperSide.LEFT: GripperSerialLink(
                config.left,
                logger=logger,
                serial_factory=serial_factory,
                error_degraded_threshold=_ERROR_DEGRADED_THRESHOLD,
                error_fault_threshold=_ERROR_FAULT_THRESHOLD,
            ),
            GripperSide.RIGHT: GripperSerialLink(
                config.right,
                logger=logger,
                serial_factory=serial_factory,
                error_degraded_threshold=_ERROR_DEGRADED_THRESHOLD,
                error_fault_threshold=_ERROR_FAULT_THRESHOLD,
            ),
        }

    # -- lifecycle ------------------------------------------------------------
    def start(self) -> None:
        for link in self._links.values():
            link.start()
        if self._estop_latched:
            self.estop_all()

    def shutdown(self, join_timeout: float = 2.0) -> None:
        for link in self._links.values():
            link.stop(join_timeout=join_timeout)

    # -- permit ---------------------------------------------------------------
    def apply_permit(self, permit: CommandPermit) -> None:
        with self._permit_lock:
            self._permit = permit

    def _current_permit(self) -> Optional[CommandPermit]:
        with self._permit_lock:
            return self._permit

    def permit_allows_now(self, now_monotonic_s: Optional[float] = None) -> bool:
        now = time.monotonic() if now_monotonic_s is None else now_monotonic_s
        return evaluate_permit(self._current_permit(), now, self._config.permit_timeout_s)

    # -- commands -------------------------------------------------------------
    def route_command(self, command: GripperCommand) -> bool:
        """Forward a command to its link only if permit is valid and no estop.

        Returns True if the command was accepted (queued to the link), False if
        it was dropped (denied/expired permit or estop). Telemetry continues
        regardless; a dropped command simply holds the last position.
        """

        if self._estop_latched:
            return False
        if not self.permit_allows_now():
            return False
        link = self._links.get(command.side)
        if link is None:
            return False
        link.submit_command(command)
        return True

    # -- telemetry ------------------------------------------------------------
    def latest_state(self, side: GripperSide) -> GripperStateSample:
        return self._links[side].latest_state()

    def aggregate_health(self, now_monotonic_s: Optional[float] = None) -> NodeHealth:
        now = time.monotonic() if now_monotonic_s is None else now_monotonic_s
        rx_stale_s = max(0.5, 5.0 / max(self._config.left.poll_hz, 1.0))
        left = evaluate_device_health(
            self._links[GripperSide.LEFT].health_signal(now),
            _ERROR_DEGRADED_THRESHOLD,
            _ERROR_FAULT_THRESHOLD,
            rx_stale_s,
        )
        right = evaluate_device_health(
            self._links[GripperSide.RIGHT].health_signal(now),
            _ERROR_DEGRADED_THRESHOLD,
            _ERROR_FAULT_THRESHOLD,
            rx_stale_s,
        )
        return aggregate_node_health(
            left, right, self._config.hardware_id, self._estop_latched
        )

    # -- estop ----------------------------------------------------------------
    def estop_all(self) -> None:
        self._estop_latched = True
        for link in self._links.values():
            link.trigger_estop()

    def clear_estop(self) -> None:
        self._estop_latched = False
        for link in self._links.values():
            link.clear_estop()

    @property
    def estop_latched(self) -> bool:
        return self._estop_latched
