"""MCAP_A input inventory and validation service for Scene 3.

This is the input gatekeeper for Scene 3's time-axis alignment pipeline.
It reads a MCAP_A and its write summary, validates consistency, builds a
SourceTopicCatalog, checks baseline image topics, computes intersection
metadata, and produces a McapAInputValidationSummary.

Business rules:
- Hard fail: missing/unreadable MCAP_A, missing/unreadable/inconsistent summary,
  missing/out-of-order baseline topics, no baseline intersection.
- Warning only (non-blocking): missing/type-mismatch/out-of-order optional fields.
- Informational: unmapped topics are recorded, not treated as errors.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from repo.mcap_topic_catalog import TopicFact, extract_topic_facts
from schemas.alignment_config import Scene3AlignmentConfig, TargetFieldMapping
from schemas.alignment_input import (
    FieldAvailability,
    InputValidationStatus,
    McapAInputValidationSummary,
    SourceFieldEntry,
    SourceTopicCatalog,
    SourceTopicEntry,
    SummaryConsistencyStatus,
    TopicTimestampOrder,
)


def _classify_timestamp_order(timestamps: list[int]) -> TopicTimestampOrder:
    """Classify a list of timestamps into a TopicTimestampOrder enum.

    Args:
        timestamps: Sorted (ascending) timestamps from a topic.

    Returns:
        TopicTimestampOrder value.
    """
    if not timestamps:
        return TopicTimestampOrder.EMPTY

    # Check if timestamps are in non-decreasing order
    is_ordered = all(timestamps[i] <= timestamps[i + 1] for i in range(len(timestamps) - 1))
    if not is_ordered:
        return TopicTimestampOrder.OUT_OF_ORDER

    # All timestamps are non-decreasing - check for duplicate-only
    if len(timestamps) > 1 and all(t == timestamps[0] for t in timestamps):
        return TopicTimestampOrder.DUPLICATE_ONLY

    return TopicTimestampOrder.ORDERED


def _build_source_topic_entry(fact: TopicFact, baseline_topics: set[str]) -> SourceTopicEntry:
    """Build a SourceTopicEntry from a TopicFact."""
    return SourceTopicEntry(
        topic=fact.topic,
        message_type=fact.message_type,
        sample_count=fact.sample_count,
        timestamp_order=_classify_timestamp_order(fact.timestamps),
        start_time_ns=fact.timestamps[0] if fact.timestamps else None,
        end_time_ns=fact.timestamps[-1] if fact.timestamps else None,
        is_baseline_topic=fact.topic in baseline_topics,
    )


def _build_source_field_entry(
    field: TargetFieldMapping,
    topic_facts: dict[str, TopicFact],
    baseline_topics: set[str],
) -> SourceFieldEntry:
    """Build a SourceFieldEntry by cross-referencing a field mapping with topic facts."""
    fact = topic_facts.get(field.source_topic)

    if fact is None:
        return SourceFieldEntry(
            field_name=field.field_name,
            source_topic=field.source_topic,
            expected_message_type=field.message_type,
            modality=field.modality.value if hasattr(field.modality, "value") else str(field.modality),
            availability=FieldAvailability.MISSING_TOPIC,
            timestamp_order=TopicTimestampOrder.EMPTY,
            actual_message_type=None,
            required_for_timeline=field.required_for_timeline,
            sample_count=0,
            blocking=field.source_topic in baseline_topics,
            notes=[f"Topic {field.source_topic} not found in MCAP_A"],
        )

    # Check message type match
    actual_type = fact.message_type
    type_match = actual_type == field.message_type
    if not type_match:
        return SourceFieldEntry(
            field_name=field.field_name,
            source_topic=field.source_topic,
            expected_message_type=field.message_type,
            modality=field.modality.value if hasattr(field.modality, "value") else str(field.modality),
            availability=FieldAvailability.TYPE_MISMATCH,
            timestamp_order=_classify_timestamp_order(fact.timestamps),
            actual_message_type=actual_type,
            required_for_timeline=field.required_for_timeline,
            sample_count=fact.sample_count,
            blocking=field.source_topic in baseline_topics,
            notes=[f"Expected {field.message_type}, got {actual_type}"],
        )

    # Check timestamp order
    timestamp_order = _classify_timestamp_order(fact.timestamps)
    if timestamp_order == TopicTimestampOrder.OUT_OF_ORDER:
        return SourceFieldEntry(
            field_name=field.field_name,
            source_topic=field.source_topic,
            expected_message_type=field.message_type,
            modality=field.modality.value if hasattr(field.modality, "value") else str(field.modality),
            availability=FieldAvailability.TIMESTAMP_UNUSABLE,
            timestamp_order=timestamp_order,
            actual_message_type=actual_type,
            required_for_timeline=field.required_for_timeline,
            sample_count=fact.sample_count,
            start_time_ns=fact.timestamps[0] if fact.timestamps else None,
            end_time_ns=fact.timestamps[-1] if fact.timestamps else None,
            blocking=field.source_topic in baseline_topics,
            notes=["Timestamps are out of order"],
        )

    if timestamp_order == TopicTimestampOrder.EMPTY:
        return SourceFieldEntry(
            field_name=field.field_name,
            source_topic=field.source_topic,
            expected_message_type=field.message_type,
            modality=field.modality.value if hasattr(field.modality, "value") else str(field.modality),
            availability=FieldAvailability.EMPTY_TOPIC,
            timestamp_order=timestamp_order,
            actual_message_type=actual_type,
            required_for_timeline=field.required_for_timeline,
            sample_count=0,
            blocking=field.source_topic in baseline_topics,
            notes=["Topic has no messages"],
        )

    return SourceFieldEntry(
        field_name=field.field_name,
        source_topic=field.source_topic,
        expected_message_type=field.message_type,
        modality=field.modality.value if hasattr(field.modality, "value") else str(field.modality),
        availability=FieldAvailability.AVAILABLE,
        timestamp_order=timestamp_order,
        actual_message_type=actual_type,
        required_for_timeline=field.required_for_timeline,
        sample_count=fact.sample_count,
        start_time_ns=fact.timestamps[0] if fact.timestamps else None,
        end_time_ns=fact.timestamps[-1] if fact.timestamps else None,
    )


def _compute_baseline_intersection(
    topic_facts: dict[str, TopicFact],
    baseline_topics: list[str],
) -> tuple[int | None, int | None, bool]:
    """Compute the overlapping time range for baseline image topics.

    Args:
        topic_facts: Mapping of topic name to TopicFact.
        baseline_topics: Ordered list of baseline image topic names (e.g., [left, right]).

    Returns:
        Tuple of (intersection_start_ns, intersection_end_ns, has_intersection).
        Returns (None, None, False) if either topic is missing or has no timestamps.
    """
    ranges: list[tuple[int, int]] = []
    for topic in baseline_topics:
        fact = topic_facts.get(topic)
        if fact is None or not fact.timestamps:
            return None, None, False
        ranges.append((fact.timestamps[0], fact.timestamps[-1]))

    if not ranges:
        return None, None, False

    intersection_start = max(r[0] for r in ranges)
    intersection_end = min(r[1] for r in ranges)

    if intersection_start > intersection_end:
        return None, None, False

    return intersection_start, intersection_end, True


def validate_mcap_a_input(
    mcap_path: str,
    summary_path: str,
    config: Scene3AlignmentConfig,
    field_mappings: list[TargetFieldMapping],
) -> tuple[SourceTopicCatalog, McapAInputValidationSummary, int | None, int | None, list[str]]:
    """Validate MCAP_A input and produce catalog + validation summary.

    This is the main entry point for the MCAP_A input inventory and validation
    service. It orchestrates file checks, summary validation, topic cataloging,
    field mapping, baseline analysis, and warning collection.

    Args:
        mcap_path: Path to the MCAP_A file.
        summary_path: Path to the mcap_a_write_summary.json file.
        config: Scene3 alignment configuration.
        field_mappings: List of target field mappings.

    Returns:
        Tuple of (SourceTopicCatalog, McapAInputValidationSummary,
                  baseline_intersection_start_ns, baseline_intersection_end_ns,
                  optional_field_warnings).
    """
    hard_fail_reasons: list[str] = []
    warnings: list[str] = []
    now_str = datetime.now(timezone.utc).isoformat()

    # ---- Step 1: Check MCAP_A file exists ----
    mcap_path_obj = Path(mcap_path)
    mcap_readable = mcap_path_obj.exists() and mcap_path_obj.is_file()
    if not mcap_readable:
        hard_fail_reasons.append("missing_mcap_a")

    # ---- Step 2: Check summary file exists and parse ----
    summary_path_obj = Path(summary_path)
    summary_data: dict | None = None
    summary_present = summary_path_obj.exists() and summary_path_obj.is_file()

    if not summary_present:
        hard_fail_reasons.append("missing_mcap_a_write_summary")
        summary_consistency = SummaryConsistencyStatus.MISSING
    else:
        try:
            summary_data = json.loads(summary_path_obj.read_text(encoding="utf-8"))
            summary_consistency = SummaryConsistencyStatus.CONSISTENT
        except (json.JSONDecodeError, UnicodeDecodeError, OSError):
            hard_fail_reasons.append("unreadable_mcap_a_write_summary")
            summary_consistency = SummaryConsistencyStatus.UNREADABLE
            summary_data = None

    # ---- Step 3: Validate summary consistency ----
    if summary_data is not None:
        if summary_data.get("status") != "completed":
            hard_fail_reasons.append("summary_not_completed")
            summary_consistency = SummaryConsistencyStatus.STATUS_FAILED
        elif summary_data.get("output_mcap_a") != mcap_path:
            hard_fail_reasons.append("summary_output_path_mismatch")
            summary_consistency = SummaryConsistencyStatus.PATH_MISMATCH
        elif not _check_summary_policy(summary_data):
            hard_fail_reasons.append("summary_policy_mismatch")
            summary_consistency = SummaryConsistencyStatus.POLICY_MISMATCH

    # ---- Step 4: Read topic catalog from MCAP_A ----
    topic_facts: list[TopicFact] = []
    topic_fact_map: dict[str, TopicFact] = {}
    if mcap_readable:
        try:
            topic_facts = extract_topic_facts(mcap_path)
            topic_fact_map = {f.topic: f for f in topic_facts}
        except (FileNotFoundError, ValueError):
            if "missing_mcap_a" not in hard_fail_reasons:
                hard_fail_reasons.append("missing_mcap_a")
            mcap_readable = False

    # ---- Step 5: Build topic entries ----
    baseline_set = set(config.baseline_image_topics)
    topic_entries = [_build_source_topic_entry(f, baseline_set) for f in topic_facts]

    # ---- Step 6: Build field entries ----
    field_entries = [
        _build_source_field_entry(fm, topic_fact_map, baseline_set)
        for fm in field_mappings
    ]

    # ---- Step 7: Identify unmapped topics ----
    mapped_topics = {fm.source_topic for fm in field_mappings}
    unmapped_topics = sorted(
        t for t in topic_fact_map if t not in mapped_topics
    )

    # ---- Step 8: Check baseline topics ----
    baseline_topics_present = all(t in topic_fact_map for t in config.baseline_image_topics)
    if not baseline_topics_present:
        missing = [t for t in config.baseline_image_topics if t not in topic_fact_map]
        hard_fail_reasons.append("missing_baseline_topic")
        for t in missing:
            warnings.append(f"missing_baseline_topic:{t}")

    # Check baseline topic timestamp order
    baseline_topics_ordered = True
    if baseline_topics_present:
        for bt in config.baseline_image_topics:
            fact = topic_fact_map.get(bt)
            if fact and _classify_timestamp_order(fact.timestamps) in (
                TopicTimestampOrder.OUT_OF_ORDER, TopicTimestampOrder.EMPTY
            ):
                baseline_topics_ordered = False
                hard_fail_reasons.append("baseline_topic_out_of_order")
                break

    # ---- Step 9: Compute baseline intersection ----
    intersection_start, intersection_end, has_intersection = _compute_baseline_intersection(
        topic_fact_map, config.baseline_image_topics
    )
    if baseline_topics_present and baseline_topics_ordered and not has_intersection:
        hard_fail_reasons.append("missing_baseline_intersection")

    # ---- Step 10: Collect optional field warnings ----
    optional_field_warnings: list[str] = []
    baseline_set_names = set()
    for fm in field_mappings:
        if fm.required_for_timeline:
            baseline_set_names.add(fm.field_name)

    for entry in field_entries:
        if entry.field_name in baseline_set_names:
            continue  # baseline fields handled separately
        if entry.availability == FieldAvailability.MISSING_TOPIC:
            optional_field_warnings.append(f"optional_field_missing:{entry.field_name}")
        elif entry.availability == FieldAvailability.TYPE_MISMATCH:
            optional_field_warnings.append(f"optional_field_type_mismatch:{entry.field_name}")
        elif entry.availability == FieldAvailability.TIMESTAMP_UNUSABLE:
            optional_field_warnings.append(f"optional_field_timestamp_unusable:{entry.field_name}")
        elif entry.availability == FieldAvailability.EMPTY_TOPIC:
            optional_field_warnings.append(f"optional_field_empty:{entry.field_name}")
        # If available, no warning needed

    # ---- Step 11: Determine overall status ----
    status = InputValidationStatus.NOT_CONSUMABLE if hard_fail_reasons else InputValidationStatus.CONSUMABLE

    # ---- Step 12: Build SourceTopicCatalog ----
    catalog = SourceTopicCatalog(
        source_mcap_a=mcap_path,
        summary_ref=summary_path,
        config_ref="scene3_alignment",
        topic_entries=topic_entries,
        field_entries=field_entries,
        unmapped_topics=unmapped_topics,
        baseline_intersection_start_ns=intersection_start,
        baseline_intersection_end_ns=intersection_end,
        has_baseline_intersection=has_intersection,
        created_at=now_str,
    )

    # ---- Step 13: Build McapAInputValidationSummary ----
    validation_summary = McapAInputValidationSummary(
        input_mcap_a=mcap_path,
        mcap_a_write_summary=summary_path,
        config_ref="scene3_alignment",
        catalog_ref="source_topic_catalog",
        status=status,
        summary_consistency_status=summary_consistency,
        hard_fail_reasons=hard_fail_reasons,
        warnings=warnings,
        baseline_topics_present=baseline_topics_present,
        baseline_topics_ordered=baseline_topics_ordered,
        has_baseline_intersection=has_intersection,
        baseline_intersection_start_ns=intersection_start,
        baseline_intersection_end_ns=intersection_end,
        required_field_failures=[r for r in hard_fail_reasons if r.startswith("missing_baseline")],
        optional_field_warnings=optional_field_warnings,
        unmapped_topic_count=len(unmapped_topics),
        created_at=now_str,
    )

    return catalog, validation_summary, intersection_start, intersection_end, optional_field_warnings


def _check_summary_policy(summary_data: dict) -> bool:
    """Check that summary timestamp/topic policies match MCAP_A contract."""
    timestamp_policy = summary_data.get("timestamp_policy")
    topic_policy = summary_data.get("topic_policy")
    if timestamp_policy != "preserve_original":
        return False
    if topic_policy != "preserve_cleaned_topics":
        return False
    return True
