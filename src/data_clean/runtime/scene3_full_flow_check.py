"""Runtime wrapper for the Scene 3 full-flow developer check."""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass, replace
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from typing import Any

from mcap.reader import make_reader

from repo.ros2_codec import (
    Ros2DynamicCodec,
    extract_pose_fields,
    select_alignment_timestamp,
)
from schemas.alignment_config import (
    AlignmentModality,
    AlignmentSide,
    Scene3AlignmentConfig,
    TargetFieldMapping,
)

from .run_directory_creator import create_run_directory
from .scene3_aligned_mcap_write_check import run_scene3_aligned_mcap_write_check
from .scene3_alignment_report_check import run_scene3_alignment_report_check
from .scene3_field_alignment_check import run_scene3_field_alignment_check
from .scene3_mcap_a_input_check import run_scene3_mcap_a_input_check
from .scene3_step_timeline_check import run_scene3_step_timeline_check


def _jsonable(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return _jsonable(asdict(value))
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    return value


def _stage_failed(result: dict[str, Any]) -> bool:
    return result.get("status") != "success"


def _output_path(result: dict[str, Any], key: str) -> Path | None:
    value = result.get("outputs", {}).get(key)
    return Path(value) if value else None


def _count_mcap_messages(mcap_path: str | Path) -> int:
    count = 0
    with Path(mcap_path).open("rb") as fh:
        reader = make_reader(fh)
        for _schema, _channel, _message in reader.iter_messages(
            log_time_order=False
        ):
            count += 1
    return count


def _ensure_default_target_fields(
    config: Scene3AlignmentConfig,
) -> Scene3AlignmentConfig:
    if config.target_fields:
        return config

    field_names = list(config.required_timeline_fields)
    if len(field_names) != len(config.baseline_image_topics):
        field_names = [
            f"image_{index + 1}"
            for index, _topic in enumerate(config.baseline_image_topics)
        ]

    default_fields: list[TargetFieldMapping] = []
    for index, (field_name, topic) in enumerate(
        zip(field_names, config.baseline_image_topics, strict=True)
    ):
        side = None
        if index == 0:
            side = AlignmentSide.LEFT
        elif index == 1:
            side = AlignmentSide.RIGHT
        default_fields.append(
            TargetFieldMapping(
                field_name=field_name,
                source_topic=topic,
                output_topic=topic,
                message_type="sensor_msgs/msg/Image",
                modality=AlignmentModality.IMAGE,
                side=side,
                required_for_timeline=True,
                strategy="nearest_neighbor",
                max_dt_ms=config.image_max_dt_ms,
            )
        )

    if config.pose_source_profile == "formal":
        left_pose_topic = "/baton_mini_left/tcp_pose"
        right_pose_topic = "/baton_mini_right/tcp_pose"
    else:
        left_pose_topic = "/baton_mini_left/tcp_common_pose"
        right_pose_topic = "/baton_mini_right/tcp_common_pose"

    default_fields.extend(
        [
            TargetFieldMapping(
                field_name="left_tcp_pose",
                source_topic=left_pose_topic,
                output_topic="/aligned/left_tcp_pose",
                message_type="nav_msgs/msg/Odometry",
                modality=AlignmentModality.POSE,
                side=AlignmentSide.LEFT,
                required_for_timeline=False,
                strategy=config.pose_strategy,
                max_dt_ms=config.image_max_dt_ms,
            ),
            TargetFieldMapping(
                field_name="right_tcp_pose",
                source_topic=right_pose_topic,
                output_topic="/aligned/right_tcp_pose",
                message_type="nav_msgs/msg/Odometry",
                modality=AlignmentModality.POSE,
                side=AlignmentSide.RIGHT,
                required_for_timeline=False,
                strategy=config.pose_strategy,
                max_dt_ms=config.image_max_dt_ms,
            ),
            TargetFieldMapping(
                field_name="left_gripper_width",
                source_topic="/gopro_left/gripper_width",
                output_topic="/aligned/left_gripper_width",
                message_type="std_msgs/msg/Float32",
                modality=AlignmentModality.GRIPPER,
                side=AlignmentSide.LEFT,
                required_for_timeline=False,
                strategy=config.gripper_strategy,
                max_dt_ms=config.image_max_dt_ms,
            ),
            TargetFieldMapping(
                field_name="right_gripper_width",
                source_topic="/gopro_right/gripper_width",
                output_topic="/aligned/right_gripper_width",
                message_type="std_msgs/msg/Float32",
                modality=AlignmentModality.GRIPPER,
                side=AlignmentSide.RIGHT,
                required_for_timeline=False,
                strategy=config.gripper_strategy,
                max_dt_ms=config.image_max_dt_ms,
            ),
            *_default_tactile_fields(config),
        ]
    )

    return replace(config, target_fields=default_fields)


def _default_tactile_fields(
    config: Scene3AlignmentConfig,
) -> list[TargetFieldMapping]:
    topics = [
        ("tactile_left_gripper_1", "/pressure/left_hand/gripper_1", AlignmentSide.LEFT),
        ("tactile_left_gripper_2", "/pressure/left_hand/gripper_2", AlignmentSide.LEFT),
        ("tactile_right_gripper_1", "/pressure/right_hand/gripper_1", AlignmentSide.RIGHT),
        ("tactile_right_gripper_2", "/pressure/right_hand/gripper_2", AlignmentSide.RIGHT),
    ]
    return [
        TargetFieldMapping(
            field_name=field_name,
            source_topic=source_topic,
            output_topic=f"/aligned/{field_name}",
            message_type="hwk_pressure_interfaces/msg/PressureFrame",
            modality=AlignmentModality.TACTILE,
            side=side,
            required_for_timeline=False,
            strategy=config.tactile_strategy,
        )
        for field_name, source_topic, side in topics
    ]


def _extract_mcap_a_field_samples(
    *,
    mcap_a_path: str | Path,
    field_mappings: list[TargetFieldMapping],
) -> dict[str, list]:
    """Extract MCAP_A samples for configured field alignment.

    Image fields use message refs so the aligned writer can copy the original
    payload and schema. Pose fields are decoded into xyz/quaternion tuples for
    interpolation and later re-encoded as Forge-friendly JointState messages.
    """
    image_topic_to_fields: dict[str, list[str]] = {}
    pose_topic_to_fields: dict[str, list[TargetFieldMapping]] = {}
    gripper_topic_to_fields: dict[str, list[str]] = {}
    tactile_topic_to_fields: dict[str, list[str]] = {}
    samples: dict[str, list] = {}

    for mapping in field_mappings:
        if mapping.modality == AlignmentModality.IMAGE:
            image_topic_to_fields.setdefault(mapping.source_topic, []).append(
                mapping.field_name
            )
            samples.setdefault(mapping.field_name, [])
        elif mapping.modality == AlignmentModality.POSE:
            pose_topic_to_fields.setdefault(mapping.source_topic, []).append(mapping)
            samples.setdefault(mapping.field_name, [])
        elif mapping.modality == AlignmentModality.GRIPPER:
            gripper_topic_to_fields.setdefault(mapping.source_topic, []).append(
                mapping.field_name
            )
            samples.setdefault(mapping.field_name, [])
        elif mapping.modality == AlignmentModality.TACTILE:
            tactile_topic_to_fields.setdefault(mapping.source_topic, []).append(
                mapping.field_name
            )
            samples.setdefault(mapping.field_name, [])

    if not any(
        (
            image_topic_to_fields,
            pose_topic_to_fields,
            gripper_topic_to_fields,
            tactile_topic_to_fields,
        )
    ):
        return samples

    topic_message_indexes: dict[str, int] = {}
    codec = Ros2DynamicCodec()
    with Path(mcap_a_path).open("rb") as fh:
        reader = make_reader(fh)
        for schema, channel, message in reader.iter_messages(log_time_order=False):
            topic = channel.topic
            if topic in image_topic_to_fields:
                message_index = topic_message_indexes.get(topic, 0)
                topic_message_indexes[topic] = message_index + 1
                message_ref = f"mcap://{topic}/msg_{message_index}"
                selected_timestamp = select_alignment_timestamp(
                    schema,
                    message,
                    codec=codec,
                )
                sample = (selected_timestamp.timestamp_ns, message_ref, None)
                for field_name in image_topic_to_fields[topic]:
                    samples[field_name].append(sample)
            if topic in pose_topic_to_fields and schema is not None:
                decoded = codec.decode(schema, message)
                selected_timestamp = select_alignment_timestamp(
                    schema,
                    message,
                    codec=codec,
                    decoded_message=decoded,
                )
                for mapping in pose_topic_to_fields[topic]:
                    pose = extract_pose_fields(decoded, mapping.message_type)
                    sample = (
                        selected_timestamp.timestamp_ns,
                        (pose[0], pose[1], pose[2]),
                        (pose[3], pose[4], pose[5], pose[6]),
                    )
                    samples[mapping.field_name].append(sample)
            if topic in gripper_topic_to_fields and schema is not None:
                decoded = codec.decode(schema, message)
                selected_timestamp = select_alignment_timestamp(
                    schema,
                    message,
                    codec=codec,
                    decoded_message=decoded,
                )
                message_index = topic_message_indexes.get(topic, 0)
                topic_message_indexes[topic] = message_index + 1
                message_ref = f"mcap://{topic}/msg_{message_index}"
                sample = (
                    selected_timestamp.timestamp_ns,
                    message_ref,
                    {"gripper_width": float(decoded.data)},
                )
                for field_name in gripper_topic_to_fields[topic]:
                    samples[field_name].append(sample)
            if topic in tactile_topic_to_fields and schema is not None:
                decoded = codec.decode(schema, message)
                selected_timestamp = select_alignment_timestamp(
                    schema,
                    message,
                    codec=codec,
                    decoded_message=decoded,
                )
                sample = (
                    selected_timestamp.timestamp_ns,
                    [float(value) for value in decoded.data],
                )
                for field_name in tactile_topic_to_fields[topic]:
                    samples[field_name].append(sample)

    return samples


def run_scene3_full_flow_check(
    *,
    mcap_a_path: str | Path,
    summary_path: str | Path,
    output_dir: str | Path,
    config: Scene3AlignmentConfig,
    run_root: str | Path = Path("src/data_clean/runs"),
) -> dict[str, Any]:
    """Run all Scene 3 developer checks as one chained smoke test."""
    mcap_a_path = Path(mcap_a_path).expanduser().resolve()
    summary_path = Path(summary_path).expanduser().resolve()
    output_dir = Path(output_dir).expanduser().resolve()
    run_root = Path(run_root)
    config = _ensure_default_target_fields(config)

    run_directory = create_run_directory(
        run_root=run_root,
        run_date=date.today(),
        target_scenes=["scene3"],
    )
    run_log_path = Path(run_directory.layout.run_log_path.path)
    steps: list[str] = ["create_run_directory"]
    errors: list[dict[str, str]] = []
    stage_results: dict[str, dict[str, Any]] = {}

    status = "success"

    try:
        mcap_input = run_scene3_mcap_a_input_check(
            mcap_a_path=mcap_a_path,
            summary_path=summary_path,
            config=config,
            run_root=run_root,
        )
        stage_results["scene3_mcap_a_input_check"] = mcap_input
        steps.append("run_scene3_mcap_a_input_check")
        if _stage_failed(mcap_input):
            status = "failed"
        else:
            catalog_path = _output_path(mcap_input, "source_topic_catalog_json")
            validation_path = _output_path(
                mcap_input, "mcap_a_input_validation_summary_json"
            )
            if catalog_path is None or validation_path is None:
                raise RuntimeError("MCAP_A input check did not produce required outputs")

            timeline = run_scene3_step_timeline_check(
                catalog_path=catalog_path,
                validation_summary_path=validation_path,
                config=config,
                run_root=run_root,
                timeline_id="scene3_full_flow",
            )
            stage_results["scene3_step_timeline_check"] = timeline
            steps.append("run_scene3_step_timeline_check")
            if _stage_failed(timeline):
                status = "failed"
            else:
                timeline_path = _output_path(timeline, "step_timeline_json")
                if timeline_path is None:
                    raise RuntimeError("Step timeline check did not produce step_timeline_json")

                field_samples = _extract_mcap_a_field_samples(
                    mcap_a_path=mcap_a_path,
                    field_mappings=config.target_fields,
                )
                field_alignment = run_scene3_field_alignment_check(
                    catalog_path=catalog_path,
                    validation_summary_path=validation_path,
                    timeline_path=timeline_path,
                    config=config,
                    field_samples=field_samples,
                    run_root=run_root,
                )
                stage_results["scene3_field_alignment_check"] = field_alignment
                steps.append("run_scene3_field_alignment_check")
                if _stage_failed(field_alignment):
                    status = "failed"
                else:
                    field_results_path = _output_path(
                        field_alignment, "field_alignment_results_json"
                    )
                    if field_results_path is None:
                        raise RuntimeError(
                            "Field alignment check did not produce field_alignment_results_json"
                        )

                    report = run_scene3_alignment_report_check(
                        field_alignment_results_path=field_results_path,
                        timeline_path=timeline_path,
                        catalog_path=catalog_path,
                        validation_summary_path=validation_path,
                        config=config,
                        run_root=run_root,
                    )
                    stage_results["scene3_alignment_report_check"] = report
                    steps.append("run_scene3_alignment_report_check")
                    if _stage_failed(report):
                        status = "failed"
                    else:
                        aligned_write = run_scene3_aligned_mcap_write_check(
                            source_mcap_path=mcap_a_path,
                            output_dir=output_dir,
                            field_alignment_results_path=field_results_path,
                            timeline_path=timeline_path,
                            run_root=run_root,
                        )
                        stage_results["scene3_aligned_mcap_write_check"] = aligned_write
                        steps.append("run_scene3_aligned_mcap_write_check")
                        if _stage_failed(aligned_write):
                            status = "failed"
                        else:
                            aligned_mcap_path = _output_path(
                                aligned_write, "aligned_mcap"
                            )
                            if aligned_mcap_path is None:
                                raise RuntimeError(
                                    "Aligned MCAP write check did not produce aligned_mcap"
                                )
                            aligned_message_count = _count_mcap_messages(
                                aligned_mcap_path
                            )
                            aligned_write.setdefault("outputs", {})[
                                "aligned_message_count"
                            ] = aligned_message_count
                            if aligned_message_count <= 0:
                                status = "failed"
                                errors.append(
                                    {
                                        "type": "EmptyAlignedMcap",
                                        "message": (
                                            "aligned.mcap contains no messages"
                                        ),
                                    }
                                )
    except Exception as exc:
        status = "failed"
        errors.append({"type": type(exc).__name__, "message": str(exc)})
        steps.append("scene3_full_flow_failed")

    stage_statuses = {
        stage_id: result.get("status", "unknown")
        for stage_id, result in stage_results.items()
    }
    stage_run_dirs = {
        stage_id: result.get("outputs", {}).get("run_dir")
        for stage_id, result in stage_results.items()
    }

    outputs = {
        "run_dir": str(run_directory.run_dir),
        "stage_run_dirs": stage_run_dirs,
        "aligned_output_dir": str(output_dir),
        "aligned_mcap": stage_results.get("scene3_aligned_mcap_write_check", {})
        .get("outputs", {})
        .get("aligned_mcap"),
        "alignment_index": stage_results.get("scene3_aligned_mcap_write_check", {})
        .get("outputs", {})
        .get("alignment_index"),
        "alignment_report": stage_results.get("scene3_aligned_mcap_write_check", {})
        .get("outputs", {})
        .get("alignment_report"),
        "aligned_message_count": stage_results.get(
            "scene3_aligned_mcap_write_check", {}
        )
        .get("outputs", {})
        .get("aligned_message_count"),
    }

    run_log = {
        "run_id": run_directory.run_id,
        "check_id": "scene3_full_flow_check",
        "status": status,
        "input": {
            "mcap_a_path": str(mcap_a_path),
            "summary_path": str(summary_path),
            "output_dir": str(output_dir),
        },
        "config": {
            "target_step_hz": config.target_step_hz,
            "target_field_count": len(config.target_fields),
            "pose_source_profile": config.pose_source_profile,
            "source_config": "cli_override",
            "temporary_override_saved": False,
        },
        "stage_statuses": stage_statuses,
        "steps": steps + ["write_run_log"],
        "errors": errors,
        "outputs": outputs,
        "created_at": datetime.now().isoformat(),
    }
    run_log_path.write_text(
        json.dumps(_jsonable(run_log), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return {
        **run_log,
        "stage_results": stage_results,
        "run_log_path": str(run_log_path),
    }
