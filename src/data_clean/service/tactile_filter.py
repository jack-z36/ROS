from __future__ import annotations

from collections import defaultdict, deque
from statistics import median
from typing import Any, Iterable

from schemas.reliability import SignalSampleRef
from schemas.tactile_filter import (
    TactileFilterConfig,
    TactileFilterResult,
    TactileFilterSampleRecord,
    TactileFilterSampleStatus,
    TactileFilterSegmentSummary,
)
from service.tactile_segment import split_tactile_segments


def filter_tactile_cell(series: Iterable[float | int], median_window: int, ema_alpha: float) -> list[float]:
    values = [float(value) for value in series]
    if not values:
        return []
    median_values = _rolling_median_values(values, median_window)
    filtered: list[float] = []
    previous: float | None = None
    for value in median_values:
        current = value if previous is None else ema_alpha * value + (1.0 - ema_alpha) * previous
        filtered.append(current)
        previous = current
    return filtered


def filter_tactile_segment(frames: Iterable[Any], config: TactileFilterConfig) -> list[TactileFilterSampleRecord]:
    ordered_frames = sorted(list(frames), key=lambda frame: (_sample_ref(frame).timestamp, _sample_ref(frame).message_index))
    split_tactile_segments(ordered_frames, missing_intervals=[], config=config)
    median_by_key = _rolling_median_by_key(ordered_frames, config.median_window)
    records: list[TactileFilterSampleRecord] = []
    previous_original: list[float] | None = None
    previous_ema: list[float] | None = None

    for frame in ordered_frames:
        sample_ref = _sample_ref(frame)
        rows, cols = _shape(frame)
        shape_summary = {"rows": rows, "cols": cols, "cell_count": rows * cols}
        if not _has_valid_shape(frame):
            records.append(
                TactileFilterSampleRecord(
                    sample_ref=sample_ref,
                    status=TactileFilterSampleStatus.INVALID_SHAPE,
                    filtered_value_summary={
                        "shape": shape_summary,
                        "original_summary": _summary(list(_field(frame, "data", []))),
                        "filtered_summary": None,
                        "diff_summary": None,
                    },
                    reason="invalid_shape",
                )
            )
            previous_original = None
            previous_ema = None
            continue

        original_values = [float(value) for value in _field(frame, "data", [])]
        median_values = median_by_key[_sample_key(sample_ref)]
        contact_reset = _contact_reset(original_values, previous_original, config.contact_reset_threshold)
        if previous_ema is None or contact_reset:
            filtered_values = median_values
        else:
            filtered_values = [
                config.ema_alpha * current + (1.0 - config.ema_alpha) * previous
                for current, previous in zip(median_values, previous_ema)
            ]

        status = TactileFilterSampleStatus.EMA_RESET if contact_reset else TactileFilterSampleStatus.FILTERED
        diff_summary = _diff_summary(original_values, filtered_values)
        filtered_summary = _summary(filtered_values)
        record = TactileFilterSampleRecord(
            sample_ref=sample_ref,
            status=status,
            filtered_value_summary={
                "shape": shape_summary,
                "original_summary": _summary(original_values),
                "filtered_summary": filtered_summary,
                "diff_summary": diff_summary,
            },
            debug_artifact_ref=_debug_artifact_ref(sample_ref, config),
            reason="ema_reset" if contact_reset else "filtered",
        )
        record.contact_reset = contact_reset
        record.filtered_matrix = _matrix(filtered_values, rows, cols)
        records.append(record)
        previous_original = original_values
        previous_ema = filtered_values

    return records


def run_tactile_audit(records: Iterable[TactileFilterSampleRecord], original_frames: Iterable[Any]) -> list[TactileFilterSampleRecord]:
    original_by_key = {_sample_key(_sample_ref(frame)): frame for frame in original_frames}
    audited = []
    for record in records:
        audit_flags: list[str] = []
        frame = original_by_key.get(_sample_key(record.sample_ref))
        filtered_matrix = getattr(record, "filtered_matrix", None)
        if frame is not None and filtered_matrix is not None:
            original_values = [float(value) for value in _field(frame, "data", [])]
            filtered_values = _flatten(filtered_matrix)
            record.filtered_value_summary["diff_summary"] = _diff_summary(original_values, filtered_values)
        diff_summary = record.filtered_value_summary.get("diff_summary") or {}
        if float(diff_summary.get("max_abs_delta", 0.0)) > 10.0:
            audit_flags.append("large_deviation")
        record.filtered_value_summary["audit_flags"] = audit_flags
        audited.append(record)
    return audited


