"""Runtime wrapper for Scene 3 alignment report check developer entry.

This module provides the ``run_scene3_alignment_report_check`` function that
orchestrates the alignment index normalization and report draft generation
for the ``scene3_alignment_report_check`` developer menu entry.  It:

1. Creates an isolated run directory.
2. Loads ``field_alignment_results.json``, ``step_timeline.json``,
   ``source_topic_catalog.json``, and ``mcap_a_input_validation_summary.json``.
3. Calls ``build_alignment_index_records()`` for normalization.
4. Calls ``build_alignment_report_draft()`` for report statistics.
5. Writes ``alignment_index_preview.json``, ``alignment_report_draft.json``,
   and a run log.
6. Returns a structured result dict.
"""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from typing import Any, get_args, get_origin, get_type_hints

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


def _reconstruct_dataclass(cls: type, data: dict) -> Any:
    """Reconstruct a dataclass from a dict, handling nested dataclasses and enums."""
    import dataclasses

    field_types = get_type_hints(cls) if dataclasses.is_dataclass(cls) else {}

    kwargs = {}
    for key, val in data.items():
        if key not in field_types:
            kwargs[key] = val
            continue
        target_type = field_types[key]
        origin = get_origin(target_type)
        args = get_args(target_type)

        if origin is list and args and dataclasses.is_dataclass(args[0]):
            inner_cls = args[0]
            kwargs[key] = [_reconstruct_dataclass(inner_cls, item) for item in val]
        elif origin is list and args and isinstance(val, list):
            kwargs[key] = val
        elif isinstance(val, dict) and dataclasses.is_dataclass(target_type):
            kwargs[key] = _reconstruct_dataclass(target_type, val)
        elif isinstance(val, str) and _is_enum_type(target_type):
            kwargs[key] = target_type(val)
        else:
            kwargs[key] = val

    return cls(**kwargs)


def _is_enum_type(tp: type) -> bool:
    """Check if a type annotation is an Enum class."""
    try:
        return issubclass(tp, Enum)
    except TypeError:
        return False


