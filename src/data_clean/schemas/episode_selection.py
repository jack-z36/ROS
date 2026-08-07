"""Types for the human episode-selection manifest."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


EPISODE_SELECTION_SCHEMA_VERSION = 1
EPISODE_SELECTION_REASONS = (
    "trajectory_anomaly",
    "video_anomaly",
    "action_gripper_anomaly",
    "temporal_sync_anomaly",
    "other",
)


@dataclass(frozen=True)
class EpisodeAnnotation:
    episode_index: int
    reason_code: str | None = None
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"episode_index": self.episode_index, "reason_code": self.reason_code, "note": self.note}


@dataclass
class EpisodeSelectionManifest:
    selection_status: str
    version: int
    job_id: str
    dataset_dir: str
    dataset_fingerprint: str
    contract_fingerprint: str
    total_episodes: int
    bad_episode_indices: list[int] = field(default_factory=list)
    train_episode_indices: list[int] = field(default_factory=list)
    annotations: list[EpisodeAnnotation] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": EPISODE_SELECTION_SCHEMA_VERSION,
            "selection_status": self.selection_status,
            "version": self.version,
            "job_id": self.job_id,
            "dataset_dir": self.dataset_dir,
            "dataset_fingerprint": self.dataset_fingerprint,
            "contract_fingerprint": self.contract_fingerprint,
            "total_episodes": self.total_episodes,
            "bad_episode_indices": self.bad_episode_indices,
            "train_episode_indices": self.train_episode_indices,
            "annotations": [item.to_dict() for item in self.annotations],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
