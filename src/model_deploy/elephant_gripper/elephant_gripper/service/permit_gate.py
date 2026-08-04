"""Permit gating: the single source of truth for "may we execute a command".

Pure function, no ROS. Default-deny: a missing, denied or expired permit means
new commands must NOT run.
"""

from __future__ import annotations

from typing import Optional

from ..types.command_permit import CommandPermit


def evaluate_permit(
    permit: Optional[CommandPermit],
    now_monotonic_s: float,
    timeout_s: float,
) -> bool:
    """Return True only when a fresh, allowed permit is present.

    Rejects when the permit is missing, ``allowed`` is False, or the permit is
    older than ``timeout_s`` (stale / expired).
    """

    if permit is None:
        return False
    if not permit.allowed:
        return False
    age = now_monotonic_s - permit.stamp_monotonic_s
    if age < 0:
        # Clock went backwards or future stamp; treat as fresh but bounded.
        age = 0.0
    return age <= timeout_s
