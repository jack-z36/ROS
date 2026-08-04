"""Tests for config/schema.py — deploy_008.

Covers acceptance scenarios S1 (valid config), S2 (invalid dims), S5 (no smoothing).
"""

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from model_deploy.act.config.schema import (
    BundleConfig,
    CommandTopicsConfig,
    DeployConfig,
    DeployConfigError,
    ImageConfig,
    ObservationTopicsConfig,
    RuntimeConfig,
    SafetyConfig,
    TopicsConfig,
)


# ---------------------------------------------------------------------------
# Helper — minimal valid raw mapping
# ---------------------------------------------------------------------------

def _valid_raw(bundle_dir: str | None = None, **overrides) -> dict:
    raw: dict = {
        "bundle": {"bundle_dir": bundle_dir or "/tmp/test_bundle"},
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
    # Merge overrides at top level
    for section in ("runtime", "image", "topics", "safety"):
        if section in overrides:
            raw[section].update(overrides.pop(section))
    raw.update(overrides)
    return raw


# ---------------------------------------------------------------------------
# S1 — valid config construction
# ---------------------------------------------------------------------------

class TestValidConfig:
    """S1: Legal config loads successfully."""

    def test_minimal_valid(self) -> None:
        cfg = DeployConfig.from_mapping(_valid_raw(), base_dir=Path("/tmp"))
        assert cfg.bundle.resolved_bundle_dir == Path("/tmp/test_bundle")
        assert cfg.runtime.mode == "dry-run"
        assert cfg.runtime.state_dim == 16
        assert cfg.runtime.action_dim == 16
        assert cfg.topics.namespace == "/act"
        assert cfg.image.image_size == 224
        assert cfg.safety.max_translation_step_m == 0.03
        assert cfg.safety.max_rotation_step_rad == 0.1
        assert cfg.safety.gripper_min == 0.0
        assert cfg.safety.gripper_max == 1.0
        assert cfg.safety.quaternion_norm_tolerance == 1e-3

    def test_raw_preserved(self) -> None:
        raw = _valid_raw()
        cfg = DeployConfig.from_mapping(raw, base_dir=Path("/tmp"))
        assert cfg.raw["bundle"]["bundle_dir"] == "/tmp/test_bundle"
        assert cfg.raw["runtime"]["state_dim"] == 16

    def test_frozen(self) -> None:
        cfg = DeployConfig.from_mapping(_valid_raw(), base_dir=Path("/tmp"))
        with pytest.raises(FrozenInstanceError):
            cfg.runtime = RuntimeConfig()  # type: ignore[misc]


# ---------------------------------------------------------------------------
# S2 — invalid dimension rejection
# ---------------------------------------------------------------------------

class TestInvalidDimensions:
    """S2: state_dim=26 or action_dim=14 must be rejected."""

    def test_state_dim_26_accepted_by_schema(self) -> None:
        """Schema parses any positive int for dims — cross-validation is deploy_009's job."""
        raw = _valid_raw()
        raw["runtime"]["state_dim"] = 26
        cfg = DeployConfig.from_mapping(raw, base_dir=Path("/tmp"))
        assert cfg.runtime.state_dim == 26

    def test_from_mapping_parses_any_dim(self) -> None:
        """Verify from_mapping doesn't reject non-16 dims (that's deploy_009's job)."""
        raw = _valid_raw()
        raw["runtime"]["state_dim"] = 26
        raw["runtime"]["action_dim"] = 14
        cfg = DeployConfig.from_mapping(raw, base_dir=Path("/tmp"))
        assert cfg.runtime.state_dim == 26
        assert cfg.runtime.action_dim == 14


# ---------------------------------------------------------------------------
# Validation edge cases
# ---------------------------------------------------------------------------

class TestRuntimeValidation:
    def test_negative_control_hz_raises(self) -> None:
        raw = _valid_raw()
        raw["runtime"]["control_hz"] = 0.0
        with pytest.raises(DeployConfigError, match="control_hz must be positive"):
            DeployConfig.from_mapping(raw, base_dir=Path("/tmp"))

    def test_negative_inference_hz_raises(self) -> None:
        raw = _valid_raw()
        raw["runtime"]["inference_hz"] = -1.0
        with pytest.raises(DeployConfigError, match="inference_hz must be positive"):
            DeployConfig.from_mapping(raw, base_dir=Path("/tmp"))

    def test_execute_horizon_exceeds_chunk_size_raises(self) -> None:
        raw = _valid_raw()
        raw["runtime"]["execute_horizon"] = 50
        raw["runtime"]["chunk_size"] = 30
        with pytest.raises(DeployConfigError, match="execute_horizon"):
            DeployConfig.from_mapping(raw, base_dir=Path("/tmp"))

    def test_prefetch_exceeds_execute_horizon_raises(self) -> None:
        raw = _valid_raw()
        raw["runtime"]["prefetch_steps"] = 20
        raw["runtime"]["execute_horizon"] = 10
        with pytest.raises(DeployConfigError, match="prefetch_steps"):
            DeployConfig.from_mapping(raw, base_dir=Path("/tmp"))

    def test_invalid_fallback_policy_raises(self) -> None:
        raw = _valid_raw()
        raw["runtime"]["fallback_policy"] = "bad_policy"
        with pytest.raises(DeployConfigError, match="fallback_policy"):
            DeployConfig.from_mapping(raw, base_dir=Path("/tmp"))

    def test_missing_bundle_raises(self) -> None:
        raw = _valid_raw()
        del raw["bundle"]
        with pytest.raises(DeployConfigError, match="Missing required"):
            DeployConfig.from_mapping(raw, base_dir=Path("/tmp"))


class TestPublishesCommandTopics:
    def test_dry_run_does_not_publish(self) -> None:
        cfg = DeployConfig.from_mapping(_valid_raw(), base_dir=Path("/tmp"))
        assert cfg.runtime.publishes_command_topics is False

    def test_shadow_run_publishes(self) -> None:
        raw = _valid_raw()
        raw["runtime"]["mode"] = "shadow-run"
        cfg = DeployConfig.from_mapping(raw, base_dir=Path("/tmp"))
        assert cfg.runtime.publishes_command_topics is True


# ---------------------------------------------------------------------------
# S5 — no smoothing fields
# ---------------------------------------------------------------------------

class TestNoSmoothingFields:
    """S5: schema must not contain any smoothing-related fields."""

    def test_runtime_has_no_blend_steps(self) -> None:
        assert not hasattr(RuntimeConfig, "blend_steps")

    def test_no_smoothing_in_defaults(self) -> None:
        r = RuntimeConfig()
        for forbidden in (
            "blend_steps",
            "smoothstep_window",
            "smoothstep_alpha",
            "cross_chunk_fusion",
            "chunk_blend_mode",
            "rtc_alignment",
            "action_smoothing",
        ):
            assert not hasattr(r, forbidden), f"RuntimeConfig has forbidden field: {forbidden}"


class TestNoBridgeMux:
    """Verify bridge/mux config sections are absent."""

    def test_deploy_config_no_bridge(self) -> None:
        cfg = DeployConfig.from_mapping(_valid_raw(), base_dir=Path("/tmp"))
        assert not hasattr(cfg, "bridge")
        assert not hasattr(cfg, "mux")

    def test_topics_no_bridge_mux(self) -> None:
        assert not hasattr(TopicsConfig, "bridge_output")
        assert not hasattr(TopicsConfig, "mux")


class TestTopicsNamespace:
    def test_default_namespace_is_act(self) -> None:
        cfg = DeployConfig.from_mapping(_valid_raw(), base_dir=Path("/tmp"))
        assert cfg.topics.namespace == "/act"

    def test_observation_topic_defaults_under_act(self) -> None:
        obs = ObservationTopicsConfig()
        assert obs.left_image.startswith("/act/")
        assert obs.right_image.startswith("/act/")

    def test_command_topic_defaults_under_act(self) -> None:
        cmd = CommandTopicsConfig()
        assert cmd.policy_action.startswith("/act/")
        assert cmd.status.startswith("/act/")


class TestTypedValidators:
    def test_positive_float_rejects_zero(self) -> None:
        raw = _valid_raw()
        raw["runtime"]["control_hz"] = 0.0
        with pytest.raises(DeployConfigError):
            DeployConfig.from_mapping(raw, base_dir=Path("/tmp"))

    def test_choice_rejects_unknown(self) -> None:
        raw = _valid_raw()
        raw["runtime"]["mode"] = "unsafe"
        with pytest.raises(DeployConfigError, match="mode"):
            DeployConfig.from_mapping(raw, base_dir=Path("/tmp"))

    def test_bool_accepts_strings(self) -> None:
        raw = _valid_raw()
        raw["runtime"]["compile_model"] = "true"
        cfg = DeployConfig.from_mapping(raw, base_dir=Path("/tmp"))
        assert cfg.runtime.compile_model is True
