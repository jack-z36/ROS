"""Run directory creator for the data cleaning pipeline."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Iterable

from schemas import (
    RunDirectory,
    RunDirectoryLayout,
    build_base_run_id,
    ensure_unique_run_id,
)


class RunDirectoryCreationError(Exception):
    """Raised when a run directory cannot be created."""


def _validate_target_scenes(target_scenes: list[str]) -> None:
    """Validate that target_scenes are either a single scene or consecutive from scene1."""
    if not target_scenes:
        raise RunDirectoryCreationError("target_scenes must be non-empty")

    numbers = []
    for scene in target_scenes:
        suffix = "".join(ch for ch in scene if ch.isdigit())
        if not suffix:
            raise RunDirectoryCreationError(
                f"target_scenes contains invalid scene name: {scene!r}"
            )
        numbers.append(int(suffix))

    numbers.sort()

    if len(numbers) == 1:
        return

    expected = list(range(1, len(numbers) + 1))
    if numbers != expected:
        raise RunDirectoryCreationError(
            f"target_scenes must be consecutive starting from scene1, got {target_scenes}"
        )


def create_run_directory(
    run_root: Path,
    run_date: date,
    target_scenes: Iterable[str],
) -> RunDirectory:
    """Create a run directory and outputs/ subdirectory.

    Args:
        run_root: Root directory for run directories.
        run_date: Date for the run.
        target_scenes: Target scene names, e.g. ["scene1"] or ["scene1", ..., "scene5"].

    Returns:
        RunDirectory descriptor with layout.

    Raises:
        RunDirectoryCreationError: If validation fails or directories cannot be created.
    """
    scenes = list(target_scenes)
    _validate_target_scenes(scenes)

    base_run_id = build_base_run_id(run_date, scenes)

    run_root = Path(run_root).resolve()
    run_root.mkdir(parents=True, exist_ok=True)

    existing_ids = {
        d.name for d in run_root.iterdir() if d.is_dir()
    }
    run_id = ensure_unique_run_id(base_run_id, existing_ids)

    run_dir = run_root / run_id
    try:
        run_dir.mkdir(parents=True, exist_ok=False)
    except FileExistsError:
        raise RunDirectoryCreationError(
            f"Run directory already exists and no unique suffix could be generated: {run_dir}"
        )

    outputs_dir = run_dir / "outputs"
    try:
        outputs_dir.mkdir(parents=True, exist_ok=False)
    except OSError as exc:
        raise RunDirectoryCreationError(
            f"Failed to create outputs directory: {outputs_dir}: {exc}"
        )

    layout = RunDirectoryLayout.from_run_dir(run_dir)

    return RunDirectory(
        run_dir=run_dir,
        run_id=run_id,
        base_dir=run_root,
        layout=layout,
        is_new=True,
    )
