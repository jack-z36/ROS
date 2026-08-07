"""Normal-Web production configuration and readiness checks."""

from __future__ import annotations

import os
import math
from dataclasses import asdict
from pathlib import Path
from typing import Any

import yaml

from repo.config.mcap_process_config import load_app_config
from schemas.lerobot_features import (
    compile_lerobot_feature_contract,
    LeRobotFeatureConfigError,
    normalize_lerobot_features_config,
)
from schemas.pose_filter import PoseFilterAlgorithm, PoseFilterConfig
from schemas.tactile_filter import TactileFilterAlgorithm, TactileFilterConfig
from schemas.scene2_streams import DEFAULT_SCENE2_STREAMS, Scene2StreamSpec


class ProductionConfigError(ValueError):
    """Raised when a normal-Web production config cannot be saved."""


DEFAULT_WEB_FILE_MANAGEMENT = {
    "health_audited_mcap_dir": "/media/hit/D085-8696/已通过健康审计文件",
    "rejected_mcap_dir": "/media/hit/D085-8696/数据清洗缺陷文件",
    "completed_mcap_dir": "/media/hit/D085-8696/已完成清洗文件",
    "cleaning_failed_mcap_dir": "/media/hit/D085-8696/清洗失败文件",
    "artifact_retention": "production_cleanup",
    "failed_artifact_policy": "failed_stage_input",
    "space_estimate_multiplier": 4.0,
    "space_safety_gb": 20.0,
}


def production_config_view(path: str | Path) -> dict[str, Any]:
    config_path = Path(path)
    raw = _read_yaml(config_path)
    config = load_app_config(config_path)
    camera = config.camera_from_tcp or {}
    for hand, extrinsic in camera.items():
        if extrinsic.rotation_quat_xyzw != (0.0, 0.0, 0.0, 1.0):
            raise ProductionConfigError(
                f"camera_from_tcp.{hand} 的历史旋转不是零；普通生产链路不会静默丢弃该旋转，请先人工确认。"
            )
    features = _production_web_pipeline_view(raw.get("web_pipeline"))
    contract = compile_lerobot_feature_contract(features.get("lerobot_features"))
    return {
        "config_path": str(config_path),
        "camera_from_tcp": {
            hand: {"translation_mm": [value * 1000.0 for value in camera[hand].translation_m]}
            for hand in ("left", "right")
            if hand in camera
        },
        "coordinate_frame_semantics": "preserve_baton_source_frame",
        "web_pipeline": features,
        "feature_contract_preview": contract.to_dict(),
        "web_file_management": _production_web_file_management_view(raw.get("web_file_management")),
        "migrated_from_legacy": _uses_legacy_pose_units(raw),
    }


def validate_production_payload(payload: dict[str, Any]) -> dict[str, Any]:
    errors: list[dict[str, str]] = []
    camera = payload.get("camera_from_tcp")
    if not isinstance(camera, dict):
        errors.append(_error("camera_from_tcp", "必须配置左右手 TCP 外参。"))
        camera = {}
    web_pipeline = payload.get("web_pipeline")
    web_file_management = payload.get("web_file_management")

    for hand in ("left", "right"):
        ext = camera.get(hand)
        if not isinstance(ext, dict):
            errors.append(_error(f"camera_from_tcp.{hand}", "必须填写。"))
        else:
            try:
                translation = ext.get("translation_mm")
                if not isinstance(translation, list) or len(translation) != 3:
                    raise ValueError("必须填写 x、y、z，单位为 mm。")
                for value in translation:
                    _finite_float(value)
            except (TypeError, ValueError) as exc:
                errors.append(_error(f"camera_from_tcp.{hand}", str(exc)))

    errors.extend(_validate_web_pipeline_payload(web_pipeline))
    errors.extend(_validate_web_file_management_payload(web_file_management))
    return {"valid": not errors, "errors": errors}


