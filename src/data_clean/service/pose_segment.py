from __future__ import annotations

from collections import defaultdict
from statistics import median
from typing import Any, Iterable

from schemas.pose_filter import PoseFilterConfig, PoseFilterSegmentSummary
from schemas.reliability import SignalSampleRef


def split_reliable_segments(
    pose_sequence: Iterable[Any],
    missing_intervals: Iterable[Any],
    unrepaired_refs: Iterable[Any],
    config: PoseFilterConfig,
) -> list[PoseFilterSegmentSummary]:
    blocked_keys = {_sample_key(_sample_ref(ref)) for ref in unrepaired_refs}
    intervals = list(missing_intervals)
    by_stream: dict[tuple[str, str], list[Any]] = defaultdict(list)
    for sample in _pose_samples(pose_sequence):
        ref = _sample_ref(sample)
        by_stream[(ref.topic, ref.time_domain)].append(sample)

    summaries: list[PoseFilterSegmentSummary] = []
    for stream_samples in by_stream.values():
        ordered = sorted(stream_samples, key=lambda sample: (_sample_ref(sample).timestamp, _sample_ref(sample).message_index))
        current: list[Any] = []
        next_boundary = "stream_start"
        for sample in ordered:
            ref = _sample_ref(sample)
            if _sample_key(ref) in blocked_keys:
                _append_segment(summaries, current, config, [next_boundary, "unrepaired_sample_boundary"])
                current = []
                next_boundary = "unrepaired_sample_boundary"
                continue
            if current:
                previous = _sample_ref(current[-1])
                reason = None
                if ref.timestamp <= previous.timestamp:
                    reason = "non_increasing_signal_time"
                elif _crosses_missing_interval(previous, ref, intervals):
                    reason = "missing_interval_boundary"
                if reason:
                    _append_segment(summaries, current, config, [next_boundary, reason])
                    current = []
                    next_boundary = reason
            current.append(sample)
        _append_segment(summaries, current, config, [next_boundary, "stream_end"])
    return summaries


def compute_actual_window(config: PoseFilterConfig, segment_samples: Iterable[Any]) -> int:
    median_dt_sec = _median_dt_sec(list(segment_samples))
    if median_dt_sec is None or median_dt_sec <= 0:
        raise ValueError("segment samples must have strictly increasing timestamps")
    raw_window = max(1, round((config.window_duration_ms / 1000.0) / median_dt_sec))
    return _nearest_odd_at_least(raw_window, config.polyorder + 1)


def handle_short_segment(
    segment_samples: Iterable[Any],
    max_window: int,
    config: PoseFilterConfig,
) -> PoseFilterSegmentSummary:
    samples = list(segment_samples)
    actual_window = _largest_odd_at_most(min(len(samples), max_window))
    status = "filtered" if actual_window > config.polyorder else "kept_original_short_segment"
    return _segment_summary(
        samples,
        config,
        actual_window if status == "filtered" else None,
        status,
        ["short_segment"],
    )


def _append_segment(
    summaries: list[PoseFilterSegmentSummary],
    samples: list[Any],
    config: PoseFilterConfig,
    boundary_reasons: list[str],
) -> None:
    if not samples:
        return
    try:
        requested_window = compute_actual_window(config, samples)
    except ValueError:
        requested_window = 0
    actual_window = _largest_odd_at_most(min(len(samples), requested_window))
    status = "filtered" if actual_window > config.polyorder else "kept_original_short_segment"
    summaries.append(
        _segment_summary(
            samples,
            config,
            actual_window if status == "filtered" else None,
            status,
            list(dict.fromkeys(boundary_reasons)),
        )
    )


def _segment_summary(
    samples: list[Any],
    config: PoseFilterConfig,
    actual_window: int | None,
    status: str,
    boundary_reasons: list[str],
) -> PoseFilterSegmentSummary:
    refs = [_sample_ref(sample) for sample in samples]
    start_ref, end_ref = refs[0], refs[-1]
    segment_id = f"pose:{start_ref.topic}:{start_ref.time_domain}:{start_ref.message_index}-{end_ref.message_index}"
    return PoseFilterSegmentSummary(
        segment_id=segment_id,
        source_topic=start_ref.topic,
        segment_start_ref=start_ref,
        segment_end_ref=end_ref,
        filtered_count=len(samples) if status == "filtered" else 0,
        kept_count=len(samples) if status != "filtered" else 0,
        rejected_count=0,
        actual_window_size_samples=actual_window,
        sample_refs=refs,
        boundary_reasons=boundary_reasons,
        status=status,
        reason=boundary_reasons[-1] if status != "filtered" else None,
        median_dt_sec=_median_dt_sec(samples),
        polyorder=config.polyorder,
        configured_window_duration_ms=config.window_duration_ms,
    )


def _median_dt_sec(samples: list[Any]) -> float | None:
    if len(samples) < 2:
        return None
    refs = [_sample_ref(sample) for sample in samples]
    deltas_ns = [float(current.timestamp) - float(previous.timestamp) for previous, current in zip(refs, refs[1:])]
    if any(delta <= 0 for delta in deltas_ns):
        return None
    return float(median(deltas_ns)) / 1_000_000_000.0


def _crosses_missing_interval(left: SignalSampleRef, right: SignalSampleRef, intervals: list[Any]) -> bool:
    return any(
        _field(interval, "topic", _field(interval, "source_topic", None)) == left.topic
        and _field(interval, "modality", "pose") == "pose"
        and _field(interval, "time_domain", left.time_domain) == left.time_domain
        and float(left.timestamp) < float(_field(interval, "end_time"))
        and float(right.timestamp) > float(_field(interval, "start_time"))
        for interval in intervals
    )


def _sample_ref(sample: Any) -> SignalSampleRef:
    if isinstance(sample, SignalSampleRef):
        return sample
    ref = _field(sample, "sample_ref", sample)
    if isinstance(ref, SignalSampleRef):
        return ref
    if isinstance(ref, dict):
        return SignalSampleRef(**{key: value for key, value in ref.items() if key in SignalSampleRef.__dataclass_fields__})
    raise TypeError("pose sample must expose a SignalSampleRef as sample_ref")


def _pose_samples(value: Iterable[Any]) -> list[Any]:
    samples = _field(value, "samples", None)
    return list(samples if samples is not None else value)


def _sample_key(ref: SignalSampleRef) -> tuple[str, int]:
    return ref.topic, ref.message_index


def _field(value: Any, name: str, default: Any = None) -> Any:
    return value.get(name, default) if isinstance(value, dict) else getattr(value, name, default)


def _nearest_odd_at_least(value: int, minimum: int) -> int:
    candidate = max(value, minimum)
    return candidate if candidate % 2 else candidate + 1


def _largest_odd_at_most(value: int) -> int:
    if value < 1:
        return 0
    return value if value % 2 else value - 1
