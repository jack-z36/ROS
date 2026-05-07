"""MCAP file processing pipeline for the ROS2 cleaning workflow."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from mcap.reader import make_reader
from mcap.records import Channel, Message, Schema
from mcap.well_known import SchemaEncoding
from mcap.writer import Writer

from core.gripper_width import GripperDetectionError, GripperWidthAccumulator
from core.mcap_process_config import AppConfig, GripperStreamConfig
from core.ros2_codec import (
    Ros2CodecError,
    Ros2DynamicCodec,
    extract_pose_fields,
    image_message_to_ndarray,
    inject_pose_fields,
    normalize_ros2_schema,
)
from core.ros2_schemas import STD_MSGS_FLOAT32
from core.tcp_transform import transform_pose_to_tcp
from core.validator import (
    FileProcessingReport,
    GripperTopicStats,
    PoseTopicStats,
    ValidationError,
    build_topic_inventory,
    validate_input_inventory,
    validate_output_contract,
)


class ProcessingError(RuntimeError):
    """Raised when a file-level MCAP processing step fails."""


@dataclass(frozen=True)
class _StreamArtifacts:
    pose_payloads_by_topic: dict[str, list[bytes]]
    gripper_payloads_by_image_topic: dict[str, list[bytes]]
    gripper_stats: dict[str, GripperTopicStats]


class _McapOutputBuilder:
    def __init__(self, writer: Writer, gripper_streams: tuple[GripperStreamConfig, ...]):
        self.writer = writer
        self._schema_map: dict[int, int] = {}
        self._channel_map: dict[int, int] = {}
        self._gripper_schema_id: int | None = None
        self._gripper_channel_ids: dict[str, int] = {}

    def ensure_original_channel(self, channel: Channel, schema: Schema | None) -> int:
        if channel.id in self._channel_map:
            return self._channel_map[channel.id]

        schema_id = 0
        if schema is not None:
            schema = normalize_ros2_schema(schema)
            schema_id = self._schema_map.get(schema.id, 0)
            if schema_id == 0:
                schema_id = self.writer.register_schema(schema.name, schema.encoding, schema.data)
                self._schema_map[schema.id] = schema_id

        output_channel_id = self.writer.register_channel(
            topic=channel.topic,
            message_encoding=channel.message_encoding,
            schema_id=schema_id,
            metadata=channel.metadata,
        )
        self._channel_map[channel.id] = output_channel_id
        return output_channel_id

    def gripper_channel_id(self, output_topic: str) -> int:
        if output_topic in self._gripper_channel_ids:
            return self._gripper_channel_ids[output_topic]

        if self._gripper_schema_id is None:
            self._gripper_schema_id = self.writer.register_schema(
                "std_msgs/msg/Float32",
                SchemaEncoding.ROS2,
                STD_MSGS_FLOAT32.encode("utf-8"),
            )

        channel_id = self.writer.register_channel(
            topic=output_topic,
            message_encoding="cdr",
            schema_id=self._gripper_schema_id,
            metadata={},
        )
        self._gripper_channel_ids[output_topic] = channel_id
        return channel_id


def _collect_stream_artifacts(input_path: Path, config: AppConfig) -> _StreamArtifacts:
    pose_streams = config.pose_by_topic()
    gripper_streams = config.gripper_by_image_topic()
    pose_payloads: dict[str, list[bytes]] = {topic: [] for topic in pose_streams}
    gripper_accumulators = {
        stream.image_topic: GripperWidthAccumulator(stream) for stream in config.gripper_streams
    }

    codec = Ros2DynamicCodec()
    with input_path.open("rb") as fh:
        reader = make_reader(fh)
        summary = reader.get_summary()
        inventory = build_topic_inventory(summary)
        validate_input_inventory(config, inventory)
        fh.seek(0)
        reader = make_reader(fh)

        for schema, channel, message in reader.iter_messages(log_time_order=False):
            topic = channel.topic
            if topic in pose_streams:
                pose_stream = pose_streams[topic]
                if schema is None:
                    raise ProcessingError(f'pose topic "{topic}" has no schema record')
                decoded_pose = codec.decode(schema, message)
                transformed_pose = transform_pose_to_tcp(
                    *extract_pose_fields(decoded_pose, pose_stream.msg_type),
                    config.transform_for_pose_stream(pose_stream),
                )
                encoded_pose = codec.encode(
                    schema,
                    inject_pose_fields(decoded_pose, pose_stream.msg_type, transformed_pose),
                )
                pose_payloads[topic].append(encoded_pose)
            elif topic in gripper_streams:
                if schema is None:
                    raise ProcessingError(f'image topic "{topic}" has no schema record')
                decoded_image = codec.decode(schema, message)
                image = image_message_to_ndarray(decoded_image, gripper_streams[topic].image_msg_type)
                gripper_accumulators[topic].consume(image)

    gripper_payloads: dict[str, list[bytes]] = {}
    gripper_stats: dict[str, GripperTopicStats] = {}
    for image_topic, accumulator in gripper_accumulators.items():
        result = accumulator.finalize()
        gripper_payloads[image_topic] = [codec.encode_float32(value) for value in result.values]
        output_topic = gripper_streams[image_topic].output_topic
        gripper_stats[image_topic] = GripperTopicStats(
            image_topic=image_topic,
            output_topic=output_topic,
            frame_count=result.frame_count,
            gripper_count=len(result.values),
            missing_frames=result.missing_frames,
            interpolated_frames=result.interpolated_frames,
        )

    return _StreamArtifacts(
        pose_payloads_by_topic=pose_payloads,
        gripper_payloads_by_image_topic=gripper_payloads,
        gripper_stats=gripper_stats,
    )


def _write_output_file(
    input_path: Path,
    output_path: Path,
    config: AppConfig,
    artifacts: _StreamArtifacts,
) -> FileProcessingReport:
    pose_streams = config.pose_by_topic()
    gripper_streams = config.gripper_by_image_topic()
    pose_iterators = {topic: iter(payloads) for topic, payloads in artifacts.pose_payloads_by_topic.items()}
    gripper_iterators = {topic: iter(payloads) for topic, payloads in artifacts.gripper_payloads_by_image_topic.items()}

    pose_output_counts = {topic: 0 for topic in pose_streams}
    input_topic_count = 0
    output_topic_count = 0

    with input_path.open("rb") as source_fh:
        source_reader = make_reader(source_fh)
        summary = source_reader.get_summary()
        inventory = build_topic_inventory(summary)
        input_topic_count = len(inventory)
        source_fh.seek(0)
        source_reader = make_reader(source_fh)

        with output_path.open("wb") as output_fh:
            writer = Writer(output_fh)
            writer.start()
            output_builder = _McapOutputBuilder(writer, config.gripper_streams)

            for schema, channel, message in source_reader.iter_messages(log_time_order=False):
                output_channel_id = output_builder.ensure_original_channel(channel, schema)
                payload = message.data
                if channel.topic in pose_iterators:
                    payload = next(pose_iterators[channel.topic])
                    pose_output_counts[channel.topic] += 1

                writer.add_message(
                    channel_id=output_channel_id,
                    log_time=message.log_time,
                    publish_time=message.publish_time,
                    sequence=message.sequence,
                    data=payload,
                )

                if channel.topic in gripper_iterators:
                    output_topic = gripper_streams[channel.topic].output_topic
                    gripper_channel_id = output_builder.gripper_channel_id(output_topic)
                    writer.add_message(
                        channel_id=gripper_channel_id,
                        log_time=message.log_time,
                        publish_time=message.publish_time,
                        sequence=message.sequence,
                        data=next(gripper_iterators[channel.topic]),
                    )

            writer.finish()

    for topic, iterator in pose_iterators.items():
        if next(iterator, None) is not None:
            raise ProcessingError(f'pose topic "{topic}" left unread replacement payloads')
    for topic, iterator in gripper_iterators.items():
        if next(iterator, None) is not None:
            raise ProcessingError(f'image topic "{topic}" left unread gripper payloads')

    output_topic_count = input_topic_count + len(config.gripper_streams)
    pose_topic_stats = tuple(
        PoseTopicStats(
            topic=stream.output_topic,
            input_count=inventory[stream.input_topic].message_count,
            output_count=pose_output_counts[stream.input_topic],
        )
        for stream in config.pose_streams
    )
    report = FileProcessingReport(
        input_file=str(input_path),
        output_file=str(output_path),
        status="success",
        input_topic_count=input_topic_count,
        output_topic_count=output_topic_count,
        pose_topics=pose_topic_stats,
        gripper_topics=tuple(artifacts.gripper_stats[stream.image_topic] for stream in config.gripper_streams),
    )
    validate_output_contract(report, expected_added_topics=len(config.gripper_streams))
    return report


def process_mcap_file(input_path: str | Path, output_path: str | Path, config: AppConfig) -> FileProcessingReport:
    input_path = Path(input_path)
    output_path = Path(output_path)
    try:
        artifacts = _collect_stream_artifacts(input_path, config)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        return _write_output_file(input_path, output_path, config, artifacts)
    except (ValidationError, Ros2CodecError, GripperDetectionError, ProcessingError) as exc:
        return FileProcessingReport(
            input_file=str(input_path),
            output_file=str(output_path),
            status="failed",
            input_topic_count=0,
            output_topic_count=0,
            pose_topics=tuple(),
            gripper_topics=tuple(),
            failure_reason=str(exc),
        )
