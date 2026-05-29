"""Field alignment result, strategy, and derived value types for Scene 3.

Defines in-memory types exchanged between the multi-strategy field
aligner (Module 4) and downstream consumers (Modules 5/6).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TypedDict


class FieldAlignmentStrategyMethod(str, Enum):
    """Alignment method identifiers per L2 FieldAlignmentStrategy.

    Values follow L2 FieldAlignmentStrategy data definition.
    """

    nearest_neighbor = "nearest_neighbor"
    interpolation_slerp = "interpolation_slerp"
    window_aggregate = "window_aggregate"
    follow_image_nearest = "follow_image_nearest"


@dataclass
class FieldAlignmentStrategy:
    """Strategy contract for aligning a single field type.

    Combines a method identifier with optional alignment parameters
    (thresholds, window config, fallback behavior) per the L2
    FieldAlignmentStrategy data definition.
    """

    method: str
    max_dt_ms: float | None = None
    window_half_width_ns: int | None = None
    fallback_method: str | None = None


class DerivedAlignmentValue(TypedDict, total=False):
    """Lightweight derived alignment value.

    Flexible TypedDict accommodating pose interpolation, gripper
    nearest-neighbor, and tactile window aggregate results.
    Intentionally non-exhaustive — consumers can extend as needed.
    Not used for images (image payloads use message_ref only).

    Per L2 FieldAlignmentResult validity rules:
    - pose interpolation / slerp → position + orientation fields
    - gripper nearest → gripper_width
    - tactile window aggregate → mean/std/min/max + sample_count
    """

    # Pose interpolation result
    position_x: float
    position_y: float
    position_z: float
    orientation_qx: float
    orientation_qy: float
    orientation_qz: float
    orientation_qw: float
    # Gripper nearest value
    gripper_width: float
    # Tactile window aggregate
    tactile_mean: float
    tactile_std: float
    tactile_min: float
    tactile_max: float
    sample_count: int


@dataclass
class FieldAlignmentResult:
    """Per-step per-field alignment result.

    The primary in-memory type exchanged between the multi-strategy
    field aligner (Module 4) and downstream consumers (Modules 5/6).

    Captures source tracking, alignment metadata, interpolation
    neighbors, window stats, fallback info, and lightweight derived
    values per the L2 FieldAlignmentResult data definition.

    Images only store a message_ref (no inline payload). Pose/gripper/
    tactile derived values may be inlined via derived_value.
    """

    # --- Required fields ---
    step_index: int
    step_time_ns: int
    field_name: str
    status: str  # FieldAlignmentStatus value (e.g. "aligned", "interpolated")
    alignment_method: str  # Actual method used (e.g. "nearest_neighbor")

    # --- Source tracking ---
    source_topic: str | None = None
    output_topic: str | None = None
    source_time_ns: int | None = None
    dt_ms: float | None = None

    # --- Interpolation neighbors ---
    neighbor_before_time_ns: int | None = None
    neighbor_after_time_ns: int | None = None

    # --- Window aggregate ---
    window_start_time_ns: int | None = None
    window_end_time_ns: int | None = None
    sample_count: int | None = None
    coverage_ratio: float | None = None

    # --- Fallback ---
    fallback_reason: str | None = None

    # --- Payload references ---
    message_ref: str | None = None
    derived_value: dict | None = None  # DerivedAlignmentValue-compatible

    # --- Debug info ---
    notes: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate field constraints.

        Per L2 FieldAlignmentResult validity rules:
        - step_index must be >= 0.
        - When status='fallback_nearest', fallback_reason is required.
        - When status='aggregated', window_start_time_ns and
          window_end_time_ns are required.
        """
        if self.step_index < 0:
            raise ValueError(
                f"step_index must be >= 0, got {self.step_index}"
            )
        if self.status == "fallback_nearest" and not self.fallback_reason:
            raise ValueError(
                "fallback_reason is required when status='fallback_nearest'"
            )
        if self.status == "aggregated":
            if self.window_start_time_ns is None:
                raise ValueError(
                    "window_start_time_ns is required when "
                    "status='aggregated'"
                )
            if self.window_end_time_ns is None:
                raise ValueError(
                    "window_end_time_ns is required when "
                    "status='aggregated'"
                )
