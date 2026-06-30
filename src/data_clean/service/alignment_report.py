"""Alignment index normalization and alignment report services for Scene 3.

Builds AlignmentIndex records from FieldAlignmentResult objects, enforcing
step_index+field_name uniqueness and stripping derived_value per L2 contract.
Also generates AlignmentReport draft statistics from index records.
"""

from __future__ import annotations

from schemas.field_alignment import FieldAlignmentResult
from schemas.step_timeline import AlignmentIndexRecord, FieldAlignmentStatus, StepTimeline
from schemas.aligned_mcap_report import (
    AlignmentDegradationSummary,
    AlignmentFieldStats,
    AlignmentReport,
    AlignmentReportStatus,
)
from schemas.alignment_input import McapAInputValidationSummary


def _to_enum(status_str: str) -> FieldAlignmentStatus:
    """Convert a status string to FieldAlignmentStatus enum.

    Falls back to invalid_input for unknown values.
    """
    try:
        return FieldAlignmentStatus(status_str)
    except ValueError:
        return FieldAlignmentStatus.invalid_input


def _result_to_record(result: FieldAlignmentResult) -> AlignmentIndexRecord:
    """Convert one FieldAlignmentResult to AlignmentIndexRecord.

    Strips derived_value — only fact fields are retained per L2 contract.
    """
    return AlignmentIndexRecord(
        step_index=result.step_index,
        step_time_ns=result.step_time_ns,
        field_name=result.field_name,
        source_topic=result.source_topic,
        output_topic=result.output_topic,
        source_time_ns=result.source_time_ns,
        alignment_method=result.alignment_method,
        status=_to_enum(result.status),
        dt_ms=result.dt_ms,
        neighbor_before_time_ns=result.neighbor_before_time_ns,
        neighbor_after_time_ns=result.neighbor_after_time_ns,
        window_start_time_ns=result.window_start_time_ns,
        window_end_time_ns=result.window_end_time_ns,
        sample_count=result.sample_count,
        coverage_ratio=result.coverage_ratio,
        fallback_reason=result.fallback_reason,
        message_ref=result.message_ref,
    )


def build_alignment_index_records(
    results: list[FieldAlignmentResult] | None,
) -> dict:
    """Normalize FieldAlignmentResult list to AlignmentIndex records.

    Per L2 alignment index normalization rules:
    - Extract fact fields only (no derived_value).
    - Enforce step_index + field_name uniqueness.
    - Return failure_reason on empty input or duplicate.

    Args:
        results: List of FieldAlignmentResult objects, or None.

    Returns:
        dict with keys:
            records (list[AlignmentIndexRecord]): Normalized records.
            record_count (int): Number of records produced.
            failure_reason (str | None): Error reason if failed, else None.
    """
    if not results:
        return {
            "records": [],
            "record_count": 0,
            "failure_reason": "missing_field_alignment_result",
        }

    seen: set[tuple[int, str]] = set()
    records: list[AlignmentIndexRecord] = []

    for result in results:
        key = (result.step_index, result.field_name)
        if key in seen:
            return {
                "records": records,
                "record_count": len(records),
                "failure_reason": "duplicate_step_field_record",
            }
        seen.add(key)
        records.append(_result_to_record(result))

    return {
        "records": records,
        "record_count": len(records),
        "failure_reason": None,
    }


# ---------------------------------------------------------------------------
# AlignmentReport draft statistics generation
# ---------------------------------------------------------------------------


def _compute_status_counts(
    records: list[AlignmentIndexRecord],
) -> dict[str, int]:
    """Count occurrences of each FieldAlignmentStatus across records.

    Returns a dict mapping status value strings to their counts.
    """
    counts: dict[str, int] = {}
    for rec in records:
        status_val = rec.status.value if isinstance(rec.status, FieldAlignmentStatus) else str(rec.status)
        counts[status_val] = counts.get(status_val, 0) + 1
    return counts


def _compute_field_stats(
    records: list[AlignmentIndexRecord],
) -> dict[str, AlignmentFieldStats]:
    """Compute per-field alignment quality statistics from index records.

    Groups records by field_name and computes AlignmentFieldStats for each.
    """
    from collections import defaultdict

    field_groups: dict[str, list[AlignmentIndexRecord]] = defaultdict(list)
    for rec in records:
        field_groups[rec.field_name].append(rec)

    stats: dict[str, AlignmentFieldStats] = {}
    for field_name, recs in field_groups.items():
        total = len(recs)
        aligned = sum(1 for r in recs if r.status == FieldAlignmentStatus.aligned)
        interpolated = sum(1 for r in recs if r.status == FieldAlignmentStatus.interpolated)
        aggregated = sum(1 for r in recs if r.status == FieldAlignmentStatus.aggregated)
        fallback = sum(1 for r in recs if r.status == FieldAlignmentStatus.fallback_nearest)
        missing_time = sum(1 for r in recs if r.status == FieldAlignmentStatus.missing_time)
        timeout = sum(1 for r in recs if r.status == FieldAlignmentStatus.timeout)
        unavailable = sum(1 for r in recs if r.status == FieldAlignmentStatus.unavailable)

        dt_values = [r.dt_ms for r in recs if r.dt_ms is not None]
        avg_dt = sum(dt_values) / len(dt_values) if dt_values else None
        max_dt = max(dt_values) if dt_values else None

        coverage_values = [r.coverage_ratio for r in recs if r.coverage_ratio is not None]
        avg_coverage = sum(coverage_values) / len(coverage_values) if coverage_values else None

        stats[field_name] = AlignmentFieldStats(
            total_count=total,
            aligned_count=aligned,
            interpolated_count=interpolated,
            aggregated_count=aggregated,
            fallback_count=fallback,
            missing_time_count=missing_time,
            timeout_count=timeout,
            unavailable_count=unavailable,
            avg_dt_ms=avg_dt,
            max_dt_ms=max_dt,
            coverage_ratio=avg_coverage,
        )

    return stats


