"""Pose interpolation / slerp / fallback field aligner for Scene 3.

This module implements the interpolation+slerp alignment strategy for pose
modality fields. Each step in a StepTimeline is aligned by finding before
and after pose samples and interpolating position (linear) and orientation
(slerp) between them. When interpolation is not possible, it falls back
to nearest-neighbor.

Business rules (from L2 multi-strategy field aligner):
- Both neighbors valid → position linear interpolation + quaternion slerp
- Missing before or after neighbor → fallback to nearest
- Neighbor beyond max_dt_ms → fallback to nearest
- No pose samples → missing_time
- Invalid quaternion (norm != 1) → invalid_input
"""
from __future__ import annotations

from typing import Any

import numpy as np

from schemas.field_alignment import FieldAlignmentResult, DerivedAlignmentValue
from schemas.step_timeline import (
    FieldAlignmentStatus,
    StepTimeline,
)

# Pose sample type: (timestamp_ns, position_xyz, orientation_xyzw)
PoseSample = tuple[int, tuple[float, float, float], tuple[float, float, float, float]]


def _normalize_quaternion(q: np.ndarray) -> np.ndarray:
    """Return normalized quaternion vector (unit length)."""
    norm = float(np.linalg.norm(q))
    if norm == 0.0:
        raise ValueError("quaternion norm must be non-zero")
    return q / norm


def _slerp(
    q_start: np.ndarray, q_end: np.ndarray, fraction: float
) -> np.ndarray:
    """Spherical linear interpolation between two quaternions.

    Args:
        q_start: Starting quaternion as (4,) numpy array (xyzw).
        q_end: Ending quaternion as (4,) numpy array (xyzw).
        fraction: Interpolation fraction [0, 1].

    Returns:
        Interpolated unit quaternion as (4,) numpy array (xyzw).
    """
    dot = float(np.dot(q_start, q_end))

    # Handle negative dot product by negating end quaternion
    if dot < 0.0:
        q_end = -q_end
        dot = -dot

    dot = min(1.0, max(-1.0, dot))

    # For nearly co-linear quaternions, use linear interpolation
    if dot > 0.9995:
        result = q_start + fraction * (q_end - q_start)
        return _normalize_quaternion(result)

    theta_0 = np.arccos(dot)
    sin_theta_0 = np.sin(theta_0)
    theta = theta_0 * fraction
    scale_start = np.sin(theta_0 - theta) / sin_theta_0
    scale_end = np.sin(theta) / sin_theta_0
    return _normalize_quaternion(
        (scale_start * q_start) + (scale_end * q_end)
    )


def _is_valid_quaternion(
    q: tuple[float, float, float, float], tolerance: float = 1e-5
) -> bool:
    """Check if a quaternion is valid (unit norm within tolerance)."""
    qx, qy, qz, qw = q
    norm_sq = qx * qx + qy * qy + qz * qz + qw * qw
    return abs(norm_sq - 1.0) <= tolerance


def _compute_dt_ms(step_time_ns: int, sample_time_ns: int) -> float:
    """Compute absolute time difference in milliseconds."""
    return abs(step_time_ns - sample_time_ns) / 1_000_000.0


def _find_nearest_sample(
    step_time_ns: int,
    samples: list[PoseSample],
) -> PoseSample | None:
    """Find the sample with the smallest time difference to step_time_ns.

    Args:
        step_time_ns: Target step timestamp in nanoseconds.
        samples: List of (timestamp_ns, position, orientation) tuples.

    Returns:
        The nearest sample tuple, or None if samples is empty.
    """
    if not samples:
        return None
    return min(samples, key=lambda s: abs(s[0] - step_time_ns))


def _find_interpolation_neighbors(
    step_time_ns: int,
    samples: list[PoseSample],
) -> tuple[PoseSample | None, PoseSample | None]:
    """Find before and after neighbors for interpolation.

    Args:
        step_time_ns: Target step timestamp in nanoseconds.
        samples: Sorted list of (timestamp_ns, position, orientation) tuples.

    Returns:
        (before_neighbor, after_neighbor) where:
        - before: sample with max timestamp < step_time_ns (or None)
        - after: sample with min timestamp >= step_time_ns (or None)
    """
    before: PoseSample | None = None
    after: PoseSample | None = None

    for sample in samples:
        ts = sample[0]
        if ts < step_time_ns:
            if before is None or ts > before[0]:
                before = sample
        else:
            if after is None or ts < after[0]:
                after = sample

    return before, after


