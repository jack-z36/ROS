"""Convert Runtime execution records into structured log events."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from ..schemas.runtime_enums import RunStatus, SceneName
from ..schemas.runtime_results import (
    PipelineResult,
    RuntimeErrorRef,
    RuntimeStepRecord,
    SceneResult,
)
from ..schemas.runtime_dispatch_types import SceneDispatchEvent
from ..schemas.structured_log_types import RuntimeLogEvent, RuntimeLogEventType


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _make_event_id(run_id: str, event_type: RuntimeLogEventType, index: int = 0) -> str:
    return f"{run_id}_{event_type.value}_{index}"


def _ensure_serializable(payload: dict[str, Any]) -> dict[str, Any]:
    try:
        json.dumps(payload)
        return payload
    except (TypeError, ValueError):
        return {"_truncated": True, "_reason": "payload not JSON serializable"}


def _convert_step_record(
    record: RuntimeStepRecord,
    run_id: str,
    index: int = 0,
) -> RuntimeLogEvent:
    if not run_id:
        raise ValueError("run_id must be non-empty")

    payload: dict[str, Any] = {"step_name": record.step_name}
    payload.update(_ensure_serializable(record.details))

    return RuntimeLogEvent(
        event_id=_make_event_id(run_id, RuntimeLogEventType.RUNTIME_STEP, index),
        run_id=run_id,
        event_type=RuntimeLogEventType.RUNTIME_STEP,
        status=record.status,
        created_at=record.started_at,
        scene_name=record.scene_name,
        message=record.message,
        payload=payload,
    )


def _convert_dispatch_event(
    event: SceneDispatchEvent,
    run_id: str,
    index: int = 0,
) -> RuntimeLogEvent:
    if not run_id:
        raise ValueError("run_id must be non-empty")

    created_at = event.created_at or _now_utc()
    payload: dict[str, Any] = {"dispatch_event_type": event.event_type.value}

    return RuntimeLogEvent(
        event_id=_make_event_id(run_id, RuntimeLogEventType.DISPATCH_EVENT, index),
        run_id=run_id,
        event_type=RuntimeLogEventType.DISPATCH_EVENT,
        status=event.status,
        created_at=created_at,
        scene_name=event.scene_name,
        message=event.message,
        payload=payload,
        error=event.error,
    )


def _convert_scene_result(
    result: SceneResult,
    run_id: str,
    index: int = 0,
) -> RuntimeLogEvent:
    if not run_id:
        raise ValueError("run_id must be non-empty")

    payload: dict[str, Any] = {
        "input_paths": result.input_paths,
        "output_paths": result.output_paths,
    }
    if result.duration_ms is not None:
        payload["duration_ms"] = result.duration_ms

    created_at = result.started_at or _now_utc()

    return RuntimeLogEvent(
        event_id=_make_event_id(run_id, RuntimeLogEventType.SCENE_RESULT, index),
        run_id=run_id,
        event_type=RuntimeLogEventType.SCENE_RESULT,
        status=result.status,
        created_at=created_at,
        scene_name=result.scene_name,
        payload=payload,
        error=result.error,
    )


def _convert_pipeline_result(
    result: PipelineResult,
    run_id: str,
    index: int = 0,
) -> RuntimeLogEvent:
    if not run_id:
        raise ValueError("run_id must be non-empty")

    payload: dict[str, Any] = {
        "scene_result_count": len(result.scene_results),
        "run_log_path": result.run_log_path,
    }
    if result.manifest_path:
        payload["manifest_path"] = result.manifest_path
    if result.error_summary_path:
        payload["error_summary_path"] = result.error_summary_path

    created_at = _now_utc()

    return RuntimeLogEvent(
        event_id=_make_event_id(run_id, RuntimeLogEventType.PIPELINE_RESULT, index),
        run_id=run_id,
        event_type=RuntimeLogEventType.PIPELINE_RESULT,
        status=result.status,
        created_at=created_at,
        payload=payload,
    )


def _convert_error_ref(
    error_ref: RuntimeErrorRef,
    run_id: str,
    index: int = 0,
) -> RuntimeLogEvent:
    if not run_id:
        raise ValueError("run_id must be non-empty")

    payload: dict[str, Any] = {
        "error_code": error_ref.error_code,
        "step_name": error_ref.step_name,
    }
    if error_ref.details:
        payload["error_details"] = _ensure_serializable(error_ref.details)
    if error_ref.suggested_next_action:
        payload["suggested_next_action"] = error_ref.suggested_next_action

    created_at = _now_utc()

    return RuntimeLogEvent(
        event_id=_make_event_id(run_id, RuntimeLogEventType.ERROR, index),
        run_id=run_id,
        event_type=RuntimeLogEventType.ERROR,
        status=RunStatus.FAILED,
        created_at=created_at,
        scene_name=error_ref.scene_name,
        message=error_ref.message,
        payload=payload,
        error=error_ref,
    )


class LogEventConverter:
    """Converts Runtime records into structured log events."""

    def convert_step(self, record: RuntimeStepRecord, run_id: str, index: int = 0) -> RuntimeLogEvent:
        return _convert_step_record(record, run_id, index)

    def convert_dispatch(self, event: SceneDispatchEvent, run_id: str, index: int = 0) -> RuntimeLogEvent:
        return _convert_dispatch_event(event, run_id, index)

    def convert_scene_result(self, result: SceneResult, run_id: str, index: int = 0) -> RuntimeLogEvent:
        return _convert_scene_result(result, run_id, index)

    def convert_pipeline_result(self, result: PipelineResult, run_id: str, index: int = 0) -> RuntimeLogEvent:
        return _convert_pipeline_result(result, run_id, index)

    def convert_error(self, error_ref: RuntimeErrorRef, run_id: str, index: int = 0) -> RuntimeLogEvent:
        return _convert_error_ref(error_ref, run_id, index)
