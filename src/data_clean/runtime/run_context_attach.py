"""Bridge between RunContext and RunDirectory creation."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from schemas import RunContext, RunDirectory
from schemas.runtime_enums import RunMode, SceneName

from .run_directory_creator import RunDirectoryCreationError, create_run_directory


class RunContextAttachError(Exception):
    """Raised when run directory cannot be attached to RunContext."""


def attach_run_directory(
    ctx: RunContext,
    *,
    run_date: date | None = None,
    run_root: Path | None = None,
) -> RunContext:
    """Create the run directory and attach it to the RunContext.

    Args:
        ctx: Existing RunContext with run_id, target_scenes, etc.
        run_date: Date for the run directory. Defaults to today.
        run_root: Root directory for runs. Defaults to src/data_clean/runs.

    Returns:
        The same RunContext instance with run_directory and run_dir populated.

    Raises:
        RunContextAttachError: If directory creation fails.
    """
    if run_date is None:
        run_date = date.today()

    if run_root is None:
        run_root = Path("src/data_clean/runs")

    scene_names = [s.value for s in ctx.target_scenes]

    try:
        run_dir_obj = create_run_directory(run_root, run_date, scene_names)
    except RunDirectoryCreationError as exc:
        raise RunContextAttachError(
            f"Failed to attach run directory for run_id={ctx.run_id!r}: {exc}"
        ) from exc

    ctx.run_directory = run_dir_obj
    ctx.run_dir = str(run_dir_obj.run_dir)

    return ctx


def build_context_with_run_dir(
    run_date: date | None = None,
    run_root: Path | None = None,
    **ctx_kwargs,
) -> RunContext:
    """Convenience: create a RunContext and immediately attach its run directory.

    Args:
        run_date: Date for the run directory. Defaults to today.
        run_root: Root directory for runs. Defaults to src/data_clean/runs.
        **ctx_kwargs: Arguments forwarded to RunContext constructor.

    Returns:
        RunContext with run_directory and run_dir populated.
    """
    if "run_id" not in ctx_kwargs:
        ctx_kwargs["run_id"] = "test-run"
    if "run_mode" not in ctx_kwargs:
        ctx_kwargs["run_mode"] = RunMode.DEV_SINGLE_SCENE
    if "target_scenes" not in ctx_kwargs:
        ctx_kwargs["target_scenes"] = [SceneName.SCENE1]
    if "output_root" not in ctx_kwargs:
        ctx_kwargs["output_root"] = str((run_root or Path("src/data_clean/runs")).resolve())

    ctx = RunContext(**ctx_kwargs)
    return attach_run_directory(ctx, run_date=run_date, run_root=run_root)
