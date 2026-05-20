"""Input artifact precheck types: requirement, check result, and summary."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .runtime_results import RuntimeErrorRef

from .runtime_enums import RunMode, RunStatus, SceneName


@dataclass
class InputArtifactRequirement:
    """Requirement for a single input artifact that a scene needs before execution."""

    scene_name: SceneName
    artifact_role: str
    path_config_key: str
    required_kind: str
    required_for_modes: list[RunMode] = field(default_factory=list)
    allow_manual_override: bool = False
    description: str = ""

    def __post_init__(self) -> None:
        if not self.artifact_role:
            raise ValueError("artifact_role must be non-empty")
        if not self.path_config_key:
            raise ValueError("path_config_key must be non-empty")
        if self.required_kind not in ("file", "directory"):
            raise ValueError(
                f"required_kind must be 'file' or 'directory', got {self.required_kind!r}"
            )


@dataclass
class InputArtifactCheckResult:
    """Result of checking a single input artifact requirement."""

    requirement: InputArtifactRequirement
    status: RunStatus
    exists: bool
    readable: bool
    kind_matches: bool
    candidate_path: str = ""
    error: RuntimeErrorRef | None = None

    def __post_init__(self) -> None:
        if self.status == RunStatus.SUCCEEDED and not self.candidate_path:
            raise ValueError("candidate_path is empty but status is succeeded")


@dataclass
class InputArtifactPrecheckSummary:
    """Aggregated summary of all input artifact checks for a single scene."""

    scene_name: SceneName
    results: list[InputArtifactCheckResult]
    status: RunStatus
    blocking_errors: list[RuntimeErrorRef] = field(default_factory=list)
    checked_at: datetime | None = None
