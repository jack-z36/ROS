"""Normal-Web production configuration and readiness checks."""

from __future__ import annotations

import os
import math
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable

import yaml

from repo.config.mcap_process_config import load_app_config
from schemas.lerobot_features import (
    LeRobotFeatureConfigError,
    normalize_lerobot_features_config,
)
from schemas.pose_filter import PoseFilterAlgorithm, PoseFilterConfig
from schemas.tactile_filter import TactileFilterAlgorithm, TactileFilterConfig


class ProductionConfigError(ValueError):
    """Raised when a normal-Web production config cannot be saved."""


@lru_cache(maxsize=1)
def realman_sdk_status() -> dict[str, Any]:
    try:
        from Robotic_Arm.rm_robot_interface import Algo, rm_force_type_e, rm_robot_arm_model_e

        algo = Algo(
            rm_robot_arm_model_e.RM_MODEL_RM_65_E,
            rm_force_type_e.RM_MODEL_RM_B_E,
        )
        version = algo.rm_algo_version()
        return {"ready": True, "version": str(version), "error": None}
    except Exception as exc:  # noqa: BLE001 - readiness must explain local dependency failures.
        return {"ready": False, "version": None, "error": f"{type(exc).__name__}: {exc}"}


def production_config_view(path: str | Path) -> dict[str, Any]:
    config_path = Path(path)
    raw = _read_yaml(config_path)
    config = load_app_config(config_path)
    camera = config.camera_from_tcp or {}
    work_frames = config.work_frames or {}
    for hand, extrinsic in camera.items():
        if extrinsic.rotation_quat_xyzw != (0.0, 0.0, 0.0, 1.0):
            raise ProductionConfigError(
                f"camera_from_tcp.{hand} 的历史旋转不是零；普通生产链路不会静默丢弃该旋转，请先人工确认。"
            )
    return {
        "config_path": str(config_path),
        "camera_from_tcp": {
            hand: {"translation_mm": [value * 1000.0 for value in camera[hand].translation_m]}
            for hand in ("left", "right")
            if hand in camera
        },
        "work_frames": {
            hand: {
                "hand": work_frames[hand].hand,
                "base_frame_id": work_frames[hand].base_frame_id,
                "work_frame_id": work_frames[hand].work_frame_id,
                "position_mm": {
                    key: value * 1000.0 for key, value in work_frames[hand].position_m.items()
                },
                "rotation_euler_rad": dict(work_frames[hand].rotation_euler_rad),
                "source": work_frames[hand].source,
            }
            for hand in ("left", "right")
            if hand in work_frames
        },
        "web_pipeline": _production_web_pipeline_view(raw.get("web_pipeline")),
        "migrated_from_legacy": _uses_legacy_pose_units(raw),
    }


def validate_production_payload(payload: dict[str, Any]) -> dict[str, Any]:
    payload = _normalize_production_payload(payload)
    errors: list[dict[str, str]] = []
    camera = payload.get("camera_from_tcp")
    work_frames = payload.get("work_frames")
    if not isinstance(camera, dict):
        errors.append(_error("camera_from_tcp", "必须配置左右手 TCP 外参。"))
        camera = {}
    if not isinstance(work_frames, dict):
        errors.append(_error("work_frames", "必须配置左右手工作坐标系。"))
        work_frames = {}
    web_pipeline = payload.get("web_pipeline")

    expected_base = {"left": "left_arm_base", "right": "right_arm_base"}
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

        work = work_frames.get(hand)
        if not isinstance(work, dict):
            errors.append(_error(f"work_frames.{hand}", "必须填写。"))
            continue
        if str(work.get("hand", hand)) != hand:
            errors.append(_error(f"work_frames.{hand}.hand", f"必须是 {hand}。"))
        if str(work.get("base_frame_id", "")) != expected_base[hand]:
            errors.append(
                _error(
                    f"work_frames.{hand}.base_frame_id",
                    f"必须是 {expected_base[hand]}。",
                )
            )
        position = work.get("position_mm")
        if not isinstance(position, dict) or any(key not in position for key in ("x", "y", "z")):
            errors.append(_error(f"work_frames.{hand}.position_mm", "必须填写 x、y、z，单位为 mm。"))
        else:
            try:
                for key in ("x", "y", "z"):
                    _finite_float(position[key])
            except (TypeError, ValueError) as exc:
                errors.append(_error(f"work_frames.{hand}.position_mm", str(exc)))
        rotation = work.get("rotation_euler_rad")
        if not isinstance(rotation, dict) or any(key not in rotation for key in ("rx", "ry", "rz")):
            errors.append(_error(f"work_frames.{hand}.rotation_euler_rad", "必须填写 rx、ry、rz，单位为 rad。"))
        else:
            try:
                for key in ("rx", "ry", "rz"):
                    _finite_float(rotation[key])
            except (TypeError, ValueError) as exc:
                errors.append(_error(f"work_frames.{hand}.rotation_euler_rad", str(exc)))
    errors.extend(_validate_web_pipeline_payload(web_pipeline))
    return {"valid": not errors, "errors": errors}


