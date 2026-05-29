"""Tactile half-step window aggregation field aligner for Scene 3.

This module implements the window_aggregate alignment strategy for tactile
modality fields. Each step in a StepTimeline is aligned by defining a window
centered on step_time_ns with half-width equal to half the step period,
then aggregating samples within that window.

Business rules (from L2 multi-strategy field aligner):
- Window: [step_time_ns - half_period, step_time_ns + half_period)
- Samples within window → status=aggregated, with derived statistics
- Empty window (no samples) → status=missing_time
- Invalid frequency (target_step_hz <= 0) → status=invalid_input
- Aggregation includes: sample_count, coverage_ratio, mean/std/min/max
- Coverage ratio is temporal span of samples within window / window width
"""
from __future__ import annotations

import math
import statistics
from typing import Any

from schemas.field_alignment import FieldAlignmentResult
from schemas.step_timeline import (
    FieldAlignmentStatus,
    StepTimeline,
)

# Tactile sample type: (timestamp_ns, value)
TactileSample = tuple[int, float]


def _compute_half_period_ns(target_step_hz: float) -> int:
    """Compute half the step period in nanoseconds.

    Args:
        target_step_hz: Target step frequency in Hz.

    Returns:
        Half the step period in nanoseconds (integer).

    Raises:
        ValueError: If target_step_hz <= 0.
    """
    if target_step_hz <= 0:
        raise ValueError(
            f"target_step_hz must be positive, got {target_step_hz}"
        )
    period_ns = int(1_000_000_000 / target_step_hz)
    return period_ns // 2


def _samples_in_window(
    samples: list[TactileSample],
    window_start_ns: int,
    window_end_ns: int,
) -> list[TactileSample]:
    """Filter samples that fall within the window [start, end).

    Args:
        samples: List of (timestamp_ns, value) tuples.
        window_start_ns: Window start time (inclusive).
        window_end_ns: Window end time (exclusive).

    Returns:
        List of samples with timestamps in [window_start_ns, window_end_ns).
    """
    return [
        s for s in samples
        if window_start_ns <= s[0] < window_end_ns
    ]


def _compute_aggregate_stats(
    window_samples: list[TactileSample],
) -> dict[str, Any]:
    """Compute aggregate statistics from window samples.

    Args:
        window_samples: List of (timestamp_ns, value) tuples in the window.
            Must be non-empty.

    Returns:
        Dict with keys: tactile_mean, tactile_std, tactile_min,
        tactile_max, sample_count.
    """
    values = [v for _, v in window_samples]
    count = len(values)
    mean_v = sum(values) / count
    if count == 1:
        std_v = 0.0
    else:
        population_var = sum((v - mean_v) ** 2 for v in values) / count
        std_v = math.sqrt(population_var)
    min_v = min(values)
    max_v = max(values)

    return {
        "tactile_mean": mean_v,
        "tactile_std": std_v,
        "tactile_min": min_v,
        "tactile_max": max_v,
        "sample_count": count,
    }


def _compute_coverage_ratio(
    window_samples: list[TactileSample],
    window_start_ns: int,
    window_end_ns: int,
) -> float:
    """Compute temporal coverage ratio of samples within the window.

    Coverage ratio = (span of sample timestamps) / (window width).
    For 0 or 1 samples, returns 0.0 (single point has no temporal extent).
    Cap result to [0.0, 1.0].

    Args:
        window_samples: List of (timestamp_ns, value) tuples in the window.
        window_start_ns: Window start time.
        window_end_ns: Window end time.

    Returns:
        Coverage ratio in range [0.0, 1.0].
    """
    if len(window_samples) < 2:
        return 0.0

    timestamps = [ts for ts, _ in window_samples]
    min_ts = min(timestamps)
    max_ts = max(timestamps)
    window_width = window_end_ns - window_start_ns

    if window_width <= 0:
        return 0.0

    span = max_ts - min_ts
    return min(1.0, max(0.0, span / window_width))


def align_tactile_field(
    timeline: StepTimeline,
    field_name: str,
    source_topic: str,
    output_topic: str,
    tactile_samples: list[TactileSample],
    target_step_hz: float | None = None,
) -> list[FieldAlignmentResult]:
    """Align a tactile field to a step timeline using half-step window aggregation.

    For each step in the timeline:
    1. Compute window: [step_time_ns - half_period, step_time_ns + half_period).
    2. Find samples within this window.
    3. If samples found → aggregate (mean, std, min, max), compute coverage.
    4. If no samples → status=missing_time.
    5. If target_step_hz is invalid (≤ 0 or None) → status=invalid_input.

    Args:
        timeline: Step timeline with step entries.
        field_name: Name of the tactile field (e.g. "tactile_left").
        source_topic: MCAP_A source topic.
        output_topic: Aligned output topic.
        tactile_samples: List of (timestamp_ns, value) tuples.
        target_step_hz: Target step frequency in Hz. If None, uses
            timeline.target_step_hz.

    Returns:
        List of FieldAlignmentResult, one per step.
    """
    results: list[FieldAlignmentResult] = []

    # Determine target_step_hz
    hz = target_step_hz if target_step_hz is not None else float(timeline.target_step_hz)

    if hz <= 0:
        # Invalid frequency for all steps
        for step_entry in timeline.steps:
            results.append(
                FieldAlignmentResult(
                    step_index=step_entry.step_index,
                    step_time_ns=step_entry.step_time_ns,
                    field_name=field_name,
                    status=FieldAlignmentStatus.invalid_input.value,
                    alignment_method="window_aggregate",
                    source_topic=source_topic,
                    output_topic=output_topic,
                    fallback_reason="invalid_step_period",
                )
            )
        return results

    half_period_ns = _compute_half_period_ns(hz)

    for step_entry in timeline.steps:
        step_time_ns = step_entry.step_time_ns
        window_start_ns = step_time_ns - half_period_ns
        window_end_ns = step_time_ns + half_period_ns

        # Find samples in window
        window_samples = _samples_in_window(
            tactile_samples, window_start_ns, window_end_ns
        )

        sample_count = len(window_samples)

        if sample_count == 0:
            # Empty window → missing_time
            results.append(
                FieldAlignmentResult(
                    step_index=step_entry.step_index,
                    step_time_ns=step_time_ns,
                    field_name=field_name,
                    status=FieldAlignmentStatus.missing_time.value,
                    alignment_method="window_aggregate",
                    source_topic=source_topic,
                    output_topic=output_topic,
                    window_start_time_ns=window_start_ns,
                    window_end_time_ns=window_end_ns,
                    sample_count=0,
                    coverage_ratio=None,
                )
            )
        else:
            # Samples found → aggregate
            stats = _compute_aggregate_stats(window_samples)
            coverage = _compute_coverage_ratio(
                window_samples, window_start_ns, window_end_ns
            )

            results.append(
                FieldAlignmentResult(
                    step_index=step_entry.step_index,
                    step_time_ns=step_time_ns,
                    field_name=field_name,
                    status=FieldAlignmentStatus.aggregated.value,
                    alignment_method="window_aggregate",
                    source_topic=source_topic,
                    output_topic=output_topic,
                    window_start_time_ns=window_start_ns,
                    window_end_time_ns=window_end_ns,
                    sample_count=sample_count,
                    coverage_ratio=coverage,
                    derived_value=stats,
                )
            )

    return results
