"""Runtime wrapper for Scene 3 field alignment check developer entry.

This module provides the ``run_scene3_field_alignment_check`` function that
orchestrates the multi-strategy field alignment for the
``scene3_field_alignment_check`` developer menu entry.  It:

1. Creates an isolated run directory.
2. Loads ``source_topic_catalog.json``, ``mcap_a_input_validation_summary.json``,
   and ``step_timeline.json``.
3. Calls the multi-strategy field alignment service for each target field
   based on its modality (image/gripper → nearest_neighbor, pose → interpolation,
   tactile → window aggregate).
4. Writes ``field_alignment_results.json`` and a run log.
5. Returns a structured result dict.
"""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from typing import Any, get_args, get_origin, get_type_hints

from schemas.alignment_config import AlignmentModality, Scene3AlignmentConfig

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
    """Reconstruct a dataclass from a dict, handling nested dataclasses and enums.

    This recursively converts nested dicts and enums so that JSON-loaded
    data can be passed to ``cls(**data)``.
    """
    import dataclasses

    field_types = get_type_hints(cls) if dataclasses.is_dataclass(cls) else {}

    kwargs = {}
    for key, val in data.items():
        if key not in field_types:
            kwargs[key] = val
            continue
        target_type = field_types[key]
        # Check if target is a list of dataclasses
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


def _load_alignment_inputs(
    catalog_path: Path,
    validation_summary_path: Path,
    timeline_path: Path,
) -> dict[str, Any]:
    """Load and reconstruct alignment input dataclasses from JSON files.

    Returns:
        Dict with keys ``catalog``, ``validation_summary``, ``timeline``.

    Raises:
        FileNotFoundError: If any input file is missing.
        json.JSONDecodeError: If any input file is not valid JSON.
    """
    from schemas.alignment_input import (
        McapAInputValidationSummary,
        SourceTopicCatalog,
    )
    from schemas.step_timeline import StepTimeline

    with open(catalog_path, "r", encoding="utf-8") as f:
        catalog_data = json.load(f)
    with open(validation_summary_path, "r", encoding="utf-8") as f:
        validation_data = json.load(f)
    with open(timeline_path, "r", encoding="utf-8") as f:
        timeline_data = json.load(f)

    catalog = _reconstruct_dataclass(SourceTopicCatalog, catalog_data)
    validation_summary = _reconstruct_dataclass(
        McapAInputValidationSummary, validation_data
    )
    timeline = _reconstruct_dataclass(StepTimeline, timeline_data)

    return {
        "catalog": catalog,
        "validation_summary": validation_summary,
        "timeline": timeline,
    }


def _dispatch_field_alignment(
    *,
    timeline: Any,
    catalog: Any,
    config: Scene3AlignmentConfig,
    field_samples: dict[str, list],
) -> tuple[list[Any], dict[str, int], list[str]]:
    """Dispatch field alignment per target field based on modality.

    Args:
        timeline: Reconstructed StepTimeline dataclass.
        catalog: Reconstructed SourceTopicCatalog dataclass.
        config: Scene3AlignmentConfig with target_fields.
        field_samples: Dict mapping field_name -> list of raw sample tuples.

    Returns:
        Tuple of (results_list, status_counts_dict, failure_reasons_list).
    """
    from schemas.field_alignment import FieldAlignmentResult

    all_results: list[Any] = []
    failure_reasons: list[str] = []

    # Categorize target fields by modality
    image_gripper_mappings: list[Any] = []
    pose_fields: list[Any] = []
    tactile_fields: list[Any] = []

    for field_mapping in config.target_fields:
        if field_mapping.modality in (
            AlignmentModality.IMAGE,
            AlignmentModality.GRIPPER,
        ):
            image_gripper_mappings.append(field_mapping)
        elif field_mapping.modality == AlignmentModality.POSE:
            pose_fields.append(field_mapping)
        elif field_mapping.modality == AlignmentModality.TACTILE:
            tactile_fields.append(field_mapping)

    # 1. Image and Gripper: use align_nearest_fields
    if image_gripper_mappings:
        try:
            from service.field_aligner import align_nearest_fields

            # Build field_samples for nearest aligner: only image/gripper
            nearest_samples: dict[str, list] = {}
            for fm in image_gripper_mappings:
                if fm.field_name in field_samples:
                    nearest_samples[fm.field_name] = field_samples[fm.field_name]

            nearest_results = align_nearest_fields(
                timeline=timeline,
                catalog=catalog,
                field_mappings=image_gripper_mappings,
                field_samples=nearest_samples,
            )
            all_results.extend(nearest_results)
        except Exception as exc:
            failure_reasons.append(
                f"image_gripper_alignment_failed: {exc}"
            )

    # 2. Pose fields: use align_pose_field
    for fm in pose_fields:
        try:
            from service.pose_field_aligner import align_pose_field

            pose_samples: list = field_samples.get(fm.field_name, [])
            pose_results = align_pose_field(
                timeline=timeline,
                field_name=fm.field_name,
                source_topic=fm.source_topic,
                output_topic=fm.output_topic,
                pose_samples=pose_samples,
                max_dt_ms=fm.max_dt_ms,
                fallback_strategy=config.pose_fallback_strategy,
            )
            all_results.extend(pose_results)
        except Exception as exc:
            failure_reasons.append(
                f"pose_alignment_failed_{fm.field_name}: {exc}"
            )

    # 3. Tactile fields: use align_tactile_field
    for fm in tactile_fields:
        try:
            from service.tactile_field_aligner import align_tactile_field

            tactile_samples: list = field_samples.get(fm.field_name, [])
            tactile_results = align_tactile_field(
                timeline=timeline,
                field_name=fm.field_name,
                source_topic=fm.source_topic,
                output_topic=fm.output_topic,
                tactile_samples=tactile_samples,
                target_step_hz=float(config.target_step_hz),
            )
            all_results.extend(tactile_results)
        except Exception as exc:
            failure_reasons.append(
                f"tactile_alignment_failed_{fm.field_name}: {exc}"
            )

    # Compute status counts
    status_counts: dict[str, int] = {}
    for r in all_results:
        s = r.status if hasattr(r, "status") else "unknown"
        status_counts[s] = status_counts.get(s, 0) + 1

    return all_results, status_counts, failure_reasons