def aggregate_tactile_result(
    segment_summaries: Iterable[TactileFilterSegmentSummary],
    records: Iterable[TactileFilterSampleRecord],
    original: Iterable[Any],
) -> TactileFilterResult:
    segment_list = list(segment_summaries)
    record_list = list(records)
    original_list = list(original)
    sample_count_before: dict[str, int] = defaultdict(int)
    sample_count_after: dict[str, int] = defaultdict(int)
    summary_by_topic: dict[str, dict[str, int]] = defaultdict(_empty_topic_summary)
    output_by_topic: dict[str, list[dict[str, Any]]] = defaultdict(list)
    original_by_key = {_sample_key(_sample_ref(frame)): frame for frame in original_list}

    for frame in original_list:
        sample_count_before[_sample_ref(frame).topic] += 1

    for record in record_list:
        topic = record.sample_ref.topic
        sample_count_after[topic] += 1
        _increment_summary(summary_by_topic[topic], record.status)
        original_frame = original_by_key.get(_sample_key(record.sample_ref))
        output_by_topic[topic].append(
            {
                "sample_ref": record.sample_ref,
                "status": record.status.value,
                "topic": topic,
                "timestamp": record.sample_ref.timestamp,
                "shape": record.filtered_value_summary.get("shape"),
                "filtered_matrix": getattr(record, "filtered_matrix", None) or _original_matrix(original_frame),
            }
        )

    if dict(sample_count_before) != dict(sample_count_after):
        raise ValueError("sample_count_before must equal sample_count_after")

    return TactileFilterResult(
        input_repair_result_ref="in_memory_tactile_sequence",
        tactile_filter_config_ref="in_memory_tactile_filter_config",
        input_sequence_refs=[],
        output_sequence_refs=dict(output_by_topic),
        sample_records=record_list,
        segment_summaries=segment_list,
        sample_count_before=dict(sample_count_before),
        sample_count_after=dict(sample_count_after),
        summary_by_topic=dict(summary_by_topic),
    )


def _rolling_median_values(values: list[float], window: int) -> list[float]:
    half_window = window // 2
    medians: list[float] = []
    for index, value in enumerate(values):
        if index < half_window or index + half_window >= len(values):
            medians.append(value)
            continue
        medians.append(float(median(values[index - half_window : index + half_window + 1])))
    return medians


def _rolling_median_by_key(frames: list[Any], window: int) -> dict[tuple[str, int], list[float]]:
    if not frames:
        return {}
    valid_indices = [index for index, frame in enumerate(frames) if _has_valid_shape(frame)]
    medians_by_index: dict[int, list[float]] = {}
    for run in _contiguous_shape_runs(frames, valid_indices):
        cell_series = list(zip(*([float(value) for value in _field(frames[index], "data", [])] for index in run)))
        filtered_cells = [deque(_rolling_median_values(list(series), window)) for series in cell_series]
        for index in run:
            medians_by_index[index] = [cell_values.popleft() for cell_values in filtered_cells]

    medians: dict[tuple[str, int], list[float]] = {}
    for index, frame in enumerate(frames):
        if not _has_valid_shape(frame):
            continue
        medians[_sample_key(_sample_ref(frame))] = medians_by_index[index]
    return medians


def _contiguous_shape_runs(frames: list[Any], indices: list[int]) -> list[list[int]]:
    runs: list[list[int]] = []
    current: list[int] = []
    previous_index: int | None = None
    previous_shape: tuple[int, int] | None = None
    for index in indices:
        shape = _shape(frames[index])
        if previous_index is None or index == previous_index + 1 and shape == previous_shape:
            current.append(index)
        else:
            runs.append(current)
            current = [index]
        previous_index = index
        previous_shape = shape
    if current:
        runs.append(current)
    return runs


