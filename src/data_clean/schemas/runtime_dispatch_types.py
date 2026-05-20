"""Service registry, binding, dispatch plan, and dispatch event types."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from .runtime_enums import SceneName, ServiceMode, RunStatus
from .runtime_results import RuntimeErrorRef
from .input_artifact_types import InputArtifactPrecheckSummary, InputArtifactRequirement


class DispatchEventType(str, Enum):
    """Controlled event types for scene dispatch lifecycle events."""

    DISPATCH_PLAN_CREATED = "dispatch_plan_created"
    SCENE_STARTED = "scene_started"
    SCENE_SUCCEEDED = "scene_succeeded"
    SCENE_FAILED = "scene_failed"
    PIPELINE_STOPPED = "pipeline_stopped"


@dataclass
class ServiceBinding:
    """Binding of a SceneName to a callable service entry point."""

    scene_name: SceneName
    service_mode: ServiceMode
    callable_ref: Callable[..., Any]
    expected_inputs: list[InputArtifactRequirement] = field(default_factory=list)
    declared_outputs: dict[str, str] = field(default_factory=dict)
    supports_smoke: bool = False

    def __post_init__(self) -> None:
        if not callable(self.callable_ref):
            raise ValueError("callable_ref must be callable")


@dataclass
class ServiceRegistry:
    """Registry mapping SceneNames to ServiceBindings under a single ServiceMode."""

    bindings: dict[SceneName, ServiceBinding]
    service_mode: ServiceMode
    registered_scenes: list[SceneName]
    created_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.bindings:
            raise ValueError("bindings must be non-empty")
        if not self.registered_scenes:
            raise ValueError("registered_scenes must be non-empty")
        for scene in self.registered_scenes:
            if scene not in self.bindings:
                raise ValueError(
                    f"registered_scene {scene} has no binding in bindings"
                )
        for scene, binding in self.bindings.items():
            if binding.service_mode != self.service_mode:
                raise ValueError(
                    f"binding for {scene} has service_mode {binding.service_mode.value}, "
                    f"expected {self.service_mode.value}"
                )


@dataclass
class SceneDispatchPlan:
    """Execution plan describing which scenes to dispatch in what order."""

    run_id: str
    target_scenes: list[SceneName]
    bindings: list[ServiceBinding]
    precheck_summaries: dict[SceneName, InputArtifactPrecheckSummary]
    stop_on_failure: bool
    service_mode: ServiceMode

    def __post_init__(self) -> None:
        if not self.run_id:
            raise ValueError("run_id must be non-empty")
        if not self.target_scenes:
            raise ValueError("target_scenes must be non-empty")
        bound_scenes = {b.scene_name for b in self.bindings}
        for scene in self.target_scenes:
            if scene not in bound_scenes:
                raise ValueError(
                    f"target_scene {scene} has no binding in bindings"
                )
            if scene not in self.precheck_summaries:
                raise ValueError(
                    f"target_scene {scene} has no precheck_summary"
                )
        for binding in self.bindings:
            if binding.service_mode != self.service_mode:
                raise ValueError(
                    f"binding for {binding.scene_name} has service_mode "
                    f"{binding.service_mode.value}, expected {self.service_mode.value}"
                )


@dataclass
class SceneDispatchEvent:
    """Structured event emitted during scene dispatch lifecycle."""

    run_id: str
    event_type: DispatchEventType
    status: RunStatus
    scene_name: SceneName | None = None
    message: str = ""
    error: RuntimeErrorRef | None = None
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.run_id:
            raise ValueError("run_id must be non-empty")
        failure_types = {
            DispatchEventType.SCENE_FAILED,
            DispatchEventType.PIPELINE_STOPPED,
        }
        if self.event_type in failure_types and self.error is None:
            raise ValueError(
                f"error must be provided when event_type is {self.event_type.value}"
            )
