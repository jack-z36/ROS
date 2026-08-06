"""Fail-closed Scene 2 MCAP inventory and whitelist decoder."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

from mcap.reader import make_reader

from repo.config.mcap_process_config import AppConfig
from repo.ros2_codec import Ros2DynamicCodec, extract_pose_fields, select_alignment_timestamp
from schemas.scene2_samples import GripperSample, PoseSample, Scene2SignalSamples, TactilePressureFrame
from schemas.scene2_streams import Scene2StreamInventory


SUPPORTED_SCHEMAS = {
    "pose": {"nav_msgs/msg/Odometry", "geometry_msgs/msg/PoseStamped"},
    "gripper": {"std_msgs/msg/Float32"},
    "tactile": {"hwk_pressure_interfaces/msg/PressureFrame", "data_clean/msg/TactilePressureFrame"},
}


def load_scene2_signal_samples(cleaned_mcap_path: str | Path, config: AppConfig) -> Scene2SignalSamples:
    path = Path(cleaned_mcap_path)
    if not path.is_file():
        raise FileNotFoundError(f"cleaned MCAP not found: {path}")

    specs = {spec.topic: spec for spec in config.scene2_streams}
    if len(specs) != len(config.scene2_streams):
        raise ValueError("duplicate_scene2_stream_topic")

    pose: list[PoseSample] = []
    gripper: list[GripperSample] = []
    tactile: list[TactilePressureFrame] = []
    counts: dict[str, int] = defaultdict(int)
    schema_by_topic: dict[str, str] = {}
    codec = Ros2DynamicCodec()

    with path.open("rb") as fh:
        reader = make_reader(fh)
        for schema, channel, message in reader.iter_messages(log_time_order=False):
            spec = specs.get(channel.topic)
            if spec is None:
                continue
            message_index = counts[channel.topic]
            counts[channel.topic] += 1
            if schema is None:
                raise ValueError(f"scene2_schema_missing: {channel.topic}")
            if schema.name not in SUPPORTED_SCHEMAS[spec.modality]:
                raise ValueError(
                    f"unsupported_scene2_schema: topic={channel.topic} modality={spec.modality} schema={schema.name}"
                )
            previous_schema = schema_by_topic.setdefault(channel.topic, schema.name)
            if previous_schema != schema.name:
                raise ValueError(f"scene2_schema_changed_within_topic: {channel.topic}")

            decoded = codec.decode(schema, message)
            selected = select_alignment_timestamp(schema, message, codec=codec, decoded_message=decoded)
            identity = {
                "time_domain": selected.time_domain,
                "log_time_ns": int(message.log_time),
                "publish_time_ns": int(message.publish_time),
                "sequence": int(message.sequence),
                "source_channel_id": int(channel.id),
            }
            if spec.modality == "pose":
                x, y, z, qx, qy, qz, qw = extract_pose_fields(decoded, schema.name)
                pose.append(PoseSample(channel.topic, selected.timestamp_ns, message_index, (x, y, z), (qx, qy, qz, qw), **identity))
            elif spec.modality == "gripper":
                gripper.append(GripperSample(channel.topic, selected.timestamp_ns, message_index, float(decoded.data), **identity))
            else:
                tactile.append(_tactile_frame(channel.topic, selected.timestamp_ns, message_index, decoded, identity))

    present = tuple(spec.topic for spec in config.scene2_streams if counts.get(spec.topic, 0) > 0)
    missing_required = tuple(spec.topic for spec in config.scene2_streams if spec.required and not counts.get(spec.topic, 0))
    missing_optional = tuple(spec.topic for spec in config.scene2_streams if not spec.required and not counts.get(spec.topic, 0))
    inventory = Scene2StreamInventory(
        configured_streams=config.scene2_streams,
        present_topics=present,
        missing_required_topics=missing_required,
        missing_optional_topics=missing_optional,
        schema_by_topic=schema_by_topic,
        message_count_by_topic=dict(counts),
    )
    if missing_required:
        raise ValueError(f"missing_required_scene2_topics: {', '.join(missing_required)}")
    return Scene2SignalSamples(pose=pose, gripper=gripper, tactile=tactile, inventory=inventory)


def _tactile_frame(
    topic: str,
    timestamp_ns: int,
    message_index: int,
    message: Any,
    identity: dict[str, Any],
) -> TactilePressureFrame:
    rows = int(getattr(message, "rows", getattr(message, "height", 0)))
    cols = int(getattr(message, "cols", getattr(message, "width", 0)))
    parts = [part for part in topic.strip("/").split("/") if part]
    return TactilePressureFrame(
        topic=topic,
        timestamp_ns=timestamp_ns,
        message_index=message_index,
        hand=parts[-2] if len(parts) >= 2 else "unknown",
        gripper=parts[-1] if parts else "unknown",
        rows=rows,
        cols=cols,
        data=[int(value) for value in list(getattr(message, "data", []))],
        **identity,
    )
