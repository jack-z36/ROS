"""Tests for scene1 dev check item: gripper calibration config."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from ui.mcap_calibration_wizard import (  # noqa: E402
    DEV_RUNS_BASE,
    GripperSideCalibration,
    Scene1DevRun,
    create_scene1_dev_run,
    write_gripper_calibration_artifacts,
)


def _patch_asset_base(tmp_path):
    return patch("ui.mcap_calibration_wizard.DEV_RUNS_BASE", tmp_path)


def _make_mock_gripper_results() -> list[GripperSideCalibration]:
    return [
        GripperSideCalibration(
            hand="left",
            image_topic="/gopro_left/image_raw",
            output_topic="/gripper_width_left",
            aruco_dict="DICT_4X4_50",
            marker_id_0=10,
            marker_id_1=11,
            marker_min=50.0,
            marker_max=120.0,
            closed_rate=0.95,
            open_rate=0.96,
            closed_std=1.2,
            open_std=1.3,
            closed_frames=45,
            open_frames=46,
        ),
        GripperSideCalibration(
            hand="right",
            image_topic="/gopro_right/image_raw",
            output_topic="/gripper_width_right",
            aruco_dict="DICT_4X4_50",
            marker_id_0=20,
            marker_id_1=21,
            marker_min=55.0,
            marker_max=125.0,
            closed_rate=0.94,
            open_rate=0.97,
            closed_std=1.1,
            open_std=1.4,
            closed_frames=44,
            open_frames=47,
        ),
    ]


class TestCreateScene1DevRun:
    """Test dev run directory creation and run_log.json initial state."""

    def test_creates_dev_run_directory_structure(self, tmp_path):
        """Dev run should create artifacts/, logs/, config/ subdirectories."""
        with _patch_asset_base(tmp_path):
            run = create_scene1_dev_run("scene1_gripper_calibration_config")

        assert run.run_dir.exists()
        assert run.artifact_dir.exists()
        assert run.log_dir.exists()
        assert (run.log_dir / "run_log.json").exists()
        assert (run.config_dir / "effective_config.yaml").exists()

    def test_run_log_initial_status_is_ready(self, tmp_path):
        """Initial run_log.json should have status 'ready'."""
        with _patch_asset_base(tmp_path):
            run = create_scene1_dev_run("scene1_gripper_calibration_config")

        log_path = run.log_dir / "run_log.json"
        with log_path.open("r") as fh:
            log_data = json.load(fh)

        assert log_data["status"] == "ready"
        assert log_data["check_id"] == "scene1_gripper_calibration_config"
        assert "run_id" in log_data
        assert "run_dir" in log_data
        assert "artifact_dir" in log_data
        assert "log_dir" in log_data
        assert "effective_config" in log_data

    def test_run_id_contains_timestamp(self, tmp_path):
        """Run ID should contain a timestamp for uniqueness."""
        with _patch_asset_base(tmp_path):
            run = create_scene1_dev_run("scene1_gripper_calibration_config")

        assert "scene1_gripper_calibration_config" in run.run_id


class TestWriteGripperCalibrationArtifacts:
    """Test writing gripper calibration artifacts to dev run directory."""

    def test_writes_calibration_config_yaml(self, tmp_path):
        """Should write gripper_calibration_config.yaml to artifacts/."""
        with _patch_asset_base(tmp_path):
            run = create_scene1_dev_run("scene1_gripper_calibration_config")
            results = _make_mock_gripper_results()
            write_gripper_calibration_artifacts(run, results)

        config_path = run.artifact_dir / "gripper_calibration_config.yaml"
        assert config_path.exists()

    def test_writes_calibration_summary_json(self, tmp_path):
        """Should write gripper_calibration_summary.json to artifacts/."""
        with _patch_asset_base(tmp_path):
            run = create_scene1_dev_run("scene1_gripper_calibration_config")
            results = _make_mock_gripper_results()
            write_gripper_calibration_artifacts(run, results)

        summary_path = run.artifact_dir / "gripper_calibration_summary.json"
        assert summary_path.exists()
        with summary_path.open("r") as fh:
            summary = json.load(fh)
        assert "left" in summary
        assert "right" in summary
        assert summary["left"]["marker_min"] == 50.0
        assert summary["left"]["marker_max"] == 120.0

    def test_updates_run_log_status_to_success(self, tmp_path):
        """Should update run_log.json status to 'success'."""
        with _patch_asset_base(tmp_path):
            run = create_scene1_dev_run("scene1_gripper_calibration_config")
            results = _make_mock_gripper_results()
            write_gripper_calibration_artifacts(run, results)

        log_path = run.log_dir / "run_log.json"
        with log_path.open("r") as fh:
            log_data = json.load(fh)
        assert log_data["status"] == "success"

    def test_writes_updated_run_log(self, tmp_path):
        """Should write updated run_log.json with artifact paths."""
        with _patch_asset_base(tmp_path):
            run = create_scene1_dev_run("scene1_gripper_calibration_config")
            results = _make_mock_gripper_results()
            write_gripper_calibration_artifacts(run, results)

        log_path = run.log_dir / "run_log.json"
        with log_path.open("r") as fh:
            log_data = json.load(fh)
        assert "artifacts" in log_data
        assert "gripper_calibration_config.yaml" in log_data["artifacts"]
        assert "gripper_calibration_summary.json" in log_data["artifacts"]


class TestSaveGripperCalibrationToProduction:
    """Test saving gripper calibration config to production."""

    def test_does_not_write_production_config_by_default(self, tmp_path):
        """Should not modify production config without explicit save."""
        prod_config = tmp_path / "data_clean_calibrated.yaml"
        prod_config.write_text("batch: {}\ntransform: {}\npose_streams: []\ngripper_streams: []\n")

        with _patch_asset_base(tmp_path):
            run = create_scene1_dev_run("scene1_gripper_calibration_config")
            results = _make_mock_gripper_results()
            write_gripper_calibration_artifacts(run, results)

        original_content = prod_config.read_text()
        assert "gripper_calibration" not in original_content

    def test_writes_production_config_when_explicitly_saved(self, tmp_path):
        """Should write to production config when save_to_production is True."""
        from ui.mcap_calibration_wizard import save_gripper_calibration_to_production

        prod_config = tmp_path / "data_clean_calibrated.yaml"
        base_config = {
            "batch": {"input_dir": "mcap", "output_dir": "mcap_cleaned"},
            "transform": {"start_from_common": {"translation": {"x": 0, "y": 0, "z": 0}, "rotation_xyzw": {"qx": 0, "qy": 0, "qz": 0, "qw": 1}}},
            "pose_streams": [
                {
                    "input_topic": "/baton_mini_left/odom",
                    "msg_type": "nav_msgs/msg/Odometry",
                    "output_topic": "/baton_mini_left/odom_common",
                    "transform": {"start_from_common": {"translation": {"x": 0, "y": 0, "z": 0}, "rotation_xyzw": {"qx": 0, "qy": 0, "qz": 0, "qw": 1}}},
                },
                {
                    "input_topic": "/baton_mini_right/odom",
                    "msg_type": "nav_msgs/msg/Odometry",
                    "output_topic": "/baton_mini_right/odom_common",
                    "transform": {"start_from_common": {"translation": {"x": 0, "y": 0, "z": 0}, "rotation_xyzw": {"qx": 0, "qy": 0, "qz": 0, "qw": 1}}},
                },
            ],
            "gripper_streams": [
                {
                    "image_topic": "/gopro_left/image_raw",
                    "image_msg_type": "sensor_msgs/msg/Image",
                    "output_topic": "/gripper_width_left",
                    "output_msg_type": "std_msgs/msg/Float32",
                    "aruco_dict": "DICT_4X4_50",
                    "marker_id_0": 0,
                    "marker_id_1": 1,
                    "marker_min": 0.0,
                    "marker_max": 1.0,
                    "gripper_max": 100.0,
                },
                {
                    "image_topic": "/gopro_right/image_raw",
                    "image_msg_type": "sensor_msgs/msg/Image",
                    "output_topic": "/gripper_width_right",
                    "output_msg_type": "std_msgs/msg/Float32",
                    "aruco_dict": "DICT_4X4_50",
                    "marker_id_0": 0,
                    "marker_id_1": 1,
                    "marker_min": 0.0,
                    "marker_max": 1.0,
                    "gripper_max": 100.0,
                },
            ],
        }
        import yaml
        with prod_config.open("w") as fh:
            yaml.safe_dump(base_config, fh)

        results = _make_mock_gripper_results()
        save_gripper_calibration_to_production(prod_config, results)

        with prod_config.open("r") as fh:
            updated = yaml.safe_load(fh)

        assert "calibration" in updated
        assert updated["calibration"]["gripper"]["left"]["calibrated"] is True
        assert updated["calibration"]["gripper"]["right"]["calibrated"] is True
