"""Pure width <-> angle mapping using a linear calibration.

Width is the normalized ROS value in [0, 1] (0 closed, 1 open); angle is the
firmware value in [0, 100]. No serial, no ROS.
"""

from __future__ import annotations

from ..config.schema import WidthAngleCalibration
from ..types.gripper_types import (
    ANGLE_MAX,
    ANGLE_MIN,
    WIDTH_MAX,
    WIDTH_MIN,
)


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def width_to_angle(width: float, calib: WidthAngleCalibration) -> int:
    """Map normalized width [0,1] to an integer firmware angle [0,100]."""

    width = _clamp(width, WIDTH_MIN, WIDTH_MAX)
    span = calib.angle_open - calib.angle_closed
    angle = calib.angle_closed + span * width
    angle_int = int(round(angle))
    return int(_clamp(angle_int, ANGLE_MIN, ANGLE_MAX))


def angle_to_width(angle: int, calib: WidthAngleCalibration) -> float:
    """Map a firmware angle [0,100] back to normalized width [0,1]."""

    span = calib.angle_open - calib.angle_closed
    if span == 0:
        return WIDTH_MIN
    width = (angle - calib.angle_closed) / span
    return _clamp(width, WIDTH_MIN, WIDTH_MAX)
