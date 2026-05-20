"""Run directory types and naming rules for the data cleaning pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from typing import Iterable


class RunArtifactKind(str, Enum):
    """Kind of a run artifact: file or directory."""

    FILE = "file"
    DIRECTORY = "directory"


@dataclass
class RunArtifactPath:
    """Structured reference to a single artifact inside a run directory."""

    path: Path
    artifact_name: str
    artifact_kind: RunArtifactKind
    owner_module: str
    format: str = ""
    required_on_success: bool = False
    required_on_failure: bool = False

    def __post_init__(self) -> None:
        if self.artifact_kind not in (RunArtifactKind.FILE, RunArtifactKind.DIRECTORY):
            raise ValueError(
                f"artifact_kind must be 'file' or 'directory', got {self.artifact_kind!r}"
            )
        if not self.owner_module:
            raise ValueError("owner_module must be non-empty")
        if not self.artifact_name:
            raise ValueError("artifact_name must be non-empty")


@dataclass
class RunDirectoryLayout:
    """Fixed internal paths within a single run directory."""

    run_log_path: RunArtifactPath
    config_snapshot_path: RunArtifactPath
    processing_manifest_path: RunArtifactPath
    error_summary_path: RunArtifactPath
    run_result_path: RunArtifactPath
    outputs_dir: RunArtifactPath

    @classmethod
    def from_run_dir(cls, run_dir: Path) -> RunDirectoryLayout:
        """Build a layout declaration for a given run directory path."""
        return cls(
            run_log_path=RunArtifactPath(
                path=run_dir / "run_log.json",
                artifact_name="run_log",
                artifact_kind=RunArtifactKind.FILE,
                owner_module="structured_logging",
                format="json",
                required_on_success=True,
                required_on_failure=True,
            ),
            config_snapshot_path=RunArtifactPath(
                path=run_dir / "config_snapshot.yaml",
                artifact_name="config_snapshot",
                artifact_kind=RunArtifactKind.FILE,
                owner_module="config_snapshot",
                format="yaml",
                required_on_success=True,
                required_on_failure=False,
            ),
            processing_manifest_path=RunArtifactPath(
                path=run_dir / "processing_manifest.json",
                artifact_name="processing_manifest",
                artifact_kind=RunArtifactKind.FILE,
                owner_module="manifest",
                format="json",
                required_on_success=True,
                required_on_failure=True,
            ),
            error_summary_path=RunArtifactPath(
                path=run_dir / "error_summary.json",
                artifact_name="error_summary",
                artifact_kind=RunArtifactKind.FILE,
                owner_module="error_summary",
                format="json",
                required_on_success=False,
                required_on_failure=True,
            ),
            run_result_path=RunArtifactPath(
                path=run_dir / "run_result.json",
                artifact_name="run_result",
                artifact_kind=RunArtifactKind.FILE,
                owner_module="manifest",
                format="json",
                required_on_success=True,
                required_on_failure=True,
            ),
            outputs_dir=RunArtifactPath(
                path=run_dir / "outputs",
                artifact_name="outputs",
                artifact_kind=RunArtifactKind.DIRECTORY,
                owner_module="run_directory",
                format="directory",
                required_on_success=True,
                required_on_failure=False,
            ),
        )


@dataclass
class RunDirectory:
    """Independent run record directory for a single Runtime execution."""

    run_dir: Path
    run_id: str
    base_dir: Path
    layout: RunDirectoryLayout | None = None
    created_at: datetime = field(default_factory=datetime.now)
    is_new: bool = True

    def __post_init__(self) -> None:
        base = self.base_dir.resolve()
        actual = self.run_dir.resolve()
        try:
            actual.relative_to(base)
        except ValueError:
            raise ValueError(
                f"run_dir {self.run_dir} must be inside base_dir {self.base_dir}"
            )
        if self.layout is None:
            object.__setattr__(self, "layout", RunDirectoryLayout.from_run_dir(self.run_dir))


def build_base_run_id(run_date: date, target_scenes: Iterable[str]) -> str:
    """Generate the base run_id without duplicate suffix.

    Single scene: ``YYYY-MM-DD_s{scene_number}``
    Full pipeline: ``YYYY-MM-DD_all``
    """
    scenes = list(target_scenes)
    date_str = run_date.strftime("%Y-%m-%d")

    if len(scenes) == 1:
        scene = scenes[0]
        number = _scene_number(scene)
        return f"{date_str}_s{number}"

    return f"{date_str}_all"


def _scene_number(scene: str) -> int:
    """Extract numeric suffix from a scene name, e.g. 'scene1' -> 1."""
    for ch in reversed(scene):
        if ch.isdigit():
            continue
        return int(scene[len(scene.rstrip("0123456789")):])
    return 1


def ensure_unique_run_id(base_run_id: str, existing_ids: set[str]) -> str:
    """Append a short sequence suffix if base_run_id already exists.

    Returns base_run_id if not in existing_ids, otherwise ``{base}_002``, ``{base}_003``, etc.
    """
    if base_run_id not in existing_ids:
        return base_run_id

    counter = 2
    while True:
        candidate = f"{base_run_id}_{counter:03d}"
        if candidate not in existing_ids:
            return candidate
        counter += 1


def build_run_id(
    run_date: date,
    target_scenes: Iterable[str],
    existing_ids: set[str],
) -> str:
    """Build a unique run_id given the date, target scenes, and already-existing IDs."""
    base = build_base_run_id(run_date, target_scenes)
    return ensure_unique_run_id(base, existing_ids)


def build_run_directory(
    run_id: str,
    *,
    base_dir: Path | None = None,
) -> RunDirectory:
    """Construct a RunDirectory descriptor without creating the actual directory."""
    if base_dir is None:
        base_dir = Path("src/data_clean/runs")

    run_dir = base_dir / run_id
    layout = RunDirectoryLayout.from_run_dir(run_dir)

    return RunDirectory(
        run_dir=run_dir,
        run_id=run_id,
        base_dir=base_dir,
        layout=layout,
    )
