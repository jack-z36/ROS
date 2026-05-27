from __future__ import annotations

from dataclasses import replace
from typing import Any, Iterable

import numpy as np

from schemas.reliability import SignalSampleRef
from schemas.repair import RepairDecisionStatus, RepairMethod, SignalRepairResult, SignalRepairRun, SignalRepairSampleRecord

NeighborSample = dict[str, Any]


def repair_pose_position(
    run: SignalRepairRun,
    prev_neighbor: NeighborSample | None,
    next_neighbor: NeighborSample | None,
) -> list[SignalRepairSampleRecord]:
    if prev_neighbor is None or next_neighbor is None:
        return _unrepaired_records(run, "missing_neighbor")
    return _linear_records(run, prev_neighbor, next_neighbor, RepairMethod.LINEAR_INTERPOLATE, "linear_interpolate")


def repair_pose_orientation(
    run: SignalRepairRun,
    prev_neighbor: NeighborSample | None,
    next_neighbor: NeighborSample | None,
) -> list[SignalRepairSampleRecord]:
    if prev_neighbor is None or next_neighbor is None:
        return _unrepaired_records(run, "missing_neighbor")

    start_ref = _neighbor_ref(prev_neighbor)
    end_ref = _neighbor_ref(next_neighbor)
    start_value = _normalized_vector(_neighbor_value(prev_neighbor))
    end_value = _normalized_vector(_neighbor_value(next_neighbor))

    records: list[SignalRepairSampleRecord] = []
    for index, sample_ref in enumerate(_ordered_refs(run)):
        fraction = _timestamp_fraction(sample_ref.timestamp, start_ref.timestamp, end_ref.timestamp)
        repaired_value = _slerp(start_value, end_value, fraction)
        records.append(
            _repaired_record(
                run,
                sample_ref,
                index,
                RepairMethod.SLERP_INTERPOLATE,
                "slerp_interpolate",
                {"value": repaired_value.tolist()},
            )
        )
    return records


def repair_gripper(
    run: SignalRepairRun,
    prev_neighbor: NeighborSample | None,
    next_neighbor: NeighborSample | None,
) -> list[SignalRepairSampleRecord]:
    if prev_neighbor is None or next_neighbor is None:
        return _unrepaired_records(run, "missing_neighbor")

    start_ref = _neighbor_ref(prev_neighbor)
    end_ref = _neighbor_ref(next_neighbor)
    start_value = float(_neighbor_value(prev_neighbor))
    end_value = float(_neighbor_value(next_neighbor))
    records: list[SignalRepairSampleRecord] = []

    for index, sample_ref in enumerate(_ordered_refs(run)):
        fraction = _timestamp_fraction(sample_ref.timestamp, start_ref.timestamp, end_ref.timestamp)
        raw_value = start_value + (end_value - start_value) * fraction
        repaired_value = min(1.0, max(0.0, raw_value))
        records.append(
            _repaired_record(
                run,
                sample_ref,
                index,
                RepairMethod.LINEAR_INTERPOLATE,
                "linear_interpolate",
                {"value": repaired_value, "clamped": repaired_value != raw_value},
            )
        )
    return records


def repair_tactile(
    run: SignalRepairRun,
    prev_neighbor: NeighborSample | None,
    next_neighbor: NeighborSample | None,
) -> list[SignalRepairSampleRecord]:
    if prev_neighbor is None or next_neighbor is None:
        return _unrepaired_records(run, "missing_neighbor")

    start_value = np.asarray(_neighbor_value(prev_neighbor), dtype=float)
    end_value = np.asarray(_neighbor_value(next_neighbor), dtype=float)
    if start_value.shape != end_value.shape:
        return _unrepaired_records(run, "tactile_shape_mismatch")

    start_ref = _neighbor_ref(prev_neighbor)
    end_ref = _neighbor_ref(next_neighbor)
    records: list[SignalRepairSampleRecord] = []
    for index, sample_ref in enumerate(_ordered_refs(run)):
        fraction = _timestamp_fraction(sample_ref.timestamp, start_ref.timestamp, end_ref.timestamp)
        repaired_value = start_value + (end_value - start_value) * fraction
        records.append(
            _repaired_record(
                run,
                sample_ref,
                index,
                RepairMethod.LINEAR_INTERPOLATE,
                "linear_interpolate",
                {"value": repaired_value.tolist(), "shape": list(repaired_value.shape)},
            )
        )
    return records


