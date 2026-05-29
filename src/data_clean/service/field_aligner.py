"""Image and gripper nearest neighbor field aligner for Scene 3.

This module implements the nearest-neighbor alignment strategy for image
and gripper modality fields. Each step in a StepTimeline is aligned to the
closest sample in time from the corresponding source topic.

Business rules (from L2 multi-strategy field aligner):
- Image: nearest neighbor only, no interpolation. message_ref only, no payload.
- Gripper: nearest neighbor directly by step_time_ns, independent of image timing.
  Derived value (gripper_width) may be inlined.
- Missing/empty topic → status=unavailable (image) or missing_time (gripper).
- Sample beyond max_dt_ms → status=timeout.
"""

from __future__ import annotations

from typing import Any

from schemas.alignment_config import AlignmentModality, TargetFieldMapping
from schemas.alignment_input import FieldAvailability, SourceTopicCatalog
from schemas.field_alignment import FieldAlignmentResult
from schemas.step_timeline import FieldAlignmentStatus, StepTimeline

# Field sample tuple: (timestamp_ns, message_ref, derived_value)
# - image: (t, "mcap://...", None)
# - gripper: (t, "mcap://...", {"gripper_width": 0.5})
SampleTuple = tuple[int, str, Any | None]


def _find_field_entry(
    catalog: SourceTopicCatalog, field_name: str
) -> dict | None:
    """Look up a field entry by field_name from the catalog.

    Returns the field entry dict-like object or None if not found.
    """
    for entry in catalog.field_entries:
        if entry.field_name == field_name:
            # Return as dict-like dataclass
            return entry  # type: ignore[return-value]
    return None


def _compute_dt_ms(step_time_ns: int, sample_time_ns: int) -> float:
    """Compute absolute time difference in milliseconds."""
    return abs(step_time_ns - sample_time_ns) / 1_000_000.0


def _find_nearest_sample(
    step_time_ns: int,
    samples: list[SampleTuple],
) -> SampleTuple | None:
    """Find the sample with the smallest time difference to step_time_ns.

    Args:
        step_time_ns: Target step timestamp in nanoseconds.
        samples: List of (timestamp_ns, message_ref, derived_value) tuples.

    Returns:
        The nearest sample tuple, or None if samples is empty.
    """
    if not samples:
        return None

    nearest = min(samples, key=lambda s: abs(s[0] - step_time_ns))
    return nearest


def _align_single_field(
    step_entry: StepTimeline,
    field_mapping: TargetFieldMapping,
    catalog: SourceTopicCatalog,
    samples: list[SampleTuple],
) -> FieldAlignmentResult:
    """Align a single field to a single step using nearest neighbor.

    This is used for each step entry - we iterate over step entries
    and fields in the main function.

    Args:
        step_entry: The single StepTimelineEntry to align.
        field_mapping: Target field configuration.
        catalog: Source topic catalog with field availability.
        samples: Source samples for this field.

    Returns:
        FieldAlignmentResult for this step-field combination.
    """
    pass


