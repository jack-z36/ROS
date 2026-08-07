"""Atomic persistence and validation for human episode selection."""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from schemas.episode_selection import EPISODE_SELECTION_REASONS


class EpisodeSelectionRepositoryError(ValueError):
    pass


def _now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def dataset_fingerprint(dataset_dir: str | Path) -> str:
    root = Path(dataset_dir).expanduser().resolve()
    records: list[dict[str, Any]] = []
    for path in sorted(root.glob("meta/info.json")) + sorted(root.glob("meta/episodes/chunk-*/file-*.parquet")) + sorted(root.glob("data/chunk-*/file-*.parquet")):
        stat = path.stat()
        records.append({"path": str(path.relative_to(root)), "size": stat.st_size, "mtime_ns": stat.st_mtime_ns})
    info = root / "meta/info.json"
    if info.is_file():
        records.append({"info_sha256": hashlib.sha256(info.read_bytes()).hexdigest()})
    return hashlib.sha256(json.dumps(records, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


class EpisodeSelectionRepository:
    def __init__(self, reports_dir: str | Path, *, job_id: str, dataset_dir: str | Path, contract_fingerprint: str, episode_indices: list[int]):
        self.reports_dir = Path(reports_dir).expanduser().resolve()
        self.job_id = job_id
        self.dataset_dir = str(Path(dataset_dir).expanduser().resolve())
        self.contract_fingerprint = contract_fingerprint
        self.episode_indices = sorted(set(int(item) for item in episode_indices))

    @property
    def manifest_path(self) -> Path:
        return self.reports_dir / "episode_selection.json"

    @property
    def train_path(self) -> Path:
        return self.reports_dir / "train_episodes.txt"

    @property
    def history_dir(self) -> Path:
        return self.reports_dir / "episode_selection_history"

    def _metadata(self) -> dict[str, Any]:
        return {"job_id": self.job_id, "dataset_dir": self.dataset_dir, "dataset_fingerprint": dataset_fingerprint(self.dataset_dir), "contract_fingerprint": self.contract_fingerprint}

    def _default(self, *, version: int = 1, status: str = "draft") -> dict[str, Any]:
        now = _now()
        meta = self._metadata()
        return {"schema_version": 1, "selection_status": status, "version": version, **meta, "total_episodes": len(self.episode_indices), "bad_episode_indices": [], "train_episode_indices": list(self.episode_indices), "annotations": [], "created_at": now, "updated_at": now}

    def _validate(self, raw: dict[str, Any], *, status: str | None = None) -> dict[str, Any]:
        if not isinstance(raw, dict) or raw.get("schema_version") != 1:
            raise EpisodeSelectionRepositoryError("invalid episode selection schema")
        expected = self._metadata()
        for key in ("job_id", "dataset_dir", "dataset_fingerprint", "contract_fingerprint"):
            if raw.get(key) != expected[key]:
                raise EpisodeSelectionRepositoryError(f"episode selection {key} mismatch")
        if status and raw.get("selection_status") != status:
            raise EpisodeSelectionRepositoryError(f"selection status must be {status}")
        bad = sorted(set(int(item) for item in raw.get("bad_episode_indices", [])))
        known = set(self.episode_indices)
        if any(item not in known for item in bad):
            raise EpisodeSelectionRepositoryError("bad episode index is not present in dataset")
        annotations_by_episode: dict[int, dict[str, Any]] = {}
        for item in raw.get("annotations", []):
            index = int(item.get("episode_index"))
            if index not in set(bad):
                raise EpisodeSelectionRepositoryError("annotation must refer to a bad episode")
            reason = item.get("reason_code")
            if reason not in (None, "", *EPISODE_SELECTION_REASONS):
                raise EpisodeSelectionRepositoryError(f"unknown episode selection reason: {reason}")
            annotations_by_episode[index] = {"episode_index": index, "reason_code": reason or None, "note": str(item.get("note") or "")}
        normalized = dict(raw)
        normalized.update({"total_episodes": len(self.episode_indices), "bad_episode_indices": bad, "train_episode_indices": [item for item in self.episode_indices if item not in set(bad)], "annotations": [annotations_by_episode[key] for key in sorted(annotations_by_episode)], "updated_at": _now()})
        return normalized

    def read(self) -> dict[str, Any]:
        if not self.manifest_path.is_file():
            value = self._default()
            self._write_current(value)
            return value
        try:
            value = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise EpisodeSelectionRepositoryError("invalid episode selection manifest") from exc
        return self._validate(value)

    def save_draft(self, raw: dict[str, Any]) -> dict[str, Any]:
        value = self._validate(raw, status="draft")
        self._write_current(value)
        return value

    def complete(self, raw: dict[str, Any]) -> dict[str, Any]:
        value = self._validate(raw, status="draft")
        value["selection_status"] = "complete"
        value["version"] = self._next_version()
        self._write_current(value)
        self.history_dir.mkdir(parents=True, exist_ok=True)
        _atomic_write(self.history_dir / f"v{value['version']:04d}.json", value)
        self._write_train(value["train_episode_indices"])
        return value

    def reopen(self) -> dict[str, Any]:
        current = self.read()
        current["selection_status"] = "draft"
        current["version"] = self._next_version()
        current["created_at"] = _now()
        return self.save_draft(current)

    def _next_version(self) -> int:
        versions = [int(path.stem[1:]) for path in self.history_dir.glob("v*.json") if path.stem[1:].isdigit()]
        return max(versions, default=0) + 1

    def _write_current(self, value: dict[str, Any]) -> None:
        _atomic_write(self.manifest_path, value)
        if value.get("selection_status") == "draft":
            self._write_train(value["train_episode_indices"])

    def _write_train(self, values: list[int]) -> None:
        self.train_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.train_path.with_name(f".{self.train_path.name}.{os.getpid()}.tmp")
        temporary.write_text("".join(f"{int(item)}\n" for item in values), encoding="utf-8")
        temporary.replace(self.train_path)


def _atomic_write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)
