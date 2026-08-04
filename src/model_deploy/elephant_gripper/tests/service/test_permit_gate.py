"""Tests for the permit gate (default-deny semantics)."""

from elephant_gripper.service.permit_gate import evaluate_permit
from elephant_gripper.types.command_permit import CommandPermit


def test_missing_permit_denied():
    assert evaluate_permit(None, now_monotonic_s=10.0, timeout_s=0.5) is False


def test_denied_permit_denied():
    permit = CommandPermit(allowed=False, reason_code="no_operator", stamp_monotonic_s=10.0)
    assert evaluate_permit(permit, now_monotonic_s=10.1, timeout_s=0.5) is False


def test_fresh_allowed_permit_accepted():
    permit = CommandPermit(allowed=True, reason_code=None, stamp_monotonic_s=10.0)
    assert evaluate_permit(permit, now_monotonic_s=10.3, timeout_s=0.5) is True


def test_expired_allowed_permit_denied():
    permit = CommandPermit(allowed=True, reason_code=None, stamp_monotonic_s=10.0)
    assert evaluate_permit(permit, now_monotonic_s=11.0, timeout_s=0.5) is False


def test_boundary_exactly_at_timeout_accepted():
    permit = CommandPermit(allowed=True, reason_code=None, stamp_monotonic_s=10.0)
    assert evaluate_permit(permit, now_monotonic_s=10.5, timeout_s=0.5) is True


def test_future_stamp_treated_as_fresh():
    permit = CommandPermit(allowed=True, reason_code=None, stamp_monotonic_s=12.0)
    assert evaluate_permit(permit, now_monotonic_s=11.0, timeout_s=0.5) is True
