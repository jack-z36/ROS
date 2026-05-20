"""Processing manifest writer for the success path of a Runtime run."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from schemas.runtime_config_types import ConfigSnapshot
from schemas.runtime_context import RunContext
from schemas.runtime_enums import RunStatus
from schemas.runtime_results import (
    MANIFEST_SCHEMA_VERSION,
    PipelineResult,
    ProcessingManifest,
    SceneResult,
)
from schemas.run_directory_types import RunDirectoryLayout
from schemas.structured_log_types import RuntimeLogWriteResult


class ProcessingManifestError(RuntimeError):
    """Raised when the processing manifest cannot be written."""


def _validate_paths_in_run_dir(
    config_path: Path,
    log_path: str,
    run_dir: Path,
) -> None:
    """Ensure the config and log paths are inside the run directory."""
    # Validate config snapshot path
    config_resolved = config_path.resolve()
    try:
        config_resolved.relative_to(run_dir)
    except ValueError:
        raise ProcessingManifestError(
            f"config snapshot path {config_resolved} must be inside run_dir {run_dir}"
        )

    # Validate log path
    log_resolved = Path(log_path).resolve()
    try:
        log_resolved.relative_to(run_dir)
    except ValueError:
        raise ProcessingManifestError(
            f"log path {log_resolved} must be inside run_dir {run_dir}"
        )


def _validate_no_failed_scenes(pipeline_result: PipelineResult) -> None:
    """Ensure no scene results are in a failed state for the success path."""
    for sr in pipeline_result.scene_results:
        if sr.status == RunStatus.FAILED:
            raise ProcessingManifestError(
                f"success path manifest cannot contain failed scene: {sr.scene_name}"
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


def write_processing_manifest(
    run_context: RunContext,
    config_snapshot: ConfigSnapshot,
    log_write_result: RuntimeLogWriteResult,
    pipeline_result: PipelineResult,
    layout: RunDirectoryLayout,
) -> Path:
    """Write processing_manifest.json for a successful run.

    Args:
        run_context: The run context with run_id, mode, scenes, etc.
        config_snapshot: The config snapshot written for this run.
        log_write_result: The result of writing the structured log.
        pipeline_result: The final pipeline result.
        layout: The run directory layout providing the target path.

    Returns:
        The path to the written manifest file.

    Raises:
        ProcessingManifestError: If validation fails or the file cannot be written.
    """
    manifest_path = layout.processing_manifest_path.path.resolve()
    run_dir = manifest_path.parent.resolve()

    # Validate config snapshot path is not empty
    config_path = config_snapshot.snapshot_path
    if not config_path or (isinstance(config_path, Path) and str(config_path) in ("", ".")):
        raise ProcessingManifestError(
            "config_snapshot_path is required for success path manifest"
        )

    # Validate all referenced paths are inside the run directory
    _validate_paths_in_run_dir(config_path, log_write_result.log_path, run_dir)

    # Validate no failed scenes on success path
    _validate_no_failed_scenes(pipeline_result)

    # Validate config snapshot path
    config_path = config_snapshot.snapshot_path
    if not config_path or not str(config_path):
        raise ProcessingManifestError(
            "config_snapshot_path is required for success path manifest"
        )

    # Check file doesn't already exist
    if manifest_path.exists():
        raise ProcessingManifestError(
            f"processing manifest already exists: {manifest_path}"
        )

    # Ensure parent directory exists
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    # Build scene results
    scene_results_dicts = [_scene_result_to_dict(sr) for sr in pipeline_result.scene_results]

    # Build target scenes list
    target_scenes = [
        s.value if hasattr(s, "value") else str(s)
        for s in run_context.target_scenes
    ]

    # Build manifest
    now = datetime.now()
    manifest = ProcessingManifest(
        schema_version=MANIFEST_SCHEMA_VERSION,
        run_id=run_context.run_id,
        run_mode=run_context.run_mode.value if hasattr(run_context.run_mode, "value") else str(run_context.run_mode),
        service_mode=run_context.service_mode.value if hasattr(run_context.service_mode, "value") else str(run_context.service_mode),
        target_scenes=target_scenes,
        status=RunStatus.SUCCEEDED.value,
        config_snapshot_path=str(config_path),
        run_log_path=log_write_result.log_path,
        scene_results=scene_results_dicts,
        created_at=now.isoformat(),
    )

    # Write JSON
    manifest_path.write_text(
        json.dumps(manifest.to_dict(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return manifest_path
