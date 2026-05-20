"""Structured log writer for Runtime MVP run_log.json."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from schemas import (
    RunStatus,
    RunLogFile,
    RuntimeErrorRef,
    RuntimeLogWriteResult,
)


def _datetime_to_json_string(dt: datetime | None) -> str | None:
    """Convert datetime to ISO string or None."""
    if dt is None:
        return None
    return dt.isoformat()


def _log_file_to_dict(log_file: RunLogFile) -> dict:
    """Convert RunLogFile to JSON-serializable dict."""
    events_dict = []
    for event in log_file.events:
        event_dict = {
            "event_id": event.event_id,
            "run_id": event.run_id,
            "event_type": event.event_type.value,
            "step_name": event.step_name,
            "scene_name": event.scene_name.value if event.scene_name else None,
            "status": event.status.value,
            "message": event.message,
            "details": event.details,
            "error": None,
            "created_at": _datetime_to_json_string(event.created_at),
        }
        if event.error:
            event_dict["error"] = {
                "error_code": event.error.error_code,
                "step_name": event.error.step_name,
                "scene_name": event.error.scene_name.value if event.error.scene_name else None,
                "message": event.error.message,
                "details": event.error.details,
                "suggested_next_action": event.error.suggested_next_action,
            }
        events_dict.append(event_dict)

    return {
        "run_id": log_file.run_id,
        "run_dir": log_file.run_dir,
        "started_at": _datetime_to_json_string(log_file.started_at),
        "finished_at": _datetime_to_json_string(log_file.finished_at),
        "status": log_file.status.value,
        "target_scenes": [s.value for s in log_file.target_scenes],
        "config_snapshot_path": log_file.config_snapshot_path,
        "events": events_dict,
    }


def write_run_log(log_file: RunLogFile, run_log_path: str) -> RuntimeLogWriteResult:
    """Write structured log events to run_log.json.

    Args:
        log_file: RunLogFile containing events and metadata.
        run_log_path: Path where run_log.json should be written.

    Returns:
        RuntimeLogWriteResult with write status and metadata.
    """
    result_path = run_log_path if run_log_path else "invalid"

    if not run_log_path:
        return RuntimeLogWriteResult(
            run_id=log_file.run_id,
            run_log_path=result_path,
            status=RunStatus.FAILED,
            event_count=0,
            written_at=datetime.now(),
            error=RuntimeErrorRef(
                error_code="run_log_path_missing",
                step_name="write_run_log",
                message="run_log_path is empty",
            ),
        )

    log_path = Path(run_log_path)
    run_dir = Path(log_file.run_dir).resolve()

    if not str(log_path.resolve()).startswith(str(run_dir)):
        return RuntimeLogWriteResult(
            run_id=log_file.run_id,
            run_log_path=result_path,
            status=RunStatus.FAILED,
            event_count=0,
            written_at=datetime.now(),
            error=RuntimeErrorRef(
                error_code="run_log_path_escape",
                step_name="write_run_log",
                message="run_log_path escapes the run directory",
                details={"run_log_path": run_log_path, "run_dir": str(run_dir)},
            ),
        )

    if log_path.exists():
        return RuntimeLogWriteResult(
            run_id=log_file.run_id,
            run_log_path=result_path,
            status=RunStatus.FAILED,
            event_count=0,
            written_at=datetime.now(),
            error=RuntimeErrorRef(
                error_code="run_log_already_exists",
                step_name="write_run_log",
                message="run_log.json already exists",
                details={"run_log_path": run_log_path},
            ),
        )

    try:
        log_dict = _log_file_to_dict(log_file)
        json_content = json.dumps(log_dict, indent=2)
        log_path.write_text(json_content)
    except (TypeError, ValueError) as e:
        return RuntimeLogWriteResult(
            run_id=log_file.run_id,
            run_log_path=result_path,
            status=RunStatus.FAILED,
            event_count=0,
            written_at=datetime.now(),
            error=RuntimeErrorRef(
                error_code="run_log_event_not_serializable",
                step_name="write_run_log",
                message="Log event contains non-serializable data",
                details={"error": str(e)},
            ),
        )

    return RuntimeLogWriteResult(
        run_id=log_file.run_id,
        run_log_path=result_path,
        status=RunStatus.SUCCEEDED,
        event_count=len(log_file.events),
        written_at=datetime.now(),
    )

    log_path = Path(run_log_path)
    run_dir = Path(log_file.run_dir).resolve()

    if not str(log_path.resolve()).startswith(str(run_dir)):
        return RuntimeLogWriteResult(
            run_id=log_file.run_id,
            run_log_path=run_log_path,
            status=RunStatus.FAILED,
            event_count=0,
            written_at=datetime.now(),
            error=RuntimeErrorRef(
                error_code="run_log_path_escape",
                step_name="write_run_log",
                message="run_log_path escapes the run directory",
                details={"run_log_path": run_log_path, "run_dir": str(run_dir)},
            ),
        )

    if log_path.exists():
        return RuntimeLogWriteResult(
            run_id=log_file.run_id,
            run_log_path=run_log_path,
            status=RunStatus.FAILED,
            event_count=0,
            written_at=datetime.now(),
            error=RuntimeErrorRef(
                error_code="run_log_already_exists",
                step_name="write_run_log",
                message="run_log.json already exists",
                details={"run_log_path": run_log_path},
            ),
        )

    try:
        log_dict = _log_file_to_dict(log_file)
        json_content = json.dumps(log_dict, indent=2)
        log_path.write_text(json_content)
    except (TypeError, ValueError) as e:
        return RuntimeLogWriteResult(
            run_id=log_file.run_id,
            run_log_path=run_log_path,
            status=RunStatus.FAILED,
            event_count=0,
            written_at=datetime.now(),
            error=RuntimeErrorRef(
                error_code="run_log_event_not_serializable",
                step_name="write_run_log",
                message="Log event contains non-serializable data",
                details={"error": str(e)},
            ),
        )

    return RuntimeLogWriteResult(
        run_id=log_file.run_id,
        run_log_path=run_log_path,
        status=RunStatus.SUCCEEDED,
        event_count=len(log_file.events),
        written_at=datetime.now(),
    )