def save_production_config(path: str | Path, payload: dict[str, Any]) -> dict[str, Any]:
    validation = validate_production_payload(payload)
    if not validation["valid"]:
        raise ProductionConfigError("; ".join(item["message"] for item in validation["errors"]))
    config_path = Path(path)
    raw = _read_yaml(config_path)
    raw["camera_from_tcp"] = payload["camera_from_tcp"]
    raw.pop("work_frames", None)
    raw["web_pipeline"] = _normalize_web_pipeline_payload(payload.get("web_pipeline"))
    raw["web_file_management"] = _normalize_web_file_management_payload(payload.get("web_file_management"))
    raw.pop("frame_alignment", None)
    calibration = raw.get("calibration")
    if isinstance(calibration, dict):
        calibration.pop("common_frame", None)
        gripper = calibration.get("gripper", {})
        gripper_ready = all(
            isinstance(gripper.get(hand), dict) and gripper[hand].get("calibrated") is True
            for hand in ("left", "right")
        )
        calibration["complete"] = gripper_ready
        calibration["calibrated"] = gripper_ready
    _ensure_tcp_pose_topics(raw)

    temporary = config_path.with_name(f".{config_path.name}.{os.getpid()}.tmp")
    temporary.write_text(
        yaml.safe_dump(raw, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    try:
        load_app_config(temporary)
        temporary.replace(config_path)
    finally:
        if temporary.exists():
            temporary.unlink()
    return production_config_view(config_path)


def production_readiness(
    path: str | Path,
) -> dict[str, Any]:
    config_path = Path(path)
    missing: list[str] = []
    try:
        config = load_app_config(config_path)
        view = production_config_view(config_path)
    except Exception as exc:  # noqa: BLE001 - Web must receive a readable readiness failure.
        return {
            "ready": False,
            "config_path": str(config_path),
            "missing_items": ["正式配置无法读取"],
            "error": f"{type(exc).__name__}: {exc}",
        }

    gripper = config.calibration.get("gripper", {})
    for hand, label in (("left", "左手夹爪标定"), ("right", "右手夹爪标定")):
        value = gripper.get(hand, {}) if isinstance(gripper, dict) else {}
        if not isinstance(value, dict) or not value.get("calibrated"):
            missing.append(label)
    if not isinstance(_read_yaml(config_path).get("camera_from_tcp"), dict):
        missing.append("独立 camera_from_tcp 外参")
    for hand, label in (("left", "左手"), ("right", "右手")):
        if hand not in (config.camera_from_tcp or {}):
            missing.append(f"{label} camera_from_tcp")
    expected_topics = {"/baton_mini_left/tcp_pose", "/baton_mini_right/tcp_pose"}
    actual_topics = {stream.output_tcp_pose for stream in config.pose_streams}
    if not expected_topics.issubset(actual_topics):
        missing.append("左右原始坐标系 TCP pose 输出 topic")
    return {
        "ready": not missing,
        "config_path": str(config_path),
        "missing_items": missing,
        "coordinate_frame_semantics": "preserve_baton_source_frame",
        "gripper": {
            hand: bool(isinstance(gripper, dict) and isinstance(gripper.get(hand), dict) and gripper[hand].get("calibrated"))
            for hand in ("left", "right")
        },
        "config": view,
    }


def _read_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ProductionConfigError("正式配置必须是 YAML mapping。")
    return data


def _production_web_pipeline_view(data: Any | None) -> dict[str, Any]:
    return _normalize_web_pipeline_payload(data)


def _production_web_file_management_view(data: Any | None) -> dict[str, Any]:
    return _normalize_web_file_management_payload(data)


def _normalize_web_pipeline_payload(data: Any | None) -> dict[str, Any]:
    source = data if isinstance(data, dict) else {}
    scene2 = source.get("scene2", {}) if isinstance(source.get("scene2", {}), dict) else {}
    pose_filter = _normalize_pose_filter(scene2.get("pose_filter"))
    tactile_filter = _normalize_tactile_filter(scene2.get("tactile_filter"))
    streams = _normalize_scene2_streams(scene2.get("streams"))
    lerobot_features = normalize_lerobot_features_config(source.get("lerobot_features"))
    return {
        "schema_version": 2,
        "scene2": {
            "streams": streams,
            "pose_filter": pose_filter,
            "tactile_filter": tactile_filter,
        },
        "lerobot_features": lerobot_features,
    }


def _normalize_scene2_streams(data: Any | None) -> list[dict[str, Any]]:
    source = [asdict(stream) for stream in DEFAULT_SCENE2_STREAMS] if data is None else data
    if not isinstance(source, list) or not all(isinstance(item, dict) for item in source):
        raise ValueError("scene2.streams 必须是列表")
    streams = [
        Scene2StreamSpec(
            topic=str(item.get("topic", "")),
            modality=str(item.get("modality", "")),
            required=bool(item.get("required", False)),
        )
        for item in source
    ]
    topics = [stream.topic for stream in streams]
    duplicates = sorted({topic for topic in topics if topics.count(topic) > 1})
    if duplicates:
        raise ValueError(f"scene2.streams topic 不得重复: {duplicates}")
    required = {(stream.topic, stream.modality) for stream in DEFAULT_SCENE2_STREAMS if stream.required}
    actual = {(stream.topic, stream.modality) for stream in streams if stream.required}
    if not required.issubset(actual):
        raise ValueError("scene2.streams 缺少固定 pose/gripper 必需 topic")
    return [asdict(stream) for stream in streams]


def _normalize_pose_filter(data: Any | None) -> dict[str, Any]:
    values = _pose_filter_defaults()
    if isinstance(data, dict):
        values.update(data)
    values["algorithm"] = PoseFilterAlgorithm(values["algorithm"]).value
    config = PoseFilterConfig(
        algorithm=PoseFilterAlgorithm(values["algorithm"]),
        window_duration_ms=int(values["window_duration_ms"]),
        polyorder=int(values["polyorder"]),
        position_guard_max_delta_m=float(values["position_guard_max_delta_m"]),
        orientation_guard_max_delta_deg=float(values["orientation_guard_max_delta_deg"]),
        timestamp_policy=str(values["timestamp_policy"]),
    )
    if config.window_duration_ms <= 0:
        raise ValueError("scene2.pose_filter.window_duration_ms 必须大于 0")
    if config.polyorder < 0:
        raise ValueError("scene2.pose_filter.polyorder 不得小于 0")
    if config.position_guard_max_delta_m < 0:
        raise ValueError("scene2.pose_filter.position_guard_max_delta_m 不得小于 0")
    if config.orientation_guard_max_delta_deg < 0:
        raise ValueError("scene2.pose_filter.orientation_guard_max_delta_deg 不得小于 0")
    if config.timestamp_policy != "preserve_original":
        raise ValueError("scene2.pose_filter.timestamp_policy 必须是 preserve_original")
    return {
        "algorithm": config.algorithm.value,
        "window_duration_ms": config.window_duration_ms,
        "polyorder": config.polyorder,
        "position_guard_max_delta_m": config.position_guard_max_delta_m,
        "orientation_guard_max_delta_deg": config.orientation_guard_max_delta_deg,
        "timestamp_policy": config.timestamp_policy,
    }


def _normalize_tactile_filter(data: Any | None) -> dict[str, Any]:
    values = _tactile_filter_defaults()
    if isinstance(data, dict):
        values.update(data)
    values["algorithm"] = TactileFilterAlgorithm(values["algorithm"]).value
    contact_reset = values.get("contact_reset_threshold")
    config = TactileFilterConfig(
        algorithm=TactileFilterAlgorithm(values["algorithm"]),
        median_window=int(values["median_window"]),
        ema_alpha=float(values["ema_alpha"]),
        contact_reset_threshold=None if contact_reset in (None, "") else float(contact_reset),
        timestamp_policy=str(values["timestamp_policy"]),
    )
    return {
        "algorithm": config.algorithm.value,
        "median_window": config.median_window,
        "ema_alpha": config.ema_alpha,
        "contact_reset_threshold": config.contact_reset_threshold,
        "timestamp_policy": config.timestamp_policy,
    }


def _pose_filter_defaults() -> dict[str, Any]:
    config = PoseFilterConfig()
    return {
        "algorithm": config.algorithm.value,
        "window_duration_ms": config.window_duration_ms,
        "polyorder": config.polyorder,
        "position_guard_max_delta_m": config.position_guard_max_delta_m,
        "orientation_guard_max_delta_deg": config.orientation_guard_max_delta_deg,
        "timestamp_policy": config.timestamp_policy,
    }


def _tactile_filter_defaults() -> dict[str, Any]:
    config = TactileFilterConfig()
    return {
        "algorithm": config.algorithm.value,
        "median_window": config.median_window,
        "ema_alpha": config.ema_alpha,
        "contact_reset_threshold": config.contact_reset_threshold,
        "timestamp_policy": config.timestamp_policy,
    }


def _validate_web_pipeline_payload(data: Any | None) -> list[dict[str, str]]:
    if data is None:
        return []
    if not isinstance(data, dict):
        return [_error("web_pipeline", "必须是配置对象。")]
    try:
        _normalize_web_pipeline_payload(data)
    except (ValueError, TypeError, LeRobotFeatureConfigError) as exc:
        return [_error("web_pipeline", str(exc))]
    return []


def _normalize_web_file_management_payload(data: Any | None) -> dict[str, Any]:
    values = dict(DEFAULT_WEB_FILE_MANAGEMENT)
    if isinstance(data, dict):
        values.update(data)
    health_audited_dir = str(
        values.get("health_audited_mcap_dir") or DEFAULT_WEB_FILE_MANAGEMENT["health_audited_mcap_dir"]
    ).strip()
    rejected_dir = str(values.get("rejected_mcap_dir") or DEFAULT_WEB_FILE_MANAGEMENT["rejected_mcap_dir"]).strip()
    completed_dir = str(values.get("completed_mcap_dir") or DEFAULT_WEB_FILE_MANAGEMENT["completed_mcap_dir"]).strip()
    cleaning_failed_dir = str(
        values.get("cleaning_failed_mcap_dir") or DEFAULT_WEB_FILE_MANAGEMENT["cleaning_failed_mcap_dir"]
    ).strip()
    artifact_retention = str(values.get("artifact_retention") or "production_cleanup")
    failed_policy = str(values.get("failed_artifact_policy") or "failed_stage_input")
    if artifact_retention not in {"production_cleanup", "keep_all"}:
        raise ValueError("web_file_management.artifact_retention 必须是 production_cleanup 或 keep_all")
    if failed_policy not in {"failed_stage_input", "keep_all"}:
        raise ValueError("web_file_management.failed_artifact_policy 必须是 failed_stage_input 或 keep_all")
    multiplier = float(values.get("space_estimate_multiplier", DEFAULT_WEB_FILE_MANAGEMENT["space_estimate_multiplier"]))
    safety_gb = float(values.get("space_safety_gb", DEFAULT_WEB_FILE_MANAGEMENT["space_safety_gb"]))
    if not math.isfinite(multiplier) or multiplier <= 0:
        raise ValueError("web_file_management.space_estimate_multiplier 必须大于 0")
    if not math.isfinite(safety_gb) or safety_gb < 0:
        raise ValueError("web_file_management.space_safety_gb 不得小于 0")
    return {
        "health_audited_mcap_dir": health_audited_dir,
        "rejected_mcap_dir": rejected_dir,
        "completed_mcap_dir": completed_dir,
        "cleaning_failed_mcap_dir": cleaning_failed_dir,
        "artifact_retention": artifact_retention,
        "failed_artifact_policy": failed_policy,
        "space_estimate_multiplier": multiplier,
        "space_safety_gb": safety_gb,
    }


def _validate_web_file_management_payload(data: Any | None) -> list[dict[str, str]]:
    if data is None:
        return []
    if not isinstance(data, dict):
        return [_error("web_file_management", "必须是配置对象。")]
    try:
        _normalize_web_file_management_payload(data)
    except (ValueError, TypeError) as exc:
        return [_error("web_file_management", str(exc))]
    return []


def _ensure_tcp_pose_topics(raw: dict[str, Any]) -> None:
    streams = raw.get("pose_streams")
    if not isinstance(streams, list):
        raise ProductionConfigError("pose_streams 必须是列表。")
    found: set[str] = set()
    for stream in streams:
        if not isinstance(stream, dict):
            continue
        topic = str(stream.get("input_topic", ""))
        if "_left" in topic:
            stream.pop("output_arm_base_tcp_pose", None)
            stream["output_tcp_pose"] = "/baton_mini_left/tcp_pose"
            found.add("left")
        elif "_right" in topic:
            stream.pop("output_arm_base_tcp_pose", None)
            stream["output_tcp_pose"] = "/baton_mini_right/tcp_pose"
            found.add("right")
    if found != {"left", "right"}:
        raise ProductionConfigError("pose_streams 必须包含左右 Baton Mini 输入 topic。")


def _uses_legacy_pose_units(raw: dict[str, Any]) -> bool:
    camera = raw.get("camera_from_tcp", {})
    if "camera_from_tcp" not in raw and isinstance(raw.get("frame_alignment"), dict):
        return True
    return any(
        isinstance(camera.get(hand), dict) and "translation_mm" not in camera[hand]
        for hand in ("left", "right")
    )


def _finite_float(value: Any) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError("必须是有限数值。")
    return number


def _error(path: str, message: str) -> dict[str, str]:
    return {"path": path, "message": message}
