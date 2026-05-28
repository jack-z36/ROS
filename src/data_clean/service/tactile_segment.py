from __future__ import annotations

from typing import Any, Iterable

from schemas.reliability import SignalSampleRef
from schemas.tactile_filter import TactileFilterConfig, TactileFilterSegmentSummary


def detect_contact_change(current_frame: Any, prev_frame: Any, threshold: float | None) -> bool:
    if threshold is None:
        return False
    current_data = list(_field(current_frame, "data", []))
    prev_data = list(_field(prev_frame, "data", []))
    if len(current_data) != len(prev_data):
        return False
    return any(abs(float(current) - float(previous)) > threshold for current, previous in zip(current_data, prev_data))


def split_tactile_segments(
    frames: Iterable[Any],
    missing_intervals: Iterable[Any],
    config: TactileFilterConfig,
) -> list[TactileFilterSegmentSummary]:
    ordered_frames = sorted(list(frames), key=lambda frame: (_sample_ref(frame).timestamp, _sample_ref(frame).message_index))
    intervals = list(missing_intervals)
    segments: list[TactileFilterSegmentSummary] = []
    current: list[Any] = []
    expected_shape: tuple[int, int] | None = None
    pending_reason: str | None = None
    pending_reset: SignalSampleRef | None = None

    for frame in ordered_frames:
        ref = _sample_ref(frame)
        if _is_unrepaired_boundary(frame):
            _append_segment(segments, current, config, "unrepaired_sample_boundary", pending_reset)
            current = []
            pending_reason = "unrepaired_sample_boundary"
            pending_reset = None
            continue

        shape = _shape(frame)
        if not _has_valid_shape(frame) or (expected_shape is not None and shape != expected_shape):
            _append_segment(segments, current, config, pending_reason or "tactile_shape_mismatch", pending_reset)
            current = []
            pending_reason = None
            pending_reset = None
            segments.append(_invalid_shape_segment(frame, config))
            continue
        if expected_shape is None:
            expected_shape = shape

        if current:
            previous_frame = current[-1]
            previous_ref = _sample_ref(previous_frame)
            if _crosses_missing_interval(previous_ref, ref, intervals):
                _append_segment(segments, current, config, "missing_interval_boundary", pending_reset)
                current = []
                pending_reason = "missing_interval_boundary"
                pending_reset = None
            elif detect_contact_change(frame, previous_frame, config.contact_reset_threshold):
                _append_segment(segments, current, config, "contact_reset", pending_reset)
                current = []
                pending_reason = "contact_reset"
                pending_reset = ref

        current.append(frame)

    _append_segment(segments, current, config, pending_reason, pending_reset)
    return segments


def _append_segment(
    segments: list[TactileFilterSegmentSummary],
    frames: list[Any],
    config: TactileFilterConfig,
    reason: str | None,
    reset_ref: SignalSampleRef | None,
) -> None:
    if not frames:
        return
    status = "filtered" if len(frames) >= config.median_window else "kept_original"
    segment = _segment_summary(frames, config, status)
    segment.reason = reason or "segment_ready"
    segment.boundary_reasons = [segment.reason]
    segment.reset_points = [reset_ref] if reset_ref is not None else []
    segment.ema_reset_count = len(segment.reset_points)
    segments.append(segment)


def _segment_summary(frames: list[Any], config: TactileFilterConfig, status: str) -> TactileFilterSegmentSummary:
    start_ref = _sample_ref(frames[0])
    end_ref = _sample_ref(frames[-1])
    rows, cols = _shape(frames[0])
    sample_count = len(frames)
    segment = TactileFilterSegmentSummary(
        source_topic=start_ref.topic,
        segment_start_ref=start_ref,
        segment_end_ref=end_ref,
        sample_count=sample_count,
        filtered_count=sample_count if status == "filtered" else 0,
        kept_original_count=sample_count if status == "kept_original" else 0,
        skipped_boundary_count=0,
        ema_reset_count=0,
        invalid_shape_count=sample_count if status == "invalid_shape" else 0,
        median_window=config.median_window,
        ema_alpha=config.ema_alpha,
    )
    segment.segment_id = f"{start_ref.topic}:{start_ref.message_index}-{end_ref.message_index}"
    segment.start_time = start_ref.timestamp
    segment.end_time = end_ref.timestamp
    segment.cell_count = rows * cols
    segment.rows = rows
    segment.cols = cols
    segment.status = status
    return segment


def _invalid_shape_segment(frame: Any, config: TactileFilterConfig) -> TactileFilterSegmentSummary:
    segment = _segment_summary([frame], config, "invalid_shape")
    rows = _field(frame, "rows", 0)
    cols = _field(frame, "cols", 0)
    segment.cell_count = int(rows) * int(cols) if int(rows) > 0 and int(cols) > 0 else 0
    segment.reason = "tactile_shape_mismatch"
    segment.boundary_reasons = ["tactile_shape_mismatch"]
    segment.reset_points = []
    return segment


def _is_unrepaired_boundary(frame: Any) -> bool:
    status = _field(frame, "status", _field(frame, "repair_status", None))
    if hasattr(status, "value"):
        status = status.value
    return str(status) in {"unrepaired", "unrepairable", "skipped", "skipped_boundary"}


def _has_valid_shape(frame: Any) -> bool:
    rows, cols = _shape(frame)
    return rows > 0 and cols > 0 and rows * cols == len(list(_field(frame, "data", [])))


def _shape(frame: Any) -> tuple[int, int]:
    return int(_field(frame, "rows", 0)), int(_field(frame, "cols", 0))


def _crosses_missing_interval(previous_ref: SignalSampleRef, current_ref: SignalSampleRef, intervals: list[Any]) -> bool:
    for interval in intervals:
        topic = _field(interval, "topic", _field(interval, "source_topic", None))
        modality = _field(interval, "modality", "tactile")
        if topic not in (None, previous_ref.topic) or modality != "tactile":
            continue
        start_time = float(_field(interval, "start_time"))
        end_time = float(_field(interval, "end_time"))
        if float(previous_ref.timestamp) < end_time and float(current_ref.timestamp) > start_time:
            return True
    return False


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
    if isinstance(frame, SignalSampleRef):
        return frame
    if isinstance(frame, dict) and {"topic", "timestamp", "message_index"}.issubset(frame):
        return SignalSampleRef(
            topic=str(frame["topic"]),
            timestamp=frame["timestamp"],
            message_index=int(frame["message_index"]),
            modality=str(frame.get("modality", "tactile")),
            time_domain=str(frame.get("time_domain", "log_time")),
        )
    topic = str(_field(frame, "topic"))
    timestamp = _field(frame, "timestamp_ns", _field(frame, "timestamp"))
    message_index = int(_field(frame, "message_index"))
    return SignalSampleRef(
        topic=topic,
        timestamp=timestamp,
        message_index=message_index,
        modality="tactile",
        time_domain=str(_field(frame, "time_domain", "log_time")),
    )


def _field(value: Any, name: str, default: Any = None) -> Any:
    if isinstance(value, dict):
        return value.get(name, default)
    return getattr(value, name, default)
