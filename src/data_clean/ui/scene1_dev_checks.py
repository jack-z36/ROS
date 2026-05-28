"""Scene 1 developer checks."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from config.mcap_process_config import (
    AppConfig,
    ExtrinsicConfig,
    FrameAlignmentConfig,
    load_app_config,
    validate_frame_alignment,
)
from runtime import mcap_clean_launcher
from service.gripper_width import GripperExtractionResult, write_gripper_dev_artifacts
from service.tcp_transform import transform_camera_to_common_tcp, transform_pose_to_common_camera_frame
from service.validator import (
    FileProcessingReport,
    GripperTopicStats,
    PoseTopicStats,
    scene1_output_contract_validate,
    write_scene1_contract_report,
    write_scene1_smoke_summary,
)
from ui.mcap_calibration_wizard import (
    GripperSideCalibration,
    Scene1DevRun,
    create_scene1_dev_run,
    write_gripper_calibration_artifacts,
)

WORKSPACE_DIR = Path("/home/hit/ROS")
DEFAULT_CONFIG = WORKSPACE_DIR / "config/data_clean/data_clean_calibrated.yaml"


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)


def _load_config_or_smoke(config_path: str | Path = DEFAULT_CONFIG) -> AppConfig:
    path = Path(config_path)
    if path.exists():
        return load_app_config(path)
    return load_app_config(WORKSPACE_DIR / "config/data_clean/data_clean_smoke_test.yaml")


def _update_run_log(
    dev_run: Scene1DevRun,
    *,
    status: str,
    artifacts: dict[str, str],
    failure_reason: str | None = None,
    extra: dict[str, Any] | None = None,
) -> Scene1DevRun:
    run_log_path = dev_run.log_dir / "run_log.json"
    with run_log_path.open("r", encoding="utf-8") as fh:
        run_log = json.load(fh)

    run_log["status"] = status
    run_log["artifacts"] = artifacts
    if failure_reason:
        run_log["failure_reason"] = failure_reason
    if extra:
        run_log.update(extra)
    run_log["completed_at"] = datetime.now().astimezone().isoformat(timespec="seconds")

    with run_log_path.open("w", encoding="utf-8") as fh:
        json.dump(run_log, fh, ensure_ascii=False, indent=2)

    return Scene1DevRun(
        run_id=dev_run.run_id,
        check_id=dev_run.check_id,
        run_dir=dev_run.run_dir,
        artifact_dir=dev_run.artifact_dir,
        log_dir=dev_run.log_dir,
        config_dir=dev_run.config_dir,
        effective_config=dev_run.effective_config,
        status=status,
    )


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


def run_scene1_common_pose_transform(config_path: str | Path = DEFAULT_CONFIG) -> Scene1DevRun:
    """Run a deterministic common-frame pose transform dev check."""
    dev_run = create_scene1_dev_run("scene1_common_pose_transform")
    config = _load_config_or_smoke(config_path)
    frame_alignment = config.frame_alignment or FrameAlignmentConfig(
        common_anchor="left",
        common_from_left_start=ExtrinsicConfig.identity(),
        common_from_right_start=ExtrinsicConfig.identity(),
        camera_from_left_tcp=ExtrinsicConfig.identity(),
        camera_from_right_tcp=ExtrinsicConfig.identity(),
    )

    raw_samples = [
        {
            "hand": "left",
            "raw_pose": (0.1, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0),
        },
        {
            "hand": "right",
            "raw_pose": (0.2, 0.1, 0.0, 0.0, 0.0, 0.0, 1.0),
        },
    ]
    samples: list[dict[str, Any]] = []
    for item in raw_samples:
        hand = item["hand"]
        raw_pose = item["raw_pose"]
        camera_pose = transform_pose_to_common_camera_frame(*raw_pose, frame_alignment, hand)
        tcp_pose = transform_camera_to_common_tcp(*camera_pose, frame_alignment, hand)
        samples.append({
            "hand": hand,
            "raw_pose": list(raw_pose),
            "camera_pose_common": list(camera_pose),
            "tcp_pose_common": list(tcp_pose),
            "raw_pose_retained": True,
        })

    samples_path = dev_run.artifact_dir / "common_pose_samples.json"
    _write_json(samples_path, {
        "generated_by": "scene1_common_pose_transform",
        "source_config": str(config_path),
        "samples": samples,
    })
    with dev_run.effective_config.open("w", encoding="utf-8") as fh:
        yaml.safe_dump({"frame_alignment": {"common_anchor": frame_alignment.common_anchor}}, fh, allow_unicode=True)

    print()
    print("位姿转换小样本已生成")
    print(f"  样本: {samples_path}")
    print(f"  日志: {dev_run.log_dir / 'run_log.json'}")
    return _update_run_log(
        dev_run,
        status="success",
        artifacts={"common_pose_samples.json": str(samples_path)},
    )


def run_scene1_gripper_width_extract(config_path: str | Path = DEFAULT_CONFIG) -> Scene1DevRun:
    """Generate gripper-width extraction dev artifacts from deterministic samples."""
    dev_run = create_scene1_dev_run("scene1_gripper_width_extract")
    config = _load_config_or_smoke(config_path)

    results = []
    for stream in config.gripper_streams:
        result = GripperExtractionResult(
            values=[0.25, 0.5, 0.75],
            frame_count=3,
            direct_detection_frames=2,
            missing_frames=1,
            interpolated_frames=1,
        )
        results.append((result, stream))

    write_gripper_dev_artifacts(results, dev_run.artifact_dir)
    samples_path = dev_run.artifact_dir / "gripper_width_samples.json"
    stats_path = dev_run.artifact_dir / "gripper_width_stats.json"

    print()
    print("夹爪开合提取小样本已生成")
    print(f"  样本: {samples_path}")
    print(f"  统计: {stats_path}")
    print(f"  日志: {dev_run.log_dir / 'run_log.json'}")
    return _update_run_log(
        dev_run,
        status="success",
        artifacts={
            "gripper_width_samples.json": str(samples_path),
            "gripper_width_stats.json": str(stats_path),
        },
    )


def run_scene1_gripper_calibration_config(config_path: str | Path = DEFAULT_CONFIG) -> Scene1DevRun:
    """Generate temporary GripperCalibrationConfig artifacts from current config."""
    dev_run = create_scene1_dev_run("scene1_gripper_calibration_config")
    config = _load_config_or_smoke(config_path)

    results: list[GripperSideCalibration] = []
    for stream in config.gripper_streams:
        hand = "right" if "right" in stream.image_topic or "right" in stream.output_topic else "left"
        results.append(GripperSideCalibration(
            hand=hand,
            image_topic=stream.image_topic,
            output_topic=stream.output_topic,
            aruco_dict=stream.aruco_dict,
            marker_id_0=stream.marker_id_0,
            marker_id_1=stream.marker_id_1,
            marker_min=stream.marker_min,
            marker_max=stream.marker_max,
            closed_rate=1.0,
            open_rate=1.0,
            closed_std=0.0,
            open_std=0.0,
            closed_frames=3,
            open_frames=3,
        ))

    completed = write_gripper_calibration_artifacts(dev_run, results)
    print()
    print("夹爪开合配置模板已生成")
    print(f"  配置: {dev_run.artifact_dir / 'gripper_calibration_config.yaml'}")
    print(f"  摘要: {dev_run.artifact_dir / 'gripper_calibration_summary.json'}")
    print("  实时重新标定请使用: ./start_data_clean.sh --calibrate")
    return completed


def _representative_report(config: AppConfig) -> FileProcessingReport:
    pose_topics = tuple(
        PoseTopicStats(topic=stream.input_topic, input_count=3, output_count=3)
        for stream in config.pose_streams
    )
    gripper_topics = tuple(
        GripperTopicStats(
            image_topic=stream.image_topic,
            output_topic=stream.output_topic,
            frame_count=3,
            gripper_count=3,
            missing_frames=1,
            interpolated_frames=1,
        )
        for stream in config.gripper_streams
    )
    expected_added = len(config.gripper_streams)
    if config.frame_alignment is not None:
        expected_added += sum(1 for s in config.pose_streams if s.output_camera_pose_common)
        expected_added += sum(1 for s in config.pose_streams if s.output_tcp_pose_common)

    input_topic_count = len(config.pose_streams) + len(config.gripper_streams)
    return FileProcessingReport(
        input_file="scene1_dev_sample_input.mcap",
        output_file="scene1_dev_sample_output.mcap",
        status="success",
        input_topic_count=input_topic_count,
        output_topic_count=input_topic_count + expected_added,
        pose_topics=pose_topics,
        gripper_topics=gripper_topics,
    )


def run_scene1_output_contract_validate(config_path: str | Path = DEFAULT_CONFIG) -> Scene1DevRun:
    """Validate Scene 1 output contract against representative dev stats."""
    dev_run = create_scene1_dev_run("scene1_output_contract_validate")
    config = _load_config_or_smoke(config_path)
    report = _representative_report(config)
    result = scene1_output_contract_validate(report, config)
    report_path = write_scene1_contract_report(result, dev_run.artifact_dir)

    print()
    print("配置/输出契约报告已生成")
    print(f"  报告: {report_path}")
    print(f"  状态: {result.status}")
    if result.failure_reason:
        print(f"  原因: {result.failure_reason}")
    return _update_run_log(
        dev_run,
        status=result.status,
        artifacts={"output_contract_report.json": str(report_path)},
        failure_reason=result.failure_reason,
        extra={"contract_checks": result.run_log.get("checks", [])},
    )


def run_scene1_smoke_test(config_path: str | Path = DEFAULT_CONFIG) -> Scene1DevRun:
    """Run Scene 1 smoke test into an isolated dev directory when input exists."""
    dev_run = create_scene1_dev_run("scene1_smoke_test")
    config = _load_config_or_smoke(config_path)
    files = mcap_clean_launcher._iter_input_files(config)
    if not files:
        report = FileProcessingReport(
            input_file=str(Path(config.batch.input_dir) / config.batch.file_glob),
            output_file=str(dev_run.artifact_dir / "debug_cleaned"),
            status="skipped",
            input_topic_count=0,
            output_topic_count=0,
            pose_topics=tuple(),
            gripper_topics=tuple(),
            failure_reason="no input MCAP files matched config batch.input_dir/file_glob",
        )
        result = scene1_output_contract_validate(report, config)
        summary_path = write_scene1_smoke_summary(report, result, dev_run.artifact_dir)
        print()
        print("全场景测试已跳过: 未找到输入 MCAP")
        print(f"  摘要: {summary_path}")
        print(f"  输入目录: {config.batch.input_dir}")
        return _update_run_log(
            dev_run,
            status="skipped",
            artifacts={"smoke_summary.json": str(summary_path)},
            failure_reason=report.failure_reason,
        )

    output_dir = dev_run.artifact_dir / "debug_cleaned"
    exit_code = mcap_clean_launcher.main([
        "--config",
        str(config_path),
        "--latest",
        "1",
        "--workers",
        "1",
        "--output-dir",
        str(output_dir),
    ])
    status = "success" if exit_code == 0 else "failed"
    summary_path = dev_run.artifact_dir / "smoke_summary.json"
    _write_json(summary_path, {
        "status": status,
        "exit_code": exit_code,
        "input_count": len(files),
        "output_dir": str(output_dir),
    })
    print()
    print("全场景测试已运行")
    print(f"  状态: {status}")
    print(f"  摘要: {summary_path}")
    return _update_run_log(
        dev_run,
        status=status,
        artifacts={"smoke_summary.json": str(summary_path)},
        failure_reason=None if status == "success" else f"launcher exit code {exit_code}",
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
