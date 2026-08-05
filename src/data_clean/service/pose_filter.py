from __future__ import annotations

import math
from collections import defaultdict
from typing import Any, Iterable

from scipy.signal import savgol_filter

from schemas.pose_filter import (
    PoseFilterConfig,
    PoseFilterInputSequence,
    PoseFilterResult,
    PoseFilterSampleRecord,
    PoseFilterSampleStatus,
    PoseFilterSegmentSummary,
)
from schemas.reliability import SignalSampleRef

# Coordinate-frame output patterns removed from the current production route.
_REMOVED_FRAME_TOPIC_PATTERNS = (
    "common_frame_tcp_pose",
    "common_frame",
    "robot_base",
    "arm_base",
)


def validate_source_frame_data(samples: Iterable[Any]) -> bool:
    """Validate that pose topics do not claim a converted coordinate frame.

    Checks each sample's topic field for known common-frame or robot_base
    patterns.  Raises ValueError with 'invalid_pose_frame_for_current_route'
    if any sample still uses the old pipeline topic naming.

    Returns True if all samples pass validation.
    """
    for sample in samples:
        topic = _field(_sample_ref(sample), "topic", "")
        for pattern in _REMOVED_FRAME_TOPIC_PATTERNS:
            if pattern in topic.lower():
                raise ValueError(
                    f"invalid_pose_frame_for_current_route: "
                    f"topic={topic!r} contains legacy pattern {pattern!r}. "
                    "Production requires TCP poses in each Baton stream's "
                    "original source frame."
                )
    return True


def filter_pose_segments(
    pose_sequence: Iterable[Any],
    segment_summaries: Iterable[PoseFilterSegmentSummary],
    config: PoseFilterConfig | None = None,
    *,
    input_repair_result_ref: Any = "in_memory_pose_sequence",
    input_sequence_refs: list[PoseFilterInputSequence | str] | None = None,
    validate_source_frame: bool = False,
) -> PoseFilterResult:
    active_config = config or PoseFilterConfig()

    if validate_source_frame:
        validate_source_frame_data(pose_sequence)
    samples = list(pose_sequence)
    segments = list(segment_summaries)
    segment_by_key = _segment_samples_by_key(samples, segments)
    candidate_by_key = _candidate_positions_by_key(samples, segments, segment_by_key, active_config)

    sample_records: list[PoseFilterSampleRecord] = []
    final_by_topic: dict[str, list[dict[str, Any]]] = defaultdict(list)
    summary_by_topic: dict[str, dict[str, int]] = defaultdict(_empty_topic_summary)
    sample_count_before: dict[str, int] = defaultdict(int)
    sample_count_after: dict[str, int] = defaultdict(int)

    for sample in samples:
        sample_ref = _sample_ref(sample)
        topic = sample_ref.topic
        sample_count_before[topic] += 1
        original_pose = _pose_value(sample)
        segment = segment_by_key.get(_sample_key(sample_ref))
        candidate_position = candidate_by_key.get(_sample_key(sample_ref))

        if segment is None or candidate_position is None:
            status = PoseFilterSampleStatus.KEPT_ORIGINAL
            candidate_pose = None
            final_pose = original_pose
            guard_delta = {"position_m": 0.0, "orientation_deg": 0.0}
            reason = _kept_reason(segment)
        else:
            candidate_pose = {
                "position": candidate_position,
                "orientation": original_pose["orientation"],
            }
            guard_delta = {
                "position_m": _position_delta_m(original_pose["position"], candidate_position),
                "orientation_deg": _orientation_delta_deg(original_pose["orientation"], candidate_pose["orientation"]),
            }
            if _exceeds_guard(guard_delta, active_config):
                status = PoseFilterSampleStatus.FILTER_REJECTED_BY_GUARD
                final_pose = original_pose
                reason = _guard_reason(guard_delta, active_config)
            else:
                status = PoseFilterSampleStatus.FILTERED
                final_pose = candidate_pose
                reason = None

        sample_records.append(
            PoseFilterSampleRecord(
                sample_ref=sample_ref,
                status=status,
                original_position=original_pose["position"],
                original_orientation=original_pose["orientation"],
                candidate_filtered_value=candidate_pose,
                final_value=final_pose,
                guard_delta=guard_delta,
                reason=reason,
            )
        )
        final_by_topic[topic].append({"sample_ref": sample_ref, **final_pose})
        sample_count_after[topic] += 1
        _increment_topic_summary(summary_by_topic[topic], status)

    _update_segment_counts(segments, sample_records)
    return PoseFilterResult(
        input_repair_result_ref=input_repair_result_ref,
        pose_filter_config_ref=active_config,
        input_sequence_refs=input_sequence_refs or [],
        output_sequence_refs=dict(final_by_topic),
        sample_records=sample_records,
        segment_summaries=segments,
        sample_count_before=dict(sample_count_before),
        sample_count_after=dict(sample_count_after),
        timestamp_policy=active_config.timestamp_policy,
        summary_by_topic=dict(summary_by_topic),
    )