def _interpolate_position(
    pos_before: tuple[float, float, float],
    pos_after: tuple[float, float, float],
    fraction: float,
) -> dict[str, float]:
    """Linearly interpolate between two 3D positions.

    Args:
        pos_before: (x, y, z) of before neighbor.
        pos_after: (x, y, z) of after neighbor.
        fraction: Interpolation fraction [0, 1].

    Returns:
        Dict with position_x, position_y, position_z keys.
    """
    return {
        "position_x": pos_before[0] + fraction * (pos_after[0] - pos_before[0]),
        "position_y": pos_before[1] + fraction * (pos_after[1] - pos_before[1]),
        "position_z": pos_before[2] + fraction * (pos_after[2] - pos_before[2]),
    }


def _interpolate_orientation(
    q_before: tuple[float, float, float, float],
    q_after: tuple[float, float, float, float],
    fraction: float,
) -> dict[str, float]:
    """SLERP between two quaternions.

    Args:
        q_before: (qx, qy, qz, qw) of before neighbor.
        q_after: (qx, qy, qz, qw) of after neighbor.
        fraction: Interpolation fraction [0, 1].

    Returns:
        Dict with orientation_qx, orientation_qy, orientation_qz, orientation_qw keys.
    """
    q_start = np.array(q_before, dtype=float)
    q_end = np.array(q_after, dtype=float)
    q_result = _slerp(q_start, q_end, fraction)
    return {
        "orientation_qx": float(q_result[0]),
        "orientation_qy": float(q_result[1]),
        "orientation_qz": float(q_result[2]),
        "orientation_qw": float(q_result[3]),
    }


