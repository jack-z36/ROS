from __future__ import annotations

from pathlib import Path
import threading

from repo.job_store import JobStore
from ui.web_launcher import DataCleanWebApp, STAGE_VERSIONS


def _checkpoint_app(tmp_path: Path) -> DataCleanWebApp:
    app = object.__new__(DataCleanWebApp)
    app.job_store = JobStore(tmp_path / "data_clean.sqlite3")
    app.diagnostics_dir = tmp_path / "diagnostics"
    app.jobs_dir = tmp_path / "jobs"
    app.jobs_dir.mkdir()
    app.lock = threading.RLock()
    app.cancel_events = {}
    app.jobs = {}
    return app


def test_file_stage_retries_atomically_and_skips_valid_checkpoint(
    tmp_path: Path,
) -> None:
    app = _checkpoint_app(tmp_path)
    item = {
        "input_path": str(tmp_path / "raw.mcap"),
        "input_sha256": "input",
        "status": "running",
        "stage_outputs": {},
        "stage_statuses": {},
    }
    job = {
        "job_id": "job-stage",
        "status": "running",
        "created_at": "2026-07-29T00:00:00+08:00",
        "config_sha256": "config",
        "files": [item],
    }
    app.jobs[job["job_id"]] = job
    app.job_store.upsert_job(job)
    target = tmp_path / "sidecar" / "scene1"
    paths = {"cleaned_dir": target}
    calls = 0

    def runner(attempt_paths: dict[str, Path]) -> Path:
        nonlocal calls
        calls += 1
        output = attempt_paths["cleaned_dir"] / "cleaned.mcap"
        output.write_bytes(f"attempt-{calls}".encode())
        item.setdefault("stage_outputs", {})["cleaned_mcap"] = str(output)
        if calls == 1:
            raise RuntimeError("injected mid-write failure")
        return output

    app._run_checkpointed_file_stage(
        job=job,
        item=item,
        file_index=0,
        stage="scene1",
        label="scene1",
        target_key="cleaned_dir",
        paths=paths,
        input_sha256="input",
        runner=runner,
    )
    assert calls == 2
    assert (target / "cleaned.mcap").read_bytes() == b"attempt-2"
    checkpoint = app.job_store.checkpoint_record("job-stage", 0, "scene1")
    assert checkpoint is not None
    assert checkpoint["attempts"] == 2
    assert checkpoint["stage_version"] == STAGE_VERSIONS["scene1"]
    assert checkpoint["validation"]["item_snapshot"]["stage_outputs"][
        "cleaned_mcap"
    ] == str(target / "cleaned.mcap")
    assert list((tmp_path / "diagnostics" / "job-stage").iterdir())

    def must_not_run(_attempt_paths: dict[str, Path]) -> Path:
        raise AssertionError("valid checkpoint should skip the stage runner")

    app._run_checkpointed_file_stage(
        job=job,
        item=item,
        file_index=0,
        stage="scene1",
        label="scene1",
        target_key="cleaned_dir",
        paths=paths,
        input_sha256="input",
        runner=must_not_run,
    )
    assert app.job_store.validate_checkpoint(
        "job-stage",
        0,
        "scene1",
        expected_stage_version=STAGE_VERSIONS["scene1"],
        expected_input_sha256="input",
        expected_config_sha256="config",
    ).valid
