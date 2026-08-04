"""SafetyConfig contract — deploy_032 ActionDomain-aligned thresholds.

Verifies defaults (meters / radians / gripper 0~1), illegal rejection, and
that hardware-register domains (300~1000) are not the schema defaults.
"""

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from model_deploy.act.config.schema import DeployConfig, DeployConfigError, SafetyConfig


class TestSafetyDefaults:
    def test_default_translation_and_rotation(self) -> None:
        s = SafetyConfig()
        assert s.max_translation_step_m == 0.01
        assert s.max_translation_step_m > 0
        assert s.max_rotation_step_rad == 0.05
        assert s.max_rotation_step_rad > 0

    def test_default_gripper_is_action_domain_not_hardware_register(self) -> None:
        s = SafetyConfig()
        assert s.gripper_min == 0.0
        assert s.gripper_max == 1.0
        assert s.gripper_min <= s.gripper_max
        assert s.max_gripper_step == 0.2
        assert s.max_gripper_step >= 0
        # Must not look like F100 / RM native hand register domain.
        assert not (s.gripper_min >= 100 and s.gripper_max >= 300)
        assert (s.gripper_min, s.gripper_max) != (300.0, 1000.0)

    def test_default_quaternion_and_domain_metadata(self) -> None:
        s = SafetyConfig()
        assert s.quaternion_norm_tolerance == 1e-3
        assert s.quaternion_norm_tolerance > 0
        assert s.pose_frame == "base"
        assert s.quaternion_order == "xyzw"
        assert s.gripper_domain == "normalized_0_1"

    def test_safety_frozen(self) -> None:
        s = SafetyConfig()
        with pytest.raises(FrozenInstanceError):
            s.max_translation_step_m = 0.99  # type: ignore[misc]

    def test_no_legacy_fields(self) -> None:
        s = SafetyConfig()
        for legacy in (
            "max_tcp_delta_per_step",
            "hand_min",
            "hand_max",
            "quaternion_check",
        ):
            assert not hasattr(s, legacy), f"SafetyConfig still has legacy field: {legacy}"


class TestSafetyInDeployConfig:
    def _raw(self, **safety_overrides) -> dict:
        return {
            "bundle": {"bundle_dir": "/tmp/test"},
            "runtime": {
                "mode": "dry-run",
                "control_hz": 30.0,
                "inference_hz": 10.0,
                "chunk_size": 30,
                "execute_horizon": 10,
                "state_dim": 16,
                "action_dim": 16,
                "fallback_policy": "hold_last_action",
            },
            "image": {"image_size": 224},
            "topics": {"namespace": "/act"},
            "safety": safety_overrides,
        }

    def test_empty_safety_uses_action_domain_defaults(self) -> None:
        cfg = DeployConfig.from_mapping(self._raw(), base_dir=Path("/tmp"))
        assert cfg.safety.max_translation_step_m == 0.01
        assert cfg.safety.max_rotation_step_rad == 0.05
        assert cfg.safety.gripper_min == 0.0
        assert cfg.safety.gripper_max == 1.0
        assert cfg.safety.max_gripper_step == 0.2
        assert cfg.safety.quaternion_norm_tolerance == 1e-3

    def test_custom_values_parsed(self) -> None:
        cfg = DeployConfig.from_mapping(
            self._raw(
                max_translation_step_m=0.005,
                max_rotation_step_rad=0.02,
                gripper_min=0.0,
                gripper_max=1.0,
                max_gripper_step=0.05,
                quaternion_norm_tolerance=1e-4,
                pose_frame="tcp",
                gripper_domain="normalized_0_1",
            ),
            base_dir=Path("/tmp"),
        )
        assert cfg.safety.max_translation_step_m == 0.005
        assert cfg.safety.max_rotation_step_rad == 0.02
        assert cfg.safety.gripper_min == 0.0
        assert cfg.safety.gripper_max == 1.0
        assert cfg.safety.max_gripper_step == 0.05
        assert cfg.safety.quaternion_norm_tolerance == 1e-4
        assert cfg.safety.pose_frame == "tcp"

    def test_translation_step_negative_rejected(self) -> None:
        with pytest.raises(DeployConfigError, match="max_translation_step_m"):
            DeployConfig.from_mapping(
                self._raw(max_translation_step_m=-0.01), base_dir=Path("/tmp")
            )

    def test_translation_step_zero_rejected(self) -> None:
        with pytest.raises(DeployConfigError, match="max_translation_step_m"):
            DeployConfig.from_mapping(
                self._raw(max_translation_step_m=0.0), base_dir=Path("/tmp")
            )

    def test_rotation_step_zero_rejected(self) -> None:
        with pytest.raises(DeployConfigError, match="max_rotation_step_rad"):
            DeployConfig.from_mapping(
                self._raw(max_rotation_step_rad=0.0), base_dir=Path("/tmp")
            )

    def test_gripper_min_exceeds_max_rejected(self) -> None:
        with pytest.raises(DeployConfigError, match="gripper_min"):
            DeployConfig.from_mapping(
                self._raw(gripper_min=0.9, gripper_max=0.1), base_dir=Path("/tmp")
            )

    def test_max_gripper_step_negative_rejected(self) -> None:
        with pytest.raises(DeployConfigError, match="max_gripper_step"):
            DeployConfig.from_mapping(
                self._raw(max_gripper_step=-0.01), base_dir=Path("/tmp")
            )

    def test_max_gripper_step_zero_allowed(self) -> None:
        cfg = DeployConfig.from_mapping(
            self._raw(max_gripper_step=0.0), base_dir=Path("/tmp")
        )
        assert cfg.safety.max_gripper_step == 0.0

    def test_quaternion_norm_tolerance_zero_rejected(self) -> None:
        with pytest.raises(DeployConfigError, match="quaternion_norm_tolerance"):
            DeployConfig.from_mapping(
                self._raw(quaternion_norm_tolerance=0.0), base_dir=Path("/tmp")
            )

    def test_legacy_max_tcp_delta_rejected(self) -> None:
        with pytest.raises(DeployConfigError, match="legacy keys"):
            DeployConfig.from_mapping(
                self._raw(max_tcp_delta_per_step=0.03), base_dir=Path("/tmp")
            )

    def test_legacy_hand_min_max_rejected(self) -> None:
        with pytest.raises(DeployConfigError, match="legacy keys"):
            DeployConfig.from_mapping(
                self._raw(hand_min=300.0, hand_max=1000.0), base_dir=Path("/tmp")
            )

    def test_legacy_quaternion_check_rejected(self) -> None:
        with pytest.raises(DeployConfigError, match="legacy keys"):
            DeployConfig.from_mapping(
                self._raw(quaternion_check=True), base_dir=Path("/tmp")
            )

    def test_invalid_quaternion_order_rejected(self) -> None:
        with pytest.raises(DeployConfigError, match="quaternion_order"):
            DeployConfig.from_mapping(
                self._raw(quaternion_order="wxyz"), base_dir=Path("/tmp")
            )
