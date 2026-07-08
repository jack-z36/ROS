"""Tests for experiment_config_loader.py — deploy_006."""

from pathlib import Path

import pytest
import yaml

from model_deploy.act.repo.experiment_config_loader import (
    EXPERIMENT_CONFIG_NAME,
    ExperimentConfigLoadError,
    load_experiment_config,
)


def _write_yaml(path: Path, payload: dict) -> None:
    with path.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(payload, fh)


class TestLoadExperimentConfig:
    def test_normal_load(self, tmp_path: Path) -> None:
        cfg_path = tmp_path / EXPERIMENT_CONFIG_NAME
        payload = {"state_dim": 16, "action_dim": 16, "chunk_size": 100}
        _write_yaml(cfg_path, payload)
        result = load_experiment_config(cfg_path)
        assert result == payload
        assert result["state_dim"] == 16
        assert result["action_dim"] == 16

    def test_missing_file_raises(self, tmp_path: Path) -> None:
        missing = tmp_path / "nonexistent.yaml"
        with pytest.raises(ExperimentConfigLoadError, match="not found"):
            load_experiment_config(missing)

    def test_bad_yaml_raises(self, tmp_path: Path) -> None:
        cfg_path = tmp_path / EXPERIMENT_CONFIG_NAME
        cfg_path.write_text(": bad yaml :::")
        with pytest.raises(ExperimentConfigLoadError, match="Failed to parse"):
            load_experiment_config(cfg_path)

    def test_root_not_mapping_raises(self, tmp_path: Path) -> None:
        cfg_path = tmp_path / EXPERIMENT_CONFIG_NAME
        _write_yaml(cfg_path, [1, 2, 3])  # type: ignore[arg-type]
        with pytest.raises(ExperimentConfigLoadError, match="must be a mapping"):
            load_experiment_config(cfg_path)

    def test_scalar_root_raises(self, tmp_path: Path) -> None:
        cfg_path = tmp_path / EXPERIMENT_CONFIG_NAME
        cfg_path.write_text("42\n")
        with pytest.raises(ExperimentConfigLoadError, match="must be a mapping"):
            load_experiment_config(cfg_path)

    def test_dimension_fields_preserved(self, tmp_path: Path) -> None:
        cfg_path = tmp_path / EXPERIMENT_CONFIG_NAME
        payload = {"state_dim": 16, "action_dim": 16, "extra": {"nested": True}}
        _write_yaml(cfg_path, payload)
        result = load_experiment_config(cfg_path)
        assert result["state_dim"] == 16
        assert result["extra"]["nested"] is True

    def test_missing_field_not_filled(self, tmp_path: Path) -> None:
        cfg_path = tmp_path / EXPERIMENT_CONFIG_NAME
        _write_yaml(cfg_path, {"chunk_size": 100})
        result = load_experiment_config(cfg_path)
        assert "state_dim" not in result
        assert "action_dim" not in result
        assert result["chunk_size"] == 100
