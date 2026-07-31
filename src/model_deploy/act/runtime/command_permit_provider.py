"""Fail-closed real-command permit state machine.

This module owns only RAM state and decisions.  ROS subscriptions, heartbeat
publishing, topology inspection and emergency-stop service calls live in the
UI adapter.
"""

from __future__ import annotations

import math
import threading
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Optional

from model_deploy.act.types.action_publish import CommandPermit


class PermitState(str, Enum):
    DISABLED = "DISABLED"
    WAITING_HEALTH = "WAITING_HEALTH"
    ALLOWED = "ALLOWED"
    DENIED = "DENIED"


@dataclass(frozen=True)
class HardwareGateSample:
    healthy: bool
    reason_code: str
    received_at_s: float

    def __post_init__(self) -> None:
        if not isinstance(self.healthy, bool):
            raise TypeError("HardwareGateSample.healthy must be bool")
        if not self.reason_code:
            raise ValueError("HardwareGateSample.reason_code must be non-empty")
        if not math.isfinite(self.received_at_s) or self.received_at_s < 0.0:
            raise ValueError("HardwareGateSample.received_at_s must be finite and >= 0")


class CommandPermitProvider:
    """Combine mode, operator confirmation, topology, health and runtime state."""

    def __init__(
        self,
        *,
        mode: str,
        command_output_enabled: bool,
        monotonic_clock: Callable[[], float],
        health_timeout_s: float = 0.5,
        warmup_allowed_heartbeats: int = 2,
    ) -> None:
        if mode not in {"dry-run", "real-run"}:
            raise ValueError("mode must be dry-run or real-run")
        if not isinstance(command_output_enabled, bool):
            raise TypeError("command_output_enabled must be bool")
        if health_timeout_s <= 0.0:
            raise ValueError("health_timeout_s must be positive")
        if warmup_allowed_heartbeats < 1:
            raise ValueError("warmup_allowed_heartbeats must be >= 1")

        self._mode = mode
        self._command_output_enabled = command_output_enabled
        self._clock = monotonic_clock
        self._health_timeout_s = float(health_timeout_s)
        self._warmup_required = int(warmup_allowed_heartbeats)
        self._lock = threading.RLock()

        self._rm65: Optional[HardwareGateSample] = None
        self._gripper: Optional[HardwareGateSample] = None
        self._topology_ready = False
        self._topology_reason = "TOPOLOGY_NOT_READY"
        self._runtime_ready = False
        self._runtime_reason = "RUNTIME_NOT_READY"
        self._latched_denial: Optional[str] = None
        self._allowed_heartbeats = 0
        self._has_been_allowed = False
        self._last_state = PermitState.DISABLED
        self._last_reason = "COMMAND_OUTPUT_DISABLED"

    def update_rm65_health(self, healthy: bool, reason_code: str) -> None:
        with self._lock:
            self._rm65 = HardwareGateSample(
                healthy=healthy,
                reason_code=reason_code,
                received_at_s=self._now(),
            )

    def update_gripper_health(self, healthy: bool, reason_code: str) -> None:
        with self._lock:
            self._gripper = HardwareGateSample(
                healthy=healthy,
                reason_code=reason_code,
                received_at_s=self._now(),
            )

    def update_topology(self, ready: bool, reason_code: str) -> None:
        with self._lock:
            self._topology_ready = bool(ready)
            self._topology_reason = reason_code or "TOPOLOGY_NOT_READY"

    def update_runtime_ready(self, ready: bool, reason_code: str) -> None:
        with self._lock:
            self._runtime_ready = bool(ready)
            self._runtime_reason = reason_code or "RUNTIME_NOT_READY"

    def latch_denial(self, reason_code: str) -> None:
        with self._lock:
            self._latched_denial = reason_code or "RUNTIME_FAULT"
            self._allowed_heartbeats = 0

    def heartbeat_permit(self) -> CommandPermit:
        """Return the permit to publish to drivers on this heartbeat."""
        with self._lock:
            allowed, reason, state = self._evaluate_raw()
            self._last_state = state
            self._last_reason = reason
            return CommandPermit(allowed, None if allowed else reason)

    def record_heartbeat_published(self, permit: CommandPermit) -> None:
        with self._lock:
            if permit.allowed:
                self._allowed_heartbeats += 1
            else:
                self._allowed_heartbeats = 0

    def command_permit(self) -> CommandPermit:
        """Return the per-control-tick permit after heartbeat warmup."""
        with self._lock:
            allowed, reason, state = self._evaluate_raw()
            if not allowed:
                self._last_state = state
                self._last_reason = reason
                self._allowed_heartbeats = 0
                return CommandPermit(False, reason)
            if self._allowed_heartbeats < self._warmup_required:
                self._last_state = PermitState.WAITING_HEALTH
                self._last_reason = "PERMIT_HEARTBEAT_WARMUP"
                return CommandPermit(False, "PERMIT_HEARTBEAT_WARMUP")
            self._last_state = PermitState.ALLOWED
            self._last_reason = "ALLOWED"
            self._has_been_allowed = True
            return CommandPermit(True)

    def dependency_status(self) -> tuple[bool, str]:
        """Report whether real-run ROS topology and hardware health are ready.

        This deliberately excludes runtime observation readiness and heartbeat
        warmup.  The ROS adapter uses it during node construction to fail fast
        when the hardware-side contract cannot be established.
        """
        with self._lock:
            if self._mode != "real-run" or not self._command_output_enabled:
                return True, "COMMAND_OUTPUT_DISABLED"
            if self._latched_denial is not None:
                return False, self._latched_denial
            if not self._topology_ready:
                return False, self._topology_reason
            now = self._now()
            for label, sample in (
                ("RM65", self._rm65),
                ("GRIPPER", self._gripper),
            ):
                if sample is None:
                    return False, f"{label}_HEALTH_MISSING"
                if now - sample.received_at_s > self._health_timeout_s:
                    return False, f"{label}_HEALTH_STALE"
                if not sample.healthy:
                    return False, sample.reason_code
            return True, "HARDWARE_DEPENDENCIES_READY"

    @property
    def state(self) -> PermitState:
        with self._lock:
            return self._last_state

    @property
    def reason_code(self) -> str:
        with self._lock:
            return self._last_reason

    @property
    def allowed_heartbeat_count(self) -> int:
        with self._lock:
            return self._allowed_heartbeats

    @property
    def has_been_allowed(self) -> bool:
        with self._lock:
            return self._has_been_allowed

    def _evaluate_raw(self) -> tuple[bool, str, PermitState]:
        if self._mode != "real-run" or not self._command_output_enabled:
            return False, "COMMAND_OUTPUT_DISABLED", PermitState.DISABLED
        if self._latched_denial is not None:
            return False, self._latched_denial, PermitState.DENIED
        if not self._topology_ready:
            return False, self._topology_reason, PermitState.WAITING_HEALTH
        if not self._runtime_ready:
            return False, self._runtime_reason, PermitState.WAITING_HEALTH

        now = self._now()
        for label, sample in (("RM65", self._rm65), ("GRIPPER", self._gripper)):
            if sample is None:
                return False, f"{label}_HEALTH_MISSING", PermitState.WAITING_HEALTH
            if now - sample.received_at_s > self._health_timeout_s:
                return False, f"{label}_HEALTH_STALE", PermitState.WAITING_HEALTH
            if not sample.healthy:
                return False, sample.reason_code, PermitState.DENIED
        return True, "ALLOWED", PermitState.ALLOWED

    def _now(self) -> float:
        value = self._clock()
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError("permit monotonic clock must return a number")
        value = float(value)
        if not math.isfinite(value) or value < 0.0:
            raise ValueError("permit monotonic clock must be finite and >= 0")
        return value


__all__ = [
    "CommandPermitProvider",
    "HardwareGateSample",
    "PermitState",
]
