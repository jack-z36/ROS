"""SQLite authority for resumable Web jobs, checkpoints, events, and publishing."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import time
from typing import Any, Iterable, Iterator
import uuid


ACTIVE_JOB_STATUSES = frozenset({"queued", "running", "recovering"})
TERMINAL_JOB_STATUSES = frozenset(
    {"succeeded", "partial_failed", "failed", "cancelled"}
)
ALL_JOB_STATUSES = ACTIVE_JOB_STATUSES | TERMINAL_JOB_STATUSES
CHECKPOINT_STAGES = ("scene1", "scene2", "scene3", "bridge", "export", "gate")
DEFAULT_MAX_STAGE_ATTEMPTS = 3


class JobStoreError(RuntimeError):
    """Raised when persistent job state violates its invariants."""


class StageAttemptsExhausted(JobStoreError):
    """Raised after a stage has reached its configured retry limit."""


@dataclass(frozen=True)
class CheckpointValidation:
    valid: bool
    reason: str | None
    manifest: tuple[dict[str, Any], ...]
    attempts: int
    stage_version: str | None


@dataclass(frozen=True)
class ClaimedJob:
    job_id: str
    previous_status: str
    recovering: bool


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _pid_is_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def sha256_file(path: str | Path, *, chunk_size: int = 4 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        while chunk := stream.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_json(value: Any) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _replace_path_prefix(value: Any, old: str, new: str) -> Any:
    if isinstance(value, dict):
        return {
            key: _replace_path_prefix(item, old, new)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_replace_path_prefix(item, old, new) for item in value]
    if isinstance(value, str) and (value == old or value.startswith(old + os.sep)):
        return new + value[len(old):]
    return value


def build_output_manifest(paths: Iterable[str | Path]) -> list[dict[str, Any]]:
    """Hash explicit output files/directories into a deterministic manifest."""

    entries: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw in paths:
        path = Path(raw).expanduser().resolve()
        key = str(path)
        if key in seen:
            continue
        seen.add(key)
        if not path.exists():
            raise JobStoreError(f"checkpoint output does not exist: {path}")
        if path.is_file():
            entries.append(_manifest_file(path, root=path.parent))
            continue
        if not path.is_dir():
            raise JobStoreError(f"unsupported checkpoint output type: {path}")
        files = sorted(item for item in path.rglob("*") if item.is_file())
        if not files:
            raise JobStoreError(f"checkpoint output directory is empty: {path}")
        entries.append(
            {
                "path": str(path),
                "kind": "directory",
                "file_count": len(files),
            }
        )
        entries.extend(_manifest_file(item, root=path) for item in files)
    if not entries:
        raise JobStoreError("checkpoint output manifest must not be empty")
    return entries


def validate_output_manifest(manifest: Iterable[dict[str, Any]]) -> tuple[bool, str | None]:
    for entry in manifest:
        path = Path(str(entry.get("path", "")))
        kind = entry.get("kind")
        if kind == "directory":
            if not path.is_dir():
                return False, f"checkpoint directory missing: {path}"
            count = sum(1 for item in path.rglob("*") if item.is_file())
            if count != int(entry.get("file_count", -1)):
                return False, f"checkpoint directory file count changed: {path}"
            continue
        if kind != "file":
            return False, f"checkpoint manifest kind is invalid: {kind}"
        if not path.is_file():
            return False, f"checkpoint file missing: {path}"
        stat = path.stat()
        if stat.st_size != int(entry.get("size", -1)):
            return False, f"checkpoint file size changed: {path}"
        if sha256_file(path) != entry.get("sha256"):
            return False, f"checkpoint file sha256 changed: {path}"
    return True, None


def _manifest_file(path: Path, *, root: Path) -> dict[str, Any]:
    stat = path.stat()
    return {
        "path": str(path),
        "relative_path": str(path.relative_to(root)),
        "kind": "file",
        "size": stat.st_size,
        "sha256": sha256_file(path),
    }


class JobStore:
    """Thread-safe-by-connection SQLite repository with WAL enabled."""

    def __init__(self, database_path: str | Path, *, busy_timeout_ms: int = 30_000):
        self.path = Path(database_path).expanduser().resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.busy_timeout_ms = max(1_000, int(busy_timeout_ms))
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(
            self.path,
            timeout=self.busy_timeout_ms / 1000,
            isolation_level=None,
        )
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute(f"PRAGMA busy_timeout = {self.busy_timeout_ms}")
        return connection

    @contextmanager
    def transaction(self, *, immediate: bool = False) -> Iterator[sqlite3.Connection]:
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE" if immediate else "BEGIN")
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute("PRAGMA journal_mode = WAL")
            connection.execute("PRAGMA synchronous = FULL")
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    job_id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    started_at TEXT,
                    finished_at TEXT,
                    owner_id TEXT,
                    lease_expires_at REAL,
                    heartbeat_at TEXT,
                    current_checkpoint TEXT,
                    recovery_from TEXT,
                    recoveries INTEGER NOT NULL DEFAULT 0,
                    cancel_requested INTEGER NOT NULL DEFAULT 0,
                    last_error TEXT,
                    pid INTEGER,
                    boot_id TEXT,
                    imported_legacy INTEGER NOT NULL DEFAULT 0,
                    CHECK(status IN (
                        'queued','running','recovering','succeeded',
                        'partial_failed','failed','cancelled'
                    ))
                );

                CREATE INDEX IF NOT EXISTS jobs_claim_idx
                    ON jobs(status, lease_expires_at, created_at);

                CREATE TABLE IF NOT EXISTS job_files (
                    job_id TEXT NOT NULL REFERENCES jobs(job_id) ON DELETE CASCADE,
                    file_index INTEGER NOT NULL,
                    input_path TEXT NOT NULL,
                    input_sha256 TEXT,
                    status TEXT NOT NULL,
                    current_stage TEXT,
                    payload_json TEXT NOT NULL,
                    PRIMARY KEY(job_id, file_index)
                );

                CREATE TABLE IF NOT EXISTS stage_checkpoints (
                    job_id TEXT NOT NULL REFERENCES jobs(job_id) ON DELETE CASCADE,
                    file_index INTEGER NOT NULL,
                    stage_name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    attempts INTEGER NOT NULL DEFAULT 0,
                    stage_version TEXT,
                    input_sha256 TEXT,
                    config_sha256 TEXT,
                    processing_config_fingerprint TEXT,
                    contract_fingerprint TEXT,
                    quality_report_version TEXT,
                    feature_schema_version TEXT,
                    started_at TEXT,
                    finished_at TEXT,
                    output_manifest_json TEXT,
                    validation_json TEXT,
                    error TEXT,
                    PRIMARY KEY(job_id, file_index, stage_name)
                );

                CREATE TABLE IF NOT EXISTS job_events (
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id TEXT NOT NULL REFERENCES jobs(job_id) ON DELETE CASCADE,
                    created_at TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    payload_json TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS job_events_job_idx
                    ON job_events(job_id, event_id);

                CREATE TABLE IF NOT EXISTS publish_transactions (
                    transaction_id TEXT PRIMARY KEY,
                    job_id TEXT NOT NULL REFERENCES jobs(job_id) ON DELETE CASCADE,
                    target_path TEXT NOT NULL,
                    staging_path TEXT NOT NULL,
                    backup_path TEXT NOT NULL,
                    status TEXT NOT NULL,
                    target_existed INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    error TEXT,
                    CHECK(status IN (
                        'prepared','old_backed_up','new_installed',
                        'committed','rolled_back','failed'
                    ))
                );

                CREATE INDEX IF NOT EXISTS publish_recovery_idx
                    ON publish_transactions(status, updated_at);
                """
            )
            existing_columns = {
                str(row[1])
                for row in connection.execute("PRAGMA table_info(stage_checkpoints)").fetchall()
            }
            for name in (
                "processing_config_fingerprint",
                "contract_fingerprint",
                "quality_report_version",
                "feature_schema_version",
            ):
                if name not in existing_columns:
                    connection.execute(f"ALTER TABLE stage_checkpoints ADD COLUMN {name} TEXT")

    def import_legacy_jobs(self, jobs_dir: str | Path) -> dict[str, int]:
        """Idempotently import JSON history without inventing checkpoints."""

        imported = 0
        skipped = 0
        directory = Path(jobs_dir)
        if not directory.is_dir():
            return {"imported": 0, "skipped": 0}
        for path in sorted(directory.glob("*.json")):
            try:
                value = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                skipped += 1
                continue
            if not isinstance(value, dict) or not value.get("job_id"):
                skipped += 1
                continue
            job_id = str(value["job_id"])
            if self.job_exists(job_id):
                skipped += 1
                continue
            status = str(value.get("status", "failed"))
            if status in {"running", "cancelling", "waiting"}:
                status = "failed"
                value["status"] = status
                value["failure_reason"] = (
                    "由旧 JSON 导入；旧任务没有持久 checkpoint，不能自动恢复。"
                )
            if status not in ALL_JOB_STATUSES:
                status = "failed"
                value["status"] = status
            self.upsert_job(value, imported_legacy=True)
            self.append_event(
                job_id,
                "legacy_job_imported",
                {"source_path": str(path), "recoverable": False},
            )
            imported += 1
        return {"imported": imported, "skipped": skipped}

    def job_exists(self, job_id: str) -> bool:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT 1 FROM jobs WHERE job_id = ?",
                (job_id,),
            ).fetchone()
        return row is not None

    def upsert_job(self, job: dict[str, Any], *, imported_legacy: bool = False) -> None:
        job_id = str(job.get("job_id", "")).strip()
        status = str(job.get("status", "queued"))
        if not job_id:
            raise JobStoreError("job_id must not be empty")
        if status not in ALL_JOB_STATUSES:
            raise JobStoreError(f"invalid persistent job status: {status}")
        now = utc_now_iso()
        payload = json.dumps(job, ensure_ascii=False, default=str)
        with self.transaction(immediate=True) as connection:
            connection.execute(
                """
                INSERT INTO jobs (
                    job_id,status,payload_json,created_at,updated_at,started_at,
                    finished_at,last_error,imported_legacy
                ) VALUES (?,?,?,?,?,?,?,?,?)
                ON CONFLICT(job_id) DO UPDATE SET
                    status=excluded.status,
                    payload_json=excluded.payload_json,
                    updated_at=excluded.updated_at,
                    started_at=excluded.started_at,
                    finished_at=excluded.finished_at,
                    last_error=excluded.last_error,
                    imported_legacy=MAX(jobs.imported_legacy, excluded.imported_legacy)
                """,
                (
                    job_id,
                    status,
                    payload,
                    str(job.get("created_at") or now),
                    now,
                    job.get("started_at"),
                    job.get("finished_at"),
                    job.get("failure_reason"),
                    int(imported_legacy),
                ),
            )
            for index, file_payload in enumerate(job.get("files", [])):
                if not isinstance(file_payload, dict):
                    continue
                connection.execute(
                    """
                    INSERT INTO job_files (
                        job_id,file_index,input_path,input_sha256,status,
                        current_stage,payload_json
                    ) VALUES (?,?,?,?,?,?,?)
                    ON CONFLICT(job_id,file_index) DO UPDATE SET
                        input_path=excluded.input_path,
                        input_sha256=COALESCE(excluded.input_sha256,job_files.input_sha256),
                        status=excluded.status,
                        current_stage=excluded.current_stage,
                        payload_json=excluded.payload_json
                    """,
                    (
                        job_id,
                        index,
                        str(file_payload.get("input_path", "")),
                        file_payload.get("input_sha256"),
                        str(file_payload.get("status", "waiting")),
                        file_payload.get("current_stage"),
                        json.dumps(file_payload, ensure_ascii=False, default=str),
                    ),
                )

    def load_job(self, job_id: str) -> dict[str, Any]:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT payload_json,status,heartbeat_at,current_checkpoint,
                       recovery_from,recoveries,cancel_requested,pid,boot_id
                FROM jobs WHERE job_id = ?
                """,
                (job_id,),
            ).fetchone()
        if row is None:
            raise KeyError(job_id)
        return self._hydrate_job_row(row, job_id=job_id)

    def load_jobs(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT payload_json,status,heartbeat_at,current_checkpoint,
                       recovery_from,recoveries,cancel_requested,pid,boot_id
                FROM jobs ORDER BY created_at
                """
            ).fetchall()
        return [self._hydrate_job_row(row) for row in rows]

    @staticmethod
    def _hydrate_job_row(
        row: sqlite3.Row,
        *,
        job_id: str | None = None,
    ) -> dict[str, Any]:
        """Overlay authoritative lease/checkpoint columns on the UI payload."""

        value = json.loads(row["payload_json"])
        if not isinstance(value, dict):
            raise JobStoreError(
                f"job payload is not an object: {job_id or '<unknown>'}"
            )
        value["status"] = row["status"]
        value["last_heartbeat"] = row["heartbeat_at"]
        value["current_checkpoint"] = row["current_checkpoint"]
        value["recovery_from"] = row["recovery_from"]
        value["recovery_count"] = int(row["recoveries"] or 0)
        value["cancel_requested"] = bool(row["cancel_requested"])
        value["worker_pid"] = row["pid"]
        value["worker_boot_id"] = row["boot_id"]
        return value

    def delete_job(self, job_id: str) -> None:
        with self.transaction(immediate=True) as connection:
            row = connection.execute(
                "SELECT status FROM jobs WHERE job_id = ?",
                (job_id,),
            ).fetchone()
            if row is None:
                raise KeyError(job_id)
            if row["status"] in ACTIVE_JOB_STATUSES:
                raise JobStoreError("active jobs cannot be deleted")
            connection.execute("DELETE FROM jobs WHERE job_id = ?", (job_id,))

    def append_event(self, job_id: str, event_type: str, payload: dict[str, Any]) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO job_events(job_id,created_at,event_type,payload_json)
                VALUES (?,?,?,?)
                """,
                (
                    job_id,
                    utc_now_iso(),
                    event_type,
                    json.dumps(payload, ensure_ascii=False, default=str),
                ),
            )

    def events(self, job_id: str, *, limit: int = 200) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT event_id,created_at,event_type,payload_json
                FROM job_events WHERE job_id = ?
                ORDER BY event_id DESC LIMIT ?
                """,
                (job_id, max(1, int(limit))),
            ).fetchall()
        return [
            {
                "event_id": row["event_id"],
                "created_at": row["created_at"],
                "event_type": row["event_type"],
                "payload": json.loads(row["payload_json"]),
            }
            for row in reversed(rows)
        ]

    def recover_abandoned_jobs(self, *, current_boot_id: str) -> list[str]:
        """Queue active jobs from a prior process and finalize persisted cancellation."""

        recovered: list[str] = []
        with self.transaction(immediate=True) as connection:
            rows = connection.execute(
                """
                SELECT job_id,status,payload_json,current_checkpoint,boot_id,
                       lease_expires_at,pid
                FROM jobs WHERE status IN ('running','recovering')
                """
            ).fetchall()
            for row in rows:
                lease_is_live = bool(
                    row["lease_expires_at"]
                    and row["lease_expires_at"] > time.time()
                )
                owner_process_is_live = bool(
                    row["boot_id"] == current_boot_id
                    and row["pid"]
                    and _pid_is_alive(int(row["pid"]))
                )
                if lease_is_live and owner_process_is_live:
                    continue
                job = json.loads(row["payload_json"])
                job["status"] = "recovering"
                job["recovery_from"] = row["current_checkpoint"]
                job["notification"] = "检测到上次服务中断，正在从最后有效 checkpoint 恢复。"
                connection.execute(
                    """
                    UPDATE jobs SET status='recovering',payload_json=?,owner_id=NULL,
                        lease_expires_at=NULL,heartbeat_at=NULL,recovery_from=?,
                        recoveries=recoveries+1,updated_at=?
                    WHERE job_id=?
                    """,
                    (
                        json.dumps(job, ensure_ascii=False, default=str),
                        row["current_checkpoint"],
                        utc_now_iso(),
                        row["job_id"],
                    ),
                )
                recovered.append(row["job_id"])
        for job_id in recovered:
            self.append_event(
                job_id,
                "job_recovery_queued",
                {"reason": "owner_missing_or_lease_expired"},
            )
        return recovered

    def claim_next(
        self,
        *,
        owner_id: str,
        boot_id: str,
        pid: int,
        lease_seconds: float,
    ) -> ClaimedJob | None:
        now = time.time()
        with self.transaction(immediate=True) as connection:
            row = connection.execute(
                """
                SELECT job_id,status,payload_json
                FROM jobs
                WHERE cancel_requested=0
                  AND (status IN ('queued','recovering')
                   OR (status='running' AND (lease_expires_at IS NULL OR lease_expires_at < ?))
                  )
                ORDER BY CASE status WHEN 'recovering' THEN 0 ELSE 1 END, created_at
                LIMIT 1
                """,
                (now,),
            ).fetchone()
            if row is None:
                return None
            previous = str(row["status"])
            next_status = "recovering" if previous in {"recovering", "running"} else "running"
            job = json.loads(row["payload_json"])
            job["status"] = next_status
            job["started_at"] = job.get("started_at") or utc_now_iso()
            job["last_heartbeat"] = utc_now_iso()
            connection.execute(
                """
                UPDATE jobs SET status=?,payload_json=?,owner_id=?,lease_expires_at=?,
                    heartbeat_at=?,updated_at=?,pid=?,boot_id=?
                WHERE job_id=?
                """,
                (
                    next_status,
                    json.dumps(job, ensure_ascii=False, default=str),
                    owner_id,
                    now + lease_seconds,
                    job["last_heartbeat"],
                    utc_now_iso(),
                    pid,
                    boot_id,
                    row["job_id"],
                ),
            )
        self.append_event(
            row["job_id"],
            "job_claimed",
            {"owner_id": owner_id, "status": next_status},
        )
        return ClaimedJob(
            job_id=row["job_id"],
            previous_status=previous,
            recovering=next_status == "recovering",
        )

    def heartbeat(self, job_id: str, *, owner_id: str, lease_seconds: float) -> bool:
        heartbeat = utc_now_iso()
        with self.transaction(immediate=True) as connection:
            row = connection.execute(
                "SELECT payload_json FROM jobs WHERE job_id=? AND owner_id=?",
                (job_id, owner_id),
            ).fetchone()
            if row is None:
                return False
            job = json.loads(row["payload_json"])
            job["last_heartbeat"] = heartbeat
            connection.execute(
                """
                UPDATE jobs SET heartbeat_at=?,lease_expires_at=?,updated_at=?,payload_json=?
                WHERE job_id=? AND owner_id=?
                """,
                (
                    heartbeat,
                    time.time() + lease_seconds,
                    heartbeat,
                    json.dumps(job, ensure_ascii=False, default=str),
                    job_id,
                    owner_id,
                ),
            )
        return True

    def release_lease(self, job_id: str, *, owner_id: str) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE jobs SET owner_id=NULL,lease_expires_at=NULL,updated_at=?
                WHERE job_id=? AND owner_id=?
                """,
                (utc_now_iso(), job_id, owner_id),
            )

    def request_cancel(self, job_id: str) -> None:
        with self.transaction(immediate=True) as connection:
            row = connection.execute(
                "SELECT status,payload_json,owner_id FROM jobs WHERE job_id=?",
                (job_id,),
            ).fetchone()
            if row is None:
                raise KeyError(job_id)
            if row["status"] in TERMINAL_JOB_STATUSES:
                return
            job = json.loads(row["payload_json"])
            job["cancel_requested"] = True
            cancel_immediately = (
                row["status"] in {"queued", "recovering"}
                and row["owner_id"] is None
            )
            if cancel_immediately:
                job["status"] = "cancelled"
                job["finished_at"] = utc_now_iso()
                job["notification"] = "排队任务已持久取消，不会在服务重启后恢复。"
            else:
                job["notification"] = "取消请求已持久化，将在当前安全边界停止。"
            connection.execute(
                """
                UPDATE jobs SET cancel_requested=1,status=?,payload_json=?,
                    finished_at=COALESCE(?,finished_at),updated_at=?
                WHERE job_id=?
                """,
                (
                    job["status"],
                    json.dumps(job, ensure_ascii=False, default=str),
                    job.get("finished_at"),
                    utc_now_iso(),
                    job_id,
                ),
            )
        self.append_event(job_id, "job_cancel_requested", {})

    def cancel_requested(self, job_id: str) -> bool:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT cancel_requested FROM jobs WHERE job_id=?",
                (job_id,),
            ).fetchone()
        return bool(row and row["cancel_requested"])

    def resume_failed_job(self, job_id: str) -> None:
        """Queue a failed job only when at least one checkpoint remains valid."""

        with self.transaction(immediate=True) as connection:
            row = connection.execute(
                "SELECT status,payload_json FROM jobs WHERE job_id=?",
                (job_id,),
            ).fetchone()
            if row is None:
                raise KeyError(job_id)
            if row["status"] != "failed":
                raise JobStoreError("only failed jobs can be resumed")
        completed = self.completed_checkpoints(job_id)
        if not completed:
            raise JobStoreError("job has no completed checkpoint and cannot be resumed")
        valid = any(
            self.validate_checkpoint(job_id, item["file_index"], item["stage_name"]).valid
            for item in completed
        )
        if not valid:
            raise JobStoreError("job checkpoints are no longer valid")
        with self.transaction(immediate=True) as connection:
            row = connection.execute(
                "SELECT payload_json FROM jobs WHERE job_id=?",
                (job_id,),
            ).fetchone()
            job = json.loads(row["payload_json"])
            job["status"] = "recovering"
            job["finished_at"] = None
            job["failure_reason"] = None
            job["cancel_requested"] = False
            job["notification"] = "手动恢复已排队。"
            reset_rows = connection.execute(
                """
                SELECT file_index,stage_name,attempts,status
                FROM stage_checkpoints
                WHERE job_id=? AND status IN ('failed','invalid','running')
                """,
                (job_id,),
            ).fetchall()
            connection.execute(
                """
                UPDATE stage_checkpoints
                SET attempts=0,status='failed',started_at=NULL,finished_at=NULL,
                    output_manifest_json=NULL,validation_json=NULL
                WHERE job_id=? AND status IN ('failed','invalid','running')
                """,
                (job_id,),
            )
            connection.execute(
                """
                UPDATE jobs SET status='recovering',payload_json=?,finished_at=NULL,
                    last_error=NULL,cancel_requested=0,owner_id=NULL,
                    lease_expires_at=NULL,recoveries=recoveries+1,
                    recovery_from=current_checkpoint,updated_at=?
                WHERE job_id=?
                """,
                (
                    json.dumps(job, ensure_ascii=False, default=str),
                    utc_now_iso(),
                    job_id,
                ),
            )
        self.append_event(
            job_id,
            "job_manual_resume_queued",
            {
                "reset_attempt_windows": [
                    {
                        "file_index": row["file_index"],
                        "stage": row["stage_name"],
                        "previous_attempts": row["attempts"],
                        "previous_status": row["status"],
                    }
                    for row in reset_rows
                ]
            },
        )

    def begin_checkpoint(
        self,
        *,
        job_id: str,
        file_index: int,
        stage_name: str,
        stage_version: str,
        input_sha256: str,
        config_sha256: str,
        processing_config_fingerprint: str | None = None,
        contract_fingerprint: str | None = None,
        quality_report_version: str | None = None,
        feature_schema_version: str | None = None,
        max_attempts: int = DEFAULT_MAX_STAGE_ATTEMPTS,
    ) -> int:
        if stage_name not in CHECKPOINT_STAGES:
            raise JobStoreError(f"unknown checkpoint stage: {stage_name}")
        with self.transaction(immediate=True) as connection:
            row = connection.execute(
                """
                SELECT attempts,status FROM stage_checkpoints
                WHERE job_id=? AND file_index=? AND stage_name=?
                """,
                (job_id, file_index, stage_name),
            ).fetchone()
            attempts = int(row["attempts"]) if row else 0
            if attempts >= max_attempts:
                raise StageAttemptsExhausted(
                    f"{stage_name} exceeded {max_attempts} attempts"
                )
            attempts += 1
            now = utc_now_iso()
            connection.execute(
                """
                INSERT INTO stage_checkpoints(
                    job_id,file_index,stage_name,status,attempts,stage_version,
                    input_sha256,config_sha256,started_at,finished_at,
                    processing_config_fingerprint,contract_fingerprint,
                    quality_report_version,feature_schema_version,
                    output_manifest_json,validation_json,error
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(job_id,file_index,stage_name) DO UPDATE SET
                    status='running',attempts=excluded.attempts,
                    stage_version=excluded.stage_version,
                    input_sha256=excluded.input_sha256,
                    config_sha256=excluded.config_sha256,
                    processing_config_fingerprint=excluded.processing_config_fingerprint,
                    contract_fingerprint=excluded.contract_fingerprint,
                    quality_report_version=excluded.quality_report_version,
                    feature_schema_version=excluded.feature_schema_version,
                    started_at=excluded.started_at,finished_at=NULL,
                    output_manifest_json=NULL,validation_json=NULL,error=NULL
                """,
                (
                    job_id,
                    file_index,
                    stage_name,
                    "running",
                    attempts,
                    stage_version,
                    input_sha256,
                    config_sha256,
                    now,
                    None,
                    processing_config_fingerprint,
                    contract_fingerprint,
                    quality_report_version,
                    feature_schema_version,
                    None,
                    None,
                    None,
                ),
            )
            connection.execute(
                """
                UPDATE jobs SET current_checkpoint=?,updated_at=?
                WHERE job_id=?
                """,
                (f"{file_index}:{stage_name}", now, job_id),
            )
        self.append_event(
            job_id,
            "checkpoint_started",
            {"file_index": file_index, "stage": stage_name, "attempt": attempts},
        )
        return attempts

    def complete_checkpoint(
        self,
        *,
        job_id: str,
        file_index: int,
        stage_name: str,
        output_paths: Iterable[str | Path],
        validation: dict[str, Any],
    ) -> list[dict[str, Any]]:
        manifest = build_output_manifest(output_paths)
        valid, reason = validate_output_manifest(manifest)
        if not valid:
            raise JobStoreError(reason or "checkpoint output validation failed")
        finished = utc_now_iso()
        with self.transaction(immediate=True) as connection:
            updated = connection.execute(
                """
                UPDATE stage_checkpoints SET status='completed',finished_at=?,
                    output_manifest_json=?,validation_json=?,error=NULL
                WHERE job_id=? AND file_index=? AND stage_name=? AND status='running'
                """,
                (
                    finished,
                    json.dumps(manifest, ensure_ascii=False),
                    json.dumps(validation, ensure_ascii=False, default=str),
                    job_id,
                    file_index,
                    stage_name,
                ),
            ).rowcount
            if updated != 1:
                raise JobStoreError(
                    f"checkpoint was not running: {job_id}/{file_index}/{stage_name}"
                )
            connection.execute(
                "UPDATE jobs SET current_checkpoint=?,updated_at=? WHERE job_id=?",
                (f"{file_index}:{stage_name}", finished, job_id),
            )
        self.append_event(
            job_id,
            "checkpoint_completed",
            {"file_index": file_index, "stage": stage_name, "files": len(manifest)},
        )
        return manifest

    def fail_checkpoint(
        self,
        *,
        job_id: str,
        file_index: int,
        stage_name: str,
        error: str,
    ) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE stage_checkpoints SET status='failed',finished_at=?,error=?
                WHERE job_id=? AND file_index=? AND stage_name=?
                """,
                (utc_now_iso(), error, job_id, file_index, stage_name),
            )
        self.append_event(
            job_id,
            "checkpoint_failed",
            {"file_index": file_index, "stage": stage_name, "error": error},
        )

    def validate_checkpoint(
        self,
        job_id: str,
        file_index: int,
        stage_name: str,
        *,
        expected_stage_version: str | None = None,
        expected_input_sha256: str | None = None,
        expected_config_sha256: str | None = None,
    ) -> CheckpointValidation:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT * FROM stage_checkpoints
                WHERE job_id=? AND file_index=? AND stage_name=?
                """,
                (job_id, file_index, stage_name),
            ).fetchone()
        if row is None or row["status"] != "completed":
            return CheckpointValidation(False, "checkpoint_not_completed", (), 0, None)
        manifest_raw = json.loads(row["output_manifest_json"] or "[]")
        manifest = tuple(manifest_raw if isinstance(manifest_raw, list) else [])
        comparisons = (
            ("stage_version", expected_stage_version),
            ("input_sha256", expected_input_sha256),
            ("config_sha256", expected_config_sha256),
        )
        for column, expected in comparisons:
            if expected is not None and row[column] != expected:
                return CheckpointValidation(
                    False,
                    f"checkpoint_{column}_changed",
                    manifest,
                    int(row["attempts"]),
                    row["stage_version"],
                )
        valid, reason = validate_output_manifest(manifest)
        if not valid:
            self.invalidate_checkpoint(job_id, file_index, stage_name, reason or "manifest_invalid")
        return CheckpointValidation(
            valid,
            reason,
            manifest,
            int(row["attempts"]),
            row["stage_version"],
        )

    def invalidate_checkpoint(
        self,
        job_id: str,
        file_index: int,
        stage_name: str,
        reason: str,
    ) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE stage_checkpoints SET status='invalid',error=?,finished_at=?
                WHERE job_id=? AND file_index=? AND stage_name=?
                """,
                (reason, utc_now_iso(), job_id, file_index, stage_name),
            )
        self.append_event(
            job_id,
            "checkpoint_invalidated",
            {"file_index": file_index, "stage": stage_name, "reason": reason},
        )

    def checkpoint_record(
        self,
        job_id: str,
        file_index: int,
        stage_name: str,
    ) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT * FROM stage_checkpoints
                WHERE job_id=? AND file_index=? AND stage_name=?
                """,
                (job_id, file_index, stage_name),
            ).fetchone()
        if row is None:
            return None
        result = dict(row)
        for key in ("output_manifest_json", "validation_json"):
            result[key.removesuffix("_json")] = json.loads(result.pop(key) or "null")
        return result

    def relocate_checkpoint_manifest(
        self,
        *,
        job_id: str,
        file_index: int,
        stage_name: str,
        old_root: str | Path,
        new_root: str | Path,
    ) -> None:
        """Rewrite paths after an atomic staging -> target directory rename."""

        old = str(Path(old_root).expanduser().resolve())
        new = str(Path(new_root).expanduser().resolve())
        with self.transaction(immediate=True) as connection:
            row = connection.execute(
                """
                SELECT output_manifest_json,validation_json FROM stage_checkpoints
                WHERE job_id=? AND file_index=? AND stage_name=? AND status='completed'
                """,
                (job_id, file_index, stage_name),
            ).fetchone()
            if row is None:
                return
            manifest = json.loads(row["output_manifest_json"] or "[]")
            for entry in manifest:
                raw = str(entry.get("path", ""))
                if raw == old or raw.startswith(old + os.sep):
                    entry["path"] = new + raw[len(old):]
            validation = _replace_path_prefix(
                json.loads(row["validation_json"] or "null"),
                old,
                new,
            )
            connection.execute(
                """
                UPDATE stage_checkpoints
                SET output_manifest_json=?,validation_json=?
                WHERE job_id=? AND file_index=? AND stage_name=?
                """,
                (
                    json.dumps(manifest, ensure_ascii=False),
                    json.dumps(validation, ensure_ascii=False, default=str),
                    job_id,
                    file_index,
                    stage_name,
                ),
            )

    def completed_checkpoints(self, job_id: str) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT file_index,stage_name,attempts,stage_version,finished_at
                FROM stage_checkpoints
                WHERE job_id=? AND status='completed'
                ORDER BY file_index,finished_at
                """,
                (job_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def create_publish_transaction(
        self,
        *,
        job_id: str,
        target_path: str | Path,
        staging_path: str | Path,
        backup_path: str | Path,
        target_existed: bool,
    ) -> str:
        transaction_id = uuid.uuid4().hex
        now = utc_now_iso()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO publish_transactions(
                    transaction_id,job_id,target_path,staging_path,backup_path,
                    status,target_existed,created_at,updated_at
                ) VALUES (?,?,?,?,?,?,?,?,?)
                """,
                (
                    transaction_id,
                    job_id,
                    str(Path(target_path).resolve()),
                    str(Path(staging_path).resolve()),
                    str(Path(backup_path).resolve()),
                    "prepared",
                    int(target_existed),
                    now,
                    now,
                ),
            )
        self.append_event(
            job_id,
            "publish_prepared",
            {"transaction_id": transaction_id, "target": str(target_path)},
        )
        return transaction_id

    def update_publish_transaction(
        self,
        transaction_id: str,
        status: str,
        *,
        error: str | None = None,
    ) -> None:
        if status not in {
            "prepared",
            "old_backed_up",
            "new_installed",
            "committed",
            "rolled_back",
            "failed",
        }:
            raise JobStoreError(f"invalid publish transaction status: {status}")
        with self.transaction(immediate=True) as connection:
            row = connection.execute(
                "SELECT job_id FROM publish_transactions WHERE transaction_id=?",
                (transaction_id,),
            ).fetchone()
            if row is None:
                raise KeyError(transaction_id)
            connection.execute(
                """
                UPDATE publish_transactions SET status=?,updated_at=?,error=?
                WHERE transaction_id=?
                """,
                (status, utc_now_iso(), error, transaction_id),
            )
        self.append_event(
            row["job_id"],
            f"publish_{status}",
            {"transaction_id": transaction_id, "error": error},
        )

    def incomplete_publish_transactions(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM publish_transactions
                WHERE status IN ('prepared','old_backed_up','new_installed')
                ORDER BY created_at
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def committed_publish_transactions(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM publish_transactions
                WHERE status='committed' ORDER BY created_at
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def publish_transaction(self, transaction_id: str) -> dict[str, Any]:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM publish_transactions WHERE transaction_id=?",
                (transaction_id,),
            ).fetchone()
        if row is None:
            raise KeyError(transaction_id)
        return dict(row)

    def publish_transactions_for_job(self, job_id: str) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM publish_transactions
                WHERE job_id=? ORDER BY created_at,transaction_id
                """,
                (job_id,),
            ).fetchall()
        return [dict(row) for row in rows]
