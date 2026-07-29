"""Independent JSON-in/JSON-out official LeRobot 0.5.2 exporter process."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import sys
import traceback
from typing import Any

import numpy as np

from repo.bridge_mcap_reader import iter_bridge_frames
from schemas.lerobot_export import (
    OFFICIAL_LEROBOT_VERSION,
    LeRobotExportRequest,
    official_lerobot_features,
)
from service.lerobot_official_validator import validate_official_lerobot_dataset


def exporter_runtime_fingerprint() -> dict[str, Any]:
    """Describe the exact writer runtime so reports can be reproduced."""

    import lerobot
    import torch

    lock = _dependency_lock()
    versions = {
        name: importlib.metadata.version(name)
        for name in lock["packages"]
    }
    version = versions["lerobot"]
    module_path = Path(lerobot.__file__).resolve()
    return {
        "lerobot_version": version,
        "lerobot_module": str(module_path),
        "python_version": platform.python_version(),
        "python_executable": sys.executable,
        "torch_version": torch.__version__,
        "locked_packages": versions,
        "source_fingerprint": _source_fingerprint(module_path.parent),
    }


def assert_official_exporter_runtime() -> dict[str, Any]:
    fingerprint = exporter_runtime_fingerprint()
    if fingerprint["lerobot_version"] != OFFICIAL_LEROBOT_VERSION:
        raise RuntimeError(
            f"official exporter requires lerobot {OFFICIAL_LEROBOT_VERSION}, "
            f"got {fingerprint['lerobot_version']}"
        )
    lock = _dependency_lock()
    if not platform.python_version().startswith(f"{lock['python']}."):
        raise RuntimeError(
            f"official exporter requires Python {lock['python']}.x, got {platform.python_version()}"
        )
    drift = {
        name: {"expected": expected, "actual": fingerprint["locked_packages"].get(name)}
        for name, expected in lock["packages"].items()
        if fingerprint["locked_packages"].get(name) != expected
    }
    if drift:
        raise RuntimeError(f"official exporter dependency lock mismatch: {drift}")
    expected_source = str(lock.get("source_fingerprint", ""))
    if (
        not expected_source
        or fingerprint["source_fingerprint"] != expected_source
    ):
        raise RuntimeError(
            "official exporter LeRobot source fingerprint mismatch: "
            f"expected={expected_source or '<missing>'} "
            f"actual={fingerprint['source_fingerprint']}"
        )
    return fingerprint


def export_official_lerobot(request: LeRobotExportRequest) -> dict[str, Any]:
    """Write episodes in request order and run the blocking compatibility gate."""

    from lerobot.datasets.lerobot_dataset import LeRobotDataset

    fingerprint = assert_official_exporter_runtime()
    output_dir = Path(request.output_dir)
    if output_dir.exists():
        raise FileExistsError(f"official export output already exists: {output_dir}")
    output_dir.parent.mkdir(parents=True, exist_ok=True)

    dataset = LeRobotDataset.create(
        repo_id=request.effective_repo_id,
        robot_type=request.robot_type,
        fps=request.fps,
        features=official_lerobot_features(request),
        root=output_dir,
        use_videos=True,
        image_writer_processes=0,
        image_writer_threads=max(2, min(8, os.cpu_count() or 2)),
        vcodec="h264",
        encoder_threads=max(1, min(4, (os.cpu_count() or 2) // 2)),
    )
    episode_summaries: list[dict[str, Any]] = []
    total_frames = 0
    try:
        for episode_index, bridge_dir in enumerate(request.bridge_dirs):
            frame_count = 0
            for frame in iter_bridge_frames(
                bridge_dir,
                state_dim=request.state_dim,
                action_dim=request.action_dim,
                image_height=request.image_height,
                image_width=request.image_width,
            ):
                dataset.add_frame(
                    {
                        "observation.state": np.asarray(frame.state, dtype=np.float32),
                        "action": np.asarray(frame.action, dtype=np.float32),
                        "observation.images.left": frame.image_left,
                        "observation.images.right": frame.image_right,
                        "task": request.task,
                    }
                )
                frame_count += 1
            if frame_count == 0:
                raise RuntimeError(f"bridge produced an empty episode: {bridge_dir}")
            dataset.save_episode(parallel_encoding=True)
            total_frames += frame_count
            episode_summaries.append(
                {
                    "episode_index": episode_index,
                    "bridge_dir": bridge_dir,
                    "frames": frame_count,
                }
            )
    finally:
        dataset.finalize()

    compatibility = validate_official_lerobot_dataset(request)
    return {
        "status": "success",
        "job_id": request.job_id,
        "output_lerobot_v3": str(output_dir),
        "repo_id": request.effective_repo_id,
        "episodes": len(episode_summaries),
        "frames": total_frames,
        "bridge_count": len(request.bridge_dirs),
        "state_dim": request.state_dim,
        "action_dim": request.action_dim,
        "fps": request.fps,
        "task": request.task,
        "bridges": episode_summaries,
        "actual_schema": compatibility["actual_schema"],
        "stats": compatibility["stats_features"],
        "runtime_fingerprint": fingerprint,
        "official_compatibility": compatibility,
    }


def run_request_file(request_path: Path, response_path: Path) -> int:
    response: dict[str, Any]
    try:
        raw = json.loads(request_path.read_text(encoding="utf-8"))
        request = LeRobotExportRequest.from_dict(raw)
        response = export_official_lerobot(request)
        return_code = 0
    except Exception as exc:  # noqa: BLE001 - process boundary must serialize every failure.
        response = {
            "status": "failed",
            "error": {
                "type": type(exc).__name__,
                "message": str(exc),
                "traceback": traceback.format_exc(),
            },
        }
        return_code = 1
    response_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = response_path.with_name(f".{response_path.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(response, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temporary, response_path)
    return return_code


def _source_fingerprint(package_dir: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(package_dir.rglob("*.py")):
        digest.update(str(path.relative_to(package_dir)).encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _dependency_lock() -> dict[str, Any]:
    path = Path(__file__).resolve().parents[1] / "config/lerobot_export.lock.json"
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or not isinstance(value.get("packages"), dict):
        raise RuntimeError(f"invalid LeRobot exporter dependency lock: {path}")
    return value


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--response", type=Path, required=True)
    parser.add_argument("--preflight", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    if args.preflight:
        try:
            result = {"status": "success", "runtime_fingerprint": assert_official_exporter_runtime()}
            args.response.parent.mkdir(parents=True, exist_ok=True)
            args.response.write_text(json.dumps(result, indent=2), encoding="utf-8")
            return 0
        except Exception as exc:  # noqa: BLE001
            args.response.parent.mkdir(parents=True, exist_ok=True)
            args.response.write_text(
                json.dumps(
                    {"status": "failed", "error": {"type": type(exc).__name__, "message": str(exc)}},
                    indent=2,
                ),
                encoding="utf-8",
            )
            return 1
    return run_request_file(args.request, args.response)


if __name__ == "__main__":
    raise SystemExit(main())
