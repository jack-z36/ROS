"""Aligned MCAP write orchestrator with staging commit strategy.

Coordinates the low-level write operations (aligned MCAP, alignment index,
alignment report) through a two-phase staging commit:

1. All writes go to a staging directory first.
2. On success: all files are committed (moved) to the output directory.
3. On failure: staging is cleaned; a failure summary and run log are
   persisted for diagnostics.

Per L3 service_s3_022.
"""

from __future__ import annotations

import json
import os
import shutil
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any

from mcap.reader import make_reader

from repo.aligned_mcap_writer import write_aligned_mcap
from repo.alignment_sidecar_writer import (
    write_alignment_index,
    write_alignment_report,
)

from schemas.aligned_mcap_report import (
    AlignedMcapWriteSummary,
    AlignmentReport,
    AlignmentReportFinalization,
)
from schemas.field_alignment import FieldAlignmentResult
from schemas.step_timeline import AlignmentIndexRecord, StepTimeline


WRITABLE_ALIGNMENT_STATUSES: set[str] = {
    "aligned",
    "interpolated",
    "aggregated",
    "fallback_nearest",
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def run_aligned_mcap_write_staging(
    source_mcap_path: str,
    field_results: list[FieldAlignmentResult],
    timeline: StepTimeline,
    alignment_index_records: list[AlignmentIndexRecord],
    alignment_report_draft: AlignmentReport,
    alignment_report_finalization: AlignmentReportFinalization,
    staging_dir: str,
    output_dir: str,
    run_id: str | None = None,
    config_ref: str | None = None,
) -> AlignedMcapWriteSummary:
    """Orchestrate an atomic staging commit of aligned MCAP + sidecar writes.

    All artifacts are written to *staging_dir* first.  If every write
    succeeds they are moved to *output_dir* and the summary status is
    ``completed``.  If any write fails the staging area is cleaned up,
    summary status is ``failed``, and a ``run_log.json`` is written to
    *output_dir* for diagnostics.

    Args:
        source_mcap_path: Path to the source MCAP_A.
        field_results:    Per-step per-field alignment results.
        timeline:         StepTimeline providing step timestamp context.
        alignment_index_records:  Records for alignment_index.parquet.
        alignment_report_draft:   Draft AlignmentReport to finalize.
        alignment_report_finalization:  Finalization overrides for the report.
        staging_dir:      Temporary write directory (created if needed).
        output_dir:       Final output directory.
        run_id:           Optional run identifier.
        config_ref:       Optional config reference string.

    Returns:
        An :class:`AlignedMcapWriteSummary` with the outcome.
    """
    # --- Ensure directories exist ---
    os.makedirs(staging_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    # --- Define output filenames ---
    mcap_filename = "aligned.mcap"
    index_filename = "alignment_index.parquet"
    report_filename = "alignment_report.json"
    summary_filename = "aligned_mcap_write_summary.json"

    staging_mcap = os.path.join(staging_dir, mcap_filename)
    staging_index = os.path.join(staging_dir, index_filename)
    staging_report = os.path.join(staging_dir, report_filename)

    step_count = len(timeline.steps) if timeline.steps else len(field_results)
    field_count = len({r.field_name for r in field_results})

    # --- Phase 1: Write all artifacts to staging ---
    steps_run: list[dict[str, Any]] = []
    failure_reason: str | None = None

    if not any(r.status in WRITABLE_ALIGNMENT_STATUSES for r in field_results):
        failure_reason = "no_writable_alignment_results"
        summary = AlignedMcapWriteSummary(
            input_mcap_a=source_mcap_path,
            status="failed",
            failure_reason=failure_reason,
            config_ref=config_ref,
            step_count=step_count,
            field_count=field_count,
            staging_dir=staging_dir,
            commit_policy="staging_atomic_commit",
            created_at=_now_iso(),
            run_id=run_id,
        )
        _write_summary(summary, os.path.join(output_dir, summary_filename))
        _write_run_log(
            run_id=run_id or "unknown",
            source_mcap=source_mcap_path,
            config_ref=config_ref,
            staging_dir=staging_dir,
            output_dir=output_dir,
            steps=steps_run,
            failure_reason=failure_reason,
            output_path=os.path.join(output_dir, "run_log.json"),
        )
        _clean_staging(staging_dir)
        return summary

    try:
        # Step 1: Write aligned MCAP to staging
        steps_run.append({"step": "write_aligned_mcap", "status": "started"})
        write_aligned_mcap(
            source_mcap_path=source_mcap_path,
            results=field_results,
            timeline=timeline,
            output_path=staging_mcap,
        )
        steps_run[-1]["status"] = "completed"
        steps_run[-1]["output"] = staging_mcap
        aligned_message_count = _count_mcap_messages(staging_mcap)
        steps_run[-1]["message_count"] = aligned_message_count
        if aligned_message_count <= 0:
            raise ValueError("aligned_mcap_has_no_messages")

        # Step 2: Write alignment index to staging
        steps_run.append({"step": "write_alignment_index", "status": "started"})
        write_alignment_index(
            records=alignment_index_records,
            output_path=staging_index,
        )
        steps_run[-1]["status"] = "completed"
        steps_run[-1]["output"] = staging_index

        # Step 3: Write alignment report to staging
        steps_run.append({"step": "write_alignment_report", "status": "started"})
        write_alignment_report(
            draft=alignment_report_draft,
            finalization=alignment_report_finalization,
            output_path=staging_report,
        )
        steps_run[-1]["status"] = "completed"
        steps_run[-1]["output"] = staging_report

    except (ValueError, OSError) as exc:
        failure_reason = f"{type(exc).__name__}: {exc}"
        # Clean up partial staging artifacts
        _clean_staging(staging_dir, keep=[summary_filename])

        # Write failure summary
        summary = AlignedMcapWriteSummary(
            input_mcap_a=source_mcap_path,
            status="failed",
            failure_reason=failure_reason,
            config_ref=config_ref,
            step_count=step_count,
            field_count=field_count,
            staging_dir=staging_dir,
            commit_policy="staging_atomic_commit",
            created_at=_now_iso(),
            run_id=run_id,
        )
        _write_summary(summary, os.path.join(output_dir, summary_filename))
        _write_run_log(
            run_id=run_id or "unknown",
            source_mcap=source_mcap_path,
            config_ref=config_ref,
            staging_dir=staging_dir,
            output_dir=output_dir,
            steps=steps_run,
            failure_reason=failure_reason,
            output_path=os.path.join(output_dir, "run_log.json"),
        )
        return summary

    # --- Phase 2: Commit from staging to output_dir ---
    output_mcap = os.path.join(output_dir, mcap_filename)
    output_index = os.path.join(output_dir, index_filename)
    output_report = os.path.join(output_dir, report_filename)

    try:
        shutil.move(staging_mcap, output_mcap)
        shutil.move(staging_index, output_index)
        shutil.move(staging_report, output_report)
    except OSError as exc:
        failure_reason = f"CommitFailed: {exc}"
        _clean_staging(staging_dir)
        summary = AlignedMcapWriteSummary(
            input_mcap_a=source_mcap_path,
            status="failed",
            failure_reason=failure_reason,
            config_ref=config_ref,
            step_count=step_count,
            field_count=field_count,
            staging_dir=staging_dir,
            commit_policy="staging_atomic_commit",
            created_at=_now_iso(),
            run_id=run_id,
        )
        _write_summary(summary, os.path.join(output_dir, summary_filename))
        _write_run_log(
            run_id=run_id or "unknown",
            source_mcap=source_mcap_path,
            config_ref=config_ref,
            staging_dir=staging_dir,
            output_dir=output_dir,
            steps=steps_run,
            failure_reason=failure_reason,
            output_path=os.path.join(output_dir, "run_log.json"),
        )
        return summary

    # --- Clean up staging dir ---
    _clean_staging(staging_dir)

    # --- Build completed summary ---
    summary = AlignedMcapWriteSummary(
        input_mcap_a=source_mcap_path,
        status="completed",
        output_aligned_mcap=output_mcap,
        alignment_index_path=output_index,
        alignment_report_path=output_report,
        failure_reason=None,
        config_ref=config_ref,
        step_count=step_count,
        field_count=field_count,
        staging_dir=staging_dir,
        commit_policy="staging_atomic_commit",
        created_at=_now_iso(),
        run_id=run_id,
    )
    _write_summary(summary, os.path.join(output_dir, summary_filename))
    _write_run_log(
        run_id=run_id or "unknown",
        source_mcap=source_mcap_path,
        config_ref=config_ref,
        staging_dir=staging_dir,
        output_dir=output_dir,
        steps=steps_run,
        failure_reason=None,
        output_path=os.path.join(output_dir, "run_log.json"),
    )
    return summary


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _now_iso() -> str:
    """Return current UTC timestamp as ISO string."""
    return datetime.now(timezone.utc).isoformat()


def _count_mcap_messages(mcap_path: str) -> int:
    count = 0
    with open(mcap_path, "rb") as fh:
        reader = make_reader(fh)
        for _schema, _channel, _message in reader.iter_messages(
            log_time_order=False
        ):
            count += 1
    return count


def _clean_staging(staging_dir: str, keep: list[str] | None = None) -> None:
    """Remove staging directory, optionally keeping certain files."""
    if not os.path.isdir(staging_dir):
        return
    if keep:
        for name in os.listdir(staging_dir):
            if name not in keep:
                path = os.path.join(staging_dir, name)
                try:
                    if os.path.isfile(path):
                        os.remove(path)
                    elif os.path.isdir(path):
                        shutil.rmtree(path)
                except OSError:
                    pass
    else:
        shutil.rmtree(staging_dir, ignore_errors=True)


def _write_summary(
    summary: AlignedMcapWriteSummary,
    output_path: str,
) -> None:
    """Serialize summary to JSON."""
    parent = os.path.dirname(os.path.abspath(output_path))
    if parent and not os.path.exists(parent):
        os.makedirs(parent, exist_ok=True)
    data: dict[str, Any] = asdict(summary)
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _write_run_log(
    run_id: str,
    source_mcap: str,
    config_ref: str | None,
    staging_dir: str,
    output_dir: str,
    steps: list[dict[str, Any]],
    failure_reason: str | None,
    output_path: str,
) -> None:
    """Write a minimal run log to the output directory."""
    parent = os.path.dirname(os.path.abspath(output_path))
    if parent and not os.path.exists(parent):
        os.makedirs(parent, exist_ok=True)

    log: dict[str, Any] = {
        "run_id": run_id,
        "source_mcap": source_mcap,
        "config_ref": config_ref,
        "staging_dir": staging_dir,
        "output_dir": output_dir,
        "execution_steps": steps,
        "status": "failed" if failure_reason else "completed",
        "failure_reason": failure_reason,
        "created_at": _now_iso(),
    }
    with open(output_path, "w") as f:
        json.dump(log, f, indent=2, ensure_ascii=False)
