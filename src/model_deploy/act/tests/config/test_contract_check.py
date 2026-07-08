"""Tests for contract cross-validation — deploy_009.

Covers:
- check_bundle_contract: complete / missing files
- check_normalizer_contract: dim 16 pass / dim mismatch fail
- load_deploy_config: end-to-end pass / bundle incomplete / dim mismatch
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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_bundle(base: Path, *, state_dim: int = 16, action_dim: int = 16) -> Path:
    """Create a minimal valid mock bundle under *base*."""
    bundle = base / "bundle"
    bundle.mkdir()
    adapter = bundle / "adapter"
    adapter.mkdir()
    (bundle / "checkpoint.pt").write_text("dummy")

    manifest = {
        "schema_version": 1,
        "model": {
            "pretrained_path": "checkpoint.pt",
            "state_dim": state_dim,
            "action_dim": action_dim,
            "chunk_size": 30,
        },
    }
    (bundle / "manifest.json").write_text(json.dumps(manifest))

    normalizers = {
        "state": {"min": [0.0] * state_dim, "max": [1.0] * state_dim, "identity_indices": []},
        "action": {"min": [-1.0] * action_dim, "max": [1.0] * action_dim, "identity_indices": []},
    }
    (bundle / "normalizers.json").write_text(json.dumps(normalizers))

    experiment = {"state_dim": state_dim, "action_dim": action_dim, "chunk_size": 30}
    (bundle / "experiment_config.yaml").write_text(yaml.safe_dump(experiment))

    return bundle


def _write_deploy_yaml(path: Path, bundle_dir: str, state_dim: int = 16, action_dim: int = 16) -> None:
    payload = {
        "bundle": {"bundle_dir": bundle_dir},
        "runtime": {
            "mode": "dry-run",
            "control_hz": 30.0,
            "inference_hz": 10.0,
            "chunk_size": 30,
            "execute_horizon": 10,
            "state_dim": state_dim,
            "action_dim": action_dim,
            "fallback_policy": "hold_last_action",
        },
        "image": {"image_size": 224},
        "topics": {"namespace": "/act"},
        "safety": {},
    }
    path.write_text(yaml.safe_dump(payload))


# ---------------------------------------------------------------------------
# check_bundle_contract
# ---------------------------------------------------------------------------


class TestCheckBundleContract:
    def test_passes_when_complete(self, tmp_path: Path) -> None:
        bundle = _make_bundle(tmp_path)
        manifest = json.loads((bundle / "manifest.json").read_text())
        result = check_bundle_contract(bundle, manifest)
        assert isinstance(result, BundleContractResult)
        assert result.is_pass is True
        assert result.missing_files == ()

    def test_fails_when_checkpoint_missing(self, tmp_path: Path) -> None:
        bundle = _make_bundle(tmp_path)
        (bundle / "checkpoint.pt").unlink()
        manifest = json.loads((bundle / "manifest.json").read_text())
        # Manifest still references the deleted checkpoint
        (bundle / "manifest.json").write_text(json.dumps({
            "schema_version": 1,
            "model": {"pretrained_path": "checkpoint.pt", "state_dim": 16, "action_dim": 16, "chunk_size": 30},
        }))
        manifest2 = json.loads((bundle / "manifest.json").read_text())
        result = check_bundle_contract(bundle, manifest2)
        assert result.is_pass is False
        assert "checkpoint" in result.missing_files or any("checkpoint" in f for f in result.missing_files) or result.passed is False

    def test_fails_when_adapter_missing(self, tmp_path: Path) -> None:
        bundle = _make_bundle(tmp_path)
        import shutil
        shutil.rmtree(bundle / "adapter")
        manifest = json.loads((bundle / "manifest.json").read_text())
        result = check_bundle_contract(bundle, manifest)
        assert result.is_pass is False
        assert "adapter" in result.missing_files


# ---------------------------------------------------------------------------
# check_normalizer_contract
# ---------------------------------------------------------------------------


class TestCheckNormalizerContract:
    def test_passes_at_dim_16(self) -> None:
        sn = ActionStateNormalizer(min_vals=[0] * 16, max_vals=[1] * 16)
        an = ActionStateNormalizer(min_vals=[-1] * 16, max_vals=[1] * 16)
        result = check_normalizer_contract(sn, an)
        assert isinstance(result, NormalizerContractResult)
        assert result.is_pass is True
        assert result.expected_dim == 16

    def test_fails_on_state_dim_mismatch(self) -> None:
        sn = ActionStateNormalizer(min_vals=[0] * 8, max_vals=[1] * 8)
        an = ActionStateNormalizer(min_vals=[-1] * 16, max_vals=[1] * 16)
        result = check_normalizer_contract(sn, an)
        assert result.is_pass is False
        assert "State normalizer" in result.reason

    def test_fails_on_action_dim_mismatch(self) -> None:
        sn = ActionStateNormalizer(min_vals=[0] * 16, max_vals=[1] * 16)
        an = ActionStateNormalizer(min_vals=[-1] * 8, max_vals=[1] * 8)
        result = check_normalizer_contract(sn, an)
        assert result.is_pass is False
        assert "Action normalizer" in result.reason

    def test_fails_on_both_dim_mismatch(self) -> None:
        sn = ActionStateNormalizer(min_vals=[0] * 14, max_vals=[1] * 14)
        an = ActionStateNormalizer(min_vals=[-1] * 14, max_vals=[1] * 14)
        result = check_normalizer_contract(sn, an)
        assert result.is_pass is False
        assert result.actual_dim == 14


# ---------------------------------------------------------------------------
# load_deploy_config end-to-end
# ---------------------------------------------------------------------------


class TestLoadDeployConfigEndToEnd:
    def test_pass_with_valid_bundle(self, tmp_path: Path) -> None:
        bundle = _make_bundle(tmp_path)
        yaml_path = tmp_path / "deploy.yaml"
        _write_deploy_yaml(yaml_path, str(bundle))
        cfg = load_deploy_config(yaml_path)
        assert isinstance(cfg, DeployConfig)
        assert cfg.runtime.state_dim == 16

    def test_raises_when_bundle_incomplete(self, tmp_path: Path) -> None:
        bundle = _make_bundle(tmp_path)
        (bundle / "normalizers.json").unlink()
        yaml_path = tmp_path / "deploy.yaml"
        _write_deploy_yaml(yaml_path, str(bundle))
        with pytest.raises(DeployConfigError):
            load_deploy_config(yaml_path)

    def test_raises_when_dim_mismatch(self, tmp_path: Path) -> None:
        bundle = _make_bundle(tmp_path, state_dim=14, action_dim=14)
        yaml_path = tmp_path / "deploy.yaml"
        _write_deploy_yaml(yaml_path, str(bundle))
        with pytest.raises(DeployConfigError):
            load_deploy_config(yaml_path)

    def test_root_not_mapping_raises(self, tmp_path: Path) -> None:
        bad = tmp_path / "bad.yaml"
        bad.write_text("- not a mapping\n")
        with pytest.raises(DeployConfigError, match="must be a mapping"):
            load_deploy_config(bad)

    def test_bundle_dir_not_set_skips_checks(self, tmp_path: Path) -> None:
        """When bundle_dir is null, contract checks are skipped."""
        yaml_path = tmp_path / "deploy.yaml"
        _write_deploy_yaml(yaml_path, "null")
        cfg = load_deploy_config(yaml_path)
        assert isinstance(cfg, DeployConfig)
