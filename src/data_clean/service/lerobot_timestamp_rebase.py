"""Rebase LeRobot v3 dataset timestamps to per-episode relative seconds.

The Forge LeRobot v3 writer stores the raw MCAP ``log_time / 1e9`` absolute Unix
timestamp in the parquet ``timestamp`` column. LeRobot v3 training expects every
episode to start at ``0.0`` and increase by the real per-frame interval. This
post-processor reads back each ``data/chunk-*/file-*.parquet`` after the writer
finishes, subtracts each episode's first-frame timestamp, and rewrites the file
in place — leaving every other column, the row order and the schema untouched.

It does not touch videos, ``info.json``, ``stats.json`` or episode metadata: the
``timestamp`` dtype stays ``float32`` and all other features are unchanged.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq


class LeRobotTimestampRebaseError(RuntimeError):
    """Raised when a dataset cannot be rebased safely."""


def _validate_dataset(dataset_dir: Path) -> None:
    """Make sure ``dataset_dir`` looks like a LeRobot v3 dataset before mutating it."""
    info_path = dataset_dir / "meta" / "info.json"
    if not info_path.is_file():
        raise LeRobotTimestampRebaseError(
            f"not a LeRobot v3 dataset (missing {info_path}): {dataset_dir}"
        )
    try:
        info = json.loads(info_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise LeRobotTimestampRebaseError(
            f"could not parse {info_path}: {exc}"
        ) from exc
    version = info.get("codebase_version")
    if version != "v3.0":
        raise LeRobotTimestampRebaseError(
            f"unsupported LeRobot codebase_version {version!r} "
            f"(expected 'v3.0'): {dataset_dir}"
        )
    data_dir = dataset_dir / "data"
    if not data_dir.is_dir():
        raise LeRobotTimestampRebaseError(
            f"missing data/ directory: {data_dir}"
        )


def _data_parquet_files(dataset_dir: Path) -> list[Path]:
    """Return every ``data/chunk-*/file-*.parquet`` sorted by chunk then file."""
    return sorted((dataset_dir / "data").glob("chunk-*/file-*.parquet"))


def rebase_lerobot_timestamps(
    dataset_dir: str | Path,
    *,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Rebase ``timestamp`` to per-episode relative seconds (first frame = 0.0).

    Args:
        dataset_dir: Root of a LeRobot v3 dataset (containing ``meta/info.json``
            and ``data/chunk-*/file-*.parquet``).
        dry_run: If True, only report what would change; do not rewrite files.

    Returns:
        A JSON-friendly summary:
        ``{"dataset_dir": ..., "dry_run": bool, "files_rewritten": int,
        "files": [{"path": ..., "episodes": [{"episode_index": int,
        "t0": float, "frame_count": int}]}]}``

    Raises:
        LeRobotTimestampRebaseError: if the directory is not a LeRobot v3 dataset
            or a parquet read/write fails.
    """
    dataset_path = Path(dataset_dir).expanduser().resolve()
    _validate_dataset(dataset_path)

    files_summary: list[dict[str, Any]] = []
    rewritten = 0

    for table_path in _data_parquet_files(dataset_path):
        table = pq.read_table(table_path)
        columns = table.column_names
        if "timestamp" not in columns or "episode_index" not in columns:
            # Not a data parquet we understand; skip without mutating it.
            continue

        episode_index = table.column("episode_index").to_pylist()
        timestamp = table.column("timestamp").to_pylist()

        # Preserver the original dtype (float32) when rebuilding the array.
        timestamp_type = table.schema.field("timestamp").type
        episode_type = table.schema.field("episode_index").type

        # First-row timestamp per episode (rows are ordered by frame_index
        # within each episode by the LeRobot v3 writer, so the first
        # occurrence of an episode_index is its frame_index=0 row).
        first_ts: dict[int, float] = {}
        for ep, ts in zip(episode_index, timestamp):
            ep_key = int(ep)
            if ep_key not in first_ts:
                first_ts[ep_key] = float(ts)

        new_timestamp = [
            float(ts) - first_ts[int(ep)] for ep, ts in zip(episode_index, timestamp)
        ]

        episode_report = [
            {"episode_index": ep, "t0": t0, "frame_count": sum(1 for e in episode_index if int(e) == ep)}
            for ep, t0 in sorted(first_ts.items())
        ]
        files_summary.append(
            {"path": str(table_path), "episodes": episode_report}
        )

        if dry_run:
            continue

        import pyarrow as pa

        new_columns = []
        for name in columns:
            if name == "timestamp":
                new_columns.append(pa.array(new_timestamp, type=timestamp_type))
            elif name == "episode_index":
                # Reuse the original column data unchanged.
                new_columns.append(table.column(name))
            else:
                new_columns.append(table.column(name))
        rebuilt = pa.table(dict(zip(columns, new_columns)), schema=table.schema)
        # Preserve the original compression to avoid schema/dtype drift.
        original_file = pq.ParquetFile(table_path)
        compression = None
        try:
            row_groups = original_file.metadata.num_row_groups
            if row_groups > 0:
                compression = original_file.metadata.row_group(0).column(0).compression
        except Exception:
            compression = None
        pq.write_table(
            rebuilt,
            table_path,
            compression=compression if compression != "NONE" else None,
        )
        rewritten += 1

    return {
        "dataset_dir": str(dataset_path),
        "dry_run": dry_run,
        "files_rewritten": rewritten,
        "files": files_summary,
    }