def align_pose_field(
    timeline: StepTimeline,
    field_name: str,
    source_topic: str,
    output_topic: str,
    pose_samples: list[PoseSample],
    max_dt_ms: float | None = None,
    fallback_strategy: str = "nearest_neighbor",
) -> list[FieldAlignmentResult]:
    """Align a pose field to a step timeline using interpolation+slerp.

    For each step in the timeline:
    1. Find before and after pose samples.
    2. If both exist and are within max_dt_ms → interpolate.
    3. If only one exists → fallback to nearest.
    4. If both exist but one is beyond max_dt_ms → fallback to nearest.
    5. If no samples → missing_time.
    6. If quaternion invalid → invalid_input.

    Args:
        timeline: Step timeline with step entries.
        field_name: Name of the pose field (e.g. "arm_pose").
        source_topic: MCAP_A source topic.
        output_topic: Aligned output topic.
        pose_samples: List of (timestamp_ns, position_xyz, orientation_xyzw).
        max_dt_ms: Maximum allowed time delta in ms for interpolation.
        fallback_strategy: Fallback strategy name (default: nearest_neighbor).

    Returns:
        List of FieldAlignmentResult, one per step.
    """
    results: list[FieldAlignmentResult] = []

    # Sort samples by timestamp for neighbor finding
    sorted_samples = sorted(pose_samples, key=lambda s: s[0])

    for step_entry in timeline.steps:
        step_time_ns = step_entry.step_time_ns

        if not sorted_samples:
            # Step 5: No samples at all
            results.append(
                FieldAlignmentResult(
                    step_index=step_entry.step_index,
                    step_time_ns=step_time_ns,
                    field_name=field_name,
                    status=FieldAlignmentStatus.missing_time.value,
                    alignment_method="none",
                    source_topic=source_topic,
                    output_topic=output_topic,
                    fallback_reason="missing_time",
                )
            )
            continue

        # Validate quaternions in all samples
        for _, _, q in sorted_samples:
            if not _is_valid_quaternion(q):
                results.append(
                    FieldAlignmentResult(
                        step_index=step_entry.step_index,
                        step_time_ns=step_time_ns,
                        field_name=field_name,
                        status=FieldAlignmentStatus.invalid_input.value,
                        alignment_method="none",
                        source_topic=source_topic,
                        output_topic=output_topic,
                        fallback_reason="invalid_quaternion",
                    )
                )
                break
        else:
            # No invalid quaternion found; proceed with alignment
            before, after = _find_interpolation_neighbors(
                step_time_ns, sorted_samples
            )

            # Case 1: Both neighbors exist
            if before is not None and after is not None:
                dt_before = _compute_dt_ms(step_time_ns, before[0])
                dt_after = _compute_dt_ms(step_time_ns, after[0])

                if (max_dt_ms is None or dt_before <= max_dt_ms) and (
                    max_dt_ms is None or dt_after <= max_dt_ms
                ):
                    # Both neighbors valid → interpolate
                    total_dt = after[0] - before[0]
                    if total_dt > 0:
                        fraction = (step_time_ns - before[0]) / total_dt
                    else:
                        fraction = 0.0

                    position = _interpolate_position(
                        before[1], after[1], fraction
                    )
                    orientation = _interpolate_orientation(
                        before[2], after[2], fraction
                    )

                    derived: dict[str, Any] = {}
                    derived.update(position)
                    derived.update(orientation)

                    results.append(
                        FieldAlignmentResult(
                            step_index=step_entry.step_index,
                            step_time_ns=step_time_ns,
                            field_name=field_name,
                            status=FieldAlignmentStatus.interpolated.value,
                            alignment_method="interpolation_slerp",
                            source_topic=source_topic,
                            output_topic=output_topic,
                            source_time_ns=step_time_ns,
                            neighbor_before_time_ns=before[0],
                            neighbor_after_time_ns=after[0],
                            derived_value=derived,
                        )
                    )
                else:
                    # Neighbor beyond threshold → fallback to nearest
                    fallback_reason = "neighbor_timeout"
                    nearest = _find_nearest_sample(
                        step_time_ns, sorted_samples
                    )
                    nearest_dt = _compute_dt_ms(
                        step_time_ns, nearest[0]
                    ) if nearest else None
                    results.append(
                        FieldAlignmentResult(
                            step_index=step_entry.step_index,
                            step_time_ns=step_time_ns,
                            field_name=field_name,
                            status=FieldAlignmentStatus.fallback_nearest.value,
                            alignment_method="nearest_neighbor",
                            source_topic=source_topic,
                            output_topic=output_topic,
                            source_time_ns=nearest[0] if nearest else None,
                            dt_ms=nearest_dt,
                            neighbor_before_time_ns=before[0],
                            neighbor_after_time_ns=after[0],
                            fallback_reason=fallback_reason,
                            derived_value={
                                "position_x": nearest[1][0],
                                "position_y": nearest[1][1],
                                "position_z": nearest[1][2],
                                "orientation_qx": nearest[2][0],
                                "orientation_qy": nearest[2][1],
                                "orientation_qz": nearest[2][2],
                                "orientation_qw": nearest[2][3],
                            }
                            if nearest
                            else None,
                        )
                    )

            elif before is not None or after is not None:
                # Case 2: Only one neighbor → fallback to nearest
                fallback_reason = "missing_neighbor"
                nearest = _find_nearest_sample(
                    step_time_ns, sorted_samples
                )
                nearest_dt = _compute_dt_ms(
                    step_time_ns, nearest[0]
                ) if nearest else None
                results.append(
                    FieldAlignmentResult(
                        step_index=step_entry.step_index,
                        step_time_ns=step_time_ns,
                        field_name=field_name,
                        status=FieldAlignmentStatus.fallback_nearest.value,
                        alignment_method="nearest_neighbor",
                        source_topic=source_topic,
                        output_topic=output_topic,
                        source_time_ns=nearest[0] if nearest else None,
                        dt_ms=nearest_dt,
                        neighbor_before_time_ns=before[0] if before else None,
                        neighbor_after_time_ns=after[0] if after else None,
                        fallback_reason=fallback_reason,
                        derived_value={
                            "position_x": nearest[1][0],
                            "position_y": nearest[1][1],
                            "position_z": nearest[1][2],
                            "orientation_qx": nearest[2][0],
                            "orientation_qy": nearest[2][1],
                            "orientation_qz": nearest[2][2],
                            "orientation_qw": nearest[2][3],
                        }
                        if nearest
                        else None,
                    )
                )

    return results