def filter_position_segment(samples: Iterable[Any], config: PoseFilterConfig) -> list[PoseFilterSampleRecord]:
    pose_samples = list(samples)
    if not pose_samples:
        return []
    candidate_positions = _filter_positions(pose_samples, config)
    records = []
    for sample, candidate_position in zip(pose_samples, candidate_positions):
        original_pose = _pose_value(sample)
        candidate_pose = {
            "position": candidate_position,
            "orientation": original_pose["orientation"],
        }
        records.append(
            PoseFilterSampleRecord(
                sample_ref=_sample_ref(sample),
                status=PoseFilterSampleStatus.FILTERED,
                original_position=original_pose["position"],
                original_orientation=original_pose["orientation"],
                candidate_filtered_value=candidate_pose,
                final_value=candidate_pose,
                guard_delta={
                    "position_m": _position_delta_m(original_pose["position"], candidate_position),
                    "orientation_deg": _orientation_delta_deg(original_pose["orientation"], candidate_pose["orientation"]),
                },
            )
        )
    return run_guard_audit(records, config)


def filter_orientation_segment(samples: Iterable[Any], config: PoseFilterConfig) -> list[PoseFilterSampleRecord]:
    records = []
    for sample in samples:
        original_pose = _pose_value(sample)
        records.append(
            PoseFilterSampleRecord(
                sample_ref=_sample_ref(sample),
                status=PoseFilterSampleStatus.KEPT_ORIGINAL,
                original_position=original_pose["position"],
                original_orientation=original_pose["orientation"],
                candidate_filtered_value=None,
                final_value=original_pose,
                guard_delta={"position_m": 0.0, "orientation_deg": 0.0},
                reason="orientation_kept_original",
            )
        )
    return records


def run_guard_audit(sample_records: Iterable[PoseFilterSampleRecord], config: PoseFilterConfig) -> list[PoseFilterSampleRecord]:
    audited = []
    for record in sample_records:
        candidate_pose = record.candidate_filtered_value or record.final_value
        original_pose = {"position": record.original_position, "orientation": record.original_orientation}
        guard_delta = {
            "position_m": _position_delta_m(original_pose["position"], candidate_pose["position"]),
            "orientation_deg": _orientation_delta_deg(original_pose["orientation"], candidate_pose["orientation"]),
        }
        record.guard_delta = guard_delta
        if _exceeds_guard(guard_delta, config):
            record.status = PoseFilterSampleStatus.FILTER_REJECTED_BY_GUARD
            record.final_value = original_pose
            record.reason = _guard_reason(guard_delta, config)
        elif record.status is PoseFilterSampleStatus.FILTERED:
            record.final_value = candidate_pose
            record.reason = None
        audited.append(record)
    return audited


def merge_segment_results(
    segment_summaries: Iterable[PoseFilterSegmentSummary],
    sample_records: Iterable[PoseFilterSampleRecord],
) -> PoseFilterResult:
    records = list(sample_records)
    sample_count_by_topic: dict[str, int] = defaultdict(int)
    summary_by_topic: dict[str, dict[str, int]] = defaultdict(_empty_topic_summary)
    output_by_topic: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        topic = record.sample_ref.topic
        sample_count_by_topic[topic] += 1
        output_by_topic[topic].append({"sample_ref": record.sample_ref, **record.final_value})
        _increment_topic_summary(summary_by_topic[topic], record.status)
    return PoseFilterResult(
        input_repair_result_ref="in_memory_pose_sequence",
        pose_filter_config_ref=PoseFilterConfig(),
        input_sequence_refs=[],
        output_sequence_refs=dict(output_by_topic),
        sample_records=records,
        segment_summaries=list(segment_summaries),
        sample_count_before=dict(sample_count_by_topic),
        sample_count_after=dict(sample_count_by_topic),
        summary_by_topic=dict(summary_by_topic),
    )


def _candidate_positions_by_key(
    samples: list[Any],
    segments: list[PoseFilterSegmentSummary],
    segment_by_key: dict[tuple[str, int], PoseFilterSegmentSummary],
    config: PoseFilterConfig,
) -> dict[tuple[str, int], dict[str, float]]:
    samples_by_key = {_sample_key(_sample_ref(sample)): sample for sample in samples}
    candidates: dict[tuple[str, int], dict[str, float]] = {}
    for segment in segments:
        if getattr(segment, "status", "filtered") != "filtered" or segment.actual_window_size_samples is None:
            continue
        segment_keys = [key for key, key_segment in segment_by_key.items() if key_segment is segment]
        segment_samples = [samples_by_key[key] for key in sorted(segment_keys, key=lambda item: item[1])]
        if len(segment_samples) <= config.polyorder:
            continue
        window = min(segment.actual_window_size_samples, len(segment_samples))
        if window % 2 == 0:
            window -= 1
        if window <= config.polyorder:
            continue
        filtered_positions = _filter_positions(segment_samples, config, window)
        for index, sample in enumerate(segment_samples):
            candidates[_sample_key(_sample_ref(sample))] = filtered_positions[index]
    return candidates


