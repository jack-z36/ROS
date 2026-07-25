"""Local (RAM) CommandPermit type.

Kept separate from the ROS ``act_interfaces/CommandPermit`` message so the
service layer can reason about permits without importing ROS and without
cross-package importing ``act/`` private implementations. The UI layer
converts the ROS message into this type at the boundary.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class CommandPermit:
    """Human-authorization permit as understood inside the node.

    ``stamp_monotonic_s`` is the ``time.monotonic`` timestamp captured when the
    permit was received, used by the permit gate for freshness / expiry checks.
    Invariant: ``allowed=True`` implies ``reason_code`` is None/empty;
    ``allowed=False`` implies a non-empty stable ``reason_code``.
    """

    allowed: bool
    reason_code: Optional[str]
    stamp_monotonic_s: float

    @classmethod
    def denied(cls, reason_code: str, stamp_monotonic_s: float = 0.0) -> "CommandPermit":
        """A default-deny permit used before any permit message arrives."""

        return cls(allowed=False, reason_code=reason_code, stamp_monotonic_s=stamp_monotonic_s)
