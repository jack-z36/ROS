"""Augment a LeRobot v3 dataset ``meta/stats.json`` with image feature stats.

The Forge ``LeRobotV3Writer`` intentionally computes stats for only
``observation.state`` and ``action`` (see ``_STAT_FEATURES`` in
``forge/formats/lerobot_v3/writer.py``). Its comment assumes upstream loaders only
require *some* feature to have stats. Current LeRobot training versions instead
require **every** feature declared in ``info.json`` to have a stats entry, so a
dataset with ``observation.images.left/right`` (dtype ``video``) and no matching
stats keys makes ACT/PI0.5 training crash with ``KeyError: 'observation.images.*'``.

This post-processor runs after the Forge writer finishes. For each ``video``
feature it decodes every frame with OpenCV and computes per-channel (RGB) min/max/
mean/std, normalised to ``[0, 1]`` by dividing by 255 (the LeRobot convention).
``count`` is the decoded frame count. Existing non-video entries (state/action)
are preserved; video entries are overwritten so the call is idempotent.

It mirrors ``service.lerobot_timestamp_rebase``: an independent module with dataset
validation, a ``dry_run`` flag and a JSON-friendly summary.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np


class LeRobotImageStatsError(RuntimeError):
    """Raised when image stats cannot be computed or written safely."""


def _validate_dataset(dataset_dir: Path) -> dict[str, Any]:
    """Load and validate ``meta/info.json`` for a LeRobot v3 dataset."""
    info_path = dataset_dir / "meta" / "info.json"
    if not info_path.is_file():
        raise LeRobotImageStatsError(
            f"not a LeRobot v3 dataset (missing {info_path}): {dataset_dir}"
        )
    try:
        info = json.loads(info_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise LeRobotImageStatsError(
            f"could not parse {info_path}: {exc}"
        ) from exc
    version = info.get("codebase_version")
    if version != "v3.0":
        raise LeRobotImageStatsError(
            f"unsupported LeRobot codebase_version {version!r} "
            f"(expected 'v3.0'): {dataset_dir}"
        )
    return info


def _video_feature_keys(info: dict[str, Any]) -> list[str]:
    """Feature keys whose dtype is ``video`` (e.g. observation.images.left)."""
    features = info.get("features") or {}
    return [key for key, spec in features.items() if spec.get("dtype") == "video"]


def _video_files(dataset_dir: Path, feature: str) -> list[Path]:
    """``videos/<feature>/chunk-*/file-*.mp4`` sorted by chunk then file."""
    return sorted((dataset_dir / "videos" / feature).glob("chunk-*/file-*.mp4"))


def _accumulate_video(path: Path, acc: dict[str, Any]) -> int:
    """Decode every frame of one video, folding spatial axes onto the channel dim.

    cv2 yields BGR uint8 frames shaped ``(H, W, 3)``. Each frame is converted to
    RGB and the H, W axes are reduced so only the 3 channels remain; per-channel
    sum / sum-of-squares / min / max are accumulated in place. ``acc`` is mutated.
    Returns the number of decoded frames.
    """
    import cv2

    capture = cv2.VideoCapture(str(path))
    if not capture.isOpened():
        raise LeRobotImageStatsError(f"无法打开视频文件: {path}")
    decoded = 0
    try:
        while True:
            ok, frame = capture.read()
            if not ok or frame is None:
                break
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB).astype(np.float64)
            acc["sum"] += rgb.sum(axis=(0, 1))
            acc["sq_sum"] += (rgb ** 2).sum(axis=(0, 1))
            frame_min = rgb.min(axis=(0, 1))
            frame_max = rgb.max(axis=(0, 1))
            if acc["min"] is None:
                acc["min"] = frame_min.copy()
                acc["max"] = frame_max.copy()
            else:
                acc["min"] = np.minimum(acc["min"], frame_min)
                acc["max"] = np.maximum(acc["max"], frame_max)
            acc["pixels"] += rgb.shape[0] * rgb.shape[1]
            decoded += 1
    finally:
        capture.release()
    return decoded


def _decode_feature_stats(
    dataset_dir: Path, feature: str
) -> tuple[dict[str, list], dict[str, Any]]:
    """Decode all videos for one feature, returning normalised stats + a report.

    Per-channel mean/std use the full pixel population as the denominator; because
    resolution is constant across frames, the frame count is a consistent pool
    weight for downstream aggregation. Values are divided by 255 so they land in
    ``[0, 1]`` as LeRobot expects.
    """
    acc: dict[str, Any] = {
        "sum": np.zeros(3, dtype=np.float64),
        "sq_sum": np.zeros(3, dtype=np.float64),
        "min": None,
        "max": None,
        "pixels": 0,
    }
    files = _video_files(dataset_dir, feature)
    if not files:
        raise LeRobotImageStatsError(
            f"video feature {feature!r} 声明于 info.json 但未找到 mp4 文件"
        )
    frames = 0
    for path in files:
        frames += _accumulate_video(path, acc)
    if frames == 0 or acc["pixels"] == 0:
        raise LeRobotImageStatsError(
            f"video feature {feature!r} 解码 0 帧: {dataset_dir}"
        )

    pixel_count = acc["pixels"]
    mean_raw = acc["sum"] / pixel_count
    var_raw = np.clip(acc["sq_sum"] / pixel_count - mean_raw ** 2, 0.0, None)
    stats = {
        "min": (acc["min"] / 255.0).tolist(),
        "max": (acc["max"] / 255.0).tolist(),
        "mean": (mean_raw / 255.0).tolist(),
        "std": (np.sqrt(var_raw) / 255.0).tolist(),
        "count": [int(frames)],
    }
    report = {"feature": feature, "frames_decoded": int(frames), "chunks": len(files)}
    return stats, report


def augment_image_stats(
    dataset_dir: str | Path,
    *,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Add per-channel image stats for every video feature in a LeRobot v3 dataset.

    Args:
        dataset_dir: Root of a LeRobot v3 dataset (containing ``meta/info.json``,
            ``meta/stats.json`` and ``videos/<feature>/chunk-*/file-*.mp4``).
        dry_run: If True, decode and report stats but do not rewrite ``stats.json``.

    Returns:
        A JSON-friendly summary:
        ``{"dataset_dir": ..., "dry_run": bool, "video_features": [
        {"feature": ..., "frames_decoded": int, "chunks": int}],
        "files_touched": ["meta/stats.json"]}``.

    Raises:
        LeRobotImageStatsError: if the directory is not a LeRobot v3 dataset,
            a video cannot be opened/decoded, or ``stats.json`` is unreadable.
    """
    dataset_path = Path(dataset_dir).expanduser().resolve()
    info = _validate_dataset(dataset_path)
    features = _video_feature_keys(info)

    stats_path = dataset_path / "meta" / "stats.json"
    if not features:
        return {
            "dataset_dir": str(dataset_path),
            "dry_run": dry_run,
            "video_features": [],
            "files_touched": [],
            "note": "info.json 无 video feature，无需补充图像统计。",
        }

    if stats_path.is_file():
        try:
            stats = json.loads(stats_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise LeRobotImageStatsError(
                f"could not parse {stats_path}: {exc}"
            ) from exc
    else:
        stats = {}
    if not isinstance(stats, dict):
        raise LeRobotImageStatsError(
            f"stats.json 不是 JSON object: {stats_path}"
        )

    feature_reports: list[dict[str, Any]] = []
    for feature in features:
        feat_stats, report = _decode_feature_stats(dataset_path, feature)
        stats[feature] = feat_stats
        feature_reports.append(report)

    if dry_run:
        return {
            "dataset_dir": str(dataset_path),
            "dry_run": True,
            "video_features": feature_reports,
            "files_touched": [],
        }

    tmp_path = stats_path.with_name(f".stats.json.tmp.{_write_pid()}")
    tmp_path.write_text(
        json.dumps(stats, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    tmp_path.replace(stats_path)

    return {
        "dataset_dir": str(dataset_path),
        "dry_run": False,
        "video_features": feature_reports,
        "files_touched": [str(stats_path)],
    }


def _write_pid() -> int:
    import os

    return os.getpid()
