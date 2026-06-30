"""Aligned MCAP artifact, alignment report, and write summary types for Scene 3."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class AlignmentReportStatus(str, Enum):
    """Status of an alignment report attempt.

    Values follow L2 AlignmentReport data definition:
    - completed: all fields aligned or quality-degraded but processing finished.
    - degraded: some fields had quality issues (missing, timeout, fallback)
      but processing completed without fatal error.
    - failed: processing could not complete due to input error or fatal
      condition.
    """

    completed = "completed"
    degraded = "degraded"
    failed = "failed"


@dataclass
class AlignmentFieldStats:
    """Per-field alignment quality statistics.

    Provides machine-readable error and quality metrics for each field,
    used in AlignmentReport.field_stats and consumed by Scene 4 quality
    report.

    Per L2 data definition: at minimum includes count, rate, and dt
    basics; more granular percentiles can be added by downstream
    services without changing this type.
    """

    total_count: int = 0
    aligned_count: int = 0
    interpolated_count: int = 0
    aggregated_count: int = 0
    fallback_count: int = 0
    missing_time_count: int = 0
    timeout_count: int = 0
    unavailable_count: int = 0
    avg_dt_ms: float | None = None
    max_dt_ms: float | None = None
    coverage_ratio: float | None = None


@dataclass
class AlignmentDegradationSummary:
    """Summary of quality degradation facts.

    Aggregates missing, timeout, fallback, and unavailable counts
    across all fields. Does NOT express training availability decisions.

    Per L2 data definition:
    - Degradation facts represent quality metrics only.
    - Does not replace training mask or episode discard logic.
    - fallback_reason_counts tracks why fallbacks occurred.
    """

    missing_time_count: int = 0
    timeout_count: int = 0
    fallback_nearest_count: int = 0
    unavailable_count: int = 0
    missing_time_fields: list[str] = field(default_factory=list)
    timeout_fields: list[str] = field(default_factory=list)
    fallback_fields: list[str] = field(default_factory=list)
    unavailable_fields: list[str] = field(default_factory=list)
    fallback_reason_counts: dict[str, int] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)


@dataclass
class AlignedMcap:
    """Aligned MCAP output artifact.

    Represents the aligned MCAP output with references to its sidecar files
    (alignment index and alignment report) and the overall status.
    """

    output_aligned_mcap: str
    alignment_index_path: str
    alignment_report_path: str
    status: str
    failure_reason: str | None = None


@dataclass
class AlignmentReport:
    """Alignment statistics report (machine-readable summary).

    This report stores only aggregate statistics — it does NOT embed
    per-step-field alignment detail.  The full per-step-field facts
    live in the AlignmentIndex (alignment_index.parquet).

    The report has two lifecycle stages:
      - draft:  input_mcap_a, field_stats, status_counts populated;
                output_aligned_mcap/alignment_index may be None.
      - final:  output_aligned_mcap and alignment_index are set before
                the report is written to disk.
    """

    input_mcap_a: str
    field_stats: dict[str, AlignmentFieldStats]
    status_counts: dict[str, int]
    status: str = "completed"
    failure_reason: str | None = None
    mcap_a_write_summary_ref: str | None = None
    config_ref: str | None = None
    step_timeline_summary: dict[str, Any] | None = None
    degradation_summary: AlignmentDegradationSummary | None = None
    output_aligned_mcap: str | None = None
    alignment_index: str | None = None
    run_id: str | None = None

    def __post_init__(self) -> None:
        """Validate status value per L2 AlignmentReport data definition."""
        valid_statuses = {"completed", "degraded", "failed"}
        if self.status not in valid_statuses:
            raise ValueError(
                f"AlignmentReport status must be one of {valid_statuses}, "
                f"got {self.status!r}"
            )


@dataclass
class AlignedMcapWriteSummary:
    """Summary of the aligned MCAP and sidecar write operation.

    Answers: where was the aligned MCAP written, from which MCAP_A,
    was it successful, and what was the failure reason.
    Per L3 service_s3_019: paths are nullable (null allowed), commit_policy
    defaults to "staging_atomic_commit", status must be completed/failed.
    """

    input_mcap_a: str
    status: str
    output_aligned_mcap: str | None = None
    alignment_index_path: str | None = None
    alignment_report_path: str | None = None
    failure_reason: str | None = None
    config_ref: str | None = None
    step_count: int = 0
    field_count: int = 0
    staging_dir: str | None = None
    commit_policy: str = "staging_atomic_commit"
    created_at: str | None = None
    run_id: str | None = None

    def __post_init__(self) -> None:
        """Validate status and required fields per L3 data definition."""
        valid_statuses = {"completed", "failed"}
        if self.status not in valid_statuses:
            raise ValueError(
                f"AlignedMcapWriteSummary status must be one of "
                f"{valid_statuses}, got {self.status!r}"
            )
        if self.status == "completed":
            if not self.output_aligned_mcap:
                raise ValueError(
                    "output_aligned_mcap must be set when status is completed"
                )
            if not self.alignment_index_path:
                raise ValueError(
                    "alignment_index_path must be set when status is completed"
                )
            if not self.alignment_report_path:
                raise ValueError(
                    "alignment_report_path must be set when status is completed"
                )


@dataclass
class AlignmentReportFinalization:
    """Fields needed to finalize an AlignmentReport from draft to final state.

    Per L2 AlignmentReport data definition, the finalization step sets
    output_aligned_mcap, alignment_index, run_id, and status before the
    report is written to disk as alignment_report.json.
    """

    status: str = "completed"
    output_aligned_mcap: str | None = None
    alignment_index: str | None = None
    run_id: str | None = None
    failure_reason: str | None = None

    def __post_init__(self) -> None:
        """Validate status and required fields per L2/L3 data definition."""
        valid_statuses = {"completed", "degraded", "failed"}
        if self.status not in valid_statuses:
            raise ValueError(
                f"AlignmentReportFinalization status must be one of "
                f"{valid_statuses}, got {self.status!r}"
            )
        if self.status in ("completed", "degraded") and not self.output_aligned_mcap:
            raise ValueError(
                "output_aligned_mcap must be set when status is completed or degraded"
            )
