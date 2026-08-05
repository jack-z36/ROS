"""MCAP file processing pipeline for the ROS2 cleaning workflow."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from mcap.reader import make_reader
from mcap.records import Channel, Message, Schema
from mcap.well_known import SchemaEncoding
from mcap.writer import Writer

from repo.config.mcap_process_config import AppConfig, GripperStreamConfig
from repo.ros2_codec import (
    Ros2CodecError,
    Ros2DynamicCodec,
    extract_pose_fields,
    image_message_to_ndarray,
    inject_pose_fields,
    normalize_ros2_schema,
)
from service.gripper_width import GripperDetectionError, GripperWidthAccumulator
from service.tcp_transform import (
    compute_tcp_pose_in_source_frame,
    transform_camera_to_common_tcp,
    transform_pose_to_common_camera_frame,
)
from service.validator import (
    FileProcessingReport,
    GripperTopicStats,
    PoseTopicStats,
    ValidationError,
    build_topic_inventory,
    validate_input_inventory,
    validate_output_contract,
)
from schemas.ros2_schemas import STD_MSGS_FLOAT32


class ProcessingError(RuntimeError):
    """Raised when a file-level MCAP processing step fails."""


@dataclass(frozen=True)
class _StreamArtifacts:
    raw_pose_payloads_by_topic: dict[str, list[bytes]]
    camera_common_pose_payloads_by_topic: dict[str, list[bytes]]
    tcp_common_pose_payloads_by_topic: dict[str, list[bytes]]
    tcp_pose_payloads_by_topic: dict[str, list[bytes]]
    gripper_payloads_by_image_topic: dict[str, list[bytes]]
    gripper_stats: dict[str, GripperTopicStats]


class _McapOutputBuilder:
    def __init__(self, writer: Writer, gripper_streams: tuple[GripperStreamConfig, ...]):
        self.writer = writer
        self._schema_map: dict[int, int] = {}
        self._channel_map: dict[int, int] = {}
        self._gripper_schema_id: int | None = None
        self._gripper_channel_ids: dict[str, int] = {}
        self._pose_schema_ids: dict[str, int] = {}
        self._pose_channel_ids: dict[str, int] = {}

    def _schema_id(self, schema: Schema | None) -> int:
        if schema is None:
            return 0
        schema = normalize_ros2_schema(schema)
        schema_id = self._schema_map.get(schema.id, 0)
        if schema_id == 0:
            schema_id = self.writer.register_schema(schema.name, schema.encoding, schema.data)
            self._schema_map[schema.id] = schema_id
        return schema_id

    def ensure_original_channel(self, channel: Channel, schema: Schema | None) -> int:
        if channel.id in self._channel_map:
            return self._channel_map[channel.id]

        schema_id = self._schema_id(schema)
        output_channel_id = self.writer.register_channel(
            topic=channel.topic,
            message_encoding=channel.message_encoding,
            schema_id=schema_id,
            metadata=channel.metadata,
        )
        self._channel_map[channel.id] = output_channel_id
        return output_channel_id

    def register_pose_output_channel(
        self,
        output_topic: str,
        input_schema: Schema | None,
        input_channel: Channel,
    ) -> int:
        cache_key = f"pose:{output_topic}"
        if cache_key in self._pose_channel_ids:
            return self._pose_channel_ids[cache_key]

        if input_schema is None:
            raise ProcessingError(f'cannot register output channel for "{output_topic}": no input schema')

        schema_id = self._schema_id(input_schema)
        channel_id = self.writer.register_channel(
            topic=output_topic,
            message_encoding=input_channel.message_encoding,
            schema_id=schema_id,
            metadata={},
        )
        self._pose_channel_ids[cache_key] = channel_id
        return channel_id

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
    raw_pose_payloads: dict[str, list[bytes]] = {topic: [] for topic in pose_streams}
    camera_common_pose_payloads: dict[str, list[bytes]] = {topic: [] for topic in pose_streams}
    tcp_common_pose_payloads: dict[str, list[bytes]] = {topic: [] for topic in pose_streams}
    tcp_pose_payloads: dict[str, list[bytes]] = {topic: [] for topic in pose_streams}
    gripper_accumulators = {
        stream.image_topic: GripperWidthAccumulator(stream) for stream in config.gripper_streams
    }

    topic_to_hand: dict[str, str] = {}
    has_tcp_output = False
    for stream in config.pose_streams:
        if "_left" in stream.input_topic:
            topic_to_hand[stream.input_topic] = "left"
        elif "_right" in stream.input_topic:
            topic_to_hand[stream.input_topic] = "right"
        if stream.output_tcp_pose:
            has_tcp_output = True

    if has_tcp_output:
        if not config.camera_from_tcp:
            raise ProcessingError("TCP pose output requires camera_from_tcp configuration")

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
                pose_tuple = extract_pose_fields(decoded_pose, pose_stream.msg_type)

                raw_pose_payloads[topic].append(message.data)

                if config.frame_alignment is not None:
                    hand = topic_to_hand.get(topic, "left")
                    need_camera_common = bool(pose_stream.output_camera_pose_common)
                    need_tcp_common = bool(pose_stream.output_tcp_pose_common)

                    if need_camera_common or need_tcp_common:
                        camera_common_pose = transform_pose_to_common_camera_frame(
                            *pose_tuple,
                            config.frame_alignment,
                            hand,
                        )
                        if need_camera_common:
                            encoded_camera_common = codec.encode(
                                schema,
                                inject_pose_fields(decoded_pose, pose_stream.msg_type, camera_common_pose),
                            )
                            camera_common_pose_payloads[topic].append(encoded_camera_common)

                        if need_tcp_common:
                            tcp_common_pose = transform_camera_to_common_tcp(
                                *camera_common_pose,
                                config.frame_alignment,
                                hand,
                            )
                            encoded_tcp_common = codec.encode(
                                schema,
                                inject_pose_fields(decoded_pose, pose_stream.msg_type, tcp_common_pose),
                            )
                            tcp_common_pose_payloads[topic].append(encoded_tcp_common)

                # The production pose applies exactly one camera-to-TCP
                # extrinsic and otherwise preserves the raw source frame.
                if pose_stream.output_tcp_pose:
                    hand = topic_to_hand.get(topic)
                    if hand is None:
                        raise ProcessingError(
                            f'TCP pose output cannot infer hand from input topic "{topic}"'
                        )
                    extrinsic = (config.camera_from_tcp or {}).get(hand)
                    if extrinsic is None:
                        raise ProcessingError(f'TCP pose output requires camera_from_tcp.{hand}')

                    tcp_pose = compute_tcp_pose_in_source_frame(
                        *pose_tuple,
                        extrinsic.translation_m,
                        extrinsic.rotation_quat_xyzw,
                    )
                    encoded_tcp = codec.encode(
                        schema,
                        inject_pose_fields(decoded_pose, pose_stream.msg_type, tcp_pose),
                    )
                    tcp_pose_payloads[topic].append(encoded_tcp)

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
        raw_pose_payloads_by_topic=raw_pose_payloads,
        camera_common_pose_payloads_by_topic=camera_common_pose_payloads,
        tcp_common_pose_payloads_by_topic=tcp_common_pose_payloads,
        tcp_pose_payloads_by_topic=tcp_pose_payloads,
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
    raw_pose_iterators = {topic: iter(payloads) for topic, payloads in artifacts.raw_pose_payloads_by_topic.items()}
    camera_common_iterators = {
        topic: iter(payloads)
        for topic, payloads in artifacts.camera_common_pose_payloads_by_topic.items()
        if payloads
    }
    tcp_common_iterators = {
        topic: iter(payloads)
        for topic, payloads in artifacts.tcp_common_pose_payloads_by_topic.items()
        if payloads
    }
    tcp_pose_iterators = {
        topic: iter(payloads)
        for topic, payloads in artifacts.tcp_pose_payloads_by_topic.items()
        if payloads
    }
    gripper_iterators = {topic: iter(payloads) for topic, payloads in artifacts.gripper_payloads_by_image_topic.items()}

    pose_output_counts = {topic: 0 for topic in pose_streams}
    camera_common_output_counts: dict[str, int] = {topic: 0 for topic in camera_common_iterators}
    tcp_common_output_counts: dict[str, int] = {topic: 0 for topic in tcp_common_iterators}
    tcp_pose_output_counts: dict[str, int] = {topic: 0 for topic in tcp_pose_iterators}
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

            pose_schema_cache: dict[str, tuple[Schema | None, Channel]] = {}

            for schema, channel, message in source_reader.iter_messages(log_time_order=False):
                output_channel_id = output_builder.ensure_original_channel(channel, schema)
                payload = message.data
                if channel.topic in raw_pose_iterators:
                    payload = next(raw_pose_iterators[channel.topic])
                    pose_output_counts[channel.topic] += 1
                    if channel.topic not in pose_schema_cache:
                        pose_schema_cache[channel.topic] = (schema, channel)

                writer.add_message(
                    channel_id=output_channel_id,
                    log_time=message.log_time,
                    publish_time=message.publish_time,
                    sequence=message.sequence,
                    data=payload,
                )

                if channel.topic in camera_common_iterators:
                    cached_schema, cached_channel = pose_schema_cache.get(channel.topic, (schema, channel))
                    stream = pose_streams[channel.topic]
                    if stream.output_camera_pose_common:
                        cam_channel_id = output_builder.register_pose_output_channel(
                            stream.output_camera_pose_common,
                            cached_schema,
                            cached_channel,
                        )
                        writer.add_message(
                            channel_id=cam_channel_id,
                            log_time=message.log_time,
                            publish_time=message.publish_time,
                            sequence=message.sequence,
                            data=next(camera_common_iterators[channel.topic]),
                        )
                        camera_common_output_counts[channel.topic] += 1

                if channel.topic in tcp_common_iterators:
                    cached_schema, cached_channel = pose_schema_cache.get(channel.topic, (schema, channel))
                    stream = pose_streams[channel.topic]
                    if stream.output_tcp_pose_common:
                        tcp_channel_id = output_builder.register_pose_output_channel(
                            stream.output_tcp_pose_common,
                            cached_schema,
                            cached_channel,
                        )
                        writer.add_message(
                            channel_id=tcp_channel_id,
                            log_time=message.log_time,
                            publish_time=message.publish_time,
                            sequence=message.sequence,
                            data=next(tcp_common_iterators[channel.topic]),
                        )
                        tcp_common_output_counts[channel.topic] += 1

                if channel.topic in tcp_pose_iterators:
                    cached_schema, cached_channel = pose_schema_cache.get(channel.topic, (schema, channel))
                    stream = pose_streams[channel.topic]
                    if stream.output_tcp_pose:
                        tcp_pose_channel_id = output_builder.register_pose_output_channel(
                            stream.output_tcp_pose,
                            cached_schema,
                            cached_channel,
                        )
                        writer.add_message(
                            channel_id=tcp_pose_channel_id,
                            log_time=message.log_time,
                            publish_time=message.publish_time,
                            sequence=message.sequence,
                            data=next(tcp_pose_iterators[channel.topic]),
                        )
                        tcp_pose_output_counts[channel.topic] += 1

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

    for topic, iterator in raw_pose_iterators.items():
        if next(iterator, None) is not None:
            raise ProcessingError(f'pose topic "{topic}" left unread raw payloads')
    for topic, iterator in camera_common_iterators.items():
        if next(iterator, None) is not None:
            raise ProcessingError(f'camera common pose topic "{topic}" left unread payloads')
    for topic, iterator in tcp_common_iterators.items():
        if next(iterator, None) is not None:
            raise ProcessingError(f'tcp common pose topic "{topic}" left unread payloads')
    for topic, iterator in tcp_pose_iterators.items():
        if next(iterator, None) is not None:
            raise ProcessingError(f'TCP pose topic "{topic}" left unread payloads')
    for topic, iterator in gripper_iterators.items():
        if next(iterator, None) is not None:
            raise ProcessingError(f'image topic "{topic}" left unread gripper payloads')

    extra_topics = len(config.gripper_streams)
    if config.frame_alignment is not None:
        extra_topics += sum(
            1 for s in config.pose_streams if s.output_camera_pose_common
        ) + sum(
            1 for s in config.pose_streams if s.output_tcp_pose_common
        )
    extra_topics += sum(1 for s in config.pose_streams if s.output_tcp_pose)
    output_topic_count = input_topic_count + extra_topics
    pose_topic_stats = tuple(
        PoseTopicStats(
            topic=stream.output_topic,
            input_count=inventory[stream.input_topic].message_count,
            output_count=pose_output_counts[stream.input_topic],
        )
        for stream in config.pose_streams
    )
    tcp_pose_topic_stats = tuple(
        PoseTopicStats(
            topic=stream.output_tcp_pose,
            input_count=inventory[stream.input_topic].message_count,
            output_count=tcp_pose_output_counts.get(stream.input_topic, 0),
            hand=(
                "left" if "_left" in stream.input_topic
                else "right" if "_right" in stream.input_topic
                else None
            ),
            frame_id="source_frame",
        )
        for stream in config.pose_streams
        if stream.output_tcp_pose
    )
    report = FileProcessingReport(
        input_file=str(input_path),
        output_file=str(output_path),
        status="success",
        input_topic_count=input_topic_count,
        output_topic_count=output_topic_count,
        pose_topics=pose_topic_stats + tcp_pose_topic_stats,
        gripper_topics=tuple(artifacts.gripper_stats[stream.image_topic] for stream in config.gripper_streams),
    )
    validate_output_contract(report, expected_added_topics=extra_topics)
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
