"""Local web UI for normal data-clean interaction.

The web UI is the normal-user entry for building one LeRobot v3 dataset from a
selected raw MCAP batch. Users choose the final LeRobot export parent directory
freely. Sidecar/intermediate artifacts remain under ``asset/.../dev/debug`` or
runtime runs.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import mimetypes
import os
import shutil
import socket
import subprocess
import threading
import time
import uuid
import webbrowser
from dataclasses import asdict
from datetime import datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from repo.config.mcap_process_config import (
    AppConfig,
    calibration_missing_items,
    config_is_calibrated,
    load_app_config,
)
from runtime.forge_bridge_check import run_forge_bridge_check
from runtime.forge_bridge_to_lerobot import convert_forge_bridges_to_lerobot
from runtime.production_config import (
    production_config_view,
    production_readiness,
    save_production_config,
    validate_production_payload,
)
from runtime.scene2_mcap_a_writer import run_scene2_mcap_a_writer
from runtime.scene3_full_flow_check import run_scene3_full_flow_check
from runtime.web_pipeline_config import (
    build_web_job_effective_config,
    load_web_job_effective_config,
)
from schemas.alignment_config import Scene3AlignmentConfig
from schemas.lerobot_features import (
    lerobot_feature_schema,
    tcp_pose_offsets,
)
from service.mcap_io import process_mcap_file
from service.baton_pose_audit import (
    DEFAULT_LEFT_TOPIC,
    DEFAULT_MAX_SAMPLES,
    DEFAULT_RIGHT_TOPIC,
    DEFAULT_SHOW_SAMPLES,
    audit_mcap_file,
    audit_mcap_files,
    move_audit_results,
    summarize_results,
)
from service.training_readiness import (
    build_training_readiness_summary,
    count_flagged_episodes,
    training_readiness_contract_fingerprint,
)


WORKSPACE_DIR = Path("/home/hit/ROS")
DEFAULT_RUN_ROOT = WORKSPACE_DIR / "src/data_clean/runs/web_jobs"
STAGE2_ASSET_ROOT = WORKSPACE_DIR / "asset/阶段二：数据清洗"
DEFAULT_OUTPUT_PARENT = STAGE2_ASSET_ROOT / "prod/exports/lerobot"
SIDECAR_ROOT = STAGE2_ASSET_ROOT / "dev/debug/web_jobs"
PRESETS_DIR = WORKSPACE_DIR / "config/data_clean/presets"
BATON_AUDIT_DIRNAME = "baton_pose_audits"
DEFAULT_GLOBAL_WORKERS = 6
STAGE_NAMES = [
    "夹爪提取",
    "位姿转换",
    "滤波",
    "对齐",
    "数据格式转换",
    "评估报告生成",
]
STAGE_KEYS = {
    "scene1": (0, 1),
    "scene2": (2,),
    "scene3": (3,),
    "bridge": (4,),
    "dataset": (4,),
    "quality": (5,),
}


def _now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _job_id() -> str:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{stamp}_{uuid.uuid4().hex[:8]}"


def _default_dataset_name() -> str:
    return datetime.now().strftime("%Y%m%d_%H")


def _safe_name(raw: str | None, default: str | None = None) -> str:
    text = (raw or default or _default_dataset_name()).strip()
    safe = "".join(char if char.isalnum() or char in {"_", "-"} else "_" for char in text)
    return safe.strip("_-") or _default_dataset_name()


def _suggest_dataset_name(output_parent: Path, requested: str | None) -> str:
    base = _safe_name(requested)
    sidecar_parent = SIDECAR_ROOT
    for index in range(1, 1000):
        candidate = base if index == 1 else f"{base}_{index:03d}"
        if not (output_parent / candidate).exists() and not (sidecar_parent / f"{candidate}_data_clean_sidecar").exists():
            return candidate
    return f"{base}_{uuid.uuid4().hex[:6]}"


def _safe_path(raw: str | None, default: Path = Path("/")) -> Path:
    if not raw:
        return default
    return Path(os.path.expandvars(raw)).expanduser().resolve()


def _format_size(size: int) -> str:
    units = ("B", "KiB", "MiB", "GiB", "TiB")
    value = float(size)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            if unit == "B":
                return f"{int(value)} {unit}"
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{size} B"


def _json_default(value: Any) -> Any:
    if hasattr(value, "to_dict"):
        return value.to_dict()
    if hasattr(value, "__dataclass_fields__"):
        return asdict(value)
    if isinstance(value, Path):
        return str(value)
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def _read_json(path: Path, fallback: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return fallback


def _write_json_atomic(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
    tmp.replace(path)


def _position_bounds(episodes: list[dict[str, Any]], hands: tuple[str, ...]) -> dict[str, list[float]]:
    mins = [float("inf"), float("inf"), float("inf")]
    maxs = [float("-inf"), float("-inf"), float("-inf")]
    found = False
    for episode in episodes:
        for hand in hands:
            for sample in episode.get(hand, []):
                position = sample.get("position", [])
                if len(position) < 3:
                    continue
                found = True
                for axis in range(3):
                    value = float(position[axis])
                    mins[axis] = min(mins[axis], value)
                    maxs[axis] = max(maxs[axis], value)
    if not found:
        mins = [0.0, 0.0, 0.0]
        maxs = [0.0, 0.0, 0.0]
    return {
        "min": mins,
        "max": maxs,
        "center": [(mins[index] + maxs[index]) / 2 for index in range(3)],
    }


def _hydrate_trajectory_metadata(summary: dict[str, Any], bridge_mode: str) -> dict[str, Any]:
    hydrated = dict(summary)
    episodes = hydrated.get("episodes", [])
    if not isinstance(episodes, list):
        episodes = []
    formal = bridge_mode == "formal"
    hydrated.update(
        {
            "coordinate_frame_profile": "dual_arm_base" if formal else "common_frame_compat",
            "coordinate_frames": {
                "left": "left_arm_base" if formal else "common_frame",
                "right": "right_arm_base" if formal else "common_frame",
            },
            "hand_bounds": {
                "left": _position_bounds(episodes, ("left",)),
                "right": _position_bounds(episodes, ("right",)),
            },
            "projection_hint": {
                "coordinate_system": "right-handed",
                "origin_mode": "local_bounds_min",
                "units": "source-values",
            },
        }
    )
    hydrated["bounds"] = _position_bounds(episodes, ("left", "right"))
    return hydrated


def _job_lerobot_features(job: dict[str, Any]) -> dict[str, Any] | None:
    summary = job.get("effective_config_summary")
    if isinstance(summary, dict) and isinstance(summary.get("lerobot_features"), dict):
        return summary["lerobot_features"]
    snapshot_path = job.get("config_snapshot_path")
    if snapshot_path:
        try:
            snapshot = load_web_job_effective_config(Path(str(snapshot_path)))
            return snapshot.lerobot_features_config()
        except Exception:
            return None
    return None


def _tcp_offsets_or_legacy(lerobot_features: dict[str, Any] | None) -> dict[str, tuple[int, int]]:
    try:
        offsets = tcp_pose_offsets(lerobot_features)
        if {"left_tcp_pose", "right_tcp_pose"}.issubset(offsets):
            return offsets
    except Exception:
        pass
    return {"left_tcp_pose": (0, 7), "right_tcp_pose": (7, 14)}


def _state_contract_text(lerobot_features: dict[str, Any] | None) -> str:
    offsets = _tcp_offsets_or_legacy(lerobot_features)
    left = offsets["left_tcp_pose"]
    right = offsets["right_tcp_pose"]
    return f"left state[{left[0]}:{left[1]}], right state[{right[0]}:{right[1]}]"


def _stage(name: str, status: str = "waiting", summary: str = "") -> dict[str, Any]:
    return {
        "name": name,
        "status": status,
        "summary": summary,
        "started_at": None,
        "finished_at": None,
        "duration_ms": None,
        "failure_reason": None,
        "artifacts": [],
    }


def _new_stages() -> list[dict[str, Any]]:
    return [_stage(name) for name in STAGE_NAMES]


def _status_counts(files: list[dict[str, Any]]) -> dict[str, int]:
    counts = {
        "total": len(files),
        "waiting": 0,
        "running": 0,
        "success": 0,
        "warning": 0,
        "failed": 0,
        "skipped": 0,
    }
    for item in files:
        status = item.get("status", "waiting")
        if status in counts:
            counts[status] += 1
    return counts


def _job_progress(job: dict[str, Any]) -> int:
    files = job.get("files", [])
    if not files:
        return 0
    done = sum(1 for item in files if item.get("status") in {"success", "warning", "failed", "skipped"})
    return int(done / len(files) * 100)


def _calibration_info(config: AppConfig) -> dict[str, Any]:
    missing = calibration_missing_items(config)
    return {
        "calibrated": config_is_calibrated(config),
        "missing_items": missing,
        "message": "" if not missing else "当前配置未完整标定，允许继续运行，但结果需要人工复核。",
    }


def _first_error(result: dict[str, Any]) -> str | None:
    errors = result.get("errors")
    if isinstance(errors, list) and errors:
        first = errors[0]
        if isinstance(first, dict):
            return str(first.get("message") or first)
        return str(first)
    return None


class DataCleanWebApp:
    def __init__(
        self,
        *,
        config_path: Path,
        run_root: Path = DEFAULT_RUN_ROOT,
        global_workers: int = DEFAULT_GLOBAL_WORKERS,
    ) -> None:
        self.config_path = config_path
        self.run_root = run_root
        self.jobs_dir = run_root / "jobs"
        self.baton_audits_dir = run_root / BATON_AUDIT_DIRNAME
        self.staging_dir = run_root / "outputs/staging"
        self.settings_path = run_root / "settings.json"
        self.lock = threading.RLock()
        self.global_workers = max(1, global_workers)
        self.worker_budget = threading.BoundedSemaphore(self.global_workers)
        self.jobs: dict[str, dict[str, Any]] = {}
        self.cancel_events: dict[str, threading.Event] = {}
        self.baton_audit_tasks: dict[str, dict[str, Any]] = {}
        self.baton_move_tasks: dict[str, dict[str, Any]] = {}
        self.visualizer_processes: list[subprocess.Popen[str]] = []
        self.gripper_calibration_process: subprocess.Popen[str] | None = None
        self.gripper_calibration_url: str | None = None
        self._load_jobs()

    def _load_jobs(self) -> None:
        self.jobs_dir.mkdir(parents=True, exist_ok=True)
        for path in sorted(self.jobs_dir.glob("*.json")):
            data = _read_json(path, None)
            if not isinstance(data, dict) or not data.get("job_id"):
                continue
            if data.get("status") in {"running", "cancelling"}:
                data["status"] = "failed"
                data["finished_at"] = _now_iso()
                data["failure_reason"] = "服务重启后任务进程已不存在，请用失败文件重新创建任务。"
                data["notification"] = "服务重启后已停止未完成任务。"
                for stage in data.get("stages", []):
                    if stage.get("status") in {"running", "waiting"}:
                        stage["status"] = "failed"
                        stage["failure_reason"] = data["failure_reason"]
                        break
                _write_json_atomic(path, data)
            self.jobs[data["job_id"]] = data

    def _save_job(self, job: dict[str, Any]) -> None:
        job["progress"] = _job_progress(job)
        job["counts"] = _status_counts(job.get("files", []))
        self.jobs[job["job_id"]] = job
        _write_json_atomic(self.jobs_dir / f"{job['job_id']}.json", job)

    def _settings(self) -> dict[str, Any]:
        data = _read_json(self.settings_path, {})
        return data if isinstance(data, dict) else {}

    def _save_settings(self, input_dir: str, output_dir: str) -> None:
        _write_json_atomic(
            self.settings_path,
            {
                "last_input_dir": input_dir,
                "last_output_dir": output_dir,
                "updated_at": _now_iso(),
            },
        )

    def load_config(self, *, input_dir: str | None = None, output_dir: str | None = None, workers: int | None = None) -> AppConfig:
        return load_app_config(
            self.config_path,
            input_dir_override=input_dir,
            output_dir_override=output_dir,
            workers_override=workers,
        )

    def dashboard(self) -> dict[str, Any]:
        with self.lock:
            jobs = sorted(self.jobs.values(), key=lambda item: item.get("created_at", ""), reverse=True)
            running = [self._public_job(job) for job in jobs if job.get("status") in {"running", "cancelling"}]
            recent = [self._public_job(job) for job in jobs[:10]]
        config = self.load_config()
        settings = self._settings()
        readiness = self.production_readiness()
        return {
            "running": running,
            "recent": recent,
            "settings": {
                "last_input_dir": settings.get("last_input_dir", config.batch.input_dir),
                "last_output_dir": settings.get("last_output_dir", str(DEFAULT_OUTPUT_PARENT)),
                "default_dataset_name": _suggest_dataset_name(
                    _safe_path(settings.get("last_output_dir", str(DEFAULT_OUTPUT_PARENT))),
                    _default_dataset_name(),
                ),
                "sidecar_root": str(SIDECAR_ROOT),
                "global_workers": self.global_workers,
            },
            "calibration": _calibration_info(config),
            "production_readiness": readiness,
        }

    def production_config(self) -> dict[str, Any]:
        return {
            **production_config_view(self.config_path),
            "readiness": self.production_readiness(),
        }

    def validate_production_config(self, payload: dict[str, Any]) -> dict[str, Any]:
        return validate_production_payload(payload)

    def save_production_config(self, payload: dict[str, Any]) -> dict[str, Any]:
        saved = save_production_config(self.config_path, payload)
        return {**saved, "readiness": self.production_readiness()}

    def production_readiness(self) -> dict[str, Any]:
        return production_readiness(self.config_path)

    def gripper_calibration_status(self) -> dict[str, Any]:
        process = self.gripper_calibration_process
        running = process is not None and process.poll() is None
        if not running:
            self.gripper_calibration_process = None
            self.gripper_calibration_url = None
        return {
            "running": running,
            "url": self.gripper_calibration_url,
            "readiness": self.production_readiness(),
        }

    def open_gripper_calibration(self) -> dict[str, Any]:
        current = self.gripper_calibration_status()
        if current["running"]:
            return current
        port = self._free_port()
        url = f"http://127.0.0.1:{port}/"
        self.gripper_calibration_process = subprocess.Popen(
            [
                os.environ.get("DATA_CLEAN_PYTHON", os.sys.executable),
                "-m",
                "ui.mcap_calibration_wizard",
                "--config",
                str(self.config_path),
                "--output",
                str(self.config_path),
                "--port",
                str(port),
                "--gripper-only",
                "--no-browser",
            ],
            text=True,
        )
        self.gripper_calibration_url = url
        return {"running": True, "url": url, "readiness": self.production_readiness()}

    def close(self) -> None:
        process = self.gripper_calibration_process
        if process is None or process.poll() is not None:
            return
        process.terminate()
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=3)

    def history(self) -> dict[str, Any]:
        with self.lock:
            jobs = sorted(self.jobs.values(), key=lambda item: item.get("created_at", ""), reverse=True)
            return {"jobs": [self._public_job(job) for job in jobs]}

    def filesystem(self, raw_path: str | None) -> dict[str, Any]:
        path = _safe_path(raw_path)
        if not path.exists():
            parent = path.parent if path.parent.exists() else Path("/")
            return {
                "path": str(path),
                "exists": False,
                "parent": str(parent),
                "entries": [],
                "breadcrumbs": self._breadcrumbs(parent),
            }
        if not path.is_dir():
            path = path.parent
        entries: list[dict[str, Any]] = []
        try:
            for entry in sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
                if entry.is_dir():
                    entries.append({"name": entry.name, "path": str(entry), "is_dir": True})
        except PermissionError:
            return {
                "path": str(path),
                "exists": True,
                "parent": str(path.parent),
                "entries": [],
                "breadcrumbs": self._breadcrumbs(path),
                "error": "permission_denied",
            }
        return {
            "path": str(path),
            "exists": True,
            "parent": str(path.parent),
            "entries": entries,
            "breadcrumbs": self._breadcrumbs(path),
        }

    def _breadcrumbs(self, path: Path) -> list[dict[str, str]]:
        parts: list[dict[str, str]] = [{"name": "/", "path": "/"}]
        current = Path("/")
        for part in path.parts[1:]:
            current = current / part
            parts.append({"name": part, "path": str(current)})
        return parts

    def create_directory(self, payload: dict[str, Any]) -> dict[str, Any]:
        path = _safe_path(str(payload.get("path", "")))
        path.mkdir(parents=True, exist_ok=True)
        return {"path": str(path), "created": True}

    def scan_input_files(self, payload: dict[str, Any]) -> dict[str, Any]:
        input_dir = _safe_path(str(payload.get("input_dir", "")))
        files: list[dict[str, Any]] = []
        if input_dir.is_dir():
            for path in sorted(input_dir.glob("*.mcap"), key=lambda p: p.stat().st_mtime, reverse=True):
                stat = path.stat()
                files.append(
                    {
                        "name": path.name,
                        "path": str(path),
                        "size": stat.st_size,
                        "size_text": _format_size(stat.st_size),
                        "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
                        "status": "waiting",
                        "selected": True,
                    }
                )
        return {"input_dir": str(input_dir), "files": files, "count": len(files)}

    def preview_baton_pose_audit(self, payload: dict[str, Any]) -> dict[str, Any]:
        input_dir = _safe_path(str(payload.get("input_dir", "")))
        raw_files = payload.get("files", [])
        selected = self._normalize_selected_files(raw_files)
        if not selected and not raw_files and input_dir.is_dir():
            selected = sorted(input_dir.glob("*.mcap"), key=lambda p: p.name)
        if not selected:
            raise ValueError("no selected MCAP files")

        left_topic = str(payload.get("left_topic") or DEFAULT_LEFT_TOPIC)
        right_topic = str(payload.get("right_topic") or DEFAULT_RIGHT_TOPIC)
        max_samples = int(payload.get("max_samples") or DEFAULT_MAX_SAMPLES)
        show_samples = int(payload.get("show_samples") or DEFAULT_SHOW_SAMPLES)
        classified_dir = _safe_path(
            str(payload.get("classified_dir") or (input_dir / "_baton_pose_classified")),
            input_dir / "_baton_pose_classified",
        )

        audit_id = _job_id()
        results = audit_mcap_files(
            selected,
            left_topic=left_topic,
            right_topic=right_topic,
            max_samples=max_samples,
            show_samples=show_samples,
        )
        result_dicts = [result.to_dict() for result in results]
        record = {
            "audit_id": audit_id,
            "status": "previewed",
            "created_at": _now_iso(),
            "updated_at": _now_iso(),
            "input_dir": str(input_dir),
            "classified_dir": str(classified_dir),
            "left_topic": left_topic,
            "right_topic": right_topic,
            "max_samples": max_samples,
            "show_samples": show_samples,
            "summary": summarize_results(result_dicts),
            "results": result_dicts,
            "move_results": [],
            "report_path": str(self.baton_audits_dir / f"{audit_id}.json"),
        }
        self.baton_audits_dir.mkdir(parents=True, exist_ok=True)
        _write_json_atomic(self.baton_audits_dir / f"{audit_id}.json", record)
        return record

    def get_baton_pose_audit(self, audit_id: str) -> dict[str, Any]:
        path = self.baton_audits_dir / f"{audit_id}.json"
        if not path.exists():
            raise KeyError(audit_id)
        data = _read_json(path, None)
        if not isinstance(data, dict):
            raise ValueError("audit_record_invalid")
        return data

    def move_baton_pose_audit(self, payload: dict[str, Any]) -> dict[str, Any]:
        audit_id = str(payload.get("audit_id") or "")
        if not audit_id:
            raise ValueError("audit_id is required")
        record = self.get_baton_pose_audit(audit_id)
        classified_dir = _safe_path(
            str(payload.get("classified_dir") or record.get("classified_dir") or ""),
            Path(record.get("input_dir", ".")) / "_baton_pose_classified",
        )
        move_results = move_audit_results(record.get("results", []), classified_dir)
        record["status"] = "moved"
        record["updated_at"] = _now_iso()
        record["classified_dir"] = str(classified_dir)
        record["move_results"] = [asdict(item) for item in move_results]
        record["summary"] = {
            **record.get("summary", {}),
            "moved_count": sum(1 for item in move_results if item.moved),
            "move_failed_count": sum(1 for item in move_results if not item.moved),
        }
        _write_json_atomic(self.baton_audits_dir / f"{audit_id}.json", record)
        return record

    def start_baton_pose_audit(self, payload: dict[str, Any]) -> dict[str, Any]:
        input_dir = _safe_path(str(payload.get("input_dir", "")))
        raw_files = payload.get("files", [])
        selected = self._normalize_selected_files(raw_files)
        if not selected and not raw_files and input_dir.is_dir():
            selected = sorted(input_dir.glob("*.mcap"), key=lambda p: p.name)
        if not selected:
            raise ValueError("no selected MCAP files")

        audit_id = _job_id()
        classified_dir = _safe_path(
            str(payload.get("classified_dir") or (input_dir / "_baton_pose_classified")),
            input_dir / "_baton_pose_classified",
        )
        task = self._new_baton_task(
            audit_id=audit_id,
            operation="audit",
            total=len(selected),
            classified_dir=str(classified_dir),
        )
        with self.lock:
            self.baton_audit_tasks[audit_id] = task
        thread = threading.Thread(
            target=self._run_baton_pose_audit_task,
            args=(
                audit_id,
                selected,
                {
                    "input_dir": str(input_dir),
                    "classified_dir": str(classified_dir),
                    "left_topic": str(payload.get("left_topic") or DEFAULT_LEFT_TOPIC),
                    "right_topic": str(payload.get("right_topic") or DEFAULT_RIGHT_TOPIC),
                    "max_samples": int(payload.get("max_samples") or DEFAULT_MAX_SAMPLES),
                    "show_samples": int(payload.get("show_samples") or DEFAULT_SHOW_SAMPLES),
                },
            ),
            daemon=True,
        )
        thread.start()
        return {"audit_id": audit_id, "task": self._public_baton_task(task)}

    def baton_pose_audit_status(self, audit_id: str) -> dict[str, Any]:
        with self.lock:
            task = self.baton_audit_tasks.get(audit_id)
            if task is not None:
                payload = {"task": self._public_baton_task(task)}
                if task.get("status") == "succeeded" and task.get("record"):
                    payload["record"] = task["record"]
                return payload
        try:
            record = self.get_baton_pose_audit(audit_id)
        except KeyError:
            return {
                "task": self._public_baton_task(
                    {
                        "audit_id": audit_id,
                        "operation": "audit",
                        "status": "failed",
                        "progress": 0,
                        "total": 0,
                        "done": 0,
                        "current_file": None,
                        "started_at": None,
                        "finished_at": _now_iso(),
                        "failure_reason": "任务已中断，请重新开始审计。",
                    }
                )
            }
        return {
            "task": self._public_baton_task(
                {
                    "audit_id": audit_id,
                    "operation": "audit",
                    "status": "succeeded",
                    "progress": 100,
                    "total": int(record.get("summary", {}).get("total", len(record.get("results", [])))),
                    "done": int(record.get("summary", {}).get("total", len(record.get("results", [])))),
                    "current_file": None,
                    "started_at": record.get("created_at"),
                    "finished_at": record.get("updated_at"),
                    "failure_reason": None,
                }
            ),
            "record": record,
        }

    def start_baton_pose_move(self, audit_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        record = self.get_baton_pose_audit(audit_id)
        classified_dir = _safe_path(
            str(payload.get("classified_dir") or record.get("classified_dir") or ""),
            Path(record.get("input_dir", ".")) / "_baton_pose_classified",
        )
        total = len(record.get("results", []))
        task = self._new_baton_task(
            audit_id=audit_id,
            operation="move",
            total=total,
            classified_dir=str(classified_dir),
        )
        with self.lock:
            self.baton_move_tasks[audit_id] = task
        thread = threading.Thread(
            target=self._run_baton_pose_move_task,
            args=(audit_id, record, classified_dir),
            daemon=True,
        )
        thread.start()
        return {"audit_id": audit_id, "task": self._public_baton_task(task)}

    def baton_pose_move_status(self, audit_id: str) -> dict[str, Any]:
        with self.lock:
            task = self.baton_move_tasks.get(audit_id)
            if task is not None:
                payload = {"task": self._public_baton_task(task)}
                if task.get("status") == "succeeded" and task.get("record"):
                    payload["record"] = task["record"]
                return payload
        return {
            "task": self._public_baton_task(
                {
                    "audit_id": audit_id,
                    "operation": "move",
                    "status": "failed",
                    "progress": 0,
                    "total": 0,
                    "done": 0,
                    "current_file": None,
                    "started_at": None,
                    "finished_at": _now_iso(),
                    "failure_reason": "任务已中断，请重新开始审计。",
                }
            )
        }

    def _run_baton_pose_audit_task(self, audit_id: str, selected: list[Path], options: dict[str, Any]) -> None:
        results: list[dict[str, Any]] = []
        try:
            for index, path in enumerate(selected):
                self._update_baton_task(
                    self.baton_audit_tasks,
                    audit_id,
                    current_file=path.name,
                    current_path=str(path),
                )
                result = audit_mcap_file(
                    path,
                    left_topic=options["left_topic"],
                    right_topic=options["right_topic"],
                    max_samples=options["max_samples"],
                    show_samples=options["show_samples"],
                )
                results.append(result.to_dict())
                self._update_baton_task(
                    self.baton_audit_tasks,
                    audit_id,
                    done=index + 1,
                    progress=int((index + 1) / len(selected) * 100),
                )
            record = {
                "audit_id": audit_id,
                "status": "previewed",
                "created_at": self.baton_audit_tasks[audit_id]["started_at"],
                "updated_at": _now_iso(),
                "input_dir": options["input_dir"],
                "classified_dir": options["classified_dir"],
                "left_topic": options["left_topic"],
                "right_topic": options["right_topic"],
                "max_samples": options["max_samples"],
                "show_samples": options["show_samples"],
                "summary": summarize_results(results),
                "results": results,
                "move_results": [],
                "report_path": str(self.baton_audits_dir / f"{audit_id}.json"),
            }
            self.baton_audits_dir.mkdir(parents=True, exist_ok=True)
            _write_json_atomic(self.baton_audits_dir / f"{audit_id}.json", record)
            self._finish_baton_task(self.baton_audit_tasks, audit_id, "succeeded", record=record)
        except Exception as exc:  # noqa: BLE001
            self._finish_baton_task(self.baton_audit_tasks, audit_id, "failed", failure_reason=f"{type(exc).__name__}: {exc}")

    def _run_baton_pose_move_task(self, audit_id: str, record: dict[str, Any], classified_dir: Path) -> None:
        move_results = []
        results = list(record.get("results", []))
        try:
            total = len(results)
            for index, result in enumerate(results):
                source = Path(str(result.get("input_path", "")))
                self._update_baton_task(
                    self.baton_move_tasks,
                    audit_id,
                    current_file=source.name,
                    current_path=str(source),
                )
                move_results.extend(move_audit_results([result], classified_dir))
                self._update_baton_task(
                    self.baton_move_tasks,
                    audit_id,
                    done=index + 1,
                    progress=int((index + 1) / total * 100) if total else 100,
                )
            record["status"] = "moved"
            record["updated_at"] = _now_iso()
            record["classified_dir"] = str(classified_dir)
            record["move_results"] = [asdict(item) for item in move_results]
            record["summary"] = {
                **record.get("summary", {}),
                "moved_count": sum(1 for item in move_results if item.moved),
                "move_failed_count": sum(1 for item in move_results if not item.moved),
            }
            _write_json_atomic(self.baton_audits_dir / f"{audit_id}.json", record)
            self._finish_baton_task(self.baton_move_tasks, audit_id, "succeeded", record=record)
        except Exception as exc:  # noqa: BLE001
            self._finish_baton_task(self.baton_move_tasks, audit_id, "failed", failure_reason=f"{type(exc).__name__}: {exc}")

    def _new_baton_task(self, *, audit_id: str, operation: str, total: int, classified_dir: str) -> dict[str, Any]:
        return {
            "audit_id": audit_id,
            "operation": operation,
            "status": "running",
            "progress": 0,
            "total": total,
            "done": 0,
            "current_file": None,
            "current_path": None,
            "classified_dir": classified_dir,
            "started_at": _now_iso(),
            "finished_at": None,
            "failure_reason": None,
            "record": None,
        }

    def _update_baton_task(self, store: dict[str, dict[str, Any]], audit_id: str, **updates: Any) -> None:
        with self.lock:
            task = store.get(audit_id)
            if task is None:
                return
            task.update(updates)

    def _finish_baton_task(
        self,
        store: dict[str, dict[str, Any]],
        audit_id: str,
        status: str,
        *,
        record: dict[str, Any] | None = None,
        failure_reason: str | None = None,
    ) -> None:
        with self.lock:
            task = store.get(audit_id)
            if task is None:
                return
            task["status"] = status
            task["finished_at"] = _now_iso()
            task["current_file"] = None
            task["current_path"] = None
            task["failure_reason"] = failure_reason
            if status == "succeeded":
                task["progress"] = 100
                task["done"] = task.get("total", 0)
            if record is not None:
                task["record"] = record

    def _public_baton_task(self, task: dict[str, Any]) -> dict[str, Any]:
        public = {key: value for key, value in task.items() if key != "record"}
        started = public.get("started_at")
        finished = public.get("finished_at")
        try:
            if started:
                end = datetime.fromisoformat(finished) if finished else datetime.now().astimezone()
                public["elapsed_ms"] = int((end - datetime.fromisoformat(started)).total_seconds() * 1000)
            else:
                public["elapsed_ms"] = 0
        except ValueError:
            public["elapsed_ms"] = 0
        return public

    def preview_job(self, payload: dict[str, Any]) -> dict[str, Any]:
        input_dir = _safe_path(str(payload.get("input_dir", "")))
        output_parent = _safe_path(str(payload.get("output_dir", "")), DEFAULT_OUTPUT_PARENT)
        raw_files = payload.get("files", [])
        selected = self._normalize_selected_files(raw_files)
        total_size = 0
        for input_path in selected:
            size = input_path.stat().st_size if input_path.exists() else 0
            total_size += size
        requested_name = payload.get("dataset_name") or _default_dataset_name()
        dataset_name = _suggest_dataset_name(output_parent, str(requested_name))
        dataset_dir = output_parent / dataset_name
        sidecar_dir = SIDECAR_ROOT / f"{dataset_name}_data_clean_sidecar"
        bridge_mode = "formal"
        config = self.load_config(input_dir=str(input_dir), output_dir=str(output_parent))
        readiness = self.production_readiness()
        return {
            "input_dir": str(input_dir),
            "output_dir": str(output_parent),
            "output_parent": str(output_parent),
            "dataset_name": dataset_name,
            "dataset_dir": str(dataset_dir),
            "sidecar_dir": str(sidecar_dir),
            "dataset_dir_exists": dataset_dir.exists(),
            "sidecar_dir_exists": sidecar_dir.exists(),
            "mode": bridge_mode,
            "file_count": len(selected),
            "total_size": total_size,
            "total_size_text": _format_size(total_size),
            "targets": [
                {"input_path": str(path), "size": path.stat().st_size if path.exists() else 0}
                for path in selected
            ],
            "conflicts": [
                {"path": str(path), "type": kind}
                for path, kind in ((dataset_dir, "dataset"), (sidecar_dir, "sidecar"))
                if path.exists()
            ],
            "calibration": _calibration_info(config),
            "production_readiness": readiness,
            "global_workers": self.global_workers,
        }

    def create_job(self, payload: dict[str, Any]) -> dict[str, Any]:
        readiness = self.production_readiness()
        if not readiness["ready"]:
            raise ValueError("生产配置未就绪：" + "、".join(readiness["missing_items"]))
        input_dir = _safe_path(str(payload.get("input_dir", "")))
        output_parent = _safe_path(str(payload.get("output_dir", "")), DEFAULT_OUTPUT_PARENT)
        selected = self._normalize_selected_files(payload.get("files", []))
        if not selected:
            raise ValueError("no selected MCAP files")
        output_parent.mkdir(parents=True, exist_ok=True)
        dataset_name = _safe_name(str(payload.get("dataset_name") or _default_dataset_name()))
        dataset_dir = output_parent / dataset_name
        sidecar_dir = SIDECAR_ROOT / f"{dataset_name}_data_clean_sidecar"
        bridge_mode = "formal"
        worker_limit = payload.get("workers", "auto")
        if worker_limit in (None, "", "auto"):
            workers = min(self.global_workers, max(1, len(selected)))
        else:
            workers = max(1, min(int(worker_limit), self.global_workers, len(selected)))
        conflict_policy = str(payload.get("conflict_policy", "overwrite"))
        if conflict_policy not in {"overwrite", "skip"}:
            raise ValueError("conflict_policy must be overwrite or skip")
        if conflict_policy == "skip" and (dataset_dir.exists() or sidecar_dir.exists()):
            raise ValueError("dataset or sidecar already exists; choose overwrite or use a new dataset name")

        job_id = _job_id()
        effective = build_web_job_effective_config(
            default_config_path=self.config_path,
            presets_dir=PRESETS_DIR,
            run_dir=self.run_root / "runs" / job_id,
            preset_name="",
            overrides={},
            bridge_mode=bridge_mode,
            formal_manual_override_confirmed=True,
        )
        files = []
        for input_path in selected:
            files.append(
                {
                    "name": input_path.name,
                    "input_path": str(input_path),
                    "output_path": str(dataset_dir),
                    "status": "waiting",
                    "current_stage": None,
                    "included_in_dataset": False,
                    "episode_count": 0,
                    "stage_outputs": {},
                    "stage_statuses": {},
                    "quality_warnings": [],
                    "failure_reason": None,
                    "warning": None,
                    "started_at": None,
                    "finished_at": None,
                    "duration_ms": None,
                    "report": None,
                }
            )
        job = {
            "job_id": job_id,
            "remark": str(payload.get("remark", "")),
            "status": "running",
            "created_at": _now_iso(),
            "started_at": _now_iso(),
            "finished_at": None,
            "duration_ms": None,
            "input_dir": str(input_dir),
            "output_dir": str(output_parent),
            "output_parent": str(output_parent),
            "dataset_name": dataset_name,
            "dataset_dir": str(dataset_dir),
            "sidecar_dir": str(sidecar_dir),
            "bridge_mode": bridge_mode,
            "calibration_ready": True,
            "preset_name": "",
            "config_overrides": {},
            "config_snapshot_path": str(effective.snapshot_path),
            "scene1_config_path": str(effective.scene1_config_path),
            "effective_config_summary": effective.effective_summary,
            "config_diff": effective.diff,
            "manual_calibration_override": effective.manual_calibration_override,
            "formal_manual_override_confirmed": True,
            "run_endpoint": str(payload.get("run_endpoint", "full")),
            "workers": workers,
            "conflict_policy": conflict_policy,
            "calibration": _calibration_info(self.load_config(input_dir=str(input_dir), output_dir=str(output_parent))),
            "stages": _new_stages(),
            "files": files,
            "dataset_summary": None,
            "quality_summary": None,
            "published": [],
            "backups": [],
            "failure_reason": None,
            "notification": None,
        }
        with self.lock:
            self.cancel_events[job_id] = threading.Event()
            self._save_job(job)
            self._save_settings(str(input_dir), str(output_parent))
        thread = threading.Thread(target=self._run_job, args=(job_id,), daemon=True)
        thread.start()
        return {"job": self._public_job(job)}

    def _normalize_selected_files(self, raw_files: Any) -> list[Path]:
        selected: list[Path] = []
        if not isinstance(raw_files, list):
            return selected
        for item in raw_files:
            raw_path = item.get("path") if isinstance(item, dict) else item
            if not raw_path:
                continue
            path = _safe_path(str(raw_path))
            if path.is_file() and path.suffix == ".mcap":
                selected.append(path)
        return selected

    def _run_job(self, job_id: str) -> None:
        with self.lock:
            job = self.jobs[job_id]
        started = time.monotonic()
        cancel_event = self.cancel_events[job_id]
        staging_root = self.staging_dir / job_id
        dataset_staging = staging_root / "dataset" / job["dataset_name"]
        sidecar_staging = staging_root / "sidecar" / f"{job['dataset_name']}_data_clean_sidecar"
        backup_root = staging_root / "backups"
        dataset_staging.mkdir(parents=True, exist_ok=True)
        sidecar_staging.mkdir(parents=True, exist_ok=True)
        backup_root.mkdir(parents=True, exist_ok=True)

        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=job["workers"]) as executor:
                futures = [
                    executor.submit(self._run_file_flow, job_id, index, sidecar_staging)
                    for index, _item in enumerate(job["files"])
                ]
                for future in concurrent.futures.as_completed(futures):
                    future.result()

            if cancel_event.is_set():
                job["status"] = "cancelled"
                job["notification"] = "任务已取消，已回滚本批次产物。"
                for index, stage in enumerate(job["stages"]):
                    if stage.get("status") in {"running", "waiting"}:
                        self._mark_stage(job, index, "skipped", "任务已取消，本批次产物已回滚。")
                self._rollback_job(job)
            else:
                self._aggregate_file_stages(job)
                successful_bridge_dirs = [
                    item["stage_outputs"]["forge_bridge_dir"]
                    for item in job["files"]
                    if item.get("included_in_dataset") and item.get("stage_outputs", {}).get("forge_bridge_dir")
                ]
                if successful_bridge_dirs:
                    self._mark_stage(job, 4, "running", "正在把成功 bridge episodes 聚合为单个 LeRobot v3 数据集。")
                    with self.lock:
                        self._save_job(job)
                    dataset_result = self.convert_successful_bridges_to_dataset(
                        bridge_dirs=successful_bridge_dirs,
                        output_dir=dataset_staging,
                        fps=float(job["effective_config_summary"]["lerobot"]["fps"]),
                    )
                    job["dataset_summary"] = dataset_result
                    for item in job["files"]:
                        if item.get("included_in_dataset"):
                            item["output_path"] = str(Path(job["dataset_dir"]))
                    self._mark_stage(
                        job,
                        4,
                        "success" if not any(item.get("status") == "failed" for item in job["files"]) else "partial_failed",
                        f"已聚合 {dataset_result['bridge_count']} 个 MCAP，"
                        f"{dataset_result['episodes']} episodes / {dataset_result['frames']} frames。",
                    )
                    self._mark_stage(job, 5, "running", "正在运行 Forge inspect / quality。")
                    with self.lock:
                        self._save_job(job)
                    quality_summary = self.run_dataset_quality_checks(
                        dataset_dir=dataset_staging,
                        reports_dir=sidecar_staging / "reports",
                        fps=float(dataset_result.get("fps", 15.0)),
                        job=job,
                    )
                    replacements = {
                        str(dataset_staging): str(Path(job["dataset_dir"])),
                        str(sidecar_staging): str(Path(job["sidecar_dir"])),
                    }
                    dataset_result = self._rewrite_value_paths(dataset_result, replacements)
                    quality_summary = self._rewrite_value_paths(quality_summary, replacements)
                    job["dataset_summary"] = dataset_result
                    job["quality_summary"] = quality_summary
                    job["files"] = self._rewrite_value_paths(job["files"], replacements)
                    self._rewrite_sidecar_report_paths(sidecar_staging, replacements)
                    quality_status = "success" if not quality_summary.get("warnings") else "partial_failed"
                    self._mark_stage(
                        job,
                        5,
                        quality_status,
                        "质量检查完成；低分或 flags 仅作为警告，不阻止发布。"
                        if quality_summary.get("warnings")
                        else "质量检查完成，未发现阻断性问题。",
                    )
                    (sidecar_staging / "dataset_summary.json").write_text(
                        json.dumps(dataset_result, ensure_ascii=False, indent=2),
                        encoding="utf-8",
                    )
                    sidecar_job_summary = dict(job)
                    sidecar_job_summary.pop("effective_config_summary", None)
                    sidecar_job_summary.pop("config_overrides", None)
                    (sidecar_staging / "job_summary.json").write_text(
                        json.dumps(sidecar_job_summary, ensure_ascii=False, indent=2, default=_json_default),
                        encoding="utf-8",
                    )
                    if cancel_event.is_set():
                        job["status"] = "cancelled"
                        job["notification"] = "任务已取消，已回滚本批次产物。"
                        self._rollback_job(job)
                    else:
                        self._publish_path(job, dataset_staging, Path(job["dataset_dir"]), backup_root)
                        self._publish_path(job, sidecar_staging, Path(job["sidecar_dir"]), backup_root)
                else:
                    self._mark_stage(job, 5, "skipped", "没有成功 bridge episodes，未运行最终数据集评估。")

                counts = _status_counts(job["files"])
                included = sum(1 for item in job["files"] if item.get("included_in_dataset"))
                if included == 0:
                    job["status"] = "failed"
                    job["notification"] = "任务失败，没有 MCAP 成功进入最终数据集。"
                elif counts["failed"]:
                    job["status"] = "partial_failed"
                    job["notification"] = "任务部分完成，成功样本已发布为 LeRobot v3 数据集。"
                else:
                    job["status"] = "succeeded"
                    job["notification"] = "批次数据集构建完成。"
                self._discard_backups(job)
        except Exception as exc:  # noqa: BLE001 - preserve job summary for the UI.
            job["status"] = "failed"
            job["failure_reason"] = f"{type(exc).__name__}: {exc}"
            job["notification"] = "任务失败，已回滚本批次已发布产物。"
            for index, stage in enumerate(job["stages"]):
                if stage.get("status") in {"running", "waiting"}:
                    self._mark_stage(job, index, "failed", job["failure_reason"])
                    break
            self._rollback_job(job)
        finally:
            job["finished_at"] = _now_iso()
            job["duration_ms"] = int((time.monotonic() - started) * 1000)
            shutil.rmtree(staging_root, ignore_errors=True)
            with self.lock:
                self._save_job(job)
                self.cancel_events.pop(job_id, None)

    def _run_file_flow(self, job_id: str, index: int, sidecar_root: Path) -> None:
        with self.lock:
            job = self.jobs[job_id]
            item = job["files"][index]
        cancel_event = self.cancel_events[job_id]
        item_started = time.monotonic()
        stem = _safe_name(Path(item["input_path"]).stem)
        paths = {
            "cleaned_dir": sidecar_root / "01_cleaned" / stem,
            "mcap_a_run_root": sidecar_root / "02_mcap_a" / stem,
            "aligned_dir": sidecar_root / "03_aligned" / stem,
            "bridge_dir": sidecar_root / "04_forge_bridge" / stem,
            "logs_dir": sidecar_root / "logs" / stem,
        }
        for path in paths.values():
            path.mkdir(parents=True, exist_ok=True)
        with self.worker_budget:
            try:
                if cancel_event.is_set():
                    return
                self._update_file(job, item, status="running", started_at=_now_iso())
                cleaned_mcap = self.run_scene1_cleaning_for_file(job, item, paths)
                if cancel_event.is_set():
                    return
                mcap_a_result = self.run_scene2_mcap_a_for_file(job, item, cleaned_mcap, paths)
                if cancel_event.is_set():
                    return
                aligned_result = self.run_scene3_alignment_for_file(job, item, mcap_a_result, paths)
                if cancel_event.is_set():
                    return
                bridge_result = self.run_forge_bridge_for_file(job, item, aligned_result, paths)
                outputs = bridge_result.get("outputs", {})
                self._update_file(
                    job,
                    item,
                    status="success",
                    current_stage="数据格式转换",
                    included_in_dataset=True,
                    episode_count=int(outputs.get("output_step_count", 0)),
                    warning=(
                        "format-only 模式：格式验证数据集，不代表正式训练可用。"
                        if job.get("bridge_mode") == "format-only"
                        else None
                    ),
                )
            except Exception as exc:  # noqa: BLE001 - isolate one MCAP failure.
                stage_statuses = item.setdefault("stage_statuses", {})
                running_keys = [key for key, status in stage_statuses.items() if status == "running"]
                if not running_keys:
                    running_keys = ["scene1"]
                for key in running_keys:
                    stage_statuses[key] = "failed"
                self._update_file(
                    job,
                    item,
                    status="failed",
                    included_in_dataset=False,
                    failure_reason=f"{type(exc).__name__}: {exc}",
                )
            finally:
                self._update_file(
                    job,
                    item,
                    finished_at=_now_iso(),
                    duration_ms=int((time.monotonic() - item_started) * 1000),
                )

    def run_scene1_cleaning_for_file(self, job: dict[str, Any], item: dict[str, Any], paths: dict[str, Path]) -> Path:
        self._mark_file_stage(job, item, "scene1", "running", "夹爪提取 / 位姿转换")
        output_path = paths["cleaned_dir"] / f"{Path(item['input_path']).stem}_cleaned.mcap"
        config = load_app_config(
            job["scene1_config_path"],
            input_dir_override=job["input_dir"],
            output_dir_override=str(paths["cleaned_dir"]),
            workers_override=1,
        )
        report = process_mcap_file(item["input_path"], str(output_path), config)
        item["report"] = report.to_dict()
        item.setdefault("stage_outputs", {})["cleaned_mcap"] = str(output_path)
        if report.status != "success":
            self._mark_file_stage(job, item, "scene1", "failed", "夹爪提取 / 位姿转换")
            raise RuntimeError(report.failure_reason or f"scene1_status_{report.status}")
        self._mark_file_stage(job, item, "scene1", "success", "夹爪提取 / 位姿转换")
        return output_path

    def run_scene2_mcap_a_for_file(
        self,
        job: dict[str, Any],
        item: dict[str, Any],
        cleaned_mcap: Path,
        paths: dict[str, Path],
    ) -> dict[str, Any]:
        self._mark_file_stage(job, item, "scene2", "running", "滤波")
        effective = load_web_job_effective_config(Path(job["config_snapshot_path"]))
        result = run_scene2_mcap_a_writer(
            cleaned_mcap_path=cleaned_mcap,
            config_path=job["scene1_config_path"],
            run_root=paths["mcap_a_run_root"],
            detection_config=effective.detection_config(),
            pose_filter_config=effective.pose_filter_config(),
            tactile_filter_config=effective.tactile_filter_config(),
        )
        item.setdefault("stage_outputs", {}).update(
            {
                "mcap_a": result.get("outputs", {}).get("mcap_a"),
                "mcap_a_summary": result.get("outputs", {}).get("mcap_a_write_summary_json"),
                "scene2_run_dir": result.get("outputs", {}).get("run_dir"),
            }
        )
        if result.get("status") != "success":
            self._mark_file_stage(job, item, "scene2", "failed", "滤波")
            raise RuntimeError(_first_error(result) or "scene2_mcap_a_failed")
        self._mark_file_stage(job, item, "scene2", "success", "滤波")
        return result

    def run_scene3_alignment_for_file(
        self,
        job: dict[str, Any],
        item: dict[str, Any],
        mcap_a_result: dict[str, Any],
        paths: dict[str, Path],
    ) -> dict[str, Any]:
        self._mark_file_stage(job, item, "scene3", "running", "对齐")
        outputs = mcap_a_result.get("outputs", {})
        effective = load_web_job_effective_config(Path(job["config_snapshot_path"]))
        config = effective.alignment_config(output_dir=str(paths["aligned_dir"]))
        result = run_scene3_full_flow_check(
            mcap_a_path=outputs["mcap_a"],
            summary_path=outputs["mcap_a_write_summary_json"],
            output_dir=paths["aligned_dir"],
            config=config,
            run_root=paths["logs_dir"] / "scene3",
        )
        item.setdefault("stage_outputs", {}).update(
            {
                "aligned_mcap": result.get("outputs", {}).get("aligned_mcap"),
                "alignment_index": result.get("outputs", {}).get("alignment_index"),
                "alignment_report": result.get("outputs", {}).get("alignment_report"),
                "aligned_message_count": result.get("outputs", {}).get("aligned_message_count"),
            }
        )
        if result.get("status") != "success":
            self._mark_file_stage(job, item, "scene3", "failed", "对齐")
            raise RuntimeError(_first_error(result) or "scene3_alignment_failed")
        self._mark_file_stage(job, item, "scene3", "success", "对齐")
        return result

    def run_forge_bridge_for_file(
        self,
        job: dict[str, Any],
        item: dict[str, Any],
        aligned_result: dict[str, Any],
        paths: dict[str, Path],
    ) -> dict[str, Any]:
        self._mark_file_stage(job, item, "bridge", "running", "数据格式转换")
        aligned_mcap = aligned_result.get("outputs", {}).get("aligned_mcap")
        bridge_config = job["effective_config_summary"]["bridge"]
        effective = load_web_job_effective_config(Path(job["config_snapshot_path"]))
        result = run_forge_bridge_check(
            aligned_mcap_path=aligned_mcap,
            output_dir=paths["bridge_dir"],
            mode=job.get("bridge_mode", "format-only"),
            pose_source_profile=job.get("bridge_mode", "format-only"),
            calibration_ready=bool(job.get("calibration_ready")),
            max_pose_abs_m=float(bridge_config["max_pose_abs_m"]),
            lerobot_features=effective.lerobot_features_config(),
        )
        outputs = result.get("outputs", {})
        item.setdefault("stage_outputs", {}).update(
            {
                "forge_bridge_dir": str(paths["bridge_dir"]),
                "forge_ready_mcap": outputs.get("forge_ready_mcap"),
                "forge_topic_config": outputs.get("forge_topic_config"),
                "forge_bridge_report": outputs.get("forge_bridge_report"),
                "training_eligible": outputs.get("training_eligible"),
            }
        )
        if result.get("status") != "success":
            self._mark_file_stage(job, item, "bridge", "failed", "数据格式转换")
            raise RuntimeError(_first_error(result) or "forge_bridge_failed")
        self._mark_file_stage(job, item, "bridge", "success", "数据格式转换")
        return result

    def convert_successful_bridges_to_dataset(self, *, bridge_dirs: list[str], output_dir: Path, fps: float) -> dict[str, Any]:
        return convert_forge_bridges_to_lerobot(
            bridge_dirs=bridge_dirs,
            output_dir=output_dir,
            fps=fps,
        )

    def run_dataset_quality_checks(self, *, dataset_dir: Path, reports_dir: Path, fps: float, job: dict[str, Any] | None = None) -> dict[str, Any]:
        reports_dir.mkdir(parents=True, exist_ok=True)
        forge_bin = Path("/home/hit/forge/.venv/bin/forge")
        forge = str(forge_bin) if forge_bin.exists() else "forge"
        inspect_path = reports_dir / "forge_inspect.json"
        quality_path = reports_dir / "forge_quality.json"
        flagged_path = reports_dir / "forge_quality_flagged.json"
        warnings: list[str] = []

        inspect_proc = subprocess.run(
            [forge, "inspect", str(dataset_dir), "--output", "json", "--deep"],
            text=True,
            capture_output=True,
            check=False,
            env={**os.environ, "COLUMNS": "100000"},
        )
        inspect_path.write_text(
            inspect_proc.stdout if inspect_proc.stdout else inspect_proc.stderr,
            encoding="utf-8",
        )
        if inspect_proc.returncode != 0:
            warnings.append(f"forge inspect failed: {inspect_proc.stderr.strip()}")

        quality_proc = subprocess.run(
            [
                forge,
                "quality",
                str(dataset_dir),
                "--fps",
                str(fps),
                "--export",
                str(quality_path),
                "--export-flagged",
                str(flagged_path),
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        if quality_proc.returncode != 0:
            warnings.append(f"forge quality failed: {quality_proc.stderr.strip()}")
            if not quality_path.exists():
                quality_path.write_text(quality_proc.stdout + quality_proc.stderr, encoding="utf-8")
        flagged = _read_json(flagged_path, [])
        flagged_count = count_flagged_episodes(flagged)
        if flagged_count:
            warnings.append(f"quality flagged episodes: {flagged_count}")
        inspect_data = _read_json(inspect_path, {})
        quality_data = _read_json(quality_path, {})
        summary = {
            "inspect_report": str(inspect_path),
            "quality_report": str(quality_path),
            "flagged_report": str(flagged_path) if flagged_path.exists() else None,
            "num_episodes": inspect_data.get("num_episodes") if isinstance(inspect_data, dict) else None,
            "total_frames": inspect_data.get("total_frames") if isinstance(inspect_data, dict) else None,
            "format": inspect_data.get("format") if isinstance(inspect_data, dict) else None,
            "overall_score": quality_data.get("overall_score") if isinstance(quality_data, dict) else None,
            "subscores": quality_data.get("subscores", {}) if isinstance(quality_data, dict) else {},
            "per_episode": quality_data.get("per_episode", []) if isinstance(quality_data, dict) else [],
            "flags": quality_data.get("flags", []) if isinstance(quality_data, dict) else [],
            "recommendations": quality_data.get("recommendations", []) if isinstance(quality_data, dict) else [],
            "flagged_count": flagged_count,
            "warnings": warnings,
        }
        try:
            summary["training_readiness"] = build_training_readiness_summary(
                job=job or {},
                quality_summary=summary,
                dataset_dir=dataset_dir,
                reports_dir=reports_dir,
            )
        except Exception as exc:  # noqa: BLE001
            summary["warnings"].append(f"training readiness summary failed: {type(exc).__name__}: {exc}")
        _write_json_atomic(reports_dir / "quality_visual_summary.json", summary)
        return summary

    def _hydrate_quality_summary(self, job: dict[str, Any]) -> None:
        summary = job.get("quality_summary")
        if isinstance(summary, dict) and "per_episode" in summary:
            self._ensure_training_readiness_summary(job, summary)
            return
        sidecar_dir = Path(job.get("sidecar_dir", ""))
        cache_path = sidecar_dir / "reports" / "quality_visual_summary.json"
        cached = _read_json(cache_path, None)
        if isinstance(cached, dict) and "per_episode" in cached:
            job["quality_summary"] = cached
            self._ensure_training_readiness_summary(job, cached)
            return
        if isinstance(summary, dict) and summary.get("quality_report"):
            quality_path = Path(summary["quality_report"])
        else:
            quality_path = sidecar_dir / "reports" / "forge_quality.json"
        if isinstance(summary, dict) and summary.get("inspect_report"):
            inspect_path = Path(summary["inspect_report"])
        else:
            inspect_path = sidecar_dir / "reports" / "forge_inspect.json"
        if isinstance(summary, dict) and summary.get("flagged_report"):
            flagged_path = Path(summary["flagged_report"])
        else:
            flagged_path = sidecar_dir / "reports" / "forge_quality_flagged.json"
        quality_data = _read_json(quality_path, {})
        inspect_data = _read_json(inspect_path, {})
        flagged = _read_json(flagged_path, [])
        if not isinstance(quality_data, dict):
            return
        hydrated = {
            "inspect_report": str(inspect_path) if inspect_path else None,
            "quality_report": str(quality_path) if quality_path else None,
            "flagged_report": str(flagged_path) if flagged_path.exists() else None,
            "num_episodes": inspect_data.get("num_episodes") if isinstance(inspect_data, dict) else quality_data.get("num_episodes"),
            "total_frames": inspect_data.get("total_frames") if isinstance(inspect_data, dict) else None,
            "format": inspect_data.get("format") if isinstance(inspect_data, dict) else None,
            "overall_score": quality_data.get("overall_score"),
            "subscores": quality_data.get("subscores", {}),
            "per_episode": quality_data.get("per_episode", []),
            "flags": quality_data.get("flags", []),
            "recommendations": quality_data.get("recommendations", []),
            "flagged_count": count_flagged_episodes(flagged),
            "warnings": (summary or {}).get("warnings", []) if isinstance(summary, dict) else [],
        }
        job["quality_summary"] = hydrated
        self._ensure_training_readiness_summary(job, hydrated)
        if sidecar_dir:
            _write_json_atomic(cache_path, hydrated)

    def _ensure_training_readiness_summary(self, job: dict[str, Any], summary: dict[str, Any]) -> None:
        sidecar_dir = Path(job.get("sidecar_dir", ""))
        reports_dir = sidecar_dir / "reports"
        self._refresh_flagged_count(summary, reports_dir)
        expected_fingerprint = training_readiness_contract_fingerprint(job)
        existing = summary.get("training_readiness")
        if (
            isinstance(existing, dict)
            and isinstance(existing.get("storage_media"), dict)
            and existing.get("contract_fingerprint") == expected_fingerprint
        ):
            return
        readiness_path = reports_dir / "training_readiness_summary.json"
        cached = _read_json(readiness_path, None)
        if (
            isinstance(cached, dict)
            and isinstance(cached.get("storage_media"), dict)
            and cached.get("contract_fingerprint") == expected_fingerprint
        ):
            summary["training_readiness"] = cached
            return
        dataset_dir_raw = job.get("dataset_dir") or (job.get("dataset_summary") or {}).get("output_lerobot_v3")
        if not dataset_dir_raw:
            return
        dataset_dir = Path(str(dataset_dir_raw))
        if not dataset_dir.exists() or not reports_dir.exists():
            return
        try:
            summary["training_readiness"] = build_training_readiness_summary(
                job=job,
                quality_summary=summary,
                dataset_dir=dataset_dir,
                reports_dir=reports_dir,
            )
            _write_json_atomic(reports_dir / "quality_visual_summary.json", summary)
        except Exception as exc:  # noqa: BLE001
            warnings = summary.setdefault("warnings", [])
            if isinstance(warnings, list):
                warning = f"training readiness summary failed: {type(exc).__name__}: {exc}"
                if warning not in warnings:
                    warnings.append(warning)

    def _refresh_flagged_count(self, summary: dict[str, Any], reports_dir: Path) -> None:
        flagged_path_raw = summary.get("flagged_report")
        flagged_path = Path(str(flagged_path_raw)) if flagged_path_raw else reports_dir / "forge_quality_flagged.json"
        flagged = _read_json(flagged_path, None)
        summary["flagged_count"] = count_flagged_episodes(flagged)

    def trajectory(self, job_id: str) -> dict[str, Any]:
        with self.lock:
            job = self.jobs.get(job_id)
            if job is None:
                raise KeyError(job_id)
            dataset_dir = Path(job.get("dataset_dir", ""))
            sidecar_dir = Path(job.get("sidecar_dir", ""))
            bridge_mode = str(job.get("bridge_mode", "format-only"))
            lerobot_features = _job_lerobot_features(job)
        cache_path = sidecar_dir / "reports" / "trajectory_summary.json"
        cached = _read_json(cache_path, None)
        if isinstance(cached, dict):
            data = _hydrate_trajectory_metadata(cached, bridge_mode)
            if data != cached and sidecar_dir:
                _write_json_atomic(cache_path, data)
            return data
        data = _hydrate_trajectory_metadata(
            self._build_trajectory_summary(dataset_dir, lerobot_features),
            bridge_mode,
        )
        if sidecar_dir:
            _write_json_atomic(cache_path, data)
        return data

    def _build_trajectory_summary(
        self,
        dataset_dir: Path,
        lerobot_features: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not dataset_dir.exists():
            raise ValueError("dataset_not_found")
        data_files = sorted((dataset_dir / "data").glob("chunk-*/file-*.parquet"))
        if not data_files:
            raise ValueError("lerobot_data_files_not_found")
        try:
            import pyarrow.parquet as pq
        except Exception as exc:  # noqa: BLE001 - user-facing dependency error.
            raise ValueError(f"pyarrow_unavailable: {exc}") from exc

        episodes: dict[int, dict[str, Any]] = {}
        mins = [float("inf"), float("inf"), float("inf")]
        maxs = [float("-inf"), float("-inf"), float("-inf")]
        total_frames = 0
        for parquet_path in data_files:
            table = pq.read_table(parquet_path)
            names = set(table.column_names)
            required = {"episode_index", "frame_index", "timestamp", "observation.state"}
            missing = required - names
            if "observation.state" in missing:
                raise ValueError("observation_state_missing")
            if missing:
                raise ValueError(f"trajectory_columns_missing: {sorted(missing)}")
            episode_col = table["episode_index"]
            frame_col = table["frame_index"]
            timestamp_col = table["timestamp"]
            state_col = table["observation.state"]
            for row_index in range(table.num_rows):
                state = state_col[row_index].as_py()
                if state is None:
                    raise ValueError("observation_state_missing")
                offsets = _tcp_offsets_or_legacy(lerobot_features)
                left_start, left_end = offsets["left_tcp_pose"]
                right_start, right_end = offsets["right_tcp_pose"]
                if len(state) < max(left_end, right_end):
                    raise ValueError("observation_state_too_short")
                episode_index = int(episode_col[row_index].as_py())
                episode = episodes.setdefault(
                    episode_index,
                    {
                        "episode_index": episode_index,
                        "frame_count": 0,
                        "left": [],
                        "right": [],
                    },
                )
                frame = int(frame_col[row_index].as_py())
                timestamp = float(timestamp_col[row_index].as_py())
                left_pose = [float(value) for value in state[left_start:left_end]]
                right_pose = [float(value) for value in state[right_start:right_end]]
                left_position = left_pose[:3]
                left_quaternion = left_pose[3:7]
                right_position = right_pose[:3]
                right_quaternion = right_pose[3:7]
                episode["left"].append(
                    {
                        "frame": frame,
                        "t": timestamp,
                        "position": left_position,
                        "quaternion": left_quaternion,
                    }
                )
                episode["right"].append(
                    {
                        "frame": frame,
                        "t": timestamp,
                        "position": right_position,
                        "quaternion": right_quaternion,
                    }
                )
                episode["frame_count"] += 1
                total_frames += 1
                for point in (left_position, right_position):
                    for axis in range(3):
                        mins[axis] = min(mins[axis], point[axis])
                        maxs[axis] = max(maxs[axis], point[axis])

        if total_frames == 0:
            raise ValueError("lerobot_data_files_not_found")
        center = [(mins[index] + maxs[index]) / 2 for index in range(3)]
        return {
            "dataset_dir": str(dataset_dir),
            "episodes": [episodes[key] for key in sorted(episodes)],
            "total_frames": total_frames,
            "bounds": {
                "min": mins,
                "max": maxs,
                "center": center,
            },
            "state_contract": _state_contract_text(lerobot_features),
            "lerobot_feature_schema": lerobot_feature_schema(lerobot_features),
        }

    def _rewrite_value_paths(self, value: Any, replacements: dict[str, str]) -> Any:
        if isinstance(value, str):
            result = value
            for old, new in replacements.items():
                result = result.replace(old, new)
            return result
        if isinstance(value, list):
            return [self._rewrite_value_paths(item, replacements) for item in value]
        if isinstance(value, dict):
            return {
                key: self._rewrite_value_paths(item, replacements)
                for key, item in value.items()
            }
        return value

    def _rewrite_sidecar_report_paths(self, sidecar_dir: Path, replacements: dict[str, str]) -> None:
        for path in sidecar_dir.rglob("*.json"):
            data = _read_json(path, None)
            if data is None:
                continue
            rewritten = self._rewrite_value_paths(data, replacements)
            _write_json_atomic(path, rewritten)

    def _publish_path(self, job: dict[str, Any], staging_output: Path, target: Path, backup_root: Path) -> None:
        target.parent.mkdir(parents=True, exist_ok=True)
        backup_path = backup_root / f"{uuid.uuid4().hex}_{target.name}"
        backup_record = {"target": str(target), "backup": str(backup_path), "target_existed": target.exists()}
        if target.exists():
            shutil.move(str(target), str(backup_path))
        shutil.move(str(staging_output), str(target))
        job["published"].append(str(target))
        job["backups"].append(backup_record)

    def _rollback_job(self, job: dict[str, Any]) -> None:
        for target_raw in reversed(job.get("published", [])):
            target = Path(target_raw)
            if target.exists():
                if target.is_dir():
                    shutil.rmtree(target)
                else:
                    target.unlink()
        for record in reversed(job.get("backups", [])):
            backup = Path(record["backup"])
            target = Path(record["target"])
            if record.get("target_existed") and backup.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(backup), str(target))

    def _discard_backups(self, job: dict[str, Any]) -> None:
        for record in job.get("backups", []):
            backup = Path(record["backup"])
            if backup.exists():
                if backup.is_dir():
                    shutil.rmtree(backup)
                else:
                    backup.unlink()
        job["backups"] = []

    def _mark_stage(self, job: dict[str, Any], index: int, status: str, summary: str) -> None:
        stage = job["stages"][index]
        if status == "running" and stage["started_at"] is None:
            stage["started_at"] = _now_iso()
        if status in {"success", "partial_failed", "failed", "skipped"}:
            stage["finished_at"] = _now_iso()
            if stage["started_at"]:
                try:
                    start = datetime.fromisoformat(stage["started_at"])
                    end = datetime.fromisoformat(stage["finished_at"])
                    stage["duration_ms"] = int((end - start).total_seconds() * 1000)
                except ValueError:
                    stage["duration_ms"] = None
        stage["status"] = status
        stage["summary"] = summary

    def _mark_file_stage(self, job: dict[str, Any], item: dict[str, Any], key: str, status: str, label: str) -> None:
        item.setdefault("stage_statuses", {})[key] = status
        item["current_stage"] = label
        for stage_index in STAGE_KEYS.get(key, ()):
            if status == "running":
                self._mark_stage(job, stage_index, "running", f"正在执行：{label}")
        with self.lock:
            self._save_job(job)

    def _update_file(self, job: dict[str, Any], item: dict[str, Any], **updates: Any) -> None:
        with self.lock:
            item.update(updates)
            self._save_job(job)

    def _aggregate_file_stages(self, job: dict[str, Any]) -> None:
        summaries = {
            "scene1": "raw MCAP -> cleaned MCAP 完成情况",
            "scene2": "cleaned MCAP -> MCAP_A 完成情况",
            "scene3": "MCAP_A -> aligned MCAP 完成情况",
            "bridge": "aligned MCAP -> Forge bridge 完成情况",
        }
        for key, summary in summaries.items():
            statuses = [item.get("stage_statuses", {}).get(key) for item in job["files"]]
            success = statuses.count("success")
            failed = statuses.count("failed")
            if success and failed:
                status = "partial_failed"
            elif success:
                status = "success"
            elif failed:
                status = "failed"
            else:
                status = "skipped"
            for index in STAGE_KEYS[key]:
                self._mark_stage(job, index, status, f"{summary}：成功 {success}，失败 {failed}。")

    def get_job(self, job_id: str) -> dict[str, Any]:
        with self.lock:
            job = self.jobs.get(job_id)
            if job is None:
                raise KeyError(job_id)
            self._hydrate_quality_summary(job)
            return {"job": self._public_job(job)}

    def cancel_job(self, job_id: str) -> dict[str, Any]:
        with self.lock:
            job = self.jobs.get(job_id)
            if job is None:
                raise KeyError(job_id)
            if job.get("status") not in {"running"}:
                return {"job": self._public_job(job), "message": "任务已经结束。"}
            job["status"] = "cancelling"
            job["notification"] = "正在取消任务，当前文件处理结束后回滚。"
            self.cancel_events.setdefault(job_id, threading.Event()).set()
            self._save_job(job)
            return {"job": self._public_job(job)}

    def retry_failed(self, job_id: str) -> dict[str, Any]:
        with self.lock:
            job = self.jobs.get(job_id)
            if job is None:
                raise KeyError(job_id)
            failed = [item for item in job.get("files", []) if item.get("status") == "failed"]
            return {
                "draft": {
                    "remark": f"重跑失败文件: {job_id}",
                    "input_dir": job.get("input_dir", ""),
                    "output_dir": job.get("output_parent", job.get("output_dir", "")),
                    "dataset_name": _suggest_dataset_name(
                        _safe_path(job.get("output_parent", job.get("output_dir", "")), DEFAULT_OUTPUT_PARENT),
                        f"{job.get('dataset_name', _default_dataset_name())}_retry",
                    ),
                    "bridge_mode": job.get("bridge_mode", "format-only"),
                    "preset_name": job.get("preset_name", ""),
                    "config_overrides": job.get("config_overrides", {}),
                    "files": [{"path": item["input_path"], "name": item["name"]} for item in failed],
                }
            }

    def open_visualizer(self, job_id: str) -> dict[str, Any]:
        with self.lock:
            job = self.jobs.get(job_id)
            if job is None:
                raise KeyError(job_id)
        dataset_dir = Path(job.get("dataset_dir", ""))
        if not dataset_dir.exists():
            raise ValueError("最终数据集目录不存在，无法打开可视化。")
        forge_bin = Path("/home/hit/forge/.venv/bin/forge")
        command = [str(forge_bin) if forge_bin.exists() else "forge"]
        port = self._free_port()
        command.extend(["visualize", str(dataset_dir), "--backend", "web", "--port", str(port)])
        proc = subprocess.Popen(command, text=True)
        self.visualizer_processes.append(proc)
        return {"url": f"http://127.0.0.1:{port}", "message": "已启动 Forge Web Viewer。"}

    def _free_port(self) -> int:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(("127.0.0.1", 0))
            return int(sock.getsockname()[1])

    def delete_history(self, job_id: str) -> dict[str, Any]:
        with self.lock:
            job = self.jobs.get(job_id)
            if job is None:
                raise KeyError(job_id)
            if job.get("status") in {"running", "cancelling"}:
                raise ValueError("运行中的任务不能删除历史。")
            self.jobs.pop(job_id, None)
            path = self.jobs_dir / f"{job_id}.json"
            if path.exists():
                path.unlink()
        return {"deleted": True, "job_id": job_id}

    def _public_job(self, job: dict[str, Any]) -> dict[str, Any]:
        public = dict(job)
        public["progress"] = _job_progress(job)
        public["counts"] = _status_counts(job.get("files", []))
        return public


class DataCleanRequestHandler(BaseHTTPRequestHandler):
    app_state: DataCleanWebApp

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        return

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        try:
            if parsed.path == "/":
                self._send_html(INDEX_HTML)
            elif parsed.path == "/api/dashboard":
                self._send_json(self.app_state.dashboard())
            elif parsed.path == "/api/history":
                self._send_json(self.app_state.history())
            elif parsed.path == "/api/production-config":
                self._send_json(self.app_state.production_config())
            elif parsed.path == "/api/production-readiness":
                self._send_json(self.app_state.production_readiness())
            elif parsed.path == "/api/calibration/gripper/status":
                self._send_json(self.app_state.gripper_calibration_status())
            elif parsed.path == "/api/filesystem":
                query = parse_qs(parsed.query)
                self._send_json(self.app_state.filesystem(query.get("path", ["/"])[0]))
            elif parsed.path.startswith("/api/baton-pose-audit/") and parsed.path.endswith("/move/status"):
                audit_id = parsed.path.split("/")[3]
                self._send_json(self.app_state.baton_pose_move_status(audit_id))
            elif parsed.path.startswith("/api/baton-pose-audit/") and parsed.path.endswith("/status"):
                audit_id = parsed.path.split("/")[3]
                self._send_json(self.app_state.baton_pose_audit_status(audit_id))
            elif parsed.path.startswith("/api/baton-pose-audit/"):
                audit_id = parsed.path.split("/")[3]
                self._send_json(self.app_state.get_baton_pose_audit(audit_id))
            elif parsed.path.startswith("/api/jobs/") and parsed.path.endswith("/trajectory"):
                job_id = parsed.path.split("/")[3]
                self._send_json(self.app_state.trajectory(job_id))
            elif parsed.path.startswith("/api/jobs/"):
                job_id = parsed.path.split("/")[3]
                self._send_json(self.app_state.get_job(job_id))
            else:
                self._send_error(HTTPStatus.NOT_FOUND, "not_found")
        except Exception as exc:  # noqa: BLE001
            self._send_error(HTTPStatus.BAD_REQUEST, str(exc))

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        try:
            payload = self._read_payload()
            if parsed.path == "/api/filesystem/create-directory":
                self._send_json(self.app_state.create_directory(payload))
            elif parsed.path == "/api/production-config/validate":
                self._send_json(self.app_state.validate_production_config(payload))
            elif parsed.path == "/api/production-config":
                self._send_json(self.app_state.save_production_config(payload))
            elif parsed.path == "/api/calibration/gripper/open":
                self._send_json(self.app_state.open_gripper_calibration())
            elif parsed.path == "/api/input-files/scan":
                self._send_json(self.app_state.scan_input_files(payload))
            elif parsed.path == "/api/baton-pose-audit/start":
                self._send_json(self.app_state.start_baton_pose_audit(payload))
            elif parsed.path.startswith("/api/baton-pose-audit/") and parsed.path.endswith("/move/start"):
                audit_id = parsed.path.split("/")[3]
                self._send_json(self.app_state.start_baton_pose_move(audit_id, payload))
            elif parsed.path == "/api/baton-pose-audit/preview":
                self._send_json(self.app_state.preview_baton_pose_audit(payload))
            elif parsed.path == "/api/baton-pose-audit/move":
                self._send_json(self.app_state.move_baton_pose_audit(payload))
            elif parsed.path == "/api/jobs/preview":
                self._send_json(self.app_state.preview_job(payload))
            elif parsed.path == "/api/jobs":
                self._send_json(self.app_state.create_job(payload))
            elif parsed.path.startswith("/api/jobs/") and parsed.path.endswith("/cancel"):
                job_id = parsed.path.split("/")[3]
                self._send_json(self.app_state.cancel_job(job_id))
            elif parsed.path.startswith("/api/jobs/") and parsed.path.endswith("/retry-failed"):
                job_id = parsed.path.split("/")[3]
                self._send_json(self.app_state.retry_failed(job_id))
            elif parsed.path.startswith("/api/jobs/") and parsed.path.endswith("/open-visualizer"):
                job_id = parsed.path.split("/")[3]
                self._send_json(self.app_state.open_visualizer(job_id))
            else:
                self._send_error(HTTPStatus.NOT_FOUND, "not_found")
        except Exception as exc:  # noqa: BLE001
            self._send_error(HTTPStatus.BAD_REQUEST, str(exc))

    def do_DELETE(self) -> None:
        parsed = urlparse(self.path)
        try:
            if parsed.path.startswith("/api/history/"):
                job_id = parsed.path.split("/")[3]
                self._send_json(self.app_state.delete_history(job_id))
            else:
                self._send_error(HTTPStatus.NOT_FOUND, "not_found")
        except Exception as exc:  # noqa: BLE001
            self._send_error(HTTPStatus.BAD_REQUEST, str(exc))

    def _read_payload(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        if length == 0:
            return {}
        raw = self.rfile.read(length)
        data = json.loads(raw.decode("utf-8"))
        if not isinstance(data, dict):
            raise ValueError("JSON payload must be an object")
        return data

    def _send_html(self, html: str) -> None:
        data = html.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_json(self, payload: Any) -> None:
        data = json.dumps(payload, ensure_ascii=False, default=_json_default).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_error(self, status: HTTPStatus, message: str) -> None:
        data = json.dumps({"error": message}, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", mimetypes.types_map.get(".json", "application/json"))
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


INDEX_HTML = r"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>数据清洗看板</title>
  <style>
    :root { color-scheme: light; --blue:#2563eb; --bg:#f5f7fb; --card:#fff; --muted:#667085; --line:#e4e7ec; --bad:#b42318; --ok:#027a48; --warn:#b54708; }
    * { box-sizing: border-box; }
    body { margin:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; background:var(--bg); color:#101828; }
    header { display:flex; align-items:center; justify-content:space-between; padding:16px 28px; background:#0f172a; color:white; }
    header h1 { margin:0; font-size:20px; }
    nav button { margin-left:8px; border:0; border-radius:8px; padding:8px 12px; cursor:pointer; background:#1e293b; color:white; }
    nav button.active { background:var(--blue); }
    main { padding:24px; }
    .card { background:var(--card); border:1px solid var(--line); border-radius:14px; padding:18px; box-shadow:0 1px 2px rgba(16,24,40,.04); margin-bottom:16px; }
    .row { display:flex; gap:12px; align-items:center; flex-wrap:wrap; }
    .split { display:grid; grid-template-columns: 390px 1fr; gap:18px; align-items:start; }
    label { display:block; font-weight:650; margin:12px 0 6px; }
    input, select { width:100%; padding:10px 12px; border:1px solid var(--line); border-radius:10px; background:white; }
    button { border:0; border-radius:10px; padding:10px 14px; cursor:pointer; background:#e5e7eb; color:#111827; font-weight:650; }
    button.primary { background:var(--blue); color:white; }
    button.danger { background:#fee4e2; color:var(--bad); }
    button.ghost { background:#f2f4f7; color:#344054; }
    button:disabled { opacity:.55; cursor:not-allowed; }
    table { width:100%; border-collapse:collapse; font-size:14px; }
    th, td { border-bottom:1px solid var(--line); padding:9px; text-align:left; vertical-align:top; }
    th { color:#475467; font-size:12px; }
    .badge { display:inline-flex; border-radius:999px; padding:4px 9px; font-size:12px; font-weight:700; background:#eef2ff; color:#3730a3; }
    .running { background:#dbeafe; color:#1d4ed8; }
    .succeeded, .success { background:#dcfae6; color:var(--ok); }
    .unit_consistent_likely, .normal { background:#dcfae6; color:var(--ok); }
    .unit_mismatch_suspected, .unit_mismatch { background:#fef0c7; color:var(--warn); }
    .missing_pose_topic, .pose_value_invalid_suspected, .decode_failed, .other_issue { background:#fee4e2; color:var(--bad); }
    .partial_failed, .warning, .partial { background:#fef0c7; color:var(--warn); }
    .failed { background:#fee4e2; color:var(--bad); }
    .cancelled, .skipped { background:#f2f4f7; color:#475467; }
    .muted { color:var(--muted); }
    .notice { padding:12px 14px; border-radius:12px; background:#eff8ff; border:1px solid #b2ddff; margin-bottom:14px; }
    .warnbox { padding:12px; border-radius:12px; background:#fffaeb; border:1px solid #fedf89; color:#93370d; }
    .config-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(260px,1fr)); gap:10px; margin-top:10px; }
    .config-section { border:1px solid var(--line); border-radius:12px; padding:12px; background:#f8fafc; }
    .config-section label { font-size:13px; }
    .config-section .enable { display:flex; gap:8px; align-items:center; margin:0 0 8px; }
    .config-section .enable input { width:auto; }
    .config-errors { color:var(--bad); }
    .grid { display:grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap:12px; }
    .stage { border:1px solid var(--line); border-radius:12px; padding:12px; background:#fff; }
    .progress { height:10px; background:#eaecf0; border-radius:999px; overflow:hidden; }
    .progress > div { height:100%; background:var(--blue); width:0%; transition:width .2s; }
    .tabs { display:flex; gap:8px; margin:16px 0; }
    .tabs button.active { background:var(--blue); color:white; }
    .score-grid { display:grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap:12px; }
    .score-card { border:1px solid var(--line); border-radius:12px; padding:12px; background:#fff; }
    .score-track { height:10px; border-radius:999px; background:#eaecf0; overflow:hidden; margin-top:8px; }
    .score-fill { height:100%; border-radius:999px; }
    .score-good { background:#12b76a; }
    .score-warn { background:#f79009; }
    .score-bad { background:#f04438; }
    .readiness-hero { border:1px solid var(--line); border-radius:8px; padding:16px; margin-bottom:16px; background:#fff; }
    .readiness-hero.pass { border-color:#abefc6; background:#f6fef9; }
    .readiness-hero.review { border-color:#fedf89; background:#fffcf5; }
    .readiness-hero.block { border-color:#fecdca; background:#fffbfa; }
    .readiness-title { margin:0; font-size:22px; }
    .readiness-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:10px; margin:14px 0; }
    .readiness-module { border:1px solid var(--line); border-radius:8px; padding:12px; background:#fff; min-height:116px; }
    .readiness-module.pass { border-color:#abefc6; }
    .readiness-module.review { border-color:#fedf89; }
    .readiness-module.block { border-color:#fecdca; }
    .readiness-module.info { border-color:#d0d5dd; background:#f9fafb; }
    .readiness-module h4 { margin:0 0 8px; }
    .risk-list, .action-list { margin:8px 0 0; padding-left:18px; }
    .metric-note { color:var(--muted); font-size:13px; margin-top:8px; }
    .dim-pill { display:inline-flex; border-radius:999px; padding:3px 8px; margin:2px; background:#f2f4f7; color:#344054; font-size:12px; font-weight:650; }
    .readiness-status { display:inline-flex; align-items:center; border-radius:999px; padding:5px 10px; font-size:13px; font-weight:750; }
    .readiness-status.pass { background:#dcfae6; color:var(--ok); }
    .readiness-status.review { background:#fef0c7; color:var(--warn); }
    .readiness-status.block { background:#fee4e2; color:var(--bad); }
    .readiness-status.info { background:#eef2ff; color:#3730a3; }
    .detail-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(280px,1fr)); gap:12px; }
    .trajectory-layout { display:grid; grid-template-columns: minmax(0, 1fr) 300px; gap:16px; align-items:start; }
    .trajectory-canvas { width:100%; height:620px; border:1px solid var(--line); border-radius:14px; background:#0b1020; display:block; }
    .trajectory-dual { display:grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap:12px; }
    .trajectory-dual .trajectory-canvas { height:620px; }
    .trajectory-panel-title { margin:0 0 8px; color:var(--muted); font-size:13px; }
    .trajectory-playback { margin-top:14px; padding-top:12px; border-top:1px solid var(--line); }
    .trajectory-playback input[type="range"] { padding:0; }
    .legend-dot { display:inline-block; width:10px; height:10px; border-radius:999px; margin-right:6px; }
    .modal { position:fixed; inset:0; background:rgba(15,23,42,.45); display:none; align-items:center; justify-content:center; padding:24px; z-index:10; }
    .modal.open { display:flex; }
    .modal-card { width:min(860px, 96vw); max-height:86vh; overflow:auto; background:white; border-radius:16px; padding:18px; }
    .dir-list button { display:block; width:100%; text-align:left; margin:4px 0; background:#f8fafc; }
    .right { margin-left:auto; }
    .path { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size:12px; word-break:break-all; }
    .hidden { display:none; }
  </style>
</head>
<body>
<header>
  <h1>数据清洗网页交互</h1>
  <nav>
    <button id="nav-dashboard" onclick="showPage('dashboard')">看板</button>
    <button id="nav-create" onclick="showPage('create')">新建任务</button>
    <button id="nav-audit" onclick="showPage('audit')">位姿审计</button>
    <button id="nav-config" onclick="showPage('config')">配置中心</button>
    <button id="nav-history" onclick="showPage('history')">历史记录</button>
  </nav>
</header>
<main>
  <div id="notice"></div>
  <section id="page-dashboard"></section>
  <section id="page-create" class="hidden"></section>
  <section id="page-audit" class="hidden"></section>
  <section id="page-config" class="hidden"></section>
  <section id="page-job" class="hidden"></section>
  <section id="page-history" class="hidden"></section>
</main>
<div id="dir-modal" class="modal"><div class="modal-card">
  <div class="row"><h3 id="dir-title">选择目录</h3><button class="right" onclick="closeDirModal()">关闭</button></div>
  <div class="row"><input id="dir-path"><button onclick="loadDir(document.getElementById('dir-path').value)">打开</button><button onclick="createDirFromInput()">新建此目录</button></div>
  <div id="dir-breadcrumbs" class="row muted"></div>
  <div id="dir-list" class="dir-list"></div>
  <div class="row"><button onclick="selectCurrentDir()" class="primary">选择当前目录</button></div>
</div></div>
<div id="confirm-modal" class="modal"><div class="modal-card" id="confirm-body"></div></div>
<script>
let state = {page:'dashboard', dashboard:null, history:null, files:[], selected:new Set(), auditFiles:[], auditSelected:new Set(), auditPreview:null, auditTask:null, auditMoveTask:null, auditPollTimer:null, currentJob:null, jobTab:'quality', trajectory:null, trajectoryEpisode:'all', trajectoryView:{zoom:1, showLeft:true, showRight:true, showMarkers:true, showAxes:true}, trajectoryPlayback:{playing:false, frameIndex:0, speed:1, rafId:null, wallStartedAt:null, mediaStartedAt:null}, dirTarget:null, dirPath:'/', preview:null, retryDraft:null, productionConfig:null};
const statusText = {running:'运行中', succeeded:'成功', partial_failed:'部分失败', failed:'失败', cancelled:'已取消', cancelling:'取消中', waiting:'等待', success:'成功', warning:'成功但有警告', skipped:'跳过', unit_consistent_likely:'正常', unit_mismatch_suspected:'单位疑似不统一', missing_pose_topic:'缺少位姿 topic', pose_value_invalid_suspected:'位姿值异常', decode_failed:'读取失败', normal:'正常', unit_mismatch:'单位异常', other_issue:'其他异常'};
async function api(path, opts={}) {
  const res = await fetch(path, {headers:{'Content-Type':'application/json'}, ...opts});
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || res.statusText);
  return data;
}
function badge(s) { return `<span class="badge ${s}">${statusText[s] || s}</span>`; }
function fmtMs(ms) { if (!ms) return '-'; return ms < 1000 ? `${ms} ms` : `${(ms/1000).toFixed(1)} s`; }
function setNotice(text, kind='notice') { document.getElementById('notice').innerHTML = text ? `<div class="${kind}">${text}</div>` : ''; }
function showPage(page) {
  if (page !== 'job') stopTrajectoryPlayback();
  state.page = page;
  for (const id of ['dashboard','create','audit','config','job','history']) document.getElementById(`page-${id}`).classList.toggle('hidden', id !== page);
  for (const id of ['dashboard','create','audit','config','history']) document.getElementById(`nav-${id}`).classList.toggle('active', id === page);
  if (page === 'dashboard') loadDashboard();
  if (page === 'create') renderCreate();
  if (page === 'audit') renderAudit();
  if (page === 'config') loadProductionConfig();
  if (page === 'history') loadHistory();
}
async function loadDashboard() {
  state.dashboard = await api('/api/dashboard');
  renderDashboard();
}
function renderDashboard() {
  const d = state.dashboard;
  const running = d.running.map(jobCard).join('') || '<p class="muted">当前没有运行中的任务。</p>';
  const recent = d.recent.map(jobRow).join('') || '<tr><td class="muted">暂无历史</td></tr>';
  document.getElementById('page-dashboard').innerHTML = `
    <div class="card row"><div><h2>任务看板</h2><p class="muted">正常模式只展示生产交互；开发者检验请使用 <code>./start_data_clean.sh --dev</code>。</p></div><button class="primary right" onclick="showPage('create')">新建清洗任务</button></div>
    <div class="card"><h3>运行中的批次</h3>${running}</div>
    <div class="card"><h3>最近历史</h3><table><tbody>${recent}</tbody></table></div>`;
}
function jobCard(job) {
  return `<div class="card"><div class="row"><b>${job.remark || job.job_id}</b>${badge(job.status)}<button class="right" onclick="openJob('${job.job_id}')">查看详情</button></div><div class="progress"><div style="width:${job.progress}%"></div></div><p class="muted">${job.input_dir} -> ${job.dataset_dir || job.output_dir}</p></div>`;
}
function jobRow(job) {
  const included = (job.files || []).filter(f => f.included_in_dataset).length;
  return `<tr><td><b>${job.remark || job.job_id}</b><br><span class="muted">${job.created_at}</span></td><td>${badge(job.status)}</td><td>${included}/${job.counts.total} 纳入数据集</td><td><button onclick="openJob('${job.job_id}')">查看</button></td></tr>`;
}
function renderCreate() {
  const s = state.dashboard?.settings || {};
  const input = state.retryDraft?.input_dir || s.last_input_dir || '';
  const output = state.retryDraft?.output_dir || s.last_output_dir || '';
  const datasetName = state.retryDraft?.dataset_name || s.default_dataset_name || '';
  const remark = state.retryDraft?.remark || '';
  const ready = state.dashboard?.production_readiness || {ready:false, missing_items:['正在读取生产配置']};
  const readinessBox = ready.ready
    ? '<div class="notice" style="margin-top:14px">生产配置已就绪：任务将使用左右 arm-base TCP 位姿构建训练数据集。</div>'
    : `<div class="warnbox" style="margin-top:14px">生产配置未就绪：${(ready.missing_items || []).map(escapeHtml).join('、')}。<br><button onclick="showPage('config')">进入配置中心</button></div>`;
  document.getElementById('page-create').innerHTML = `
    <div class="split">
      <div class="card">
        <h2>新建清洗任务</h2>
        <label>备注（可选）</label><input id="remark" value="${escapeHtml(remark)}" placeholder="例如：上午采集样本">
        <label>数据集名称</label><input id="dataset-name" value="${escapeHtml(datasetName)}" oninput="previewJob()" placeholder="YYYYMMDD_HH">
        <label>输入目录</label><div class="row"><input id="input-dir" value="${escapeHtml(input)}"><button onclick="openDirModal('input')">浏览</button></div>
        <label>输出父目录（LeRobot export）</label><div class="row"><input id="output-dir" value="${escapeHtml(output)}" oninput="previewJob()"><button onclick="openDirModal('output')">浏览</button></div>
        ${readinessBox}
        <details><summary>高级设置</summary>
          <label>运行终点</label><select id="run-endpoint"><option value="full">完整批次数据集构建</option></select>
          <label>当前批次 worker</label><input id="workers" value="auto" placeholder="auto 或正整数">
        </details>
        <div class="row" style="margin-top:14px"><button onclick="scanFiles()" class="primary">扫描 MCAP</button></div>
      </div>
      <div class="card">
        <div class="row"><h2>文件选择与预览</h2><button class="right" onclick="scanFiles()">刷新</button></div>
        <div class="row"><input id="file-search" placeholder="搜索文件名" oninput="renderFileTable()"><button onclick="selectAll(true)">全选</button><button onclick="selectAll(false)">全不选</button><button onclick="invertSelection()">反选</button></div>
        <div id="file-table"></div>
        <div id="preview-box"></div>
      </div>
    </div>`;
  if (state.retryDraft) {
    state.files = state.retryDraft.files.map(f => ({name:f.name, path:f.path, size:0, size_text:'-', modified_at:'-', status:'waiting'}));
    state.selected = new Set(state.files.map(f => f.path));
    state.retryDraft = null;
    renderFileTable();
  }
}
function renderAudit() {
  const s = state.dashboard?.settings || {};
  const input = document.getElementById('audit-input-dir')?.value || s.last_input_dir || '/home/hit/下载/mcap';
  const classified = document.getElementById('audit-classified-dir')?.value || `${input.replace(/\/$/,'')}/_baton_pose_classified`;
  const disabled = auditBusy() ? 'disabled' : '';
  document.getElementById('page-audit').innerHTML = `
    <div class="split">
      <div class="card">
        <h2>Baton Mini 位姿审计</h2>
        <p class="muted">检查 raw MCAP 中左右 Baton Mini 位姿 topic 的 xyz 和四元数数值，按左右量级是否统一给文件分类。审计不会移动文件；只有确认移动后才会改动 MCAP 位置。</p>
        <label>输入目录</label><div class="row"><input id="audit-input-dir" value="${escapeHtml(input)}" oninput="auditInputChanged()" ${disabled}><button onclick="openDirModal('audit-input')" ${disabled}>浏览</button></div>
        <label>分类目标目录</label><div class="row"><input id="audit-classified-dir" value="${escapeHtml(classified)}" ${disabled}><button onclick="openDirModal('audit-classified')" ${disabled}>浏览</button></div>
        <label>左手位姿 topic</label><input id="audit-left-topic" value="/baton_mini_left/fast_odom" ${disabled}>
        <label>右手位姿 topic</label><input id="audit-right-topic" value="/baton_mini_right/fast_odom" ${disabled}>
        <details><summary>高级参数</summary>
          <label>每侧最大采样数</label><input id="audit-max-samples" value="1000" ${disabled}>
          <p class="muted">页面固定展示前 3 条原始位姿；完整统计写入审计 JSON。</p>
        </details>
        <div class="row" style="margin-top:14px"><button id="audit-scan-btn" class="primary" onclick="scanAuditFiles()" ${disabled}>扫描 MCAP</button><button id="audit-start-btn" onclick="runBatonAudit()" ${disabled}>开始审计</button></div>
      </div>
      <div class="card">
        <div class="row"><h2>文件选择</h2><button class="right" onclick="scanAuditFiles()" ${disabled}>刷新</button></div>
        <div class="row"><input id="audit-file-search" placeholder="搜索文件名" oninput="renderAuditFileTable()" ${disabled}><button onclick="selectAuditAll(true)" ${disabled}>全选</button><button onclick="selectAuditAll(false)" ${disabled}>全不选</button><button onclick="invertAuditSelection()" ${disabled}>反选</button></div>
        <div id="audit-file-table"></div>
      </div>
    </div>
    <div id="audit-result"></div>`;
  renderAuditFileTable();
  renderAuditResult();
}
function auditInputChanged() {
  const input = document.getElementById('audit-input-dir')?.value || '';
  const classified = document.getElementById('audit-classified-dir');
  if (classified && input) classified.value = `${input.replace(/\/$/,'')}/_baton_pose_classified`;
}
async function scanAuditFiles() {
  if (auditBusy()) return;
  const inputDir = document.getElementById('audit-input-dir').value;
  const data = await api('/api/input-files/scan', {method:'POST', body:JSON.stringify({input_dir:inputDir})});
  state.auditFiles = data.files;
  state.auditSelected = new Set(data.files.map(f => f.path));
  state.auditPreview = null;
  renderAuditFileTable();
  renderAuditResult();
}
function renderAuditFileTable() {
  const host = document.getElementById('audit-file-table');
  if (!host) return;
  const disabled = auditBusy() ? 'disabled' : '';
  const q = (document.getElementById('audit-file-search')?.value || '').toLowerCase();
  const files = state.auditFiles.filter(f => f.name.toLowerCase().includes(q)).sort((a,b)=>a.name.localeCompare(b.name));
  const rows = files.map(f => `<tr><td><input type="checkbox" ${state.auditSelected.has(f.path)?'checked':''} onchange="toggleAuditFile('${jsEscape(f.path)}', this.checked)" ${disabled}></td><td>${escapeHtml(f.name)}</td><td>${f.size_text}</td><td>${f.modified_at}</td></tr>`).join('');
  host.innerHTML = `<table><thead><tr><th></th><th>名称</th><th>大小</th><th>修改时间</th></tr></thead><tbody>${rows || '<tr><td colspan="4" class="muted">未扫描到 .mcap 文件</td></tr>'}</tbody></table>`;
}
function toggleAuditFile(path, checked) { if (auditBusy()) return; checked ? state.auditSelected.add(path) : state.auditSelected.delete(path); renderAuditFileTable(); }
function selectAuditAll(on) { if (auditBusy()) return; state.auditFiles.forEach(f => on ? state.auditSelected.add(f.path) : state.auditSelected.delete(f.path)); renderAuditFileTable(); }
function invertAuditSelection() { if (auditBusy()) return; state.auditFiles.forEach(f => state.auditSelected.has(f.path) ? state.auditSelected.delete(f.path) : state.auditSelected.add(f.path)); renderAuditFileTable(); }
async function runBatonAudit() {
  const files = [...state.auditSelected].map(path => ({path}));
  if (!files.length) { alert('请选择至少一个 MCAP 文件。'); return; }
  if (auditBusy()) return;
  const payload = {
    input_dir:document.getElementById('audit-input-dir').value,
    classified_dir:document.getElementById('audit-classified-dir').value,
    left_topic:document.getElementById('audit-left-topic').value,
    right_topic:document.getElementById('audit-right-topic').value,
    max_samples:Number(document.getElementById('audit-max-samples').value || 1000),
    files,
  };
  state.auditPreview = null;
  state.auditMoveTask = null;
  setNotice('正在审计 Baton Mini 位姿 topic...', 'notice');
  const data = await api('/api/baton-pose-audit/start', {method:'POST', body:JSON.stringify(payload)});
  state.auditTask = data.task;
  renderAuditResult();
  renderAuditFileTable();
  pollBatonAudit(data.task.audit_id);
}
async function pollBatonAudit(auditId) {
  clearAuditPoll();
  state.auditPollTimer = setInterval(async () => {
    try {
      const data = await api(`/api/baton-pose-audit/${auditId}/status`);
      state.auditTask = data.task;
      if (data.task.status === 'succeeded') {
        clearAuditPoll();
        state.auditPreview = data.record;
        state.auditTask = null;
        setNotice('位姿审计完成。请先查看分类结果，再决定是否移动。');
        renderAuditFileTable();
      } else if (data.task.status === 'failed') {
        clearAuditPoll();
        setNotice(`位姿审计失败：${escapeHtml(data.task.failure_reason || '')}`, 'warnbox');
        renderAuditFileTable();
      }
      renderAuditResult();
    } catch (error) {
      clearAuditPoll();
      state.auditTask = {status:'failed', failure_reason:'任务已中断，请重新开始审计。', progress:0, done:0, total:0, operation:'audit'};
      setNotice('位姿审计任务已中断，请重新开始审计。', 'warnbox');
      renderAuditFileTable();
      renderAuditResult();
    }
  }, 500);
}
function renderAuditResult() {
  const host = document.getElementById('audit-result');
  if (!host) return;
  if (state.auditTask) {
    host.innerHTML = progressCard(state.auditTask, '正在审计 Baton Mini 位姿 topic');
    return;
  }
  if (state.auditMoveTask) {
    host.innerHTML = progressCard(state.auditMoveTask, '正在移动分类 MCAP');
    return;
  }
  const audit = state.auditPreview;
  if (!audit) {
    host.innerHTML = '<div class="card"><h3>审计结果</h3><p class="muted">扫描并选择 MCAP 后，点击“开始审计”。</p></div>';
    return;
  }
  const summary = audit.summary || {};
  const counts = summary.status_counts || {};
  const moveCounts = summary.move_group_counts || {};
  const warning = summary.has_unit_mismatch ? `<div class="warnbox"><b>发现单位疑似不统一：</b>${counts.unit_mismatch_suspected || 0} 个 MCAP 将归入 unit_mismatch。</div>` : '';
  const moved = (audit.move_results || []).length > 0;
  const rows = (audit.results || []).map(item => auditResultRow(item, audit.move_results || [])).join('');
  host.innerHTML = `<div class="card">
    <div class="row"><div><h3>审计结果</h3><p class="path">${escapeHtml(audit.report_path || '')}</p></div>${badge(audit.status || 'success')}<button class="primary right" onclick="openAuditMoveConfirm()" ${moved || auditBusy()?'disabled':''}>确认移动分类</button></div>
    ${warning}
    <p><b>文件：</b>${summary.total || 0} 个 <b>正常：</b>${moveCounts.normal || 0} <b>单位异常：</b>${moveCounts.unit_mismatch || 0} <b>其他异常：</b>${moveCounts.other_issue || 0}</p>
    <p><b>分类目录：</b><span class="path">${escapeHtml(audit.classified_dir || '')}</span></p>
    <p class="muted">${escapeHtml(summary.unit_note || '')}</p>
    ${moved ? `<div class="notice">已移动 ${summary.moved_count || 0} 个文件，失败 ${summary.move_failed_count || 0} 个。</div>` : ''}
    <table><thead><tr><th>文件</th><th>分类</th><th>移动目录</th><th>左右数量</th><th>median / p95 比值</th><th>左手统计</th><th>右手统计</th><th>前 3 条原始位姿</th></tr></thead><tbody>${rows}</tbody></table>
  </div>`;
}
function progressCard(task, title) {
  const progress = Math.max(0, Math.min(100, Number(task.progress || 0)));
  const done = Number(task.done || 0), total = Number(task.total || 0);
  const current = task.current_file ? `<p><b>当前文件：</b>${escapeHtml(task.current_file)}</p>` : '';
  const target = task.classified_dir ? `<p><b>分类目录：</b><span class="path">${escapeHtml(task.classified_dir)}</span></p>` : '';
  const failure = task.status === 'failed' ? `<div class="warnbox">${escapeHtml(task.failure_reason || '任务失败')}</div>` : '';
  return `<div class="card"><div class="row"><h3>${escapeHtml(title)}</h3>${badge(task.status || 'running')}</div><div class="progress"><div style="width:${progress}%"></div></div><p><b>进度：</b>${done}/${total} (${progress}%) <b>耗时：</b>${fmtMs(task.elapsed_ms)}</p>${current}${target}${failure}</div>`;
}
function auditBusy() {
  return Boolean((state.auditTask && state.auditTask.status === 'running') || (state.auditMoveTask && state.auditMoveTask.status === 'running'));
}
function clearAuditPoll() {
  if (state.auditPollTimer) clearInterval(state.auditPollTimer);
  state.auditPollTimer = null;
}
function auditResultRow(item, moves) {
  const move = moves.find(m => m.source_path === item.input_path);
  const left = item.left || {}, right = item.right || {};
  return `<tr>
    <td><b>${escapeHtml(item.name)}</b><br><span class="path">${escapeHtml(item.input_path)}</span>${move ? `<br><span class="path">-> ${escapeHtml(move.target_path)}</span>` : ''}<br><span class="muted">${escapeHtml(item.reason || '')}</span></td>
    <td>${badge(item.status)}</td>
    <td>${badge(item.move_group)}</td>
    <td>左 ${left.message_count || 0} / 采样 ${left.sample_count || 0}<br>右 ${right.message_count || 0} / 采样 ${right.sample_count || 0}</td>
    <td>${fmtNum(item.median_scale_ratio)}<br>${fmtNum(item.p95_scale_ratio)}</td>
    <td>${sideStatsText(left)}</td>
    <td>${sideStatsText(right)}</td>
    <td>${sampleBlock('L', left.samples)}${sampleBlock('R', right.samples)}</td>
  </tr>`;
}
function sideStatsText(side) {
  return `<span class="muted">${escapeHtml(side.schema_name || '-')}</span><br>median ${fmtNum(side.median_abs_xyz)}<br>p95 ${fmtNum(side.p95_abs_xyz)}<br>qnorm ${fmtNum(side.quaternion_norm_min)} ~ ${fmtNum(side.quaternion_norm_max)}`;
}
function sampleBlock(label, samples) {
  const rows = (samples || []).map(row => `[${row.map(v => fmtNum(v)).join(', ')}]`).join('<br>');
  return `<b>${label}</b><br><span class="path">${rows || '-'}</span><br>`;
}
function fmtNum(value) {
  const n = Number(value);
  if (!Number.isFinite(n)) return '-';
  return Math.abs(n) >= 100 ? n.toFixed(3) : n.toPrecision(6);
}
function openAuditMoveConfirm() {
  if (auditBusy()) return;
  const audit = state.auditPreview;
  if (!audit) return;
  const counts = audit.summary?.move_group_counts || {};
  document.getElementById('confirm-body').innerHTML = `<h2>确认移动分类</h2><p>将把 ${audit.results.length} 个 MCAP 移动到：</p><p class="path">${escapeHtml(document.getElementById('audit-classified-dir').value)}</p><p>normal：${counts.normal || 0}，unit_mismatch：${counts.unit_mismatch || 0}，other_issue：${counts.other_issue || 0}</p><div class="warnbox">移动会改变原始 MCAP 文件位置；同名文件不会覆盖，会自动追加后缀。</div><div class="row"><button class="primary" onclick="moveAuditFiles()">确认移动</button><button onclick="closeConfirm()">取消</button></div>`;
  document.getElementById('confirm-modal').classList.add('open');
}
async function moveAuditFiles() {
  const audit = state.auditPreview;
  if (!audit) return;
  if (auditBusy()) return;
  const payload = {audit_id:audit.audit_id, classified_dir:document.getElementById('audit-classified-dir').value};
  const data = await api(`/api/baton-pose-audit/${audit.audit_id}/move/start`, {method:'POST', body:JSON.stringify(payload)});
  state.auditMoveTask = data.task;
  closeConfirm();
  setNotice('正在移动分类 MCAP...', 'notice');
  renderAuditResult();
  renderAuditFileTable();
  pollBatonAuditMove(audit.audit_id);
}
async function pollBatonAuditMove(auditId) {
  clearAuditPoll();
  state.auditPollTimer = setInterval(async () => {
    try {
      const data = await api(`/api/baton-pose-audit/${auditId}/move/status`);
      state.auditMoveTask = data.task;
      if (data.task.status === 'succeeded') {
        clearAuditPoll();
        state.auditPreview = data.record;
        state.auditMoveTask = null;
        setNotice('位姿审计分类移动完成。');
        renderAuditFileTable();
      } else if (data.task.status === 'failed') {
        clearAuditPoll();
        setNotice(`移动分类失败：${escapeHtml(data.task.failure_reason || '')}`, 'warnbox');
        renderAuditFileTable();
      }
      renderAuditResult();
    } catch (error) {
      clearAuditPoll();
      state.auditMoveTask = {status:'failed', failure_reason:'任务已中断，请重新开始审计。', progress:0, done:0, total:0, operation:'move'};
      setNotice('移动分类任务已中断，请重新开始审计。', 'warnbox');
      renderAuditFileTable();
      renderAuditResult();
    }
  }, 500);
}
async function loadProductionConfig() {
  state.productionConfig = await api('/api/production-config');
  renderProductionConfig();
}
function productionPoseFields(prefix, value) {
  const t = value?.translation_mm || [0,0,0];
  return `<label>固定平移 translation_mm（mm）</label><div class="row">${['x','y','z'].map((axis,i)=>`<input data-production="${prefix}.translation_mm.${i}" value="${escapeHtml(String(t[i] ?? ''))}" placeholder="${axis} (mm)">`).join('')}</div>
  <p class="muted">相机到 TCP 的旋转固定为 0，无需填写。</p>`;
}
function productionWorkFields(hand, value) {
  const p = value?.position_mm || {x:0,y:0,z:0}, r = value?.rotation_euler_rad || {rx:0,ry:0,rz:0};
  return `<label>工作坐标系原点 position_mm（mm）</label><div class="row">${['x','y','z'].map(axis=>`<input data-production="work_frames.${hand}.position_mm.${axis}" value="${escapeHtml(String(p[axis] ?? ''))}" placeholder="${axis} (mm)">`).join('')}</div>
  <label>工作坐标系旋转 rotation_euler_rad（欧拉角，rad）</label><div class="row">${['rx','ry','rz'].map(axis=>`<input data-production="work_frames.${hand}.rotation_euler_rad.${axis}" value="${escapeHtml(String(r[axis] ?? ''))}" placeholder="${axis} (rad)">`).join('')}</div>`;
}
function productionFilterFields(web) {
  const scene2 = web?.scene2 || {}, pose = scene2.pose_filter || {}, tactile = scene2.tactile_filter || {};
  const field = (label, path, value) => `<label>${label}</label><input data-production="${path}" value="${escapeHtml(String(value ?? ''))}">`;
  return `<div class="config-grid">
    <div class="config-section"><h3>Pose filter</h3>
      ${field('窗口时长 ms', 'web_pipeline.scene2.pose_filter.window_duration_ms', pose.window_duration_ms)}
      ${field('Polyorder', 'web_pipeline.scene2.pose_filter.polyorder', pose.polyorder)}
      ${field('位置 guard 最大差 m', 'web_pipeline.scene2.pose_filter.position_guard_max_delta_m', pose.position_guard_max_delta_m)}
      ${field('方向 guard 最大差 deg', 'web_pipeline.scene2.pose_filter.orientation_guard_max_delta_deg', pose.orientation_guard_max_delta_deg)}
    </div>
    <div class="config-section"><h3>Tactile filter</h3>
      ${field('Median window', 'web_pipeline.scene2.tactile_filter.median_window', tactile.median_window)}
      ${field('EMA alpha', 'web_pipeline.scene2.tactile_filter.ema_alpha', tactile.ema_alpha)}
      ${field('接触 reset 阈值', 'web_pipeline.scene2.tactile_filter.contact_reset_threshold', tactile.contact_reset_threshold ?? '')}
    </div>
  </div>`;
}
function lerobotSegmentLabel(id) {
  const labels = {
    left_tcp_pose:'左 TCP pose', right_tcp_pose:'右 TCP pose',
    left_gripper_width:'左夹爪宽度', right_gripper_width:'右夹爪宽度',
    tactile_left_gripper_1:'左触觉 1', tactile_left_gripper_2:'左触觉 2',
    tactile_right_gripper_1:'右触觉 1', tactile_right_gripper_2:'右触觉 2',
    left_tcp_pose_t_plus_1:'左 TCP pose t+1', right_tcp_pose_t_plus_1:'右 TCP pose t+1',
    left_gripper_width_t_plus_1:'左夹爪 t+1', right_gripper_width_t_plus_1:'右夹爪 t+1',
  };
  return labels[id] || id;
}
function lerobotFeatureRows(kind, segments) {
  return (segments || []).map((item, index) => {
    const required = item.id.includes('tcp_pose');
    return `<tr data-feature-kind="${kind}" data-feature-id="${escapeHtml(item.id)}">
      <td><input data-feature-enabled type="checkbox" ${item.enabled?'checked':''} ${required?'disabled':''}></td>
      <td>${escapeHtml(lerobotSegmentLabel(item.id))}<br><span class="path">${escapeHtml(item.id)}</span></td>
      <td><input data-feature-order value="${index + 1}" style="width:72px"></td>
    </tr>`;
  }).join('');
}
function productionLerobotFields(web) {
  const features = web?.lerobot_features || {};
  return `<div class="config-grid">
    <div class="config-section"><h3>observation.state</h3><table><thead><tr><th>启用</th><th>段落</th><th>顺序</th></tr></thead><tbody>${lerobotFeatureRows('state_segments', features.state_segments)}</tbody></table></div>
    <div class="config-section"><h3>action（固定 t+1 绝对量）</h3><table><thead><tr><th>启用</th><th>段落</th><th>顺序</th></tr></thead><tbody>${lerobotFeatureRows('action_segments', features.action_segments)}</tbody></table></div>
  </div>`;
}
function renderProductionConfig() {
  const data = state.productionConfig, ready = data.readiness || {};
  const camera = data.camera_from_tcp || {}, work = data.work_frames || {}, sdk = ready.sdk || {}, web = data.web_pipeline || {};
  const handCard = hand => `<div class="config-section"><h3>${hand==='left'?'左臂':'右臂'}</h3><p class="muted">目标 base frame：<b>${hand}_arm_base</b></p><h4>相机到夹爪 TCP 外参</h4>${productionPoseFields(`camera_from_tcp.${hand}`, camera[hand])}<h4>工作坐标系在机械臂 base 下的位姿</h4>${productionWorkFields(hand, work[hand])}</div>`;
  const gripper = ready.gripper || {};
  document.getElementById('page-config').innerHTML = `<div class="card"><div class="row"><div><h2>配置中心</h2><p class="path">${escapeHtml(data.config_path || '')}</p></div>${ready.ready?badge('success'):badge('warning')}<span>RealMan SDK：${sdk.ready?'已就绪 '+escapeHtml(sdk.version || ''):'不可用'}</span></div>${ready.ready?'<div class="notice">生产配置已就绪。</div>':`<div class="warnbox">仍需处理：${(ready.missing_items || []).map(escapeHtml).join('、')}</div>`}</div>
  <div class="card"><div class="row"><div><h3>夹爪开合标定</h3><p class="muted">通过 GoPro 实时画面与 ArUco 自动采样生成，无需手工编辑底层 marker 参数。</p></div><button class="primary right" onclick="openGripperCalibration()">自动生成 / 重新标定</button></div><div class="row">${badge(gripper.left?'success':'warning')} 左手夹爪 ${gripper.left?'已配置':'缺失'} ${badge(gripper.right?'success':'warning')} 右手夹爪 ${gripper.right?'已配置':'缺失'}</div></div>
  <div class="card"><h3>左右臂 base 位姿转换</h3><p class="muted">人工填写：平移使用 mm，机械臂 base 旋转使用欧拉角 rad。Baton Mini 原始位姿、Runtime 换算结果和最终机械臂 TCP 输出的位置统一使用 m。</p><div class="config-grid">${handCard('left')}${handCard('right')}</div></div>
  <div class="card"><h3>滤波参数</h3><p class="muted">保存后作为生产默认值影响后续任务；已运行任务保留自己的 config snapshot。</p>${productionFilterFields(web)}</div>
  <div class="card"><h3>LeRobot 维度定义</h3><p class="muted">候选字段来自当前 aligned MCAP。TCP pose 为必选；action 固定使用下一帧 t+1 绝对目标。</p>${productionLerobotFields(web)}</div>
  <div class="card"><div id="production-errors"></div><button class="primary" onclick="saveProductionConfig()">校验并保存正式配置</button></div>`;
}
function productionPayload() {
  const result = JSON.parse(JSON.stringify({
    camera_from_tcp: state.productionConfig?.camera_from_tcp || {left:{translation_mm:[]},right:{translation_mm:[]}},
    work_frames: state.productionConfig?.work_frames || {left:{hand:'left',base_frame_id:'left_arm_base',work_frame_id:'camera_work',position_mm:{},rotation_euler_rad:{}},right:{hand:'right',base_frame_id:'right_arm_base',work_frame_id:'camera_work',position_mm:{},rotation_euler_rad:{}}},
    web_pipeline: state.productionConfig?.web_pipeline || {},
  }));
  document.querySelectorAll('[data-production]').forEach(input => setNested(result, input.dataset.production, input.value === '' ? null : Number(input.value)));
  result.web_pipeline ||= {};
  result.web_pipeline.lerobot_features ||= {};
  ['state_segments','action_segments'].forEach(kind => {
    result.web_pipeline.lerobot_features[kind] = [...document.querySelectorAll(`[data-feature-kind="${kind}"]`)]
      .map(row => ({id:row.dataset.featureId, enabled:row.querySelector('[data-feature-enabled]').checked, order:Number(row.querySelector('[data-feature-order]').value) || 999}))
      .sort((a,b) => a.order - b.order)
      .map(item => ({id:item.id, enabled:item.enabled}));
  });
  return result;
}
async function saveProductionConfig() {
  const payload = productionPayload();
  const checked = await api('/api/production-config/validate', {method:'POST', body:JSON.stringify(payload)});
  const host = document.getElementById('production-errors');
  if (!checked.valid) { host.innerHTML = `<div class="config-errors"><ul>${checked.errors.map(item=>`<li>${escapeHtml(item.path)}：${escapeHtml(item.message)}</li>`).join('')}</ul></div>`; return; }
  if (!confirm('保存后会影响所有后续生产任务；已运行任务保持各自的 config snapshot 不变。确认保存？')) return;
  state.productionConfig = await api('/api/production-config', {method:'POST', body:JSON.stringify(payload)});
  setNotice('正式配置已保存。后续任务会写入独立 config snapshot。');
  await loadDashboard();
  renderProductionConfig();
}
async function openGripperCalibration() {
  const result = await api('/api/calibration/gripper/open', {method:'POST', body:'{}'});
  window.open(result.url, '_blank');
  setTimeout(loadProductionConfig, 1500);
}
function getNested(obj, path, fallback='') {
  const value = path.split('.').reduce((current, key) => current == null ? undefined : current[key], obj);
  return value == null ? fallback : value;
}
function setNested(obj, path, value) {
  const keys = path.split('.');
  let current = obj;
  keys.slice(0, -1).forEach(key => current = current[key] ||= {});
  current[keys[keys.length - 1]] = value;
}
function hasNested(obj, path) { return getNested(obj, path, undefined) !== undefined; }
function parseConfigValue(input) {
  if (input.dataset.kind === 'number') return input.value === '' ? null : Number(input.value);
  if (input.dataset.kind === 'int') return input.value === '' ? null : Number.parseInt(input.value, 10);
  if (input.dataset.kind === 'csv-number') return input.value.split(',').map(value => Number(value.trim()));
  if (input.dataset.kind === 'csv') return input.value.split(',').map(value => value.trim()).filter(Boolean);
  return input.value;
}
function collectConfigOverrides() {
  const result = {};
  document.querySelectorAll('.config-section').forEach(section => {
    if (!section.querySelector('.config-enable')?.checked) return;
    section.querySelectorAll('[data-config-path]').forEach(input => setNested(result, input.dataset.configPath, parseConfigValue(input)));
  });
  return result;
}
function configRequest() {
  return {
    preset_name: state.presetName || '',
    overrides: collectConfigOverrides(),
    bridge_mode: document.getElementById('bridge-mode')?.value || 'format-only',
    formal_manual_override_confirmed: document.getElementById('formal-manual-confirm')?.checked || false,
  };
}
function cfg(path, fallback='') { return getNested(state.configPreview?.effective_summary || {}, path, fallback); }
function configField(label, path, kind='text') {
  const value = cfg(path, '');
  const display = Array.isArray(value) ? value.join(', ') : value;
  return `<label>${label}</label><input data-config-path="${path}" data-kind="${kind}" value="${escapeHtml(String(display ?? ''))}" onchange="configChanged()">`;
}
function configSection(title, block, body) {
  return `<div class="config-section" data-config-block="${block}"><label class="enable"><input class="config-enable" type="checkbox" ${hasNested(state.configOverrides, block)?'checked':''} onchange="configChanged()"> 覆盖 ${title}</label>${body}</div>`;
}
async function loadConfigWorkspace() {
  try {
    state.configPresets = (await api('/api/config/presets')).presets || [];
    await refreshConfigPreview();
  } catch (error) {
    document.getElementById('config-workbench').innerHTML = `<div class="config-errors">${escapeHtml(error.message)}</div>`;
  }
}
async function refreshConfigPreview() {
  state.configPreview = await api('/api/config/preview', {method:'POST', body:JSON.stringify(configRequest())});
  renderConfigWorkbench();
}
async function configChanged() {
  state.configOverrides = collectConfigOverrides();
  await refreshConfigPreview();
  await previewJob();
}
async function choosePreset(name) {
  state.presetName = name;
  state.configOverrides = {};
  await refreshConfigPreview();
  await previewJob();
}
async function saveCurrentPreset() {
  const name = prompt('Preset 名称（字母、数字、下划线或连字符）');
  if (!name) return;
  state.configOverrides = collectConfigOverrides();
  await api('/api/config/presets', {method:'POST', body:JSON.stringify({name, overrides:state.configOverrides, bridge_mode:document.getElementById('bridge-mode')?.value || 'format-only'})});
  state.presetName = name;
  await loadConfigWorkspace();
}
async function deleteCurrentPreset() {
  if (!state.presetName || !confirm(`删除 preset ${state.presetName}？正式配置不会被修改。`)) return;
  await api(`/api/config/presets/${encodeURIComponent(state.presetName)}`, {method:'DELETE'});
  state.presetName = '';
  state.configOverrides = {};
  await loadConfigWorkspace();
}
function renderConfigWorkbench() {
  const host = document.getElementById('config-workbench');
  if (!host || !state.configPreview) return;
  const presetOptions = [`<option value="">不使用 preset</option>`, ...state.configPresets.map(item => `<option value="${escapeHtml(item.name)}" ${item.name===state.presetName?'selected':''}>${escapeHtml(item.name)}</option>`)].join('');
  const gripper = hand => configSection(`场景一：${hand === 'left' ? '左手' : '右手'}夹爪`, `scene1.gripper.${hand}`,
    configField('图像 topic', `scene1.gripper.${hand}.image_topic`) +
    configField('输出 topic', `scene1.gripper.${hand}.output_topic`) +
    configField('ArUco 字典', `scene1.gripper.${hand}.aruco_dict`) +
    configField('marker id 0', `scene1.gripper.${hand}.marker_id_0`, 'int') +
    configField('marker id 1', `scene1.gripper.${hand}.marker_id_1`, 'int') +
    configField('marker min', `scene1.gripper.${hand}.marker_min`, 'number') +
    configField('marker max', `scene1.gripper.${hand}.marker_max`, 'number') +
    configField('gripper max', `scene1.gripper.${hand}.gripper_max`, 'number'));
  const extrinsic = name =>
    configField(`${name} translation_m`, `scene1.frame_alignment.extrinsics.${name}.translation_m`, 'csv-number') +
    configField(`${name} quaternion xyzw`, `scene1.frame_alignment.extrinsics.${name}.rotation_quat_xyzw`, 'csv-number');
  const frame = configSection('场景一：坐标系转换', 'scene1.frame_alignment',
    `<label>公共锚点</label><select data-config-path="scene1.frame_alignment.common_anchor" onchange="configChanged()"><option value="left" ${cfg('scene1.frame_alignment.common_anchor')==='left'?'selected':''}>left</option><option value="right" ${cfg('scene1.frame_alignment.common_anchor')==='right'?'selected':''}>right</option></select>` +
    extrinsic('common_from_left_start') + extrinsic('common_from_right_start') +
    extrinsic('camera_from_left_tcp') + extrinsic('camera_from_right_tcp') +
    configField('左手 pose 输入 topic', 'scene1.frame_alignment.pose_streams.left.input_topic') +
    configField('左手 camera pose 输出 topic', 'scene1.frame_alignment.pose_streams.left.output_camera_pose_common') +
    configField('左手 TCP pose 输出 topic', 'scene1.frame_alignment.pose_streams.left.output_tcp_pose_common') +
    configField('右手 pose 输入 topic', 'scene1.frame_alignment.pose_streams.right.input_topic') +
    configField('右手 camera pose 输出 topic', 'scene1.frame_alignment.pose_streams.right.output_camera_pose_common') +
    configField('右手 TCP pose 输出 topic', 'scene1.frame_alignment.pose_streams.right.output_tcp_pose_common'));
  const detection = configSection('场景二：可靠性检测', 'scene2.detection',
    configField('最大 gap 时长 ms', 'scene2.detection.max_gap_duration_ms', 'number') +
    configField('Quaternion norm 容差', 'scene2.detection.quaternion_norm_tolerance', 'number') +
    configField('Pose 跳变阈值', 'scene2.detection.pose_position_jump_threshold', 'number') +
    configField('夹爪跳变阈值', 'scene2.detection.gripper_jump_threshold', 'number') +
    configField('触觉 spike 均值差阈值', 'scene2.detection.tactile_spike_mean_delta_threshold', 'number') +
    configField('触觉 zero ratio 阈值', 'scene2.detection.tactile_zero_ratio_threshold', 'number') +
    configField('触觉 saturation ratio 阈值', 'scene2.detection.tactile_saturation_ratio_threshold', 'number'));
  const pose = configSection('场景二：Pose filter', 'scene2.pose_filter',
    configField('窗口时长 ms', 'scene2.pose_filter.window_duration_ms', 'int') +
    configField('Polyorder', 'scene2.pose_filter.polyorder', 'int') +
    configField('位置 guard 最大差 m', 'scene2.pose_filter.position_guard_max_delta_m', 'number') +
    configField('方向 guard 最大差 deg', 'scene2.pose_filter.orientation_guard_max_delta_deg', 'number'));
  const tactile = configSection('场景二：Tactile filter', 'scene2.tactile_filter',
    configField('Median window', 'scene2.tactile_filter.median_window', 'int') +
    configField('EMA alpha', 'scene2.tactile_filter.ema_alpha', 'number') +
    configField('接触 reset 阈值', 'scene2.tactile_filter.contact_reset_threshold', 'number'));
  const align = configSection('场景三：时间轴对齐', 'scene3',
    configField('目标 step Hz', 'scene3.target_step_hz', 'int') +
    configField('图像最大偏差 ms', 'scene3.image_max_dt_ms', 'int') +
    configField('左右 baseline 图像 topic', 'scene3.baseline_image_topics', 'csv') +
    `<p class="muted">固定策略：pose interpolation_slerp；fallback nearest_neighbor；tactile window_aggregate；gripper follow_image_nearest。</p>`);
  const bridge = configSection('Forge bridge 与 LeRobot', 'bridge',
    configField('Pose 绝对值上限 m', 'bridge.max_pose_abs_m', 'number'));
  const lerobot = configSection('LeRobot', 'lerobot',
    configField('LeRobot fps', 'lerobot.fps', 'number'));
  const errors = (state.configPreview.errors || []).map(item => `<li>${escapeHtml(item)}</li>`).join('');
  const warnings = (state.configPreview.warnings || []).map(item => `<li>${escapeHtml(item)}</li>`).join('');
  const diff = (state.configPreview.diff || []).map(item => `<li><code>${escapeHtml(item.path)}</code></li>`).join('');
  host.innerHTML = `<div class="row"><div style="flex:1"><label>默认配置</label><div class="path">${escapeHtml(state.configPreview.default_config_path || '')}</div></div><div style="min-width:220px"><label>Preset</label><select onchange="choosePreset(this.value)">${presetOptions}</select></div><button onclick="saveCurrentPreset()">保存当前覆盖为 preset</button><button onclick="deleteCurrentPreset()" ${state.presetName?'':'disabled'}>删除 preset</button></div><div class="config-grid">${gripper('left')}${gripper('right')}${frame}${detection}${pose}${tactile}${align}${bridge}${lerobot}</div><div style="margin-top:12px"><label><input id="formal-manual-confirm" type="checkbox" style="width:auto" ${state.configPreview.manual_calibration_override && configRequest().formal_manual_override_confirmed?'checked':''} onchange="configChanged()"> 我已确认本次手工标定覆盖可用于 formal 导出</label><p class="muted">仅在 formal 且修改夹爪标定或坐标系外参时需要确认。</p>${errors?`<div class="config-errors"><b>配置错误</b><ul>${errors}</ul></div>`:''}${warnings?`<div class="warnbox"><b>配置警告</b><ul>${warnings}</ul></div>`:''}<details><summary>本次覆盖摘要（${state.configPreview.diff?.length || 0} 项）</summary><ul>${diff || '<li>无覆盖</li>'}</ul></details></div>`;
}
async function scanFiles() {
  const inputDir = document.getElementById('input-dir').value;
  const data = await api('/api/input-files/scan', {method:'POST', body:JSON.stringify({input_dir:inputDir})});
  state.files = data.files;
  state.selected = new Set(data.files.map(f => f.path));
  renderFileTable();
  await previewJob();
}
function renderFileTable() {
  const q = (document.getElementById('file-search')?.value || '').toLowerCase();
  const files = state.files.filter(f => f.name.toLowerCase().includes(q)).sort((a,b)=>a.name.localeCompare(b.name));
  const rows = files.map(f => `<tr><td><input type="checkbox" ${state.selected.has(f.path)?'checked':''} onchange="toggleFile('${jsEscape(f.path)}', this.checked)"></td><td>${escapeHtml(f.name)}</td><td>${f.size_text}</td><td>${f.modified_at}</td><td>${badge(f.status || 'waiting')}</td></tr>`).join('');
  document.getElementById('file-table').innerHTML = `<table><thead><tr><th></th><th>名称</th><th>大小</th><th>修改时间</th><th>状态</th></tr></thead><tbody>${rows || '<tr><td colspan="5" class="muted">未扫描到 .mcap 文件</td></tr>'}</tbody></table>`;
}
function toggleFile(path, checked) { checked ? state.selected.add(path) : state.selected.delete(path); previewJob(); }
function selectAll(on) { state.files.forEach(f => on ? state.selected.add(f.path) : state.selected.delete(f.path)); renderFileTable(); previewJob(); }
function invertSelection() { state.files.forEach(f => state.selected.has(f.path) ? state.selected.delete(f.path) : state.selected.add(f.path)); renderFileTable(); previewJob(); }
async function previewJob() {
  const files = [...state.selected].map(path => ({path}));
  const payload = {input_dir:document.getElementById('input-dir').value, output_dir:document.getElementById('output-dir').value, dataset_name:document.getElementById('dataset-name')?.value || '', files};
  if (!files.length || !payload.output_dir) { document.getElementById('preview-box').innerHTML = '<p class="muted">请选择文件和输出目录。</p>'; return; }
  state.preview = await api('/api/jobs/preview', {method:'POST', body:JSON.stringify(payload)});
  const p = state.preview;
  if (document.getElementById('dataset-name') && document.getElementById('dataset-name').value !== p.dataset_name) {
    document.getElementById('dataset-name').value = p.dataset_name;
  }
  const conflictText = p.conflicts.map(c => `<li class="path">${escapeHtml(c.type)}: ${escapeHtml(c.path)}</li>`).join('');
  const ready = p.production_readiness || {ready:false,missing_items:[]};
  document.getElementById('preview-box').innerHTML = `<hr><p><b>已选择：</b>${p.file_count} 个，${p.total_size_text}</p><p><b>最终 dataset：</b><span class="path">${escapeHtml(p.dataset_dir)}</span></p><p><b>sidecar：</b><span class="path">${escapeHtml(p.sidecar_dir)}</span></p><p><b>生产链路：</b>左右 arm-base TCP 绝对位姿</p><div class="warnbox">建议先在“位姿审计”页面检查左右 Baton Mini 原始位姿单位是否一致；该检查只提示，不阻止清洗。</div><p><b>冲突：</b>${p.conflicts.length} 个目录</p>${conflictText ? `<ul>${conflictText}</ul>` : ''}${ready.ready?'':`<div class="warnbox">生产配置未就绪：${(ready.missing_items||[]).map(escapeHtml).join('、')}。<button onclick="showPage('config')">进入配置中心</button></div>`}<button class="primary" onclick="openConfirm()" ${ready.ready?'':'disabled'}>开始清洗</button>`;
}
function openConfirm() {
  const p = state.preview;
  if (!p) return;
  const conflicts = p.conflicts.map(c => `<li class="path">${escapeHtml(c.type)}: ${escapeHtml(c.path)}</li>`).join('');
  document.getElementById('confirm-body').innerHTML = `<h2>确认启动任务</h2><p>输入：<span class="path">${escapeHtml(p.input_dir)}</span></p><p>输出父目录：<span class="path">${escapeHtml(p.output_parent)}</span></p><p>最终 dataset：<span class="path">${escapeHtml(p.dataset_dir)}</span></p><p>sidecar：<span class="path">${escapeHtml(p.sidecar_dir)}</span></p><p>文件：${p.file_count} 个，${p.total_size_text}</p><p>生产链路：左右 arm-base TCP 绝对位姿</p><p>worker：${escapeHtml(document.getElementById('workers').value || 'auto')}</p>${conflicts ? `<h3>同名目录冲突</h3><ul>${conflicts}</ul><label>冲突策略</label><select id="conflict-policy"><option value="overwrite">覆盖</option><option value="skip">取消启动</option></select>` : '<input id="conflict-policy" type="hidden" value="overwrite">'}<div class="row"><button class="primary" onclick="submitJob()">确认启动</button><button onclick="closeConfirm()">取消</button></div>`;
  document.getElementById('confirm-modal').classList.add('open');
}
function closeConfirm() { document.getElementById('confirm-modal').classList.remove('open'); }
async function submitJob() {
  const policy = document.getElementById('conflict-policy').value;
  if (policy === 'skip') { closeConfirm(); return; }
  const payload = {remark:document.getElementById('remark').value, dataset_name:document.getElementById('dataset-name').value, input_dir:document.getElementById('input-dir').value, output_dir:document.getElementById('output-dir').value, run_endpoint:document.getElementById('run-endpoint').value, workers:document.getElementById('workers').value || 'auto', conflict_policy:policy, files:[...state.selected].map(path=>({path}))};
  const data = await api('/api/jobs', {method:'POST', body:JSON.stringify(payload)});
  closeConfirm();
  openJob(data.job.job_id);
}
async function openJob(id) {
  if (state.currentJob && state.currentJob.job_id !== id) {
    stopTrajectoryPlayback(true);
    state.trajectory = null;
    state.trajectoryEpisode = 'all';
  }
  const data = await api(`/api/jobs/${id}`);
  state.currentJob = data.job;
  renderJob();
  showPage('job');
}
function renderJob() {
  const j = state.currentJob;
  document.title = j.status === 'running' ? `运行中 ${j.progress}% - 数据清洗` : `${statusText[j.status] || j.status} - 数据清洗`;
  const stages = j.stages.map(s => `<div class="stage"><div class="row"><b>${s.name}</b>${badge(s.status)}</div><p>${escapeHtml(s.summary || '')}</p><p class="muted">耗时：${fmtMs(s.duration_ms)}</p>${s.failure_reason ? `<p class="failed">${escapeHtml(s.failure_reason)}</p>` : ''}</div>`).join('');
  const failedBtn = j.counts.failed ? `<button onclick="retryFailed('${j.job_id}')">以失败文件新建任务</button>` : '';
  const cancelBtn = j.status === 'running' ? `<button class="danger" onclick="cancelJob('${j.job_id}')">取消批次</button>` : '';
  const included = j.files.filter(f => f.included_in_dataset).length;
  const summary = j.dataset_summary || {};
  const visualizer = j.dataset_dir ? `<button onclick="openVisualizer('${j.job_id}')">打开可视化</button>` : '';
  const tab = state.jobTab || 'quality';
  const body = tab === 'trajectory' ? renderTrajectoryTab() : tab === 'files' ? renderFilesTab(j) : renderQualityTab(j);
  document.getElementById('page-job').innerHTML = `<div class="card"><div class="row"><h2>${escapeHtml(j.remark || j.dataset_name || j.job_id)}</h2>${badge(j.status)}<button class="right" onclick="showPage('dashboard')">返回看板</button>${cancelBtn}</div><div class="progress"><div style="width:${j.progress}%"></div></div><p><b>Dataset：</b><span class="path">${escapeHtml(j.dataset_dir || '')}</span></p><p><b>Sidecar：</b><span class="path">${escapeHtml(j.sidecar_dir || '')}</span></p><p><b>配置快照：</b><span class="path">${escapeHtml(j.config_snapshot_path || '历史任务无快照')}</span></p><p class="muted">${j.input_dir} -> ${j.output_parent || j.output_dir}</p><p>${j.notification || ''}</p><div class="row"><b>纳入 ${included}</b><b>失败 ${j.counts.failed}</b><b>episode ${summary.episodes || 0}</b><b>frame ${summary.frames || 0}</b><b>耗时 ${fmtMs(j.duration_ms)}</b>${visualizer}${failedBtn}</div><div class="notice">生产任务：左右 arm-base TCP 绝对位姿，可由训练侧 LeRobot 框架继续转换为相对表示。</div></div><div class="grid">${stages}</div><div class="tabs"><button class="${tab==='quality'?'active':''}" onclick="switchJobTab('quality')">评测报告</button><button class="${tab==='trajectory'?'active':''}" onclick="switchJobTab('trajectory')">3D轨迹</button><button class="${tab==='files'?'active':''}" onclick="switchJobTab('files')">逐文件状态</button></div>${body}`;
  if (tab === 'trajectory') initTrajectoryCanvas();
}
function switchJobTab(tab) {
  if (tab !== 'trajectory') stopTrajectoryPlayback();
  state.jobTab = tab;
  renderJob();
}
function scoreClass(value) {
  const n = Number(value);
  if (n >= 0.85) return 'score-good';
  if (n >= 0.70) return 'score-warn';
  return 'score-bad';
}
function fmtScore(value, digits=3) {
  const n = Number(value);
  return Number.isFinite(n) ? n.toFixed(digits) : '-';
}
function renderQualityTab(j) {
  const quality = j.quality_summary || {};
  const summary = j.dataset_summary || {};
  const readiness = quality.training_readiness || fallbackReadiness(quality, summary);
  const riskItems = (readiness.key_risks || []).map(item => `<li>${escapeHtml(item)}</li>`).join('');
  const actionItems = (readiness.next_actions || []).map(item => `<li>${escapeHtml(item)}</li>`).join('');
  const modules = (readiness.modules || []).map(module => readinessModule(module)).join('');
  const riskByEpisode = new Map((readiness.episode_risks || []).map(item => [item.episode_id, item]));
  const explanations = readiness.subscore_explanations || {};
  const subscores = Object.entries(quality.subscores || {}).map(([key, value]) => {
    const n = Math.max(0, Math.min(1, Number(value) || 0));
    const exp = explanations[key] || {};
    return `<div class="score-card"><div class="row"><b>${escapeHtml(exp.name || key)}</b><b class="right">${fmtScore(value)}</b></div><div class="score-track"><div class="score-fill ${scoreClass(value)}" style="width:${n*100}%"></div></div><p class="metric-note">${escapeHtml(exp.meaning || '')}</p><p class="metric-note">${escapeHtml(exp.impact || '')}</p><p class="path">${escapeHtml(key)}</p></div>`;
  }).join('');
  const episodes = (quality.per_episode || []).map(ep => {
    const risk = riskByEpisode.get(ep.episode_id) || {};
    const dims = (risk.top_saturated_dimensions || []).slice(0,4).map(dim => `<span class="dim-pill">${escapeHtml(dim.label || dim.key || dim.index)} ${fmtPct(dim.saturation_rate)}</span>`).join('') || '<span class="muted">-</span>';
    return `<tr><td>${escapeHtml(ep.episode_id ?? '-')}</td><td>${ep.num_frames ?? '-'}</td><td>${fmtScore(ep.overall_score)}</td><td>${escapeHtml((ep.flags || []).join('、') || '-')}</td><td>${fmtPct(ep.overall_saturation)}</td><td>${dims}</td><td>smoothness LDLJ ${fmtScore(ep.ldlj,2)}<br>夹爪 chatter ${fmtScore(ep.gripper_chatter_rate,3)}</td><td>${escapeHtml(risk.review_hint || '无明显复查点')}</td></tr>`;
  }).join('');
  const flags = (quality.flags || []).map(flag => `<span class="badge failed">${escapeHtml(flag)}</span>`).join('') || '<span class="muted">无</span>';
  const recs = (quality.recommendations || []).map(item => `<li>${escapeHtml(item)}</li>`).join('');
  const warnings = (quality.warnings || []).map(w => `<li>${escapeHtml(w)}</li>`).join('');
  return `<div class="card"><h3>PI0.5 / VLA 训练前技术体检</h3>
    <div class="readiness-hero ${escapeHtml(readiness.level || 'review')}">
      <div class="row"><h3 class="readiness-title">${escapeHtml(readiness.conclusion || '需要复查')}</h3><span class="readiness-status ${escapeHtml(readiness.level || 'review')}">${escapeHtml(readiness.conclusion || '需要复查')}</span></div>
      <p>${escapeHtml(readiness.headline || '')}</p>
      <div class="row"><b>格式 ${escapeHtml(quality.format || '-')}</b><b>质量分 ${quality.overall_score ?? '-'}</b><b>${readiness.dataset_size?.episodes ?? quality.num_episodes ?? summary.episodes ?? 0} episodes</b><b>${readiness.dataset_size?.frames ?? quality.total_frames ?? summary.frames ?? 0} frames</b><b>${escapeHtml(readiness.dataset_size?.duration_text || '-')}</b><b>${readiness.dataset_size?.fps || '-'} FPS</b></div>
      <div class="split" style="grid-template-columns:1fr 1fr; margin-top:12px">
        <div><b>关键风险</b><ul class="risk-list">${riskItems}</ul></div>
        <div><b>下一步动作</b><ul class="action-list">${actionItems}</ul></div>
      </div>
    </div>
    ${warnings ? `<div class="warnbox"><b>质量警告</b><ul>${warnings}</ul></div>` : ''}
    <h4>我应该看什么</h4><div class="readiness-grid">${modules}</div>
    <h4>逐 episode 风险</h4><table><thead><tr><th>episode</th><th>frames</th><th>score</th><th>flags</th><th>动作贴边</th><th>主要贴边维度</th><th>平滑/夹爪</th><th>复查提示</th></tr></thead><tbody>${episodes || '<tr><td colspan="8" class="muted">暂无逐 episode 数据。</td></tr>'}</tbody></table>
    <details><summary>技术指标详情（Forge 原始分数）</summary><div class="score-grid" style="margin-top:12px">${subscores || '<p class="muted">暂无 subscores。</p>'}</div><h4>全局 flags</h4><div class="row">${flags}</div>${recs ? `<h4>Forge 建议</h4><ul>${recs}</ul>` : ''}</details>
    <details><summary>报告文件位置</summary><p><b>训练摘要：</b><span class="path">${escapeHtml(readiness.report_path || '')}</span></p><p><b>Inspect：</b><span class="path">${escapeHtml(quality.inspect_report || '')}</span></p><p><b>Quality：</b><span class="path">${escapeHtml(quality.quality_report || '')}</span></p>${quality.flagged_report ? `<p><b>Flagged：</b><span class="path">${escapeHtml(quality.flagged_report)}</span></p>` : ''}</details>
  </div>`;
}
function readinessModule(module) {
  const status = module.status || 'info';
  const metrics = moduleMetricsText(module);
  const risks = (module.risks || []).map(item => `<li>${escapeHtml(item)}</li>`).join('');
  return `<div class="readiness-module ${escapeHtml(status)}"><div class="row"><h4>${escapeHtml(module.title || '')}</h4><span class="readiness-status ${escapeHtml(status)}">${escapeHtml(module.label || status)}</span></div><p>${escapeHtml(module.summary || '')}</p>${metrics ? `<p class="metric-note">${metrics}</p>` : ''}${risks ? `<ul class="risk-list">${risks}</ul>` : ''}</div>`;
}
function moduleMetricsText(module) {
  const m = module.metrics || {};
  if (module.id === 'format_input') {
    const expected = (m.expected_state_dim != null || m.expected_action_dim != null) ? ` / expected ${m.expected_state_dim ?? '-'}:${m.expected_action_dim ?? '-'}` : '';
    return `state ${m.state_dim ?? '-'} / action ${m.action_dim ?? '-'}${expected} / 双目 ${m.dual_cameras ? '是' : '否'}`;
  }
  if (module.id === 'storage_media') {
    const ratio = Number(m.raw_to_dataset_ratio);
    const ratioText = Number.isFinite(ratio) ? ` / 压缩比 ${ratio.toFixed(1)}x` : '';
    const rowsText = m.parquet_total_rows != null ? ` / 表格行 ${m.parquet_total_rows}` : '';
    return `raw ${m.raw_total_size_text || '-'} -> LeRobot ${m.dataset_total_size_text || '-'} / 视频 ${m.video_total_size_text || '-'} / mp4 ${m.video_file_count ?? 0}${rowsText}${ratioText}`;
  }
  if (module.id === 'action_health') return `总分 ${fmtScore(m.overall_score)} / 全局 flags ${(m.global_flags || []).length}`;
  if (module.id === 'sync_quality') return `max dt ${fmtScore(m.max_dt_ms,1)} ms / 一帧 ${fmtScore(m.frame_interval_ms,1)} ms / terminal drop ${m.terminal_dropped_steps ?? 0}`;
  if (module.id === 'gripper_tactile') return `夹爪最高插值 ${fmtPct(m.max_gripper_interpolation_rate)} / 触觉最低覆盖 ${fmtPct(m.min_tactile_coverage_ratio)}`;
  if (module.id === 'dataset_scale') return m.note || '';
  return '';
}
function fallbackReadiness(quality, summary) {
  const frames = quality.total_frames ?? summary.frames ?? 0;
  const fps = summary.fps || 0;
  const duration = fps ? `约 ${(frames/fps).toFixed(1)} 秒` : '-';
  return {level:'review', conclusion:'需要复查', headline:'正在使用旧版质量摘要，建议重新打开或重新运行质量检查生成训练前摘要。', key_risks:['暂无训练前解释摘要。'], next_actions:['查看 Forge 原始分数和逐 episode flags。'], modules:[{id:'dataset_scale', title:'数据量', status:'info', label:'仅展示', summary:`${quality.num_episodes ?? summary.episodes ?? 0} episodes / ${frames} frames / ${duration}。`, risks:[], metrics:{note:'数据量只展示，不参与本页训练可用性判定。'}}], dataset_size:{episodes:quality.num_episodes ?? summary.episodes ?? 0, frames, fps, duration_text:duration}, episode_risks:[], subscore_explanations:{}, report_path:''};
}
function fmtPct(value) {
  const n = Number(value);
  return Number.isFinite(n) ? `${(n*100).toFixed(1)}%` : '-';
}
function renderFilesTab(j) {
  const rows = j.files.map(f => `<tr><td>${escapeHtml(f.name)}</td><td>${badge(f.status)}</td><td>${f.included_in_dataset ? '是' : '否'}</td><td>${f.episode_count || 0}</td><td>${escapeHtml(f.current_stage || '-')}</td><td class="path">${escapeHtml(f.stage_outputs?.aligned_mcap || f.stage_outputs?.cleaned_mcap || '')}</td><td>${escapeHtml(f.failure_reason || f.warning || (f.quality_warnings || []).join('；'))}</td></tr>`).join('');
  return `<div class="card"><h3>逐文件状态</h3><table><thead><tr><th>文件</th><th>状态</th><th>纳入</th><th>episode</th><th>阶段</th><th>阶段产物</th><th>原因/警告</th></tr></thead><tbody>${rows}</tbody></table></div>`;
}
function renderTrajectoryTab() {
  const t = state.trajectory;
  const opts = t ? ['<option value="all">全部 episode</option>'].concat(t.episodes.map(ep => `<option value="${ep.episode_index}" ${String(state.trajectoryEpisode)===String(ep.episode_index)?'selected':''}>Episode ${ep.episode_index} (${ep.frame_count} frames)</option>`)).join('') : '<option>加载中</option>';
  const summary = t ? `<div class="row"><b>episode ${t.episodes.length}</b><b>frame ${t.total_frames}</b><b>契约 ${escapeHtml(t.state_contract)}</b></div><p class="muted">固定工程视角：右手坐标系，显示局部原点固定在左下角。Canvas 只做可视化平移与等比例缩放，不改写原始数据。</p>` : '<p class="muted">正在加载轨迹数据...</p>';
  const dual = t?.coordinate_frame_profile === 'dual_arm_base';
  const canvases = dual
    ? `<div class="trajectory-dual"><div><p class="trajectory-panel-title">左手 TCP · left_arm_base</p><canvas id="trajectory-left" class="trajectory-canvas"></canvas></div><div><p class="trajectory-panel-title">右手 TCP · right_arm_base</p><canvas id="trajectory-right" class="trajectory-canvas"></canvas></div></div>`
    : `<div><p class="trajectory-panel-title">左右手 TCP · common_frame</p><canvas id="trajectory-common" class="trajectory-canvas"></canvas></div>`;
  const ep = selectedTrajectoryEpisode();
  const disabled = ep ? '' : 'disabled';
  const maxFrame = Math.max(0, (ep?.frame_count || 1) - 1);
  return `<div class="card"><h3>3D 手末端轨迹</h3>${summary}${dual ? '<div class="warnbox">formal 数据的左右 TCP 分别属于各自机械臂 base 坐标系，采用双画布同步播放，不比较双手绝对空间位置。</div>' : ''}<div class="trajectory-layout">${canvases}<div class="card"><label>Episode</label><select id="trajectory-episode" onchange="selectTrajectoryEpisode(this.value)">${opts}</select><label><input type="checkbox" style="width:auto" ${state.trajectoryView.showLeft?'checked':''} onchange="state.trajectoryView.showLeft=this.checked; drawTrajectory()"> 显示左手轨迹</label><label><input type="checkbox" style="width:auto" ${state.trajectoryView.showRight?'checked':''} onchange="state.trajectoryView.showRight=this.checked; drawTrajectory()"> 显示右手轨迹</label><label><input type="checkbox" style="width:auto" ${state.trajectoryView.showMarkers?'checked':''} onchange="state.trajectoryView.showMarkers=this.checked; drawTrajectory()"> 显示起点/当前点和当前姿态短轴</label><label><input type="checkbox" style="width:auto" ${state.trajectoryView.showAxes?'checked':''} onchange="state.trajectoryView.showAxes=this.checked; drawTrajectory()"> 显示坐标轴/网格</label><button onclick="resetTrajectoryView()">重置缩放</button><div class="trajectory-playback"><div class="row"><button id="trajectory-play" onclick="toggleTrajectoryPlayback()" ${disabled}>播放</button><button onclick="resetTrajectoryPlayback()" ${disabled}>回到起点</button></div><label>播放进度</label><input id="trajectory-progress" type="range" min="0" max="${maxFrame}" value="${Math.min(state.trajectoryPlayback.frameIndex, maxFrame)}" oninput="seekTrajectoryFrame(this.value)" ${disabled}><p id="trajectory-time" class="muted">${ep ? '' : '全部 episode 为静态总览，请选择单个 episode 播放。'}</p><label>播放速度</label><select id="trajectory-speed" onchange="setTrajectoryPlaybackSpeed(this.value)" ${disabled}><option value="0.25">0.25x</option><option value="0.5">0.5x</option><option value="1">1x</option><option value="2">2x</option></select></div><div style="margin-top:14px"><span class="legend-dot" style="background:#60a5fa"></span>左手<br><span class="legend-dot" style="background:#f87171"></span>右手</div><p id="trajectory-info" class="muted"></p></div></div></div>`;
}
async function ensureTrajectoryLoaded() {
  if (!state.currentJob || state.trajectory?.job_id === state.currentJob.job_id) return;
  state.trajectory = null;
  const data = await api(`/api/jobs/${state.currentJob.job_id}/trajectory`);
  data.job_id = state.currentJob.job_id;
  state.trajectory = data;
  renderJob();
}
function initTrajectoryCanvas() {
  ensureTrajectoryLoaded().catch(e => {
    const holder = document.getElementById('trajectory-info');
    if (holder) holder.textContent = e.message;
  });
  for (const spec of trajectoryCanvasSpecs()) {
    const canvas = document.getElementById(spec.id);
    if (!canvas) continue;
    canvas.onwheel = e => {
      e.preventDefault();
      state.trajectoryView.zoom *= e.deltaY < 0 ? 1.1 : 0.9;
      state.trajectoryView.zoom = Math.max(0.2, Math.min(8, state.trajectoryView.zoom));
      drawTrajectory();
    };
    canvas.ondblclick = resetTrajectoryView;
  }
  const speed = document.getElementById('trajectory-speed');
  if (speed) speed.value = String(state.trajectoryPlayback.speed);
  drawTrajectory();
}
function resetTrajectoryView() {
  state.trajectoryView.zoom = 1;
  drawTrajectory();
}
function selectTrajectoryEpisode(value) {
  stopTrajectoryPlayback(true);
  state.trajectoryEpisode = value;
  renderJob();
}
function selectedTrajectoryEpisodes() {
  const t = state.trajectory;
  if (!t) return [];
  if (state.trajectoryEpisode === 'all') return t.episodes;
  return t.episodes.filter(ep => String(ep.episode_index) === String(state.trajectoryEpisode));
}
function selectedTrajectoryEpisode() {
  return state.trajectoryEpisode === 'all' ? null : selectedTrajectoryEpisodes()[0] || null;
}
function trajectoryCanvasSpecs() {
  const t = state.trajectory;
  if (!t) return [];
  if (t.coordinate_frame_profile === 'dual_arm_base') {
    return [
      {id:'trajectory-left', hands:['left'], bounds:t.hand_bounds.left, frame:t.coordinate_frames.left},
      {id:'trajectory-right', hands:['right'], bounds:t.hand_bounds.right, frame:t.coordinate_frames.right},
    ];
  }
  return [{id:'trajectory-common', hands:['left','right'], bounds:t.bounds, frame:t.coordinate_frames.left}];
}
function makeTrajectoryProjection(canvas, bounds) {
  const dpr = window.devicePixelRatio || 1;
  const min = bounds.min, max = bounds.max;
  const dx = Math.max(0, max[0]-min[0]), dy = Math.max(0, max[1]-min[1]), dz = Math.max(0, max[2]-min[2]);
  const span = Math.max(dx, dy, dz, 1);
  const projectedWidth = Math.max(dx + dy * 0.45, span * 0.28);
  const projectedHeight = Math.max(dz + dy * 0.35, span * 0.28);
  const pad = 58 * dpr;
  const scale = Math.min((canvas.width-pad*2)/projectedWidth, (canvas.height-pad*2)/projectedHeight) * state.trajectoryView.zoom;
  return {min, max, dx, dy, dz, span, pad, scale:Math.max(scale, 0.0001), originX:pad, originY:canvas.height-pad};
}
function projectPoint(point, projection) {
  const x=point[0]-projection.min[0], y=point[1]-projection.min[1], z=point[2]-projection.min[2];
  return [projection.originX+(x+y*0.45)*projection.scale, projection.originY-(z+y*0.35)*projection.scale];
}
function drawPolyline(ctx, points, color, projection) {
  if (!points.length) return;
  ctx.strokeStyle = color;
  ctx.lineWidth = 2;
  ctx.beginPath();
  points.forEach((sample, index) => {
    const [x, y] = projectPoint(sample.position, projection);
    if (index === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
  });
  ctx.stroke();
}
function drawMarker(ctx, sample, color, projection, radius) {
  const [x, y] = projectPoint(sample.position, projection);
  ctx.fillStyle = color;
  ctx.beginPath();
  ctx.arc(x, y, radius, 0, Math.PI * 2);
  ctx.fill();
}
function drawTrajectory() {
  for (const spec of trajectoryCanvasSpecs()) drawTrajectoryCanvas(spec);
  updateTrajectoryInfo();
  updateTrajectoryPlaybackControls();
}
function drawTrajectoryCanvas(spec) {
  const canvas = document.getElementById(spec.id);
  if (!canvas) return;
  const dpr = window.devicePixelRatio || 1;
  const rect = canvas.getBoundingClientRect();
  canvas.width = Math.max(1, Math.floor(rect.width * dpr));
  canvas.height = Math.max(1, Math.floor(rect.height * dpr));
  const ctx = canvas.getContext('2d');
  ctx.setTransform(1,0,0,1,0,0);
  ctx.fillStyle = '#0b1020';
  ctx.fillRect(0,0,canvas.width,canvas.height);
  const projection = makeTrajectoryProjection(canvas, spec.bounds);
  if (state.trajectoryView.showAxes) drawTrajectoryAxes(ctx, projection);
  const eps = selectedTrajectoryEpisodes();
  for (const ep of eps) {
    for (const hand of spec.hands) {
      if ((hand === 'left' && !state.trajectoryView.showLeft) || (hand === 'right' && !state.trajectoryView.showRight)) continue;
      const samples = visibleTrajectorySamples(ep[hand] || []);
      const color = hand === 'left' ? '#60a5fa' : '#f87171';
      drawPolyline(ctx, samples, color, projection);
      if (state.trajectoryView.showMarkers && samples.length) {
        drawMarker(ctx, samples[0], '#22c55e', projection, 5*dpr);
        drawMarker(ctx, samples[samples.length-1], '#f59e0b', projection, 6*dpr);
        drawOrientationTick(ctx, samples[samples.length-1], hand === 'left' ? '#93c5fd' : '#fecaca', projection);
      }
    }
  }
  ctx.fillStyle = '#98a2b3';
  ctx.font = `${12*dpr}px sans-serif`;
  ctx.fillText(`${spec.frame} · local origin = bounds.min`, 16*dpr, 24*dpr);
}
function visibleTrajectorySamples(samples) {
  if (state.trajectoryEpisode === 'all') return samples;
  return samples.slice(0, Math.min(samples.length, state.trajectoryPlayback.frameIndex+1));
}
function drawTrajectoryAxes(ctx, projection) {
  const origin = projection.min;
  const len = Math.max(projection.span * 0.22, 0.001);
  const axes = [
    {label:'X', color:'#ef4444', p:[origin[0]+len, origin[1], origin[2]]},
    {label:'Y', color:'#22c55e', p:[origin[0], origin[1]+len, origin[2]]},
    {label:'Z', color:'#3b82f6', p:[origin[0], origin[1], origin[2]+len]},
  ];
  const [ox, oy] = projectPoint(origin, projection);
  ctx.strokeStyle = 'rgba(148,163,184,.18)';
  ctx.lineWidth = 1;
  for (let i=0; i<=4; i++) {
    const x=origin[0]+projection.dx*i/4, y=origin[1]+projection.dy*i/4;
    const [ax,ay]=projectPoint([x,origin[1],origin[2]],projection), [bx,by]=projectPoint([x,origin[1]+projection.dy,origin[2]],projection);
    const [cx,cy]=projectPoint([origin[0],y,origin[2]],projection), [dx,dy]=projectPoint([origin[0]+projection.dx,y,origin[2]],projection);
    ctx.beginPath(); ctx.moveTo(ax,ay); ctx.lineTo(bx,by); ctx.moveTo(cx,cy); ctx.lineTo(dx,dy); ctx.stroke();
  }
  for (const axis of axes) {
    const [x, y] = projectPoint(axis.p, projection);
    ctx.strokeStyle = axis.color;
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(ox, oy);
    ctx.lineTo(x, y);
    ctx.stroke();
    ctx.fillStyle = axis.color;
    ctx.font = `${13*(window.devicePixelRatio||1)}px sans-serif`;
    ctx.fillText(axis.label, x + 6, y + 6);
  }
  ctx.fillStyle = '#cbd5e1';
  ctx.fillText('O(local)', ox + 6, oy - 8);
}
function drawOrientationTick(ctx, sample, color, projection) {
  ctx.strokeStyle = color;
  ctx.lineWidth = 1;
  const dir = quaternionForward(sample.quaternion);
  const len = projection.span * 0.035;
  const p2 = [sample.position[0]+dir[0]*len, sample.position[1]+dir[1]*len, sample.position[2]+dir[2]*len];
  const [x1,y1]=projectPoint(sample.position,projection), [x2,y2]=projectPoint(p2,projection);
  ctx.beginPath(); ctx.moveTo(x1,y1); ctx.lineTo(x2,y2); ctx.stroke();
}
function quaternionForward(q) {
  const x=q[0], y=q[1], z=q[2], w=q[3];
  return [2*(x*z + w*y), 2*(y*z - w*x), 1 - 2*(x*x + y*y)];
}
function trajectoryRelativeTime(ep, frameIndex) {
  if (!ep || !ep.left.length) return 0;
  const index = Math.max(0, Math.min(frameIndex, ep.left.length-1));
  return Number(ep.left[index].t) - Number(ep.left[0].t);
}
function stopTrajectoryPlayback(reset=false) {
  const pb = state.trajectoryPlayback;
  if (pb.rafId !== null) cancelAnimationFrame(pb.rafId);
  pb.playing = false; pb.rafId = null; pb.wallStartedAt = null; pb.mediaStartedAt = null;
  if (reset) pb.frameIndex = 0;
  updateTrajectoryPlaybackControls();
}
function resetTrajectoryPlayback() {
  stopTrajectoryPlayback(true);
  drawTrajectory();
}
function toggleTrajectoryPlayback() {
  const ep = selectedTrajectoryEpisode();
  if (!ep) return;
  if (state.trajectoryPlayback.playing) {
    stopTrajectoryPlayback();
    return;
  }
  if (state.trajectoryPlayback.frameIndex >= ep.frame_count-1) state.trajectoryPlayback.frameIndex = 0;
  const pb = state.trajectoryPlayback;
  pb.playing = true;
  pb.wallStartedAt = performance.now();
  pb.mediaStartedAt = trajectoryRelativeTime(ep, pb.frameIndex);
  pb.rafId = requestAnimationFrame(advanceTrajectoryPlayback);
  updateTrajectoryPlaybackControls();
}
function advanceTrajectoryPlayback(now) {
  const ep = selectedTrajectoryEpisode(), pb = state.trajectoryPlayback;
  if (!ep || !pb.playing) return stopTrajectoryPlayback();
  const target = pb.mediaStartedAt + (now-pb.wallStartedAt)/1000*pb.speed;
  while (pb.frameIndex+1 < ep.frame_count && trajectoryRelativeTime(ep, pb.frameIndex+1) <= target) pb.frameIndex += 1;
  drawTrajectory();
  if (pb.frameIndex >= ep.frame_count-1) return stopTrajectoryPlayback();
  pb.rafId = requestAnimationFrame(advanceTrajectoryPlayback);
}
function seekTrajectoryFrame(value) {
  stopTrajectoryPlayback();
  state.trajectoryPlayback.frameIndex = Number(value) || 0;
  drawTrajectory();
}
function setTrajectoryPlaybackSpeed(value) {
  const pb = state.trajectoryPlayback;
  const wasPlaying = pb.playing;
  stopTrajectoryPlayback();
  pb.speed = Number(value) || 1;
  if (wasPlaying) toggleTrajectoryPlayback();
  updateTrajectoryPlaybackControls();
}
function updateTrajectoryPlaybackControls() {
  const ep = selectedTrajectoryEpisode(), pb = state.trajectoryPlayback;
  const button = document.getElementById('trajectory-play');
  if (button) button.textContent = pb.playing ? '暂停' : '播放';
  const slider = document.getElementById('trajectory-progress');
  if (slider && ep) { slider.max = Math.max(0, ep.frame_count-1); slider.value = Math.min(pb.frameIndex, ep.frame_count-1); }
  const speed = document.getElementById('trajectory-speed');
  if (speed) speed.value = String(pb.speed);
  const time = document.getElementById('trajectory-time');
  if (time) time.textContent = ep ? `frame ${Math.min(pb.frameIndex+1, ep.frame_count)} / ${ep.frame_count} · ${trajectoryRelativeTime(ep,pb.frameIndex).toFixed(2)} s / ${trajectoryRelativeTime(ep,ep.frame_count-1).toFixed(2)} s` : '全部 episode 为静态总览，请选择单个 episode 播放。';
}
function updateTrajectoryInfo() {
  const info = document.getElementById('trajectory-info'), t = state.trajectory;
  if (!info || !t) return;
  const ep = selectedTrajectoryEpisode(), parts = [`右手坐标系 · ${t.coordinate_frame_profile}`, `原始 bounds ${formatBounds(t.bounds)}`];
  if (ep) {
    const index = Math.min(state.trajectoryPlayback.frameIndex, ep.frame_count-1);
    if (ep.left[index]) parts.push(`左手 raw ${ep.left[index].position.map(v=>Number(v).toFixed(3)).join(', ')}`);
    if (ep.right[index]) parts.push(`右手 raw ${ep.right[index].position.map(v=>Number(v).toFixed(3)).join(', ')}`);
  }
  info.textContent = parts.join(' | ');
}
function formatBounds(bounds) { return `min ${bounds.min.map(v=>Number(v).toFixed(3)).join(', ')} / max ${bounds.max.map(v=>Number(v).toFixed(3)).join(', ')}`; }
async function cancelJob(id) { if (!confirm('取消后会回滚本批次已发布产物，确认取消？')) return; await api(`/api/jobs/${id}/cancel`, {method:'POST', body:'{}'}); await openJob(id); }
async function retryFailed(id) { const data = await api(`/api/jobs/${id}/retry-failed`, {method:'POST', body:'{}'}); state.retryDraft = data.draft; showPage('create'); }
async function openVisualizer(id) { try { const data = await api(`/api/jobs/${id}/open-visualizer`, {method:'POST', body:'{}'}); window.open(data.url, '_blank'); } catch(e) { alert(e.message); } }
async function loadHistory() { state.history = await api('/api/history'); renderHistory(); }
function renderHistory() {
  const rows = state.history.jobs.map(j => `<tr><td><b>${escapeHtml(j.remark || j.job_id)}</b><br><span class="muted">${j.created_at}</span></td><td>${badge(j.status)}</td><td>${j.counts.success}/${j.counts.total}</td><td><button onclick="openJob('${j.job_id}')">查看</button><button class="danger" onclick="deleteHistory('${j.job_id}')">删除记录</button></td></tr>`).join('');
  document.getElementById('page-history').innerHTML = `<div class="card"><h2>历史记录</h2><p class="muted">删除历史只删除网页摘要，不删除真实产物。</p><table><tbody>${rows}</tbody></table></div>`;
}
async function deleteHistory(id) { if (!confirm('只删除历史摘要，不删除输出产物。确认？')) return; await api(`/api/history/${id}`, {method:'DELETE'}); loadHistory(); }
function dirInputId(target) {
  if (target === 'input') return 'input-dir';
  if (target === 'output') return 'output-dir';
  if (target === 'audit-input') return 'audit-input-dir';
  if (target === 'audit-classified') return 'audit-classified-dir';
  return 'input-dir';
}
function openDirModal(target) { state.dirTarget = target; const raw = document.getElementById(dirInputId(target)).value || '/'; loadDir(raw); document.getElementById('dir-modal').classList.add('open'); }
function closeDirModal() { document.getElementById('dir-modal').classList.remove('open'); }
async function loadDir(path) {
  const data = await api(`/api/filesystem?path=${encodeURIComponent(path)}`);
  state.dirPath = data.exists ? data.path : path;
  document.getElementById('dir-path').value = state.dirPath;
  document.getElementById('dir-breadcrumbs').innerHTML = data.breadcrumbs.map(b => `<button onclick="loadDir('${jsEscape(b.path)}')">${escapeHtml(b.name)}</button>`).join('');
  document.getElementById('dir-list').innerHTML = `<button onclick="loadDir('${jsEscape(data.parent || '/')}')">.. 返回上级</button>` + data.entries.map(e => `<button onclick="loadDir('${jsEscape(e.path)}')">[目录] ${escapeHtml(e.name)}</button>`).join('');
}
async function createDirFromInput() { const path = document.getElementById('dir-path').value; if (!confirm(`创建目录？\n${path}`)) return; await api('/api/filesystem/create-directory', {method:'POST', body:JSON.stringify({path})}); await loadDir(path); }
function selectCurrentDir() {
  const id = dirInputId(state.dirTarget);
  document.getElementById(id).value = document.getElementById('dir-path').value;
  closeDirModal();
  if (state.dirTarget === 'input') scanFiles();
  else if (state.dirTarget === 'output') previewJob();
  else if (state.dirTarget === 'audit-input') { auditInputChanged(); scanAuditFiles(); }
}
function escapeHtml(s) { return String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }
function jsEscape(s) { return String(s).replace(/\\/g,'\\\\').replace(/'/g,"\\'"); }
setInterval(async () => {
  if (state.page === 'dashboard') await loadDashboard();
  if (state.page === 'job' && state.currentJob) await openJob(state.currentJob.job_id);
  if (state.page === 'config') {
    const status = await api('/api/calibration/gripper/status');
    const before = JSON.stringify(state.productionConfig?.readiness?.gripper || {});
    const after = JSON.stringify(status.readiness?.gripper || {});
    if (before !== after) await loadProductionConfig();
  }
}, 3000);
loadDashboard().then(()=>showPage('dashboard'));
</script>
</body>
</html>
"""


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Data clean local web UI.")
    parser.add_argument("--config", required=True, help="YAML config path.")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host. Defaults to 127.0.0.1.")
    parser.add_argument("--port", type=int, default=0, help="Bind port. 0 chooses a free port.")
    parser.add_argument("--global-workers", type=int, default=DEFAULT_GLOBAL_WORKERS, help="Global worker budget.")
    parser.add_argument("--no-browser", action="store_true", help="Do not open browser automatically.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    if args.host != "127.0.0.1":
        raise SystemExit("Normal web mode only supports 127.0.0.1 in this version.")
    app = DataCleanWebApp(
        config_path=Path(args.config),
        global_workers=args.global_workers,
    )
    handler_cls = type(
        "BoundDataCleanRequestHandler",
        (DataCleanRequestHandler,),
        {"app_state": app},
    )
    server = ThreadingHTTPServer((args.host, args.port), handler_cls)
    host, port = server.server_address
    url = f"http://{host}:{port}/"
    print("Data clean web UI")
    print(f"  URL: {url}")
    print(f"  Config: {args.config}")
    print(f"  Global workers: {app.global_workers}")
    print("  Press Ctrl+C in this terminal to stop the web service.")
    if not args.no_browser and os.environ.get("DATA_CLEAN_WEB_NO_BROWSER") != "1":
        webbrowser.open(url, new=2)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping data clean web UI.")
    finally:
        server.server_close()
        app.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
