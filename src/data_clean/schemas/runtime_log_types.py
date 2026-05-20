"""Structured log types for Runtime MVP run_log.json."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from .runtime_enums import RunStatus, SceneName
from .runtime_results import PipelineResult, RuntimeErrorRef, SceneResult


class RuntimeLogEventType(str, Enum):
    """Controlled event types for structured log entries."""

    RUNTIME_STEP = "runtime_step"
    DISPATCH_EVENT = "dispatch_event"
    SCENE_RESULT = "scene_result"
    PIPELINE_RESULT = "pipeline_result"
    ERROR = "error"


@dataclass
class RuntimeLogEvent:
    """Single structured log event written to run_log.json."""

    event_id: str
    run_id: str
    event_type: RuntimeLogEventType
    status: RunStatus
    created_at: datetime
    step_name: str = ""
    scene_name: SceneName | None = None
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)
    error: RuntimeErrorRef | None = None

    def __post_init__(self) -> None:
        if not self.event_id:
            raise ValueError("event_id must be non-empty")
        if not self.run_id:
            raise ValueError("run_id must be non-empty")


@dataclass
class RunLogFile:
    """Structured log file content for a single Runtime run."""

    run_id: str
    run_dir: str
    status: RunStatus
    target_scenes: list[SceneName]
    events: list[RuntimeLogEvent] = field(default_factory=list)
    started_at: datetime | None = None
    finished_at: datetime | None = None
    config_snapshot_path: str = ""
    scene_results: list[SceneResult] = field(default_factory=list)
    pipeline_result: PipelineResult | None = None
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
    """Result of writing run_log.json."""

    run_id: str
    run_log_path: str
    status: RunStatus
    event_count: int
    written_at: datetime | None = None
    error: RuntimeErrorRef | None = None

    def __post_init__(self) -> None:
        if not self.run_id:
            raise ValueError("run_id must be non-empty")
        if not self.run_log_path:
            raise ValueError("run_log_path must be non-empty")
