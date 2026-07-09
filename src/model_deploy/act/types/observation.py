"""Observation types for L2-02 ObservationSnapshot assembly.

Defines the cross-module RAM data contracts consumed by L2-03 batch adapter
and L2-06 ControlLoop: ObservationState, ObservationSnapshot, and
ObservationFreshnessResult.

All types are frozen dataclasses — created once, read-only thereafter,
safe for cross-thread sharing.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

import numpy as np

# ---------------------------------------------------------------------------
# Dimension constant
# ---------------------------------------------------------------------------

EXPECTED_STATE_DIM: int = 16
"""Expected dimension of the encoded_state vector in ObservationSnapshot."""


# ---------------------------------------------------------------------------
# ObservationState
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ObservationState:
    """Structured ACT observation state from TCP pose and gripper data.

    Encodes the 6 sub-fields that together form the 16D state vector:
        - left_tcp_position  (3,)   xyz
        - left_tcp_orientation (4,) xyzw quaternion
        - left_gripper_width   float [0, 1]
        - right_tcp_position  (3,)   xyz
        - right_tcp_orientation (4,) xyzw quaternion
        - right_gripper_width   float [0, 1]

    This is a pure data container — no ROS, no runtime state, no config.
    """

    left_tcp_position: np.ndarray
    left_tcp_orientation: np.ndarray
    left_gripper_width: float
    right_tcp_position: np.ndarray
    right_tcp_orientation: np.ndarray
    right_gripper_width: float


# ---------------------------------------------------------------------------
# ObservationSnapshot
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ObservationSnapshot:
    """Complete observation RAM object exposed to L2-03 and L2-06.

    Created by ObservationCollector, consumed by L2-03 batch adapter and
    L2-06 ControlLoop latest-observation reader.  Placed in ``types/`` so
    downstream L2s import only the data contract, not L2-02 service/runtime.

    Fields:
        images:        Mapping from camera name to RAM image array.
        state:         Structured state fields (6 sub-fields).
        encoded_state: 16D float32 state vector.
        captured_at_s:  Monotonic timestamp (seconds) when capture completed.

    Raises:
        ValueError: If ``encoded_state.shape != (16,)``.
    """

    images: Mapping[str, object]
    state: ObservationState
    encoded_state: np.ndarray
    captured_at_s: float

    def __post_init__(self) -> None:
        """Validate encoded_state dimension on construction."""
        if self.encoded_state.shape != (EXPECTED_STATE_DIM,):
            raise ValueError(
                f"encoded_state must have shape ({EXPECTED_STATE_DIM},), "
                f"got {self.encoded_state.shape}"
            )


# ---------------------------------------------------------------------------
# ObservationFreshnessResult
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ObservationFreshnessResult:
    """Diagnostic report for observation readiness and freshness.

    Constructed by ObservationCollector when checking whether all required
    fields are present and within ``max_age_s``.  Exposed as an observable
    diagnostic — no ROS dependency, no topic publishing.

    Fields:
        missing_fields:  Names of required fields not yet received.
        stale_fields:    Names of fields whose latest update exceeds max_age_s.
        field_ages_s:    Mapping from field name to age in seconds.
        ready:           True when **all** required fields are present and fresh.
    """

    missing_fields: Sequence[str]
    stale_fields: Sequence[str]
    field_ages_s: Mapping[str, float]
    ready: bool
