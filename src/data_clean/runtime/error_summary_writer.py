"""Error summary writer for Runtime MVP error_summary.json."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from schemas import ErrorSummary, RuntimeResultSchemaVersion
from schemas.runtime_results import RuntimeErrorRef, SceneResult
from schemas.run_directory_types import RunDirectoryLayout
from schemas.runtime_enums import SceneName, RunStatus
from schemas.structured_log_types import RuntimeLogWriteResult


@dataclass
class ErrorSummaryWriteResult:
    """Result of writing error_summary.json."""

    run_id: str
    error_summary_path: str
    status: RunStatus
    error: RuntimeErrorRef | None = None


def _scene_result_to_dict(sr: SceneResult) -> dict[str, Any]:
    """Convert a SceneResult to a JSON-serializable dict."""
    d: dict[str, Any] = {
        "scene_name": sr.scene_name.value if hasattr(sr.scene_name, "value") else str(sr.scene_name),
        "status": sr.status.value if hasattr(sr.status, "value") else str(sr.status),
    }
    if sr.input_paths:
        # Convert Path objects to strings
        d["input_paths"] = [str(p) if hasattr(p, '__fspath__') else p for p in sr.input_paths]
    if sr.output_paths:
        # Convert Path objects to strings
        d["output_paths"] = [str(p) if hasattr(p, '__fspath__') else p for p in sr.output_paths]
    if sr.started_at:
        d["started_at"] = sr.started_at.isoformat()
    if sr.finished_at:
        d["finished_at"] = sr.finished_at.isoformat()
    if sr.duration_ms is not None:
        d["duration_ms"] = sr.duration_ms
    if sr.error:
        d["error"] = {
            "error_code": sr.error.error_code,
            "step_name": sr.error.step_name,
            "message": sr.error.message,
        }
    return d


def _error_ref_to_dict(error: RuntimeErrorRef) -> dict[str, Any]:
    """Convert a RuntimeErrorRef to a JSON-serializable dict."""
    d: dict[str, Any] = {
        "error_code": error.error_code,
        "step_name": error.step_name,
        "message": error.message,
    }
    if error.scene_name:
        d["scene_name"] = error.scene_name.value if hasattr(error.scene_name, "value") else str(error.scene_name)
    if error.details:
        d["details"] = error.details
    if error.suggested_next_action:
        d["suggested_next_action"] = error.suggested_next_action
    return d


def write_error_summary(
    run_id: str,
    error: RuntimeErrorRef,
    failed_step: str,
    log_write_result: RuntimeLogWriteResult,
    layout: RunDirectoryLayout,
    scene_results: list[SceneResult],
    failed_scene: SceneName | None = None,
    suggested_next_action: str = "",
) -> ErrorSummaryWriteResult:
    """Write error_summary.json for a failed run.

    Args:
        run_id: The run identifier.
        error: The structured error reference.
        failed_step: The step that failed.
        log_write_result: The result of writing the structured log.
        layout: The run directory layout providing the target path.
        scene_results: List of scene results before failure.
        failed_scene: The scene that failed (if any).
        suggested_next_action: Suggested next action for debugging.

    Returns:
        ErrorSummaryWriteResult with write status and metadata.
    """
    # Get error_summary_path from layout
    error_summary_path_str = layout.error_summary_path.path
    result_path = error_summary_path_str if error_summary_path_str else "invalid"

    # Validate error_summary_path is not empty
    if not error_summary_path_str:
        return ErrorSummaryWriteResult(
            run_id=run_id,
            error_summary_path=result_path,
            status=RunStatus.FAILED,
            error=RuntimeErrorRef(
                error_code="error_summary_path_missing",
                step_name="write_error_summary",
                message="error_summary_path is empty",
            ),
        )

    error_summary_path = Path(error_summary_path_str)

    # Extract run_dir from the layout paths (get parent of run_log_path)
    run_log_path_val = layout.run_log_path.path
    if run_log_path_val:
        run_dir = Path(run_log_path_val).parent.resolve()
    else:
        # Fallback to error_summary_path parent
        run_dir = error_summary_path.parent.resolve()

    # Validate path is inside run directory (path escape check)
    try:
        error_summary_path.resolve().relative_to(run_dir)
    except ValueError:
        return ErrorSummaryWriteResult(
            run_id=run_id,
            error_summary_path=result_path,
            status=RunStatus.FAILED,
            error=RuntimeErrorRef(
                error_code="error_summary_path_escape",
                step_name="write_error_summary",
                message="error_summary_path escapes the run directory",
                details={"error_summary_path": error_summary_path_str, "run_dir": str(run_dir)},
            ),
        )

    # Check file doesn't already exist (no pollution)
    if error_summary_path.exists():
        return ErrorSummaryWriteResult(
            run_id=run_id,
            error_summary_path=result_path,
            status=RunStatus.FAILED,
            error=RuntimeErrorRef(
                error_code="error_summary_already_exists",
                step_name="write_error_summary",
                message="error_summary.json already exists",
                details={"error_summary_path": error_summary_path_str},
            ),
        )

    # Ensure parent directory exists
    error_summary_path.parent.mkdir(parents=True, exist_ok=True)

    # Determine run_log_path - use expected path from log_write_result, fallback to layout
    run_log_path = log_write_result.log_path
    if not run_log_path:
        run_log_path = layout.run_log_path.path

    # The error_summary.json always contains "failed" status because it's written on failure path
    # But ErrorSummaryWriteResult.status indicates whether the write operation succeeded
    error_summary_status = RunStatus.FAILED  # This goes into the JSON file

    # Build message from error
    message = error.message

    # Build config_snapshot_path if available
    config_snapshot_path_val = layout.config_snapshot_path.path
    if config_snapshot_path_val:
        config_snapshot_path = str(config_snapshot_path_val)
    else:
        config_snapshot_path = ""

    # Build suggested_next_action
    if not suggested_next_action and error.suggested_next_action:
        suggested_next_action = error.suggested_next_action

    # Convert scene_results to dicts
    scene_results_dicts = [_scene_result_to_dict(sr) for sr in scene_results]

    # Convert failed_scene to string if present
    failed_scene_str = None
    if failed_scene:
        failed_scene_str = failed_scene.value if hasattr(failed_scene, "value") else str(failed_scene)

    # Build error_summary content
    now = datetime.now()
    error_summary_dict: dict[str, Any] = {
        "schema_version": RuntimeResultSchemaVersion.ERROR_SUMMARY_V1.value,
        "run_id": run_id,
        "status": error_summary_status.value,
        "failed_step": failed_step,
        "failed_scene": failed_scene_str,
        "error": _error_ref_to_dict(error),
        "run_log_path": run_log_path,
        "config_snapshot_path": config_snapshot_path,
        "scene_results": scene_results_dicts,
        "message": message,
        "suggested_next_action": suggested_next_action,
        "created_at": now.isoformat(),
    }

    # Write JSON
    try:
        error_summary_path.write_text(
            json.dumps(error_summary_dict, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    except (TypeError, ValueError) as e:
        return ErrorSummaryWriteResult(
            run_id=run_id,
            error_summary_path=result_path,
            status=RunStatus.FAILED,
            error=RuntimeErrorRef(
                error_code="error_summary_not_serializable",
                step_name="write_error_summary",
                message="Error summary contains non-serializable data",
                details={"error": str(e)},
            ),
        )

    return ErrorSummaryWriteResult(
        run_id=run_id,
        error_summary_path=str(error_summary_path),
        status=RunStatus.SUCCEEDED,
    )
