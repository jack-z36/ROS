"""Read-only MCAP topic metadata extractor for Scene 3 input inventory.

This module extracts raw topic facts from an MCAP file without applying
any business rules, validation logic, or hard fail decisions. It is the
repo-layer helper for the MCAP_A input validation service.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from mcap.reader import make_reader

from repo.ros2_codec import Ros2DynamicCodec, select_alignment_timestamp


@dataclass
class TopicFact:
    """Raw topic metadata extracted from an MCAP file.

    All fields express facts about the topic as stored in the MCAP,
    without interpretation or validation.
    """

    topic: str
    message_type: str
    sample_count: int
    timestamps: list[int] = field(default_factory=list)


def extract_topic_facts(mcap_path: str | Path) -> list[TopicFact]:
    """Read MCAP file and extract raw topic facts.

    Args:
        mcap_path: Path to the MCAP file.

    Returns:
        List of TopicFact, one per unique topic in the MCAP.

    Raises:
        FileNotFoundError: If the MCAP file does not exist.
        ValueError: If the file cannot be read as MCAP.
    """
    path = Path(mcap_path)
    if not path.exists():
        raise FileNotFoundError(f"MCAP file not found: {path}")

    topic_data: dict[str, dict] = {}
    codec = Ros2DynamicCodec()

    try:
        with path.open("rb") as fh:
            reader = make_reader(fh)
            for schema, channel, message in reader.iter_messages(log_time_order=False):
                if channel.topic not in topic_data:
                    topic_data[channel.topic] = {
                        "message_type": schema.name if schema else "unknown",
                        "timestamps": [],
                    }
                selected_timestamp = select_alignment_timestamp(
                    schema,
                    message,
                    codec=codec,
                )
                topic_data[channel.topic]["timestamps"].append(
                    selected_timestamp.timestamp_ns
                )
    except Exception as exc:
        raise ValueError(f"Failed to read MCAP file {path}: {exc}") from exc

    facts: list[TopicFact] = []
    for topic_name, data in topic_data.items():
        facts.append(
            TopicFact(
                topic=topic_name,
                message_type=data["message_type"],
                sample_count=len(data["timestamps"]),
                timestamps=sorted(data["timestamps"]),
            )
        )
    facts.sort(key=lambda f: f.topic)
    return facts
