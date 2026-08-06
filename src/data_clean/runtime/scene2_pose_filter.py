from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from typing import Any

from repo.config.mcap_process_config import load_app_config
from schemas.pose_filter import PoseFilterConfig, PoseFilterInputSequence, PoseFilterResult
from schemas.reliability import SignalReliabilityDetectionResult, SignalSampleRef
from schemas.repair import RepairDecisionStatus, SignalRepairResult
from service.detectors import PoseSample, ReliabilityDetectionConfig
from service.pose_filter import filter_pose_segments
from service.pose_segment import split_reliable_segments

from .run_directory_creator import create_run_directory
from .scene2_signal_reliability import SampleLoader, load_scene2_signal_samples
from .scene2_signal_repair import (
    _run_detection,
    _sample_ref_from_sample,
    compute_signal_repair,
)


def run_scene2_pose_filter(
    *,
    cleaned_mcap_path: str | Path,
    config_path: str | Path,
    run_root: str | Path = Path("src/data_clean/runs"),
    detection_config: ReliabilityDetectionConfig | None = None,
    pose_filter_config: PoseFilterConfig | None = None,
    sample_loader: SampleLoader | None = None,
) -> dict[str, Any]:
    cleaned_mcap = Path(cleaned_mcap_path)
    config_path = Path(config_path)
    run_root = Path(run_root)
    detection_config = detection_config or ReliabilityDetectionConfig()
    pose_filter_config = pose_filter_config or PoseFilterConfig()
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
    filter_path = outputs_dir / "pose_filter_result.json"
    diff_summary_path = outputs_dir / "pose_filter_diff_summary.json"
    filtered_sequences_dir = outputs_dir / "filtered_pose_sequences"
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
    filter_result = PoseFilterResult(
        input_repair_result_ref=repair_result,
        pose_filter_config_ref=pose_filter_config,
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

        repair_result = compute_signal_repair(
            samples=samples,
            detection_result=detection_result,
            config_path=config_path,
            run_id=run_directory.run_id,
        )
        repair_path.write_text(json.dumps(_jsonable(repair_result), ensure_ascii=False, indent=2), encoding="utf-8")
        steps.extend(["build_repair_runs", "find_legal_neighbors", "run_signal_repair", "write_repair_result"])

        filter_result = compute_pose_filter(
            samples=samples,
            detection_result=detection_result,
            repair_result=repair_result,
            pose_filter_config=pose_filter_config,
            repair_result_ref=repair_path,
            run_id=run_directory.run_id,
        )
        filter_result.run_id = run_directory.run_id
        filter_result.created_at = datetime.now().isoformat()
        filter_path.write_text(json.dumps(_jsonable(filter_result), ensure_ascii=False, indent=2), encoding="utf-8")
        steps.extend(["segment_pose", "filter_pose", "write_pose_filter_result"])

        diff_summary = _diff_summary(filter_result)
        diff_summary_path.write_text(json.dumps(_jsonable(diff_summary), ensure_ascii=False, indent=2), encoding="utf-8")
        filtered_sequence_refs_path.write_text(
            json.dumps(
                _jsonable(
                    {
                        "pose_filter_result_ref": str(filter_path),
                        "output_sequence_refs": filter_result.output_sequence_refs,
                    }
                ),
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        steps.extend(["write_pose_filter_diff_summary", "write_filtered_pose_sequences"])
    except Exception as exc:
        errors.append({"type": type(exc).__name__, "message": str(exc)})

    outputs = {
        "run_dir": str(run_directory.run_dir),
        "signal_reliability_detection_result_json": str(detection_path),
        "signal_repair_result_json": str(repair_path),
        "pose_filter_result_json": str(filter_path),
        "pose_filter_diff_summary_json": str(diff_summary_path),
        "filtered_pose_sequences_dir": str(filtered_sequences_dir),
    }
    run_log = {
        "run_id": run_directory.run_id,
        "check_id": "scene2_pose_filter",
        "status": "failed" if errors else "success",
        "input": {
            "cleaned_mcap": str(cleaned_mcap),
            "detection_result": str(detection_path),
            "signal_repair_result": str(repair_path),
        },
        "config": {
            "repair_policy_config_ref": str(config_path),
            "pose_filter_config": _jsonable(pose_filter_config),
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


def _split_segments_by_topic(
    pose_sequence: list[dict[str, Any]],
    missing_intervals: list[Any],
    unrepaired_refs: list[SignalSampleRef],
    config: PoseFilterConfig | None = None,
) -> list[PoseFilterSegmentSummary]:
    """Group pose samples by topic and create reliable segments per topic."""
    by_topic: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for sample in pose_sequence:
        by_topic[sample["sample_ref"].topic].append(sample)

    unrepaired_by_topic: dict[str, list[SignalSampleRef]] = defaultdict(list)
    for ref in unrepaired_refs:
        unrepaired_by_topic[ref.topic].append(ref)

    all_segments: list[PoseFilterSegmentSummary] = []
    for topic, topic_samples in by_topic.items():
        topic_unrepaired = unrepaired_by_topic.get(topic, [])
        topic_segments = split_reliable_segments(
            topic_samples,
            missing_intervals=missing_intervals,
            unrepaired_refs=topic_unrepaired,
            config=config,
        )
        all_segments.extend(topic_segments)
    return all_segments


def _repaired_pose_sequence(samples: list[PoseSample], repair_result: SignalRepairResult) -> list[dict[str, Any]]:
    repairs = _pose_repairs_by_key(repair_result)
    sequence = []
    for sample in samples:
        sample_ref = _sample_ref_from_sample(sample, "pose")
        position = {"x": sample.position[0], "y": sample.position[1], "z": sample.position[2]}
        orientation = {
            "x": sample.orientation_xyzw[0],
            "y": sample.orientation_xyzw[1],
            "z": sample.orientation_xyzw[2],
            "w": sample.orientation_xyzw[3],
        }
        for repair in repairs.get(_sample_key(sample_ref), []):
            if repair["replacement_unit"] == "pose.position" and len(repair["value"]) == 3:
                position = {"x": repair["value"][0], "y": repair["value"][1], "z": repair["value"][2]}
            elif repair["replacement_unit"] == "pose.orientation" and len(repair["value"]) == 4:
                orientation = {"x": repair["value"][0], "y": repair["value"][1], "z": repair["value"][2], "w": repair["value"][3]}
        sequence.append({"sample_ref": sample_ref, "position": position, "orientation": orientation})
    return sequence


def _pose_repairs_by_key(repair_result: SignalRepairResult) -> dict[tuple[str, int], list[dict[str, Any]]]:
    repairs: dict[tuple[str, int], list[dict[str, Any]]] = {}
    for run in repair_result.repair_runs:
        if run.modality != "pose":
            continue
        for record in run.sample_records:
            if record.status is not RepairDecisionStatus.REPAIRED:
                continue
            value = record.value_summary.get("value")
            if not isinstance(value, list):
                continue
            repairs.setdefault(_sample_key(record.sample_ref), []).append(
                {"replacement_unit": run.replacement_unit, "value": value}
            )
    return repairs


def _unrepaired_pose_refs(repair_result: SignalRepairResult) -> list[SignalSampleRef]:
    refs = []
    for run in repair_result.repair_runs:
        if run.modality != "pose":
            continue
        for record in run.sample_records:
            if record.status is not RepairDecisionStatus.REPAIRED:
                refs.append(record.sample_ref)
    return refs


def _input_sequence_refs(
    pose_sequence: list[dict[str, Any]],
    repair_result: SignalRepairResult,
    repair_path: Path,
) -> list[PoseFilterInputSequence]:
    refs_by_topic: dict[str, list[SignalSampleRef]] = {}
    for sample in pose_sequence:
        sample_ref = sample["sample_ref"]
        refs_by_topic.setdefault(sample_ref.topic, []).append(sample_ref)
    return [
        PoseFilterInputSequence(
            source_topic=topic,
            input_sequence_ref={"repair_result_ref": str(repair_path), "topic": topic},
            input_repair_result_ref=repair_result,
            sample_refs=refs,
        )
        for topic, refs in refs_by_topic.items()
    ]


def compute_pose_filter(
    *,
    samples: Any,
    detection_result: SignalReliabilityDetectionResult,
    repair_result: SignalRepairResult,
    pose_filter_config: PoseFilterConfig,
    repair_result_ref: Path | str,
    run_id: str,
) -> PoseFilterResult:
    pose_sequence = _repaired_pose_sequence(samples.pose, repair_result)
    segments = _split_segments_by_topic(
        pose_sequence,
        missing_intervals=detection_result.missing_interval_issues,
        unrepaired_refs=_unrepaired_pose_refs(repair_result),
        config=pose_filter_config,
    )
    result = filter_pose_segments(
        pose_sequence,
        segments,
        pose_filter_config,
        input_repair_result_ref=repair_result,
        input_sequence_refs=_input_sequence_refs(pose_sequence, repair_result, Path(repair_result_ref)),
    )
    result.run_id = run_id
    result.created_at = datetime.now().isoformat()
    return result


def _diff_summary(filter_result: PoseFilterResult) -> dict[str, Any]:
    return {
        "summary_by_topic": filter_result.summary_by_topic,
        "sample_count_before": filter_result.sample_count_before,
        "sample_count_after": filter_result.sample_count_after,
        "guard_rejected": sum(
            topic_summary.get("filter_rejected_by_guard", 0)
            for topic_summary in filter_result.summary_by_topic.values()
        ),
        "segment_stats": _segment_stats(filter_result),
    }


def _run_stats(
    detection_result: SignalReliabilityDetectionResult,
    repair_result: SignalRepairResult,
    filter_result: PoseFilterResult,
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
        "guard_rejected": sum(
            topic_summary.get("filter_rejected_by_guard", 0)
            for topic_summary in filter_result.summary_by_topic.values()
        ),
    }


def _segment_stats(filter_result: PoseFilterResult) -> dict[str, int]:
    return {
        "segments": len(filter_result.segment_summaries),
        "filtered": sum(segment.filtered_count for segment in filter_result.segment_summaries),
        "kept": sum(segment.kept_count for segment in filter_result.segment_summaries),
        "rejected": sum(segment.rejected_count for segment in filter_result.segment_summaries),
    }


def _sample_key(sample_ref: SignalSampleRef) -> tuple[str, int]:
    return sample_ref.topic, sample_ref.message_index


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
