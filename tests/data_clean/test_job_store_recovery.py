from __future__ import annotations

import json
import os
from pathlib import Path
import sqlite3

import pytest

from repo.job_store import (
    JobStore,
    StageAttemptsExhausted,
    sha256_file,
    sha256_json,
)
from runtime.transactional_publish import TransactionalPublisher
from runtime.diagnostic_retention import cleanup_expired_job_staging


def _job(job_id: str = "job-1", status: str = "queued") -> dict:
    return {
        "job_id": job_id,
        "status": status,
        "created_at": "2026-07-29T00:00:00+08:00",
        "files": [
            {
                "input_path": "/tmp/input.mcap",
                "input_sha256": "input-digest",
                "status": "waiting",
            }
        ],
    }


def test_store_uses_wal_and_imports_legacy_json_once(tmp_path: Path) -> None:
    jobs_dir = tmp_path / "jobs"
    jobs_dir.mkdir()
    legacy = _job("legacy", "running")
    (jobs_dir / "legacy.json").write_text(json.dumps(legacy), encoding="utf-8")

    store = JobStore(tmp_path / "data_clean.sqlite3")
    assert store.import_legacy_jobs(jobs_dir) == {"imported": 1, "skipped": 0}
    assert store.import_legacy_jobs(jobs_dir) == {"imported": 0, "skipped": 1}
    imported = store.load_job("legacy")
    assert imported["status"] == "failed"
    assert "没有持久 checkpoint" in imported["failure_reason"]

    with sqlite3.connect(store.path) as connection:
        assert connection.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
    assert {
        "jobs",
        "job_files",
        "stage_checkpoints",
        "job_events",
        "publish_transactions",
    }.issubset(tables)


def test_lease_recovery_and_persistent_cancel(tmp_path: Path) -> None:
    store = JobStore(tmp_path / "data_clean.sqlite3")
    store.upsert_job(_job())
    claimed = store.claim_next(
        owner_id="old-owner",
        boot_id="old-boot",
        pid=123,
        lease_seconds=600,
    )
    assert claimed is not None
    assert store.load_job("job-1")["status"] == "running"

    recovered = store.recover_abandoned_jobs(current_boot_id="new-boot")
    assert recovered == ["job-1"]
    assert store.load_job("job-1")["status"] == "recovering"
    reclaimed = store.claim_next(
        owner_id="new-owner",
        boot_id="new-boot",
        pid=456,
        lease_seconds=30,
    )
    assert reclaimed is not None and reclaimed.recovering
    store.request_cancel("job-1")
    assert store.cancel_requested("job-1")


def test_queued_cancel_is_terminal_and_not_claimed(tmp_path: Path) -> None:
    store = JobStore(tmp_path / "data_clean.sqlite3")
    store.upsert_job(_job())
    store.request_cancel("job-1")
    assert store.load_job("job-1")["status"] == "cancelled"
    assert (
        store.claim_next(
            owner_id="worker",
            boot_id="boot",
            pid=os.getpid(),
            lease_seconds=30,
        )
        is None
    )


def test_checkpoint_detects_corruption_and_limits_attempts(tmp_path: Path) -> None:
    store = JobStore(tmp_path / "data_clean.sqlite3")
    store.upsert_job(_job())
    source = tmp_path / "input.mcap"
    source.write_bytes(b"input")
    output = tmp_path / "stage" / "output.mcap"
    output.parent.mkdir()
    output.write_bytes(b"valid")
    input_digest = sha256_file(source)
    config_digest = sha256_json({"fps": 15})

    attempt = store.begin_checkpoint(
        job_id="job-1",
        file_index=0,
        stage_name="scene1",
        stage_version="scene1-v1",
        input_sha256=input_digest,
        config_sha256=config_digest,
    )
    assert attempt == 1
    store.complete_checkpoint(
        job_id="job-1",
        file_index=0,
        stage_name="scene1",
        output_paths=[output],
        validation={"readable": True},
    )
    valid = store.validate_checkpoint(
        "job-1",
        0,
        "scene1",
        expected_stage_version="scene1-v1",
        expected_input_sha256=input_digest,
        expected_config_sha256=config_digest,
    )
    assert valid.valid

    output.write_bytes(b"corrupt")
    invalid = store.validate_checkpoint("job-1", 0, "scene1")
    assert not invalid.valid
    assert "size changed" in (invalid.reason or "")

    assert store.begin_checkpoint(
        job_id="job-1",
        file_index=0,
        stage_name="scene1",
        stage_version="scene1-v1",
        input_sha256=input_digest,
        config_sha256=config_digest,
    ) == 2
    store.fail_checkpoint(
        job_id="job-1",
        file_index=0,
        stage_name="scene1",
        error="injected failure 2",
    )
    assert store.begin_checkpoint(
        job_id="job-1",
        file_index=0,
        stage_name="scene1",
        stage_version="scene1-v1",
        input_sha256=input_digest,
        config_sha256=config_digest,
    ) == 3
    store.fail_checkpoint(
        job_id="job-1",
        file_index=0,
        stage_name="scene1",
        error="injected failure 3",
    )
    with pytest.raises(StageAttemptsExhausted):
        store.begin_checkpoint(
            job_id="job-1",
            file_index=0,
            stage_name="scene1",
            stage_version="scene1-v1",
            input_sha256=input_digest,
            config_sha256=config_digest,
        )


