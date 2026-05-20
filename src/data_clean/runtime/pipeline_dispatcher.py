"""Pipeline dispatcher — sequential multi-scene orchestration with stop-on-failure."""

from __future__ import annotations

from datetime import datetime, timezone

from schemas.input_artifact_types import InputArtifactPrecheckSummary
from schemas.runtime_context import RunContext
from schemas.runtime_enums import RunStatus, SceneName
from schemas.runtime_results import PipelineResult, RuntimeErrorRef, SceneResult
from schemas.runtime_dispatch_types import (
    DispatchEventType,
    SceneDispatchEvent,
    SceneDispatchPlan,
    ServiceRegistry,
)

from .scene_dispatcher import dispatch_single_scene


def dispatch_pipeline(
    context: RunContext,
    plan: SceneDispatchPlan,
    registry: ServiceRegistry,
) -> tuple[PipelineResult, list[SceneDispatchEvent]]:
    """Execute a multi-scene pipeline sequentially.

    Iterates through plan.target_scenes in order, calling dispatch_single_scene
    for each. If a scene fails and plan.stop_on_failure is True, stops execution
    and returns a failed PipelineResult with all scene results collected so far.

    Args:
        context: The RunContext for this execution.
        plan: The SceneDispatchPlan describing which scenes to run.
        registry: The ServiceRegistry with all bindings.

    Returns:
        A tuple of (PipelineResult, list of SceneDispatchEvent).
    """
    all_events: list[SceneDispatchEvent] = []
    scene_results: list[SceneResult] = []

    for scene_name in plan.target_scenes:
        scene_result, scene_events = dispatch_single_scene(
            context, scene_name, registry, plan.precheck_summaries[scene_name]
        )
        all_events.extend(scene_events)
        scene_results.append(scene_result)

        if scene_result.status == RunStatus.FAILED:
            if plan.stop_on_failure:
                error = RuntimeErrorRef(
                    error_code="pipeline_stopped_on_failure",
                    step_name="dispatch_pipeline",
                    message=f"Pipeline stopped after scene {scene_name.value} failed",
                    scene_name=scene_name,
                )
                all_events.append(
                    SceneDispatchEvent(
                        run_id=context.run_id,
                        event_type=DispatchEventType.PIPELINE_STOPPED,
                        status=RunStatus.FAILED,
                        scene_name=scene_name,
                        error=error,
                    )
                )
                return (
                    PipelineResult(
                        run_id=context.run_id,
                        status=RunStatus.FAILED,
                        scene_results=scene_results,
                        run_dir=context.run_dir,
                    ),
                    all_events,
                )

    all_succeeded = all(r.status == RunStatus.SUCCEEDED for r in scene_results)
    return (
        PipelineResult(
            run_id=context.run_id,
            status=RunStatus.SUCCEEDED if all_succeeded else RunStatus.FAILED,
            scene_results=scene_results,
            run_dir=context.run_dir,
        ),
        all_events,
    )
