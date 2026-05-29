"""Runtime wrapper for Scene 3 aligned MCAP write check developer entry.

This module provides the ``run_scene3_aligned_mcap_write_check`` function that
orchestrates the aligned MCAP write check for the
``scene3_aligned_mcap_write_check`` developer menu entry.  It:

1. Creates an isolated run directory.
2. Accepts a source MCAP_A path and output directory.
3. Calls ``run_aligned_mcap_write_staging()`` from the service layer.
4. Writes a run log.
5. Returns a structured result dict.
"""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from typing import Any

from .run_directory_creator import create_run_directory


def _jsonable(value: Any) -> Any:
    """Convert common types to JSON-serializable values."""
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return _jsonable(asdict(value))
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    return value


def run_scene3_aligned_mcap_write_check(
    *,
    source_mcap_path: str | Path,
    output_dir: str | Path,
    field_alignment_results_path: str | Path | None = None,
    timeline_path: str | Path | None = None,
    run_root: str | Path = Path("src/data_clean/runs"),
) -> dict[str, Any]:
    """Run the Scene 3 aligned MCAP write check as a developer entry.

    Args:
        source_mcap_path: Path to the source MCAP_A file to use as input.
        output_dir: Directory where staging and final outputs are written.
        field_alignment_results_path: Optional path to full-flow
            ``field_alignment_results.json``. When provided with
            ``timeline_path``, the write check uses real upstream alignment
            artifacts instead of a synthetic smoke-test record.
        timeline_path: Optional path to full-flow ``step_timeline.json``.
        run_root: Root directory under which an isolated run directory is
            created for metadata (logs, run tracking).

    Returns:
        A dict with ``run_id``, ``status`` (``"success"`` / ``"failed"``),
        ``outputs`` (paths to aligned MCAP, alignment index, alignment report,
        write summary, run log), and ``run_log_path``.
    """
    source_mcap_path = Path(source_mcap_path)
    output_dir = Path(output_dir)
    run_root = Path(run_root)

    run_directory = create_run_directory(
        run_root=run_root,
        run_date=date.today(),
        target_scenes=["scene3"],
    )
    outputs_dir = Path(run_directory.layout.outputs_dir.path)
    run_log_path = Path(run_directory.layout.run_log_path.path)
    steps: list[str] = ["create_run_directory"]
    errors: list[dict[str, str]] = []

    # Ensure output_dir exists
    output_dir.mkdir(parents=True, exist_ok=True)

    summary_data: dict[str, Any] | None = None
    stderr_output: str | None = None

    try:
        from service.aligned_mcap_writer import run_aligned_mcap_write_staging

        steps.append("import_staging_service")

        # Build minimal inputs from the source MCAP path.
        # We use a simplified invocation that exercises the staging commit
        # mechanism.  The staging_dir is set inside output_dir.
        staging_dir = output_dir / "staging"

        from schemas.step_timeline import FieldAlignmentStatus, StepTimeline, StepTimelineEntry
        from schemas.field_alignment import FieldAlignmentResult

        if field_alignment_results_path is not None and timeline_path is not None:
            from runtime.scene3_alignment_report_check import (
                _load_field_alignment_results,
                _load_step_timeline,
            )
            from service.alignment_report import (
                build_alignment_index_records,
                build_alignment_report_draft,
            )

            field_results = _load_field_alignment_results(
                Path(field_alignment_results_path)
            )
            timeline = _load_step_timeline(Path(timeline_path))
            index_result = build_alignment_index_records(field_results)
            failure_reason = index_result.get("failure_reason")
            if failure_reason:
                raise ValueError(failure_reason)
            alignment_index_records = index_result.get("records", [])
            report_draft = build_alignment_report_draft(
                alignment_index_records=alignment_index_records,
                step_timeline=timeline,
                input_mcap_a=str(source_mcap_path),
                config_ref="aligned_mcap_write_check",
            )
        else:
            # Create a one-record smoke input to exercise the staging pipeline.
            timeline = StepTimeline(
                timeline_id="aligned_mcap_write_check",
                target_step_hz=15,
                start_time_ns=0,
                end_time_ns=0,
                step_count=1,
                steps=[StepTimelineEntry(step_index=0, step_time_ns=0)],
            )
            field_results = [
                FieldAlignmentResult(
                    step_index=0,
                    step_time_ns=0,
                    field_name="aligned_mcap_write_smoke",
                    status=FieldAlignmentStatus.missing_time.value,
                    alignment_method="none",
                    source_topic=None,
                    output_topic=None,
                )
            ]
            from service.alignment_report import (
                build_alignment_index_records,
                build_alignment_report_draft,
            )

            index_result = build_alignment_index_records(field_results)
            alignment_index_records = index_result.get("records", [])
            report_draft = build_alignment_report_draft(
                alignment_index_records=alignment_index_records,
                step_timeline=timeline,
                input_mcap_a=str(source_mcap_path),
                config_ref="aligned_mcap_write_check",
            )

        from schemas.aligned_mcap_report import (
            AlignmentReport,
            AlignmentReportFinalization,
        )

        finalization = AlignmentReportFinalization(
            output_aligned_mcap=str(output_dir / "aligned.mcap"),
            alignment_index=str(output_dir / "alignment_index.parquet"),
            run_id="aligned_mcap_write_check",
            status="completed",
        )

        steps.append("call_staging_service")

        summary = run_aligned_mcap_write_staging(
            source_mcap_path=str(source_mcap_path),
            field_results=field_results,
            timeline=timeline,
            alignment_index_records=alignment_index_records,
            alignment_report_draft=report_draft,
            alignment_report_finalization=finalization,
            staging_dir=str(staging_dir),
            output_dir=str(output_dir),
            run_id="aligned_mcap_write_check",
            config_ref="aligned_mcap_write_check",
        )

        summary_data = asdict(summary) if is_dataclass(summary) else summary

        if summary_data.get("status") == "completed":
            steps.append("staging_commit_completed")
        else:
            steps.append("staging_commit_failed")

    except Exception as exc:
        errors.append({"type": type(exc).__name__, "message": str(exc)})
        steps.append("check_failed")

    # Determine overall status
    status = "success"
    if errors:
        status = "failed"
    elif summary_data and summary_data.get("status") == "failed":
        status = "failed"

    # Build outputs dict
    outputs: dict[str, str | None] = {
        "run_dir": str(run_directory.run_dir),
    }
    if summary_data:
        outputs["aligned_mcap"] = summary_data.get("output_aligned_mcap")
        outputs["alignment_index"] = summary_data.get("alignment_index_path")
        outputs["alignment_report"] = summary_data.get("alignment_report_path")
        outputs["write_summary"] = str(
            output_dir / "aligned_mcap_write_summary.json"
        )
        outputs["staging_dir"] = summary_data.get("staging_dir")
    else:
        outputs["aligned_mcap"] = None
        outputs["alignment_index"] = None
        outputs["alignment_report"] = None
        outputs["write_summary"] = None
        outputs["staging_dir"] = str(staging_dir) if "staging_dir" in dir() else None

    # Build and write run log
    run_log = {
        "run_id": run_directory.run_id,
        "check_id": "scene3_aligned_mcap_write_check",
        "status": status,
        "input": {
            "source_mcap_path": str(source_mcap_path),
            "output_dir": str(output_dir),
        },
        "outputs": outputs,
        "summary": summary_data,
        "steps": steps + ["write_run_log"],
        "errors": errors,
        "created_at": datetime.now().isoformat(),
    }
    run_log_path.write_text(
        json.dumps(_jsonable(run_log), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return {
        **run_log,
        "run_log_path": str(run_log_path),
    }
