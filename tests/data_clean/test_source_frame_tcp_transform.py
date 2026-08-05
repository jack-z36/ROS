from __future__ import annotations

import math
from pathlib import Path
import shutil

import pytest
import yaml

from repo.config.mcap_process_config import load_app_config
from runtime.production_config import (
    production_readiness,
    save_production_config,
    validate_production_payload,
)
from runtime.scene3_full_flow_check import _ensure_default_target_fields
from schemas.alignment_config import Scene3AlignmentConfig
from service.tcp_transform import compute_tcp_pose_in_source_frame


REPO_ROOT = Path(__file__).resolve().parents[2]
PRODUCTION_CONFIG = REPO_ROOT / "config/data_clean/data_clean_calibrated.yaml"


def test_camera_to_tcp_translation_preserves_source_frame() -> None:
    result = compute_tcp_pose_in_source_frame(
        1.0,
        2.0,
        3.0,
        0.0,
        0.0,
        0.0,
        1.0,
        translation_m=(0.1, -0.2, 0.3),
        rotation_quat_xyzw=(0.0, 0.0, 0.0, 1.0),
    )

    assert result == pytest.approx((1.1, 1.8, 3.3, 0.0, 0.0, 0.0, 1.0))


def test_camera_rotation_rotates_tcp_offset_without_another_frame_transform() -> None:
    half_turn = math.sqrt(0.5)
    result = compute_tcp_pose_in_source_frame(
        1.0,
        2.0,
        3.0,
        0.0,
        0.0,
        half_turn,
        half_turn,
        translation_m=(0.1, 0.0, 0.0),
        rotation_quat_xyzw=(0.0, 0.0, 0.0, 1.0),
    )

    assert result[:3] == pytest.approx((1.0, 2.1, 3.0), abs=1e-12)
    assert result[3:] == pytest.approx((0.0, 0.0, half_turn, half_turn))


def test_dynamic_camera_motion_remains_dynamic_after_single_transform() -> None:
    first = compute_tcp_pose_in_source_frame(
        0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0,
        translation_m=(0.0, 0.0, 0.145),
        rotation_quat_xyzw=(0.0, 0.0, 0.0, 1.0),
    )
    second = compute_tcp_pose_in_source_frame(
        0.25, -0.1, 0.05, 0.0, 0.0, 0.0, 1.0,
        translation_m=(0.0, 0.0, 0.145),
        rotation_quat_xyzw=(0.0, 0.0, 0.0, 1.0),
    )

    assert tuple(second[index] - first[index] for index in range(3)) == pytest.approx(
        (0.25, -0.1, 0.05)
    )


def test_production_config_requires_only_camera_to_tcp_pose_configuration() -> None:
    config = load_app_config(PRODUCTION_CONFIG)

    assert not hasattr(config, "work_frames")
    assert {stream.output_tcp_pose for stream in config.pose_streams} == {
        "/baton_mini_left/tcp_pose",
        "/baton_mini_right/tcp_pose",
    }
    assert production_readiness(PRODUCTION_CONFIG)["ready"] is True

    payload_result = validate_production_payload(
        {
            "camera_from_tcp": {
                "left": {"translation_mm": [0.0, 0.0, 145.0]},
                "right": {"translation_mm": [0.0, 0.0, 145.0]},
            }
        }
    )
    assert payload_result == {"valid": True, "errors": []}


def test_formal_scene3_consumes_source_frame_tcp_topics() -> None:
    config = _ensure_default_target_fields(Scene3AlignmentConfig(pose_source_profile="formal"))
    fields = {field.field_name: field.source_topic for field in config.target_fields}

    assert fields["left_tcp_pose"] == "/baton_mini_left/tcp_pose"
    assert fields["right_tcp_pose"] == "/baton_mini_right/tcp_pose"


def test_saving_production_config_removes_legacy_arm_base_requirements(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "production.yaml"
    shutil.copyfile(PRODUCTION_CONFIG, config_path)
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    raw["work_frames"] = {"left": {}, "right": {}}
    for stream in raw["pose_streams"]:
        stream["output_arm_base_tcp_pose"] = "/legacy_arm_base_pose"
        stream.pop("output_tcp_pose", None)
    config_path.write_text(
        yaml.safe_dump(raw, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )

    save_production_config(
        config_path,
        {
            "camera_from_tcp": {
                "left": {"translation_mm": [0.0, 0.0, 145.0]},
                "right": {"translation_mm": [0.0, 0.0, 145.0]},
            }
        },
    )

    saved = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    assert "work_frames" not in saved
    assert all("output_arm_base_tcp_pose" not in stream for stream in saved["pose_streams"])
    assert {stream["output_tcp_pose"] for stream in saved["pose_streams"]} == {
        "/baton_mini_left/tcp_pose",
        "/baton_mini_right/tcp_pose",
    }
