"""Scene 3 MCAP_A input catalog and validation summary types."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class TopicTimestampOrder(str, Enum):
    """Timestamp ordering status for a topic."""

    ORDERED = "ordered"
    DUPLICATE_ONLY = "duplicate_only"
    OUT_OF_ORDER = "out_of_order"
    EMPTY = "empty"


class FieldAvailability(str, Enum):
    """Availability status of a field source."""

    AVAILABLE = "available"
    MISSING_TOPIC = "missing_topic"
    TYPE_MISMATCH = "type_mismatch"
    TIMESTAMP_UNUSABLE = "timestamp_unusable"
    EMPTY_TOPIC = "empty_topic"


class InputValidationStatus(str, Enum):
    """Overall MCAP_A input consumption status."""

    CONSUMABLE = "consumable"
    NOT_CONSUMABLE = "not_consumable"


class SummaryConsistencyStatus(str, Enum):
    """Consistency status of the MCAP_A write summary."""

    CONSISTENT = "consistent"
    MISSING = "missing"
    UNREADABLE = "unreadable"
    STATUS_FAILED = "status_failed"
    PATH_MISMATCH = "path_mismatch"
    POLICY_MISMATCH = "policy_mismatch"


@dataclass
class SourceTopicEntry:
    """A single topic entry within SourceTopicCatalog."""

    topic: str
    message_type: str
    sample_count: int
    timestamp_order: TopicTimestampOrder
    start_time_ns: int | None = None
    end_time_ns: int | None = None
    matched_field_names: list[str] = field(default_factory=list)
    is_baseline_topic: bool = False
    is_unmapped_topic: bool = False


@dataclass
class SourceFieldEntry:
    """A single field mapping entry within SourceTopicCatalog."""

    field_name: str
    source_topic: str
    expected_message_type: str
    modality: str
    availability: FieldAvailability
    timestamp_order: TopicTimestampOrder
    actual_message_type: str | None = None
    required_for_timeline: bool = False
    sample_count: int = 0
    start_time_ns: int | None = None
    end_time_ns: int | None = None
    blocking: bool = False
    notes: list[str] = field(default_factory=list)


@dataclass
class SourceTopicCatalog:
    """Structured catalog of MCAP_A topic facts and field mapping results."""

    source_mcap_a: str
    summary_ref: str
    config_ref: str
    topic_entries: list[SourceTopicEntry] = field(default_factory=list)
    field_entries: list[SourceFieldEntry] = field(default_factory=list)
    unmapped_topics: list[str] = field(default_factory=list)
    baseline_topic_status: dict | None = None
    baseline_intersection_start_ns: int | None = None
    baseline_intersection_end_ns: int | None = None
    has_baseline_intersection: bool = False
    created_at: str | None = None


@dataclass
class McapAInputValidationSummary:
    """Validation summary for a single MCAP_A input check."""

    input_mcap_a: str
    mcap_a_write_summary: str
    config_ref: str
    catalog_ref: str
    status: InputValidationStatus
    summary_consistency_status: SummaryConsistencyStatus
    hard_fail_reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    baseline_topics_present: bool = False
    baseline_topics_ordered: bool = False
    has_baseline_intersection: bool = False
    baseline_intersection_start_ns: int | None = None
    baseline_intersection_end_ns: int | None = None
    required_field_failures: list[str] = field(default_factory=list)
    optional_field_warnings: list[str] = field(default_factory=list)
    unmapped_topic_count: int = 0
    created_at: str | None = None
    run_id: str | None = None

    def __post_init__(self) -> None:
        """Validate constraint: consumable status requires empty hard_fail_reasons."""
        if self.status == InputValidationStatus.CONSUMABLE:
            if self.hard_fail_reasons:
                raise ValueError(
                    f"status=consumable requires empty hard_fail_reasons, "
                    f"got {self.hard_fail_reasons}"
                )
