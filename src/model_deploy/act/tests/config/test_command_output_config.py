"""Tests for C7 CommandOutputConfig assembly — deploy_041 (G02/G03).

Covers: default-off master switch, explicit bool override from the startup
caller, rejection of a persisted `enabled` in deploy.yaml, and parameter
validation for frame / mapping / deadband / interval / QoS.
"""

from pathlib import Path

import pytest

from model_deploy.act.config.schema import (
    CommandOutputConfig,
    DeployConfig,
    DeployConfigError,
)


# ---------------------------------------------------------------------------
# C7 dataclass defaults
# ---------------------------------------------------------------------------


class TestCommandOutputConfigDefaults:
    def test_default_off(self) -> None:
        cfg = CommandOutputConfig()
        assert cfg.command_output_enabled is False
        assert cfg.left_pose_frame_id == "left_arm_base"
        assert cfg.right_pose_frame_id == "right_arm_base"
        assert cfg.gripper_deadband == 0.01
        assert cfg.gripper_min_publish_interval_s == 0.05
        assert cfg.qos_depth == 10

    def test_explicit_on(self) -> None:
        cfg = CommandOutputConfig(command_output_enabled=True)
        assert cfg.command_output_enabled is True

    def test_frozen(self) -> None:
        from dataclasses import FrozenInstanceError

        cfg = CommandOutputConfig()
        with pytest.raises(FrozenInstanceError):
            cfg.left_pose_frame_id = "other"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# DeployConfig.command_output assembly
# ---------------------------------------------------------------------------


def _valid_raw() -> dict:
    return {
        "bundle": {"bundle_dir": "/tmp/test_bundle"},
        "runtime": {
            "mode": "dry-run",
            "control_hz": 30.0,
            "inference_hz": 10.0,
            "chunk_size": 30,
            "execute_horizon": 10,
            "prefetch_steps": 5,
            "state_dim": 16,
            "action_dim": 16,
            "fallback_policy": "hold_last_action",
        },
        "image": {"image_size": 224},
        "topics": {"namespace": "/act"},
        "safety": {},
        "command_output": {
            "left_pose_frame_id": "left_arm_base",
            "right_pose_frame_id": "right_arm_base",
            "gripper_deadband": 0.01,
            "gripper_min_publish_interval_s": 0.05,
            "qos_depth": 10,
        },
    }


class TestDeployConfigCommandOutput:
    def test_default_off(self) -> None:
        cfg = DeployConfig.from_mapping(_valid_raw(), base_dir=Path("/tmp"))
        assert isinstance(cfg.command_output, CommandOutputConfig)
        assert cfg.command_output.command_output_enabled is False

    def test_explicit_on_from_caller(self) -> None:
        raw = _valid_raw()
        raw["runtime"]["mode"] = "real-run"
        cfg = DeployConfig.from_mapping(
            raw, base_dir=Path("/tmp"), command_output_enabled=True
        )
        assert cfg.command_output.command_output_enabled is True

    def test_persisted_enabled_rejected(self) -> None:
        raw = _valid_raw()
        raw["command_output"]["enabled"] = True
        with pytest.raises(DeployConfigError, match="enabled must not appear"):
            DeployConfig.from_mapping(raw, base_dir=Path("/tmp"))

    def test_persisted_enabled_false_still_rejected(self) -> None:
        # Any persisted `enabled` key is rejected, regardless of value.
        raw = _valid_raw()
        raw["command_output"]["enabled"] = False
        with pytest.raises(DeployConfigError, match="enabled must not appear"):
            DeployConfig.from_mapping(raw, base_dir=Path("/tmp"))

    def test_missing_section_defaults(self) -> None:
        raw = _valid_raw()
        del raw["command_output"]
        cfg = DeployConfig.from_mapping(raw, base_dir=Path("/tmp"))
        assert cfg.command_output.command_output_enabled is False
        assert cfg.command_output.left_pose_frame_id == "left_arm_base"
        assert cfg.command_output.right_pose_frame_id == "right_arm_base"

    def test_yaml_cannot_turn_on_command(self) -> None:
        # Even if a YAML author tried `command_output_enabled: true`, it is not
        # a recognised key and the master switch stays off (caller decides).
        raw = _valid_raw()
        raw["command_output"]["command_output_enabled"] = True
        cfg = DeployConfig.from_mapping(raw, base_dir=Path("/tmp"))
        assert cfg.command_output.command_output_enabled is False


# ---------------------------------------------------------------------------
# C7 parameter validation
# ---------------------------------------------------------------------------


class TestCommandOutputValidation:
    def _raw(self, **overrides) -> dict:
        raw = _valid_raw()
        raw["command_output"].update(overrides)
        return raw

    def test_wrong_left_pose_frame_rejected(self) -> None:
        with pytest.raises(DeployConfigError, match="left_pose_frame_id"):
            DeployConfig.from_mapping(
                self._raw(left_pose_frame_id="base"), base_dir=Path("/tmp")
            )

    def test_deadband_exceeds_span_rejected(self) -> None:
        with pytest.raises(DeployConfigError, match="gripper_deadband"):
            DeployConfig.from_mapping(
                self._raw(gripper_deadband=1.1),
                base_dir=Path("/tmp"),
            )

    @pytest.mark.parametrize(
        "legacy_key",
        (
            "pose_frame_id",
            "gripper_input_min",
            "gripper_input_max",
            "gripper_output_min",
            "gripper_output_max",
        ),
    )
    def test_removed_mapping_keys_rejected(self, legacy_key: str) -> None:
        with pytest.raises(DeployConfigError, match="removed keys"):
            DeployConfig.from_mapping(
                self._raw(**{legacy_key: 0.0}), base_dir=Path("/tmp")
            )

    def test_negative_deadband_rejected(self) -> None:
        with pytest.raises(DeployConfigError, match="gripper_deadband"):
            DeployConfig.from_mapping(
                self._raw(gripper_deadband=-1.0), base_dir=Path("/tmp")
            )

    def test_negative_interval_rejected(self) -> None:
        with pytest.raises(DeployConfigError, match="gripper_min_publish_interval"):
            DeployConfig.from_mapping(
                self._raw(gripper_min_publish_interval_s=-0.1), base_dir=Path("/tmp")
            )

    def test_qos_depth_not_positive_rejected(self) -> None:
        with pytest.raises(DeployConfigError, match="qos_depth"):
            DeployConfig.from_mapping(self._raw(qos_depth=0), base_dir=Path("/tmp"))
