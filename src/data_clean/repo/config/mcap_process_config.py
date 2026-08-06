"""Configuration loading and validation for the MCAP cleaning pipeline."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from schemas.scene2_streams import DEFAULT_SCENE2_STREAMS, Scene2StreamSpec


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
class QuaternionConfig:
    qx: float
    qy: float
    qz: float
    qw: float


@dataclass(frozen=True)
class TransformConfig:
    translation: Vector3Config
    rotation_xyzw: QuaternionConfig


@dataclass(frozen=True)
class PoseStreamConfig:
    input_topic: str
    msg_type: str
    output_topic: str
    transform: TransformConfig | None = None
    transform_file: str = ""
    output_camera_pose_common: str = ""
    output_tcp_pose_common: str = ""
    output_tcp_pose: str = ""


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
class ExtrinsicConfig:
    """SE(3) extrinsic with translation (m) and quaternion (xyzw)."""

    translation_m: tuple[float, float, float]
    rotation_quat_xyzw: tuple[float, float, float, float]

    @classmethod
    def identity(cls) -> "ExtrinsicConfig":
        return cls(
            translation_m=(0.0, 0.0, 0.0),
            rotation_quat_xyzw=(0.0, 0.0, 0.0, 1.0),
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExtrinsicConfig":
        translation = data.get("translation_m")
        if not isinstance(translation, (list, tuple)) or len(translation) != 3:
            raise ConfigError(
                f'"translation_m" must be a list of 3 floats, got {translation!r}'
            )
        rotation = data.get("rotation_quat_xyzw")
        if not isinstance(rotation, (list, tuple)) or len(rotation) != 4:
            raise ConfigError(
                f'"rotation_quat_xyzw" must be a list of 4 floats (xyzw), got {rotation!r}'
            )
        return cls(
            translation_m=(float(translation[0]), float(translation[1]), float(translation[2])),
            rotation_quat_xyzw=(
                float(rotation[0]),
                float(rotation[1]),
                float(rotation[2]),
                float(rotation[3]),
            ),
        )

    def is_identity(self, tol: float = 1e-6) -> bool:
        tx, ty, tz = self.translation_m
        qx, qy, qz, qw = self.rotation_quat_xyzw
        return (
            abs(tx) < tol
            and abs(ty) < tol
            and abs(tz) < tol
            and abs(qx) < tol
            and abs(qy) < tol
            and abs(qz) < tol
            and abs(qw - 1.0) < tol
        )

    def quaternion_norm(self) -> float:
        qx, qy, qz, qw = self.rotation_quat_xyzw
        return (qx * qx + qy * qy + qz * qz + qw * qw) ** 0.5


@dataclass(frozen=True)
class FrameAlignmentConfig:
    """Configuration for frame alignment in scene 1 pose transformation."""

    common_anchor: str
    common_from_left_start: ExtrinsicConfig
    common_from_right_start: ExtrinsicConfig
    camera_from_left_tcp: ExtrinsicConfig
    camera_from_right_tcp: ExtrinsicConfig

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FrameAlignmentConfig":
        anchor = data.get("common_anchor")
        if anchor not in ("left", "right"):
            raise ConfigError(
                f'"common_anchor" must be "left" or "right", got {anchor!r}'
            )

        extrinsics = data.get("extrinsics")
        if not isinstance(extrinsics, dict):
            raise ConfigError('"frame_alignment.extrinsics" must be a mapping')

        required_keys = [
            "common_from_left_start",
            "common_from_right_start",
            "camera_from_left_tcp",
            "camera_from_right_tcp",
        ]
        for key in required_keys:
            if key not in extrinsics:
                raise ConfigError(f'missing required extrinsic "{key}"')

        return cls(
            common_anchor=anchor,
            common_from_left_start=ExtrinsicConfig.from_dict(extrinsics["common_from_left_start"]),
            common_from_right_start=ExtrinsicConfig.from_dict(extrinsics["common_from_right_start"]),
            camera_from_left_tcp=ExtrinsicConfig.from_dict(extrinsics["camera_from_left_tcp"]),
            camera_from_right_tcp=ExtrinsicConfig.from_dict(extrinsics["camera_from_right_tcp"]),
        )


@dataclass(frozen=True)
class AppConfig:
    batch: BatchConfig
    transform: TransformConfig
    pose_streams: tuple[PoseStreamConfig, ...]
    gripper_streams: tuple[GripperStreamConfig, ...]
    calibration: dict[str, Any]
    frame_alignment: FrameAlignmentConfig | None = None
    camera_from_tcp: dict[str, ExtrinsicConfig] | None = None
    scene2_streams: tuple[Scene2StreamSpec, ...] = DEFAULT_SCENE2_STREAMS

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
    start_from_common = _require_mapping(transform, "start_from_common")
    translation = _require_mapping(start_from_common, "translation")
    rotation = _require_mapping(start_from_common, "rotation_xyzw")
    qx = float(rotation["qx"])
    qy = float(rotation["qy"])
    qz = float(rotation["qz"])
    qw = float(rotation["qw"])
    norm = (qx * qx + qy * qy + qz * qz + qw * qw) ** 0.5
    if norm == 0.0 or abs(norm - 1.0) > 1e-3:
        raise ConfigError(
            f'"start_from_common.rotation_xyzw" must be a unit quaternion, got norm {norm:.6f}'
        )
    return TransformConfig(
        translation=Vector3Config(
            x=float(translation["x"]),
            y=float(translation["y"]),
            z=float(translation["z"]),
        ),
        rotation_xyzw=QuaternionConfig(
            qx=qx / norm,
            qy=qy / norm,
            qz=qz / norm,
            qw=qw / norm,
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


def _build_pose_streams(
    data: dict[str, Any],
    config_dir: Path,
    frame_alignment: FrameAlignmentConfig | None = None,
) -> tuple[PoseStreamConfig, ...]:
    fa_pose_streams = {}
    if frame_alignment is not None:
        fa_data = data.get("frame_alignment")
        if isinstance(fa_data, dict):
            fa_pose_streams_data = fa_data.get("pose_streams", {})
            if isinstance(fa_pose_streams_data, dict):
                for hand, hand_config in fa_pose_streams_data.items():
                    if isinstance(hand_config, dict):
                        input_topic = hand_config.get("input_topic", "")
                        if input_topic:
                            fa_pose_streams[input_topic] = hand_config

    streams = tuple(
        _build_pose_stream(item, config_dir, fa_pose_streams.get(item.get("input_topic", "")))
        for item in _require_sequence(data, "pose_streams")
    )
    if not streams:
        raise ConfigError('"pose_streams" must not be empty')
    return streams


def _build_pose_stream(
    item: dict[str, Any],
    config_dir: Path,
    fa_pose_stream: dict[str, Any] | None = None,
) -> PoseStreamConfig:
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

    output_camera_pose_common = ""
    output_tcp_pose_common = ""
    output_tcp_pose = ""
    if fa_pose_stream is not None:
        output_camera_pose_common = str(fa_pose_stream.get("output_camera_pose_common", ""))
        output_tcp_pose_common = str(fa_pose_stream.get("output_tcp_pose_common", ""))
    output_tcp_pose = str(item.get("output_tcp_pose", ""))

    return PoseStreamConfig(
        input_topic=str(item["input_topic"]),
        msg_type=str(item["msg_type"]),
        output_topic=str(item["output_topic"]),
        transform=transform,
        transform_file=transform_file,
        output_camera_pose_common=output_camera_pose_common,
        output_tcp_pose_common=output_tcp_pose_common,
        output_tcp_pose=output_tcp_pose,
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


def _build_scene2_streams(data: dict[str, Any]) -> tuple[Scene2StreamSpec, ...]:
    web_pipeline = data.get("web_pipeline", {})
    scene2 = web_pipeline.get("scene2", {}) if isinstance(web_pipeline, dict) else {}
    raw_streams = scene2.get("streams") if isinstance(scene2, dict) else None
    if raw_streams is None:
        return DEFAULT_SCENE2_STREAMS
    if not isinstance(raw_streams, list) or not all(isinstance(item, dict) for item in raw_streams):
        raise ConfigError('"web_pipeline.scene2.streams" must be a list of mappings')
    streams = tuple(
        Scene2StreamSpec(
            topic=str(item.get("topic", "")),
            modality=str(item.get("modality", "")),
            required=bool(item.get("required", False)),
        )
        for item in raw_streams
    )
    if not streams:
        raise ConfigError('"web_pipeline.scene2.streams" must not be empty')
    _ensure_unique([stream.topic for stream in streams], "scene2 stream topics")
    required_contract = {
        (stream.topic, stream.modality)
        for stream in DEFAULT_SCENE2_STREAMS
        if stream.required
    }
    actual_required = {(stream.topic, stream.modality) for stream in streams if stream.required}
    if not required_contract.issubset(actual_required):
        missing = sorted(topic for topic, modality in required_contract - actual_required)
        raise ConfigError(f"scene2 required stream contract missing topics: {', '.join(missing)}")
    return streams


def _build_camera_from_tcp(
    data: dict[str, Any],
    frame_alignment: FrameAlignmentConfig | None,
) -> dict[str, ExtrinsicConfig] | None:
    values = data.get("camera_from_tcp")
    if isinstance(values, dict):
        result = {}
        for hand in ("left", "right"):
            value = values.get(hand)
            if not isinstance(value, dict):
                raise ConfigError(f'"camera_from_tcp.{hand}" must be a mapping')
            translation_mm = value.get("translation_mm")
            if isinstance(translation_mm, (list, tuple)):
                if len(translation_mm) != 3:
                    raise ConfigError(f'"camera_from_tcp.{hand}.translation_mm" must contain 3 floats')
                result[hand] = ExtrinsicConfig(
                    translation_m=tuple(float(item) / 1000.0 for item in translation_mm),
                    rotation_quat_xyzw=(0.0, 0.0, 0.0, 1.0),
                )
                continue
            legacy = ExtrinsicConfig.from_dict(value)
            if legacy.rotation_quat_xyzw != (0.0, 0.0, 0.0, 1.0):
                raise ConfigError(
                    f'"camera_from_tcp.{hand}.rotation_quat_xyzw" is no longer configurable; '
                    "migrate to fixed zero rotation"
                )
            result[hand] = legacy
        return result
    if frame_alignment is None:
        return None
    return {
        "left": frame_alignment.camera_from_left_tcp,
        "right": frame_alignment.camera_from_right_tcp,
    }


def calibration_item_status(config: AppConfig) -> dict[str, bool]:
    calibration = config.calibration
    common_frame = calibration.get("common_frame", {})
    gripper = calibration.get("gripper", {})

    def nested_status(section: dict[str, Any], hand: str) -> bool:
        value = section.get(hand, {})
        return isinstance(value, dict) and bool(value.get("calibrated"))

    return {
        "gripper_left": nested_status(gripper, "left") if isinstance(gripper, dict) else False,
        "gripper_right": nested_status(gripper, "right") if isinstance(gripper, dict) else False,
        "common_frame_left": nested_status(common_frame, "left") if isinstance(common_frame, dict) else False,
        "common_frame_right": nested_status(common_frame, "right") if isinstance(common_frame, dict) else False,
    }


def config_is_calibrated(config: AppConfig, *, require_common_frame: bool = False) -> bool:
    """Check if config is calibrated.

    By default (require_common_frame=False), only gripper calibration is required.
    Pass require_common_frame=True for legacy behavior requiring all 4 items.
    """
    status = calibration_item_status(config)
    if not require_common_frame:
        return status["gripper_left"] and status["gripper_right"]
    return all(status.values())


def calibration_missing_items(config: AppConfig, *, include_common_frame: bool = False) -> list[str]:
    """List missing calibration items.

    By default (include_common_frame=False), only gripper items are listed.
    Pass include_common_frame=True for legacy listing of common_frame items.
    """
    labels = {
        "gripper_left": "左手夹爪",
        "gripper_right": "右手夹爪",
    }
    if include_common_frame:
        labels["common_frame_left"] = "左手 common frame"
        labels["common_frame_right"] = "右手 common frame"
    status = calibration_item_status(config)
    return [label for key, label in labels.items() if not status.get(key, False)]


def load_frame_alignment(data: dict[str, Any]) -> FrameAlignmentConfig:
    """Load and parse frame_alignment section from config dict."""
    fa_data = data.get("frame_alignment")
    if fa_data is None or not isinstance(fa_data, dict):
        raise ConfigError('"frame_alignment" section is required and must be a mapping')
    return FrameAlignmentConfig.from_dict(fa_data)


def validate_frame_alignment(config: FrameAlignmentConfig) -> None:
    """Validate frame_alignment config for semantic correctness."""
    if config.common_anchor == "left" and not config.common_from_left_start.is_identity():
        raise ConfigError(
            'when common_anchor is "left", common_from_left_start must be identity'
        )
    if config.common_anchor == "right" and not config.common_from_right_start.is_identity():
        raise ConfigError(
            'when common_anchor is "right", common_from_right_start must be identity'
        )

    for name, ext in [
        ("common_from_left_start", config.common_from_left_start),
        ("common_from_right_start", config.common_from_right_start),
        ("camera_from_left_tcp", config.camera_from_left_tcp),
        ("camera_from_right_tcp", config.camera_from_right_tcp),
    ]:
        norm = ext.quaternion_norm()
        if norm == 0.0 or abs(norm - 1.0) > 1e-3:
            raise ConfigError(
                f'extrinsic "{name}" has invalid quaternion norm {norm:.6f}, must be unit quaternion'
            )


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
    _ensure_unique(
        [stream.output_topic for stream in config.pose_streams]
        + [stream.output_topic for stream in config.gripper_streams],
        "derived output topics",
    )

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

    for hand, extrinsic in (config.camera_from_tcp or {}).items():
        norm = extrinsic.quaternion_norm()
        if norm == 0.0 or abs(norm - 1.0) > 1e-3:
            raise ConfigError(
                f'"camera_from_tcp.{hand}.rotation_quat_xyzw" must be a unit quaternion, got norm {norm:.6f}'
            )

    tcp_output_topics = [stream.output_tcp_pose for stream in config.pose_streams if stream.output_tcp_pose]
    _ensure_unique(tcp_output_topics, "TCP pose output topics")
    _ensure_unique(
        [stream.output_topic for stream in config.pose_streams]
        + tcp_output_topics
        + [stream.output_topic for stream in config.gripper_streams],
        "all output topics",
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

    frame_alignment_data = raw_data.get("frame_alignment")
    frame_alignment = None
    if frame_alignment_data is not None:
        frame_alignment = load_frame_alignment(raw_data)
        validate_frame_alignment(frame_alignment)

    camera_from_tcp = _build_camera_from_tcp(raw_data, frame_alignment)

    app_config = AppConfig(
        batch=batch,
        transform=_build_transform_config(raw_data),
        pose_streams=_build_pose_streams(raw_data, config_path.parent, frame_alignment),
        gripper_streams=_build_gripper_streams(raw_data),
        calibration=_build_calibration(raw_data),
        frame_alignment=frame_alignment,
        camera_from_tcp=camera_from_tcp,
        scene2_streams=_build_scene2_streams(raw_data),
    )
    _validate_cross_field_rules(app_config)
    return app_config