def test_manual_resume_resets_failed_attempt_window_and_relocates_snapshot(
    tmp_path: Path,
) -> None:
    store = JobStore(tmp_path / "data_clean.sqlite3")
    store.upsert_job(_job())
    old_root = tmp_path / "staging"
    new_root = tmp_path / "published"
    old_root.mkdir()
    output = old_root / "scene1.mcap"
    output.write_bytes(b"scene1")
    store.begin_checkpoint(
        job_id="job-1",
        file_index=0,
        stage_name="scene1",
        stage_version="v1",
        input_sha256="input",
        config_sha256="config",
    )
    store.complete_checkpoint(
        job_id="job-1",
        file_index=0,
        stage_name="scene1",
        output_paths=[output],
        validation={
            "item_snapshot": {
                "stage_outputs": {"cleaned_mcap": str(output)}
            }
        },
    )
    os.replace(old_root, new_root)
    store.relocate_checkpoint_manifest(
        job_id="job-1",
        file_index=0,
        stage_name="scene1",
        old_root=old_root,
        new_root=new_root,
    )
    record = store.checkpoint_record("job-1", 0, "scene1")
    assert record is not None
    assert record["validation"]["item_snapshot"]["stage_outputs"]["cleaned_mcap"] == str(
        new_root / "scene1.mcap"
    )
    assert store.validate_checkpoint("job-1", 0, "scene1").valid

    for expected_attempt in (1, 2, 3):
        assert store.begin_checkpoint(
            job_id="job-1",
            file_index=0,
            stage_name="scene2",
            stage_version="v1",
            input_sha256="scene1",
            config_sha256="config",
        ) == expected_attempt
        store.fail_checkpoint(
            job_id="job-1",
            file_index=0,
            stage_name="scene2",
            error=f"injected {expected_attempt}",
        )
    failed_job = store.load_job("job-1")
    failed_job["status"] = "failed"
    store.upsert_job(failed_job)
    store.resume_failed_job("job-1")
    assert store.load_job("job-1")["status"] == "recovering"
    assert store.begin_checkpoint(
        job_id="job-1",
        file_index=0,
        stage_name="scene2",
        stage_version="v1",
        input_sha256="scene1",
        config_sha256="config",
    ) == 1


def test_publish_recovery_finishes_old_backup_state(tmp_path: Path) -> None:
    store = JobStore(tmp_path / "data_clean.sqlite3")
    store.upsert_job(_job())
    parent = tmp_path / "exports"
    parent.mkdir()
    target = parent / "dataset"
    target.mkdir()
    (target / "version.txt").write_text("old", encoding="utf-8")
    staging = parent / ".data-clean-staging" / "job-1" / "dataset"
    staging.mkdir(parents=True)
    (staging / "version.txt").write_text("new", encoding="utf-8")
    backup = parent / ".data-clean-backup.job-1.dataset"
    transaction_id = store.create_publish_transaction(
        job_id="job-1",
        target_path=target,
        staging_path=staging,
        backup_path=backup,
        target_existed=True,
    )

    # Simulate SIGKILL after the filesystem rename but before the SQLite update.
    os.replace(target, backup)
    recovered = TransactionalPublisher(store).recover_incomplete()
    assert recovered[0]["transaction_id"] == transaction_id
    assert recovered[0]["status"] == "committed"
    assert (target / "version.txt").read_text(encoding="utf-8") == "new"
    assert not backup.exists()


