"""ROS2 dynamic message decoding/encoding utilities for MCAP payloads."""

from __future__ import annotations

import textwrap
from types import SimpleNamespace
from typing import Any

import numpy as np
from mcap.records import Message, Schema
from mcap_ros2.decoder import Decoder
from mcap_ros2.writer import serialize_dynamic

from schemas.ros2_schemas import STD_MSGS_FLOAT32


class Ros2CodecError(RuntimeError):
    """Raised when a ROS2 MCAP payload cannot be decoded or re-encoded."""


SUPPORTED_POSE_TYPES = {
    "nav_msgs/msg/Odometry",
    "geometry_msgs/msg/PoseStamped",
}

SUPPORTED_IMAGE_TYPES = {
    "sensor_msgs/msg/Image",
}

SUPPORTED_IMAGE_ENCODINGS = {
    "bgr8",
    "rgb8",
    "mono8",
}


class Ros2DynamicCodec:
    """Caches decoders/encoders for ROS2 dynamic message handling."""

    def __init__(self):
        self.decoder = Decoder()
        self._encoder_cache: dict[int, Any] = {}
        self._schema_cache: dict[int, Schema] = {}
        self._float32_encoder = serialize_dynamic("std_msgs/msg/Float32", STD_MSGS_FLOAT32)["std_msgs/msg/Float32"]

    def decode(self, schema: Schema, message: Message) -> Any:
        try:
            return self.decoder.decode(normalize_ros2_schema(schema, self._schema_cache), message)
        except Exception as exc:
            raise Ros2CodecError(f'failed to decode "{schema.name}" message: {exc}') from exc

    def encode(self, schema: Schema, ros_message: Any) -> bytes:
        normalized_schema = normalize_ros2_schema(schema, self._schema_cache)
        encoder = self._encoder_cache.get(normalized_schema.id)
        try:
            if encoder is None:
                encoder = serialize_dynamic(
                    normalized_schema.name,
                    normalized_schema.data.decode("utf-8"),
                )[normalized_schema.name]
                self._encoder_cache[normalized_schema.id] = encoder
            return encoder(ros_message)
        except Exception as exc:
            raise Ros2CodecError(f'failed to encode "{schema.name}" message: {exc}') from exc

    def encode_float32(self, value: float) -> bytes:
        return self._float32_encoder(SimpleNamespace(data=float(value)))


def normalize_ros2_schema(schema: Schema, cache: dict[int, Schema] | None = None) -> Schema:
    """Return a schema whose ROS2 message definition has parser-friendly indentation."""

    if schema.encoding != "ros2msg":
        return schema
    if cache is not None and schema.id in cache:
        return cache[schema.id]

    schema_text = schema.data.decode("utf-8")
    normalized_text = textwrap.dedent(schema_text).strip() + "\n"
    if normalized_text == schema_text:
        normalized_schema = schema
    else:
        normalized_schema = Schema(
            id=schema.id,
            name=schema.name,
            encoding=schema.encoding,
            data=normalized_text.encode("utf-8"),
        )
    if cache is not None:
        cache[schema.id] = normalized_schema
    return normalized_schema


def extract_pose_fields(ros_message: Any, msg_type: str) -> tuple[float, float, float, float, float, float, float]:
    if msg_type == "nav_msgs/msg/Odometry":
        pose = ros_message.pose.pose
    elif msg_type == "geometry_msgs/msg/PoseStamped":
        pose = ros_message.pose
    else:
        raise Ros2CodecError(f'unsupported pose message type "{msg_type}"')

    position = pose.position
    orientation = pose.orientation
    return (
        float(position.x),
        float(position.y),
        float(position.z),
        float(orientation.x),
        float(orientation.y),
        float(orientation.z),
        float(orientation.w),
    )


def inject_pose_fields(
    ros_message: Any,
    msg_type: str,
    transformed_pose: tuple[float, float, float, float, float, float, float],
) -> Any:
    if msg_type == "nav_msgs/msg/Odometry":
        pose = ros_message.pose.pose
    elif msg_type == "geometry_msgs/msg/PoseStamped":
        pose = ros_message.pose
    else:
        raise Ros2CodecError(f'unsupported pose message type "{msg_type}"')

    x, y, z, qx, qy, qz, qw = transformed_pose
    pose.position.x = x
    pose.position.y = y
    pose.position.z = z
    pose.orientation.x = qx
    pose.orientation.y = qy
    pose.orientation.z = qz
    pose.orientation.w = qw
    return ros_message


def inject_tactile_fields(
    ros_message: Any,
    filtered_matrix: list[list[float]],
) -> Any:
    """Replace tactile pressure data with filtered values.

    Works with ``hwk_pressure_interfaces/msg/PressureFrame`` which has a
    mutable ``data`` flat list field.  The ``rows`` / ``cols`` fields are
    preserved as-is.
    """
    flat_data = [float(cell) for row in filtered_matrix for cell in row]
    ros_message.data = flat_data
    return ros_message


def image_message_to_ndarray(ros_message: Any, msg_type: str) -> np.ndarray:
    if msg_type not in SUPPORTED_IMAGE_TYPES:
        raise Ros2CodecError(f'unsupported image message type "{msg_type}"')

    encoding = str(ros_message.encoding)
    if encoding not in SUPPORTED_IMAGE_ENCODINGS:
        raise Ros2CodecError(
            f'unsupported image encoding "{encoding}" (supported: {sorted(SUPPORTED_IMAGE_ENCODINGS)})'
        )

    height = int(ros_message.height)
    width = int(ros_message.width)
    step = int(ros_message.step)
    raw = bytes(ros_message.data)

    if encoding in {"bgr8", "rgb8"}:
        channels = 3
        row_width = width * channels
        expected_min_length = height * step
        if len(raw) < expected_min_length:
            raise Ros2CodecError("image payload shorter than expected from height/step")
        flat = np.frombuffer(raw, dtype=np.uint8)
        rows = flat.reshape(height, step)[:, :row_width]
        image = rows.reshape(height, width, channels)
        if encoding == "rgb8":
            return image[:, :, ::-1]
        return image

    expected_min_length = height * step
    if len(raw) < expected_min_length:
        raise Ros2CodecError("image payload shorter than expected from height/step")
    flat = np.frombuffer(raw, dtype=np.uint8)
    rows = flat.reshape(height, step)[:, :width]
    return rows