def repair_hold(run: SignalRepairRun, nearest_neighbor: NeighborSample | None) -> list[SignalRepairSampleRecord]:
    if nearest_neighbor is None:
        return _unrepaired_records(run, "missing_neighbor")

    value = _neighbor_value(nearest_neighbor)
    return [
        _repaired_record(
            run,
            sample_ref,
            index,
            RepairMethod.COPY_NEAREST,
            "copy_nearest",
            {"value": _plain_value(value)},
        )
        for index, sample_ref in enumerate(_ordered_refs(run))
    ]


def run_all_repairs(
    runs: Iterable[SignalRepairRun],
    neighbors_dict: dict[str, dict[str, NeighborSample | None]],
) -> list[SignalRepairResult]:
    results: list[SignalRepairResult] = []
    for run in runs:
        neighbors = neighbors_dict.get(run.repair_run_id, {})
        sample_records = _dispatch_repair(run, neighbors)
        status = (
            RepairDecisionStatus.REPAIRED
            if sample_records and all(record.status is RepairDecisionStatus.REPAIRED for record in sample_records)
            else RepairDecisionStatus.UNREPAIRABLE
        )
        reason = "repaired" if status is RepairDecisionStatus.REPAIRED else _first_record_reason(sample_records, "missing_neighbor")
        repaired_run = replace(
            run,
            status=status,
            applied_method=sample_records[0].repair_method if sample_records and status is RepairDecisionStatus.REPAIRED else None,
            reason=reason,
            sample_records=sample_records,
            previous_neighbor_ref=_optional_neighbor_ref(neighbors.get("previous")),
            next_neighbor_ref=_optional_neighbor_ref(neighbors.get("next")),
        )
        sample_count = len(run.input_window_refs)
        results.append(
            SignalRepairResult(
                input_detection_result_ref="repair_compute_input",
                repair_policy_config_ref="repair_compute_policy",
                repair_runs=[repaired_run],
                output_sequence_refs={run.source_topic: f"repaired://{run.repair_run_id}/{run.source_topic}"},
                sample_count_before={run.source_topic: sample_count},
                sample_count_after={run.source_topic: sample_count},
                summary_by_modality={run.modality: _summary(status)},
            )
        )
    return results


def _dispatch_repair(run: SignalRepairRun, neighbors: dict[str, NeighborSample | None]) -> list[SignalRepairSampleRecord]:
    previous = neighbors.get("previous")
    next_neighbor = neighbors.get("next")
    if _is_hold_run(run):
        return repair_hold(run, _nearest_neighbor(run, previous, next_neighbor))
    if run.replacement_unit == "pose.position":
        return repair_pose_position(run, previous, next_neighbor)
    if run.replacement_unit == "pose.orientation":
        return repair_pose_orientation(run, previous, next_neighbor)
    if run.replacement_unit == "gripper.value":
        return repair_gripper(run, previous, next_neighbor)
    if run.replacement_unit == "tactile.frame":
        return repair_tactile(run, previous, next_neighbor)
    return _unrepaired_records(run, "unsupported_replacement_unit")


def _linear_records(
    run: SignalRepairRun,
    prev_neighbor: NeighborSample,
    next_neighbor: NeighborSample,
    method: RepairMethod,
    reason: str,
) -> list[SignalRepairSampleRecord]:
    start_ref = _neighbor_ref(prev_neighbor)
    end_ref = _neighbor_ref(next_neighbor)
    start_value = np.asarray(_neighbor_value(prev_neighbor), dtype=float)
    end_value = np.asarray(_neighbor_value(next_neighbor), dtype=float)
    records: list[SignalRepairSampleRecord] = []
    for index, sample_ref in enumerate(_ordered_refs(run)):
        fraction = _timestamp_fraction(sample_ref.timestamp, start_ref.timestamp, end_ref.timestamp)
        repaired_value = start_value + (end_value - start_value) * fraction
        records.append(_repaired_record(run, sample_ref, index, method, reason, {"value": repaired_value.tolist()}))
    return records


