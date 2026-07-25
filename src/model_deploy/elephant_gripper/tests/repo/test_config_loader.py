"""Tests for the YAML config loader."""

import textwrap

import pytest

from elephant_gripper.config.schema import ConfigError
from elephant_gripper.repo.config_loader import load_config, parse_node_config
from elephant_gripper.types.gripper_types import GripperSide

_VALID_YAML = textwrap.dedent(
    """
    elephant_gripper_node:
      ros__parameters:
        left_port: /dev/elephant_gripper_left
        right_port: /dev/elephant_gripper_right
        baudrate: 115200
        gripper_id: 14
        publish_hz: 50.0
        poll_hz: 30.0
        permit_timeout_s: 0.5
        calibration:
          angle_closed: 0
          angle_open: 100
    """
)


def _write(tmp_path, text):
    path = tmp_path / "cfg.yaml"
    path.write_text(text, encoding="utf-8")
    return str(path)


def test_load_valid_config(tmp_path):
    config = load_config(_write(tmp_path, _VALID_YAML))
    assert config.left.side is GripperSide.LEFT
    assert config.left.port == "/dev/elephant_gripper_left"
    assert config.right.port == "/dev/elephant_gripper_right"
    assert config.left.baudrate == 115200
    assert config.publish_hz == 50.0
    assert config.left.calibration.angle_open == 100


def test_missing_file_raises():
    with pytest.raises(ConfigError):
        load_config("/nonexistent/path/cfg.yaml")


def test_missing_left_port_raises():
    with pytest.raises(ConfigError):
        parse_node_config({"right_port": "/dev/x"})


def test_missing_right_port_raises():
    with pytest.raises(ConfigError):
        parse_node_config({"left_port": "/dev/x"})


def test_invalid_command_range_raises():
    with pytest.raises(ConfigError):
        parse_node_config(
            {
                "left_port": "/dev/l",
                "right_port": "/dev/r",
                "command_min": 0.8,
                "command_max": 0.2,
            }
        )


def test_invalid_calibration_raises():
    with pytest.raises(ConfigError):
        parse_node_config(
            {
                "left_port": "/dev/l",
                "right_port": "/dev/r",
                "calibration": {"angle_closed": 50, "angle_open": 50},
            }
        )


def test_non_numeric_baudrate_raises():
    with pytest.raises(ConfigError):
        parse_node_config(
            {"left_port": "/dev/l", "right_port": "/dev/r", "baudrate": "fast"}
        )


def test_defaults_applied():
    config = parse_node_config({"left_port": "/dev/l", "right_port": "/dev/r"})
    assert config.publish_hz == 50.0
    assert config.permit_timeout_s == 0.5
    assert config.use_fake_serial is False
    assert config.left.baudrate == 115200
