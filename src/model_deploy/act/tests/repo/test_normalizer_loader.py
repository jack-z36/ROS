"""Tests for normalizer_loader.py — deploy_005."""

import json
from pathlib import Path

import pytest

from model_deploy.act.repo.normalizer_loader import NORMALIZERS_NAME, load_bundle_normalizers


def _valid_payload() -> dict:
    return {
        "state": {"min": [0.0] * 16, "max": [1.0] * 16, "identity_indices": []},
        "action": {"min": [-1.0] * 16, "max": [1.0] * 16, "identity_indices": []},
    }


class TestLoadBundleNormalizers:
    def test_normal_roundtrip(self, tmp_path: Path) -> None:
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        payload = _valid_payload()
        (bundle / NORMALIZERS_NAME).write_text(json.dumps(payload))
        s, a = load_bundle_normalizers(bundle)
        assert s.vector_dim == 16
        assert a.vector_dim == 16

    def test_missing_file_raises(self, tmp_path: Path) -> None:
        empty = tmp_path / "empty"
        empty.mkdir()
        with pytest.raises(FileNotFoundError):
            load_bundle_normalizers(empty)

    def test_bad_json_raises(self, tmp_path: Path) -> None:
        bad = tmp_path / "bad"
        bad.mkdir()
        (bad / NORMALIZERS_NAME).write_text("garbage")
        with pytest.raises(json.JSONDecodeError):
            load_bundle_normalizers(bad)

    def test_missing_state_key_raises(self, tmp_path: Path) -> None:
        bad = tmp_path / "bad"
        bad.mkdir()
        (bad / NORMALIZERS_NAME).write_text(json.dumps({"action": {"min": [0], "max": [1]}}))
        with pytest.raises(KeyError):
            load_bundle_normalizers(bad)

    def test_missing_action_key_raises(self, tmp_path: Path) -> None:
        bad = tmp_path / "bad"
        bad.mkdir()
        (bad / NORMALIZERS_NAME).write_text(json.dumps({"state": {"min": [0], "max": [1]}}))
        with pytest.raises(KeyError):
            load_bundle_normalizers(bad)

    def test_numpy_values_restored(self, tmp_path: Path) -> None:
        bundle = tmp_path / "bundle"
        bundle.mkdir()
        payload = _valid_payload()
        (bundle / NORMALIZERS_NAME).write_text(json.dumps(payload))
        s, a = load_bundle_normalizers(bundle)
        import numpy as np
        np.testing.assert_allclose(s.min_vals, np.zeros(16), atol=1e-6)
        np.testing.assert_allclose(s.max_vals, np.ones(16), atol=1e-6)
