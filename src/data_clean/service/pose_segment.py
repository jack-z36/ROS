from __future__ import annotations

from statistics import median
from typing import Any, Iterable

from schemas.pose_filter import PoseFilterConfig, PoseFilterSegmentSummary
from schemas.reliability import SignalSampleRef


def split_reliable_segments(
    pose_sequence: Iterable[Any],
    missing_intervals: Iterable[Any],
    unrepaired_refs: Iterable[Any],
) -> list[PoseFilterSegmentSummary]:
    samples = _pose_samples(pose_sequence)
    intervals = list(missing_intervals)
    blocked_keys = {_sample_key(ref) for ref in unrepaired_refs}
    segments: list[PoseFilterSegmentSummary] = []
    current: list[Any] = []
    split_reason: str | None = None

    for sample in samples:
        sample_ref = _sample_ref(sample)
        if _sample_key(sample_ref) in blocked_keys:
            _append_segment(segments, current, split_reason or "split_by_unrepaired_pose")
            current = []
            split_reason = "split_by_unrepaired_pose"
            continue

        if current:
            previous_ref = _sample_ref(current[-1])
            if sample_ref.timestamp <= previous_ref.timestamp:
                segments.clear()
                segments.append(_segment_summary(current + [sample], None, "skipped_invalid_time", "invalid_segment_time_order"))
                return segments
            if _crosses_missing_interval(previous_ref, sample_ref, intervals):
                _append_segment(segments, current, "split_by_missing_interval")
                current = []
                split_reason = "split_by_missing_interval"

        current.append(sample)

    _append_segment(segments, current, split_reason)
    return segments


def compute_actual_window(config: PoseFilterConfig, segment_samples: Iterable[Any]) -> int:
    median_dt_sec = _median_dt_sec(list(segment_samples))
    if median_dt_sec is None or median_dt_sec <= 0:
        raise ValueError("segment samples must have strictly increasing timestamps")

    raw_window = max(1, round((config.window_duration_ms / 1000.0) / median_dt_sec))
    return _nearest_odd_at_least(raw_window, config.polyorder + 1)


def handle_short_segment(segment_samples: Iterable[Any], max_window: int) -> PoseFilterSegmentSummary:
    samples = list(segment_samples)
    actual_window = _largest_odd_at_most(min(len(samples), max_window))
    if actual_window <= PoseFilterConfig().polyorder:
        return _segment_summary(samples, None, "kept_original_short_segment", "short_segment_kept_original")
    return _segment_summary(samples, actual_window, "filtered", "adaptive_short_segment_window")


def _append_segment(segments: list[PoseFilterSegmentSummary], samples: list[Any], reason: str | None) -> None:
    if not samples:
        return
    config = PoseFilterConfig()
    actual_window = compute_actual_window(config, samples) if len(samples) > 1 else config.polyorder + 1
    if actual_window > len(samples):
        segments.append(handle_short_segment(samples, actual_window))
        if reason and segments[-1].status == "filtered":
            segments[-1].reason = reason
        return
    segments.append(_segment_summary(samples, actual_window, "filtered", reason))


def _segment_summary(
    samples: list[Any],
    actual_window_size_samples: int | None,
    status: str,
    reason: str | None,
) -> PoseFilterSegmentSummary:
    start_ref = _sample_ref(samples[0])
    end_ref = _sample_ref(samples[-1])
    sample_count = len(samples)
    summary = PoseFilterSegmentSummary(
        source_topic=start_ref.topic,
        segment_start_ref=start_ref,
        segment_end_ref=end_ref,
        filtered_count=sample_count if status == "filtered" else 0,
        kept_count=sample_count if status != "filtered" else 0,
        rejected_count=0,
        actual_window_size_samples=actual_window_size_samples,
    )
    summary.segment_id = f"{start_ref.topic}:{start_ref.message_index}-{end_ref.message_index}"
    summary.sample_count = sample_count
    summary.median_dt_sec = _median_dt_sec(samples)
    summary.status = status
    summary.reason = reason
    summary.polyorder = PoseFilterConfig().polyorder
    summary.configured_window_duration_ms = PoseFilterConfig().window_duration_ms
    return summary


def _median_dt_sec(samples: list[Any]) -> float | None:
    if len(samples) < 2:
        return None
    refs = [_sample_ref(sample) for sample in samples]
    deltas = [float(current.timestamp) - float(previous.timestamp) for previous, current in zip(refs, refs[1:])]
    if any(delta <= 0 for delta in deltas):
        return None
    return float(median(deltas))


def _crosses_missing_interval(previous_ref: SignalSampleRef, current_ref: SignalSampleRef, intervals: list[Any]) -> bool:
    for interval in intervals:
        topic = _field(interval, "topic", _field(interval, "source_topic", None))
        modality = _field(interval, "modality", "pose")
        if topic not in (None, previous_ref.topic) or modality != "pose":
            continue
        start_time = float(_field(interval, "start_time"))
        end_time = float(_field(interval, "end_time"))
        if float(previous_ref.timestamp) < end_time and float(current_ref.timestamp) > start_time:
            return True
    return False


def _sample_ref(sample: Any) -> SignalSampleRef:
    ref = _field(sample, "sample_ref", None)
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
    if isinstance(sample, SignalSampleRef):
        return sample
    if isinstance(sample, dict) and {"topic", "timestamp", "message_index"}.issubset(sample):
        return SignalSampleRef(
            topic=str(sample["topic"]),
            timestamp=sample["timestamp"],
            message_index=int(sample["message_index"]),
            modality=str(sample.get("modality", "pose")),
            time_domain=str(sample.get("time_domain", "log_time")),
        )
    raise TypeError("pose sample must expose a SignalSampleRef as sample_ref")


def _pose_samples(pose_sequence: Iterable[Any]) -> list[Any]:
    samples = _field(pose_sequence, "samples", None)
    if samples is not None:
        return list(samples)
    return list(pose_sequence)


def _sample_key(ref: Any) -> tuple[str, int]:
    sample_ref = _sample_ref(ref) if not isinstance(ref, SignalSampleRef) else ref
    return sample_ref.topic, sample_ref.message_index


def _field(value: Any, name: str, default: Any = None) -> Any:
    if isinstance(value, dict):
        return value.get(name, default)
    return getattr(value, name, default)


def _nearest_odd_at_least(value: int, minimum: int) -> int:
    candidate = max(value, minimum)
    if candidate % 2 == 1:
        return candidate
    lower = candidate - 1
    upper = candidate + 1
    if lower >= minimum and abs(value - lower) < abs(upper - value):
        return lower
    return upper


def _largest_odd_at_most(value: int) -> int:
    if value < 1:
        return 0
    return value if value % 2 == 1 else value - 1
