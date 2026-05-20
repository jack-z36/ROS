"""Single scene dispatcher — dispatch one scene with precheck guard."""

from __future__ import annotations

from datetime import datetime, timezone

from schemas.input_artifact_types import InputArtifactPrecheckSummary
from schemas.runtime_context import RunContext
from schemas.runtime_enums import RunStatus, SceneName
from schemas.runtime_results import RuntimeErrorRef, SceneResult
from schemas.runtime_dispatch_types import (
    DispatchEventType,
    SceneDispatchEvent,
    ServiceRegistry,
)

from .service_registry import lookup_service_binding


def dispatch_single_scene(
    context: RunContext,
    scene_name: SceneName,
    registry: ServiceRegistry,
    precheck_summary: InputArtifactPrecheckSummary,
) -> tuple[SceneResult, list[SceneDispatchEvent]]:
    """Dispatch a single scene.

    Args:
        context: The RunContext for this execution.
        scene_name: The scene to dispatch.
        registry: The ServiceRegistry to look up the binding.
        precheck_summary: The input artifact precheck summary for this scene.

    Returns:
        A tuple of (SceneResult, list of SceneDispatchEvent).
    """
    events: list[SceneDispatchEvent] = []
    run_id = context.run_id

    if precheck_summary.status != RunStatus.SUCCEEDED:
        error = RuntimeErrorRef(
            error_code="scene_precheck_failed",
            step_name="dispatch_single_scene",
            message=f"Precheck failed for scene {scene_name.value}",
            scene_name=scene_name,
        )
        events.append(
            SceneDispatchEvent(
                run_id=run_id,
                event_type=DispatchEventType.SCENE_FAILED,
                status=RunStatus.FAILED,
                scene_name=scene_name,
                error=error,
            )
        )
        return (
            SceneResult(
                scene_name=scene_name,
                status=RunStatus.FAILED,
                error=error,
            ),
            events,
        )

    try:
        binding = lookup_service_binding(registry, scene_name)
    except KeyError:
        error = RuntimeErrorRef(
            error_code="service_not_registered",
            step_name="dispatch_single_scene",
            message=f"Service not registered for scene {scene_name.value}",
            scene_name=scene_name,
        )
        events.append(
            SceneDispatchEvent(
                run_id=run_id,
                event_type=DispatchEventType.SCENE_FAILED,
                status=RunStatus.FAILED,
                scene_name=scene_name,
                error=error,
            )
        )
        return (
            SceneResult(
                scene_name=scene_name,
                status=RunStatus.FAILED,
                error=error,
            ),
            events,
        )

    started_at = datetime.now(timezone.utc)
    events.append(
        SceneDispatchEvent(
            run_id=run_id,
            event_type=DispatchEventType.SCENE_STARTED,
            status=RunStatus.RUNNING,
            scene_name=scene_name,
        )
    )

    try:
        binding.callable_ref(context, scene_name, precheck_summary)
    except Exception as exc:
        finished_at = datetime.now(timezone.utc)
        duration_ms = int((finished_at - started_at).total_seconds() * 1000)
        # If the exception carries a structured error_code, preserve it
        error_code = getattr(exc, "error_code", None)
        if error_code is None:
            error_code = "service_call_failed"
        error = RuntimeErrorRef(
            error_code=error_code,
            step_name="dispatch_single_scene",
            message=str(exc),
            scene_name=scene_name,
        )
        events.append(
            SceneDispatchEvent(
                run_id=run_id,
                event_type=DispatchEventType.SCENE_FAILED,
                status=RunStatus.FAILED,
                scene_name=scene_name,
                error=error,
            )
        )
        return (
            SceneResult(
                scene_name=scene_name,
                status=RunStatus.FAILED,
                input_paths=dict(context.input_paths),
                started_at=started_at,
                finished_at=finished_at,
                duration_ms=duration_ms,
                error=error,
            ),
            events,
        )

    finished_at = datetime.now(timezone.utc)
    duration_ms = int((finished_at - started_at).total_seconds() * 1000)
    events.append(
        SceneDispatchEvent(
            run_id=run_id,
            event_type=DispatchEventType.SCENE_SUCCEEDED,
            status=RunStatus.SUCCEEDED,
            scene_name=scene_name,
        )
    )
    return (
        SceneResult(
            scene_name=scene_name,
            status=RunStatus.SUCCEEDED,
            input_paths=dict(context.input_paths),
            started_at=started_at,
            finished_at=finished_at,
            duration_ms=duration_ms,
        ),
        events,
    )
