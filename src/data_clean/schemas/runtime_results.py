"""Runtime result and error reference types for the data cleaning pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .runtime_enums import RunStatus, SceneName


@dataclass
class RuntimeErrorRef:
    """Structured error reference for Runtime failures."""

    error_code: str
    step_name: str
    message: str
    scene_name: SceneName | None = None
    details: dict[str, Any] = field(default_factory=dict)
    suggested_next_action: str = ""

    def __post_init__(self) -> None:
        if not self.error_code:
            raise ValueError("error_code must be non-empty")
        if not self.step_name:
            raise ValueError("step_name must be non-empty")
        if not self.message:
            raise ValueError("message must be non-empty")


@dataclass
class RuntimeStepRecord:
    """Structured record for a single Runtime execution step."""

    step_name: str
    status: RunStatus
    started_at: datetime
    scene_name: SceneName | None = None
    finished_at: datetime | None = None
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.step_name:
            raise ValueError("step_name must be non-empty")


@dataclass
class SceneResult:
    """Result summary for a single scene execution."""

    scene_name: SceneName
    status: RunStatus
    input_paths: dict[str, str] = field(default_factory=dict)
    output_paths: dict[str, str] = field(default_factory=dict)
    started_at: datetime | None = None
    finished_at: datetime | None = None
    duration_ms: int | None = None
    error: RuntimeErrorRef | None = None


MANIFEST_SCHEMA_VERSION = "runtime_manifest.v1"


@dataclass
class ProcessingManifest:
    """Processing manifest written on the success path of a Runtime run."""

    schema_version: str
    run_id: str
    run_mode: str
    service_mode: str
    target_scenes: list[str]
    status: str
    config_snapshot_path: str
    run_log_path: str
    scene_results: list[dict[str, Any]]
    created_at: str
    input_artifacts: dict[str, Any] = field(default_factory=dict)
    output_artifacts: dict[str, Any] = field(default_factory=dict)
    tool_versions: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("schema_version must be non-empty")
        if not self.run_id:
            raise ValueError("run_id must be non-empty")
        if not self.run_mode:
            raise ValueError("run_mode must be non-empty")
        if not self.service_mode:
            raise ValueError("service_mode must be non-empty")
        if not self.target_scenes:
            raise ValueError("target_scenes must be non-empty")
        if not self.status:
            raise ValueError("status must be non-empty")
        if not self.config_snapshot_path:
            raise ValueError("config_snapshot_path must be non-empty")
        if not self.run_log_path:
            raise ValueError("run_log_path must be non-empty")
        if not self.created_at:
            raise ValueError("created_at must be non-empty")

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-compatible dict."""
        result: dict[str, Any] = {
            "schema_version": self.schema_version,
            "run_id": self.run_id,
            "run_mode": self.run_mode,
            "service_mode": self.service_mode,
            "target_scenes": self.target_scenes,
            "status": self.status,
            "config_snapshot_path": self.config_snapshot_path,
            "run_log_path": self.run_log_path,
            "scene_results": self.scene_results,
            "created_at": self.created_at,
        }
        if self.input_artifacts:
            result["input_artifacts"] = self.input_artifacts
        if self.output_artifacts:
            result["output_artifacts"] = self.output_artifacts
        if self.tool_versions:
            result["tool_versions"] = self.tool_versions
        if self.metadata:
            result["metadata"] = self.metadata
        return result


@dataclass
class PipelineResult:
    """Final result summary for a single or full-pipeline Runtime run."""

    run_id: str
    status: RunStatus
    scene_results: list[SceneResult] = field(default_factory=list)
    run_dir: str = ""
    run_log_path: str = ""
    manifest_path: str = ""
    error_summary_path: str = ""

    def __post_init__(self) -> None:
        if not self.run_id:
            raise ValueError("run_id must be non-empty")
