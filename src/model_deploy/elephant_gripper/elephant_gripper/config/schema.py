"""Configuration schema: typed parameters, defaults and validation.

No file I/O and no ROS/serial imports here. The ``repo`` layer parses YAML
into these frozen dataclasses; validation failures raise :class:`ConfigError`.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..types.gripper_types import (
    ANGLE_MAX,
    ANGLE_MIN,
    WIDTH_MAX,
    WIDTH_MIN,
    GripperSide,
)


class ConfigError(ValueError):
    """Raised when the configuration is structurally or semantically invalid."""


@dataclass(frozen=True)
class WidthAngleCalibration:
    """Linear map between normalized width [0,1] and firmware angle [0,100].

    ``angle_closed`` corresponds to width 0.0 and ``angle_open`` to width 1.0.
    They need not be 0/100 in case the mechanical range is restricted, but must
    stay within the firmware angle bounds and must differ so the map is
    invertible.
    """

    angle_closed: int = ANGLE_MIN
    angle_open: int = ANGLE_MAX

    def __post_init__(self) -> None:
        for name, value in (("angle_closed", self.angle_closed), ("angle_open", self.angle_open)):
            if not ANGLE_MIN <= value <= ANGLE_MAX:
                raise ConfigError(
                    f"{name} must be in [{ANGLE_MIN}, {ANGLE_MAX}], got {value}"
                )
        if self.angle_closed == self.angle_open:
            raise ConfigError("angle_closed and angle_open must differ (map not invertible)")


@dataclass(frozen=True)
class GripperLinkConfig:
    """Per-gripper serial link configuration."""

    side: GripperSide
    port: str
    baudrate: int = 115200
    gripper_id: int = 0x0E
    serial_timeout_s: float = 0.08
    enable_wait_s: float = 0.1
    set_angle_wait_s: float = 0.1
    poll_hz: float = 30.0
    reconnect_backoff_min_s: float = 0.5
    reconnect_backoff_max_s: float = 5.0
    command_min: float = WIDTH_MIN
    command_max: float = WIDTH_MAX
    calibration: WidthAngleCalibration = field(default_factory=WidthAngleCalibration)

    def __post_init__(self) -> None:
        if not self.port:
            raise ConfigError(f"{self.side.value}: port must not be empty")
        if self.baudrate <= 0:
            raise ConfigError(f"{self.side.value}: baudrate must be positive")
        if not 0 <= self.gripper_id <= 0xFF:
            raise ConfigError(f"{self.side.value}: gripper_id must be in range 0..255")
        if self.serial_timeout_s <= 0.0:
            raise ConfigError(f"{self.side.value}: serial_timeout_s must be positive")
        if self.enable_wait_s < 0.0 or self.set_angle_wait_s < 0.0:
            raise ConfigError(f"{self.side.value}: wait times must be non-negative")
        if self.poll_hz <= 0.0:
            raise ConfigError(f"{self.side.value}: poll_hz must be positive")
        if self.reconnect_backoff_min_s <= 0.0:
            raise ConfigError(f"{self.side.value}: reconnect_backoff_min_s must be positive")
        if self.reconnect_backoff_max_s < self.reconnect_backoff_min_s:
            raise ConfigError(
                f"{self.side.value}: reconnect_backoff_max_s must be >= min"
            )
        if not WIDTH_MIN <= self.command_min < self.command_max <= WIDTH_MAX:
            raise ConfigError(
                f"{self.side.value}: require {WIDTH_MIN} <= command_min < "
                f"command_max <= {WIDTH_MAX}"
            )


@dataclass(frozen=True)
class NodeConfig:
    """Whole-node configuration."""

    left: GripperLinkConfig
    right: GripperLinkConfig
    publish_hz: float = 50.0
    health_publish_hz: float = 5.0
    permit_timeout_s: float = 0.5
    command_timeout_s: float = 0.5
    hardware_id: str = "elephant_gripper"
    estop_on_startup: bool = False
    use_fake_serial: bool = False

    def __post_init__(self) -> None:
        if self.publish_hz <= 0.0:
            raise ConfigError("publish_hz must be positive")
        if self.health_publish_hz <= 0.0:
            raise ConfigError("health_publish_hz must be positive")
        if self.permit_timeout_s <= 0.0:
            raise ConfigError("permit_timeout_s must be positive")
        if self.command_timeout_s <= 0.0:
            raise ConfigError("command_timeout_s must be positive")
        if not self.hardware_id:
            raise ConfigError("hardware_id must not be empty")
        if self.left.side is not GripperSide.LEFT:
            raise ConfigError("left link must have side LEFT")
        if self.right.side is not GripperSide.RIGHT:
            raise ConfigError("right link must have side RIGHT")
