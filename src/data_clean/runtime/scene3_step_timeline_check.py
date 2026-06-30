"""Runtime wrapper for Scene 3 step timeline check developer entry.

This module provides the ``run_scene3_step_timeline_check`` function that
orchestrates the step timeline generation for the ``scene3_step_timeline_check``
developer menu entry.  It:

1. Creates an isolated run directory.
2. Loads ``source_topic_catalog.json`` and ``mcap_a_input_validation_summary.json``.
3. Calls the ``generate_step_timeline`` service.
4. Writes ``step_timeline.json``, ``step_timeline_generation_summary.json``,
   and a run log.
5. Returns a structured result dict.
"""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from typing import Any

from schemas.alignment_config import Scene3AlignmentConfig

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


def run_scene3_step_timeline_check(
    *,
    catalog_path: str | Path,
    validation_summary_path: str | Path,
    config: Scene3AlignmentConfig,
    run_root: str | Path = Path("src/data_clean/runs"),
    timeline_id: str = "step_timeline",
) -> dict[str, Any]:
    """Run the Scene 3 step timeline check as a developer entry.

    Args:
        catalog_path: Path to the ``source_topic_catalog.json`` file.
        validation_summary_path: Path to the ``mcap_a_input_validation_summary.json`` file.
        config: ``Scene3AlignmentConfig`` with target_step_hz, baseline_image_topics, etc.
        run_root: Root directory under which an isolated run directory is created.
        timeline_id: Identifier for the generated timeline.

    Returns:
        A dict with ``run_id``, ``status`` (``"success"`` / ``"failed"``),
        ``step_count``, ``failure_reasons``, ``first_step_time_ns``,
        ``last_step_time_ns``, ``outputs`` (paths), and ``run_log_path``.
    """
    catalog_path = Path(catalog_path)
    validation_summary_path = Path(validation_summary_path)
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

    timeline = None
    gen_summary = None
    failure_reasons: list[str] = []
    step_count = 0
    first_step_time_ns: int | None = None
    last_step_time_ns: int | None = None

    try:
        # Load input files
        with open(catalog_path, "r", encoding="utf-8") as f:
            catalog_data = json.load(f)
        with open(validation_summary_path, "r", encoding="utf-8") as f:
            validation_data = json.load(f)

        steps.append("load_input_files")

        # Import and call the step timeline generator service
        from schemas.alignment_input import (
            McapAInputValidationSummary,
            SourceTopicCatalog,
        )
        from service.step_timeline_generator import generate_step_timeline

        # Reconstruct dataclasses from dicts
        catalog = SourceTopicCatalog(**catalog_data)
        validation_summary = McapAInputValidationSummary(**validation_data)

        timeline, gen_summary = generate_step_timeline(
            validation_summary=validation_summary,
            catalog=catalog,
            config=config,
            timeline_id=timeline_id,
        )
        steps.append("run_step_timeline_generation")

        if timeline is not None:
            step_count = len(timeline.steps)
            first_step_time_ns = timeline.steps[0].step_time_ns if timeline.steps else None
            last_step_time_ns = timeline.steps[-1].step_time_ns if timeline.steps else None
        else:
            step_count = 0

        if gen_summary is not None:
            failure_reasons = list(gen_summary.failure_reasons)

    except Exception as exc:
        errors.append({"type": type(exc).__name__, "message": str(exc)})
        steps.append("run_step_timeline_generation_failed")

    # Write step_timeline.json
    step_timeline_path_str: str | None = None
    if timeline is not None:
        tl_path = outputs_dir / "step_timeline.json"
        step_timeline_path_str = str(tl_path)
        tl_path.write_text(
            json.dumps(_jsonable(timeline), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        steps.append("write_step_timeline")

    # Write step_timeline_generation_summary.json
    gen_summary_path_str: str | None = None
    if gen_summary is not None:
        gs_path = outputs_dir / "step_timeline_generation_summary.json"
        gen_summary_path_str = str(gs_path)
        gs_path.write_text(
            json.dumps(_jsonable(gen_summary), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        steps.append("write_step_timeline_generation_summary")
    elif errors:
        # Write a failure summary when generation failed entirely
        gs_path = outputs_dir / "step_timeline_generation_summary.json"
        gen_summary_path_str = str(gs_path)
        failure_summary = {
            "status": "failed",
            "failure_reasons": [e["message"] for e in errors],
            "source_topic_catalog_ref": str(catalog_path),
            "input_validation_summary_ref": str(validation_summary_path),
            "config_ref": "cli_override",
            "timeline_ref": None,
            "target_step_hz": config.target_step_hz,
            "baseline_intersection_start_ns": None,
            "baseline_intersection_end_ns": None,
            "step_count": 0,
            "first_step_time_ns": None,
            "last_step_time_ns": None,
            "created_at": datetime.now().isoformat(),
        }
        gs_path.write_text(
            json.dumps(failure_summary, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        steps.append("write_step_timeline_generation_summary")

    outputs = {
        "run_dir": str(run_directory.run_dir),
        "step_timeline_json": step_timeline_path_str,
        "step_timeline_generation_summary_json": gen_summary_path_str,
    }

    # Determine overall status
    status = "success"
    if errors:
        status = "failed"
    elif failure_reasons:
        status = "failed"

    # Build and write run log
    run_log = {
        "run_id": run_directory.run_id,
        "check_id": "scene3_step_timeline_check",
        "status": status,
        "input": {
            "catalog_path": str(catalog_path),
            "validation_summary_path": str(validation_summary_path),
        },
        "config": {
            "target_step_hz": config.target_step_hz,
            "source_config": "cli_override",
            "temporary_override_saved": False,
        },
        "timeline": {
            "step_count": step_count,
            "first_step_time_ns": first_step_time_ns,
            "last_step_time_ns": last_step_time_ns,
            "failure_reasons": failure_reasons,
        },
        "steps": steps + ["write_run_log"],
        "errors": errors,
        "outputs": outputs,
        "created_at": datetime.now().isoformat(),
    }
    run_log_path.write_text(
        json.dumps(_jsonable(run_log), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return {
        **run_log,
        "run_log_path": str(run_log_path),
        "step_count": step_count,
        "first_step_time_ns": first_step_time_ns,
        "last_step_time_ns": last_step_time_ns,
        "failure_reasons": failure_reasons,
    }