def save_production_config(path: str | Path, payload: dict[str, Any]) -> dict[str, Any]:
    payload = _normalize_production_payload(payload)
    validation = validate_production_payload(payload)
    if not validation["valid"]:
        raise ProductionConfigError("; ".join(item["message"] for item in validation["errors"]))
    config_path = Path(path)
    raw = _read_yaml(config_path)
    raw["camera_from_tcp"] = payload["camera_from_tcp"]
    raw["work_frames"] = payload["work_frames"]
    raw["web_pipeline"] = _normalize_web_pipeline_payload(payload.get("web_pipeline"))
    for hand in ("left", "right"):
        raw["work_frames"][hand]["hand"] = hand
        raw["work_frames"][hand]["base_frame_id"] = f"{hand}_arm_base"
        raw["work_frames"][hand]["source"] = "user_input"
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
    _ensure_arm_base_topics(raw)

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


def _normalize_production_payload(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return payload
    normalized = dict(payload)

    camera = payload.get("camera_from_tcp")
    if isinstance(camera, dict):
        normalized_camera: dict[str, Any] = {}
        for hand in ("left", "right"):
            ext = camera.get(hand)
            if not isinstance(ext, dict):
                if ext is not None:
                    normalized_camera[hand] = ext
                continue
            ext_out = dict(ext)
            ext_out["translation_mm"] = _normalize_xyz_sequence(ext.get("translation_mm"))
            normalized_camera[hand] = ext_out
        normalized["camera_from_tcp"] = normalized_camera

    work_frames = payload.get("work_frames")
    if isinstance(work_frames, dict):
        normalized_work: dict[str, Any] = {}
        for hand in ("left", "right"):
            work = work_frames.get(hand)
            if not isinstance(work, dict):
                if work is not None:
                    normalized_work[hand] = work
                continue
            work_out = dict(work)
            work_out.setdefault("hand", hand)
            work_out.setdefault("base_frame_id", f"{hand}_arm_base")
            work_out.setdefault("work_frame_id", "camera_work")
            normalized_work[hand] = work_out
        normalized["work_frames"] = normalized_work

    return normalized


def _normalize_xyz_sequence(value: Any) -> Any:
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        return [value.get(index, value.get(str(index))) for index in range(3)]
    return value


def production_readiness(
    path: str | Path,
    *,
    sdk_status_provider: Callable[[], dict[str, Any]] = realman_sdk_status,
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
            "sdk": {"ready": False, "version": None, "error": None},
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
        if hand not in (config.work_frames or {}):
            missing.append(f"{label} work_frame_in_arm_base")
        elif config.work_frames[hand].source != "user_input":
            missing.append(f"{label} work_frame_in_arm_base 待确认")
    expected_topics = {"/left_arm_base_tcp_pose", "/right_arm_base_tcp_pose"}
    actual_topics = {stream.output_arm_base_tcp_pose for stream in config.pose_streams}
    if not expected_topics.issubset(actual_topics):
        missing.append("左右 arm-base TCP pose 输出 topic")
    sdk = sdk_status_provider()
    if not sdk.get("ready"):
        missing.append("RealMan SDK Algo")
    return {
        "ready": not missing,
        "config_path": str(config_path),
        "missing_items": missing,
        "sdk": sdk,
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


def _normalize_web_pipeline_payload(data: Any | None) -> dict[str, Any]:
    source = data if isinstance(data, dict) else {}
    scene2 = source.get("scene2", {}) if isinstance(source.get("scene2", {}), dict) else {}
    pose_filter = _normalize_pose_filter(scene2.get("pose_filter"))
    tactile_filter = _normalize_tactile_filter(scene2.get("tactile_filter"))
    lerobot_features = normalize_lerobot_features_config(source.get("lerobot_features"))
    return {
        "schema_version": 1,
        "scene2": {
            "pose_filter": pose_filter,
            "tactile_filter": tactile_filter,
        },
        "lerobot_features": lerobot_features,
    }


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


def _ensure_arm_base_topics(raw: dict[str, Any]) -> None:
    streams = raw.get("pose_streams")
    if not isinstance(streams, list):
        raise ProductionConfigError("pose_streams 必须是列表。")
    found: set[str] = set()
    for stream in streams:
        if not isinstance(stream, dict):
            continue
        topic = str(stream.get("input_topic", ""))
        if "_left" in topic:
            stream["output_arm_base_tcp_pose"] = "/left_arm_base_tcp_pose"
            found.add("left")
        elif "_right" in topic:
            stream["output_arm_base_tcp_pose"] = "/right_arm_base_tcp_pose"
            found.add("right")
    if found != {"left", "right"}:
        raise ProductionConfigError("pose_streams 必须包含左右 Baton Mini 输入 topic。")


def _uses_legacy_pose_units(raw: dict[str, Any]) -> bool:
    camera = raw.get("camera_from_tcp", {})
    work_frames = raw.get("work_frames", {})
    if "camera_from_tcp" not in raw and isinstance(raw.get("frame_alignment"), dict):
        return True
    return any(
        isinstance(camera.get(hand), dict) and "translation_mm" not in camera[hand]
        or isinstance(work_frames.get(hand), dict) and "position_mm" not in work_frames[hand]
        for hand in ("left", "right")
    )


def _finite_float(value: Any) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError("必须是有限数值。")
    return number


def _error(path: str, message: str) -> dict[str, str]:
    return {"path": path, "message": message}
