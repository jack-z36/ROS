"""Configuration loading and validation for the MCAP cleaning pipeline."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


class ConfigError(ValueError):
    """Raised when the YAML configuration is invalid."""


@dataclass(frozen=True)
class BatchConfig:
    input_dir: str
    output_dir: str
    file_glob: str = "*.mcap"
    workers: int = 1
    overwrite: bool = False
    fail_fast: bool = False


@dataclass(frozen=True)
class Vector3Config:
    x: float
    y: float
    z: float


@dataclass(frozen=True)
class EulerDegConfig:
    roll: float
    pitch: float
    yaw: float


@dataclass(frozen=True)
class TcpOffsetConfig:
    x: float
    z: float


@dataclass(frozen=True)
class TransformConfig:
    base_position: Vector3Config
    base_orientation_deg: EulerDegConfig
    tcp_offset: TcpOffsetConfig


@dataclass(frozen=True)
class PoseStreamConfig:
    input_topic: str
    msg_type: str
    output_topic: str
    transform: TransformConfig | None = None
    transform_file: str = ""


@dataclass(frozen=True)
class GripperStreamConfig:
    image_topic: str
    image_msg_type: str
    output_topic: str
    output_msg_type: str
    aruco_dict: str
    marker_id_0: int
    marker_id_1: int
    marker_min: float
    marker_max: float
    gripper_max: float


@dataclass(frozen=True)
class AppConfig:
    batch: BatchConfig
    transform: TransformConfig
    pose_streams: tuple[PoseStreamConfig, ...]
    gripper_streams: tuple[GripperStreamConfig, ...]
    calibration: dict[str, Any]

    def pose_by_topic(self) -> dict[str, PoseStreamConfig]:
        return {stream.input_topic: stream for stream in self.pose_streams}

    def gripper_by_image_topic(self) -> dict[str, GripperStreamConfig]:
        return {stream.image_topic: stream for stream in self.gripper_streams}

    def transform_for_pose_stream(self, stream: PoseStreamConfig) -> TransformConfig:
        return stream.transform or self.transform


def _require_mapping(data: dict[str, Any], key: str) -> dict[str, Any]:
    value = data.get(key)
    if not isinstance(value, dict):
        raise ConfigError(f'"{key}" must be a mapping')
    return value


def _require_sequence(data: dict[str, Any], key: str) -> list[dict[str, Any]]:
    value = data.get(key)
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        raise ConfigError(f'"{key}" must be a list of mappings')
    return value


def _build_batch_config(data: dict[str, Any]) -> BatchConfig:
    batch = _require_mapping(data, "batch")
    workers = int(batch.get("workers", 1))
    if workers < 1:
        raise ConfigError('"batch.workers" must be >= 1')
    return BatchConfig(
        input_dir=str(batch["input_dir"]),
        output_dir=str(batch["output_dir"]),
        file_glob=str(batch.get("file_glob", "*.mcap")),
        workers=workers,
        overwrite=bool(batch.get("overwrite", False)),
        fail_fast=bool(batch.get("fail_fast", False)),
    )


def _resolve_config_path(raw_path: str, config_dir: Path) -> Path:
    path = Path(os.path.expandvars(raw_path)).expanduser()
    if path.is_absolute():
        return path
    return config_dir / path


def _build_transform_from_mapping(transform: dict[str, Any]) -> TransformConfig:
    base_position = _require_mapping(transform, "base_position")
    base_orientation = _require_mapping(transform, "base_orientation_deg")
    tcp_offset = _require_mapping(transform, "tcp_offset")
    return TransformConfig(
        base_position=Vector3Config(
            x=float(base_position["x"]),
            y=float(base_position["y"]),
            z=float(base_position["z"]),
        ),
        base_orientation_deg=EulerDegConfig(
            roll=float(base_orientation["roll"]),
            pitch=float(base_orientation["pitch"]),
            yaw=float(base_orientation["yaw"]),
        ),
        tcp_offset=TcpOffsetConfig(
            x=float(tcp_offset["x"]),
            z=float(tcp_offset["z"]),
        ),
    )


def _build_transform_config(data: dict[str, Any]) -> TransformConfig:
    return _build_transform_from_mapping(_require_mapping(data, "transform"))


def _load_transform_file(path_raw: str, config_dir: Path) -> tuple[TransformConfig, str]:
    path = _resolve_config_path(path_raw, config_dir)
    if not path.is_file():
        raise ConfigError(f'pose stream transform_file does not exist: "{path}"')
    with path.open("r", encoding="utf-8") as fh:
        raw_data = yaml.safe_load(fh) or {}
    if not isinstance(raw_data, dict):
        raise ConfigError(f'transform_file "{path}" must contain a mapping')
    transform_data = raw_data.get("transform", raw_data)
    if not isinstance(transform_data, dict):
        raise ConfigError(f'transform_file "{path}" must contain a transform mapping')
    return _build_transform_from_mapping(transform_data), str(path)


def _build_pose_streams(data: dict[str, Any], config_dir: Path) -> tuple[PoseStreamConfig, ...]:
    streams = tuple(
        _build_pose_stream(item, config_dir)
        for item in _require_sequence(data, "pose_streams")
    )
    if not streams:
        raise ConfigError('"pose_streams" must not be empty')
    return streams


def _build_pose_stream(item: dict[str, Any], config_dir: Path) -> PoseStreamConfig:
    transform_file_raw = str(item.get("transform_file", "")).strip()
    inline_transform = item.get("transform")
    if transform_file_raw and isinstance(inline_transform, dict):
        raise ConfigError(
            f'pose stream "{item.get("input_topic", "")}" must use either transform_file or inline transform, not both'
        )

    transform = None
    transform_file = ""
    if transform_file_raw:
        transform, transform_file = _load_transform_file(transform_file_raw, config_dir)
    elif isinstance(inline_transform, dict):
        transform = _build_transform_from_mapping(inline_transform)

    return PoseStreamConfig(
        input_topic=str(item["input_topic"]),
        msg_type=str(item["msg_type"]),
        output_topic=str(item["output_topic"]),
        transform=transform,
        transform_file=transform_file,
    )


def _build_gripper_streams(data: dict[str, Any]) -> tuple[GripperStreamConfig, ...]:
    streams = tuple(
        GripperStreamConfig(
            image_topic=str(item["image_topic"]),
            image_msg_type=str(item["image_msg_type"]),
            output_topic=str(item["output_topic"]),
            output_msg_type=str(item["output_msg_type"]),
            aruco_dict=str(item["aruco_dict"]),
            marker_id_0=int(item["marker_id_0"]),
            marker_id_1=int(item["marker_id_1"]),
            marker_min=float(item["marker_min"]),
            marker_max=float(item["marker_max"]),
            gripper_max=float(item["gripper_max"]),
        )
        for item in _require_sequence(data, "gripper_streams")
    )
    if not streams:
        raise ConfigError('"gripper_streams" must not be empty')
    return streams


def _build_calibration(data: dict[str, Any]) -> dict[str, Any]:
    calibration = data.get("calibration", {})
    if calibration is None:
        return {}
    if not isinstance(calibration, dict):
        raise ConfigError('"calibration" must be a mapping when present')
    return calibration


def calibration_item_status(config: AppConfig) -> dict[str, bool]:
    calibration = config.calibration
    tcp = calibration.get("tcp", {})
    gripper = calibration.get("gripper", {})

    def nested_status(section: dict[str, Any], hand: str) -> bool:
        value = section.get(hand, {})
        return isinstance(value, dict) and bool(value.get("calibrated"))

    if isinstance(tcp, dict) and isinstance(gripper, dict):
        nested = {
            "gripper_left": nested_status(gripper, "left"),
            "gripper_right": nested_status(gripper, "right"),
            "tcp_left": nested_status(tcp, "left"),
            "tcp_right": nested_status(tcp, "right"),
        }
        if any(nested.values()) or any(hand in tcp or hand in gripper for hand in ("left", "right")):
            return nested

    legacy_gripper = bool(gripper.get("calibrated")) if isinstance(gripper, dict) else False
    legacy_tcp = bool(tcp.get("calibrated")) if isinstance(tcp, dict) else False
    return {
        "gripper_left": legacy_gripper,
        "gripper_right": legacy_gripper,
        "tcp_left": legacy_tcp,
        "tcp_right": legacy_tcp,
    }


def config_is_calibrated(config: AppConfig) -> bool:
    return all(calibration_item_status(config).values())


def calibration_missing_items(config: AppConfig) -> list[str]:
    labels = {
        "gripper_left": "左手夹爪",
        "gripper_right": "右手夹爪",
        "tcp_left": "左手 TCP",
        "tcp_right": "右手 TCP",
    }
    status = calibration_item_status(config)
    return [label for key, label in labels.items() if not status.get(key, False)]


def _ensure_unique(values: list[str], label: str) -> None:
    duplicates = sorted({value for value in values if values.count(value) > 1})
    if duplicates:
        duplicate_str = ", ".join(duplicates)
        raise ConfigError(f'duplicate {label}: {duplicate_str}')


def _validate_cross_field_rules(config: AppConfig) -> None:
    _ensure_unique([stream.input_topic for stream in config.pose_streams], "pose input topics")
    _ensure_unique([stream.output_topic for stream in config.pose_streams], "pose output topics")
    _ensure_unique([stream.image_topic for stream in config.gripper_streams], "image topics")
    _ensure_unique([stream.output_topic for stream in config.gripper_streams], "gripper output topics")

    if any(stream.image_msg_type != "sensor_msgs/msg/Image" for stream in config.gripper_streams):
        raise ConfigError('v1 only supports "sensor_msgs/msg/Image" as gripper image input')
    if any(stream.output_msg_type != "std_msgs/msg/Float32" for stream in config.gripper_streams):
        raise ConfigError('v1 only supports "std_msgs/msg/Float32" as gripper output type')

    for stream in config.gripper_streams:
        if stream.marker_max <= stream.marker_min:
            raise ConfigError(
                f'gripper stream "{stream.image_topic}" has invalid marker range: marker_max must be > marker_min'
            )
        if stream.gripper_max <= 0:
            raise ConfigError(
                f'gripper stream "{stream.image_topic}" has invalid gripper_max: must be > 0'
            )


def load_app_config(
    path: str | Path,
    *,
    input_dir_override: str | None = None,
    output_dir_override: str | None = None,
    workers_override: int | None = None,
) -> AppConfig:
    config_path = Path(path)
    with config_path.open("r", encoding="utf-8") as fh:
        raw_data = yaml.safe_load(fh) or {}
    if not isinstance(raw_data, dict):
        raise ConfigError("top-level YAML document must be a mapping")

    batch = _build_batch_config(raw_data)
    if input_dir_override is not None:
        batch = BatchConfig(
            input_dir=input_dir_override,
            output_dir=batch.output_dir,
            file_glob=batch.file_glob,
            workers=batch.workers,
            overwrite=batch.overwrite,
            fail_fast=batch.fail_fast,
        )
    if output_dir_override is not None:
        batch = BatchConfig(
            input_dir=batch.input_dir,
            output_dir=output_dir_override,
            file_glob=batch.file_glob,
            workers=batch.workers,
            overwrite=batch.overwrite,
            fail_fast=batch.fail_fast,
        )
    if workers_override is not None:
        if workers_override < 1:
            raise ConfigError("--workers must be >= 1")
        batch = BatchConfig(
            input_dir=batch.input_dir,
            output_dir=batch.output_dir,
            file_glob=batch.file_glob,
            workers=workers_override,
            overwrite=batch.overwrite,
            fail_fast=batch.fail_fast,
        )

    app_config = AppConfig(
        batch=batch,
        transform=_build_transform_config(raw_data),
        pose_streams=_build_pose_streams(raw_data, config_path.parent),
        gripper_streams=_build_gripper_streams(raw_data),
        calibration=_build_calibration(raw_data),
    )
    _validate_cross_field_rules(app_config)
    return app_config
