"""Physical response verification for real ACT command output.

The command publisher can only prove that ROS accepted a write.  This module
compares the next fresh observation with the command baseline so real-run can
distinguish a moving robot from a robot that merely receives messages.

The verifier deliberately allows one outstanding command at a time.  That
gives each command a bounded response window and prevents a high-rate policy
stream from hiding a stalled actuator behind newer targets.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Optional

import numpy as np

from model_deploy.act.types.action_spec import ActionSpec
from model_deploy.act.types.observation import ObservationSnapshot


class ResponseState(str, Enum):
    IDLE = "IDLE"
    WAITING = "WAITING"
    COMPLETE = "COMPLETE"
    FAULT = "FAULT"


@dataclass(frozen=True)
class ResponseCheck:
    state: ResponseState
    reason_code: Optional[str] = None
    detail: Optional[str] = None


@dataclass(frozen=True)
class _PendingCommand:
    action_id: str
    target: ActionSpec
    baseline: ObservationSnapshot
    issued_at_s: float


_COMPONENT_NAMES = (
    "left_tcp_translation",
    "left_tcp_rotation",
    "left_gripper",
    "right_tcp_translation",
    "right_tcp_rotation",
    "right_gripper",
)


def _rotation_error(q0: np.ndarray, q1: np.ndarray) -> float:
    q0 = np.asarray(q0, dtype=np.float64).ravel()
    q1 = np.asarray(q1, dtype=np.float64).ravel()
    n0 = float(np.linalg.norm(q0))
    n1 = float(np.linalg.norm(q1))
    if n0 <= 0.0 or n1 <= 0.0:
        return math.inf
    dot = abs(float(np.dot(q0 / n0, q1 / n1)))
    return 2.0 * math.acos(min(1.0, max(0.0, dot)))


def _errors(action: ActionSpec, observation: ObservationSnapshot) -> tuple[float, ...]:
    state = observation.state
    return (
        float(np.linalg.norm(np.asarray(action.left_tcp_action[:3]) - state.left_tcp_position)),
        _rotation_error(action.left_tcp_action[3:7], state.left_tcp_orientation),
        abs(float(action.left_gripper) - float(state.left_gripper_width)),
        float(np.linalg.norm(np.asarray(action.right_tcp_action[:3]) - state.right_tcp_position)),
        _rotation_error(action.right_tcp_action[3:7], state.right_tcp_orientation),
        abs(float(action.right_gripper) - float(state.right_gripper_width)),
    )


class ActionResponseVerifier:
    """Verify movement progress or hold stability for one real command."""

    def __init__(
        self,
        *,
        motion_check_enabled: bool = True,
        response_timeout_s: float = 0.5,
        hold_window_s: float = 0.2,
        epsilon_move_translation_m: float = 1e-3,
        epsilon_move_rotation_rad: float = 1e-2,
        epsilon_move_gripper: float = 1e-2,
        epsilon_hold_translation_m: float = 1e-3,
        epsilon_hold_rotation_rad: float = 1e-2,
        epsilon_hold_gripper: float = 1e-2,
    ) -> None:
        if not isinstance(motion_check_enabled, bool):
            raise TypeError("motion_check_enabled must be bool")
        values = (
            response_timeout_s,
            hold_window_s,
            epsilon_move_translation_m,
            epsilon_move_rotation_rad,
            epsilon_move_gripper,
            epsilon_hold_translation_m,
            epsilon_hold_rotation_rad,
            epsilon_hold_gripper,
        )
        if any(not math.isfinite(float(v)) or float(v) < 0.0 for v in values):
            raise ValueError("response verifier parameters must be finite and non-negative")
        if response_timeout_s <= 0.0 or hold_window_s <= 0.0:
            raise ValueError("response_timeout_s and hold_window_s must be positive")
        self._motion_check_enabled = motion_check_enabled
        self._response_timeout_s = float(response_timeout_s)
        self._hold_window_s = float(hold_window_s)
        self._move = (
            float(epsilon_move_translation_m),
            float(epsilon_move_rotation_rad),
            float(epsilon_move_gripper),
        )
        self._hold = (
            float(epsilon_hold_translation_m),
            float(epsilon_hold_rotation_rad),
            float(epsilon_hold_gripper),
        )
        self._pending: Optional[_PendingCommand] = None
        self._baseline_errors: tuple[float, ...] = ()
        self._state = ResponseState.IDLE
        self._reason_code: Optional[str] = None
        self._detail: Optional[str] = None

    @property
    def state(self) -> ResponseState:
        return self._state

    @property
    def reason_code(self) -> Optional[str]:
        return self._reason_code

    @property
    def detail(self) -> Optional[str]:
        return self._detail

    @property
    def pending(self) -> bool:
        return self._pending is not None

    def on_published(
        self,
        action_id: str,
        target: ActionSpec,
        baseline: ObservationSnapshot,
        issued_at_s: float,
    ) -> None:
        if self._pending is not None:
            raise RuntimeError("cannot publish a new action before the previous response is resolved")
        if not action_id:
            raise ValueError("action_id must be non-empty")
        if not math.isfinite(float(issued_at_s)):
            raise ValueError("issued_at_s must be finite")
        self._pending = _PendingCommand(action_id, target, baseline, float(issued_at_s))
        self._baseline_errors = _errors(target, baseline)
        self._state = ResponseState.WAITING
        self._reason_code = None
        self._detail = None

    def observe(self, observation: Optional[ObservationSnapshot], now_s: float) -> ResponseCheck:
        if not math.isfinite(float(now_s)):
            self._state = ResponseState.FAULT
            self._reason_code = "RESPONSE_CLOCK_INVALID"
            self._detail = None
            return ResponseCheck(self._state, self._reason_code, self._detail)
        if self._pending is None:
            if self._state is ResponseState.FAULT:
                return ResponseCheck(self._state, self._reason_code, self._detail)
            self._state = ResponseState.IDLE
            self._reason_code = None
            self._detail = None
            return ResponseCheck(self._state)
        if observation is None:
            if float(now_s) - self._pending.issued_at_s > self._response_timeout_s:
                return self._fault("RESPONSE_FEEDBACK_STALE", "observation")
            return ResponseCheck(ResponseState.WAITING, "RESPONSE_FEEDBACK_WAITING")

        elapsed = float(now_s) - self._pending.issued_at_s
        # Some learned policies intentionally make non-monotonic trajectory
        # samples.  In this deployment mode fresh feedback is required, but
        # movement towards the previous sample is not an E-stop contract.
        if not self._motion_check_enabled:
            self._pending = None
            self._state = ResponseState.COMPLETE
            self._reason_code = "RESPONSE_FRESH"
            return ResponseCheck(self._state, self._reason_code)
        current = _errors(self._pending.target, observation)
        # A target is a move if any corresponding component is outside its
        # movement deadband.  Every moving component must show progress.
        moving = tuple(
            baseline >= threshold
            for baseline, threshold in zip(
                self._baseline_errors,
                self._move * 2,
            )
        )
        progress = tuple(
            (not is_move) or (current_error < baseline_error)
            for is_move, current_error, baseline_error in zip(
                moving, current, self._baseline_errors
            )
        )
        if any(moving):
            if all(progress):
                self._pending = None
                self._state = ResponseState.COMPLETE
                self._reason_code = "RESPONSE_PROGRESS"
                return ResponseCheck(self._state, self._reason_code)
            if elapsed > self._response_timeout_s:
                stalled = ",".join(
                    name
                    for name, is_move, made_progress in zip(
                        _COMPONENT_NAMES, moving, progress
                    )
                    if is_move and not made_progress
                )
                return self._fault("RESPONSE_TIMEOUT", stalled or "unknown")
            return ResponseCheck(ResponseState.WAITING, "RESPONSE_WAITING")

        # For a hold command, inspect the entire hold window for drift.
        # Compare the measured state with the command baseline for the hold
        # contract.  This is independent of the target error above.
        hold_drift = _state_delta(self._pending.baseline, observation)
        hold_components = tuple(
            baseline < threshold for baseline, threshold in zip(self._baseline_errors, self._move * 2)
        )
        if any(hold_components):
            hold_limits = self._hold * 2
            if any(delta > limit for delta, limit in zip(hold_drift, hold_limits)):
                return self._fault("HOLD_DRIFT")
            if elapsed >= self._hold_window_s:
                self._pending = None
                self._state = ResponseState.COMPLETE
                self._reason_code = "HOLD_STABLE"
                return ResponseCheck(self._state, self._reason_code)

        return ResponseCheck(ResponseState.WAITING, "RESPONSE_WAITING")

    def _fault(self, reason: str, detail: Optional[str] = None) -> ResponseCheck:
        self._pending = None
        self._state = ResponseState.FAULT
        self._reason_code = reason
        self._detail = detail
        return ResponseCheck(self._state, reason, detail)


def _state_delta(before: ObservationSnapshot, after: ObservationSnapshot) -> tuple[float, ...]:
    a = before.state
    b = after.state
    return (
        float(np.linalg.norm(np.asarray(b.left_tcp_position) - a.left_tcp_position)),
        _rotation_error(a.left_tcp_orientation, b.left_tcp_orientation),
        abs(float(b.left_gripper_width) - float(a.left_gripper_width)),
        float(np.linalg.norm(np.asarray(b.right_tcp_position) - a.right_tcp_position)),
        _rotation_error(a.right_tcp_orientation, b.right_tcp_orientation),
        abs(float(b.right_gripper_width) - float(a.right_gripper_width)),
    )


__all__ = ["ActionResponseVerifier", "ResponseCheck", "ResponseState"]
