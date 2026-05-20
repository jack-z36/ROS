"""Structured log types: log file, log event, write result, and controlled event types."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from .runtime_enums import RunStatus, SceneName
from .runtime_results import RuntimeErrorRef


class RuntimeLogEventType(str, Enum):
    """Controlled event types for Runtime structured log entries."""

    RUNTIME_STEP = "runtime_step"
    DISPATCH_EVENT = "dispatch_event"
    SCENE_RESULT = "scene_result"
    PIPELINE_RESULT = "pipeline_result"
    ERROR = "error"
    RUN_STARTED = "run_started"
    RUN_FINISHED = "run_finished"


@dataclass
class RuntimeLogEvent:
    """A single structured event in the Runtime log."""

    run_id: str
    event_type: RuntimeLogEventType
    status: RunStatus
    event_id: str
    scene_name: SceneName | None = None
    message: str = ""
    error: RuntimeErrorRef | None = None
    payload: dict[str, Any] = field(default_factory=dict)
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.run_id:
            raise ValueError("run_id must be non-empty")
        if not self.event_id:
            raise ValueError("event_id must be non-empty")
        if self.status == RunStatus.FAILED and self.error is None:
            raise ValueError(
                "error must be provided when status is FAILED"
            )


@dataclass
class RunLogFile:
    """Structured log file written as run_log.json for a single Runtime run."""

    run_id: str
    run_dir: str
    status: RunStatus
    target_scenes: list[SceneName]
    events: list[RuntimeLogEvent] = field(default_factory=list)
    started_at: datetime | None = None
    finished_at: datetime | None = None
    config_snapshot_path: str | None = None
    scene_results: list[Any] = field(default_factory=list)
    pipeline_result: Any | None = None
    errors: list[RuntimeErrorRef] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.run_id:
            raise ValueError("run_id must be non-empty")
        if not self.run_dir:
            raise ValueError("run_dir must be non-empty")
        if not self.target_scenes:
            raise ValueError("target_scenes must be non-empty")


@dataclass
class RuntimeLogWriteResult:
    """Result of writing the structured log file."""

    run_id: str
    run_log_path: str
    status: RunStatus
    event_count: int = 0
    written_at: datetime | None = None
    error: RuntimeErrorRef | None = None

    @property
    def log_path(self) -> str:
        """Alias for run_log_path for backward compatibility."""
        return self.run_log_path

    @property
    def success(self) -> bool:
        """Alias: True if status is SUCCEEDED."""
        return self.status == RunStatus.SUCCEEDED

    def __post_init__(self) -> None:
        if not self.run_id:
            raise ValueError("run_id must be non-empty")
        if self.status == RunStatus.FAILED and self.error is None:
            raise ValueError(
                "error must be provided when status is FAILED"
            )
