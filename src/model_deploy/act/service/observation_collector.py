"""ObservationCollector – assemble ObservationSnapshot from cached sensor fields.

Thread-safe RAM cache of the latest image, TCP pose, and gripper width
values.  Provides completeness / freshness checks and constructs an
ObservationSnapshot when all required fields are present and within
``max_age_s``.

No ROS dependency — works with plain RAM values fed by the ui layer.
"""

from __future__ import annotations

import time
import threading
from typing import Callable, List, Mapping, Optional, Sequence

import numpy as np

from model_deploy.act.types.observation import (
    EXPECTED_STATE_DIM,
    ObservationState,
    ObservationSnapshot,
    ObservationFreshnessResult,
)

# Type alias for the state-codec callable that turns an ObservationState
# into a 16D encoded_state vector.
StateCodec = Callable[[ObservationState], np.ndarray]


def _default_state_codec(state: ObservationState) -> np.ndarray:
    """Encode an ObservationState into a 16D float32 vector.

    Segment layout (same as StateSpec / encode_state):
        [0:7)   left_tcp_pose  (xyz + quaternion)
        [7:14)  right_tcp_pose (xyz + quaternion)
        [14:15) left_gripper_width
        [15:16) right_gripper_width
    """
    left_tcp = np.concatenate(
        [np.asarray(state.left_tcp_position, dtype=np.float32).ravel(),
         np.asarray(state.left_tcp_orientation, dtype=np.float32).ravel()]
    )
    right_tcp = np.concatenate(
        [np.asarray(state.right_tcp_position, dtype=np.float32).ravel(),
         np.asarray(state.right_tcp_orientation, dtype=np.float32).ravel()]
    )
    left_grip = np.asarray([state.left_gripper_width], dtype=np.float32)
    right_grip = np.asarray([state.right_gripper_width], dtype=np.float32)

    encoded = np.concatenate([left_tcp, right_tcp, left_grip, right_grip])
    if encoded.shape[0] != EXPECTED_STATE_DIM:
        raise ValueError(
            f"Encoded state has {encoded.shape[0]} elements, expected {EXPECTED_STATE_DIM}"
        )
    return encoded.astype(np.float32)


