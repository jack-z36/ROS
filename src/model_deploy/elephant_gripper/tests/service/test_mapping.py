"""Tests for width <-> angle mapping."""

from elephant_gripper.config.schema import WidthAngleCalibration
from elephant_gripper.service.mapping import angle_to_width, width_to_angle


def test_default_calibration_endpoints():
    calib = WidthAngleCalibration()
    assert width_to_angle(0.0, calib) == 0
    assert width_to_angle(1.0, calib) == 100
    assert width_to_angle(0.5, calib) == 50


def test_width_to_angle_clamps():
    calib = WidthAngleCalibration()
    assert width_to_angle(-1.0, calib) == 0
    assert width_to_angle(2.0, calib) == 100


def test_angle_to_width_endpoints():
    calib = WidthAngleCalibration()
    assert angle_to_width(0, calib) == 0.0
    assert angle_to_width(100, calib) == 1.0
    assert abs(angle_to_width(50, calib) - 0.5) < 1e-9


def test_angle_to_width_clamps():
    calib = WidthAngleCalibration()
    assert angle_to_width(-10, calib) == 0.0
    assert angle_to_width(200, calib) == 1.0


def test_restricted_calibration_range():
    calib = WidthAngleCalibration(angle_closed=20, angle_open=80)
    assert width_to_angle(0.0, calib) == 20
    assert width_to_angle(1.0, calib) == 80
    assert width_to_angle(0.5, calib) == 50
    assert abs(angle_to_width(50, calib) - 0.5) < 1e-9


def test_roundtrip_stability():
    calib = WidthAngleCalibration()
    for angle in range(0, 101):
        width = angle_to_width(angle, calib)
        assert width_to_angle(width, calib) == angle