def run_scene3_field_alignment_check(
    *,
    catalog_path: str | Path,
    validation_summary_path: str | Path,
    timeline_path: str | Path,
    config: Scene3AlignmentConfig,
    field_samples: dict[str, list] | None = None,
    run_root: str | Path = Path("src/data_clean/runs"),
) -> dict[str, Any]:
    """Run the Scene 3 field alignment check as a developer entry.

    Args:
        catalog_path: Path to the ``source_topic_catalog.json`` file.
        validation_summary_path: Path to the
            ``mcap_a_input_validation_summary.json`` file.
        timeline_path: Path to the ``step_timeline.json`` file.
        config: ``Scene3AlignmentConfig`` with target_fields and alignment
            parameters.
        field_samples: Optional dict mapping field_name -> list of raw sample
            tuples.  If omitted, an empty dict is used (no alignment runs).
        run_root: Root directory under which an isolated run directory is
            created.

    Returns:
        A dict with ``run_id``, ``status`` (``"success"`` / ``"failed"``),
        ``field_count``, ``status_counts``, ``failure_reasons``, ``outputs``
        (paths), and ``run_log_path``.
    """
    catalog_path = Path(catalog_path)
    validation_summary_path = Path(validation_summary_path)
    timeline_path = Path(timeline_path)
    run_root = Path(run_root)
    field_samples = field_samples or {}

    run_directory = create_run_directory(
        run_root=run_root,
        run_date=date.today(),
        target_scenes=["scene3"],
    )
    outputs_dir = Path(run_directory.layout.outputs_dir.path)
    run_log_path = Path(run_directory.layout.run_log_path.path)
    steps: list[str] = ["create_run_directory"]
    errors: list[dict[str, str]] = []

    all_results: list[Any] = []
    status_counts: dict[str, int] = {}
    failure_reasons: list[str] = []
    field_alignment_results_path_str: str | None = None
    failure_summary_path_str: str | None = None

    try:
        inputs = _load_alignment_inputs(
            catalog_path, validation_summary_path, timeline_path
        )
        steps.append("load_input_files")

        results, counts, reasons = _dispatch_field_alignment(
            timeline=inputs["timeline"],
            catalog=inputs["catalog"],
            config=config,
            field_samples=field_samples,
        )
        all_results = results
        status_counts = counts
        failure_reasons = reasons

        if not failure_reasons:
            steps.append("run_field_alignment")
        else:
            steps.append("run_field_alignment_with_warnings")

    except FileNotFoundError as exc:
        errors.append({"type": "FileNotFoundError", "message": str(exc)})
        steps.append("load_input_files_failed")
    except json.JSONDecodeError as exc:
        errors.append({"type": "JSONDecodeError", "message": str(exc)})
        steps.append("load_input_files_failed")
    except Exception as exc:
        errors.append({"type": type(exc).__name__, "message": str(exc)})
        steps.append("run_field_alignment_failed")

    # Write field_alignment_results.json
    if not errors:
        results_path = outputs_dir / "field_alignment_results.json"
        field_alignment_results_path_str = str(results_path)
        # Serialize results (convert dataclasses to dicts)
        serialized_results = _jsonable(all_results)
        field_alignment_output = {
            "results": serialized_results,
            "summary": {
                "field_count": len(config.target_fields),
                "total_result_count": len(all_results),
                "status_counts": status_counts,
                "failure_reasons": failure_reasons,
            },
        }
        results_path.write_text(
            json.dumps(field_alignment_output, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        steps.append("write_field_alignment_results")
    elif errors:
        # Write a failure summary
        fail_path = outputs_dir / "failure_summary.json"
        failure_summary_path_str = str(fail_path)
        failure_summary = {
            "status": "failed",
            "failure_reasons": [e["message"] for e in errors],
            "catalog_path": str(catalog_path),
            "validation_summary_path": str(validation_summary_path),
            "timeline_path": str(timeline_path),
            "config_ref": "cli_override",
            "created_at": datetime.now().isoformat(),
        }
        fail_path.write_text(
            json.dumps(failure_summary, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        steps.append("write_failure_summary")

    outputs = {
        "run_dir": str(run_directory.run_dir),
        "field_alignment_results_json": field_alignment_results_path_str,
        "failure_summary_json": failure_summary_path_str,
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
        "check_id": "scene3_field_alignment_check",
        "status": status,
        "input": {
            "catalog_path": str(catalog_path),
            "validation_summary_path": str(validation_summary_path),
            "timeline_path": str(timeline_path),
        },
        "config": {
            "target_step_hz": config.target_step_hz,
            "target_field_count": len(config.target_fields),
            "source_config": "cli_override",
            "temporary_override_saved": False,
        },
        "alignment": {
            "field_count": len(config.target_fields),
            "total_result_count": len(all_results),
            "status_counts": status_counts,
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
        "field_count": len(config.target_fields),
        "status_counts": status_counts,
        "failure_reasons": failure_reasons,
    }
