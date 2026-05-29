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
    compute_tcp_in_camera,
    transform_camera_to_common_tcp,
    transform_pose_to_common_camera_frame,
)
from schemas.arm_base_pose import (
    FrameIdType,
    HandType,
    WorkFrameInArmBasePose,
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
    arm_base_tcp_pose_payloads_by_topic: dict[str, list[bytes]]
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


def _ensure_algo():
    """Lazy-init shared Algo instance for arm-base transform."""
    import importlib

    try:
        mod = importlib.import_module("Robotic_Arm.rm_robot_interface")
        arm_model = mod.rm_robot_arm_model_e.RM_MODEL_RM_65_E
        force_type = mod.rm_force_type_e.RM_MODEL_RM_B_E
        return mod.Algo(arm_model, force_type)
    except Exception:
        return None


_ALGO_CACHE: dict[bool, object] = {}


def _get_algo() -> object | None:
    """Return cached Algo instance or None if unavailable."""
    if True not in _ALGO_CACHE:
        _ALGO_CACHE[True] = _ensure_algo()
    return _ALGO_CACHE[True]


def _build_work_frame(work_frame_config, hand: str) -> WorkFrameInArmBasePose:
    """Build WorkFrameInArmBasePose from config."""
    h = HandType.LEFT if hand == "left" else HandType.RIGHT
    fid = FrameIdType.LEFT_ARM_BASE if hand == "left" else FrameIdType.RIGHT_ARM_BASE
    return WorkFrameInArmBasePose(
        hand=h,
        frame_id=fid,
        position_m=dict(work_frame_config.position_m),
        orientation=dict(work_frame_config.orientation),
    )


def _collect_stream_artifacts(input_path: Path, config: AppConfig) -> _StreamArtifacts:
    pose_streams = config.pose_by_topic()
    gripper_streams = config.gripper_by_image_topic()
    raw_pose_payloads: dict[str, list[bytes]] = {topic: [] for topic in pose_streams}
    camera_common_pose_payloads: dict[str, list[bytes]] = {topic: [] for topic in pose_streams}
    tcp_common_pose_payloads: dict[str, list[bytes]] = {topic: [] for topic in pose_streams}
    arm_base_tcp_pose_payloads: dict[str, list[bytes]] = {topic: [] for topic in pose_streams}
    gripper_accumulators = {
        stream.image_topic: GripperWidthAccumulator(stream) for stream in config.gripper_streams
    }

    topic_to_hand: dict[str, str] = {}
    has_arm_base_output = False
    for stream in config.pose_streams:
        if "_left" in stream.input_topic:
            topic_to_hand[stream.input_topic] = "left"
        elif "_right" in stream.input_topic:
            topic_to_hand[stream.input_topic] = "right"
        if stream.output_arm_base_tcp_pose:
            has_arm_base_output = True

    algo = _get_algo() if has_arm_base_output and config.work_frames else None

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
                    camera_common_pose = transform_pose_to_common_camera_frame(
                        *pose_tuple,
                        config.frame_alignment,
                        hand,
                    )
                    encoded_camera_common = codec.encode(
                        schema,
                        inject_pose_fields(decoded_pose, pose_stream.msg_type, camera_common_pose),
                    )
                    camera_common_pose_payloads[topic].append(encoded_camera_common)

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

                # Arm-base TCP pose: compute if output topic is configured and SDK available
                if pose_stream.output_arm_base_tcp_pose and algo is not None and config.work_frames:
                    hand = topic_to_hand.get(topic, "left")
                    work_frame_config = config.work_frames.get(hand)
                    if work_frame_config is not None:
                        from service.arm_base_transform import compute_arm_base_tcp_pose

                        # Step 1: TCP-in-camera from extrinsic
                        if config.frame_alignment is not None:
                            extrinsic_t = (
                                config.frame_alignment.camera_from_left_tcp.translation_m
                                if hand == "left"
                                else config.frame_alignment.camera_from_right_tcp.translation_m
                            )
                            extrinsic_q = (
                                config.frame_alignment.camera_from_left_tcp.rotation_quat_xyzw
                                if hand == "left"
                                else config.frame_alignment.camera_from_right_tcp.rotation_quat_xyzw
                            )
                        else:
                            extrinsic_t = (0.0, 0.0, 0.0)
                            extrinsic_q = (0.0, 0.0, 0.0, 1.0)

                        tcp_in_camera = compute_tcp_in_camera(
                            *pose_tuple, extrinsic_t, extrinsic_q,
                        )

                        # Step 2: Build work frame
                        wf = _build_work_frame(work_frame_config, hand)

                        # Step 3: Compute arm-base TCP pose
                        arm_base_result = compute_arm_base_tcp_pose(
                            tcp_x=tcp_in_camera[0],
                            tcp_y=tcp_in_camera[1],
                            tcp_z=tcp_in_camera[2],
                            tcp_qx=tcp_in_camera[3],
                            tcp_qy=tcp_in_camera[4],
                            tcp_qz=tcp_in_camera[5],
                            tcp_qw=tcp_in_camera[6],
                            work_frame=wf,
                            algo=algo,
                        )

                        # Step 4: Encode as ROS2 message payload
                        arm_base_pose_tuple = (
                            arm_base_result.position_m["x"],
                            arm_base_result.position_m["y"],
                            arm_base_result.position_m["z"],
                            arm_base_result.orientation["x"],
                            arm_base_result.orientation["y"],
                            arm_base_result.orientation["z"],
                            arm_base_result.orientation["w"],
                        )
                        encoded_arm_base = codec.encode(
                            schema,
                            inject_pose_fields(decoded_pose, pose_stream.msg_type, arm_base_pose_tuple),
                        )
                        arm_base_tcp_pose_payloads[topic].append(encoded_arm_base)

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
        arm_base_tcp_pose_payloads_by_topic=arm_base_tcp_pose_payloads,
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
    arm_base_iterators = {
        topic: iter(payloads)
        for topic, payloads in artifacts.arm_base_tcp_pose_payloads_by_topic.items()
        if payloads
    }
    gripper_iterators = {topic: iter(payloads) for topic, payloads in artifacts.gripper_payloads_by_image_topic.items()}

    pose_output_counts = {topic: 0 for topic in pose_streams}
    camera_common_output_counts: dict[str, int] = {topic: 0 for topic in camera_common_iterators}
    tcp_common_output_counts: dict[str, int] = {topic: 0 for topic in tcp_common_iterators}
    arm_base_output_counts: dict[str, int] = {topic: 0 for topic in arm_base_iterators}
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

                if channel.topic in arm_base_iterators:
                    cached_schema, cached_channel = pose_schema_cache.get(channel.topic, (schema, channel))
                    stream = pose_streams[channel.topic]
                    if stream.output_arm_base_tcp_pose:
                        arm_base_channel_id = output_builder.register_pose_output_channel(
                            stream.output_arm_base_tcp_pose,
                            cached_schema,
                            cached_channel,
                        )
                        writer.add_message(
                            channel_id=arm_base_channel_id,
                            log_time=message.log_time,
                            publish_time=message.publish_time,
                            sequence=message.sequence,
                            data=next(arm_base_iterators[channel.topic]),
                        )
                        arm_base_output_counts[channel.topic] += 1

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
    for topic, iterator in arm_base_iterators.items():
        if next(iterator, None) is not None:
            raise ProcessingError(f'arm base tcp pose topic "{topic}" left unread payloads')
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
    extra_topics += sum(1 for s in config.pose_streams if s.output_arm_base_tcp_pose)
    output_topic_count = input_topic_count + extra_topics
    pose_topic_stats = tuple(
        PoseTopicStats(
            topic=stream.output_topic,
            input_count=inventory[stream.input_topic].message_count,
            output_count=pose_output_counts[stream.input_topic],
        )
        for stream in config.pose_streams
    )
    arm_base_topic_stats = tuple(
        PoseTopicStats(
            topic=stream.output_arm_base_tcp_pose,
            input_count=inventory[stream.input_topic].message_count,
            output_count=arm_base_output_counts.get(stream.input_topic, 0),
            hand=(
                "left" if "_left" in stream.input_topic
                else "right" if "_right" in stream.input_topic
                else None
            ),
            frame_id=(
                "left_arm_base" if "_left" in stream.input_topic
                else "right_arm_base" if "_right" in stream.input_topic
                else None
            ),
        )
        for stream in config.pose_streams
        if stream.output_arm_base_tcp_pose
    )
    report = FileProcessingReport(
        input_file=str(input_path),
        output_file=str(output_path),
        status="success",
        input_topic_count=input_topic_count,
        output_topic_count=output_topic_count,
        pose_topics=pose_topic_stats + arm_base_topic_stats,
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
