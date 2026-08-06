"""Scene 2 stream inventory and shared runtime context contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


SCENE2_STREAM_MODALITIES = {"pose", "gripper", "tactile"}


@dataclass(frozen=True)
class Scene2StreamSpec:
    topic: str
    modality: str
    required: bool

    def __post_init__(self) -> None:
        if not self.topic.startswith("/"):
            raise ValueError("scene2 stream topic must be absolute")
        if self.modality not in SCENE2_STREAM_MODALITIES:
            raise ValueError(f"unsupported scene2 modality: {self.modality}")


DEFAULT_SCENE2_STREAMS: tuple[Scene2StreamSpec, ...] = (
    Scene2StreamSpec("/baton_mini_left/tcp_pose", "pose", True),
    Scene2StreamSpec("/baton_mini_right/tcp_pose", "pose", True),
    Scene2StreamSpec("/gopro_left/gripper_width", "gripper", True),
    Scene2StreamSpec("/gopro_right/gripper_width", "gripper", True),
    Scene2StreamSpec("/pressure/left_hand/gripper_1", "tactile", False),
    Scene2StreamSpec("/pressure/left_hand/gripper_2", "tactile", False),
    Scene2StreamSpec("/pressure/right_hand/gripper_1", "tactile", False),
    Scene2StreamSpec("/pressure/right_hand/gripper_2", "tactile", False),
)


@dataclass(frozen=True)
class Scene2StreamInventory:
    configured_streams: tuple[Scene2StreamSpec, ...]
    present_topics: tuple[str, ...]
    missing_required_topics: tuple[str, ...] = ()
    missing_optional_topics: tuple[str, ...] = ()
    schema_by_topic: dict[str, str] = field(default_factory=dict)
    message_count_by_topic: dict[str, int] = field(default_factory=dict)


@dataclass
class Scene2RunContext:
    run_id: str
    input_cleaned_mcap: str
    input_identity: dict[str, Any]
    config_snapshot: dict[str, Any]
    stream_inventory: Scene2StreamInventory | None = None

