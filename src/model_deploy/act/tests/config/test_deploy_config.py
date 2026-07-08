"""验收项 6 (前半): DeployConfig 聚合 + frozen + 非法配置入口失败.

Verifies:
- Valid deploy.yaml → from_mapping constructs successfully, frozen
- Illegal yaml (missing field / wrong type) → DeployConfigError
"""

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from model_deploy.act.config.schema import (
    DeployConfig,
    DeployConfigError,
    TopicsConfig,
)


def _raw(**overrides) -> dict:
    r = {
        "bundle": {"bundle_dir": "/tmp/test"},
        "runtime": {
            "mode": "dry-run", "control_hz": 30.0, "inference_hz": 10.0,
            "chunk_size": 30, "execute_horizon": 10, "state_dim": 16,
            "action_dim": 16, "fallback_policy": "hold_last_action",
        },
        "image": {"image_size": 224},
        "topics": {"namespace": "/act"},
        "safety": {},
    }
    for k, v in overrides.items():
        if isinstance(v, dict) and isinstance(r.get(k), dict):
            r[k].update(v)
        else:
            r[k] = v
    return r


class TestDeployConfigConstruction:
    def test_valid_raw_constructs(self) -> None:
        cfg = DeployConfig.from_mapping(_raw(), base_dir=Path("/tmp"))
        assert isinstance(cfg, DeployConfig)
        assert cfg.runtime.state_dim == 16
        assert cfg.topics.namespace == "/act"

    def test_frozen_immutable(self) -> None:
        cfg = DeployConfig.from_mapping(_raw(), base_dir=Path("/tmp"))
        with pytest.raises(FrozenInstanceError):
            cfg.runtime = cfg.runtime  # type: ignore[misc]
        with pytest.raises(FrozenInstanceError):
            cfg.topics = TopicsConfig()  # type: ignore[misc]

    def test_raw_preserved(self) -> None:
        raw = _raw()
        cfg = DeployConfig.from_mapping(raw, base_dir=Path("/tmp"))
        assert cfg.raw["bundle"]["bundle_dir"] == "/tmp/test"


class TestIllegalConfigRejection:
    def test_missing_bundle_raises(self) -> None:
        raw = _raw()
        del raw["bundle"]
        with pytest.raises(DeployConfigError, match="Missing required"):
            DeployConfig.from_mapping(raw, base_dir=Path("/tmp"))

    def test_root_not_mapping_raises(self) -> None:
        from model_deploy.act.config.schema import load_deploy_config
        import tempfile
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("- not a mapping\n")
            p = f.name
        try:
            with pytest.raises(DeployConfigError, match="must be a mapping"):
                load_deploy_config(p)
        finally:
            Path(p).unlink()

    def test_wrong_type_raises(self) -> None:
        with pytest.raises(DeployConfigError, match="must be a string"):
            DeployConfig.from_mapping(_raw(runtime={"mode": 123}), base_dir=Path("/tmp"))


class TestCompleteConfigTree:
    def test_all_subconfigs_present(self) -> None:
        cfg = DeployConfig.from_mapping(_raw(), base_dir=Path("/tmp"))
        assert cfg.bundle is not None
        assert cfg.runtime is not None
        assert cfg.image is not None
        assert cfg.topics is not None
        assert cfg.safety is not None
        assert not hasattr(cfg, "bridge")
        assert not hasattr(cfg, "mux")
