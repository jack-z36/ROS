"""Aligned MCAP writer for Scene 3.

Writes aligned field results into an MCAP file with step timestamps.
Only statuses in {aligned, interpolated, aggregated, fallback_nearest}
produce messages. Fields with missing_time, timeout, or unavailable status
are silently skipped — no empty messages, no reuse of previous valid values.

Per L3 service_s3_021.
"""

from __future__ import annotations

import os
import re
from typing import Any

from mcap.reader import make_reader
from mcap.writer import CompressionType, Writer

from schemas.field_alignment import FieldAlignmentResult
from schemas.step_timeline import StepTimeline

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VALID_WRITE_STATUSES: set[str] = {
    "aligned",
    "interpolated",
    "aggregated",
    "fallback_nearest",
}

MESSAGE_REF_PATTERN = re.compile(r"mcap://(.+)/msg_(\d+)$")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ensure_parent(output_path: str) -> None:
    """Create parent directory of output_path if it does not exist."""
    parent = os.path.dirname(os.path.abspath(output_path))
    if parent and not os.path.exists(parent):
        os.makedirs(parent, exist_ok=True)


def _parse_message_ref(message_ref: str) -> tuple[str, int] | None:
    """Parse a message_ref URI into (topic, index).

    Expected format: ``mcap://<topic>/msg_<index>``.
    Example: ``mcap:///gopro_left/image_raw/msg_0``.
    Returns ``None`` if the ref cannot be parsed.
    """
    match = MESSAGE_REF_PATTERN.match(message_ref)
    if match:
        return match.group(1), int(match.group(2))
    return None


def _build_source_payload_index(
    source_mcap_path: str,
) -> dict[str, list[tuple[int, bytes]]]:
    """Read source MCAP and index payloads by topic.

    Returns ``{topic: [(publish_time, payload), ...]}``.
    """
    index: dict[str, list[tuple[int, bytes]]] = {}
    with open(source_mcap_path, "rb") as f:
        reader = make_reader(f)
        for _, channel, message in reader.iter_messages(log_time_order=False):
            if channel.topic not in index:
                index[channel.topic] = []
            index[channel.topic].append((message.publish_time, message.data))
    return index


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def write_aligned_mcap(
    source_mcap_path: str,
    results: list[FieldAlignmentResult],
    timeline: StepTimeline,
    output_path: str,
) -> str:
    """Write aligned field results into an MCAP file.

    Only results with a status in *VALID_WRITE_STATUSES* produce messages.
    Results with ``missing_time``, ``timeout``, or ``unavailable`` status
    are silently skipped — no empty placeholders, no reuse of previous
    valid values.

    Args:
    source_mcap_path:
        Path to the source MCAP_A (used for schema and payload lookup).
        results:
            List of per-step per-field alignment results.
        timeline:
            The :class:`StepTimeline` used for alignment (provides step
            timestamp context).
        output_path:
            Destination path for the aligned MCAP.

    Returns:
        ``output_path`` on success.

    Raises:
        ValueError: If any required argument is ``None``.
        OSError:    If *output_path* cannot be written.
    """
    # ---- Validation ----
    if source_mcap_path is None:
        raise ValueError("source_mcap_path must not be None")
    if results is None:
        raise ValueError("results must not be None")
    if timeline is None:
        raise ValueError("timeline must not be None")
    if output_path is None:
        raise ValueError("output_path must not be None")

    # ---- Index source MCAP payloads ----
    source_payloads = _build_source_payload_index(source_mcap_path)

    _ensure_parent(output_path)

    # ---- Write output MCAP ----
    with open(output_path, "wb") as f:
        writer = Writer(f, compression=CompressionType.NONE)
        writer.start()

        # Registry: topic -> (schema_id, channel_id)
        schema_registry: dict[str, int] = {}
        channel_registry: dict[str, int] = {}

        for result in results:
            # Step 1 — filter by status
            if result.status not in VALID_WRITE_STATUSES:
                continue

            # Step 2 — determine topic
            topic = result.output_topic or result.source_topic
            if not topic:
                continue

            # Step 3 — resolve payload
            payload = _resolve_payload(result, source_payloads)
            if payload is None:
                continue

            # Step 4 — register schema/channel if first use of this topic
            if topic not in channel_registry:
                schema_id = _register_topic_schema(
                    writer, topic, source_payloads, schema_registry
                )
                channel_id = writer.register_channel(
                    topic,
                    message_encoding="cdr",
                    schema_id=schema_id,
                )
                channel_registry[topic] = channel_id
            else:
                channel_id = channel_registry[topic]

            # Step 5 — write message at step timestamp
            step_time_ns = result.step_time_ns
            writer.add_message(
                channel_id=channel_id,
                log_time=step_time_ns,
                publish_time=step_time_ns,
                sequence=0,
                data=payload,
            )

        writer.finish()

    return output_path


