"""deploy_056 startup-resource / config seam tests (P0-01..04, P0-06-config, P0-09-config).

Covers the L2-01 config seams fixed for L2-06:
- default deploy.yaml parses with command output OFF.
- ``load_deploy_config`` keyword ``command_output_enabled`` is the only switch;
  a persisted ``enabled`` in YAML is rejected.
- ``max_observation_age_sec`` is independent from ``max_action_age_sec``.
- ``max_inference_requests`` / ``max_pending_chunks`` must be exactly 1.
- canonical ``topics.observation.images`` mapping; legacy/conflict/missing/duplicate
  cases fail deterministically.
- null ``bundle_dir`` parses; the production resource loader fails fast on it.
"""

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from model_deploy.act.config.schema import (
    DeployConfig,
    DeployConfigError,
    ObservationTopicsConfig,
    load_deploy_config,
)
from model_deploy.act.repo import load_act_runtime_resources

DEPLOY_YAML = (
    Path(__file__).resolve().parents[4] / "model_deploy/act/config_files/deploy.yaml"
)


def _valid_raw(**overrides) -> dict:
    raw: dict = {
        "bundle": {"bundle_dir": None},
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
    }
    for section in ("runtime", "image", "topics", "safety"):
        if section in overrides:
            raw[section].update(overrides.pop(section))
    raw.update(overrides)
    return raw


# ---------------------------------------------------------------------------
# Default deploy.yaml + command-output master switch
# ---------------------------------------------------------------------------


class TestDefaultDeployYaml:
    def test_default_yaml_parses(self) -> None:
        cfg = load_deploy_config(DEPLOY_YAML)
        assert isinstance(cfg, DeployConfig)
        # 真实部署配置：model.checkpoint_dir 直接指向训练 checkpoint。
        assert cfg.model.checkpoint_dir is not None
        assert cfg.bundle.bundle_dir is None
        assert cfg.runtime.max_observation_age_sec > 0
        assert cfg.runtime.max_inference_requests == 1
        assert cfg.runtime.max_pending_chunks == 1

    def test_default_command_output_off(self) -> None:
        cfg = load_deploy_config(DEPLOY_YAML)
        assert cfg.command_output.command_output_enabled is False

    def test_real_command_has_feedback_window_and_driver_headroom(self) -> None:
        """Default deploy avoids response-progress E-stops but keeps action bounds."""
        cfg = load_deploy_config(DEPLOY_YAML)
        assert cfg.runtime.response_motion_check_enabled is False
        assert cfg.runtime.response_timeout_sec == 2.0
        assert cfg.safety.max_translation_step_m == 0.008
        assert cfg.safety.max_rotation_step_rad == 0.04

    def test_canonical_images_mapping_present(self) -> None:
        cfg = load_deploy_config(DEPLOY_YAML)
        topics = cfg.topics.observation.image_topics
        assert set(topics.keys()) == {"left", "right"}
        assert topics["left"] == "/act/observation/image/left_gripper_fisheye"
        assert topics["right"] == "/act/observation/image/right_gripper_fisheye"


class TestCommandOutputKeyword:
    def test_keyword_enables(self) -> None:
        raw = _valid_raw()
        raw["runtime"]["mode"] = "real-run"
        cfg = DeployConfig.from_mapping(
            raw, base_dir=Path("/tmp"), command_output_enabled=True
        )
        assert cfg.command_output.command_output_enabled is True

    def test_yaml_enabled_rejected(self) -> None:
        raw = _valid_raw()
        raw.setdefault("command_output", {})["enabled"] = True
        with pytest.raises(DeployConfigError, match="enabled must not appear"):
            DeployConfig.from_mapping(raw, base_dir=Path("/tmp"))

    def test_yaml_cannot_self_enable(self) -> None:
        raw = _valid_raw()
        raw.setdefault("command_output", {})["command_output_enabled"] = True
        cfg = DeployConfig.from_mapping(raw, base_dir=Path("/tmp"))
        assert cfg.command_output.command_output_enabled is False


# ---------------------------------------------------------------------------
# Observation freshness vs action age
# ---------------------------------------------------------------------------


class TestObservationAge:
    def test_independent_defaults(self) -> None:
        cfg = DeployConfig.from_mapping(_valid_raw(), base_dir=Path("/tmp"))
        assert cfg.runtime.max_observation_age_sec > 0
        assert cfg.runtime.max_observation_age_sec != cfg.runtime.max_action_age_sec

    def test_observation_age_must_be_positive(self) -> None:
        with pytest.raises(DeployConfigError, match="max_observation_age_sec"):
            DeployConfig.from_mapping(
                _valid_raw(runtime={"max_observation_age_sec": 0.0}), base_dir=Path("/tmp")
            )


