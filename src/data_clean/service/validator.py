"""Validation and reporting helpers for MCAP cleaning jobs."""

from __future__ import annotations

from dataclasses import asdict, dataclass
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
