from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .reliability import MissingIntervalIssue, SignalReliabilityDetectionResult, SignalSampleRef


class RepairMethod(str, Enum):
    INTERPOLATE_LINEAR = "interpolate_linear"
    FORWARD_FILL = "forward_fill"
    BACKWARD_FILL = "backward_fill"
    SENSOR_FUSION = "sensor_fusion"
    LINEAR_INTERPOLATE = "linear_interpolate"
    SLERP_INTERPOLATE = "slerp_interpolate"
    HOLD_PREVIOUS = "hold_previous"
    HOLD_NEXT = "hold_next"
    COPY_NEAREST = "copy_nearest"
    NO_OP = "no_op"


class RepairDecisionStatus(str, Enum):
    PENDING = "pending"
    REPAIRED = "repaired"
    UNREPAIRABLE = "unrepairable"
    SKIPPED = "skipped"


class RepairDisposition(str, Enum):
    """Upstream decision about whether a detected field may be modified."""

    AUTO_REPAIR = "auto_repair"
    MASK_ONLY = "mask_only"
    MANUAL_REVIEW = "manual_review"
    UNRECOVERABLE = "unrecoverable"
    NO_ACTION = "no_action"


@dataclass(frozen=True)
class SignalIssueDisposition:
    issue_id: str
    action: RepairDisposition
    field_path: str
    reason: str
    sample_ref: SignalSampleRef | None = None
    planned_method: RepairMethod | None = None


@dataclass
class SignalRepairPolicyConfig:
    repair_methods: list[RepairMethod]
    max_gap_duration_ns: int
    timestamp_policy: str = "preserve_original"
    allow_interpolate_to_hold_fallback: bool = False


@dataclass
class SignalRepairSampleRecord:
    sample_ref: SignalSampleRef
    status: RepairDecisionStatus
    repair_method: RepairMethod | None
    reason: str
    sample_issue_ids: list[str] = field(default_factory=list)
    original_value_ref: str | None = None
    repaired_value_ref: str | None = None
    value_summary: dict[str, Any] = field(default_factory=dict)


@dataclass
class SignalRepairRun:
    repair_run_id: str
    source_topic: str
    modality: str
    replacement_unit: str
    input_window_refs: list[SignalSampleRef]
    sample_issue_ids: list[str]
    status: RepairDecisionStatus
    applied_method: RepairMethod | None
    reason: str
    disposition: RepairDisposition = RepairDisposition.NO_ACTION
    planned_method: RepairMethod | None = None
    replacement_contract: dict[str, Any] = field(default_factory=dict)
    sample_records: list[SignalRepairSampleRecord] = field(default_factory=list)
    previous_neighbor_ref: SignalSampleRef | None = None
    next_neighbor_ref: SignalSampleRef | None = None


@dataclass
class SignalRepairResult:
    input_detection_result_ref: SignalReliabilityDetectionResult | str
    repair_policy_config_ref: SignalRepairPolicyConfig | str
    repair_runs: list[SignalRepairRun] = field(default_factory=list)
    dispositions: list[SignalIssueDisposition] = field(default_factory=list)
    unhandled_missing_interval_records: list[MissingIntervalIssue | dict[str, Any]] = field(default_factory=list)
    output_sequence_refs: dict[str, str] = field(default_factory=dict)
    timestamp_policy: str = "preserve_original"
    sample_count_before: dict[str, int] = field(default_factory=dict)
    sample_count_after: dict[str, int] = field(default_factory=dict)
    summary_by_modality: dict[str, Any] = field(default_factory=dict)
    created_at: str | None = None
    run_id: str | None = None
    run_context: Any | None = None
