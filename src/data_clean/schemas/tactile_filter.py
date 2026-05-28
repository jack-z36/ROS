from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from math import isfinite
from typing import Any

from .reliability import SignalSampleRef
from .repair import SignalRepairResult


class TactileFilterAlgorithm(str, Enum):
    MEDIAN_EMA = "median_ema"


class TactileFilterSampleStatus(str, Enum):
    FILTERED = "filtered"
    KEPT_ORIGINAL = "kept_original"
    SKIPPED_BOUNDARY = "skipped_boundary"
    EMA_RESET = "ema_reset"
    INVALID_SHAPE = "invalid_shape"


@dataclass
class TactileFilterConfig:
    algorithm: TactileFilterAlgorithm = TactileFilterAlgorithm.MEDIAN_EMA
    median_window: int = 3
    ema_alpha: float = 0.35
    contact_reset_threshold: float | None = None
    timestamp_policy: str = "preserve_original"

    def __post_init__(self) -> None:
        if self.median_window < 3 or self.median_window % 2 == 0:
            raise ValueError("median_window must be an odd integer greater than or equal to 3")
        if not 0 < self.ema_alpha <= 1:
            raise ValueError("ema_alpha must be in (0, 1]")
        if self.contact_reset_threshold is not None and (
            self.contact_reset_threshold < 0 or not isfinite(self.contact_reset_threshold)
        ):
            raise ValueError("contact_reset_threshold must be finite and non-negative")
        if self.timestamp_policy != "preserve_original":
            raise ValueError("timestamp_policy must be preserve_original")


@dataclass
class TactileFilterInputSequence:
    source_topic: str
    input_sequence_ref: str | dict[str, Any]
    input_repair_result_ref: SignalRepairResult | str
    modality: str = "tactile"
    sample_refs: list[SignalSampleRef] = field(default_factory=list)


@dataclass
class TactileFilterSampleRecord:
    sample_ref: SignalSampleRef
    status: TactileFilterSampleStatus
    filtered_value_summary: dict[str, Any]
    debug_artifact_ref: str | None = None
    reason: str | None = None


@dataclass
class TactileFilterSegmentSummary:
    source_topic: str
    segment_start_ref: SignalSampleRef | str
    segment_end_ref: SignalSampleRef | str
    sample_count: int
    filtered_count: int
    kept_original_count: int
    skipped_boundary_count: int
    ema_reset_count: int
    invalid_shape_count: int
    median_window: int | None = None
    ema_alpha: float | None = None


@dataclass
class TactileFilterResult:
    input_repair_result_ref: SignalRepairResult | str
    tactile_filter_config_ref: TactileFilterConfig | str
    input_sequence_refs: list[TactileFilterInputSequence | str]
    output_sequence_refs: dict[str, str] | list[Any]
    sample_records: list[TactileFilterSampleRecord] = field(default_factory=list)
    segment_summaries: list[TactileFilterSegmentSummary] = field(default_factory=list)
    sample_count_before: dict[str, int] = field(default_factory=dict)
    sample_count_after: dict[str, int] = field(default_factory=dict)
    timestamp_policy: str = "preserve_original"
    summary_by_topic: dict[str, Any] = field(default_factory=dict)
    created_at: str | None = None
    run_id: str | None = None

    def __post_init__(self) -> None:
        if self.sample_count_before != self.sample_count_after:
            raise ValueError("sample_count_before must equal sample_count_after")
        if self.timestamp_policy != "preserve_original":
            raise ValueError("timestamp_policy must be preserve_original")
