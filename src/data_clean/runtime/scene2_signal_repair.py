from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from typing import Any

from repo.config.mcap_process_config import load_app_config
from schemas.reliability import SignalReliabilityDetectionResult, SignalSampleRef
from schemas.repair import RepairDecisionStatus, SignalIssueDisposition, SignalRepairResult
from service.detectors import (
    GripperSample,
    ReliabilityDetectionConfig,
    TactilePressureFrame,
    detect_gripper_reliability,
    detect_pose_reliability,
    detect_tactile_reliability,
)
from service.repair_compute import NeighborSample, run_all_repairs
from service.repair_run import aggregate_sample_issues, build_repair_runs, decide_issue_dispositions, find_legal_neighbors

from .run_directory_creator import create_run_directory
from .scene2_signal_reliability import SampleLoader, load_scene2_signal_samples, merge_detection_results


def run_scene2_signal_repair(
    *,
    cleaned_mcap_path: str | Path,
    config_path: str | Path,
    run_root: str | Path = Path("src/data_clean/runs"),
    detection_config: ReliabilityDetectionConfig | None = None,
    sample_loader: SampleLoader | None = None,
) -> dict[str, Any]:
    cleaned_mcap = Path(cleaned_mcap_path)
    config_path = Path(config_path)
    run_root = Path(run_root)
    detection_config = detection_config or ReliabilityDetectionConfig()
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
    repaired_sequences_dir = outputs_dir / "repaired_sequences"
    repaired_sequences_dir.mkdir(parents=True, exist_ok=True)
    sequence_refs_path = repaired_sequences_dir / "repaired_sequence_refs.json"
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
        steps.extend(["build_repair_runs", "find_legal_neighbors"])
        repair_path.write_text(json.dumps(_jsonable(repair_result), ensure_ascii=False, indent=2), encoding="utf-8")
        steps.append("write_repair_result")

        sequence_refs_path.write_text(
            json.dumps(
                _jsonable(
                    {
                        "repair_result_ref": str(repair_path),
                        "output_sequence_refs": repair_result.output_sequence_refs,
                        "repair_runs": repair_result.repair_runs,
                    }
                ),
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        steps.append("write_repaired_sequences")
    except Exception as exc:
        errors.append({"type": type(exc).__name__, "message": str(exc)})

    outputs = {
        "run_dir": str(run_directory.run_dir),
        "signal_reliability_detection_result_json": str(detection_path),
        "signal_repair_result_json": str(repair_path),
        "repaired_sequences_dir": str(repaired_sequences_dir),
    }
    run_log = {
        "run_id": run_directory.run_id,
        "check_id": "scene2_signal_repair",
        "status": "failed" if errors else "success",
        "input": {"cleaned_mcap": str(cleaned_mcap), "detection_result": str(detection_path)},
        "config": {
            "repair_policy_config_ref": str(config_path),
            "temporary_override_saved": False,
        },
        "steps": steps + ["write_run_log"],
        "stats": _run_stats(detection_result, repair_result),
        "errors": errors,
        "outputs": outputs,
        "created_at": datetime.now().isoformat(),
    }
    run_log_path.write_text(json.dumps(_jsonable(run_log), ensure_ascii=False, indent=2), encoding="utf-8")
    return {**run_log, "run_log_path": str(run_log_path)}


def _run_detection(
    *,
    samples: Any,
    cleaned_mcap: Path,
    config_path: Path,
    detection_config: ReliabilityDetectionConfig,
    run_id: str,
) -> SignalReliabilityDetectionResult:
    pose_result = detect_pose_reliability(
        samples.pose,
        config=detection_config,
        input_cleaned_mcap=str(cleaned_mcap),
        rule_config_ref=str(config_path),
    )
    gripper_result = detect_gripper_reliability(
        samples.gripper,
        config=detection_config,
        input_cleaned_mcap=str(cleaned_mcap),
        rule_config_ref=str(config_path),
    )
    tactile_result = detect_tactile_reliability(
        samples.tactile,
        config=detection_config,
        input_cleaned_mcap=str(cleaned_mcap),
        rule_config_ref=str(config_path),
    )
    return merge_detection_results(
        input_cleaned_mcap=str(cleaned_mcap),
        rule_config_ref=str(config_path),
        results=(pose_result, gripper_result, tactile_result),
        run_id=run_id,
    )


def _sample_refs(samples: Any) -> list[SignalSampleRef]:
    return [*_pose_refs(samples.pose), *_gripper_refs(samples.gripper), *_tactile_refs(samples.tactile)]


def _sample_value_map(samples: Any) -> dict[tuple[str, str, int | float, int, str], NeighborSample]:
    values: dict[tuple[str, str, int | float, int, str], NeighborSample] = {}
    for sample in samples.pose:
        position_ref = _sample_ref_from_sample(sample, "pose")
        values[_value_key(position_ref, "pose.position")] = {"sample_ref": position_ref, "value": list(sample.position)}
        orientation_ref = position_ref
        values[_value_key(orientation_ref, "pose.orientation")] = {"sample_ref": orientation_ref, "value": list(sample.orientation_xyzw)}
    for sample in samples.gripper:
        sample_ref = _sample_ref_from_sample(sample, "gripper")
        values[_value_key(sample_ref, "gripper.value")] = {"sample_ref": sample_ref, "value": sample.value}
    for frame in samples.tactile:
        sample_ref = _sample_ref_from_sample(frame, "tactile")
        values[_value_key(sample_ref, "tactile.frame")] = {"sample_ref": sample_ref, "value": _tactile_matrix(frame)}
    return values


def _pose_refs(samples: list[Any]) -> list[SignalSampleRef]:
    return [_sample_ref_from_sample(sample, "pose") for sample in samples]


def _gripper_refs(samples: list[GripperSample]) -> list[SignalSampleRef]:
    return [_sample_ref_from_sample(sample, "gripper") for sample in samples]


def _tactile_refs(frames: list[TactilePressureFrame]) -> list[SignalSampleRef]:
    return [_sample_ref_from_sample(frame, "tactile") for frame in frames]


def _sample_ref(
    topic: str,
    timestamp: int | float,
    message_index: int,
    modality: str,
    time_domain: str,
    *,
    log_time_ns: int | None = None,
    publish_time_ns: int | None = None,
    sequence: int | None = None,
    source_channel_id: int | None = None,
) -> SignalSampleRef:
    return SignalSampleRef(
        topic=topic,
        timestamp=timestamp,
        message_index=message_index,
        modality=modality,
        time_domain=time_domain,
        log_time_ns=log_time_ns,
        publish_time_ns=publish_time_ns,
        sequence=sequence,
        source_channel_id=source_channel_id,
    )


def _sample_ref_from_sample(sample: Any, modality: str) -> SignalSampleRef:
    return _sample_ref(
        sample.topic,
        sample.timestamp_ns,
        sample.message_index,
        modality,
        sample.time_domain,
        log_time_ns=getattr(sample, "log_time_ns", None),
        publish_time_ns=getattr(sample, "publish_time_ns", None),
        sequence=getattr(sample, "sequence", None),
        source_channel_id=getattr(sample, "source_channel_id", None),
    )


def _neighbor_samples(
    replacement_unit: str,
    neighbors: Any,
    sample_values: dict[tuple[str, str, int | float, int, str, str], NeighborSample],
) -> dict[str, NeighborSample | None]:
    return {
        "previous": _neighbor_sample(replacement_unit, neighbors.previous_ref, sample_values),
        "next": _neighbor_sample(replacement_unit, neighbors.next_ref, sample_values),
    }


def _neighbor_sample(
    replacement_unit: str,
    sample_ref: SignalSampleRef | None,
    sample_values: dict[tuple[str, str, int | float, int, str, str], NeighborSample],
) -> NeighborSample | None:
    if sample_ref is None:
        return None
    return sample_values.get(_value_key(sample_ref, replacement_unit))


def _merge_repair_results(
    *,
    detection_result: SignalReliabilityDetectionResult,
    config_path: Path,
    partial_results: list[SignalRepairResult],
    run_id: str,
    dispositions: list[SignalIssueDisposition] | None = None,
) -> SignalRepairResult:
    repair_runs = [run for result in partial_results for run in result.repair_runs]
    output_sequence_refs = {topic: ref for result in partial_results for topic, ref in result.output_sequence_refs.items()}
    sample_count_before = _merge_counts(result.sample_count_before for result in partial_results)
    sample_count_after = _merge_counts(result.sample_count_after for result in partial_results)
    return SignalRepairResult(
        input_detection_result_ref=detection_result,
        repair_policy_config_ref=str(config_path),
        repair_runs=repair_runs,
        dispositions=dispositions or [],
        unhandled_missing_interval_records=list(detection_result.missing_interval_issues),
        output_sequence_refs=output_sequence_refs,
        sample_count_before=sample_count_before,
        sample_count_after=sample_count_after,
        summary_by_modality=_summary_by_modality(repair_runs),
        created_at=datetime.now().isoformat(),
        run_id=run_id,
    )


def _merge_counts(counts: Any) -> dict[str, int]:
    merged: dict[str, int] = {}
    for count in counts:
        for topic, value in count.items():
            merged[topic] = merged.get(topic, 0) + value
    return merged


def _summary_by_modality(repair_runs: Any) -> dict[str, dict[str, int]]:
    summary: dict[str, dict[str, int]] = {}
    for run in repair_runs:
        counts = summary.setdefault(run.modality, {"repaired": 0, "unrepaired": 0, "skipped": 0})
        if run.status is RepairDecisionStatus.REPAIRED:
            counts["repaired"] += 1
        elif run.status is RepairDecisionStatus.SKIPPED:
            counts["skipped"] += 1
        else:
            counts["unrepaired"] += 1
    return summary


def compute_signal_repair(
    *,
    samples: Any,
    detection_result: SignalReliabilityDetectionResult,
    config_path: Path,
    run_id: str,
) -> SignalRepairResult:
    issue_groups = aggregate_sample_issues(detection_result.sample_issues)
    dispositions = decide_issue_dispositions(issue_groups)
    repair_runs = build_repair_runs(
        issue_groups,
        detection_result.missing_interval_issues,
        dispositions,
    )
    sample_refs = _sample_refs(samples)
    sample_values = _sample_value_map(samples)
    neighbors = {
        run.repair_run_id: _neighbor_samples(
            run.replacement_unit,
            find_legal_neighbors(
                run.input_window_refs,
                sample_refs,
                issue_groups,
                detection_result.missing_interval_issues,
                replacement_unit=run.replacement_unit,
            ),
            sample_values,
        )
        for run in repair_runs
    }
    return _merge_repair_results(
        detection_result=detection_result,
        config_path=config_path,
        partial_results=run_all_repairs(repair_runs, neighbors),
        run_id=run_id,
        dispositions=dispositions,
    )


def _run_stats(detection_result: SignalReliabilityDetectionResult, repair_result: SignalRepairResult) -> dict[str, Any]:
    return {
        "sample_issue_count": len(detection_result.sample_issues),
        "missing_interval_issue_count": len(detection_result.missing_interval_issues),
        "repair_runs": len(repair_result.repair_runs),
        "summary_by_modality": repair_result.summary_by_modality,
        "sample_count_before": repair_result.sample_count_before,
        "sample_count_after": repair_result.sample_count_after,
    }


def _value_key(sample_ref: SignalSampleRef, replacement_unit: str) -> tuple[str, str, int | float, int, str, str]:
    return (*_sample_key(sample_ref), replacement_unit)


def _sample_key(sample_ref: SignalSampleRef) -> tuple[str, str, int | float, int, str]:
    return (sample_ref.topic, sample_ref.time_domain, sample_ref.timestamp, sample_ref.message_index, sample_ref.modality)


def _tactile_matrix(frame: TactilePressureFrame) -> list[list[int]]:
    return [frame.data[index : index + frame.cols] for index in range(0, len(frame.data), frame.cols)]


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
