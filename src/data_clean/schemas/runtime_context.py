"""Runtime context types for stage-2 data cleaning pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .run_directory_types import RunDirectory


class RunMode(str, Enum):
    """Runtime execution mode: dev/prod x single/pipeline."""

    DEV_SINGLE_SCENE = "dev_single_scene"
    DEV_FULL_PIPELINE = "dev_full_pipeline"
    PROD_SINGLE_SCENE = "prod_single_scene"
    PROD_FULL_PIPELINE = "prod_full_pipeline"


class ServiceMode(str, Enum):
    """Service invocation mode: fake or real."""

    FAKE = "fake"
    REAL = "real"


class SceneName(str, Enum):
    """Stage-2 business scene identifiers."""

    SCENE1 = "scene1"
    SCENE2 = "scene2"
    SCENE3 = "scene3"
    SCENE4 = "scene4"
    SCENE5 = "scene5"


class RunStatus(str, Enum):
    """Runtime lifecycle status."""

    CREATED = "created"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class RunContext:
    """Complete context snapshot for a single Runtime execution."""

    run_id: str
    run_mode: RunMode
    service_mode: ServiceMode = ServiceMode.FAKE
    target_scenes: list[SceneName] = field(default_factory=list)
    active_scene: SceneName | None = None
    input_paths: dict[str, str] = field(default_factory=dict)
    output_root: str = ""
    run_dir: str = ""
    run_directory: RunDirectory | None = None
    config_path: str = ""
    config_snapshot_path: str = ""
    status: RunStatus = RunStatus.CREATED
    started_at: datetime | None = None
    finished_at: datetime | None = None
    duration_ms: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.run_id:
            raise ValueError("run_id must be non-empty")
        if not self.target_scenes:
            raise ValueError("target_scenes must be non-empty")
        if not self.output_root:
            raise ValueError("output_root must be non-empty")
