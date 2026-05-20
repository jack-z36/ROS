"""Fake service plan and result types for the data cleaning pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .runtime_enums import FakeServiceBehavior, RunStatus, SceneName, ServiceMode
from .runtime_results import RuntimeErrorRef


@dataclass
class FakeServicePlan:
    """Execution plan describing what a fake service should simulate."""

    scene_name: SceneName
    service_mode: ServiceMode
    behavior: FakeServiceBehavior
    declared_outputs: dict[str, str]
    input_summary: dict[str, Any] | None = None
    message: str | None = None

    def __post_init__(self) -> None:
        if self.service_mode != ServiceMode.FAKE:
            raise ValueError(
                f"service_mode must be FAKE, got {self.service_mode.value!r}"
            )


@dataclass
class FakeServiceResult:
    """Result returned by a fake service execution."""

    scene_name: SceneName
    behavior: FakeServiceBehavior
    status: RunStatus
    output_paths: dict[str, str]
    started_at: datetime
    finished_at: datetime
    duration_ms: int
    input_summary: dict[str, Any] | None = None
    error: RuntimeErrorRef | None = None

    def __post_init__(self) -> None:
        if self.finished_at < self.started_at:
            raise ValueError(
                f"finished_at ({self.finished_at}) must not be earlier than "
                f"started_at ({self.started_at})"
            )
        if self.status == RunStatus.SUCCEEDED and self.error is not None:
            raise ValueError(
                "error must be None when status is SUCCEEDED"
            )
        if self.status == RunStatus.FAILED and self.error is None:
            raise ValueError(
                "error must be provided when status is FAILED"
            )
