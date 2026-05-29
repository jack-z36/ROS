"""Step timeline, field alignment status, and alignment index types for Scene 3."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class StepTimelineGenerationStatus(str, Enum):
    """Status of a step timeline generation attempt.

    Values follow L2 StepTimelineGenerationSummary data definition.
    """

    generated = "generated"
    failed = "failed"


class StepTimelineGenerationFailureReason(str, Enum):
    """Reasons why step timeline generation failed.

    Values follow L2 StepTimelineGenerationSummary failure_reasons definition.
    """

    input_not_consumable = "input_not_consumable"
    missing_baseline_intersection = "missing_baseline_intersection"
    invalid_target_step_hz = "invalid_target_step_hz"
    invalid_time_range = "invalid_time_range"


class TimestampRoundingPolicy(str, Enum):
    """Policy for rounding non-integer-ns step periods.

    Values follow L2 StepTimelineGenerationSummary timestamp_rounding_policy.
    """

    rational_accumulation_round_to_ns = "rational_accumulation_round_to_ns"


@dataclass
class StepTimelineGenerationSummary:
    """Summary of a step timeline generation attempt.

    Captures the outcome (status), failure reasons (if any), references
    to upstream artifacts, and snapshot of generation parameters.
    Success or failure — always produced by the unified step timeline generator.

    Field descriptions follow L2 StepTimelineGenerationSummary data definition.
    """

    status: str
    failure_reasons: list[str]
    source_topic_catalog_ref: str
    input_validation_summary_ref: str
    config_ref: str
    timeline_ref: str | None
    target_step_hz: int | float
    baseline_intersection_start_ns: int | None
    baseline_intersection_end_ns: int | None
    timestamp_rounding_policy: str = "rational_accumulation_round_to_ns"
    include_start: bool = True
    force_include_end: bool = False
    step_count: int = 0
    first_step_time_ns: int | None = None
    last_step_time_ns: int | None = None
    created_at: str | None = None
    run_id: str | None = None

    def __post_init__(self) -> None:
        """Validate status and failure_reasons constraints."""
        if self.status not in ("generated", "failed"):
            raise ValueError(
                f"status must be 'generated' or 'failed', got {self.status!r}"
            )


class FieldAlignmentStatus(str, Enum):
    """Status of a single step-field alignment result.

    Values follow L2 FieldAlignmentStatus data definition.
    """

    aligned = "aligned"
    interpolated = "interpolated"
    aggregated = "aggregated"
    fallback_nearest = "fallback_nearest"
    missing_time = "missing_time"
    timeout = "timeout"
    unavailable = "unavailable"
    invalid_input = "invalid_input"


@dataclass
class StepTimelineEntry:
    """A single step entry within a StepTimeline."""

    step_index: int
    step_time_ns: int


@dataclass
class StepTimeline:
    """Unified step timeline for Scene 3 alignment.

    Represents the common reference timeline generated from the intersection
    of baseline image time ranges, with a uniform step frequency.
    """

    timeline_id: str
    target_step_hz: int = 15
    start_time_ns: int = 0
    end_time_ns: int = 0
    step_count: int = 0
    range_policy: str = "required_field_intersection"
    baseline_policy: str = "stereo_image_intersection"
    steps: list[StepTimelineEntry] = field(default_factory=list)


@dataclass
class StepTimelineSummary:
    """Summary statistics for a StepTimeline.

    Used by report generators to describe the timeline characteristics.
    """

    timeline_id: str
    target_step_hz: int
    actual_step_count: int
    start_time_ns: int
    end_time_ns: int
    range_policy: str = "required_field_intersection"
    baseline_policy: str = "stereo_image_intersection"

    @property
    def duration_ns(self) -> int:
        """Compute duration in nanoseconds."""
        return self.end_time_ns - self.start_time_ns


@dataclass
class AlignmentIndexRecord:
    """A single record in the alignment index (one per step-field).

    Maps to a row in alignment_index.parquet, capturing the alignment
    fact for one field at one step.
    """

    step_index: int
    step_time_ns: int
    field_name: str
    source_topic: str | None = None
    output_topic: str | None = None
    source_time_ns: int | None = None
    alignment_method: str = "nearest_neighbor"
    status: FieldAlignmentStatus = FieldAlignmentStatus.missing_time
    dt_ms: float | None = None
    neighbor_before_time_ns: int | None = None
    neighbor_after_time_ns: int | None = None
    window_start_time_ns: int | None = None
    window_end_time_ns: int | None = None
    sample_count: int | None = None
    coverage_ratio: float | None = None
    fallback_reason: str | None = None
    message_ref: str | None = None


# Parquet schema definition for alignment_index.parquet
# Maps column names to their logical Parquet type strings.
AlignmentIndexSchema: dict[str, str] = {
    "step_index": "int64",
    "step_time_ns": "int64",
    "field_name": "string",
    "source_topic": "string",
    "output_topic": "string",
    "source_time_ns": "int64",
    "alignment_method": "string",
    "status": "string",
    "dt_ms": "float64",
    "neighbor_before_time_ns": "int64",
    "neighbor_after_time_ns": "int64",
    "window_start_time_ns": "int64",
    "window_end_time_ns": "int64",
    "sample_count": "int64",
    "coverage_ratio": "float64",
    "fallback_reason": "string",
    "message_ref": "string",
}