def _contact_reset(
    current_values: list[float], previous_values: list[float] | None, threshold: float | None
) -> bool:
    if threshold is None or previous_values is None or len(current_values) != len(previous_values):
        return False
    mean_abs_delta = sum(abs(current - previous) for current, previous in zip(current_values, previous_values)) / len(current_values)
    return mean_abs_delta > threshold


def _debug_artifact_ref(sample_ref: SignalSampleRef, config: TactileFilterConfig) -> str | None:
    if not bool(getattr(config, "emit_full_diff_in_dev", False)):
        return None
    return f"tactile_filter_full_diff/{sample_ref.topic}:{sample_ref.message_index}"


def _summary(values: list[float] | list[int]) -> dict[str, float | int | None]:
    if not values:
        return {"min": None, "max": None, "mean": None}
    numeric_values = [float(value) for value in values]
    return {
        "min": min(numeric_values),
        "max": max(numeric_values),
        "mean": sum(numeric_values) / len(numeric_values),
    }


def _diff_summary(original_values: list[float], filtered_values: list[float]) -> dict[str, float | int]:
    deltas = [abs(original - filtered) for original, filtered in zip(original_values, filtered_values)]
    changed = [delta for delta in deltas if delta > 1e-9]
    return {
        "changed_cell_count": len(changed),
        "mean_abs_delta": sum(deltas) / len(deltas) if deltas else 0.0,
        "max_abs_delta": max(deltas) if deltas else 0.0,
    }


def _matrix(values: list[float], rows: int, cols: int) -> list[list[float]]:
    return [values[row * cols : (row + 1) * cols] for row in range(rows)]


def _original_matrix(frame: Any | None) -> list[list[float]] | None:
    if frame is None or not _has_valid_shape(frame):
        return None
    rows, cols = _shape(frame)
    return _matrix([float(value) for value in _field(frame, "data", [])], rows, cols)


def _flatten(matrix: list[list[float]]) -> list[float]:
    return [float(value) for row in matrix for value in row]


def _empty_topic_summary() -> dict[str, int]:
    return {"filtered": 0, "kept_original": 0, "reset": 0, "skipped": 0, "invalid_shape": 0}


def _increment_summary(summary: dict[str, int], status: TactileFilterSampleStatus) -> None:
    if status is TactileFilterSampleStatus.FILTERED:
        summary["filtered"] += 1
    elif status is TactileFilterSampleStatus.EMA_RESET:
        summary["reset"] += 1
    elif status is TactileFilterSampleStatus.INVALID_SHAPE:
        summary["invalid_shape"] += 1
    elif status is TactileFilterSampleStatus.SKIPPED_BOUNDARY:
        summary["skipped"] += 1
    else:
        summary["kept_original"] += 1


def _sample_ref(frame: Any) -> SignalSampleRef:
    ref = _field(frame, "sample_ref", None)
    if isinstance(ref, SignalSampleRef):
        return ref
    if isinstance(ref, dict):
        return SignalSampleRef(
            topic=str(ref["topic"]),
            timestamp=ref["timestamp"],
            message_index=int(ref["message_index"]),
            modality=str(ref.get("modality", "tactile")),
            time_domain=str(ref.get("time_domain", "log_time")),
        )
    topic = str(_field(frame, "topic"))
    timestamp = _field(frame, "timestamp_ns", _field(frame, "timestamp"))
    return SignalSampleRef(
        topic=topic,
        timestamp=timestamp,
        message_index=int(_field(frame, "message_index")),
        modality="tactile",
        time_domain=str(_field(frame, "time_domain", "log_time")),
    )


def _sample_key(sample_ref: SignalSampleRef) -> tuple[str, int]:
    return sample_ref.topic, sample_ref.message_index


def _has_valid_shape(frame: Any) -> bool:
    rows, cols = _shape(frame)
    return rows > 0 and cols > 0 and rows * cols == len(list(_field(frame, "data", [])))


def _shape(frame: Any) -> tuple[int, int]:
    return int(_field(frame, "rows", 0)), int(_field(frame, "cols", 0))


def _field(value: Any, name: str, default: Any = None) -> Any:
    if isinstance(value, dict):
        return value.get(name, default)
    return getattr(value, name, default)
