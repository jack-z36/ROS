"""Run result index writer for Runtime end-of-run state tracking."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from schemas.manifest_types import RuntimeResultSchemaVersion, RunResultIndex
from schemas.runtime_enums import RunStatus
from schemas.runtime_results import SceneResult
from schemas.run_directory_types import RunDirectoryLayout


class RunResultIndexError(RuntimeError):
    """Raised when the run result index cannot be written."""


def _validate_path_inside_run_dir(path: str, run_dir: Path, path_name: str) -> None:
    """Ensure a path is inside the run directory to prevent path escape."""
    if not path:
        return  # Empty paths are allowed for optional fields

    resolved = Path(path).resolve()
    try:
        resolved.relative_to(run_dir.resolve())
    except ValueError:
        raise RunResultIndexError(
            f"{path_name} {resolved} must be inside run_dir {run_dir}"
        )


def _scene_result_to_dict(sr: SceneResult) -> dict[str, Any]:
    """Convert a SceneResult to a JSON-serializable dict."""
    d: dict[str, Any] = {
        "scene_name": sr.scene_name.value if hasattr(sr.scene_name, "value") else str(sr.scene_name),
        "status": sr.status.value if hasattr(sr.status, "value") else str(sr.status),
    }
    if sr.input_paths:
        d["input_paths"] = sr.input_paths
    if sr.output_paths:
        d["output_paths"] = sr.output_paths
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


def write_run_result_index(
    run_id: str,
    status: RunStatus,
    run_dir: str,
    run_log_path: str,
    scene_results: list[SceneResult],
    manifest_path: str,
    error_summary_path: str,
    layout: RunDirectoryLayout,
) -> Path:
    """Write run_result.json for a Runtime run.

    This function writes the unified run result index that points to either
    the processing manifest (success) or error summary (failure).

    Args:
        run_id: The run ID.
        status: The final run status.
        run_dir: The run directory path.
        run_log_path: The path to the structured log.
        scene_results: List of scene results.
        manifest_path: Path to processing_manifest.json (required for success).
        error_summary_path: Path to error_summary.json (required for failure).
        layout: The run directory layout providing the target path.

    Returns:
        The path to the written run_result.json file.

    Raises:
        RunResultIndexError: If validation fails or the file cannot be written.
    """
    # Validate required fields
    if not run_id:
        raise RunResultIndexError("run_id must be non-empty")

    if not run_dir:
        raise RunResultIndexError("run_dir must be non-empty")

    if not run_log_path:
        raise RunResultIndexError("run_log_path must be non-empty")

    if status == RunStatus.SUCCEEDED and not manifest_path:
        raise RunResultIndexError(
            "manifest_path must be set for succeeded status"
        )

    if status == RunStatus.FAILED and not error_summary_path:
        raise RunResultIndexError(
            "error_summary_path must be set for failed status"
        )

    run_dir_path = Path(run_dir).resolve()
    result_path = layout.run_result_path.path.resolve()

    # Validate all paths are inside run directory
    _validate_path_inside_run_dir(run_log_path, run_dir_path, "run_log_path")
    _validate_path_inside_run_dir(manifest_path, run_dir_path, "manifest_path")
    _validate_path_inside_run_dir(error_summary_path, run_dir_path, "error_summary_path")

    # Ensure target directory exists
    result_path.parent.mkdir(parents=True, exist_ok=True)

    # Check file doesn't already exist
    if result_path.exists():
        raise RunResultIndexError(
            f"run result index already exists: {result_path}"
        )

    # Convert status to string value
    status_value = status.value if hasattr(status, "value") else str(status)

    # Build scene results
    scene_results_dicts = [_scene_result_to_dict(sr) for sr in scene_results]

    # Create the run result index
    now = datetime.now()
    run_result = RunResultIndex(
        schema_version=RuntimeResultSchemaVersion.RUN_RESULT_V1,
        run_id=run_id,
        status=status_value,
        run_dir=run_dir,
        run_log_path=run_log_path,
        scene_results=scene_results_dicts,
        created_at=now,
        manifest_path=manifest_path,
        error_summary_path=error_summary_path,
    )

    # Write JSON
    result_path.write_text(
        json.dumps(run_result.to_dict(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return result_path
