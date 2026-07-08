"""Tests for manifest_parser.py — deploy_004."""

import json
from pathlib import Path

import pytest

from model_deploy.act.repo.manifest_parser import MANIFEST_NAME, load_bundle_manifest


class TestLoadBundleManifest:
    """Tests for load_bundle_manifest."""

    def test_parse_valid_manifest(self, tmp_path: Path) -> None:
        bundle_dir = tmp_path / "bundle"
        bundle_dir.mkdir()
        payload = {
            "schema_version": 1,
            "model": {"state_dim": 16, "action_dim": 16, "chunk_size": 100},
        }
        (bundle_dir / MANIFEST_NAME).write_text(json.dumps(payload))
        result = load_bundle_manifest(bundle_dir)
        assert result == payload
        assert result["schema_version"] == 1
        assert result["model"]["state_dim"] == 16

    def test_missing_file_raises(self, tmp_path: Path) -> None:
        bundle_dir = tmp_path / "empty_bundle"
        bundle_dir.mkdir()
        with pytest.raises(FileNotFoundError):
            load_bundle_manifest(bundle_dir)

    def test_bad_json_raises(self, tmp_path: Path) -> None:
        bundle_dir = tmp_path / "bad_bundle"
        bundle_dir.mkdir()
        (bundle_dir / MANIFEST_NAME).write_text("not valid json {{{")
        with pytest.raises(json.JSONDecodeError):
            load_bundle_manifest(bundle_dir)
