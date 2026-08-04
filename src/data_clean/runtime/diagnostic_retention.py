"""Retention utilities for failed/interrupted job staging artifacts."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import shutil
import time
from typing import Any, Iterable


DEFAULT_DIAGNOSTIC_RETENTION_DAYS = 7


def retain_failed_artifacts(
    *,
    job_id: str,
    sources: Iterable[str | Path],
    diagnostics_root: str | Path,
) -> list[str]:
    root = Path(diagnostics_root).expanduser().resolve() / job_id
    root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    retained: list[str] = []
    for index, raw in enumerate(sources):
        source = Path(raw)
        if not source.exists():
            continue
        target = root / f"{stamp}_{index}_{source.name}"
        if target.exists():
            target = root / f"{stamp}_{index}_{time.time_ns()}_{source.name}"
        shutil.move(str(source), str(target))
        retained.append(str(target))
    return retained


def cleanup_expired_diagnostics(
    diagnostics_root: str | Path,
    *,
    retention_days: int = DEFAULT_DIAGNOSTIC_RETENTION_DAYS,
) -> list[str]:
    root = Path(diagnostics_root).expanduser().resolve()
    if not root.is_dir():
        return []
    cutoff = time.time() - max(1, retention_days) * 24 * 60 * 60
    removed: list[str] = []
    for job_dir in root.iterdir():
        if not job_dir.is_dir() or job_dir.stat().st_mtime >= cutoff:
            continue
        shutil.rmtree(job_dir)
        removed.append(str(job_dir))
    return removed


def cleanup_expired_job_staging(
    jobs: Iterable[dict[str, Any]],
    *,
    retention_days: int = DEFAULT_DIAGNOSTIC_RETENTION_DAYS,
) -> list[str]:
    """Remove only generated hidden staging for terminal failed jobs after TTL."""

    cutoff = time.time() - max(1, retention_days) * 24 * 60 * 60
    removed: list[str] = []
    for job in jobs:
        if job.get("status") != "failed":
            continue
        finished_at = job.get("finished_at")
        try:
            finished_timestamp = datetime.fromisoformat(str(finished_at)).timestamp()
        except (TypeError, ValueError):
            continue
        if finished_timestamp >= cutoff:
            continue
        job_id = str(job.get("job_id", ""))
        dataset_name = str(job.get("dataset_name", ""))
        sidecar_dir = Path(str(job.get("sidecar_dir", "")))
        candidates = (
            Path(str(job.get("output_parent", "")))
            / ".data-clean-staging"
            / job_id
            / dataset_name,
            sidecar_dir.parent
            / ".data-clean-staging"
            / job_id
            / sidecar_dir.name,
        )
        for candidate in candidates:
            resolved = candidate.expanduser().resolve()
            if (
                not job_id
                or ".data-clean-staging" not in resolved.parts
                or job_id not in resolved.parts
                or not resolved.is_dir()
            ):
                continue
            shutil.rmtree(resolved)
            removed.append(str(resolved))
    return removed
