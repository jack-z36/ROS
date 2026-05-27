"""Pose, tactile, and gripper reliability detectors for service scene two."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable

from schemas.reliability import (
    AnomalySource,
    IssueSeverity,
    IssueType,
    MissingIntervalIssue,
    SampleReliabilityIssue,
    SignalReliabilityDetectionResult,
    SignalSampleRef,
)


@dataclass(frozen=True)
class PoseSample:
    topic: str
    timestamp_ns: int
    message_index: int
    position: tuple[float, float, float]
    orientation_xyzw: tuple[float, float, float, float]
    time_domain: str = "log_time"


@dataclass(frozen=True)
class GripperSample:
    topic: str
    timestamp_ns: int
    message_index: int
    value: float
    time_domain: str = "log_time"


@dataclass(frozen=True)
class TactilePressureFrame:
    topic: str
    timestamp_ns: int
    message_index: int
    hand: str
    gripper: str
    rows: int
    cols: int
    data: list[int]
    time_domain: str = "log_time"


@dataclass(frozen=True)
class ReliabilityDetectionConfig:
    max_gap_duration_ns: int = 100_000_000
    quaternion_norm_tolerance: float = 0.05
    pose_position_jump_threshold: float | None = None
    gripper_range_min: float = 0.0
    gripper_range_max: float = 1.0
    gripper_jump_threshold: float | None = None
    gripper_stuck_min_samples: int = 5
    gripper_stuck_duration_ns: int = 1_000_000_000
    tactile_spike_mean_delta_threshold: float | None = None
    tactile_zero_ratio_threshold: float = 0.95
    tactile_zero_min_samples: int = 1
    tactile_zero_duration_ns: int = 0
    tactile_saturation_min_value: int = 0
    tactile_saturation_max_value: int = 65_535
    tactile_saturation_ratio_threshold: float = 0.95
    tactile_saturation_min_samples: int = 3
    tactile_saturation_duration_ns: int = 100_000_000


def detect_pose_reliability(
    samples: Iterable[PoseSample],
    *,
    config: ReliabilityDetectionConfig | None = None,
    input_cleaned_mcap: str = "synthetic",
    rule_config_ref: str = "inline",
) -> SignalReliabilityDetectionResult:
    config = config or ReliabilityDetectionConfig()
    ordered_samples = list(samples)
    sample_issues: list[SampleReliabilityIssue] = []
    missing_interval_issues = _detect_timestamp_gaps(ordered_samples, "pose", config)

    previous: PoseSample | None = None
    for sample in ordered_samples:
        if not _all_finite(sample.position):
            sample_issues.append(
                _sample_issue(
                    sample=sample,
                    modality="pose",
                    source=AnomalySource.POSE,
                    issue_type=IssueType.POSE_JUMP,
                    field_path="pose.position",
                    message="Pose position contains a non-finite value",
                    reason="non_finite_position",
                    evidence={"position": list(sample.position)},
                )
            )

        orientation = sample.orientation_xyzw
        if not _all_finite(orientation):
            sample_issues.append(
                _sample_issue(
                    sample=sample,
                    modality="pose",
                    source=AnomalySource.POSE,
                    issue_type=IssueType.INVALID_ORIENTATION,
                    field_path="pose.orientation",
                    message="Pose orientation contains a non-finite quaternion value",
                    reason="non_finite_orientation",
                    evidence={"orientation_xyzw": list(orientation)},
                )
            )
        else:
            norm = math.sqrt(sum(value * value for value in orientation))
            if abs(norm - 1.0) > config.quaternion_norm_tolerance:
                sample_issues.append(
                    _sample_issue(
                        sample=sample,
                        modality="pose",
                        source=AnomalySource.POSE,
                        issue_type=IssueType.INVALID_ORIENTATION,
                        field_path="pose.orientation",
                        message="Pose quaternion norm is outside the configured tolerance",
                        reason="quaternion_norm_deviation",
                        evidence={"norm": norm, "tolerance": config.quaternion_norm_tolerance},
                    )
                )

        if previous is not None and config.pose_position_jump_threshold is not None:
            distance = _position_distance(previous.position, sample.position)
            if distance > config.pose_position_jump_threshold:
                sample_issues.append(
                    _sample_issue(
                        sample=sample,
                        modality="pose",
                        source=AnomalySource.POSE,
                        issue_type=IssueType.POSE_JUMP,
                        field_path="pose.position",
                        message="Pose position jump exceeds the configured threshold",
                        reason="pose_position_jump",
                        evidence={"distance": distance, "threshold": config.pose_position_jump_threshold},
                    )
                )
        previous = sample

    return _detection_result(
        input_cleaned_mcap=input_cleaned_mcap,
        rule_config_ref=rule_config_ref,
        sample_issues=sample_issues,
        missing_interval_issues=missing_interval_issues,
        modality="pose",
    )


def detect_tactile_reliability(
    frames: Iterable[TactilePressureFrame],
    *,
    config: ReliabilityDetectionConfig | None = None,
    input_cleaned_mcap: str = "synthetic",
    rule_config_ref: str = "inline",
) -> SignalReliabilityDetectionResult:
    config = config or ReliabilityDetectionConfig()
    ordered_frames = list(frames)
    sample_issues: list[SampleReliabilityIssue] = []
    missing_interval_issues = _detect_timestamp_gaps(ordered_frames, "tactile", config)

    valid_frames: list[TactilePressureFrame] = []
    for frame in ordered_frames:
        expected_size = frame.rows * frame.cols
        if frame.rows <= 0 or frame.cols <= 0 or expected_size != len(frame.data):
            sample_issues.append(
                _sample_issue(
                    sample=frame,
                    modality="tactile",
                    source=AnomalySource.TACTILE,
                    issue_type=IssueType.TACTILE_SHAPE_MISMATCH,
                    field_path="tactile.frame",
                    message="Tactile pressure frame shape does not match rows and cols",
                    reason="tactile_shape_mismatch",
                    evidence={
                        "rows": frame.rows,
                        "cols": frame.cols,
                        "expected_len": expected_size,
                        "actual_len": len(frame.data),
                    },
                )
            )
        else:
            valid_frames.append(frame)

    previous: TactilePressureFrame | None = None
    for frame in valid_frames:
        if previous is not None and config.tactile_spike_mean_delta_threshold is not None:
            mean_delta = _mean_absolute_delta(previous.data, frame.data)
            if mean_delta > config.tactile_spike_mean_delta_threshold:
                sample_issues.append(
                    _sample_issue(
                        sample=frame,
                        modality="tactile",
                        source=AnomalySource.TACTILE,
                        issue_type=IssueType.TACTILE_SPIKE,
                        field_path="tactile.frame",
                        message="Tactile pressure frame changes abruptly from the previous frame",
                        reason="tactile_spike",
                        evidence={"mean_delta": mean_delta, "threshold": config.tactile_spike_mean_delta_threshold},
                    )
                )
        previous = frame

    sample_issues.extend(
        _detect_ratio_run_issue(
            valid_frames,
            issue_type=IssueType.TACTILE_ZERO_SUSPICIOUS,
            reason="tactile_zero_suspicious",
            message="Tactile pressure frame remains mostly zero for too long",
            ratio_name="zero_ratio",
            ratio_fn=lambda frame: _value_ratio(frame.data, lambda value: value == 0),
            ratio_threshold=config.tactile_zero_ratio_threshold,
            min_samples=config.tactile_zero_min_samples,
            min_duration_ns=config.tactile_zero_duration_ns,
        )
    )
    sample_issues.extend(
        _detect_ratio_run_issue(
            valid_frames,
            issue_type=IssueType.TACTILE_SATURATION,
            reason="tactile_saturation",
            message="Tactile pressure frame remains saturated for too long",
            ratio_name="saturation_ratio",
            ratio_fn=lambda frame: _value_ratio(
                frame.data,
                lambda value: value <= config.tactile_saturation_min_value or value >= config.tactile_saturation_max_value,
            ),
            ratio_threshold=config.tactile_saturation_ratio_threshold,
            min_samples=config.tactile_saturation_min_samples,
            min_duration_ns=config.tactile_saturation_duration_ns,
        )
    )

    return _detection_result(
        input_cleaned_mcap=input_cleaned_mcap,
        rule_config_ref=rule_config_ref,
        sample_issues=sample_issues,
        missing_interval_issues=missing_interval_issues,
        modality="tactile",
    )


def detect_gripper_reliability(
    samples: Iterable[GripperSample],
    *,
    config: ReliabilityDetectionConfig | None = None,
    input_cleaned_mcap: str = "synthetic",
    rule_config_ref: str = "inline",
) -> SignalReliabilityDetectionResult:
    config = config or ReliabilityDetectionConfig()
    ordered_samples = list(samples)
    sample_issues: list[SampleReliabilityIssue] = []
    missing_interval_issues = _detect_timestamp_gaps(ordered_samples, "gripper", config)

    previous: GripperSample | None = None
    stuck_run_start: GripperSample | None = None
    stuck_run_end: GripperSample | None = None
    stuck_run_length = 1

    for sample in ordered_samples:
        if not math.isfinite(sample.value) or not (config.gripper_range_min <= sample.value <= config.gripper_range_max):
            sample_issues.append(
                _sample_issue(
                    sample=sample,
                    modality="gripper",
                    source=AnomalySource.GRIPPER,
                    issue_type=IssueType.GRIPPER_OUT_OF_RANGE,
                    field_path="gripper.value",
                    message="Gripper value is outside the configured range",
                    reason="gripper_out_of_range",
                    evidence={
                        "value": sample.value,
                        "min": config.gripper_range_min,
                        "max": config.gripper_range_max,
                    },
                )
            )

        if previous is not None:
            value_delta = abs(sample.value - previous.value)
            if config.gripper_jump_threshold is not None and value_delta > config.gripper_jump_threshold:
                sample_issues.append(
                    _sample_issue(
                        sample=sample,
                        modality="gripper",
                        source=AnomalySource.GRIPPER,
                        issue_type=IssueType.GRIPPER_JUMP,
                        field_path="gripper.value",
                        message="Gripper value jump exceeds the configured threshold",
                        reason="gripper_value_jump",
                        evidence={"delta": value_delta, "threshold": config.gripper_jump_threshold},
                    )
                )

            if math.isfinite(value_delta) and value_delta == 0.0:
                if stuck_run_start is None:
                    stuck_run_start = previous
                    stuck_run_length = 2
                else:
                    stuck_run_length += 1
                stuck_run_end = sample
            else:
                stuck_run_start = None
                stuck_run_end = None
                stuck_run_length = 1
        previous = sample

    if stuck_run_start is not None and stuck_run_end is not None:
        stuck_duration = stuck_run_end.timestamp_ns - stuck_run_start.timestamp_ns
        if stuck_run_length >= config.gripper_stuck_min_samples and stuck_duration >= config.gripper_stuck_duration_ns:
            sample_issues.append(
                _sample_issue(
                    sample=stuck_run_end,
                    modality="gripper",
                    source=AnomalySource.GRIPPER,
                    issue_type=IssueType.GRIPPER_STUCK,
                    field_path="gripper.value",
                    message="Gripper value remains unchanged for too long",
                    reason="gripper_stuck_value",
                    evidence={
                        "value": stuck_run_end.value,
                        "sample_count": stuck_run_length,
                        "duration_ns": stuck_duration,
                    },
                )
            )

    return _detection_result(
        input_cleaned_mcap=input_cleaned_mcap,
        rule_config_ref=rule_config_ref,
        sample_issues=sample_issues,
        missing_interval_issues=missing_interval_issues,
        modality="gripper",
    )


def _detect_timestamp_gaps(
    samples: list[PoseSample] | list[GripperSample] | list[TactilePressureFrame],
    modality: str,
    config: ReliabilityDetectionConfig,
) -> list[MissingIntervalIssue]:
    issues: list[MissingIntervalIssue] = []
    for previous, current in zip(samples, samples[1:]):
        gap_duration = current.timestamp_ns - previous.timestamp_ns
        if gap_duration > config.max_gap_duration_ns:
            estimated_missing = max(1, math.floor(gap_duration / config.max_gap_duration_ns) - 1)
            issues.append(
                MissingIntervalIssue(
                    issue_id=f"{modality}-missing-{previous.message_index}-{current.message_index}",
                    topic=current.topic,
                    modality=modality,
                    start_time=previous.timestamp_ns,
                    end_time=current.timestamp_ns,
                    expected_count=estimated_missing,
                    actual_count=0,
                    severity=IssueSeverity.WARNING,
                    suggested_action="mark_unhandled_gap",
                    time_domain=current.time_domain,
                    reason="missing_segment",
                )
            )
    return issues


def _sample_issue(
    *,
    sample: PoseSample | GripperSample | TactilePressureFrame,
    modality: str,
    source: AnomalySource,
    issue_type: IssueType,
    field_path: str,
    message: str,
    reason: str,
    evidence: dict[str, object],
) -> SampleReliabilityIssue:
    return SampleReliabilityIssue(
        issue_id=f"{modality}-{issue_type.value}-{sample.message_index}",
        sample_ref=SignalSampleRef(
            topic=sample.topic,
            timestamp=sample.timestamp_ns,
            message_index=sample.message_index,
            modality=modality,
            time_domain=sample.time_domain,
        ),
        issue_type=issue_type,
        severity=IssueSeverity.ERROR,
        source=source,
        field_path=field_path,
        message=message,
        suggested_action="inspect_required",
        reason=reason,
        evidence=[evidence],
    )


def _detection_result(
    *,
    input_cleaned_mcap: str,
    rule_config_ref: str,
    sample_issues: list[SampleReliabilityIssue],
    missing_interval_issues: list[MissingIntervalIssue],
    modality: str,
) -> SignalReliabilityDetectionResult:
    return SignalReliabilityDetectionResult(
        input_cleaned_mcap=input_cleaned_mcap,
        rule_config_ref=rule_config_ref,
        sample_issues=sample_issues,
        missing_interval_issues=missing_interval_issues,
        summary_by_modality={
            modality: {
                "sample_issues": len(sample_issues),
                "missing_interval_issues": len(missing_interval_issues),
            }
        },
    )


def _detect_ratio_run_issue(
    frames: list[TactilePressureFrame],
    *,
    issue_type: IssueType,
    reason: str,
    message: str,
    ratio_name: str,
    ratio_fn,
    ratio_threshold: float,
    min_samples: int,
    min_duration_ns: int,
) -> list[SampleReliabilityIssue]:
    issues: list[SampleReliabilityIssue] = []
    run_start: TactilePressureFrame | None = None
    run_end: TactilePressureFrame | None = None
    run_length = 0
    run_ratio = 0.0

    for frame in frames:
        ratio = ratio_fn(frame)
        if ratio >= ratio_threshold:
            if run_start is None:
                run_start = frame
                run_length = 1
            else:
                run_length += 1
            run_end = frame
            run_ratio = ratio
        else:
            if _run_meets_threshold(run_start, run_end, run_length, min_samples, min_duration_ns):
                issues.append(
                    _sample_issue(
                        sample=run_end,
                        modality="tactile",
                        source=AnomalySource.TACTILE,
                        issue_type=issue_type,
                        field_path="tactile.frame",
                        message=message,
                        reason=reason,
                        evidence={
                            ratio_name: run_ratio,
                            "threshold": ratio_threshold,
                            "sample_count": run_length,
                            "duration_ns": run_end.timestamp_ns - run_start.timestamp_ns,
                        },
                    )
                )
            run_start = None
            run_end = None
            run_length = 0
            run_ratio = 0.0

    if _run_meets_threshold(run_start, run_end, run_length, min_samples, min_duration_ns):
        issues.append(
            _sample_issue(
                sample=run_end,
                modality="tactile",
                source=AnomalySource.TACTILE,
                issue_type=issue_type,
                field_path="tactile.frame",
                message=message,
                reason=reason,
                evidence={
                    ratio_name: run_ratio,
                    "threshold": ratio_threshold,
                    "sample_count": run_length,
                    "duration_ns": run_end.timestamp_ns - run_start.timestamp_ns,
                },
            )
        )
    return issues


def _run_meets_threshold(
    run_start: TactilePressureFrame | None,
    run_end: TactilePressureFrame | None,
    run_length: int,
    min_samples: int,
    min_duration_ns: int,
) -> bool:
    if run_start is None or run_end is None:
        return False
    return run_length >= min_samples and run_end.timestamp_ns - run_start.timestamp_ns >= min_duration_ns


def _mean_absolute_delta(left: list[int], right: list[int]) -> float:
    return sum(abs(right_value - left_value) for left_value, right_value in zip(left, right)) / len(left)


def _value_ratio(values: list[int], predicate) -> float:
    if not values:
        return 0.0
    return sum(1 for value in values if predicate(value)) / len(values)


def _all_finite(values: tuple[float, ...]) -> bool:
    return all(math.isfinite(value) for value in values)


def _position_distance(left: tuple[float, float, float], right: tuple[float, float, float]) -> float:
    if not _all_finite(left) or not _all_finite(right):
        return 0.0
    return math.sqrt(sum((right_value - left_value) ** 2 for left_value, right_value in zip(left, right)))
