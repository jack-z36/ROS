"""Move raw MCAP files after Web cleaning jobs."""

from __future__ import annotations

import shutil
from pathlib import Path

from schemas.mcap_health_audit import MoveInputFileResult, RejectGroup


def move_completed_mcap_files(
    input_paths: list[str | Path],
    completed_root: str | Path,
) -> list[MoveInputFileResult]:
    return _move_files(input_paths, Path(completed_root), "completed")


def move_failed_mcap_files(
    input_paths: list[str | Path],
    rejected_root: str | Path,
) -> list[MoveInputFileResult]:
    return _move_files(input_paths, Path(rejected_root) / RejectGroup.OTHER.value, "failed_cleaning")


def _move_files(
    input_paths: list[str | Path],
    target_dir: Path,
    group: str,
) -> list[MoveInputFileResult]:
    target_dir = target_dir.expanduser().resolve()
    results: list[MoveInputFileResult] = []
    for raw in input_paths:
        source = Path(raw).expanduser().resolve()
        target = _non_overwriting_target(target_dir / source.name)
        if not source.exists():
            results.append(
                MoveInputFileResult(
                    source_path=str(source),
                    target_path=str(target),
                    group=group,
                    moved=False,
                    reason="source_missing",
                )
            )
            continue
        try:
            target_dir.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source), str(target))
            results.append(
                MoveInputFileResult(
                    source_path=str(source),
                    target_path=str(target),
                    group=group,
                    moved=True,
                    reason="moved",
                )
            )
        except Exception as exc:  # noqa: BLE001 - report per-file archival failures.
            results.append(
                MoveInputFileResult(
                    source_path=str(source),
                    target_path=str(target),
                    group=group,
                    moved=False,
                    reason=f"{type(exc).__name__}: {exc}",
                )
            )
    return results


def _non_overwriting_target(target: Path) -> Path:
    if not target.exists():
        return target
    stem = target.stem
    suffix = target.suffix
    for index in range(1, 10000):
        candidate = target.with_name(f"{stem}_{index:03d}{suffix}")
        if not candidate.exists():
            return candidate
    return target.with_name(f"{stem}_{target.stat().st_mtime_ns}{suffix}")
