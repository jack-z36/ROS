"""Unified step timeline generator for Scene 3.

This service consumes the output of the MCAP_A input inventory and validator,
reads the baseline image intersection and target step frequency, and produces
a unified StepTimeline with rational-accumulation precision for non-integer-ns
frequencies (e.g. 15 Hz).

Business rules (from L2 unified step timeline generator):
- Only consume upstream conclusions — do not re-read MCAP_A or re-inventory topics.
- Input must be consumable (McapAInputValidationSummary.status == "consumable").
- Baseline intersection must exist (has_baseline_intersection == true, start != None).
- Target step frequency must be > 0.
- Start time must be <= end time.
- Short intervals (start == end) produce exactly 1 step.
- Non-integer-ns periods use Fraction-based rational accumulation with round-to-ns.
"""

from __future__ import annotations

from datetime import datetime, timezone
from fractions import Fraction
from typing import Any

from schemas.alignment_config import Scene3AlignmentConfig
from schemas.alignment_input import (
    InputValidationStatus,
    McapAInputValidationSummary,
    SourceTopicCatalog,
)
from schemas.step_timeline import (
    StepTimeline,
    StepTimelineEntry,
    StepTimelineGenerationSummary,
)

# Default timeline identifier used when caller does not provide one
_DEFAULT_TIMELINE_ID = "step_timeline"


def _validate_inputs(
    validation_summary: McapAInputValidationSummary,
    catalog: SourceTopicCatalog,
    config: Scene3AlignmentConfig,
) -> tuple[list[str], int | None, int | None]:
    """Validate input conditions and return failure reasons + baseline range.

    Checks performed (in order):
      1. Input must be consumable.
      2. Baseline intersection must exist.
      3. Target step Hz must be positive.
      4. Time range must be valid (start <= end).

    Returns:
        Tuple of (failure_reasons, start_time_ns, end_time_ns).
        On failure, failure_reasons is non-empty and start/end may be None.
        On success, failure_reasons is empty and start/end are valid ints.
    """
    failure_reasons: list[str] = []
    start_ns: int | None = None
    end_ns: int | None = None

    # 1. Consumable check
    if validation_summary.status != InputValidationStatus.CONSUMABLE:
        failure_reasons.append("input_not_consumable")

    # 2. Baseline intersection check
    # Try validation_summary first, fall back to catalog
    if (
        validation_summary.has_baseline_intersection
        and validation_summary.baseline_intersection_start_ns is not None
        and validation_summary.baseline_intersection_end_ns is not None
    ):
        start_ns = validation_summary.baseline_intersection_start_ns
        end_ns = validation_summary.baseline_intersection_end_ns
    elif (
        catalog.has_baseline_intersection
        and catalog.baseline_intersection_start_ns is not None
        and catalog.baseline_intersection_end_ns is not None
    ):
        start_ns = catalog.baseline_intersection_start_ns
        end_ns = catalog.baseline_intersection_end_ns
    else:
        failure_reasons.append("missing_baseline_intersection")

    # 3. Valid frequency check
    if config.target_step_hz <= 0:
        failure_reasons.append("invalid_target_step_hz")

    # 4. Time range check (only if we have valid baseline values)
    if start_ns is not None and end_ns is not None:
        if start_ns > end_ns:
            failure_reasons.append("invalid_time_range")

    return failure_reasons, start_ns, end_ns


def _generate_step_timestamps(
    start_ns: int,
    end_ns: int,
    target_hz: int,
) -> list[StepTimelineEntry]:
    """Generate minute step timestamps using rational accumulation.

    Uses Python's Fraction for exact rational arithmetic. Each step offset
    is computed as: offset = round(i * 1_000_000_000 / target_hz).
    The resulting step_time_ns is start_ns + offset.

    This ensures non-integer-ns frequencies (e.g. 15 Hz with period
    66_666_666.666... ns) do not accumulate systematic drift.

    Args:
        start_ns: Baseline intersection start time in nanoseconds.
        end_ns: Baseline intersection end time in nanoseconds.
        target_hz: Target step frequency in Hz.

    Returns:
        List of StepTimelineEntry objects, monotonically increasing,
        first entry at start_ns, last entry <= end_ns.
    """
    period = Fraction(1_000_000_000, target_hz)
    steps: list[StepTimelineEntry] = []
    step_index = 0

    while True:
        offset = round(step_index * period)
        step_time = start_ns + offset
        if step_time > end_ns:
            break
        steps.append(StepTimelineEntry(step_index=step_index, step_time_ns=step_time))
        step_index += 1

    return steps


