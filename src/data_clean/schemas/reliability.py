"""Reliability detection result types for service scene two."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class IssueSeverity(str, Enum):
    """Severity levels for reliability issues."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class IssueType(str, Enum):
    """Known issue categories emitted by reliability detection."""

    MISSING_SEGMENT = "missing_segment"
    TIMESTAMP_ANOMALY = "timestamp_anomaly"
    POSE_JUMP = "pose_jump"
    POSE_VELOCITY_ANOMALY = "pose_velocity_anomaly"
    POSE_ACCEL_ANOMALY = "pose_accel_anomaly"
    INVALID_ORIENTATION = "invalid_orientation"
    TACTILE_SHAPE_MISMATCH = "tactile_shape_mismatch"
    TACTILE_SPIKE = "tactile_spike"
    TACTILE_SATURATION = "tactile_saturation"
    TACTILE_ZERO_SUSPICIOUS = "tactile_zero_suspicious"
    GRIPPER_OUT_OF_RANGE = "gripper_out_of_range"
    GRIPPER_JUMP = "gripper_jump"
    GRIPPER_STUCK = "gripper_stuck"


class AnomalySource(str, Enum):
    """Signal modality or detector source for an issue."""

    POSE = "pose"
    TACTILE = "tactile"
    GRIPPER = "gripper"
    TIMESTAMP = "timestamp"


@dataclass
class SignalSampleRef:
    """Reference to one existing cleaned MCAP message sample."""

    topic: str
    timestamp: int | float
    message_index: int
    modality: str
    time_domain: str = "log_time"


@dataclass
class SampleReliabilityIssue:
    """Reliability problem attached to one existing sample."""

    issue_id: str
    sample_ref: SignalSampleRef
    issue_type: IssueType
    severity: IssueSeverity
    source: AnomalySource
    field_path: str
    message: str
    suggested_action: str = "inspect_required"
    reason: str = ""
    evidence: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class MissingIntervalIssue:
    """Reliability problem for a time interval with no sample to reference."""

    issue_id: str
    topic: str
    modality: str
    start_time: int | float
    end_time: int | float
    expected_count: int
    actual_count: int
    severity: IssueSeverity
    suggested_action: str
    time_domain: str = "log_time"
    issue_type: IssueType = IssueType.MISSING_SEGMENT
    reason: str = ""


@dataclass
class ReliabilityIssueGroup:
    """Display/report summary that references already emitted sample issues."""

    group_id: str
    issue_type: IssueType
    source: AnomalySource
    issue_ids: list[str]
    start_time: int | float | None = None
    end_time: int | float | None = None
    summary: str = ""
    severity: IssueSeverity | None = None


@dataclass
class SignalReliabilityDetectionResult:
    """Aggregate output of one scene two signal reliability detection run."""

    input_cleaned_mcap: str
    rule_config_ref: str
    sample_issues: list[SampleReliabilityIssue] = field(default_factory=list)
    missing_interval_issues: list[MissingIntervalIssue] = field(default_factory=list)
    issue_groups: list[ReliabilityIssueGroup] = field(default_factory=list)
    summary_by_modality: dict[str, Any] = field(default_factory=dict)
    created_at: str | None = None
    run_id: str | None = None
