"""Blocking compatibility gate implemented with the training-side LeRobot."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from schemas.lerobot_export import (
    IMAGE_FEATURES,
    OFFICIAL_CODEBASE_VERSION,
    LeRobotExportRequest,
)


class OfficialLeRobotValidationError(RuntimeError):
    """Raised when a produced dataset cannot be consumed by training."""


_STAT_KEYS = frozenset({"min", "max", "mean", "std", "count"})


def validate_official_lerobot_dataset(
    request: LeRobotExportRequest,
) -> dict[str, Any]:
    """Reload, inspect storage contracts, decode samples, and form an ACT batch."""

    from torch.utils.data import DataLoader

    import av
    from lerobot.datasets.lerobot_dataset import LeRobotDataset
    from lerobot.datasets.video_utils import get_video_info

    root = Path(request.output_dir)
    info = _read_json(root / "meta/info.json")
    if info.get("codebase_version") != OFFICIAL_CODEBASE_VERSION:
        raise OfficialLeRobotValidationError(
            f"codebase_version must be {OFFICIAL_CODEBASE_VERSION}"
        )
    if int(info.get("fps", -1)) != request.fps:
        raise OfficialLeRobotValidationError(f"info.json fps must be {request.fps}")
    features = info.get("features")
    if not isinstance(features, dict):
        raise OfficialLeRobotValidationError("info.json features is missing")
    _validate_feature_info(features, request)
    _validate_contract_sidecar(root, request)

    required_meta = (
        root / "meta/tasks.parquet",
        root / "meta/stats.json",
    )
    for path in required_meta:
        if not path.is_file():
            raise OfficialLeRobotValidationError(f"required metadata missing: {path}")
    _validate_tasks(root / "meta/tasks.parquet", request.task)
    episode_files = sorted((root / "meta/episodes").glob("chunk-*/file-*.parquet"))
    data_files = sorted((root / "data").glob("chunk-*/file-*.parquet"))
    if not episode_files or not data_files:
        raise OfficialLeRobotValidationError("episode or data parquet index is missing")

    actual_rows, episode_ranges = _validate_parquet(data_files, request)
    episodes = _validate_episode_metadata(
        episode_files,
        actual_rows,
        episode_ranges,
        root=root,
        info=info,
        request=request,
    )
    stats = _read_json(root / "meta/stats.json")
    _validate_stats(stats)

    dataset = LeRobotDataset(
        request.effective_repo_id,
        root=root,
        delta_timestamps={"action": [index / request.fps for index in range(100)]},
        video_backend="torchcodec",
    )
    if dataset.num_frames != actual_rows or dataset.num_episodes != episodes:
        raise OfficialLeRobotValidationError(
            "official loader counts disagree with parquet/episode metadata"
        )

    video_report: dict[str, Any] = {}
    expected_video_shape = (request.image_height, request.image_width)
    for key in IMAGE_FEATURES:
        paths = sorted((root / "videos" / key).glob("chunk-*/file-*.mp4"))
        if not paths:
            raise OfficialLeRobotValidationError(f"video stream missing: {key}")
        frame_total = 0
        for path in paths:
            video_info = get_video_info(path)
            if int(video_info.get("video.fps", -1)) != request.fps:
                raise OfficialLeRobotValidationError(f"{key} is not {request.fps} fps")
            size = (
                int(video_info.get("video.height", -1)),
                int(video_info.get("video.width", -1)),
            )
            if size != expected_video_shape:
                raise OfficialLeRobotValidationError(
                    f"{key} resolution mismatch: expected={expected_video_shape} actual={size}"
                )
            with av.open(str(path), "r") as container:
                frame_total += sum(1 for _frame in container.decode(video=0))
        if frame_total != actual_rows:
            raise OfficialLeRobotValidationError(
                f"{key} frame count mismatch: expected={actual_rows} actual={frame_total}"
            )
        video_report[key] = {"files": len(paths), "frames": frame_total}

    sampled_indices = sorted({0, actual_rows // 2, actual_rows - 1})
    samples = []
    for index in sampled_indices:
        item = dataset[index]
        _validate_loader_item(item, request)
        samples.append(index)

    batch = next(iter(DataLoader(dataset, batch_size=min(2, actual_rows), shuffle=False, num_workers=0)))
    if tuple(batch["observation.state"].shape[1:]) != (request.state_dim,):
        raise OfficialLeRobotValidationError("ACT batch observation.state shape mismatch")
    if tuple(batch["action"].shape[1:]) != (100, request.action_dim):
        raise OfficialLeRobotValidationError("ACT batch action window shape mismatch")
    for key in IMAGE_FEATURES:
        if tuple(batch[key].shape[1:]) != (3, request.image_height, request.image_width):
            raise OfficialLeRobotValidationError(f"ACT batch image shape mismatch: {key}")

    return {
        "status": "passed",
        "loader": "lerobot.datasets.lerobot_dataset.LeRobotDataset",
        "episodes": episodes,
        "frames": actual_rows,
        "sampled_indices": samples,
        "actual_schema": {path.name: str(pq.read_schema(path)) for path in data_files},
        "stats_features": sorted(stats),
        "videos": video_report,
        "act_batch": {
            "batch_size": int(batch["action"].shape[0]),
            "observation.state": list(batch["observation.state"].shape),
            "action": list(batch["action"].shape),
            **{key: list(batch[key].shape) for key in IMAGE_FEATURES},
        },
    }


def _validate_feature_info(features: dict[str, Any], request: LeRobotExportRequest) -> None:
    expected = {
        "observation.state": ("float32", [request.state_dim]),
        "action": ("float32", [request.action_dim]),
        IMAGE_FEATURES[0]: ("video", [request.image_height, request.image_width, 3]),
        IMAGE_FEATURES[1]: ("video", [request.image_height, request.image_width, 3]),
    }
    for key, (dtype, shape) in expected.items():
        feature = features.get(key)
        if not isinstance(feature, dict):
            raise OfficialLeRobotValidationError(f"feature missing: {key}")
        if feature.get("dtype") != dtype or list(feature.get("shape", [])) != shape:
            raise OfficialLeRobotValidationError(
                f"feature contract mismatch: {key} expected={dtype}{shape} actual={feature}"
            )
    for key, expected_names in (
        ("observation.state", request.state_names),
        ("action", request.action_names),
    ):
        actual_names = features[key].get("names")
        if list(actual_names or []) != list(expected_names):
            raise OfficialLeRobotValidationError(
                f"feature names mismatch: {key} expected={list(expected_names)} actual={actual_names}"
            )


def _validate_contract_sidecar(root: Path, request: LeRobotExportRequest) -> None:
    path = root / "meta/feature_contract.json"
    if not path.is_file():
        raise OfficialLeRobotValidationError(f"feature contract sidecar missing: {path}")
    data = _read_json(path)
    expected = request.contract_fingerprint
    actual = data.get("contract_fingerprint") or data.get("fingerprint")
    if expected and actual != expected:
        raise OfficialLeRobotValidationError(
            f"feature contract fingerprint mismatch: expected={expected} actual={actual}"
        )
    for key, expected_names in (
        ("observation.state", request.state_names),
        ("action", request.action_names),
    ):
        layout = data.get(key) or data.get("state" if key == "observation.state" else "action")
        if isinstance(layout, dict) and list(layout.get("names", [])) != list(expected_names):
            raise OfficialLeRobotValidationError(
                f"feature contract sidecar names mismatch: {key}"
            )


def _validate_parquet(
    files: list[Path],
    request: LeRobotExportRequest,
) -> tuple[int, dict[int, tuple[int, int]]]:
    rows = 0
    ranges: dict[int, list[int]] = {}
    expected_index = 0
    for path in files:
        table = pq.read_table(path)
        schema = table.schema
        expected_scalar_types = {
            "timestamp": pa.float32(),
            "frame_index": pa.int64(),
            "episode_index": pa.int64(),
            "index": pa.int64(),
            "task_index": pa.int64(),
        }
        for key, expected_type in expected_scalar_types.items():
            if schema.field(key).type != expected_type:
                raise OfficialLeRobotValidationError(
                    f"{key} parquet dtype mismatch: {schema.field(key).type}"
                )
        for key, dim in (("observation.state", request.state_dim), ("action", request.action_dim)):
            field = schema.field(key)
            if not pa.types.is_fixed_size_list(field.type):
                raise OfficialLeRobotValidationError(f"{key} parquet type is not fixed_size_list")
            if field.type.list_size != dim or field.type.value_type != pa.float32():
                raise OfficialLeRobotValidationError(
                    f"{key} parquet dtype mismatch: {field.type}"
                )
        states = np.asarray(table["observation.state"].to_pylist(), dtype=np.float32)
        actions = np.asarray(table["action"].to_pylist(), dtype=np.float32)
        if not np.isfinite(states).all() or not np.isfinite(actions).all():
            raise OfficialLeRobotValidationError("parquet state/action contains non-finite values")
        indices = [int(value) for value in table["index"].to_pylist()]
        if indices != list(range(expected_index, expected_index + len(indices))):
            raise OfficialLeRobotValidationError("global frame index is not continuous")
        expected_index += len(indices)
        for ep, frame, timestamp in zip(
            table["episode_index"].to_pylist(),
            table["frame_index"].to_pylist(),
            table["timestamp"].to_pylist(),
            strict=True,
        ):
            ep_int = int(ep)
            frame_int = int(frame)
            ranges.setdefault(ep_int, []).append(frame_int)
            if not math.isclose(
                float(timestamp),
                frame_int / request.fps,
                rel_tol=0,
                abs_tol=1e-5,
            ):
                raise OfficialLeRobotValidationError(
                    "timestamp must be generated as frame_index / fps"
                )
        rows += table.num_rows
    if rows <= 0:
        raise OfficialLeRobotValidationError("dataset contains no frames")
    episode_ranges: dict[int, tuple[int, int]] = {}
    for episode, frames in ranges.items():
        if frames != list(range(len(frames))):
            raise OfficialLeRobotValidationError(
                f"frame_index is not continuous within episode {episode}"
            )
        episode_ranges[episode] = (0, len(frames))
    return rows, episode_ranges


def _validate_episode_metadata(
    files: list[Path],
    rows: int,
    data_ranges: dict[int, tuple[int, int]],
    *,
    root: Path,
    info: dict[str, Any],
    request: LeRobotExportRequest,
) -> int:
    table = pa.concat_tables([pq.read_table(path) for path in files], promote_options="default")
    episodes = [int(value) for value in table["episode_index"].to_pylist()]
    if episodes != list(range(len(episodes))):
        raise OfficialLeRobotValidationError("episode_index metadata is not continuous")
    starts = [int(value) for value in table["dataset_from_index"].to_pylist()]
    ends = [int(value) for value in table["dataset_to_index"].to_pylist()]
    if not starts or starts[0] != 0 or ends[-1] != rows:
        raise OfficialLeRobotValidationError("episode dataset ranges do not cover all frames")
    if any(left != right for left, right in zip(ends[:-1], starts[1:], strict=True)):
        raise OfficialLeRobotValidationError("episode dataset ranges are not contiguous")
    for episode, start, end in zip(episodes, starts, ends, strict=True):
        frame_range = data_ranges.get(episode)
        if frame_range is None or frame_range != (0, end - start):
            raise OfficialLeRobotValidationError(
                f"episode frame_index range mismatch: episode={episode}"
            )
    data_path_template = str(info.get("data_path", ""))
    video_path_template = str(info.get("video_path", ""))
    if not data_path_template or not video_path_template:
        raise OfficialLeRobotValidationError(
            "info.json data_path/video_path templates are missing"
        )
    for row_index in range(table.num_rows):
        chunk_index = int(table["data/chunk_index"][row_index].as_py())
        file_index = int(table["data/file_index"][row_index].as_py())
        referenced_data = root / data_path_template.format(
            chunk_index=chunk_index,
            file_index=file_index,
        )
        if not referenced_data.is_file():
            raise OfficialLeRobotValidationError(
                f"episode references missing data parquet: {referenced_data}"
            )

    for video_key in IMAGE_FEATURES:
        previous_ranges: dict[tuple[int, int], float] = {}
        for row_index, (start, end) in enumerate(zip(starts, ends, strict=True)):
            chunk_key = f"videos/{video_key}/chunk_index"
            file_key = f"videos/{video_key}/file_index"
            from_key = f"videos/{video_key}/from_timestamp"
            to_key = f"videos/{video_key}/to_timestamp"
            for key in (chunk_key, file_key, from_key, to_key):
                if key not in table.column_names:
                    raise OfficialLeRobotValidationError(
                        f"episode video index field missing: {key}"
                    )
            chunk_index = int(table[chunk_key][row_index].as_py())
            file_index = int(table[file_key][row_index].as_py())
            from_timestamp = float(table[from_key][row_index].as_py())
            to_timestamp = float(table[to_key][row_index].as_py())
            referenced_video = root / video_path_template.format(
                video_key=video_key,
                chunk_index=chunk_index,
                file_index=file_index,
            )
            if not referenced_video.is_file():
                raise OfficialLeRobotValidationError(
                    f"episode references missing video: {referenced_video}"
                )
            file_identity = (chunk_index, file_index)
            expected_from = previous_ranges.get(file_identity, 0.0)
            if not math.isclose(
                from_timestamp,
                expected_from,
                rel_tol=0,
                abs_tol=1e-4,
            ):
                raise OfficialLeRobotValidationError(
                    f"episode video ranges are not contiguous: {video_key}"
                )
            expected_duration = (end - start) / request.fps
            if (
                to_timestamp <= from_timestamp
                or not math.isclose(
                    to_timestamp - from_timestamp,
                    expected_duration,
                    rel_tol=0,
                    abs_tol=1 / request.fps,
                )
            ):
                raise OfficialLeRobotValidationError(
                    f"episode video duration disagrees with frame range: {video_key}"
                )
            previous_ranges[file_identity] = to_timestamp
    return len(episodes)


def _validate_tasks(path: Path, expected_task: str) -> None:
    table = pq.read_table(path)
    if "task" not in table.column_names or "task_index" not in table.column_names:
        raise OfficialLeRobotValidationError("tasks.parquet schema is incomplete")
    tasks = [str(value) for value in table["task"].to_pylist()]
    indices = [int(value) for value in table["task_index"].to_pylist()]
    if tasks != [expected_task] or indices != [0]:
        raise OfficialLeRobotValidationError(
            f"task index mismatch: expected={expected_task!r} actual={tasks}"
        )


def _validate_stats(stats: dict[str, Any]) -> None:
    for key in ("observation.state", "action", *IMAGE_FEATURES):
        values = stats.get(key)
        if not isinstance(values, dict):
            raise OfficialLeRobotValidationError(f"stats missing: {key}")
        missing = sorted(_STAT_KEYS - values.keys())
        if missing:
            raise OfficialLeRobotValidationError(f"stats incomplete: {key} missing={missing}")
        for stat_name in _STAT_KEYS:
            flattened = np.asarray(values[stat_name], dtype=np.float64)
            if not np.isfinite(flattened).all():
                raise OfficialLeRobotValidationError(
                    f"stats contains non-finite value: {key}.{stat_name}"
                )


def _validate_loader_item(item: dict[str, Any], request: LeRobotExportRequest) -> None:
    import torch

    state = item["observation.state"]
    action = item["action"]
    if state.dtype != torch.float32 or tuple(state.shape) != (request.state_dim,):
        raise OfficialLeRobotValidationError("official loader state contract mismatch")
    if action.dtype != torch.float32 or tuple(action.shape) != (100, request.action_dim):
        raise OfficialLeRobotValidationError("official loader ACT action window mismatch")
    if not torch.isfinite(state).all() or not torch.isfinite(action).all():
        raise OfficialLeRobotValidationError("official loader returned non-finite tensors")
    for key in IMAGE_FEATURES:
        image = item[key]
        if tuple(image.shape) != (3, request.image_height, request.image_width):
            raise OfficialLeRobotValidationError(f"official loader image shape mismatch: {key}")
        if image.dtype != torch.float32 or not torch.isfinite(image).all():
            raise OfficialLeRobotValidationError(f"official loader image dtype/value mismatch: {key}")


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise OfficialLeRobotValidationError(f"invalid JSON metadata: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise OfficialLeRobotValidationError(f"JSON metadata must be an object: {path}")
    return value