# ---------------------------------------------------------------------------
# Queue sizes strict == 1
# ---------------------------------------------------------------------------


class TestQueueSize:
    @pytest.mark.parametrize("bad", [0, 2, 5])
    def test_inference_requests_must_be_one(self, bad: int) -> None:
        with pytest.raises(DeployConfigError, match="max_inference_requests"):
            DeployConfig.from_mapping(
                _valid_raw(runtime={"max_inference_requests": bad}), base_dir=Path("/tmp")
            )

    @pytest.mark.parametrize("bad", [0, 2, 5])
    def test_pending_chunks_must_be_one(self, bad: int) -> None:
        with pytest.raises(DeployConfigError, match="max_pending_chunks"):
            DeployConfig.from_mapping(
                _valid_raw(runtime={"max_pending_chunks": bad}), base_dir=Path("/tmp")
            )

    def test_one_is_accepted(self) -> None:
        cfg = DeployConfig.from_mapping(_valid_raw(), base_dir=Path("/tmp"))
        assert cfg.runtime.max_inference_requests == 1
        assert cfg.runtime.max_pending_chunks == 1


# ---------------------------------------------------------------------------
# Canonical camera mapping
# ---------------------------------------------------------------------------


class TestCameraMapping:
    def test_canonical_mapping_accepted(self) -> None:
        raw = _valid_raw()
        raw["topics"]["observation"] = {
            "arm_state": "/act/observation/arm_state",
            "images": {"left": "/act/im/left", "right": "/act/im/right"},
        }
        cfg = DeployConfig.from_mapping(raw, base_dir=Path("/tmp"))
        assert cfg.topics.observation.camera_keys == ("left", "right")
        assert cfg.topics.observation.image_topics["left"] == "/act/im/left"

    def test_legacy_and_canonical_conflict_fails(self) -> None:
        raw = _valid_raw()
        raw["topics"]["observation"] = {
            "left_image": "/act/im/left",
            "images": {"left": "/act/im/left", "right": "/act/im/right"},
        }
        with pytest.raises(DeployConfigError, match="cannot mix"):
            DeployConfig.from_mapping(raw, base_dir=Path("/tmp"))

    def test_legacy_only_fails(self) -> None:
        raw = _valid_raw()
        raw["topics"]["observation"] = {
            "left_image": "/act/im/left",
            "right_image": "/act/im/right",
        }
        with pytest.raises(DeployConfigError, match="canonical"):
            DeployConfig.from_mapping(raw, base_dir=Path("/tmp"))

    def test_missing_canonical_key_fails(self) -> None:
        raw = _valid_raw()
        raw["topics"]["observation"] = {
            "images": {"left": "/act/im/left"},
        }
        with pytest.raises(DeployConfigError, match="missing canonical"):
            DeployConfig.from_mapping(raw, base_dir=Path("/tmp"))

    def test_empty_images_fails(self) -> None:
        raw = _valid_raw()
        raw["topics"]["observation"] = {"images": {}}
        with pytest.raises(DeployConfigError, match="non-empty"):
            DeployConfig.from_mapping(raw, base_dir=Path("/tmp"))

    def test_empty_images_fails(self) -> None:
        raw = _valid_raw()
        raw["topics"]["observation"] = {"images": {}}
        with pytest.raises(DeployConfigError, match="non-empty"):
            DeployConfig.from_mapping(raw, base_dir=Path("/tmp"))

    def test_observation_topics_default_has_images(self) -> None:
        obs = ObservationTopicsConfig()
        assert obs.camera_keys == ("left", "right")
        assert obs.image_topics["left"] == "/act/observation/image/left_gripper_fisheye"


# ---------------------------------------------------------------------------
# Empty bundle -> resource loader fails fast
# ---------------------------------------------------------------------------


class TestEmptyBundle:
    def test_null_bundle_parses(self) -> None:
        cfg = DeployConfig.from_mapping(_valid_raw(bundle={"bundle_dir": None}), base_dir=Path("/tmp"))
        assert cfg.bundle.bundle_dir is None

    def test_resource_loader_rejects_empty_bundle(self) -> None:
        cfg = DeployConfig.from_mapping(_valid_raw(bundle={"bundle_dir": None}), base_dir=Path("/tmp"))
        with pytest.raises(DeployConfigError, match="bundle_dir is empty"):
            load_act_runtime_resources(cfg, load_policy=lambda p: object())