class ObservationCollector:
    """Thread-safe sensor field cache and snapshot builder.

    Callback threads feed update_*(); the snapshot() method assembles
    an ObservationSnapshot when all required fields are present and fresh.

    Parameters:
        required_image_keys:  Camera names that must be received.
        required_state_fields: Pose / gripper field names that must be received.
        state_codec:          Callable ``(ObservationState) -> np.ndarray``
                              producing a 16D float32 vector.  Defaults to
                              ``_default_state_codec``.
    """

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def __init__(
        self,
        required_image_keys: Sequence[str],
        required_state_fields: Sequence[str],
        state_codec: StateCodec | None = None,
    ) -> None:
        self._required_image_keys: List[str] = list(required_image_keys)
        self._required_state_fields: List[str] = list(required_state_fields)
        self._state_codec: StateCodec = state_codec or _default_state_codec

        self._images: dict[str, np.ndarray] = {}
        self._values: dict[str, object] = {}
        self._stamps: dict[str, float] = {}
        self._lock: threading.RLock = threading.RLock()

    # ------------------------------------------------------------------
    # Field updaters (called from UI callbacks)
    # ------------------------------------------------------------------

    def update_image(self, name: str, image: np.ndarray) -> None:
        """Cache the latest decoded image for *name*."""
        with self._lock:
            self._images[name] = image
            self._stamps[name] = time.monotonic()

    def update_tcp_pose(
        self,
        side: str,
        position: np.ndarray | list | tuple,
        orientation: np.ndarray | list | tuple,
    ) -> None:
        """Cache TCP pose for *side* ('left' | 'right')."""
        pos_key = f"{side}_tcp_position"
        ori_key = f"{side}_tcp_orientation"
        now = time.monotonic()
        with self._lock:
            self._values[pos_key] = np.asarray(position, dtype=np.float32)
            self._values[ori_key] = np.asarray(orientation, dtype=np.float32)
            self._stamps[pos_key] = now
            self._stamps[ori_key] = now

    def update_gripper_state(self, side: str, width: float) -> None:
        """Cache the latest gripper width for *side* ('left' | 'right')."""
        key = f"{side}_gripper_width"
        with self._lock:
            self._values[key] = float(width)
            self._stamps[key] = time.monotonic()

    # ------------------------------------------------------------------
    # Diagnostic queries
    # ------------------------------------------------------------------

    def missing_fields(self) -> List[str]:
        """Return names of required fields that have never been received."""
        with self._lock:
            missing: List[str] = []
            for key in self._required_image_keys:
                if key not in self._images:
                    missing.append(key)
            for key in self._required_state_fields:
                if key not in self._values:
                    missing.append(key)
            return missing

    def stale_fields(self, now: float, max_age_s: float) -> List[str]:
        """Return names of cached fields whose latest update exceeds *max_age_s*."""
        with self._lock:
            stale: List[str] = []
            for key in self._required_image_keys:
                if key in self._stamps and (now - self._stamps[key]) > max_age_s:
                    stale.append(key)
            for key in self._required_state_fields:
                if key in self._stamps and (now - self._stamps[key]) > max_age_s:
                    stale.append(key)
            return stale

    # ------------------------------------------------------------------
    # Field-age map (for diagnostics / freshness result)
    # ------------------------------------------------------------------

    def _field_ages_s(self, now: float) -> dict[str, float]:
        """Build {field_name: age_seconds} for all cached required fields."""
        ages: dict[str, float] = {}
        for key in self._required_image_keys:
            if key in self._stamps:
                ages[key] = now - self._stamps[key]
        for key in self._required_state_fields:
            if key in self._stamps:
                ages[key] = now - self._stamps[key]
        return ages

    # ------------------------------------------------------------------
    # Snapshot construction
    # ------------------------------------------------------------------

    def snapshot(self, max_age_s: float) -> ObservationSnapshot | None:
        """Build a fresh ObservationSnapshot or return None.

        Returns ``None`` when any required field is missing or its latest
        update is older than *max_age_s*.  Otherwise constructs
        ``ObservationState``, encodes it to 16D, and returns the snapshot.
        """
        now = time.monotonic()
        with self._lock:
            missing = self.missing_fields()
            stale = self.stale_fields(now, max_age_s)
            ready = (len(missing) == 0 and len(stale) == 0)

            if not ready:
                return None

            # --- build ObservationState from cache ---
            state = ObservationState(
                left_tcp_position=self._values["left_tcp_position"],      # type: ignore[arg-type]
                left_tcp_orientation=self._values["left_tcp_orientation"],  # type: ignore[arg-type]
                left_gripper_width=float(self._values["left_gripper_width"]),  # type: ignore[arg-type]
                right_tcp_position=self._values["right_tcp_position"],    # type: ignore[arg-type]
                right_tcp_orientation=self._values["right_tcp_orientation"],  # type: ignore[arg-type]
                right_gripper_width=float(self._values["right_gripper_width"]),  # type: ignore[arg-type]
            )

            # --- encode via state codec ---
            encoded = self._state_codec(state)

            # --- build snapshot ---
            captured_at_s = time.time()
            return ObservationSnapshot(
                images=dict(self._images),
                state=state,
                encoded_state=encoded,
                captured_at_s=captured_at_s,
            )

    # ------------------------------------------------------------------
    # Freshness diagnostic report
    # ------------------------------------------------------------------

    def freshness_result(self, max_age_s: float) -> ObservationFreshnessResult:
        """Return a structured diagnostic without building a snapshot."""
        now = time.monotonic()
        with self._lock:
            missing = self.missing_fields()
            stale = self.stale_fields(now, max_age_s)
            ages = self._field_ages_s(now)
            ready = (len(missing) == 0 and len(stale) == 0)
            return ObservationFreshnessResult(
                missing_fields=missing,
                stale_fields=stale,
                field_ages_s=ages,
                ready=ready,
            )
