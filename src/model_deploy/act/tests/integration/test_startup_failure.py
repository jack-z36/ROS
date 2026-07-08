"""验收项 6 (后半): 启动失败 — 非法配置在入口处失败.

End-to-end tests: illegal deploy.yaml / incomplete bundle → program must NOT
enter the run loop (i.e. load_deploy_config must raise).
"""

import json
from pathlib import Path

import pytest
import yaml

from model_deploy.act.config.schema import DeployConfigError, load_deploy_config


def _make_bundle(base: Path, *, state_dim: int = 16, action_dim: int = 16) -> Path:
    b = base / "bundle"
    b.mkdir()
    (b / "adapter").mkdir()
    (b / "checkpoint.pt").write_text("dummy")
    (b / "manifest.json").write_text(json.dumps({
        "schema_version": 1,
        "model": {"pretrained_path": "checkpoint.pt", "state_dim": state_dim, "action_dim": action_dim, "chunk_size": 30},
    }))
    (b / "normalizers.json").write_text(json.dumps({
        "state": {"min": [0.0]*state_dim, "max": [1.0]*state_dim, "identity_indices": []},
        "action": {"min": [-1.0]*action_dim, "max": [1.0]*action_dim, "identity_indices": []},
    }))
    (b / "experiment_config.yaml").write_text(yaml.safe_dump({
        "state_dim": state_dim, "action_dim": action_dim, "chunk_size": 30,
    }))
    return b


class TestStartupWithValidConfig:
    def test_valid_config_loads(self, tmp_path: Path) -> None:
        b = _make_bundle(tmp_path)
        y = tmp_path / "deploy.yaml"
        y.write_text(yaml.safe_dump({
            "bundle": {"bundle_dir": str(b)},
            "runtime": {"mode": "dry-run", "control_hz": 30.0, "inference_hz": 10.0,
                         "chunk_size": 30, "execute_horizon": 10, "state_dim": 16,
                         "action_dim": 16, "fallback_policy": "hold_last_action"},
            "image": {"image_size": 224},
            "topics": {"namespace": "/act"},
            "safety": {},
        }))
        cfg = load_deploy_config(y)
        assert cfg.runtime.state_dim == 16


class TestStartupFailureOnInvalidConfig:
    def test_yaml_not_mapping_fails(self, tmp_path: Path) -> None:
        y = tmp_path / "bad.yaml"
        y.write_text("[1, 2, 3]\n")
        with pytest.raises(DeployConfigError):
            load_deploy_config(y)

    def test_control_hz_zero_fails(self, tmp_path: Path) -> None:
        b = _make_bundle(tmp_path)
        y = tmp_path / "deploy.yaml"
        y.write_text(yaml.safe_dump({
            "bundle": {"bundle_dir": str(b)},
            "runtime": {"control_hz": 0},
            "image": {},
            "topics": {},
            "safety": {},
        }))
        with pytest.raises(DeployConfigError):
            load_deploy_config(y)

    def test_missing_bundle_section_fails(self, tmp_path: Path) -> None:
        y = tmp_path / "deploy.yaml"
        y.write_text(yaml.safe_dump({
            "runtime": {"control_hz": 30.0},
            "image": {},
            "topics": {},
            "safety": {},
        }))
        with pytest.raises(DeployConfigError):
            load_deploy_config(y)

    def test_dim_mismatch_fails(self, tmp_path: Path) -> None:
        b = _make_bundle(tmp_path, state_dim=20, action_dim=20)
        y = tmp_path / "deploy.yaml"
        y.write_text(yaml.safe_dump({
            "bundle": {"bundle_dir": str(b)},
            "runtime": {"mode": "dry-run", "control_hz": 30.0, "inference_hz": 10.0,
                         "chunk_size": 30, "execute_horizon": 10, "state_dim": 16,
                         "action_dim": 16, "fallback_policy": "hold_last_action"},
            "image": {"image_size": 224},
            "topics": {"namespace": "/act"},
            "safety": {},
        }))
        with pytest.raises(DeployConfigError):
            load_deploy_config(y)

    def test_normalizer_dim_mismatch_stops_startup(self, tmp_path: Path) -> None:
        """Normalizer with wrong dim must prevent startup."""
        b = _make_bundle(tmp_path, state_dim=8, action_dim=8)
        y = tmp_path / "deploy.yaml"
        y.write_text(yaml.safe_dump({
            "bundle": {"bundle_dir": str(b)},
            "runtime": {"mode": "dry-run", "control_hz": 30.0, "inference_hz": 10.0,
                         "chunk_size": 30, "execute_horizon": 10, "state_dim": 16,
                         "action_dim": 16, "fallback_policy": "hold_last_action"},
            "image": {"image_size": 224},
            "topics": {"namespace": "/act"},
            "safety": {},
        }))
        with pytest.raises(DeployConfigError):
            load_deploy_config(y)
