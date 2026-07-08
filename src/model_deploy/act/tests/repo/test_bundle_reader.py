"""Tests for bundle_reader.py — deploy_007."""

import json
from pathlib import Path

import pytest

from model_deploy.act.repo.bundle_reader import (
    BUNDLE_SCHEMA_VERSION,
    BundleStructureError,
    check_bundle_files,
    resolve_bundle_adapter_dir,
    resolve_checkpoint_path,
)


def _make_bundle(base: Path, *, missing: set[str] | None = None) -> Path:
    bundle = base / "bundle"
    bundle.mkdir()
    required = {"manifest.json", "normalizers.json", "experiment_config.yaml", "adapter"}
    missing = missing or set()
    for name in required - missing:
        target = bundle / name
        if name == "adapter":
            target.mkdir()
        else:
            target.write_text("{}" if name.endswith(".json") else "key: value\n")
    return bundle


class TestCheckBundleFiles:
    def test_complete_bundle(self, tmp_path: Path) -> None:
        bundle = _make_bundle(tmp_path)
        assert check_bundle_files(bundle) == []

    def test_missing_manifest(self, tmp_path: Path) -> None:
        bundle = _make_bundle(tmp_path, missing={"manifest.json"})
        missing = check_bundle_files(bundle)
        assert "manifest.json" in missing

    def test_missing_normalizers(self, tmp_path: Path) -> None:
        bundle = _make_bundle(tmp_path, missing={"normalizers.json"})
        missing = check_bundle_files(bundle)
        assert "normalizers.json" in missing

    def test_missing_experiment_config(self, tmp_path: Path) -> None:
        bundle = _make_bundle(tmp_path, missing={"experiment_config.yaml"})
        missing = check_bundle_files(bundle)
        assert "experiment_config.yaml" in missing

    def test_missing_adapter(self, tmp_path: Path) -> None:
        bundle = _make_bundle(tmp_path, missing={"adapter"})
        missing = check_bundle_files(bundle)
        assert "adapter" in missing

    def test_missing_multiple(self, tmp_path: Path) -> None:
        bundle = _make_bundle(tmp_path, missing={"manifest.json", "adapter"})
        missing = check_bundle_files(bundle)
        assert len(missing) == 2
        assert "manifest.json" in missing
        assert "adapter" in missing

    def test_bundle_dir_not_exist_raises(self, tmp_path: Path) -> None:
        with pytest.raises(BundleStructureError, match="does not exist"):
            check_bundle_files(tmp_path / "nonexistent")


class TestResolveAdapterDir:
    def test_exists(self, tmp_path: Path) -> None:
        bundle = _make_bundle(tmp_path)
        result = resolve_bundle_adapter_dir(bundle)
        assert result.is_dir()
        assert result.name == "adapter"

    def test_not_exists_raises(self, tmp_path: Path) -> None:
        bundle = _make_bundle(tmp_path, missing={"adapter"})
        with pytest.raises(FileNotFoundError, match="does not exist"):
            resolve_bundle_adapter_dir(bundle)


class TestResolveCheckpointPath:
    def test_from_manifest_pretrained_path(self, tmp_path: Path) -> None:
        bundle = _make_bundle(tmp_path)
        ckpt = bundle / "checkpoint.pt"
        ckpt.write_text("dummy")
        manifest = json.loads((bundle / "manifest.json").read_text())
        manifest["model"] = {"pretrained_path": "checkpoint.pt"}
        (bundle / "manifest.json").write_text(json.dumps(manifest))
        result = resolve_checkpoint_path(bundle)
        assert result == ckpt.resolve()

    def test_fallback_directory_scan_pt(self, tmp_path: Path) -> None:
        bundle = _make_bundle(tmp_path)
        ckpt = bundle / "weights.pt"
        ckpt.write_text("dummy")
        result = resolve_checkpoint_path(bundle)
        assert result == ckpt.resolve()

    def test_fallback_directory_scan_safetensors(self, tmp_path: Path) -> None:
        bundle = _make_bundle(tmp_path)
        ckpt = bundle / "model.safetensors"
        ckpt.write_text("dummy")
        result = resolve_checkpoint_path(bundle)
        assert result == ckpt.resolve()

    def test_fallback_checkpoint_dir(self, tmp_path: Path) -> None:
        bundle = _make_bundle(tmp_path)
        ckpt_dir = bundle / "checkpoint"
        ckpt_dir.mkdir()
        result = resolve_checkpoint_path(bundle)
        assert result == ckpt_dir.resolve()

    def test_no_checkpoint_raises(self, tmp_path: Path) -> None:
        bundle = _make_bundle(tmp_path)
        with pytest.raises(BundleStructureError, match="Cannot resolve checkpoint"):
            resolve_checkpoint_path(bundle)


class TestConstants:
    def test_bundle_schema_version(self) -> None:
        assert BUNDLE_SCHEMA_VERSION == 1
