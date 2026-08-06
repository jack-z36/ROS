from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from .reliability import SignalSampleRef


McapAWriterOperationKind = Literal["copy", "replace"]


@dataclass(frozen=True)
class MCAP_A_MessageReplacement:
    sample_ref: SignalSampleRef
    replacement_unit: str
    value: Any


@dataclass
class MCAP_A_WriterConfig:
    output_path: str
    copy_original_topics: list[str] = field(default_factory=list)
    replace_topics: dict[str, str] = field(default_factory=dict)
    compression: str = "zstd"
    chunk_size: int = 8 * 1024 * 1024
    filename_policy: str = "derive_from_cleaned_stem"
    topic_policy: str = "preserve_cleaned_topics"
    strict_required_inputs: bool = True

    def __post_init__(self) -> None:
        if not self.output_path:
            raise ValueError("output_path is required")
        if self.chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        if self.filename_policy != "derive_from_cleaned_stem":
            raise ValueError("filename_policy must be derive_from_cleaned_stem")
        if self.topic_policy != "preserve_cleaned_topics":
            raise ValueError("topic_policy must be preserve_cleaned_topics")
        if not self.strict_required_inputs:
            raise ValueError("strict_required_inputs must be true")


@dataclass
class MCAP_A_WritePlan:
    source_mcap: str
    output_mcap: str
    operations: list[dict[str, Any]]
    timestamp_policy: str = "preserve_original"
    output_sequence_refs: dict[str, str] | list[Any] = field(default_factory=dict)
    run_id: str | None = None
    run_context: Any | None = None

    def __post_init__(self) -> None:
        if not self.source_mcap:
            raise ValueError("source_mcap is required")
        if not self.output_mcap:
            raise ValueError("output_mcap is required")
        if self.timestamp_policy != "preserve_original":
            raise ValueError("timestamp_policy must be preserve_original")
        for operation in self.operations:
            operation_kind = operation.get("operation")
            if operation_kind not in {"copy", "replace"}:
                raise ValueError("operations must be copy or replace operations")
            if operation_kind == "replace" and not operation.get("sequence_ref"):
                raise ValueError("replace operations must include sequence_ref")


@dataclass
class MCAP_A_OutputContract:
    topic_list: list[str]
    message_count: int
    start_time: int | float | None
    end_time: int | float | None
    checksum: str

    def __post_init__(self) -> None:
        if self.message_count < 0:
            raise ValueError("message_count must be non-negative")


@dataclass
class MCAP_A_WriterResult:
    plan: MCAP_A_WritePlan
    contract: MCAP_A_OutputContract
    success: bool
    error_log: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.success and self.error_log:
            raise ValueError("successful writer result must not include error_log entries")
        if not self.success and not self.error_log:
            raise ValueError("failed writer result must include error_log entries")