def _resolve_payload(
    result: FieldAlignmentResult,
    source_payloads: dict[str, list[tuple[int, bytes]]],
) -> bytes | None:
    """Resolve the payload for a FieldAlignmentResult.

    Priority:
    1. If ``derived_value`` is set → encode it (for pose/gripper/tactile).
    2. If ``message_ref`` is set → copy payload from source MCAP
       (typically for image fields).
    3. Otherwise → ``None`` (unresolvable, message skipped).
    """
    # Try derived value first
    if result.derived_value is not None:
        return _encode_derived_value(result.derived_value, result.output_topic)

    # Fall back to message_ref (source payload copy)
    if result.message_ref is not None:
        return _resolve_message_ref_payload(result.message_ref, source_payloads)

    return None


def _resolve_message_ref_payload(
    message_ref: str,
    source_payloads: dict[str, list[tuple[int, bytes]]],
) -> bytes | None:
    """Copy a payload from source MCAP using the message_ref URI.

    The ``message_ref`` format is ``mcap://<topic>/msg_<index>``.
    """
    parsed = _parse_message_ref(message_ref)
    if parsed is None:
        return None
    topic, msg_idx = parsed
    entries = source_payloads.get(topic)
    if entries is None or msg_idx >= len(entries):
        return None
    return entries[msg_idx][1]


def _register_topic_schema(
    writer: Writer,
    topic: str,
    source_payloads: dict[str, list[tuple[int, bytes]]],
    schema_registry: dict[str, int],
) -> int:
    """Register a schema for *topic* in the output writer.

    Uses a generic ROS2 schema placeholder since the aligned MCAP does not
    need to replicate the exact source schema; it only needs a compatible
    encoding so downstream readers can decode the message.

    Returns the registered schema id.
    """
    generic_schema_name = "example/msg/Bytes"
    generic_schema_text = b"uint8[] data"

    if generic_schema_name not in schema_registry:
        sid = writer.register_schema(
            generic_schema_name,
            "ros2msg",
            generic_schema_text,
        )
        schema_registry[generic_schema_name] = sid

    return schema_registry[generic_schema_name]


def _encode_derived_value(
    derived_value: dict[str, Any],
    output_topic: str | None,
) -> bytes | None:
    """Encode a *derived_value* dict into a ROS2 serialized payload.

    Currently supports:
    - Gripper: ``{"gripper_width": float}`` → ``std_msgs/msg/Float32``
    - Pose: ``{"position_x/y/z", "orientation_qx/qy/qz/qw"}`` → not yet
      implemented (returns ``None`` for now).

    Per L3 constraints: image fields do NOT use *derived_value* (they use
    *message_ref*), so only lightweight derived values are handled here.
    """
    # Gripper width
    if "gripper_width" in derived_value:
        from mcap_ros2.writer import serialize_dynamic

        width = float(derived_value["gripper_width"])
        encoder = serialize_dynamic(
            "std_msgs/msg/Float32",
            "float32 data",
        )
        from types import SimpleNamespace

        ros_msg = SimpleNamespace(data=width)
        return encoder[list(encoder.keys())[0]](ros_msg)

    # Pose — not yet implemented (returns None so message is skipped)
    # Tactile — not yet implemented
    return None
