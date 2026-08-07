from pathlib import Path

import pytest

from repo.episode_selection_repository import (
    EpisodeSelectionRepository,
    EpisodeSelectionRepositoryError,
)


def _repo(tmp_path: Path) -> EpisodeSelectionRepository:
    dataset = tmp_path / "dataset"
    (dataset / "meta").mkdir(parents=True)
    (dataset / "meta/info.json").write_text('{"features": {}}', encoding="utf-8")
    return EpisodeSelectionRepository(
        tmp_path / "sidecar/reports",
        job_id="job-1",
        dataset_dir=dataset,
        contract_fingerprint="contract-1",
        episode_indices=[0, 2, 5],
    )


def test_default_and_draft_keep_original_episode_indices(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    manifest = repo.read()
    assert manifest["train_episode_indices"] == [0, 2, 5]

    manifest["bad_episode_indices"] = [5, 5]
    manifest["annotations"] = [{"episode_index": 5, "reason_code": "video_anomaly", "note": "blur"}]
    saved = repo.save_draft(manifest)
    assert saved["train_episode_indices"] == [0, 2]
    assert repo.train_path.read_text(encoding="utf-8") == "0\n2\n"


def test_complete_history_reopen_and_invalid_index(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    manifest = repo.read()
    manifest["bad_episode_indices"] = [2]
    manifest["annotations"] = [{"episode_index": 2, "reason_code": None, "note": ""}]
    complete = repo.complete(repo.save_draft(manifest))
    assert complete["selection_status"] == "complete"
    assert complete["version"] == 1
    assert (repo.history_dir / "v0001.json").is_file()
    reopened = repo.reopen()
    assert reopened["selection_status"] == "draft"
    assert reopened["version"] == 2

    reopened["bad_episode_indices"] = [99]
    with pytest.raises(EpisodeSelectionRepositoryError, match="not present"):
        repo.save_draft(reopened)


def test_all_episodes_can_be_excluded(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    manifest = repo.read()
    manifest["bad_episode_indices"] = [0, 2, 5]
    manifest["annotations"] = []
    completed = repo.complete(repo.save_draft(manifest))
    assert completed["train_episode_indices"] == []
    assert repo.train_path.read_text(encoding="utf-8") == ""


def test_fingerprint_mismatch_is_rejected(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    manifest = repo.read()
    manifest["contract_fingerprint"] = "other"
    with pytest.raises(EpisodeSelectionRepositoryError, match="contract_fingerprint"):
        repo.save_draft(manifest)