def _build_failure_summary(
    failure_reasons: list[str],
    validation_summary: McapAInputValidationSummary,
    catalog: SourceTopicCatalog,
    config: Scene3AlignmentConfig,
    start_ns: int | None,
    end_ns: int | None,
) -> StepTimelineGenerationSummary:
    """Build a StepTimelineGenerationSummary for a failed generation attempt."""
    return StepTimelineGenerationSummary(
        status="failed",
        failure_reasons=failure_reasons,
        source_topic_catalog_ref="catalog_ref",
        input_validation_summary_ref="validation_ref",
        config_ref="config_ref",
        timeline_ref=None,
        target_step_hz=config.target_step_hz,
        baseline_intersection_start_ns=start_ns,
        baseline_intersection_end_ns=end_ns,
        step_count=0,
        first_step_time_ns=None,
        last_step_time_ns=None,
        created_at=datetime.now(timezone.utc).isoformat(),
    )


def _build_success_result(
    timeline: StepTimeline,
    validation_summary: McapAInputValidationSummary,
    catalog: SourceTopicCatalog,
    config: Scene3AlignmentConfig,
) -> StepTimelineGenerationSummary:
    """Build a StepTimelineGenerationSummary for a successful generation."""
    first_time = timeline.steps[0].step_time_ns if timeline.steps else None
    last_time = timeline.steps[-1].step_time_ns if timeline.steps else None

    return StepTimelineGenerationSummary(
        status="generated",
        failure_reasons=[],
        source_topic_catalog_ref="catalog_ref",
        input_validation_summary_ref="validation_ref",
        config_ref="config_ref",
        timeline_ref=timeline.timeline_id,
        target_step_hz=config.target_step_hz,
        baseline_intersection_start_ns=timeline.start_time_ns,
        baseline_intersection_end_ns=timeline.end_time_ns,
        step_count=len(timeline.steps),
        first_step_time_ns=first_time,
        last_step_time_ns=last_time,
        created_at=datetime.now(timezone.utc).isoformat(),
    )


def generate_step_timeline(
    validation_summary: McapAInputValidationSummary,
    catalog: SourceTopicCatalog,
    config: Scene3AlignmentConfig,
    timeline_id: str = _DEFAULT_TIMELINE_ID,
) -> tuple[StepTimeline | None, StepTimelineGenerationSummary]:
    """Generate a unified step timeline from validated upstream inputs.

    This is the main entry point for the unified step timeline generator.
    It validates inputs, generates step timestamps using rational accumulation,
    and returns either a successful (StepTimeline, summary) or failed
    (None, failure summary) result.

    Args:
        validation_summary: Output from MCAP_A input validator.
        catalog: Source topic catalog with baseline intersection metadata.
        config: Scene 3 alignment configuration (target_step_hz, etc.).
        timeline_id: Optional identifier for the generated timeline.

    Returns:
        Tuple of (StepTimeline | None, StepTimelineGenerationSummary).
        On success, timeline is a populated StepTimeline and summary.status
        is "generated". On failure, timeline is None and summary.status is
        "failed" with non-empty failure_reasons.
    """
    # ---- Step 1: Validate inputs ----
    failure_reasons, start_ns, end_ns = _validate_inputs(
        validation_summary, catalog, config
    )

    if failure_reasons:
        return None, _build_failure_summary(
            failure_reasons=failure_reasons,
            validation_summary=validation_summary,
            catalog=catalog,
            config=config,
            start_ns=start_ns,
            end_ns=end_ns,
        )

    # start_ns and end_ns are guaranteed non-None when failure_reasons is empty
    assert start_ns is not None and end_ns is not None

    # ---- Step 2: Generate step timestamps ----
    steps = _generate_step_timestamps(
        start_ns=start_ns,
        end_ns=end_ns,
        target_hz=config.target_step_hz,
    )

    # ---- Step 3: Build StepTimeline ----
    timeline = StepTimeline(
        timeline_id=timeline_id,
        target_step_hz=config.target_step_hz,
        start_time_ns=start_ns,
        end_time_ns=end_ns,
        step_count=len(steps),
        steps=steps,
    )

    # ---- Step 4: Build summary ----
    gen_summary = _build_success_result(
        timeline=timeline,
        validation_summary=validation_summary,
        catalog=catalog,
        config=config,
    )

    return timeline, gen_summary
