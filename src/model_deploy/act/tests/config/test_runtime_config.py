"""验收项 3: Runtime 参数校验 — hz/chunk/mode/fallback.

Verifies that RuntimeConfig.__post_init__ rejects:
- hz ≤ 0
- invalid mode
- execute_horizon > chunk_size
- prefetch_steps > execute_horizon
- unknown fallback_policy
and that valid values construct successfully.
"""

from pathlib import Path

import pytest

from model_deploy.act.config.schema import DeployConfig, DeployConfigError


def _raw(**overrides) -> dict:
    runtime = {
        "mode": "dry-run",
        "control_hz": 30.0,
        "inference_hz": 10.0,
        "chunk_size": 30,
        "execute_horizon": 10,
        "prefetch_steps": 5,
        "state_dim": 16,
        "action_dim": 16,
        "fallback_policy": "hold_last_action",
    }
    runtime.update(overrides)
    return {
        "bundle": {"bundle_dir": "/tmp/test"},
        "runtime": runtime,
        "image": {"image_size": 224},
        "topics": {"namespace": "/act"},
        "safety": {},
    }


class TestRuntimeHZ:
    def test_control_hz_zero_rejected(self) -> None:
        with pytest.raises(DeployConfigError, match="control_hz"):
            DeployConfig.from_mapping(_raw(control_hz=0.0), base_dir=Path("/tmp"))

    def test_control_hz_negative_rejected(self) -> None:
        with pytest.raises(DeployConfigError, match="control_hz"):
            DeployConfig.from_mapping(_raw(control_hz=-5.0), base_dir=Path("/tmp"))

    def test_inference_hz_zero_rejected(self) -> None:
        with pytest.raises(DeployConfigError, match="inference_hz"):
            DeployConfig.from_mapping(_raw(inference_hz=0.0), base_dir=Path("/tmp"))

    def test_inference_hz_negative_rejected(self) -> None:
        with pytest.raises(DeployConfigError, match="inference_hz"):
            DeployConfig.from_mapping(_raw(inference_hz=-1.0), base_dir=Path("/tmp"))

    def test_positive_hz_accepted(self) -> None:
        cfg = DeployConfig.from_mapping(_raw(control_hz=60.0, inference_hz=20.0), base_dir=Path("/tmp"))
        assert cfg.runtime.control_hz == 60.0
        assert cfg.runtime.inference_hz == 20.0

    def test_default_delta_matches_rm65_driver_limit(self) -> None:
        cfg = DeployConfig.from_mapping(_raw(), base_dir=Path("/tmp"))
        assert cfg.runtime.max_delta_per_step == 0.01

    def test_delta_wider_than_rm65_driver_rejected(self) -> None:
        with pytest.raises(DeployConfigError, match="max_delta_per_step"):
            DeployConfig.from_mapping(
                _raw(max_delta_per_step=0.011), base_dir=Path("/tmp")
            )


class TestRuntimeMode:
    def test_invalid_mode_rejected(self) -> None:
        with pytest.raises(DeployConfigError, match="mode"):
            DeployConfig.from_mapping(_raw(mode="unsafe"), base_dir=Path("/tmp"))

    def test_valid_modes_accepted(self) -> None:
        for mode, enabled in (("dry-run", False), ("real-run", True)):
            cfg = DeployConfig.from_mapping(
                _raw(mode=mode),
                base_dir=Path("/tmp"),
                command_output_enabled=enabled,
            )
            assert cfg.runtime.mode == mode

    def test_real_run_requires_explicit_command_confirmation(self) -> None:
        with pytest.raises(DeployConfigError, match="requires.*enable-command-output"):
            DeployConfig.from_mapping(_raw(mode="real-run"), base_dir=Path("/tmp"))

    def test_dry_run_rejects_command_confirmation(self) -> None:
        with pytest.raises(DeployConfigError, match="dry-run"):
            DeployConfig.from_mapping(
                _raw(mode="dry-run"),
                base_dir=Path("/tmp"),
                command_output_enabled=True,
            )


class TestChunkSize:
    def test_execute_horizon_exceeds_chunk_size_rejected(self) -> None:
        with pytest.raises(DeployConfigError, match="execute_horizon"):
            DeployConfig.from_mapping(_raw(chunk_size=10, execute_horizon=20), base_dir=Path("/tmp"))

    def test_prefetch_exceeds_execute_horizon_rejected(self) -> None:
        with pytest.raises(DeployConfigError, match="prefetch_steps"):
            DeployConfig.from_mapping(_raw(execute_horizon=5, prefetch_steps=10), base_dir=Path("/tmp"))

    def test_valid_chunk_accepted(self) -> None:
        cfg = DeployConfig.from_mapping(_raw(chunk_size=50, execute_horizon=10, prefetch_steps=3), base_dir=Path("/tmp"))
        assert cfg.runtime.chunk_size == 50
        assert cfg.runtime.execute_horizon == 10


class TestFallbackPolicy:
    def test_unknown_fallback_rejected(self) -> None:
        with pytest.raises(DeployConfigError, match="fallback_policy"):
            DeployConfig.from_mapping(_raw(fallback_policy="do_nothing"), base_dir=Path("/tmp"))

    def test_valid_fallback_accepted(self) -> None:
        for policy in ("hold_last_action", "continue_old_chunk", "safe_stop"):
            cfg = DeployConfig.from_mapping(_raw(fallback_policy=policy), base_dir=Path("/tmp"))
            assert cfg.runtime.fallback_policy == policy


class TestValidConfig:
    def test_valid_runtime_constructs(self) -> None:
        cfg = DeployConfig.from_mapping(_raw(), base_dir=Path("/tmp"))
        assert cfg.runtime.control_hz == 30.0
        assert cfg.runtime.mode == "dry-run"
        assert cfg.runtime.chunk_size == 30


# ── image_shape tests ────────────────────────────────────────────


def _raw_with_image(**image_overrides) -> dict:
    """Return a raw mapping with image section overridden."""
    mapping = _raw()
    mapping["image"].update(image_overrides)
    return mapping


class TestImageShape:
    def test_image_shape_non_square(self) -> None:
        cfg = DeployConfig.from_mapping(
            _raw_with_image(image_shape=[480, 640]), base_dir=Path("/tmp")
        )
        assert cfg.image.image_shape == (480, 640)
        assert cfg.image.resolved_image_hw == (480, 640)
        # image_size is still stored independently
        assert cfg.image.image_size == 224

    def test_image_shape_backward_compat(self) -> None:
        cfg = DeployConfig.from_mapping(_raw(), base_dir=Path("/tmp"))
        assert cfg.image.image_shape is None
        assert cfg.image.resolved_image_hw == (224, 224)

    @pytest.mark.parametrize(
        "bad_shape",
        [
            [-1, 640],       # negative value
            [480, 0],        # zero value
            [480],           # length 1
            [480, 640, 3],   # length 3
        ],
    )
    def test_image_shape_invalid_rejected(self, bad_shape) -> None:
        with pytest.raises(DeployConfigError, match="image_shape"):
            DeployConfig.from_mapping(
                _raw_with_image(image_shape=bad_shape), base_dir=Path("/tmp")
            )
