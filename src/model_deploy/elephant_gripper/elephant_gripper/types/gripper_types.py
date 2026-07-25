"""Pure data contracts for the Elephant gripper driver.

This module must not import ROS (rclpy) or serial. It defines the in-RAM
vocabulary shared by every other layer: sides, clamp status, state samples,
commands and health levels.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, IntEnum


class GripperSide(str, Enum):
    """Which physical gripper a value belongs to."""

    LEFT = "left"
    RIGHT = "right"


class ClampStatus(IntEnum):
    """Clamp state reported by register 0x0E (14)."""

    MOVING = 0
    STOPPED_NO_OBJECT = 1
    HOLDING = 2
    DROPPED = 3

    @classmethod
    def from_raw(cls, raw: int) -> "ClampStatus":
        try:
            return cls(int(raw))
        except ValueError:
            return cls.MOVING


class HealthLevel(IntEnum):
    """Health severity, ordered so ``max`` picks the worse level.

    Values mirror ``act_interfaces/HardwareHealth`` constants.
    """

    OK = 0
    DEGRADED = 1
    FAULT = 2


# Physical angle bounds reported/accepted by the gripper firmware.
ANGLE_MIN = 0
ANGLE_MAX = 100

# Normalized width bounds published on ROS topics (0.0 = closed, 1.0 = open).
WIDTH_MIN = 0.0
WIDTH_MAX = 1.0


@dataclass(frozen=True)
class GripperStateSample:
    """A single telemetry snapshot for one gripper.

    ``width`` is the normalized position in [0, 1]; ``angle`` is the raw
    firmware angle in [0, 100]. ``monotonic_s`` is the ``time.monotonic``
    timestamp when the sample was produced. ``valid`` is False for a
    placeholder / stale sample that must not be published as fresh telemetry.
    """

    side: GripperSide
    width: float
    angle: int
    clamp_status: ClampStatus
    monotonic_s: float
    valid: bool = True

    def __post_init__(self) -> None:
        if not WIDTH_MIN <= self.width <= WIDTH_MAX:
            raise ValueError(
                f"width must be in [{WIDTH_MIN}, {WIDTH_MAX}], got {self.width}"
            )
        if not ANGLE_MIN <= self.angle <= ANGLE_MAX:
            raise ValueError(
                f"angle must be in [{ANGLE_MIN}, {ANGLE_MAX}], got {self.angle}"
            )

    @classmethod
    def placeholder(cls, side: GripperSide, monotonic_s: float = 0.0) -> "GripperStateSample":
        """A neutral, invalid sample used before any real read arrives."""

        return cls(
            side=side,
            width=WIDTH_MIN,
            angle=ANGLE_MIN,
            clamp_status=ClampStatus.MOVING,
            monotonic_s=monotonic_s,
            valid=False,
        )


@dataclass(frozen=True)
class GripperCommand:
    """A normalized target-width command for one gripper."""

    side: GripperSide
    target_width: float

    def __post_init__(self) -> None:
        if not WIDTH_MIN <= self.target_width <= WIDTH_MAX:
            raise ValueError(
                f"target_width must be in [{WIDTH_MIN}, {WIDTH_MAX}], "
                f"got {self.target_width}"
            )


@dataclass(frozen=True)
class DeviceHealth:
    """Health of one gripper link."""

    side: GripperSide
    connected: bool
    status: HealthLevel
    detail: str = ""


@dataclass(frozen=True)
class NodeHealth:
    """Aggregated health of the whole node (worse of left/right)."""

    hardware_id: str
    status: HealthLevel
    left: DeviceHealth
    right: DeviceHealth
    estop_active: bool
    detail: str = ""
