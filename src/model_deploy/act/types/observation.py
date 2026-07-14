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


def _owned_array(value: object) -> np.ndarray:
    """Return an owned, contiguous ``np.ndarray`` copy of *value*.

    Raises:
        TypeError: If *value* is not array-like.
    """
    arr = np.asarray(value)
    if arr.dtype == object:
        raise TypeError(
            f"observation array must be numeric, got object dtype from {type(value)}"
        )
    return np.array(arr, copy=True, order="C")

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

    images: Mapping[str, np.ndarray]
    state: ObservationState
    encoded_state: np.ndarray
    captured_at_s: float

    def __post_init__(self) -> None:
        """Validate contract invariants and deep-copy all owned arrays.

        Guarantees:
        - ``encoded_state`` has shape ``(EXPECTED_STATE_DIM,)`` and is finite.
        - ``images`` values are owned (Copied) ``np.ndarray`` and finite.
        - ``state`` sub-field arrays are owned copies and finite.
        - ``captured_at_s`` is a finite number.

        The deep copy makes a published ``ObservationSnapshot`` immune to
        later in-place mutation of the source buffers held by the collector
        cache (deploy_057 / P0-08 deep-ownership contract).
        """
        # --- encoded_state shape + finiteness ---
        encoded = _owned_array(self.encoded_state)
        if encoded.shape != (EXPECTED_STATE_DIM,):
            raise ValueError(
                f"encoded_state must have shape ({EXPECTED_STATE_DIM},), "
                f"got {encoded.shape}"
            )
        if not np.isfinite(encoded).all():
            raise ValueError("encoded_state contains non-finite values")

        # --- images: owned copies, finite ---
        if not isinstance(self.images, Mapping):
            raise TypeError(
                f"images must be a Mapping, got {type(self.images).__name__}"
            )
        owned_images: dict[str, np.ndarray] = {}
        for key, value in self.images.items():
            img = _owned_array(value)
            if not np.isfinite(img).all():
                raise ValueError(f"image '{key}' contains non-finite values")
            owned_images[key] = img

        # --- state sub-fields: owned copies, finite ---
        state = self.state
        state_arrays = {
            "left_tcp_position": _owned_array(state.left_tcp_position),
            "left_tcp_orientation": _owned_array(state.left_tcp_orientation),
            "right_tcp_position": _owned_array(state.right_tcp_position),
            "right_tcp_orientation": _owned_array(state.right_tcp_orientation),
        }
        for name, arr in state_arrays.items():
            if not np.isfinite(arr).all():
                raise ValueError(f"state.{name} contains non-finite values")
        owned_state = ObservationState(
            left_tcp_position=state_arrays["left_tcp_position"],
            left_tcp_orientation=state_arrays["left_tcp_orientation"],
            left_gripper_width=float(state.left_gripper_width),
            right_tcp_position=state_arrays["right_tcp_position"],
            right_tcp_orientation=state_arrays["right_tcp_orientation"],
            right_gripper_width=float(state.right_gripper_width),
        )

        # --- captured_at_s finiteness ---
        captured = float(self.captured_at_s)
        if not np.isfinite(captured):
            raise ValueError("captured_at_s must be a finite number")

        object.__setattr__(self, "encoded_state", encoded)
        object.__setattr__(self, "images", owned_images)
        object.__setattr__(self, "state", owned_state)
        object.__setattr__(self, "captured_at_s", captured)


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