def _repaired_record(
    run: SignalRepairRun,
    sample_ref: SignalSampleRef,
    index: int,
    method: RepairMethod,
    reason: str,
    value_summary: dict[str, Any],
) -> SignalRepairSampleRecord:
    return SignalRepairSampleRecord(
        sample_ref=sample_ref,
        status=RepairDecisionStatus.REPAIRED,
        repair_method=method,
        reason=reason,
        sample_issue_ids=_issue_ids_for_sample(run, index),
        repaired_value_ref=f"{run.repair_run_id}:{sample_ref.message_index}",
        value_summary=value_summary,
    )


def _unrepaired_records(run: SignalRepairRun, reason: str) -> list[SignalRepairSampleRecord]:
    return [
        SignalRepairSampleRecord(
            sample_ref=sample_ref,
            status=RepairDecisionStatus.UNREPAIRABLE,
            repair_method=None,
            reason=reason,
            sample_issue_ids=_issue_ids_for_sample(run, index),
            value_summary={},
        )
        for index, sample_ref in enumerate(_ordered_refs(run))
    ]


def _ordered_refs(run: SignalRepairRun) -> list[SignalSampleRef]:
    return sorted(run.input_window_refs, key=lambda ref: (ref.timestamp, ref.message_index))


def _issue_ids_for_sample(run: SignalRepairRun, index: int) -> list[str]:
    if len(run.sample_issue_ids) == len(run.input_window_refs):
        return [run.sample_issue_ids[index]]
    return list(run.sample_issue_ids)


def _neighbor_ref(neighbor: NeighborSample) -> SignalSampleRef:
    sample_ref = neighbor.get("sample_ref")
    if not isinstance(sample_ref, SignalSampleRef):
        raise TypeError("neighbor sample_ref must be a SignalSampleRef")
    return sample_ref


def _optional_neighbor_ref(neighbor: NeighborSample | None) -> SignalSampleRef | None:
    return None if neighbor is None else _neighbor_ref(neighbor)


def _neighbor_value(neighbor: NeighborSample) -> Any:
    return neighbor["value"]


def _timestamp_fraction(timestamp: int | float, start: int | float, end: int | float) -> float:
    if end == start:
        return 0.0
    return float((timestamp - start) / (end - start))


def _normalized_vector(value: Any) -> np.ndarray:
    vector = np.asarray(value, dtype=float)
    norm = np.linalg.norm(vector)
    if norm == 0:
        raise ValueError("quaternion norm must be non-zero")
    return vector / norm


def _slerp(start: np.ndarray, end: np.ndarray, fraction: float) -> np.ndarray:
    dot = float(np.dot(start, end))
    if dot < 0.0:
        end = -end
        dot = -dot
    dot = min(1.0, max(-1.0, dot))
    if dot > 0.9995:
        return _normalized_vector(start + fraction * (end - start))

    theta_0 = np.arccos(dot)
    sin_theta_0 = np.sin(theta_0)
    theta = theta_0 * fraction
    scale_start = np.sin(theta_0 - theta) / sin_theta_0
    scale_end = np.sin(theta) / sin_theta_0
    return _normalized_vector((scale_start * start) + (scale_end * end))


def _plain_value(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return value.tolist()
    return value


def _is_hold_run(run: SignalRepairRun) -> bool:
    return run.applied_method in {RepairMethod.COPY_NEAREST, RepairMethod.FORWARD_FILL, RepairMethod.BACKWARD_FILL, RepairMethod.HOLD_PREVIOUS, RepairMethod.HOLD_NEXT}


def _nearest_neighbor(
    run: SignalRepairRun,
    previous: NeighborSample | None,
    next_neighbor: NeighborSample | None,
) -> NeighborSample | None:
    if previous is None:
        return next_neighbor
    if next_neighbor is None:
        return previous
    target_time = _ordered_refs(run)[0].timestamp
    previous_distance = abs(target_time - _neighbor_ref(previous).timestamp)
    next_distance = abs(_neighbor_ref(next_neighbor).timestamp - target_time)
    return previous if previous_distance <= next_distance else next_neighbor


def _first_record_reason(records: list[SignalRepairSampleRecord], default: str) -> str:
    return records[0].reason if records else default


def _summary(status: RepairDecisionStatus) -> dict[str, int]:
    return {
        "repaired": 1 if status is RepairDecisionStatus.REPAIRED else 0,
        "unrepaired": 1 if status is RepairDecisionStatus.UNREPAIRABLE else 0,
        "skipped": 1 if status is RepairDecisionStatus.SKIPPED else 0,
    }
