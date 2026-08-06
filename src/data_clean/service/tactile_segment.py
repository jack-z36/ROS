from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable

from schemas.reliability import SignalSampleRef
from schemas.tactile_filter import TactileFilterConfig, TactileFilterSegmentSummary


def detect_contact_change(current_frame: Any, prev_frame: Any, threshold: float | None) -> bool:
    if threshold is None:
        return False
    current = list(_field(current_frame, "data", []))
    previous = list(_field(prev_frame, "data", []))
    if not current or len(current) != len(previous):
        return False
    return any(abs(float(a) - float(b)) > threshold for a, b in zip(current, previous))


def split_tactile_segments(
    frames: Iterable[Any],
    missing_intervals: Iterable[Any],
    config: TactileFilterConfig,
) -> list[TactileFilterSegmentSummary]:
    intervals = list(missing_intervals)
    by_stream: dict[tuple[str, str], list[Any]] = defaultdict(list)
    for frame in frames:
        ref = _sample_ref(frame)
        by_stream[(ref.topic, ref.time_domain)].append(frame)

    summaries: list[TactileFilterSegmentSummary] = []
    for stream_frames in by_stream.values():
        ordered = sorted(stream_frames, key=lambda frame: (_sample_ref(frame).timestamp, _sample_ref(frame).message_index))
        current: list[Any] = []
        boundary = "stream_start"
        for frame in ordered:
            ref = _sample_ref(frame)
            if _is_unrepaired_boundary(frame):
                _append_segment(summaries, current, config, [boundary, "unrepaired_sample_boundary"])
                current = []
                summaries.append(_boundary_segment(frame, config, "skipped_boundary", "unrepaired_sample_boundary"))
                boundary = "unrepaired_sample_boundary"
                continue
            if not _has_valid_shape(frame):
                _append_segment(summaries, current, config, [boundary, "invalid_shape_boundary"])
                current = []
                summaries.append(_boundary_segment(frame, config, "invalid_shape", "tactile_shape_mismatch"))
                boundary = "invalid_shape_boundary"
                continue

            reason = None
            if current:
                previous = current[-1]
                previous_ref = _sample_ref(previous)
                if _crosses_missing_interval(previous_ref, ref, intervals):
                    reason = "missing_interval_boundary"
                elif _shape(previous) != _shape(frame):
                    reason = "shape_change_boundary"
                elif detect_contact_change(frame, previous, config.contact_reset_threshold):
                    reason = "contact_reset_boundary"
            if reason:
                _append_segment(summaries, current, config, [boundary, reason])
                current = []
                boundary = reason
            current.append(frame)
        _append_segment(summaries, current, config, [boundary, "stream_end"])
    return summaries


def _append_segment(
    summaries: list[TactileFilterSegmentSummary],
    frames: list[Any],
    config: TactileFilterConfig,
    reasons: list[str],
) -> None:
    if not frames:
        return
    status = "filtered" if len(frames) >= config.median_window else "kept_original"
    summaries.append(_summary(frames, config, status, list(dict.fromkeys(reasons))))


def _boundary_segment(frame: Any, config: TactileFilterConfig, status: str, reason: str) -> TactileFilterSegmentSummary:
    return _summary([frame], config, status, [reason])


def _summary(
    frames: list[Any],
    config: TactileFilterConfig,
    status: str,
    reasons: list[str],
) -> TactileFilterSegmentSummary:
    refs = [_sample_ref(frame) for frame in frames]
    start, end = refs[0], refs[-1]
    rows, cols = _shape(frames[0])
    segment_id = f"tactile:{start.topic}:{start.time_domain}:{start.message_index}-{end.message_index}:{status}"
    return TactileFilterSegmentSummary(
        segment_id=segment_id,
        source_topic=start.topic,
        segment_start_ref=start,
        segment_end_ref=end,
        sample_count=len(frames),
        filtered_count=len(frames) if status == "filtered" else 0,
        kept_original_count=len(frames) if status == "kept_original" else 0,
        skipped_boundary_count=len(frames) if status == "skipped_boundary" else 0,
        ema_reset_count=1 if status == "filtered" else 0,
        invalid_shape_count=len(frames) if status == "invalid_shape" else 0,
        median_window=config.median_window,
        ema_alpha=config.ema_alpha,
        sample_refs=refs,
        boundary_reasons=reasons,
        status=status,
        reason=reasons[-1] if reasons else None,
        rows=rows,
        cols=cols,
    )


def _is_unrepaired_boundary(frame: Any) -> bool:
    status = _field(frame, "status", _field(frame, "repair_status", None))
    status = status.value if hasattr(status, "value") else status
    return str(status) in {"unrepaired", "unrepairable", "skipped", "skipped_boundary"}


def _has_valid_shape(frame: Any) -> bool:
    rows, cols = _shape(frame)
    return rows > 0 and cols > 0 and rows * cols == len(list(_field(frame, "data", [])))


def _shape(frame: Any) -> tuple[int, int]:
    return int(_field(frame, "rows", 0)), int(_field(frame, "cols", 0))


def _crosses_missing_interval(left: SignalSampleRef, right: SignalSampleRef, intervals: list[Any]) -> bool:
    return any(
        _field(interval, "topic", _field(interval, "source_topic", None)) == left.topic
        and _field(interval, "modality", "tactile") == "tactile"
        and _field(interval, "time_domain", left.time_domain) == left.time_domain
        and float(left.timestamp) < float(_field(interval, "end_time"))
        and float(right.timestamp) > float(_field(interval, "start_time"))
        for interval in intervals
    )


def _sample_ref(frame: Any) -> SignalSampleRef:
    if isinstance(frame, SignalSampleRef):
        return frame
    ref = _field(frame, "sample_ref", frame)
    if isinstance(ref, SignalSampleRef):
        return ref
    if isinstance(ref, dict):
        values = {key: value for key, value in ref.items() if key in SignalSampleRef.__dataclass_fields__}
        values.setdefault("modality", "tactile")
        return SignalSampleRef(**values)
    return SignalSampleRef(
        topic=str(_field(frame, "topic")),
        timestamp=_field(frame, "timestamp_ns", _field(frame, "timestamp")),
        message_index=int(_field(frame, "message_index")),
        modality="tactile",
        time_domain=str(_field(frame, "time_domain", "log_time")),
        log_time_ns=_field(frame, "log_time_ns", None),
        publish_time_ns=_field(frame, "publish_time_ns", None),
        sequence=_field(frame, "sequence", None),
        source_channel_id=_field(frame, "source_channel_id", None),
    )


def _field(value: Any, name: str, default: Any = None) -> Any:
    return value.get(name, default) if isinstance(value, dict) else getattr(value, name, default)
