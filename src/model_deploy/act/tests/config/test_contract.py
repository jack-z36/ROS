"""验收项 5: bundle 交付物校验 + normalizer 维度一致性.

Covers:
- BundleContractResult for complete / missing bundle
- NormalizerContractResult for dim 16 pass / dim mismatch fail
- load_deploy_config end-to-end contract validation
"""

import json
from pathlib import Path

import pytest
import yaml

from model_deploy.act.config.schema import (
    DeployConfig,
    DeployConfigError,
    check_bundle_contract,
    check_normalizer_contract,
    load_deploy_config,
)
from model_deploy.act.repo.normalization import ActionStateNormalizer
from model_deploy.act.types.contract_result import (
    BundleContractResult,
    NormalizerContractResult,
)


# ---- helpers ----

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


def _deploy_yaml(path: Path, bundle_dir: str, state_dim: int = 16, action_dim: int = 16) -> None:
    path.write_text(yaml.safe_dump({
        "bundle": {"bundle_dir": bundle_dir},
        "runtime": {"mode": "dry-run", "control_hz": 30.0, "inference_hz": 10.0, "chunk_size": 30,
                     "execute_horizon": 10, "state_dim": state_dim, "action_dim": action_dim,
                     "fallback_policy": "hold_last_action"},
        "image": {"image_size": 224},
        "topics": {"namespace": "/act"},
        "safety": {},
    }))


# ---- tests ----


class TestBundleContract:
    def test_complete_bundle_passes(self, tmp_path: Path) -> None:
        b = _make_bundle(tmp_path)
        manifest = json.loads((b / "manifest.json").read_text())
        r = check_bundle_contract(b, manifest)
        assert isinstance(r, BundleContractResult)
        assert r.is_pass
        assert r.missing_files == ()

    def test_missing_adapter_fails(self, tmp_path: Path) -> None:
        import shutil
        b = _make_bundle(tmp_path)
        shutil.rmtree(b / "adapter")
        manifest = json.loads((b / "manifest.json").read_text())
        r = check_bundle_contract(b, manifest)
        assert not r.is_pass
        assert "adapter" in r.missing_files

    def test_missing_normalizers_fails(self, tmp_path: Path) -> None:
        b = _make_bundle(tmp_path)
        (b / "normalizers.json").unlink()
        manifest = json.loads((b / "manifest.json").read_text())
        r = check_bundle_contract(b, manifest)
        assert not r.is_pass


class TestNormalizerContract:
    def test_dim_16_passes(self) -> None:
        sn = ActionStateNormalizer(min_vals=[0]*16, max_vals=[1]*16)
        an = ActionStateNormalizer(min_vals=[-1]*16, max_vals=[1]*16)
        r = check_normalizer_contract(sn, an)
        assert isinstance(r, NormalizerContractResult)
        assert r.is_pass

    def test_dim_14_fails(self) -> None:
        sn = ActionStateNormalizer(min_vals=[0]*14, max_vals=[1]*14)
        an = ActionStateNormalizer(min_vals=[-1]*14, max_vals=[1]*14)
        r = check_normalizer_contract(sn, an)
        assert not r.is_pass
        assert r.actual_dim == 14

    def test_failure_reason_readable(self) -> None:
        sn = ActionStateNormalizer(min_vals=[0]*10, max_vals=[1]*10)
        an = ActionStateNormalizer(min_vals=[0]*16, max_vals=[1]*16)
        r = check_normalizer_contract(sn, an)
        assert not r.is_pass
        assert "State normalizer" in r.reason


class TestLoadDeployConfigContract:
    def test_e2e_pass(self, tmp_path: Path) -> None:
        b = _make_bundle(tmp_path)
        y = tmp_path / "deploy.yaml"
        _deploy_yaml(y, str(b))
        cfg = load_deploy_config(y)
        assert isinstance(cfg, DeployConfig)

    def test_dim_mismatch_raises(self, tmp_path: Path) -> None:
        b = _make_bundle(tmp_path, state_dim=14, action_dim=14)
        y = tmp_path / "deploy.yaml"
        _deploy_yaml(y, str(b))
        with pytest.raises(DeployConfigError):
            load_deploy_config(y)

    def test_bundle_incomplete_raises(self, tmp_path: Path) -> None:
        b = _make_bundle(tmp_path)
        (b / "normalizers.json").unlink()
        y = tmp_path / "deploy.yaml"
        _deploy_yaml(y, str(b))
        with pytest.raises(DeployConfigError):
            load_deploy_config(y)
