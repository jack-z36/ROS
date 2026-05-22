"""Scene 1 dev check: frame_alignment config generation."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import yaml

from config.mcap_process_config import (
    AppConfig,
    ExtrinsicConfig,
    FrameAlignmentConfig,
    load_app_config,
    validate_frame_alignment,
)
from ui.mcap_calibration_wizard import (
    Scene1DevRun,
    create_scene1_dev_run,
)

WORKSPACE_DIR = Path("/home/hit/ROS")
DEFAULT_CONFIG = WORKSPACE_DIR / "config/data_clean/data_clean_calibrated.yaml"


def _extrinsic_to_dict(ext: ExtrinsicConfig) -> dict:
    return {
        "translation_m": list(ext.translation_m),
        "rotation_quat_xyzw": list(ext.rotation_quat_xyzw),
    }


def run_scene1_frame_alignment_config(
    config_path: str | Path = DEFAULT_CONFIG,
    *,
    common_from_right_start_override: ExtrinsicConfig | None = None,
    camera_from_left_tcp_override: ExtrinsicConfig | None = None,
    camera_from_right_tcp_override: ExtrinsicConfig | None = None,
) -> Scene1DevRun:
    """Generate frame_alignment config via dev check.

    When overrides are provided, they replace the corresponding fields.
    When no overrides are given, a default config with identity right_start
    and placeholder camera_from_tcp is generated for inspection.
    """
    dev_run = create_scene1_dev_run("scene1_frame_alignment_config")

    config_path = Path(config_path)
    config: AppConfig | None = None
    if config_path.exists():
        try:
            config = load_app_config(config_path)
        except Exception:
            config = None

    common_from_right = common_from_right_start_override or ExtrinsicConfig.identity()
    camera_left_tcp = camera_from_left_tcp_override or ExtrinsicConfig.identity()
    camera_right_tcp = camera_from_right_tcp_override or ExtrinsicConfig.identity()

    frame_alignment = FrameAlignmentConfig(
        common_anchor="left",
        common_from_left_start=ExtrinsicConfig.identity(),
        common_from_right_start=common_from_right,
        camera_from_left_tcp=camera_left_tcp,
        camera_from_right_tcp=camera_right_tcp,
    )
    validate_frame_alignment(frame_alignment)

    config_data = {
        "frame_alignment": {
            "common_anchor": "left",
            "pose_streams": {
                "left": {
                    "input_topic": "/baton_mini_left/fast_odom",
                    "output_camera_pose_common": "/baton_mini_left/camera_pose_common",
                    "output_tcp_pose_common": "/baton_mini_left/tcp_pose_common",
                },
                "right": {
                    "input_topic": "/baton_mini_right/fast_odom",
                    "output_camera_pose_common": "/baton_mini_right/camera_pose_common",
                    "output_tcp_pose_common": "/baton_mini_right/tcp_pose_common",
                },
            },
            "extrinsics": {
                "common_from_left_start": _extrinsic_to_dict(frame_alignment.common_from_left_start),
                "common_from_right_start": _extrinsic_to_dict(frame_alignment.common_from_right_start),
                "camera_from_left_tcp": _extrinsic_to_dict(frame_alignment.camera_from_left_tcp),
                "camera_from_right_tcp": _extrinsic_to_dict(frame_alignment.camera_from_right_tcp),
            },
        },
    }

    config_path_out = dev_run.artifact_dir / "frame_alignment_config.yaml"
    with config_path_out.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(config_data, fh, allow_unicode=True, sort_keys=False)

    summary = {
        "generated_by": "scene1_frame_alignment_config",
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "common_anchor": "left",
        "common_from_left_start": _extrinsic_to_dict(frame_alignment.common_from_left_start),
        "common_from_right_start": _extrinsic_to_dict(frame_alignment.common_from_right_start),
        "camera_from_left_tcp": _extrinsic_to_dict(frame_alignment.camera_from_left_tcp),
        "camera_from_right_tcp": _extrinsic_to_dict(frame_alignment.camera_from_right_tcp),
        "source_config": str(config_path) if config_path.exists() else "none",
        "validation": "passed",
    }

    summary_path = dev_run.artifact_dir / "frame_alignment_summary.json"
    with summary_path.open("w", encoding="utf-8") as fh:
        json.dump(summary, fh, ensure_ascii=False, indent=2)

    run_log_path = dev_run.log_dir / "run_log.json"
    with run_log_path.open("r", encoding="utf-8") as fh:
        run_log = json.load(fh)

    run_log["status"] = "success"
    run_log["artifacts"] = {
        "frame_alignment_config.yaml": str(config_path_out),
        "frame_alignment_summary.json": str(summary_path),
    }
    run_log["completed_at"] = datetime.now().astimezone().isoformat(timespec="seconds")

    with run_log_path.open("w", encoding="utf-8") as fh:
        json.dump(run_log, fh, ensure_ascii=False, indent=2)

    effective_config = dev_run.config_dir / "effective_config.yaml"
    with effective_config.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(config_data, fh, allow_unicode=True, sort_keys=False)

    print()
    print("frame_alignment 配置已生成")
    print(f"  配置: {config_path_out}")
    print(f"  摘要: {summary_path}")
    print(f"  日志: {run_log_path}")
    print()
    print("外参摘要:")
    print(f"  common_anchor: left")
    print(f"  common_from_left_start: identity")
    print(f"  common_from_right_start: t={frame_alignment.common_from_right_start.translation_m}, q={frame_alignment.common_from_right_start.rotation_quat_xyzw}")
    print(f"  camera_from_left_tcp: t={frame_alignment.camera_from_left_tcp.translation_m}, q={frame_alignment.camera_from_left_tcp.rotation_quat_xyzw}")
    print(f"  camera_from_right_tcp: t={frame_alignment.camera_from_right_tcp.translation_m}, q={frame_alignment.camera_from_right_tcp.rotation_quat_xyzw}")

    return Scene1DevRun(
        run_id=dev_run.run_id,
        check_id=dev_run.check_id,
        run_dir=dev_run.run_dir,
        artifact_dir=dev_run.artifact_dir,
        log_dir=dev_run.log_dir,
        config_dir=dev_run.config_dir,
        effective_config=dev_run.effective_config,
        status="success",
    )


def save_frame_alignment_to_production(
    dev_run: Scene1DevRun,
    output_path: str | Path = DEFAULT_CONFIG,
) -> AppConfig:
    """Save the generated frame_alignment config to production."""
    config_path = dev_run.artifact_dir / "frame_alignment_config.yaml"
    if not config_path.exists():
        raise RuntimeError(f"找不到临时配置: {config_path}")

    with config_path.open("r", encoding="utf-8") as fh:
        fa_data = yaml.safe_load(fh)

    output_path = Path(output_path)
    config = load_app_config(output_path) if output_path.exists() else None

    if config is None:
        raise RuntimeError(f"找不到生产配置: {output_path}")

    data = {
        "batch": {
            "input_dir": config.batch.input_dir,
            "output_dir": config.batch.output_dir,
            "file_glob": config.batch.file_glob,
            "workers": config.batch.workers,
            "overwrite": config.batch.overwrite,
            "fail_fast": config.batch.fail_fast,
        },
        "transform": {
            "start_from_common": {
                "translation": {
                    "x": config.transform.translation.x,
                    "y": config.transform.translation.y,
                    "z": config.transform.translation.z,
                },
                "rotation_xyzw": {
                    "qx": config.transform.rotation_xyzw.qx,
                    "qy": config.transform.rotation_xyzw.qy,
                    "qz": config.transform.rotation_xyzw.qz,
                    "qw": config.transform.rotation_xyzw.qw,
                },
            },
        },
        "pose_streams": [
            {
                "input_topic": s.input_topic,
                "msg_type": s.msg_type,
                "output_topic": s.output_topic,
            }
            for s in config.pose_streams
        ],
        "gripper_streams": [
            {
                "image_topic": s.image_topic,
                "image_msg_type": s.image_msg_type,
                "output_topic": s.output_topic,
                "output_msg_type": s.output_msg_type,
                "aruco_dict": s.aruco_dict,
                "marker_id_0": s.marker_id_0,
                "marker_id_1": s.marker_id_1,
                "marker_min": s.marker_min,
                "marker_max": s.marker_max,
                "gripper_max": s.gripper_max,
            }
            for s in config.gripper_streams
        ],
        "calibration": dict(config.calibration),
        "frame_alignment": fa_data["frame_alignment"],
    }

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = output_path.with_name(f"{output_path.name}.{stamp}.bak")
    if output_path.exists():
        import shutil
        shutil.copy2(output_path, backup)
        print(f"  已备份旧配置: {backup}")

    with output_path.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(data, fh, allow_unicode=True, sort_keys=False)

    print(f"  已写入生产配置: {output_path}")
    return load_app_config(output_path)
