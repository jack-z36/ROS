"""Managed single-job worker with SQLite leases and heartbeat."""

from __future__ import annotations

import os
from pathlib import Path
import threading
import time
from typing import Callable
import uuid

from repo.job_store import JobStore


def read_boot_id() -> str:
    path = Path("/proc/sys/kernel/random/boot_id")
    try:
        return path.read_text(encoding="utf-8").strip()
    except OSError:
        return "unknown-boot"


class PersistentJobWorker:
    """Claim one durable job at a time; per-file concurrency remains job-owned."""

    def __init__(
        self,
        *,
        store: JobStore,
        run_job: Callable[[str, bool], None],
        lease_seconds: float = 30.0,
        heartbeat_seconds: float = 5.0,
        poll_seconds: float = 1.0,
    ):
        self.store = store
        self.run_job = run_job
        self.lease_seconds = max(10.0, float(lease_seconds))
        self.heartbeat_seconds = min(
            max(1.0, float(heartbeat_seconds)),
            self.lease_seconds / 2,
        )
        self.poll_seconds = max(0.1, float(poll_seconds))
        self.boot_id = read_boot_id()
        self.owner_id = f"{self.boot_id}:{os.getpid()}:{uuid.uuid4().hex}"
        self.stop_event = threading.Event()
        self.wake_event = threading.Event()
        self.thread = threading.Thread(
            target=self._loop,
            name="data-clean-persistent-worker",
            daemon=False,
        )
        self.current_job_id: str | None = None

    def start(self) -> list[str]:
        recovered = self.store.recover_abandoned_jobs(current_boot_id=self.boot_id)
        self.thread.start()
        return recovered

    def wake(self) -> None:
        self.wake_event.set()

    def close(self, *, join_timeout: float = 10.0) -> bool:
        self.stop_event.set()
        self.wake_event.set()
        self.thread.join(timeout=max(0.0, join_timeout))
        return not self.thread.is_alive()

    def _loop(self) -> None:
        while not self.stop_event.is_set():
            claimed = self.store.claim_next(
                owner_id=self.owner_id,
                boot_id=self.boot_id,
                pid=os.getpid(),
                lease_seconds=self.lease_seconds,
            )
            if claimed is None:
                self.wake_event.wait(self.poll_seconds)
                self.wake_event.clear()
                continue
            self.current_job_id = claimed.job_id
            heartbeat_stop = threading.Event()
            heartbeat = threading.Thread(
                target=self._heartbeat_loop,
                args=(claimed.job_id, heartbeat_stop),
                name=f"data-clean-heartbeat-{claimed.job_id}",
                daemon=False,
            )
            heartbeat.start()
            try:
                try:
                    self.run_job(claimed.job_id, claimed.recovering)
                except Exception as exc:  # noqa: BLE001 - keep the managed worker alive.
                    job = self.store.load_job(claimed.job_id)
                    job["status"] = "failed"
                    job["finished_at"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
                    job["failure_reason"] = f"{type(exc).__name__}: {exc}"
                    job["notification"] = "持久 worker 捕获到未处理错误，任务已停止。"
                    self.store.upsert_job(job)
                    self.store.append_event(
                        claimed.job_id,
                        "worker_unhandled_error",
                        {"type": type(exc).__name__, "message": str(exc)},
                    )
            finally:
                heartbeat_stop.set()
                heartbeat.join(timeout=self.heartbeat_seconds + 1)
                self.store.release_lease(claimed.job_id, owner_id=self.owner_id)
                self.current_job_id = None

    def _heartbeat_loop(self, job_id: str, stop: threading.Event) -> None:
        while not stop.wait(self.heartbeat_seconds):
            if not self.store.heartbeat(
                job_id,
                owner_id=self.owner_id,
                lease_seconds=self.lease_seconds,
            ):
                return
