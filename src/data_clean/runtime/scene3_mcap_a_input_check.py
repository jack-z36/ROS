"""Runtime wrapper for Scene 3 MCAP_A input check developer entry.

This module provides the ``run_scene3_mcap_a_input_check`` function that
orchestrates the MCAP_A input validation for the ``scene3_mcap_a_input_check``
developer menu entry.  It:

1. Creates an isolated run directory.
2. Calls the ``validate_mcap_a_input`` service.
3. Writes ``source_topic_catalog.json``, ``mcap_a_input_validation_summary.json``,
   and a run log.
4. Returns a structured result dict.
"""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from typing import Any

from schemas.alignment_config import Scene3AlignmentConfig, TargetFieldMapping
from service.mcap_a_input_validator import validate_mcap_a_input

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


def run_scene3_mcap_a_input_check(
    *,
    mcap_a_path: str | Path,
    summary_path: str | Path,
    config: Scene3AlignmentConfig,
    run_root: str | Path = Path("src/data_clean/runs"),
) -> dict[str, Any]:
    """Run the Scene 3 MCAP_A input check as a developer entry.

    Args:
        mcap_a_path: Path to the MCAP_A file to validate.
        summary_path: Path to the ``mcap_a_write_summary.json`` file.
        config: ``Scene3AlignmentConfig`` with baseline image topics,
            target field mappings, etc.
        run_root: Root directory under which an isolated run directory
            is created.

    Returns:
        A dict with ``run_id``, ``status`` (``"success"`` / ``"failed"``),
        ``input``, ``config``, ``validation`` summary, ``steps``, ``errors``,
        ``outputs`` (paths), and ``run_log_path``.
    """
    mcap_a = Path(mcap_a_path)
    summary = Path(summary_path)
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

    catalog = None
    validation_summary = None
    optional_warnings: list[str] = []

    try:
        (
            catalog,
            validation_summary,
            _intersection_start,
            _intersection_end,
            optional_warnings,
        ) = validate_mcap_a_input(
            mcap_path=str(mcap_a),
            summary_path=str(summary),
            config=config,
            field_mappings=config.target_fields,
        )
        steps.append("run_mcap_a_input_validation")
    except Exception as exc:
        errors.append({"type": type(exc).__name__, "message": str(exc)})
        steps.append("run_mcap_a_input_validation_failed")

    # Write source_topic_catalog.json
    catalog_json_path: str | None = None
    if catalog is not None:
        catalog_path = outputs_dir / "source_topic_catalog.json"
        catalog_json_path = str(catalog_path)
        catalog_path.write_text(
            json.dumps(_jsonable(catalog), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        steps.append("write_source_topic_catalog")

    # Write mcap_a_input_validation_summary.json
    summary_json_path: str | None = None
    if validation_summary is not None:
        summary_path_out = outputs_dir / "mcap_a_input_validation_summary.json"
        summary_json_path = str(summary_path_out)
        summary_path_out.write_text(
            json.dumps(_jsonable(validation_summary), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        steps.append("write_mcap_a_input_validation_summary")

    outputs = {
        "run_dir": str(run_directory.run_dir),
        "source_topic_catalog_json": catalog_json_path,
        "mcap_a_input_validation_summary_json": summary_json_path,
    }

    # Determine overall status
    status = "success"
    if errors:
        status = "failed"
    elif validation_summary is not None:
        s = validation_summary.status
        if hasattr(s, "value"):
            s = s.value
        if s == "not_consumable":
            status = "failed"

    # Build and write run log
    hard_fail_reasons: list[str] = []
    warnings_list: list[str] = []
    base_topics_present = False
    has_intersection = False
    if validation_summary is not None:
        hard_fail_reasons = list(validation_summary.hard_fail_reasons)
        warnings_list = list(validation_summary.warnings)
        base_topics_present = bool(validation_summary.baseline_topics_present)
        has_intersection = bool(validation_summary.has_baseline_intersection)

    run_log = {
        "run_id": run_directory.run_id,
        "check_id": "scene3_mcap_a_input_check",
        "status": status,
        "input": {
            "mcap_a_path": str(mcap_a),
            "summary_path": str(summary),
        },
        "config": {
            "baseline_image_topics": config.baseline_image_topics,
            "target_fields_count": len(config.target_fields),
            "source_config": "cli_override",
            "temporary_override_saved": False,
        },
        "validation": {
            "hard_fail_reasons": hard_fail_reasons,
            "warnings": warnings_list,
            "optional_field_warnings": optional_warnings,
            "baseline_topics_present": base_topics_present,
            "has_baseline_intersection": has_intersection,
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

    return {**run_log, "run_log_path": str(run_log_path)}
