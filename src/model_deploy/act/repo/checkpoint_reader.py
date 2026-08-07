"""Readers for native LeRobot ACT checkpoint metadata."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from model_deploy.act.repo.bundle_reader import ModelSource, ModelSourceError


@dataclass(frozen=True)
class CheckpointMetadata:
    """Validated model contract extracted from a native ACT checkpoint."""

    state_dim: int
    action_dim: int
    chunk_size: int
    camera_keys: tuple[str, ...]
    image_shapes: tuple[tuple[int, int, int], ...]
    input_stats_path: Path
    output_stats_path: Path


def load_checkpoint_metadata(source: ModelSource) -> CheckpointMetadata:
    """Read and validate native LeRobot ACT metadata and statistic references."""
    if not source.is_checkpoint or source.pretrained_dir is None:
        raise ModelSourceError("Checkpoint metadata requires a direct checkpoint source")

    pretrained_dir = source.pretrained_dir
    model_config = _load_json(pretrained_dir / "config.json")
    preprocessor = _load_json(pretrained_dir / "policy_preprocessor.json")
    postprocessor = _load_json(pretrained_dir / "policy_postprocessor.json")

    input_features = _mapping(model_config.get("input_features"), "input_features")
    output_features = _mapping(model_config.get("output_features"), "output_features")
    state_dim = _feature_dim(input_features, "observation.state")
    action_dim = _feature_dim(output_features, "action")

    cameras: list[tuple[str, tuple[int, int, int]]] = []
    for key in input_features:
        prefix = "observation.images."
        if isinstance(key, str) and key.startswith(prefix):
            shape = _feature_shape(input_features, key)
            if len(shape) != 3:
                raise ModelSourceError(
                    f"Checkpoint image feature {key!r} must be CHW, got {shape}"
                )
            cameras.append((key[len(prefix):], (shape[0], shape[1], shape[2])))
    if not cameras:
        raise ModelSourceError("Checkpoint metadata contains no observation.images.* features")
    cameras.sort(key=lambda item: item[0])

    chunk_size = _positive_int(model_config.get("chunk_size"), "chunk_size")
    input_stats = _normalizer_state_file(
        preprocessor, "policy_preprocessor", pretrained_dir
    )
    output_stats = _normalizer_state_file(
        postprocessor, "policy_postprocessor", pretrained_dir
    )

    return CheckpointMetadata(
        state_dim=state_dim,
        action_dim=action_dim,
        chunk_size=chunk_size,
        camera_keys=tuple(item[0] for item in cameras),
        image_shapes=tuple(item[1] for item in cameras),
        input_stats_path=input_stats,
        output_stats_path=output_stats,
    )


def _load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ModelSourceError(f"Checkpoint metadata file not found: {path}")
    try:
        with path.open("r", encoding="utf-8") as fh:
            value = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        raise ModelSourceError(f"Cannot read checkpoint metadata: {path}") from exc
    return _mapping(value, str(path))


def _mapping(value: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ModelSourceError(f"Checkpoint field {name!r} must be a mapping")
    return value


def _feature_shape(features: Mapping[str, Any], key: str) -> tuple[int, ...]:
    feature = _mapping(features.get(key), key)
    raw_shape = feature.get("shape")
    if not isinstance(raw_shape, (list, tuple)) or not raw_shape:
        raise ModelSourceError(f"Checkpoint feature {key!r} has no valid shape")
    try:
        shape = tuple(int(value) for value in raw_shape)
    except (TypeError, ValueError) as exc:
        raise ModelSourceError(f"Checkpoint feature {key!r} shape is invalid") from exc
    if any(value <= 0 for value in shape):
        raise ModelSourceError(f"Checkpoint feature {key!r} shape must be positive")
    return shape


def _feature_dim(features: Mapping[str, Any], key: str) -> int:
    shape = _feature_shape(features, key)
    if len(shape) != 1:
        raise ModelSourceError(f"Checkpoint feature {key!r} must be a vector, got {shape}")
    return shape[0]


def _positive_int(value: Any, name: str) -> int:
    try:
        result = int(value)
    except (TypeError, ValueError) as exc:
        raise ModelSourceError(f"Checkpoint field {name!r} must be an integer") from exc
    if result <= 0:
        raise ModelSourceError(f"Checkpoint field {name!r} must be positive")
    return result


def _normalizer_state_file(
    pipeline: Mapping[str, Any], pipeline_name: str, pretrained_dir: Path
) -> Path:
    steps = pipeline.get("steps")
    if not isinstance(steps, list):
        raise ModelSourceError(f"{pipeline_name}.steps must be a list")
    candidates = []
    for step in steps:
        if not isinstance(step, Mapping):
            continue
        registry_name = step.get("registry_name")
        if registry_name in {"normalizer_processor", "unnormalizer_processor"}:
            state_file = step.get("state_file")
            if isinstance(state_file, str) and state_file.strip():
                candidates.append(state_file)
    if len(candidates) != 1:
        raise ModelSourceError(
            f"{pipeline_name} must reference exactly one normalization state file"
        )
    state_path = (pretrained_dir / candidates[0]).resolve()
    try:
        state_path.relative_to(pretrained_dir.resolve())
    except ValueError as exc:
        raise ModelSourceError(
            f"{pipeline_name} state file escapes checkpoint directory: {candidates[0]}"
        ) from exc
    if not state_path.is_file():
        raise ModelSourceError(f"Normalization state file not found: {state_path}")
    return state_path
