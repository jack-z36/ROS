from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .reliability import SignalSampleRef
from .repair import SignalRepairResult


class PoseFilterAlgorithm(str, Enum):
    SAVITZKY_GOLAY = "savgol"


class PoseFilterSampleStatus(str, Enum):
    FILTERED = "filtered"
    KEPT_ORIGINAL = "kept_original"
    SKIPPED_BOUNDARY = "skipped_boundary"
    FILTER_REJECTED_BY_GUARD = "filter_rejected_by_guard"


@dataclass
class PoseFilterConfig:
    algorithm: PoseFilterAlgorithm = PoseFilterAlgorithm.SAVITZKY_GOLAY
    window_duration_ms: int = 200
    polyorder: int = 2
    position_guard_max_delta_m: float = 0.02
    orientation_guard_max_delta_deg: float = 5
    timestamp_policy: str = "preserve_original"


@dataclass
class PoseFilterInputSequence:
    source_topic: str
    input_sequence_ref: str | dict[str, Any]
    input_repair_result_ref: SignalRepairResult | str
    modality: str = "pose"
    frame_id: str = "source_frame"
    sample_refs: list[SignalSampleRef] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Reject coordinate-frame semantics removed from the production route."""
        invalid_patterns = ("common_frame", "arm_base", "robot_base")
        if any(pattern in self.frame_id.lower() for pattern in invalid_patterns):
            raise ValueError(
                f"invalid_pose_frame_for_current_route: "
                f"frame_id={self.frame_id!r} must preserve the original "
                "Baton source frame"
            )


@dataclass
class PoseFilterSampleRecord:
    sample_ref: SignalSampleRef
    status: PoseFilterSampleStatus
    original_position: dict[str, Any]
    original_orientation: dict[str, Any]
    candidate_filtered_value: dict[str, Any] | None
    final_value: dict[str, Any]
    guard_delta: dict[str, float]
    reason: str | None = None


@dataclass
class PoseFilterSegmentSummary:
    source_topic: str
    segment_start_ref: SignalSampleRef | str
    segment_end_ref: SignalSampleRef | str
    filtered_count: int
    kept_count: int
    rejected_count: int
    skipped_boundary_count: int = 0
    actual_window_size_samples: int | None = None


@dataclass
class PoseFilterResult:
    input_repair_result_ref: SignalRepairResult | str
    pose_filter_config_ref: PoseFilterConfig | str
    input_sequence_refs: list[PoseFilterInputSequence | str]
    output_sequence_refs: dict[str, str] | list[Any]
    sample_records: list[PoseFilterSampleRecord] = field(default_factory=list)
    segment_summaries: list[PoseFilterSegmentSummary] = field(default_factory=list)
    sample_count_before: dict[str, int] = field(default_factory=dict)
    sample_count_after: dict[str, int] = field(default_factory=dict)
    timestamp_policy: str = "preserve_original"
    summary_by_topic: dict[str, Any] = field(default_factory=dict)
    created_at: str | None = None
    run_id: str | None = None

    def __post_init__(self) -> None:
        if self.sample_count_before != self.sample_count_after:
            raise ValueError("sample_count_before must equal sample_count_after")