def _filter_positions(samples: list[Any], config: PoseFilterConfig, window: int | None = None) -> list[dict[str, float]]:
    if len(samples) <= config.polyorder:
        return [_pose_value(sample)["position"] for sample in samples]
    active_window = window or len(samples)
    active_window = min(active_window, len(samples))
    if active_window % 2 == 0:
        active_window -= 1
    if active_window <= config.polyorder:
        return [_pose_value(sample)["position"] for sample in samples]
    filtered_axes = {
        axis: savgol_filter([float(_pose_value(sample)["position"][axis]) for sample in samples], active_window, config.polyorder)
        for axis in ("x", "y", "z")
    }
    return [
        {axis: float(filtered_axes[axis][index]) for axis in ("x", "y", "z")}
        for index in range(len(samples))
    ]


def _segment_samples_by_key(
    samples: list[Any], segments: list[PoseFilterSegmentSummary]
) -> dict[tuple[str, int], PoseFilterSegmentSummary]:
    mapping: dict[tuple[str, int], PoseFilterSegmentSummary] = {}
    refs = [_sample_ref(sample) for sample in samples]
    for segment in segments:
        start_ref = _coerce_ref(segment.segment_start_ref)
        end_ref = _coerce_ref(segment.segment_end_ref)
        for sample_ref in refs:
            if sample_ref.topic == segment.source_topic and start_ref.message_index <= sample_ref.message_index <= end_ref.message_index:
                mapping[_sample_key(sample_ref)] = segment
    return mapping


def _update_segment_counts(segments: list[PoseFilterSegmentSummary], sample_records: list[PoseFilterSampleRecord]) -> None:
    for segment in segments:
        start_ref = _coerce_ref(segment.segment_start_ref)
        end_ref = _coerce_ref(segment.segment_end_ref)
        records = [
            record
            for record in sample_records
            if record.sample_ref.topic == segment.source_topic
            and start_ref.message_index <= record.sample_ref.message_index <= end_ref.message_index
        ]
        segment.filtered_count = sum(record.status is PoseFilterSampleStatus.FILTERED for record in records)
        segment.kept_count = sum(record.status is PoseFilterSampleStatus.KEPT_ORIGINAL for record in records)
        segment.rejected_count = sum(record.status is PoseFilterSampleStatus.FILTER_REJECTED_BY_GUARD for record in records)


def _pose_value(sample: Any) -> dict[str, dict[str, float]]:
    return {
        "position": dict(_field(sample, "position")),
        "orientation": dict(_field(sample, "orientation")),
    }


def _sample_ref(sample: Any) -> SignalSampleRef:
    ref = _field(sample, "sample_ref", None)
    return _coerce_ref(ref if ref is not None else sample)


def _coerce_ref(ref: Any) -> SignalSampleRef:
    if isinstance(ref, SignalSampleRef):
        return ref
    if isinstance(ref, dict):
        return SignalSampleRef(
            topic=str(ref["topic"]),
            timestamp=ref["timestamp"],
            message_index=int(ref["message_index"]),
            modality=str(ref.get("modality", "pose")),
            time_domain=str(ref.get("time_domain", "log_time")),
        )
    raise TypeError("pose sample must expose a SignalSampleRef as sample_ref")


def _sample_key(ref: SignalSampleRef) -> tuple[str, int]:
    return ref.topic, ref.message_index


def _position_delta_m(original: dict[str, Any], candidate: dict[str, Any]) -> float:
    return math.sqrt(sum((float(candidate[axis]) - float(original[axis])) ** 2 for axis in ("x", "y", "z")))


def _orientation_delta_deg(original: dict[str, Any], candidate: dict[str, Any]) -> float:
    dot = sum(float(original[axis]) * float(candidate[axis]) for axis in ("x", "y", "z", "w"))
    dot = max(-1.0, min(1.0, abs(dot)))
    return math.degrees(2.0 * math.acos(dot))


def _exceeds_guard(guard_delta: dict[str, float], config: PoseFilterConfig) -> bool:
    return (
        guard_delta["position_m"] > config.position_guard_max_delta_m
        or guard_delta["orientation_deg"] > config.orientation_guard_max_delta_deg
    )


def _guard_reason(guard_delta: dict[str, float], config: PoseFilterConfig) -> str:
    if guard_delta["position_m"] > config.position_guard_max_delta_m:
        return "position_guard_exceeded"
    return "orientation_guard_exceeded"


def _kept_reason(segment: PoseFilterSegmentSummary | None) -> str:
    if segment is None:
        return "outside_reliable_segment"
    return str(getattr(segment, "reason", None) or "kept_original")


def _empty_topic_summary() -> dict[str, int]:
    return {"filtered": 0, "kept_original": 0, "filter_rejected_by_guard": 0, "skipped_boundary": 0}


def _increment_topic_summary(summary: dict[str, int], status: PoseFilterSampleStatus) -> None:
    summary[status.value] += 1


def _field(value: Any, name: str, default: Any = None) -> Any:
    if isinstance(value, dict):
        return value.get(name, default)
    return getattr(value, name, default)