def _compute_degradation_summary(
    records: list[AlignmentIndexRecord],
) -> AlignmentDegradationSummary:
    """Aggregate quality degradation facts across all index records.

    Collects counts and per-field lists for missing, timeout, fallback,
    and unavailable statuses. Tracks fallback reasons. Does NOT express
    training availability decisions per L2 contract.
    """
    missing_fields: list[str] = []
    timeout_fields: list[str] = []
    fallback_fields: list[str] = []
    unavailable_fields: list[str] = []
    fallback_reason_counts: dict[str, int] = {}

    for rec in records:
        if rec.status == FieldAlignmentStatus.missing_time:
            missing_fields.append(rec.field_name)
        elif rec.status == FieldAlignmentStatus.timeout:
            timeout_fields.append(rec.field_name)
        elif rec.status == FieldAlignmentStatus.fallback_nearest:
            fallback_fields.append(rec.field_name)
            if rec.fallback_reason:
                fallback_reason_counts[rec.fallback_reason] = (
                    fallback_reason_counts.get(rec.fallback_reason, 0) + 1
                )
        elif rec.status == FieldAlignmentStatus.unavailable:
            unavailable_fields.append(rec.field_name)

    return AlignmentDegradationSummary(
        missing_time_count=len(missing_fields),
        timeout_count=len(timeout_fields),
        fallback_nearest_count=len(fallback_fields),
        unavailable_count=len(unavailable_fields),
        missing_time_fields=list(set(missing_fields)),
        timeout_fields=list(set(timeout_fields)),
        fallback_fields=list(set(fallback_fields)),
        unavailable_fields=list(set(unavailable_fields)),
        fallback_reason_counts=fallback_reason_counts,
    )


def _compute_timeline_summary(
    timeline: StepTimeline,
) -> dict:
    """Extract a serializable summary dict from a StepTimeline."""
    return {
        "timeline_id": timeline.timeline_id,
        "target_step_hz": timeline.target_step_hz,
        "start_time_ns": timeline.start_time_ns,
        "end_time_ns": timeline.end_time_ns,
        "step_count": timeline.step_count,
        "range_policy": timeline.range_policy,
        "baseline_policy": timeline.baseline_policy,
    }


def build_alignment_report_draft(
    alignment_index_records: list[AlignmentIndexRecord] | None,
    step_timeline: StepTimeline | None,
    input_mcap_a: str | None = None,
    mcap_a_write_summary_ref: str | None = None,
    config_ref: str | None = None,
    input_validation_summary: McapAInputValidationSummary | None = None,
) -> AlignmentReport:
    """Generate an AlignmentReport draft from alignment index records.

    Per L2 AlignmentReport draft contract:
    - Computes status_counts, field_stats, degradation_summary from records.
    - Missing index or timeline returns a failed draft with explicit reason.
    - Degradation facts are quality statistics, not training availability decisions.

    Args:
        alignment_index_records: Normalized AlignmentIndex records, or None.
        step_timeline: Unified step timeline, or None.
        input_mcap_a: Optional MCAP_A path string.
        mcap_a_write_summary_ref: Optional write summary reference.
        config_ref: Optional config reference string.
        input_validation_summary: Optional input validation summary.

    Returns:
        AlignmentReport draft with computed statistics.
    """
    # --- Input validation ---
    if not alignment_index_records:
        return AlignmentReport(
            input_mcap_a=input_mcap_a or "",
            field_stats={},
            status_counts={},
            status=AlignmentReportStatus.failed.value,
            failure_reason="missing_alignment_index",
            mcap_a_write_summary_ref=mcap_a_write_summary_ref,
            config_ref=config_ref,
            degradation_summary=AlignmentDegradationSummary(),
        )

    if step_timeline is None:
        return AlignmentReport(
            input_mcap_a=input_mcap_a or "",
            field_stats={},
            status_counts={},
            status=AlignmentReportStatus.failed.value,
            failure_reason="missing_step_timeline",
            mcap_a_write_summary_ref=mcap_a_write_summary_ref,
            config_ref=config_ref,
            degradation_summary=AlignmentDegradationSummary(),
        )

    # --- Compute statistics ---
    status_counts = _compute_status_counts(alignment_index_records)
    field_stats = _compute_field_stats(alignment_index_records)
    degradation_summary = _compute_degradation_summary(alignment_index_records)

    # Determine overall status: if any degradation exists, status is degraded
    has_degradation = (
        degradation_summary.missing_time_count > 0
        or degradation_summary.timeout_count > 0
        or degradation_summary.fallback_nearest_count > 0
        or degradation_summary.unavailable_count > 0
    )
    overall_status = (
        AlignmentReportStatus.degraded.value
        if has_degradation
        else AlignmentReportStatus.completed.value
    )

    # Build timeline summary
    timeline_summary = _compute_timeline_summary(step_timeline)

    return AlignmentReport(
        input_mcap_a=input_mcap_a or "",
        field_stats=field_stats,
        status_counts=status_counts,
        status=overall_status,
        failure_reason=None,
        mcap_a_write_summary_ref=mcap_a_write_summary_ref,
        config_ref=config_ref,
        step_timeline_summary=timeline_summary,
        degradation_summary=degradation_summary,
    )
