"""Scene 3 alignment config and target field mapping types."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class AlignmentModality(str, Enum):
    """Modality category for a target field."""

    IMAGE = "image"
    POSE = "pose"
    TACTILE = "tactile"
    GRIPPER = "gripper"


class AlignmentSide(str, Enum):
    """Side for stereo / symmetric fields."""

    LEFT = "left"
    RIGHT = "right"


@dataclass
class TargetFieldMapping:
    """Mapping from an MCAP_A topic to an aligned output field."""

    field_name: str
    source_topic: str
    output_topic: str
    message_type: str
    modality: AlignmentModality
    side: AlignmentSide | None = None
    required_for_timeline: bool = False
    strategy: str = "nearest_neighbor"
    max_dt_ms: int | None = None


@dataclass
class Scene3AlignmentConfig:
    """Scene 3 alignment configuration and default values."""

    target_step_hz: int = 15
    baseline_image_topics: list[str] = field(
        default_factory=lambda: [
            "/gopro_left/image_raw",
            "/gopro_right/image_raw",
        ]
    )
    required_timeline_fields: list[str] = field(
        default_factory=lambda: ["image_left", "image_right"]
    )
    target_fields: list[TargetFieldMapping] = field(default_factory=list)
    image_max_dt_ms: int | None = None
    pose_strategy: str = "interpolation_slerp"
    pose_fallback_strategy: str = "nearest_neighbor"
    tactile_strategy: str = "window_aggregate"
    gripper_strategy: str = "follow_image_nearest"
    output_dir: str = "asset/阶段二：数据清洗/dev/03_aligned_mcap"

    def __post_init__(self) -> None:
        """Validate config and compute derived defaults."""
        if self.target_step_hz <= 0:
            raise ValueError(
                f"target_step_hz must be positive, got {self.target_step_hz}"
            )
        if not self.baseline_image_topics:
            raise ValueError(
                "baseline_image_topics must not be empty"
            )
        if self.image_max_dt_ms is not None and self.image_max_dt_ms <= 0:
            raise ValueError(
                f"image_max_dt_ms must be positive when explicitly set, "
                f"got {self.image_max_dt_ms}"
            )
        # Compute default image_max_dt_ms when not explicitly configured
        if self.image_max_dt_ms is None:
            self.image_max_dt_ms = int(1000 / self.target_step_hz / 2)
