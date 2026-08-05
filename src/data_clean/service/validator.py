"""Validation and reporting helpers for MCAP cleaning jobs."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from mcap.summary import Summary

from repo.config.mcap_process_config import AppConfig

SUPPORTED_POSE_TYPES = {
    "nav_msgs/msg/Odometry",
    "geometry_msgs/msg/PoseStamped",
}

SUPPORTED_IMAGE_TYPES = {
    "sensor_msgs/msg/Image",
}


class ValidationError(RuntimeError):
    """Raised when an input/output MCAP contract is violated."""


@dataclass(frozen=True)
class TopicInventory:
    topic: str
    schema_name: str | None
    schema_encoding: str | None
    message_encoding: str
    message_count: int
    channel_ids: tuple[int, ...]


@dataclass(frozen=True)
class PoseTopicStats:
    topic: str
    input_count: int
    output_count: int
    hand: str | None = None
    frame_id: str | None = None


@dataclass(frozen=True)
class GripperTopicStats:
    image_topic: str
    output_topic: str
    frame_count: int
    gripper_count: int
    missing_frames: int
    interpolated_frames: int


@dataclass(frozen=True)
class FileProcessingReport:
    input_file: str
    output_file: str
    status: str
    input_topic_count: int
    output_topic_count: int
    pose_topics: tuple[PoseTopicStats, ...]
    gripper_topics: tuple[GripperTopicStats, ...]
    failure_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_topic_inventory(summary: Summary) -> dict[str, TopicInventory]:
    message_counts = summary.statistics.channel_message_counts if summary.statistics is not None else {}
    topic_to_channels: dict[str, list[int]] = {}
    for channel_id, channel in summary.channels.items():
        topic_to_channels.setdefault(channel.topic, []).append(channel_id)

    inventory: dict[str, TopicInventory] = {}
    for topic, channel_ids in topic_to_channels.items():
        first_channel = summary.channels[channel_ids[0]]
        schema = summary.schemas.get(first_channel.schema_id) if first_channel.schema_id else None
        total_messages = sum(int(message_counts.get(channel_id, 0)) for channel_id in channel_ids)
        inventory[topic] = TopicInventory(
            topic=topic,
            schema_name=schema.name if schema is not None else None,
            schema_encoding=schema.encoding if schema is not None else None,
            message_encoding=first_channel.message_encoding,
            message_count=total_messages,
            channel_ids=tuple(channel_ids),
        )
    return inventory


def validate_input_inventory(config: AppConfig, inventory: dict[str, TopicInventory]) -> None:
    for pose_stream in config.pose_streams:
        topic_inventory = inventory.get(pose_stream.input_topic)
        if topic_inventory is None:
            raise ValidationError(f'missing configured pose topic "{pose_stream.input_topic}"')
        if topic_inventory.message_count == 0:
            raise ValidationError(f'pose topic "{pose_stream.input_topic}" has no messages')
        if len(topic_inventory.channel_ids) != 1:
            raise ValidationError(f'pose topic "{pose_stream.input_topic}" must map to exactly one channel')
        if topic_inventory.schema_name != pose_stream.msg_type:
            raise ValidationError(
                f'pose topic "{pose_stream.input_topic}" expected type "{pose_stream.msg_type}" but found "{topic_inventory.schema_name}"'
            )
        if pose_stream.msg_type not in SUPPORTED_POSE_TYPES:
            raise ValidationError(
                f'pose topic "{pose_stream.input_topic}" uses unsupported type "{pose_stream.msg_type}"'
            )
    for gripper_stream in config.gripper_streams:
        topic_inventory = inventory.get(gripper_stream.image_topic)
        if topic_inventory is None:
            raise ValidationError(f'missing configured image topic "{gripper_stream.image_topic}"')
        if topic_inventory.message_count == 0:
            raise ValidationError(f'image topic "{gripper_stream.image_topic}" has no messages')
        if len(topic_inventory.channel_ids) != 1:
            raise ValidationError(f'image topic "{gripper_stream.image_topic}" must map to exactly one channel')
        if topic_inventory.schema_name != gripper_stream.image_msg_type:
            raise ValidationError(
                f'image topic "{gripper_stream.image_topic}" expected type "{gripper_stream.image_msg_type}" but found "{topic_inventory.schema_name}"'
            )
        if gripper_stream.image_msg_type not in SUPPORTED_IMAGE_TYPES:
            raise ValidationError(
                f'image topic "{gripper_stream.image_topic}" uses unsupported type "{gripper_stream.image_msg_type}"'
            )
        if gripper_stream.output_topic in inventory:
            raise ValidationError(
                f'gripper output topic "{gripper_stream.output_topic}" conflicts with an existing topic in the input file'
            )


def validate_output_contract(report: FileProcessingReport, expected_added_topics: int) -> None:
    if report.output_topic_count != report.input_topic_count + expected_added_topics:
        raise ValidationError(
            f"expected output topic count {report.input_topic_count + expected_added_topics}, got {report.output_topic_count}"
        )
    for pose_topic in report.pose_topics:
        if pose_topic.input_count != pose_topic.output_count:
            raise ValidationError(
                f'pose topic "{pose_topic.topic}" changed message count {pose_topic.input_count} -> {pose_topic.output_count}'
            )
    for gripper_topic in report.gripper_topics:
        if gripper_topic.frame_count != gripper_topic.gripper_count:
            raise ValidationError(
                f'gripper topic "{gripper_topic.output_topic}" count mismatch: '
                f'frames={gripper_topic.frame_count}, gripper_messages={gripper_topic.gripper_count}'
            )


@dataclass(frozen=True)
class Scene1ContractResult:
    """Result of Scene 1 output contract validation."""

    status: str  # "success" | "failed" | "skipped"
    failure_reason: str | None = None
    artifacts: list[str] = field(default_factory=list)
    run_log: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def scene1_output_contract_validate(
    report: FileProcessingReport,
    config: AppConfig,
) -> Scene1ContractResult:
    """Validate Scene 1 output contract and return a structured result.

    Checks:
    - pose topic output count matches input count (raw pose retention)
    - gripper output count matches image frame count
    - output topic count matches expected (input + added topics)
    - config_path / transform_file traceability
    """
    checks: list[dict[str, str]] = []
    artifacts: list[str] = []
    failure_reasons: list[str] = []

    # Check 1: raw pose retention (input_count == output_count for each pose stream)
    for pose_topic in report.pose_topics:
        if pose_topic.input_count != pose_topic.output_count:
            failure_reasons.append(
                f'pose topic "{pose_topic.topic}" count mismatch: '
                f'input={pose_topic.input_count}, output={pose_topic.output_count}'
            )
        checks.append({
            "check": "raw_pose_retention",
            "topic": pose_topic.topic,
            "input_count": str(pose_topic.input_count),
            "output_count": str(pose_topic.output_count),
            "result": "pass" if pose_topic.input_count == pose_topic.output_count else "fail",
        })

    # Check 2: gripper count == frame count
    for gripper_topic in report.gripper_topics:
        if gripper_topic.frame_count != gripper_topic.gripper_count:
            failure_reasons.append(
                f'gripper topic "{gripper_topic.output_topic}" count mismatch: '
                f'frames={gripper_topic.frame_count}, gripper_messages={gripper_topic.gripper_count}'
            )
        checks.append({
            "check": "gripper_frame_count",
            "topic": gripper_topic.output_topic,
            "frame_count": str(gripper_topic.frame_count),
            "gripper_count": str(gripper_topic.gripper_count),
            "result": "pass" if gripper_topic.frame_count == gripper_topic.gripper_count else "fail",
        })

    # Check 3: output topic count matches expected
    expected_added = len(config.gripper_streams)
    if config.frame_alignment is not None:
        expected_added += sum(
            1 for s in config.pose_streams if s.output_camera_pose_common
        ) + sum(
            1 for s in config.pose_streams if s.output_tcp_pose_common
        )
    expected_added += sum(
        1 for s in config.pose_streams if s.output_tcp_pose
    )
    expected_output = report.input_topic_count + expected_added
    if report.output_topic_count != expected_output:
        failure_reasons.append(
            f"output topic count mismatch: expected {expected_output}, got {report.output_topic_count}"
        )
    checks.append({
        "check": "output_topic_count",
        "input_count": str(report.input_topic_count),
        "expected_added": str(expected_added),
        "expected_output": str(expected_output),
        "actual_output": str(report.output_topic_count),
        "result": "pass" if report.output_topic_count == expected_output else "fail",
    })

    # Check 4: config traceability
    config_path = ""
    transform_files: list[str] = []
    for stream in config.pose_streams:
        if stream.transform_file:
            transform_files.append(stream.transform_file)
    checks.append({
        "check": "config_traceability",
        "config_path": config_path,
        "transform_files": ",".join(transform_files),
        "result": "pass",
    })

    # Determine overall status
    if report.status == "failed":
        status = "failed"
        if report.failure_reason:
            failure_reasons.insert(0, f"processing failed: {report.failure_reason}")
    elif failure_reasons:
        status = "failed"
    else:
        status = "success"

    # Build artifacts list
    artifacts.append("output_contract_report.json")

    run_log = {
        "check_type": "scene1_output_contract_validate",
        "input_file": report.input_file,
        "output_file": report.output_file,
        "checks": checks,
    }

    return Scene1ContractResult(
        status=status,
        failure_reason="; ".join(failure_reasons) if failure_reasons else None,
        artifacts=artifacts,
        run_log=run_log,
    )


def write_scene1_contract_report(
    result: Scene1ContractResult,
    output_dir: str | Path,
) -> Path:
    """Write the contract validation result to a JSON file."""
    output_path = Path(output_dir) / "output_contract_report.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as fh:
        json.dump(result.to_dict(), fh, ensure_ascii=False, indent=2)
    return output_path


def write_scene1_smoke_summary(
    report: FileProcessingReport,
    contract_result: Scene1ContractResult,
    output_dir: str | Path,
) -> Path:
    """Write a smoke test summary combining processing report and contract result."""
    output_path = Path(output_dir) / "smoke_summary.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    summary = {
        "processing_report": report.to_dict(),
        "contract_result": contract_result.to_dict(),
    }
    with output_path.open("w", encoding="utf-8") as fh:
        json.dump(summary, fh, ensure_ascii=False, indent=2)
    return output_path