def test_publish_recovery_commits_after_new_directory_was_installed(
    tmp_path: Path,
) -> None:
    store = JobStore(tmp_path / "data_clean.sqlite3")
    store.upsert_job(_job())
    parent = tmp_path / "exports"
    parent.mkdir()
    target = parent / "dataset"
    target.mkdir()
    (target / "version.txt").write_text("old", encoding="utf-8")
    staging = parent / ".staging"
    staging.mkdir()
    (staging / "version.txt").write_text("new", encoding="utf-8")
    backup = parent / ".backup"
    transaction_id = store.create_publish_transaction(
        job_id="job-1",
        target_path=target,
        staging_path=staging,
        backup_path=backup,
        target_existed=True,
    )
    os.replace(target, backup)
    store.update_publish_transaction(transaction_id, "old_backed_up")
    os.replace(staging, target)

    recovered = TransactionalPublisher(store).recover_incomplete()
    assert recovered[0]["status"] == "committed"
    assert (target / "version.txt").read_text(encoding="utf-8") == "new"
    assert not backup.exists()


def test_publish_recovery_discards_backup_left_after_commit(tmp_path: Path) -> None:
    store = JobStore(tmp_path / "data_clean.sqlite3")
    store.upsert_job(_job())
    parent = tmp_path / "exports"
    parent.mkdir()
    target = parent / "dataset"
    target.mkdir()
    (target / "version.txt").write_text("new", encoding="utf-8")
    staging = parent / ".staging"
    staging.mkdir()
    backup = parent / ".backup"
    backup.mkdir()
    (backup / "version.txt").write_text("old", encoding="utf-8")
    transaction_id = store.create_publish_transaction(
        job_id="job-1",
        target_path=target,
        staging_path=staging,
        backup_path=backup,
        target_existed=True,
    )
    store.update_publish_transaction(transaction_id, "old_backed_up")
    store.update_publish_transaction(transaction_id, "new_installed")
    store.update_publish_transaction(transaction_id, "committed")
    staging.rmdir()

    assert TransactionalPublisher(store).recover_incomplete() == []
    assert not backup.exists()
    assert (target / "version.txt").read_text(encoding="utf-8") == "new"


def test_publish_recovery_rolls_back_when_staging_was_lost(tmp_path: Path) -> None:
    store = JobStore(tmp_path / "data_clean.sqlite3")
    store.upsert_job(_job())
    parent = tmp_path / "exports"
    parent.mkdir()
    target = parent / "dataset"
    target.mkdir()
    (target / "version.txt").write_text("old", encoding="utf-8")
    staging = parent / ".data-clean-staging" / "job-1" / "dataset"
    staging.mkdir(parents=True)
    backup = parent / ".data-clean-backup.job-1.dataset"
    transaction_id = store.create_publish_transaction(
        job_id="job-1",
        target_path=target,
        staging_path=staging,
        backup_path=backup,
        target_existed=True,
    )
    os.replace(target, backup)
    store.update_publish_transaction(transaction_id, "old_backed_up")
    staging.rmdir()

    recovered = TransactionalPublisher(store).recover_incomplete()
    assert recovered[0]["status"] == "rolled_back"
    assert (target / "version.txt").read_text(encoding="utf-8") == "old"


def test_failed_staging_is_retained_then_cleaned_by_ttl(tmp_path: Path) -> None:
    job_id = "job-ttl"
    output_parent = tmp_path / "exports"
    sidecar_dir = tmp_path / "sidecars" / "job-sidecar"
    dataset_staging = (
        output_parent / ".data-clean-staging" / job_id / "dataset"
    )
    sidecar_staging = (
        sidecar_dir.parent
        / ".data-clean-staging"
        / job_id
        / sidecar_dir.name
    )
    dataset_staging.mkdir(parents=True)
    sidecar_staging.mkdir(parents=True)
    job = {
        "job_id": job_id,
        "status": "failed",
        "finished_at": "2020-01-01T00:00:00+00:00",
        "output_parent": str(output_parent),
        "dataset_name": "dataset",
        "sidecar_dir": str(sidecar_dir),
    }
    removed = cleanup_expired_job_staging([job], retention_days=7)
    assert set(removed) == {
        str(dataset_staging.resolve()),
        str(sidecar_staging.resolve()),
    }
    assert not dataset_staging.exists()
    assert not sidecar_staging.exists()