def _load_field_alignment_results(results_path: Path) -> list:
    """Load and reconstruct FieldAlignmentResult list from JSON."""
    from schemas.field_alignment import FieldAlignmentResult

    with open(results_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    raw_results = data.get("results", [])
    return [_reconstruct_dataclass(FieldAlignmentResult, item) for item in raw_results]


def _load_step_timeline(timeline_path: Path) -> Any:
    """Load and reconstruct StepTimeline from JSON."""
    from schemas.step_timeline import StepTimeline

    with open(timeline_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return _reconstruct_dataclass(StepTimeline, data)


def _load_catalog(catalog_path: Path) -> Any:
    """Load and reconstruct SourceTopicCatalog from JSON."""
    from schemas.alignment_input import SourceTopicCatalog

    with open(catalog_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return _reconstruct_dataclass(SourceTopicCatalog, data)


def _load_validation_summary(validation_summary_path: Path) -> Any:
    """Load and reconstruct McapAInputValidationSummary from JSON."""
    from schemas.alignment_input import McapAInputValidationSummary

    with open(validation_summary_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return _reconstruct_dataclass(McapAInputValidationSummary, data)


def run_scene3_alignment_report_check(
    *,
    field_alignment_results_path: str | Path,
    timeline_path: str | Path,
    catalog_path: str | Path,
    validation_summary_path: str | Path,
    config: Scene3AlignmentConfig,
    run_root: str | Path = Path("src/data_clean/runs"),
) -> dict[str, Any]:
    """Run the Scene 3 alignment report check as a developer entry.

    Args:
        field_alignment_results_path: Path to ``field_alignment_results.json``
            produced by the field alignment check.
        timeline_path: Path to ``step_timeline.json``.
        catalog_path: Path to ``source_topic_catalog.json``.
        validation_summary_path: Path to
            ``mcap_a_input_validation_summary.json``.
        config: ``Scene3AlignmentConfig`` with alignment parameters.
        run_root: Root directory under which an isolated run directory is
            created.

    Returns:
        A dict with ``run_id``, ``status`` (``"success"`` / ``"failed"``),
        ``record_count``, ``report_status``, ``outputs`` (paths), and
        ``run_log_path``.
    """
    field_alignment_results_path = Path(field_alignment_results_path)
    timeline_path = Path(timeline_path)
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

    index_records = None
    report_draft = None
    alignment_index_preview_path_str: str | None = None
    alignment_report_draft_path_str: str | None = None
    record_count = 0
    report_status: str | None = None
    failure_reason: str | None = None

    try:
        # Step 1: Load field alignment results
        results = _load_field_alignment_results(field_alignment_results_path)
        steps.append("load_field_alignment_results")

        # Step 2: Build AlignmentIndex records
        from service.alignment_report import build_alignment_index_records

        index_result = build_alignment_index_records(results)
        index_records = index_result.get("records", [])
        failure_reason = index_result.get("failure_reason")

        if failure_reason:
            steps.append("build_alignment_index_failed")
        else:
            steps.append("build_alignment_index")
            record_count = index_result.get("record_count", 0)

            # Step 3: Load timeline, catalog, validation_summary
            timeline = _load_step_timeline(timeline_path)
            steps.append("load_step_timeline")

            catalog = _load_catalog(catalog_path)
            steps.append("load_source_topic_catalog")

            validation_summary = _load_validation_summary(validation_summary_path)
            steps.append("load_validation_summary")

            # Step 4: Build AlignmentReport draft
            from service.alignment_report import build_alignment_report_draft

            report_draft = build_alignment_report_draft(
                alignment_index_records=index_records,
                step_timeline=timeline,
                input_mcap_a=str(field_alignment_results_path),
                config_ref="scene3_alignment",
                input_validation_summary=validation_summary,
            )
            report_status = report_draft.status
            if report_draft.failure_reason:
                failure_reason = report_draft.failure_reason
                steps.append("build_alignment_report_failed")
            else:
                steps.append("build_alignment_report")

    except FileNotFoundError as exc:
        errors.append({"type": "FileNotFoundError", "message": str(exc)})
        steps.append("load_input_files_failed")
    except json.JSONDecodeError as exc:
        errors.append({"type": "JSONDecodeError", "message": str(exc)})
        steps.append("load_input_files_failed")
    except Exception as exc:
        errors.append({"type": type(exc).__name__, "message": str(exc)})
        steps.append("processing_failed")

    # Write alignment_index_preview.json
    if index_records is not None and not errors and not failure_reason:
        preview_path = outputs_dir / "alignment_index_preview.json"
        alignment_index_preview_path_str = str(preview_path)
        preview_data = {
            "records": _jsonable(index_records),
            "record_count": record_count,
            "failure_reason": failure_reason,
        }
        preview_path.write_text(
            json.dumps(preview_data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        steps.append("write_alignment_index_preview")

    # Write alignment_report_draft.json
    if report_draft is not None and not errors and not failure_reason:
        report_path = outputs_dir / "alignment_report_draft.json"
        alignment_report_draft_path_str = str(report_path)
        report_path.write_text(
            json.dumps(_jsonable(report_draft), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        steps.append("write_alignment_report_draft")

    outputs = {
        "run_dir": str(run_directory.run_dir),
        "alignment_index_preview_json": alignment_index_preview_path_str,
        "alignment_report_draft_json": alignment_report_draft_path_str,
    }

    # Determine overall status
    status = "success"
    if errors:
        status = "failed"
    elif failure_reason:
        status = "failed"

    # Build and write run log
    run_log = {
        "run_id": run_directory.run_id,
        "check_id": "scene3_alignment_report_check",
        "status": status,
        "input": {
            "field_alignment_results_path": str(field_alignment_results_path),
            "timeline_path": str(timeline_path),
            "catalog_path": str(catalog_path),
            "validation_summary_path": str(validation_summary_path),
        },
        "config": {
            "target_step_hz": config.target_step_hz,
            "source_config": "cli_override",
            "temporary_override_saved": False,
        },
        "alignment": {
            "record_count": record_count,
            "report_status": report_status,
            "failure_reason": failure_reason,
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
        "record_count": record_count,
        "report_status": report_status,
    }
