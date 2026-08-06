from __future__ import annotations

from dataclasses import replace
from typing import Any, Iterable

import numpy as np

from schemas.reliability import SignalSampleRef
from schemas.repair import (
    RepairDecisionStatus,
    RepairDisposition,
    RepairMethod,
    SignalRepairResult,
    SignalRepairRun,
    SignalRepairSampleRecord,
)

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
    try:
        start_value = _normalized_quaternion(_neighbor_value(prev_neighbor))
        end_value = _normalized_quaternion(_neighbor_value(next_neighbor))
    except ValueError:
        return _unrepaired_records(run, "invalid_quaternion_neighbor")

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
    if not np.isfinite(start_value) or not np.isfinite(end_value):
        return _unrepaired_records(run, "invalid_gripper_neighbor")
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
    target_shape = (
        int(run.replacement_contract.get("rows", 0)),
        int(run.replacement_contract.get("cols", 0)),
    )
    if (
        start_value.ndim != 2
        or end_value.ndim != 2
        or start_value.shape != end_value.shape
        or not np.all(np.isfinite(start_value))
        or not np.all(np.isfinite(end_value))
        or target_shape[0] <= 0
        or target_shape[1] <= 0
        or start_value.shape != target_shape
    ):
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


def run_all_repairs(
    runs: Iterable[SignalRepairRun],
    neighbors_dict: dict[str, dict[str, NeighborSample | None]],
) -> list[SignalRepairResult]:
    results: list[SignalRepairResult] = []
    for run in runs:
        neighbors = neighbors_dict.get(run.repair_run_id, {})
        if run.disposition is not RepairDisposition.AUTO_REPAIR or run.status is not RepairDecisionStatus.PENDING:
            skipped_status = (
                RepairDecisionStatus.UNREPAIRABLE
                if run.disposition is RepairDisposition.UNRECOVERABLE
                else RepairDecisionStatus.SKIPPED
            )
            sample_records = _decision_records(run, skipped_status, f"disposition_{run.disposition.value}")
        elif not _planned_method_matches(run):
            sample_records = _unrepaired_records(run, "planned_method_mismatch")
        else:
            try:
                sample_records = _dispatch_repair(run, neighbors)
            except (TypeError, ValueError, FloatingPointError):
                sample_records = _unrepaired_records(run, "repair_computation_failed")
        status = (
            RepairDecisionStatus.REPAIRED
            if sample_records and all(record.status is RepairDecisionStatus.REPAIRED for record in sample_records)
            else sample_records[0].status if sample_records else RepairDecisionStatus.UNREPAIRABLE
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
                output_sequence_refs=(
                    {run.source_topic: f"repaired://{run.repair_run_id}/{run.source_topic}"}
                    if status is RepairDecisionStatus.REPAIRED
                    else {}
                ),
                sample_count_before={run.source_topic: sample_count},
                sample_count_after={run.source_topic: sample_count},
                summary_by_modality={run.modality: _summary(status)},
            )
        )
    return results


def _dispatch_repair(run: SignalRepairRun, neighbors: dict[str, NeighborSample | None]) -> list[SignalRepairSampleRecord]:
    previous = neighbors.get("previous")
    next_neighbor = neighbors.get("next")
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
    if (
        start_value.shape != (3,)
        or end_value.shape != (3,)
        or not np.all(np.isfinite(start_value))
        or not np.all(np.isfinite(end_value))
    ):
        return _unrepaired_records(run, "invalid_linear_neighbor")
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


def _decision_records(
    run: SignalRepairRun,
    status: RepairDecisionStatus,
    reason: str,
) -> list[SignalRepairSampleRecord]:
    return [
        SignalRepairSampleRecord(
            sample_ref=sample_ref,
            status=status,
            repair_method=None,
            reason=reason,
            sample_issue_ids=_issue_ids_for_sample(run, index),
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
    if end <= start:
        raise ValueError("repair neighbors must have strictly increasing timestamps")
    return float((timestamp - start) / (end - start))


def _normalized_vector(value: Any) -> np.ndarray:
    vector = np.asarray(value, dtype=float)
    norm = np.linalg.norm(vector)
    if norm == 0:
        raise ValueError("quaternion norm must be non-zero")
    return vector / norm


def _normalized_quaternion(value: Any) -> np.ndarray:
    vector = np.asarray(value, dtype=float)
    if vector.shape != (4,) or not np.all(np.isfinite(vector)):
        raise ValueError("quaternion must contain four finite components")
    return _normalized_vector(vector)


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


def _planned_method_matches(run: SignalRepairRun) -> bool:
    expected = {
        "pose.position": RepairMethod.LINEAR_INTERPOLATE,
        "pose.orientation": RepairMethod.SLERP_INTERPOLATE,
        "gripper.value": RepairMethod.LINEAR_INTERPOLATE,
        "tactile.frame": RepairMethod.LINEAR_INTERPOLATE,
    }.get(run.replacement_unit)
    return expected is not None and run.planned_method is expected


def _first_record_reason(records: list[SignalRepairSampleRecord], default: str) -> str:
    return records[0].reason if records else default


def _summary(status: RepairDecisionStatus) -> dict[str, int]:
    return {
        "repaired": 1 if status is RepairDecisionStatus.REPAIRED else 0,
        "unrepaired": 1 if status is RepairDecisionStatus.UNREPAIRABLE else 0,
        "skipped": 1 if status is RepairDecisionStatus.SKIPPED else 0,
    }
