"""Manifest, error summary, and run result types for Runtime end-state tracing."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from .runtime_enums import RunMode, RunStatus, SceneName, ServiceMode
from .runtime_results import RuntimeErrorRef, SceneResult


class RuntimeResultSchemaVersion(str, Enum):
    """Controlled schema version strings for Runtime result files."""

    MANIFEST_V1 = "runtime_manifest.v1"
    ERROR_SUMMARY_V1 = "runtime_error_summary.v1"
    RUN_RESULT_V1 = "runtime_run_result.v1"


@dataclass
class ProcessingManifest:
    """Success-path processing manifest written as processing_manifest.json."""

    schema_version: RuntimeResultSchemaVersion
    run_id: str
    run_mode: RunMode
    service_mode: ServiceMode
    target_scenes: list[SceneName]
    status: RunStatus
    config_snapshot_path: str
    run_log_path: str
    scene_results: list[SceneResult]
    created_at: datetime
    input_artifacts: dict[str, Any] = field(default_factory=dict)
    output_artifacts: dict[str, Any] = field(default_factory=dict)
    tool_versions: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.run_id:
            raise ValueError("run_id must be non-empty")
        if not self.config_snapshot_path:
            raise ValueError("config_snapshot_path must be non-empty")
        if not self.run_log_path:
            raise ValueError("run_log_path must be non-empty")
        if self.scene_results is None:
            raise ValueError("scene_results must be a list")


@dataclass
class ErrorSummary:
    """Failure-path error summary written as error_summary.json."""

    schema_version: RuntimeResultSchemaVersion
    run_id: str
    status: RunStatus
    failed_step: str
    error: RuntimeErrorRef
    run_log_path: str
    message: str
    created_at: datetime
    failed_scene: SceneName | None = None
    config_snapshot_path: str = ""
    scene_results: list[SceneResult] = field(default_factory=list)
    suggested_next_action: str = ""

    def __post_init__(self) -> None:
        if not self.run_id:
            raise ValueError("run_id must be non-empty")
        if not self.failed_step:
            raise ValueError("failed_step must be non-empty")
        if self.error is None:
            raise ValueError("error must be provided")
        if not self.message:
            raise ValueError("message must be non-empty")
        if not self.run_log_path:
            raise ValueError("run_log_path must be non-empty")


@dataclass
class RunResultIndex:
    """Unified run result index written as run_result.json."""

    schema_version: RuntimeResultSchemaVersion
    run_id: str
    status: RunStatus
    run_dir: str
    run_log_path: str
    scene_results: list[dict[str, Any]]
    created_at: datetime
    manifest_path: str = ""
    error_summary_path: str = ""

    def __post_init__(self) -> None:
        if not self.run_id:
            raise ValueError("run_id must be non-empty")
        if not self.run_dir:
            raise ValueError("run_dir must be non-empty")
        if not self.run_log_path:
            raise ValueError("run_log_path must be non-empty")
        if self.scene_results is None:
            raise ValueError("scene_results must be a list")
        if self.status == RunStatus.SUCCEEDED and not self.manifest_path:
            raise ValueError("manifest_path must be set for succeeded status")
        if self.status == RunStatus.FAILED and not self.error_summary_path:
            raise ValueError("error_summary_path must be set for failed status")

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-compatible dict."""
        result: dict[str, Any] = {
            "schema_version": self.schema_version.value,
            "run_id": self.run_id,
            "status": self.status.value if hasattr(self.status, "value") else str(self.status),
            "run_dir": self.run_dir,
            "run_log_path": self.run_log_path,
            "scene_results": self.scene_results,
            "created_at": self.created_at.isoformat(),
        }
        if self.manifest_path:
            result["manifest_path"] = self.manifest_path
        if self.error_summary_path:
            result["error_summary_path"] = self.error_summary_path
        return result
