"""Web-job configuration presets, validation, snapshots, and stage adapters."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import yaml

from repo.config.mcap_process_config import load_app_config
from runtime.config_snapshot import write_config_snapshot
from schemas.alignment_config import Scene3AlignmentConfig
from schemas.lerobot_features import normalize_lerobot_features_config
from schemas.pose_filter import PoseFilterAlgorithm, PoseFilterConfig
from schemas.runtime_config_types import (
    ConfigOverrideSet,
    EffectiveRuntimeConfig,
    RuntimeConfigSource,
    RuntimeConfigSourceKind,
)
from schemas.tactile_filter import TactileFilterAlgorithm, TactileFilterConfig
from service.detectors import ReliabilityDetectionConfig


class WebPipelineConfigError(ValueError):
    """Raised when a Web pipeline preset or override is invalid."""


@dataclass
class WebPipelineEffectiveConfig:
    scene1_config_path: Path
    snapshot_path: Path
    effective_summary: dict[str, Any]
    diff: list[dict[str, Any]]
    manual_calibration_override: bool

    def detection_config(self) -> ReliabilityDetectionConfig:
        values = self.effective_summary["scene2"]["detection"]
        return ReliabilityDetectionConfig(
            max_gap_duration_ns=int(float(values["max_gap_duration_ms"]) * 1_000_000),
            quaternion_norm_tolerance=float(values["quaternion_norm_tolerance"]),
            pose_position_jump_threshold=_optional_float(values.get("pose_position_jump_threshold")),
            gripper_jump_threshold=_optional_float(values.get("gripper_jump_threshold")),
            tactile_spike_mean_delta_threshold=_optional_float(values.get("tactile_spike_mean_delta_threshold")),
            tactile_zero_ratio_threshold=float(values["tactile_zero_ratio_threshold"]),
            tactile_saturation_ratio_threshold=float(values["tactile_saturation_ratio_threshold"]),
        )

    def pose_filter_config(self) -> PoseFilterConfig:
        values = deepcopy(self.effective_summary["scene2"]["pose_filter"])
        values["algorithm"] = PoseFilterAlgorithm(values["algorithm"])
        return PoseFilterConfig(**values)

    def tactile_filter_config(self) -> TactileFilterConfig:
        values = deepcopy(self.effective_summary["scene2"]["tactile_filter"])
        values["algorithm"] = TactileFilterAlgorithm(values["algorithm"])
        return TactileFilterConfig(**values)

    def alignment_config(self, *, output_dir: str) -> Scene3AlignmentConfig:
        values = self.effective_summary["scene3"]
        return Scene3AlignmentConfig(
            target_step_hz=int(values["target_step_hz"]),
            baseline_image_topics=list(values["baseline_image_topics"]),
            image_max_dt_ms=_optional_int(values.get("image_max_dt_ms")),
            pose_source_profile=str(values["pose_source_profile"]),
            output_dir=output_dir,
        )

    def lerobot_features_config(self) -> dict[str, Any]:
        return normalize_lerobot_features_config(
            self.effective_summary.get("lerobot_features")
        )


def list_presets(presets_dir: Path) -> list[dict[str, Any]]:
    presets_dir.mkdir(parents=True, exist_ok=True)
    result = []
    for path in sorted(presets_dir.glob("*.yaml")):
        try:
            data = _read_preset(path)
            result.append({"name": data["name"], "path": str(path)})
        except WebPipelineConfigError:
            continue
    return result


def load_preset(presets_dir: Path, name: str) -> dict[str, Any]:
    return _read_preset(_preset_path(presets_dir, name))


def save_preset(presets_dir: Path, name: str, overrides: dict[str, Any]) -> dict[str, Any]:
    path = _preset_path(presets_dir, name)
    normalized = _normalize_overrides(overrides)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"schema_version": 1, "name": name, "overrides": normalized}
    path.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return {"name": name, "path": str(path), "overrides": normalized}


def delete_preset(presets_dir: Path, name: str) -> None:
    path = _preset_path(presets_dir, name)
    if path.exists():
        path.unlink()


def preview_web_pipeline_config(
    *,
    default_config_path: Path,
    presets_dir: Path,
    preset_name: str = "",
    overrides: dict[str, Any] | None = None,
    bridge_mode: str = "format-only",
    formal_manual_override_confirmed: bool = False,
) -> dict[str, Any]:
    try:
        summary, diff, manual = _build_summary(
            default_config_path=default_config_path,
            presets_dir=presets_dir,
            preset_name=preset_name,
            overrides=overrides or {},
            bridge_mode=bridge_mode,
        )
        _validate_summary(summary)
        errors = []
        if bridge_mode == "formal" and manual and not formal_manual_override_confirmed:
            errors.append("formal 模式下手工标定覆盖必须再次确认。")
        return {
            "valid": not errors,
            "default_config_path": str(default_config_path),
            "preset_name": preset_name,
            "effective_summary": summary,
            "diff": diff,
            "warnings": ["手工覆盖了标定敏感字段，请确认其物理含义。"] if manual else [],
            "errors": errors,
            "manual_calibration_override": manual,
        }
    except Exception as exc:  # noqa: BLE001 - field errors are returned to Web UI.
        return {
            "valid": False,
            "default_config_path": str(default_config_path),
            "preset_name": preset_name,
            "effective_summary": {},
            "diff": [],
            "warnings": [],
            "errors": [str(exc)],
            "manual_calibration_override": False,
        }


def build_web_job_effective_config(
    *,
    default_config_path: Path,
    presets_dir: Path,
    run_dir: Path,
    preset_name: str = "",
    overrides: dict[str, Any] | None = None,
    bridge_mode: str = "format-only",
    formal_manual_override_confirmed: bool = False,
) -> WebPipelineEffectiveConfig:
    preview = preview_web_pipeline_config(
        default_config_path=default_config_path,
        presets_dir=presets_dir,
        preset_name=preset_name,
        overrides=overrides,
        bridge_mode=bridge_mode,
        formal_manual_override_confirmed=formal_manual_override_confirmed,
    )
    if not preview["valid"]:
        raise WebPipelineConfigError("; ".join(preview["errors"]))

    run_dir.mkdir(parents=True, exist_ok=False)
    preset_overrides = load_preset(presets_dir, preset_name)["overrides"] if preset_name else {}
    task_overrides = _normalize_overrides(overrides or {})
    scene1_data = _scene1_yaml(default_config_path, preview["effective_summary"])
    scene1_path = run_dir / "scene1_effective.yaml"
    scene1_path.write_text(yaml.safe_dump(scene1_data, allow_unicode=True, sort_keys=False), encoding="utf-8")
    source = RuntimeConfigSource(
        config_path=default_config_path.resolve(),
        source_kind=RuntimeConfigSourceKind.DEFAULT,
        exists_at_load_time=default_config_path.is_file(),
        declared_by="web_launcher",
    )
    effective = EffectiveRuntimeConfig(
        config_source=source,
        override_set=ConfigOverrideSet(
            overrides={
                "preset_name": preset_name,
                "preset_overrides": preset_overrides,
                "task_overrides": task_overrides,
            },
            source_detail=f"web_launcher preset={preset_name or '<none>'}",
        ),
        config_data={
            "web_pipeline": preview["effective_summary"],
            "production_pose_config": _production_pose_snapshot(default_config_path),
            "scene1_effective": scene1_data,
            "scene1_effective_config": str(scene1_path),
            "preset_name": preset_name,
            "manual_calibration_override": preview["manual_calibration_override"],
        },
    )
    snapshot = write_config_snapshot(effective, run_dir)
    return WebPipelineEffectiveConfig(
        scene1_config_path=scene1_path,
        snapshot_path=snapshot.snapshot_path,
        effective_summary=preview["effective_summary"],
        diff=preview["diff"],
        manual_calibration_override=preview["manual_calibration_override"],
    )


def _production_pose_snapshot(path: Path) -> dict[str, Any]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    config = load_app_config(path)
    return {
        "user_input": {
            "camera_from_tcp": deepcopy(raw.get("camera_from_tcp", {})),
        },
        "runtime_normalized": {
            "camera_from_tcp": {
                hand: {
                    "translation_m": list(extrinsic.translation_m),
                    "rotation_quat_xyzw": list(extrinsic.rotation_quat_xyzw),
                }
                for hand, extrinsic in (config.camera_from_tcp or {}).items()
            },
            "coordinate_frame_semantics": "preserve_baton_source_frame",
        },
    }


def load_web_job_effective_config(snapshot_path: Path) -> WebPipelineEffectiveConfig:
    data = yaml.safe_load(snapshot_path.read_text(encoding="utf-8")) or {}
    effective = data.get("effective_config", {})
    return WebPipelineEffectiveConfig(
        scene1_config_path=Path(effective["scene1_effective_config"]),
        snapshot_path=snapshot_path,
        effective_summary=effective["web_pipeline"],
        diff=[],
        manual_calibration_override=bool(effective.get("manual_calibration_override", False)),
    )


def _build_summary(
    *,
    default_config_path: Path,
    presets_dir: Path,
    preset_name: str,
    overrides: dict[str, Any],
    bridge_mode: str,
) -> tuple[dict[str, Any], list[dict[str, Any]], bool]:
    base = _default_summary(default_config_path, bridge_mode)
    merged = deepcopy(base)
    if preset_name:
        _deep_merge(merged, load_preset(presets_dir, preset_name)["overrides"])
    _deep_merge(merged, _normalize_overrides(overrides))
    merged["bridge"]["mode"] = bridge_mode
    merged["scene3"]["pose_source_profile"] = bridge_mode
    diff = _diff(base, merged)
    sensitive = ("scene1.gripper.", "scene1.frame_alignment.")
    manual = any(any(item["path"].startswith(prefix) for prefix in sensitive) for item in diff)
    return merged, diff, manual


def _default_summary(path: Path, bridge_mode: str) -> dict[str, Any]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    production_web = raw.get("web_pipeline", {})
    if not isinstance(production_web, dict):
        production_web = {}
    production_scene2 = production_web.get("scene2", {})
    if not isinstance(production_scene2, dict):
        production_scene2 = {}
    grippers = raw.get("gripper_streams", [])
    frame = raw.get("frame_alignment", {})
    extrinsics = frame.get("extrinsics", {})
    pose_streams = frame.get("pose_streams", {})
    camera_from_tcp = raw.get("camera_from_tcp", {})
    identity = {"translation_m": [0.0, 0.0, 0.0], "rotation_quat_xyzw": [0.0, 0.0, 0.0, 1.0]}
    camera_legacy = {
        hand: _camera_tcp_legacy_extrinsic(camera_from_tcp.get(hand), identity)
        for hand in ("left", "right")
    }
    if not extrinsics:
        extrinsics = {
            "common_from_left_start": deepcopy(identity),
            "common_from_right_start": deepcopy(identity),
            "camera_from_left_tcp": camera_legacy["left"],
            "camera_from_right_tcp": camera_legacy["right"],
        }
    return {
        "scene1": {
            "gripper": {
                hand: deepcopy(grippers[index]) if index < len(grippers) else {}
                for index, hand in enumerate(("left", "right"))
            },
            "frame_alignment": {
                "common_anchor": frame.get("common_anchor", "left"),
                "extrinsics": deepcopy(extrinsics),
                "pose_streams": deepcopy(pose_streams),
            },
        },
        "scene2": {
            "detection": {
                "max_gap_duration_ms": 100,
                "quaternion_norm_tolerance": 0.05,
                "pose_position_jump_threshold": None,
                "gripper_jump_threshold": None,
                "tactile_spike_mean_delta_threshold": None,
                "tactile_zero_ratio_threshold": 0.95,
                "tactile_saturation_ratio_threshold": 0.95,
            },
            "pose_filter": _production_filter_config(
                production_scene2.get("pose_filter"),
                {**asdict(PoseFilterConfig()), "algorithm": PoseFilterConfig().algorithm.value},
            ),
            "tactile_filter": _production_filter_config(
                production_scene2.get("tactile_filter"),
                {**asdict(TactileFilterConfig()), "algorithm": TactileFilterConfig().algorithm.value},
            ),
        },
        "scene3": {
            "target_step_hz": 15,
            "baseline_image_topics": ["/gopro_left/image_raw", "/gopro_right/image_raw"],
            "image_max_dt_ms": None,
            "pose_source_profile": bridge_mode,
        },
        "bridge": {"mode": bridge_mode, "max_pose_abs_m": 10.0},
        "lerobot": {"fps": 15.0},
        "lerobot_features": normalize_lerobot_features_config(
            production_web.get("lerobot_features")
        ),
    }


def _production_filter_config(value: Any, defaults: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(defaults)
    if isinstance(value, dict):
        result.update(value)
    return result


def _camera_tcp_legacy_extrinsic(value: Any, identity: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(value, dict):
        return deepcopy(identity)
    translation_mm = value.get("translation_mm")
    if isinstance(translation_mm, list) and len(translation_mm) == 3:
        return {
            "translation_m": [float(item) / 1000.0 for item in translation_mm],
            "rotation_quat_xyzw": [0.0, 0.0, 0.0, 1.0],
        }
    return deepcopy(value)


def _scene1_yaml(default_config_path: Path, summary: dict[str, Any]) -> dict[str, Any]:
    raw = yaml.safe_load(default_config_path.read_text(encoding="utf-8")) or {}
    raw["gripper_streams"] = [
        deepcopy(summary["scene1"]["gripper"]["left"]),
        deepcopy(summary["scene1"]["gripper"]["right"]),
    ]
    if "frame_alignment" in raw:
        raw["frame_alignment"] = deepcopy(summary["scene1"]["frame_alignment"])
    return raw


def _validate_summary(summary: dict[str, Any]) -> None:
    grippers = summary["scene1"]["gripper"]
    for hand in ("left", "right"):
        stream = grippers[hand]
        if float(stream["marker_max"]) <= float(stream["marker_min"]):
            raise WebPipelineConfigError(f"scene1.gripper.{hand}: marker_max 必须大于 marker_min")
        if float(stream["gripper_max"]) <= 0:
            raise WebPipelineConfigError(f"scene1.gripper.{hand}: gripper_max 必须大于 0")
    if grippers["left"]["output_topic"] == grippers["right"]["output_topic"]:
        raise WebPipelineConfigError("左右夹爪 output_topic 不得重复")

    frame = summary["scene1"]["frame_alignment"]
    anchor = frame["common_anchor"]
    if anchor not in {"left", "right"}:
        raise WebPipelineConfigError("common_anchor 必须是 left 或 right")
    for name, value in frame["extrinsics"].items():
        translation = [float(item) for item in value["translation_m"]]
        quat = [float(item) for item in value["rotation_quat_xyzw"]]
        if len(translation) != 3:
            raise WebPipelineConfigError(f"{name}: translation_m 必须包含 3 个数值")
        if len(quat) != 4:
            raise WebPipelineConfigError(f"{name}: rotation_quat_xyzw 必须包含 4 个数值")
        norm = sum(item * item for item in quat) ** 0.5
        if abs(norm - 1.0) > 1e-3:
            raise WebPipelineConfigError(f"{name}: quaternion norm 必须接近 1")
    anchored = frame["extrinsics"][f"common_from_{anchor}_start"]
    if [float(item) for item in anchored["translation_m"]] != [0.0, 0.0, 0.0] or [float(item) for item in anchored["rotation_quat_xyzw"]] != [0.0, 0.0, 0.0, 1.0]:
        raise WebPipelineConfigError(f"common_anchor={anchor} 时 common_from_{anchor}_start 必须是 identity")

    WebPipelineEffectiveConfig(Path(), Path(), summary, [], False).detection_config()
    effective = WebPipelineEffectiveConfig(Path(), Path(), summary, [], False)
    effective.pose_filter_config()
    effective.tactile_filter_config()
    detection = summary["scene2"]["detection"]
    if float(detection["max_gap_duration_ms"]) <= 0:
        raise WebPipelineConfigError("scene2.detection.max_gap_duration_ms 必须大于 0")
    if float(detection["quaternion_norm_tolerance"]) < 0:
        raise WebPipelineConfigError("scene2.detection.quaternion_norm_tolerance 不得小于 0")
    for key in ("tactile_zero_ratio_threshold", "tactile_saturation_ratio_threshold"):
        if not 0 <= float(detection[key]) <= 1:
            raise WebPipelineConfigError(f"scene2.detection.{key} 必须位于 [0, 1]")
    for key in ("pose_position_jump_threshold", "gripper_jump_threshold", "tactile_spike_mean_delta_threshold"):
        value = detection.get(key)
        if value not in (None, "") and float(value) < 0:
            raise WebPipelineConfigError(f"scene2.detection.{key} 不得小于 0")
    pose_filter = summary["scene2"]["pose_filter"]
    if int(pose_filter["window_duration_ms"]) <= 0:
        raise WebPipelineConfigError("scene2.pose_filter.window_duration_ms 必须大于 0")
    if int(pose_filter["polyorder"]) < 0:
        raise WebPipelineConfigError("scene2.pose_filter.polyorder 不得小于 0")
    Scene3AlignmentConfig(
        target_step_hz=int(summary["scene3"]["target_step_hz"]),
        baseline_image_topics=list(summary["scene3"]["baseline_image_topics"]),
        image_max_dt_ms=_optional_int(summary["scene3"].get("image_max_dt_ms")),
        pose_source_profile=str(summary["scene3"]["pose_source_profile"]),
    )
    if float(summary["bridge"]["max_pose_abs_m"]) <= 0:
        raise WebPipelineConfigError("bridge.max_pose_abs_m 必须大于 0")
    if float(summary["lerobot"]["fps"]) <= 0:
        raise WebPipelineConfigError("lerobot.fps 必须大于 0")
    normalize_lerobot_features_config(summary.get("lerobot_features"))


def _normalize_overrides(overrides: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(overrides, dict):
        raise WebPipelineConfigError("overrides 必须是 mapping")
    allowed = {"scene1", "scene2", "scene3", "bridge", "lerobot", "lerobot_features"}
    unknown = set(overrides) - allowed
    if unknown:
        raise WebPipelineConfigError(f"不支持的 override 配置块: {sorted(unknown)}")
    normalized = deepcopy(overrides)
    _assert_known_paths(normalized, _default_override_shape())
    return normalized


def _assert_known_paths(update: dict[str, Any], shape: dict[str, Any], prefix: str = "") -> None:
    for key, value in update.items():
        path = f"{prefix}.{key}" if prefix else key
        if key not in shape:
            raise WebPipelineConfigError(f"不支持的 override 字段: {path}")
        if isinstance(value, dict):
            if not isinstance(shape[key], dict):
                raise WebPipelineConfigError(f"override 字段不是配置块: {path}")
            _assert_known_paths(value, shape[key], path)


def _default_override_shape() -> dict[str, Any]:
    return {
        "scene1": {
            "gripper": {
                hand: {
                    key: None
                    for key in (
                        "image_topic",
                        "output_topic",
                        "aruco_dict",
                        "marker_id_0",
                        "marker_id_1",
                        "marker_min",
                        "marker_max",
                        "gripper_max",
                    )
                }
                for hand in ("left", "right")
            },
            "frame_alignment": {
                "common_anchor": None,
                "extrinsics": {
                    name: {"translation_m": None, "rotation_quat_xyzw": None}
                    for name in (
                        "common_from_left_start",
                        "common_from_right_start",
                        "camera_from_left_tcp",
                        "camera_from_right_tcp",
                    )
                },
                "pose_streams": {
                    hand: {
                        "input_topic": None,
                        "output_camera_pose_common": None,
                        "output_tcp_pose_common": None,
                    }
                    for hand in ("left", "right")
                },
            },
        },
        "scene2": {
            "detection": {
                key: None
                for key in (
                    "max_gap_duration_ms",
                    "quaternion_norm_tolerance",
                    "pose_position_jump_threshold",
                    "gripper_jump_threshold",
                    "tactile_spike_mean_delta_threshold",
                    "tactile_zero_ratio_threshold",
                    "tactile_saturation_ratio_threshold",
                )
            },
            "pose_filter": {
                key: None
                for key in (
                    "algorithm",
                    "window_duration_ms",
                    "polyorder",
                    "position_guard_max_delta_m",
                    "orientation_guard_max_delta_deg",
                    "timestamp_policy",
                )
            },
            "tactile_filter": {
                key: None
                for key in (
                    "algorithm",
                    "median_window",
                    "ema_alpha",
                    "contact_reset_threshold",
                    "timestamp_policy",
                )
            },
        },
        "scene3": {
            "target_step_hz": None,
            "baseline_image_topics": None,
            "image_max_dt_ms": None,
        },
        "bridge": {"max_pose_abs_m": None},
        "lerobot": {"fps": None},
        "lerobot_features": {
            "schema_version": None,
            "state_segments": None,
            "action_segments": None,
        },
    }


def _preset_path(presets_dir: Path, name: str) -> Path:
    if not name or any(char not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-" for char in name):
        raise WebPipelineConfigError("preset 名称只允许字母、数字、下划线和连字符")
    path = (presets_dir / f"{name}.yaml").resolve()
    try:
        path.relative_to(presets_dir.resolve())
    except ValueError as exc:
        raise WebPipelineConfigError("preset 路径逃逸") from exc
    return path


def _read_preset(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise WebPipelineConfigError(f"preset 不存在: {path.stem}")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if data.get("schema_version") != 1 or data.get("name") != path.stem:
        raise WebPipelineConfigError(f"preset 格式无效: {path}")
    return {"schema_version": 1, "name": path.stem, "overrides": _normalize_overrides(data.get("overrides", {}))}


def _deep_merge(target: dict[str, Any], update: dict[str, Any]) -> None:
    for key, value in update.items():
        if isinstance(value, dict) and isinstance(target.get(key), dict):
            _deep_merge(target[key], value)
        else:
            target[key] = deepcopy(value)


def _diff(base: Any, current: Any, prefix: str = "") -> list[dict[str, Any]]:
    if isinstance(base, dict) and isinstance(current, dict):
        result: list[dict[str, Any]] = []
        for key in sorted(set(base) | set(current)):
            path = f"{prefix}.{key}" if prefix else key
            result.extend(_diff(base.get(key), current.get(key), path))
        return result
    return [] if base == current else [{"path": prefix, "default": base, "effective": current}]


def _optional_float(value: Any) -> float | None:
    return None if value in (None, "") else float(value)


def _optional_int(value: Any) -> int | None:
    return None if value in (None, "") else int(value)