def align_nearest_fields(
    timeline: StepTimeline,
    catalog: SourceTopicCatalog,
    field_mappings: list[TargetFieldMapping],
    field_samples: dict[str, list[SampleTuple]],
) -> list[FieldAlignmentResult]:
    """Align image and gripper fields to step timeline via nearest neighbor.

    For each step in the timeline and each image/gripper field mapping:
    1. Check field availability from catalog → unavailable if not available.
    2. Find nearest sample by timestamp → aligned if within max_dt_ms.
    3. Images: only message_ref, no derived_value.
    4. Gripper: derived_value contains gripper_width from the sample.

    Non-image/gripper fields in field_mappings are silently skipped
    (they will be handled by other alignment strategies).

    Args:
        timeline: Step timeline with step entries to align to.
        catalog: Source topic catalog with field availability info.
        field_mappings: List of target field mappings (image+gripper only).
        field_samples: Dict mapping field_name -> list of sample tuples.
            Each sample tuple is (timestamp_ns, message_ref, derived_value).

    Returns:
        List of FieldAlignmentResult, one per step per field.
        Results are ordered by step_index then field_name.
    """
    results: list[FieldAlignmentResult] = []

    # Build lookup: field_name -> field entry from catalog
    field_entry_map: dict[str, Any] = {}
    for entry in catalog.field_entries:
        field_entry_map[entry.field_name] = entry

    # Filter to only image and gripper fields
    relevant_mappings = [
        fm
        for fm in field_mappings
        if fm.modality
        in (AlignmentModality.IMAGE, AlignmentModality.GRIPPER)
    ]

    for step_entry in timeline.steps:
        for fm in relevant_mappings:
            field_name = fm.field_name
            field_entry = field_entry_map.get(field_name)

            # Step 1: Check field availability
            if field_entry is not None and field_entry.availability != FieldAvailability.AVAILABLE:
                avail_reason = field_entry.availability.value
                # Image missing topic → unavailable
                # Gripper empty topic → missing_time (per L3 spec)
                if fm.modality == AlignmentModality.GRIPPER and field_entry.availability in (
                    FieldAvailability.EMPTY_TOPIC,
                    FieldAvailability.MISSING_TOPIC,
                ):
                    status = FieldAlignmentStatus.missing_time.value
                else:
                    status = FieldAlignmentStatus.unavailable.value
                results.append(
                    FieldAlignmentResult(
                        step_index=step_entry.step_index,
                        step_time_ns=step_entry.step_time_ns,
                        field_name=field_name,
                        status=status,
                        alignment_method="nearest_neighbor",
                        source_topic=fm.source_topic,
                        output_topic=fm.output_topic,
                        notes=[f"field_availability: {avail_reason}"],
                    )
                )
                continue

            # Step 2: Get samples for this field
            samples = field_samples.get(field_name, [])

            # Step 3: Find nearest sample
            nearest = _find_nearest_sample(step_entry.step_time_ns, samples)

            if nearest is None:
                # No samples at all
                field_entry_avail = (
                    field_entry.availability if field_entry else None
                )
                if (
                    fm.modality == AlignmentModality.GRIPPER
                    or field_entry_avail == FieldAvailability.EMPTY_TOPIC
                ):
                    status = FieldAlignmentStatus.missing_time.value
                else:
                    status = FieldAlignmentStatus.unavailable.value
                results.append(
                    FieldAlignmentResult(
                        step_index=step_entry.step_index,
                        step_time_ns=step_entry.step_time_ns,
                        field_name=field_name,
                        status=status,
                        alignment_method="nearest_neighbor",
                        source_topic=fm.source_topic,
                        output_topic=fm.output_topic,
                        notes=["no_samples_available"],
                    )
                )
                continue

            sample_time_ns, message_ref, derived_value = nearest

            # Step 4: Check timeout (max_dt_ms)
            dt_ms = _compute_dt_ms(step_entry.step_time_ns, sample_time_ns)
            if fm.max_dt_ms is not None and dt_ms > fm.max_dt_ms:
                results.append(
                    FieldAlignmentResult(
                        step_index=step_entry.step_index,
                        step_time_ns=step_entry.step_time_ns,
                        field_name=field_name,
                        status=FieldAlignmentStatus.timeout.value,
                        alignment_method="nearest_neighbor",
                        source_topic=fm.source_topic,
                        output_topic=fm.output_topic,
                        source_time_ns=sample_time_ns,
                        dt_ms=dt_ms,
                        message_ref=message_ref,
                    )
                )
                continue

            # Step 5: Aligned
            # Image → no derived_value; Gripper → keep derived_value
            result_derived = None
            if fm.modality == AlignmentModality.GRIPPER:
                result_derived = derived_value

            results.append(
                FieldAlignmentResult(
                    step_index=step_entry.step_index,
                    step_time_ns=step_entry.step_time_ns,
                    field_name=field_name,
                    status=FieldAlignmentStatus.aligned.value,
                    alignment_method="nearest_neighbor",
                    source_topic=fm.source_topic,
                    output_topic=fm.output_topic,
                    source_time_ns=sample_time_ns,
                    dt_ms=dt_ms,
                    message_ref=message_ref,
                    derived_value=result_derived,
                )
            )

    return results
