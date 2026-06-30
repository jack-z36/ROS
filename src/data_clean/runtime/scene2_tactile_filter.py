from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from typing import Any

from repo.config.mcap_process_config import load_app_config
from schemas.reliability import SignalReliabilityDetectionResult, SignalSampleRef
from schemas.repair import RepairDecisionStatus, SignalRepairResult
from schemas.tactile_filter import TactileFilterConfig, TactileFilterInputSequence, TactileFilterResult
from service.detectors import ReliabilityDetectionConfig, TactilePressureFrame
from service.repair_compute import run_all_repairs
from service.repair_run import aggregate_sample_issues, build_repair_runs, find_legal_neighbors
from service.tactile_filter import aggregate_tactile_result, filter_tactile_segment, run_tactile_audit
from service.tactile_segment import split_tactile_segments

from .run_directory_creator import create_run_directory
from .scene2_signal_reliability import SampleLoader, load_scene2_signal_samples
from .scene2_signal_repair import (
    _merge_repair_results,
    _neighbor_samples,
    _run_detection,
    _sample_refs,
    _sample_value_map,
)


def run_scene2_tactile_filter(
    *,
    cleaned_mcap_path: str | Path,
    config_path: str | Path,
    run_root: str | Path = Path("src/data_clean/runs"),
    detection_config: ReliabilityDetectionConfig | None = None,
    tactile_filter_config: TactileFilterConfig | None = None,
    sample_loader: SampleLoader | None = None,
) -> dict[str, Any]:
    cleaned_mcap = Path(cleaned_mcap_path)
    config_path = Path(config_path)
    run_root = Path(run_root)
    detection_config = detection_config or ReliabilityDetectionConfig()
    tactile_filter_config = tactile_filter_config or TactileFilterConfig()
    steps = ["create_run_directory"]
    errors: list[dict[str, str]] = []

    app_config = load_app_config(config_path)
    run_directory = create_run_directory(
        run_root=run_root,
        run_date=date.today(),
        target_scenes=["scene2"],
    )
    outputs_dir = Path(run_directory.layout.outputs_dir.path)
    detection_path = outputs_dir / "signal_reliability_detection_result.json"
    repair_path = outputs_dir / "signal_repair_result.json"
    filter_path = outputs_dir / "tactile_filter_result.json"
    diff_summary_path = outputs_dir / "tactile_filter_diff_summary.json"
    filtered_sequences_dir = outputs_dir / "filtered_tactile_sequences"
    filtered_sequences_dir.mkdir(parents=True, exist_ok=True)
    filtered_sequence_refs_path = filtered_sequences_dir / "filtered_sequence_refs.json"
    run_log_path = Path(run_directory.layout.run_log_path.path)

    detection_result = SignalReliabilityDetectionResult(
        input_cleaned_mcap=str(cleaned_mcap),
        rule_config_ref=str(config_path),
        run_id=run_directory.run_id,
    )
    repair_result = SignalRepairResult(
        input_detection_result_ref=detection_result,
        repair_policy_config_ref=str(config_path),
        run_id=run_directory.run_id,
        created_at=datetime.now().isoformat(),
    )
    filter_result = TactileFilterResult(
        input_repair_result_ref=repair_result,
        tactile_filter_config_ref=tactile_filter_config,
        input_sequence_refs=[],
        output_sequence_refs={},
        run_id=run_directory.run_id,
        created_at=datetime.now().isoformat(),
    )

    try:
        samples = (sample_loader or load_scene2_signal_samples)(cleaned_mcap, app_config)
        steps.append("load_cleaned_mcap")

        detection_result = _run_detection(
            samples=samples,
            cleaned_mcap=cleaned_mcap,
            config_path=config_path,
            detection_config=detection_config,
            run_id=run_directory.run_id,
        )
        detection_path.write_text(json.dumps(_jsonable(detection_result), ensure_ascii=False, indent=2), encoding="utf-8")
        steps.extend(["detect_pose", "detect_gripper", "detect_tactile", "write_detection_result"])

        issue_groups = aggregate_sample_issues(detection_result.sample_issues)
        repair_runs = build_repair_runs(issue_groups, detection_result.missing_interval_issues)
        sample_refs = _sample_refs(samples)
        sample_values = _sample_value_map(samples)
        neighbors = {
            run.repair_run_id: _neighbor_samples(
                run.replacement_unit,
                find_legal_neighbors(run.input_window_refs, sample_refs, issue_groups, detection_result.missing_interval_issues),
                sample_values,
            )
            for run in repair_runs
        }
        partial_results = run_all_repairs(repair_runs, neighbors)
        repair_result = _merge_repair_results(
            detection_result=detection_result,
            config_path=config_path,
            partial_results=partial_results,
            run_id=run_directory.run_id,
        )
        repair_path.write_text(json.dumps(_jsonable(repair_result), ensure_ascii=False, indent=2), encoding="utf-8")
        steps.extend(["build_repair_runs", "find_legal_neighbors", "run_signal_repair", "write_repair_result"])

        tactile_sequence = _repaired_tactile_sequence(samples.tactile, repair_result)
        segments = split_tactile_segments(
            tactile_sequence,
            missing_intervals=detection_result.missing_interval_issues,
            config=tactile_filter_config,
        )
        records = run_tactile_audit(filter_tactile_segment(tactile_sequence, tactile_filter_config), tactile_sequence)
        filter_result = aggregate_tactile_result(segments, records, tactile_sequence)
        filter_result.input_repair_result_ref = repair_result
        filter_result.tactile_filter_config_ref = tactile_filter_config
        filter_result.input_sequence_refs = _input_sequence_refs(tactile_sequence, repair_result, repair_path)
        filter_result.run_id = run_directory.run_id
        filter_result.created_at = datetime.now().isoformat()
        filter_path.write_text(json.dumps(_jsonable(filter_result), ensure_ascii=False, indent=2), encoding="utf-8")
        steps.extend(["segment_tactile", "filter_tactile", "write_tactile_filter_result"])

        diff_summary = _diff_summary(filter_result)
        diff_summary_path.write_text(json.dumps(_jsonable(diff_summary), ensure_ascii=False, indent=2), encoding="utf-8")
        filtered_sequence_refs_path.write_text(
            json.dumps(
                _jsonable(
                    {
                        "tactile_filter_result_ref": str(filter_path),
                        "output_sequence_refs": filter_result.output_sequence_refs,
                    }
                ),
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        steps.extend(["write_tactile_filter_diff_summary", "write_filtered_tactile_sequences"])
    except Exception as exc:
        errors.append({"type": type(exc).__name__, "message": str(exc)})

    outputs = {
        "run_dir": str(run_directory.run_dir),
        "signal_reliability_detection_result_json": str(detection_path),
        "signal_repair_result_json": str(repair_path),
        "tactile_filter_result_json": str(filter_path),
        "tactile_filter_diff_summary_json": str(diff_summary_path),
        "filtered_tactile_sequences_dir": str(filtered_sequences_dir),
    }
    run_log = {
        "run_id": run_directory.run_id,
        "check_id": "scene2_tactile_filter",
        "status": "failed" if errors else "success",
        "input": {
            "cleaned_mcap": str(cleaned_mcap),
            "detection_result": str(detection_path),
            "signal_repair_result": str(repair_path),
        },
        "config": {
            "repair_policy_config_ref": str(config_path),
            "tactile_filter_config": _jsonable(tactile_filter_config),
            "temporary_override_saved": False,
        },
        "steps": steps + ["write_run_log"],
        "stats": _run_stats(detection_result, repair_result, filter_result),
        "errors": errors,
        "outputs": outputs,
        "created_at": datetime.now().isoformat(),
    }
    run_log_path.write_text(json.dumps(_jsonable(run_log), ensure_ascii=False, indent=2), encoding="utf-8")
    return {**run_log, "run_log_path": str(run_log_path)}


def _repaired_tactile_sequence(frames: list[TactilePressureFrame], repair_result: SignalRepairResult) -> list[dict[str, Any]]:
    repairs = _tactile_repairs_by_key(repair_result)
    sequence = []
    for frame in frames:
        sample_ref = SignalSampleRef(
            topic=frame.topic,
            timestamp=frame.timestamp_ns,
            message_index=frame.message_index,
            modality="tactile",
            time_domain=frame.time_domain,
        )
        matrix = [frame.data[index : index + frame.cols] for index in range(0, len(frame.data), frame.cols)]
        status = "repaired" if _sample_key(sample_ref) in repairs else "kept_original"
        value = repairs.get(_sample_key(sample_ref), matrix)
        sequence.append(
            {
                "sample_ref": sample_ref,
                "topic": frame.topic,
                "timestamp_ns": frame.timestamp_ns,
                "message_index": frame.message_index,
                "time_domain": frame.time_domain,
                "hand": frame.hand,
                "gripper": frame.gripper,
                "rows": frame.rows,
                "cols": frame.cols,
                "data": _flatten_matrix(value),
                "status": status,
            }
        )
    return sequence


def _tactile_repairs_by_key(repair_result: SignalRepairResult) -> dict[tuple[str, int], list[list[float]]]:
    repairs: dict[tuple[str, int], list[list[float]]] = {}
    for run in repair_result.repair_runs:
        if run.modality != "tactile":
            continue
        for record in run.sample_records:
            if record.status is not RepairDecisionStatus.REPAIRED:
                continue
            value = record.value_summary.get("value")
            if _is_matrix(value):
                repairs[_sample_key(record.sample_ref)] = [[float(cell) for cell in row] for row in value]
    return repairs


def _input_sequence_refs(
    tactile_sequence: list[dict[str, Any]],
    repair_result: SignalRepairResult,
    repair_path: Path,
) -> list[TactileFilterInputSequence]:
    refs_by_topic: dict[str, list[SignalSampleRef]] = {}
    for frame in tactile_sequence:
        sample_ref = frame["sample_ref"]
        refs_by_topic.setdefault(sample_ref.topic, []).append(sample_ref)
    return [
        TactileFilterInputSequence(
            source_topic=topic,
            input_sequence_ref={"repair_result_ref": str(repair_path), "topic": topic},
            input_repair_result_ref=repair_result,
            sample_refs=refs,
        )
        for topic, refs in refs_by_topic.items()
    ]


def _diff_summary(filter_result: TactileFilterResult) -> dict[str, Any]:
    return {
        "summary_by_topic": filter_result.summary_by_topic,
        "sample_count_before": filter_result.sample_count_before,
        "sample_count_after": filter_result.sample_count_after,
        "segment_stats": _segment_stats(filter_result),
        "diff_summary": _record_diff_summary(filter_result),
    }


def _run_stats(
    detection_result: SignalReliabilityDetectionResult,
    repair_result: SignalRepairResult,
    filter_result: TactileFilterResult,
) -> dict[str, Any]:
    return {
        "sample_issue_count": len(detection_result.sample_issues),
        "missing_interval_issue_count": len(detection_result.missing_interval_issues),
        "repair_runs": len(repair_result.repair_runs),
        "summary_by_modality": repair_result.summary_by_modality,
        "summary_by_topic": filter_result.summary_by_topic,
        "sample_count_before": filter_result.sample_count_before,
        "sample_count_after": filter_result.sample_count_after,
        "segment_stats": _segment_stats(filter_result),
        "diff_summary": _record_diff_summary(filter_result),
    }


def _segment_stats(filter_result: TactileFilterResult) -> dict[str, int]:
    return {
        "segments": len(filter_result.segment_summaries),
        "filtered": sum(segment.filtered_count for segment in filter_result.segment_summaries),
        "kept_original": sum(segment.kept_original_count for segment in filter_result.segment_summaries),
        "reset": sum(segment.ema_reset_count for segment in filter_result.segment_summaries),
        "skipped": sum(segment.skipped_boundary_count for segment in filter_result.segment_summaries),
        "invalid_shape": sum(segment.invalid_shape_count for segment in filter_result.segment_summaries),
    }


def _record_diff_summary(filter_result: TactileFilterResult) -> dict[str, float | int]:
    changed_cell_count = 0
    max_abs_delta = 0.0
    weighted_delta = 0.0
    cell_count = 0
    for record in filter_result.sample_records:
        diff = record.filtered_value_summary.get("diff_summary") or {}
        changed_cell_count += int(diff.get("changed_cell_count", 0))
        max_abs_delta = max(max_abs_delta, float(diff.get("max_abs_delta", 0.0)))
        shape = record.filtered_value_summary.get("shape") or {}
        record_cell_count = int(shape.get("cell_count", 0))
        weighted_delta += float(diff.get("mean_abs_delta", 0.0)) * record_cell_count
        cell_count += record_cell_count
    return {
        "changed_cell_count": changed_cell_count,
        "mean_abs_delta": weighted_delta / cell_count if cell_count else 0.0,
        "max_abs_delta": max_abs_delta,
    }


def _sample_key(sample_ref: SignalSampleRef) -> tuple[str, int]:
    return sample_ref.topic, sample_ref.message_index


def _flatten_matrix(value: Any) -> list[float | int]:
    if not isinstance(value, list):
        return []
    if not value or not isinstance(value[0], list):
        return list(value)
    return [cell for row in value for cell in row]


def _is_matrix(value: Any) -> bool:
    return isinstance(value, list) and all(isinstance(row, list) for row in value)


def _jsonable(value: Any) -> Any:
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
