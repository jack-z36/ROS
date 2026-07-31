"""Tests for real-run movement/hold response gating."""

from __future__ import annotations

import numpy as np

from model_deploy.act.runtime.action_response_verifier import (
    ActionResponseVerifier,
    ResponseState,
)
from model_deploy.act.types.action_spec import ActionSpec
from model_deploy.act.types.observation import ObservationSnapshot, ObservationState


def _action(x: float = 0.0) -> ActionSpec:
    q = np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float32)
    return ActionSpec(
        left_tcp_action=np.array([x, 0.0, 0.0, *q], dtype=np.float32),
        right_tcp_action=np.array([0.0, 0.0, 0.0, *q], dtype=np.float32),
        left_gripper=0.5,
        right_gripper=0.5,
    )


def _observation(x: float = 0.0) -> ObservationSnapshot:
    q = np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float32)
    state = ObservationState(
        left_tcp_position=np.array([x, 0.0, 0.0], dtype=np.float32),
        left_tcp_orientation=q,
        left_gripper_width=0.5,
        right_tcp_position=np.zeros(3, dtype=np.float32),
        right_tcp_orientation=q,
        right_gripper_width=0.5,
    )
    return ObservationSnapshot(
        images={}, state=state, encoded_state=np.zeros(16, dtype=np.float32), captured_at_s=0.0
    )


def test_move_requires_progress() -> None:
    verifier = ActionResponseVerifier(response_timeout_s=0.5)
    verifier.on_published("act-1", _action(0.01), _observation(0.0), 0.0)
    assert verifier.observe(_observation(0.005), 0.1).state is ResponseState.COMPLETE


def test_stalled_move_times_out() -> None:
    verifier = ActionResponseVerifier(response_timeout_s=0.5)
    verifier.on_published("act-1", _action(0.01), _observation(0.0), 0.0)
    result = verifier.observe(_observation(0.0), 0.6)
    assert result.state is ResponseState.FAULT
    assert result.reason_code == "RESPONSE_TIMEOUT"
    assert result.detail == "left_tcp_translation"


def test_motion_check_disabled_accepts_fresh_feedback_without_progress() -> None:
    verifier = ActionResponseVerifier(
        motion_check_enabled=False, response_timeout_s=0.5
    )
    verifier.on_published("act-1", _action(0.01), _observation(0.0), 0.0)
    result = verifier.observe(_observation(0.0), 0.1)
    assert result.state is ResponseState.COMPLETE
    assert result.reason_code == "RESPONSE_FRESH"


def test_motion_check_disabled_still_faults_when_feedback_is_missing() -> None:
    verifier = ActionResponseVerifier(
        motion_check_enabled=False, response_timeout_s=0.5
    )
    verifier.on_published("act-1", _action(0.01), _observation(0.0), 0.0)
    result = verifier.observe(None, 0.6)
    assert result.state is ResponseState.FAULT
    assert result.reason_code == "RESPONSE_FEEDBACK_STALE"


def test_hold_drift_faults() -> None:
    verifier = ActionResponseVerifier(response_timeout_s=0.5, hold_window_s=0.2)
    verifier.on_published("act-1", _action(0.0), _observation(0.0), 0.0)
    result = verifier.observe(_observation(0.002), 0.1)
    assert result.state is ResponseState.FAULT
    assert result.reason_code == "HOLD_DRIFT"


def test_hold_stability_completes() -> None:
    verifier = ActionResponseVerifier(response_timeout_s=0.5, hold_window_s=0.2)
    verifier.on_published("act-1", _action(0.0), _observation(0.0), 0.0)
    result = verifier.observe(_observation(0.0), 0.21)
    assert result.state is ResponseState.COMPLETE
    assert result.reason_code == "HOLD_STABLE"
