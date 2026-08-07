"""Training-readiness interpretation for LeRobot quality reports."""

from __future__ import annotations

import json
import math
import statistics
import hashlib
from pathlib import Path
from typing import Any

try:  # pyarrow is available in the data-clean environment, but keep reports robust.
    import pyarrow.parquet as pq
except Exception:  # pragma: no cover - environment fallback
    pq = None  # type: ignore[assignment]

try:  # OpenCV is used only for lightweight video metadata/first-frame checks.
    import cv2
except Exception:  # pragma: no cover - environment fallback
    cv2 = None  # type: ignore[assignment]

from schemas.lerobot_features import lerobot_feature_schema


ACTION_DIMENSIONS = [
    {"index": 0, "key": "left_x", "label": "左手 x", "group": "left", "unit": "m"},
    {"index": 1, "key": "left_y", "label": "左手 y", "group": "left", "unit": "m"},
    {"index": 2, "key": "left_z", "label": "左手 z", "group": "left", "unit": "m"},
    {"index": 3, "key": "left_qx", "label": "左手 qx", "group": "left", "unit": "quat"},
    {"index": 4, "key": "left_qy", "label": "左手 qy", "group": "left", "unit": "quat"},
    {"index": 5, "key": "left_qz", "label": "左手 qz", "group": "left", "unit": "quat"},
    {"index": 6, "key": "left_qw", "label": "左手 qw", "group": "left", "unit": "quat"},
    {"index": 7, "key": "left_gripper", "label": "左夹爪", "group": "left", "unit": "0-1"},
    {"index": 8, "key": "right_x", "label": "右手 x", "group": "right", "unit": "m"},
    {"index": 9, "key": "right_y", "label": "右手 y", "group": "right", "unit": "m"},
    {"index": 10, "key": "right_z", "label": "右手 z", "group": "right", "unit": "m"},
    {"index": 11, "key": "right_qx", "label": "右手 qx", "group": "right", "unit": "quat"},
    {"index": 12, "key": "right_qy", "label": "右手 qy", "group": "right", "unit": "quat"},
    {"index": 13, "key": "right_qz", "label": "右手 qz", "group": "right", "unit": "quat"},
    {"index": 14, "key": "right_qw", "label": "右手 qw", "group": "right", "unit": "quat"},
    {"index": 15, "key": "right_gripper", "label": "右夹爪", "group": "right", "unit": "0-1"},
]

STATUS_LABELS = {
    "pass": "通过",
    "review": "需要复查",
    "block": "暂不建议训练",
    "info": "仅展示",
}

SUBSCORE_EXPLANATIONS = {
    "action_diversity": {
        "name": "动作多样性",
        "meaning": "动作变化是否覆盖了足够多的范围。",
        "impact": "太低时，模型容易只学到少量重复动作。",
    },
    "gripper_health": {
        "name": "夹爪健康度",
        "meaning": "夹爪开闭是否过度抖动或异常频繁切换。",
        "impact": "太低时，模型可能学到不稳定的夹爪控制。",
    },
    "timestamp_regularity": {
        "name": "时间戳规律性",
        "meaning": "帧间时间是否稳定。",
        "impact": "太低时，训练样本的时序关系会变得不可靠。",
    },
    "static_detection": {
        "name": "静止检测",
        "meaning": "episode 是否大段时间没有动作。",
        "impact": "太低时，数据里可能有太多无效等待片段。",
    },
    "smoothness": {
        "name": "动作平滑度",
        "meaning": "轨迹是否抖动，Forge 使用 jerk 相关指标估计。",
        "impact": "太低时，模型会学到抖动或不连续的动作。",
    },
    "dead_actions": {
        "name": "无效动作比例",
        "meaning": "动作是否长时间几乎为零。",
        "impact": "太低时，模型会学到停住不动。",
    },
    "action_saturation": {
        "name": "动作贴边程度",
        "meaning": "动作是否长时间贴在自身观测范围的边缘。",
        "impact": "太低时，可能是归一化、夹爪范围或采集动作范围有问题。",
    },
}


def build_training_readiness_summary(
    *,
    job: dict[str, Any],
    quality_summary: dict[str, Any],
    dataset_dir: str | Path,
    reports_dir: str | Path,
) -> dict[str, Any]:
    """Build and persist a beginner-readable training-readiness summary."""

    dataset_path = Path(dataset_dir).expanduser()
    report_path = Path(reports_dir).expanduser() / "training_readiness_summary.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)

    inspect_data = _read_json(_path_or_default(quality_summary.get("inspect_report"), report_path.parent / "forge_inspect.json"), {})
    quality_data = _read_json(_path_or_default(quality_summary.get("quality_report"), report_path.parent / "forge_quality.json"), {})
    flagged_data = _read_json(_path_or_default(quality_summary.get("flagged_report"), report_path.parent / "forge_quality_flagged.json"), {})
    stats_data = _read_json(dataset_path / "meta" / "stats.json", {})
    quality_context = {**quality_data, **quality_summary} if isinstance(quality_data, dict) else dict(quality_summary)

    dataset_size = _dataset_size(job, quality_context, inspect_data)
    alignment = _alignment_summary(job)
    gripper = _gripper_tactile_summary(job, alignment)
    bridge = _bridge_summary(job)
    feature_contract = _feature_contract(job, bridge)
    action_dimensions = feature_contract["action_dimension_labels"]
    action_saturation = _action_saturation_summary(dataset_path, action_dimensions)
    storage_media = _storage_media_summary(job, dataset_path, inspect_data, dataset_size)

    modules = [
        _format_module(job, quality_context, inspect_data, bridge, feature_contract),
        _storage_media_module(storage_media),
        _action_module(quality_context, action_saturation),
        _sync_module(alignment, dataset_size),
        _gripper_module(gripper),
        _scale_module(dataset_size),
    ]

    conclusion_level = _conclusion_level(modules)
    risks = _top_risks(modules)
    actions = _next_actions(modules)
    episode_risks = _episode_risks(quality_context, action_saturation)

    summary = {
        "version": 1,
        "conclusion": STATUS_LABELS[conclusion_level],
        "level": conclusion_level,
        "headline": _headline(conclusion_level),
        "key_risks": risks,
        "next_actions": actions,
        "modules": modules,
        "dataset_size": dataset_size,
        "action_dimension_labels": action_dimensions,
        "action_saturation": action_saturation,
        "episode_risks": episode_risks,
        "alignment_summary": alignment,
        "gripper_summary": gripper,
        "bridge_summary": bridge,
        "feature_contract": feature_contract,
        "contract_fingerprint": feature_contract["contract_fingerprint"],
        "storage_media": storage_media,
        "subscore_explanations": SUBSCORE_EXPLANATIONS,
        "format_details": _format_details(quality_context, inspect_data, stats_data, flagged_data),
        "report_path": str(report_path),
    }
    _write_json_atomic(report_path, summary)
    return summary


def training_readiness_contract_fingerprint(job: dict[str, Any]) -> str:
    """Return the LeRobot feature contract fingerprint expected for this job."""

    return str(_feature_contract(job, _bridge_summary(job))["contract_fingerprint"])


def count_flagged_episodes(flagged: Any) -> int:
    """Count unique flagged episodes from Forge's list or dict export shapes."""

    if isinstance(flagged, list):
        return len(flagged)
    if isinstance(flagged, dict):
        episode_ids: set[str] = set()
        for value in flagged.values():
            if isinstance(value, list):
                episode_ids.update(str(item) for item in value)
        return len(episode_ids)
    return 0


def _read_json(path: Path, fallback: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return fallback


def _write_json_atomic(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def _path_or_default(value: Any, default: Path) -> Path:
    text = str(value or "").strip()
    return Path(text).expanduser() if text else default


def _as_float(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _as_int(value: Any) -> int | None:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    return number


def _pct(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value * 100:.1f}%"


def _dataset_size(job: dict[str, Any], quality: dict[str, Any], inspect: dict[str, Any]) -> dict[str, Any]:
    dataset = job.get("dataset_summary") if isinstance(job.get("dataset_summary"), dict) else {}
    frames = _as_int(quality.get("total_frames") or inspect.get("total_frames") or dataset.get("frames")) or 0
    episodes = _as_int(quality.get("num_episodes") or inspect.get("num_episodes") or dataset.get("episodes")) or 0
    fps = _as_float(dataset.get("fps") or inspect.get("inferred_fps")) or 0.0
    duration = frames / fps if fps > 0 else None
    return {
        "episodes": episodes,
        "frames": frames,
        "fps": fps,
        "duration_seconds": duration,
        "duration_text": f"约 {duration:.1f} 秒" if duration is not None else "-",
        "note": "数据量只展示，不参与本页训练可用性判定。",
    }


def _format_module(
    job: dict[str, Any],
    quality: dict[str, Any],
    inspect: dict[str, Any],
    bridge: dict[str, Any],
    feature_contract: dict[str, Any],
) -> dict[str, Any]:
    issues: list[str] = []
    risks: list[str] = []
    missing_required = inspect.get("missing_required") if isinstance(inspect, dict) else []
    if quality.get("format") != "lerobot-v3":
        issues.append("最终数据集不是 LeRobot v3 格式。")
    if isinstance(missing_required, list) and missing_required:
        issues.append(f"缺少训练必需字段：{', '.join(map(str, missing_required))}。")
    if not inspect.get("has_timestamps", True):
        issues.append("缺少 timestamp，无法可靠构建时序样本。")
    if not _has_dual_cameras(inspect):
        issues.append("未检测到 left/right 双目图像。")
    if not bridge.get("all_training_eligible", True):
        issues.append("存在 bridge 结果 training_eligible=false。")
    bridge_mode = job.get("bridge_mode")
    if bridge_mode and str(bridge_mode) != "formal":
        issues.append("当前不是 formal 导出，不能代表正式训练数据。")
    if job.get("calibration_ready") is False:
        issues.append("生产标定未就绪，原始坐标系下的 TCP 位姿不可作为正式训练输入。")

    state_dim = _shape_dim(inspect.get("observation_schema", {}).get("observation.state")) or _as_int((job.get("dataset_summary") or {}).get("state_dim"))
    action_dim = _shape_dim(inspect.get("action_schema")) or _as_int((job.get("dataset_summary") or {}).get("action_dim"))
    expected_state_dim = _as_int(feature_contract.get("expected_state_dim"))
    expected_action_dim = _as_int(feature_contract.get("expected_action_dim"))
    if expected_state_dim is not None and state_dim != expected_state_dim:
        issues.append(
            "observation.state 维度与当前 LeRobot 维度配置不一致，"
            f"期望 {expected_state_dim}，当前为 {state_dim or '-'}。"
        )
    if expected_action_dim is not None and action_dim != expected_action_dim:
        issues.append(
            "action 维度与当前 LeRobot 维度配置不一致，"
            f"期望 {expected_action_dim}，当前为 {action_dim or '-'}。"
        )

    status = "block" if issues else "pass"
    summary = "格式、camera→TCP 外参、双目图像、state/action 维度均满足当前 LeRobot 维度配置。" if not issues else issues[0]
    risks.extend(issues)
    return {
        "id": "format_input",
        "title": "格式输入",
        "status": status,
        "label": STATUS_LABELS[status],
        "summary": summary,
        "risks": risks,
        "metrics": {
            "format": quality.get("format"),
            "state_dim": state_dim,
            "action_dim": action_dim,
            "expected_state_dim": expected_state_dim,
            "expected_action_dim": expected_action_dim,
            "feature_schema_version": feature_contract.get("feature_schema_version"),
            "contract_fingerprint": feature_contract.get("contract_fingerprint"),
            "has_timestamps": inspect.get("has_timestamps"),
            "has_language": inspect.get("has_language"),
            "dual_cameras": _has_dual_cameras(inspect),
            "bridge_mode": job.get("bridge_mode"),
            "calibration_ready": job.get("calibration_ready"),
        },
    }


def _action_module(quality: dict[str, Any], saturation: dict[str, Any]) -> dict[str, Any]:
    subscores = quality.get("subscores") if isinstance(quality.get("subscores"), dict) else {}
    per_episode = quality.get("per_episode") if isinstance(quality.get("per_episode"), list) else []
    risks: list[str] = []

    saturated_eps = [
        ep for ep in per_episode
        if "saturated" in (ep.get("flags") or []) or (_as_float(ep.get("overall_saturation")) or 0.0) > 0.30
    ]
    if saturated_eps:
        risks.append(f"{len(saturated_eps)}/{len(per_episode) or len(saturated_eps)} 个 episode 动作长时间贴近自身边界。")

    smoothness = _as_float(subscores.get("smoothness"))
    if smoothness is not None and smoothness < 0.70:
        risks.append(f"动作平滑度较低：smoothness={smoothness:.3f}，建议看 3D 轨迹确认是否抖动。")

    gripper_health = _as_float(subscores.get("gripper_health"))
    if gripper_health is not None and gripper_health < 0.85:
        risks.append(f"夹爪控制健康度偏低：gripper_health={gripper_health:.3f}。")

    dead_actions = _as_float(subscores.get("dead_actions"))
    if dead_actions is not None and dead_actions < 0.85:
        risks.append(f"无效动作比例偏高：dead_actions={dead_actions:.3f}。")

    diversity = _as_float(subscores.get("action_diversity"))
    if diversity is not None and diversity < 0.50:
        risks.append(f"动作多样性偏低：action_diversity={diversity:.3f}。")

    top_dims = saturation.get("top_dimensions") if isinstance(saturation.get("top_dimensions"), list) else []
    if top_dims and risks:
        dim_text = "、".join(str(item.get("label")) for item in top_dims[:3])
        risks[0] = f"{risks[0]} 主要维度：{dim_text}。"

    status = "review" if risks else "pass"
    return {
        "id": "action_health",
        "title": "动作健康",
        "status": status,
        "label": STATUS_LABELS[status],
        "summary": "动作质量存在复查点，先看饱和维度和平滑度。" if risks else "动作分布没有明显质量风险。",
        "risks": risks,
        "metrics": {
            "overall_score": quality.get("overall_score"),
            "subscores": subscores,
            "global_flags": quality.get("flags", []),
            "top_saturated_dimensions": top_dims[:5],
        },
    }


def _sync_module(alignment: dict[str, Any], size: dict[str, Any]) -> dict[str, Any]:
    risks: list[str] = []
    max_dt_ms = _as_float(alignment.get("max_dt_ms"))
    if max_dt_ms is not None and max_dt_ms > 50:
        risks.append(f"图像/夹爪对齐最大延迟 {max_dt_ms:.1f} ms，接近或超过一帧间隔。")
    if int(alignment.get("missing_time_count") or 0) > 0:
        risks.append("对齐报告存在 missing time。")
    if int(alignment.get("timeout_count") or 0) > 0:
        risks.append("对齐报告存在 timeout。")
    if int(alignment.get("fallback_nearest_count") or 0) > 0:
        risks.append("对齐报告使用了 fallback nearest。")
    if int(alignment.get("unavailable_count") or 0) > 0:
        risks.append("对齐报告存在 unavailable 字段。")
    status = "review" if risks else "pass"
    frame_ms = 1000 / size["fps"] if size.get("fps") else None
    summary = (
        f"对齐最大延迟 {max_dt_ms:.1f} ms，未发现 missing/timeout/fallback。"
        if status == "pass" and max_dt_ms is not None
        else (risks[0] if risks else "暂无对齐明细。")
    )
    return {
        "id": "sync_quality",
        "title": "同步质量",
        "status": status,
        "label": STATUS_LABELS[status],
        "summary": summary,
        "risks": risks,
        "metrics": {
            "avg_dt_ms": alignment.get("avg_dt_ms"),
            "max_dt_ms": alignment.get("max_dt_ms"),
            "frame_interval_ms": frame_ms,
            "terminal_dropped_steps": alignment.get("terminal_dropped_steps"),
            "missing_time_count": alignment.get("missing_time_count"),
            "timeout_count": alignment.get("timeout_count"),
            "fallback_nearest_count": alignment.get("fallback_nearest_count"),
            "unavailable_count": alignment.get("unavailable_count"),
        },
    }


def _gripper_module(gripper: dict[str, Any]) -> dict[str, Any]:
    risks: list[str] = []
    max_rate = _as_float(gripper.get("max_gripper_interpolation_rate"))
    if max_rate is not None and max_rate > 0.10:
        stream = gripper.get("max_gripper_interpolation_stream") or "夹爪宽度"
        risks.append(f"{stream} 插值比例 {_pct(max_rate)}，建议抽查夹爪识别画面。")
    tactile_min = _as_float(gripper.get("min_tactile_coverage_ratio"))
    if tactile_min is not None and tactile_min < 0.80:
        risks.append(f"触觉覆盖率最低 {_pct(tactile_min)}，触觉信号只建议作为辅助复查。")
    status = "review" if risks else "pass"
    return {
        "id": "gripper_tactile",
        "title": "夹爪/触觉",
        "status": status,
        "label": STATUS_LABELS[status],
        "summary": "夹爪或触觉存在复查点。" if risks else "夹爪和触觉摘要未发现明显风险。",
        "risks": risks,
        "metrics": gripper,
    }


def _storage_media_module(storage: dict[str, Any]) -> dict[str, Any]:
    status = str(storage.get("status") or "info")
    return {
        "id": "storage_media",
        "title": "文件大小/视频完整性",
        "status": status,
        "label": STATUS_LABELS.get(status, status),
        "summary": str(storage.get("summary") or "暂无文件大小和媒体校验摘要。"),
        "risks": list(storage.get("risks") or []),
        "metrics": storage,
    }


def _scale_module(size: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": "dataset_scale",
        "title": "数据量",
        "status": "info",
        "label": STATUS_LABELS["info"],
        "summary": (
            f"{size.get('episodes', 0)} episodes / {size.get('frames', 0)} frames / "
            f"{size.get('duration_text', '-')} / {size.get('fps') or '-'} FPS。"
        ),
        "risks": [],
        "metrics": size,
    }


def _conclusion_level(modules: list[dict[str, Any]]) -> str:
    if any(module["status"] == "block" for module in modules):
        return "block"
    if any(module["status"] == "review" for module in modules):
        return "review"
    return "pass"


def _headline(level: str) -> str:
    if level == "block":
        return "当前数据集存在训练输入契约问题，先修复后再进入训练。"
    if level == "review":
        return "数据集技术链路已生成，但存在会影响训练质量的风险，建议复查后再训练。"
    return "数据集通过当前技术体检，可以作为训练输入继续使用。"


def _top_risks(modules: list[dict[str, Any]]) -> list[str]:
    risks: list[str] = []
    for module_id in ("format_input", "storage_media", "action_health", "sync_quality", "gripper_tactile"):
        module = next((item for item in modules if item["id"] == module_id), None)
        if module:
            risks.extend(module.get("risks", []))
    return risks[:3] or ["未发现会阻止训练输入的技术风险。"]


def _next_actions(modules: list[dict[str, Any]]) -> list[str]:
    by_id = {module["id"]: module for module in modules}
    actions: list[str] = []
    if by_id.get("format_input", {}).get("status") == "block":
        actions.append("先修复格式、formal 标定或 training_eligible 问题，再重新生成 dataset。")
    if by_id.get("storage_media", {}).get("status") == "block":
        actions.append("先修复 LeRobot 数据集缺失的 parquet/mp4 或帧数不一致问题，再进入训练。")
    elif by_id.get("storage_media", {}).get("status") == "review":
        actions.append("抽查视频首帧和文件大小体检，确认小目录不是黑屏、空视频或异常压缩。")
    if by_id.get("action_health", {}).get("status") == "review":
        actions.append("打开 3D 轨迹，重点播放带 saturated 或 smoothness 低的 episode。")
        actions.append("检查动作归一化、夹爪范围和采集动作是否长时间贴边。")
    if by_id.get("sync_quality", {}).get("status") == "review":
        actions.append("检查 alignment_report 中延迟、missing、timeout 或 fallback 的字段。")
    if by_id.get("gripper_tactile", {}).get("status") == "review":
        actions.append("抽查夹爪图像识别和 ArUco 检测，确认插值片段是否可接受。")
    if not actions:
        actions.append("继续积累更多同任务 episode，并在训练前保留这份报告用于追溯。")
    return actions[:3]


def _format_details(quality: dict[str, Any], inspect: dict[str, Any], stats: dict[str, Any], flagged: Any) -> dict[str, Any]:
    return {
        "format": quality.get("format") or inspect.get("format"),
        "format_version": inspect.get("format_version"),
        "missing_required": inspect.get("missing_required", []),
        "cameras": inspect.get("cameras", {}),
        "observation_schema": inspect.get("observation_schema", {}),
        "action_schema": inspect.get("action_schema", {}),
        "has_timestamps": inspect.get("has_timestamps"),
        "has_language": inspect.get("has_language"),
        "language_coverage": inspect.get("language_coverage"),
        "flagged_episode_count": count_flagged_episodes(flagged),
        "stats_count": (stats.get("action") or {}).get("count") if isinstance(stats, dict) else None,
    }


def _has_dual_cameras(inspect: dict[str, Any]) -> bool:
    cameras = inspect.get("cameras") if isinstance(inspect.get("cameras"), dict) else {}
    return "left" in cameras and "right" in cameras


def _shape_dim(schema: Any) -> int | None:
    if not isinstance(schema, dict):
        return None
    shape = schema.get("shape")
    if isinstance(shape, list) and shape:
        return _as_int(shape[0])
    return None


def _feature_contract(job: dict[str, Any], bridge: dict[str, Any]) -> dict[str, Any]:
    schema = _feature_schema_from_job(job)
    source = "job_effective_config"
    if schema is None:
        schema = bridge.get("feature_schema") if isinstance(bridge.get("feature_schema"), dict) else None
        source = "bridge_report"
    if schema is None:
        schema = lerobot_feature_schema(None)
        source = "legacy_default"
    state_schema = schema.get("observation.state") if isinstance(schema.get("observation.state"), dict) else {}
    action_schema = schema.get("action") if isinstance(schema.get("action"), dict) else {}
    expected_state_dim = _shape_dim(state_schema)
    expected_action_dim = _shape_dim(action_schema)
    action_dimensions = _action_dimensions_from_schema(action_schema)
    return {
        "source": source,
        "feature_schema_version": schema.get("feature_schema_version") or schema.get("schema_version"),
        "expected_state_dim": expected_state_dim,
        "expected_action_dim": expected_action_dim,
        "action_dimension_labels": action_dimensions,
        "schema": schema,
        "contract_fingerprint": _contract_fingerprint(schema),
    }


def _feature_schema_from_job(job: dict[str, Any]) -> dict[str, Any] | None:
    summary = job.get("effective_config_summary")
    if isinstance(summary, dict) and isinstance(summary.get("lerobot_features"), dict):
        try:
            return lerobot_feature_schema(summary["lerobot_features"])
        except Exception:
            return None
    return None


def _contract_fingerprint(schema: dict[str, Any]) -> str:
    existing = schema.get("contract_fingerprint") or schema.get("fingerprint")
    if existing:
        return str(existing)
    relevant = {
        "state": schema.get("observation.state", {}),
        "action": schema.get("action", {}),
    }
    payload = json.dumps(relevant, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _action_dimensions_from_schema(action_schema: dict[str, Any]) -> list[dict[str, Any]]:
    segments = action_schema.get("segments") if isinstance(action_schema, dict) else None
    if not isinstance(segments, list):
        return [dict(item) for item in ACTION_DIMENSIONS]
    dimensions: list[dict[str, Any]] = []
    for segment in segments:
        if not isinstance(segment, dict):
            continue
        offset = segment.get("offset")
        dim = _as_int(segment.get("dim"))
        if not isinstance(offset, list) or len(offset) < 2 or dim is None:
            continue
        start = _as_int(offset[0])
        end = _as_int(offset[1])
        if start is None or end is None or end <= start:
            continue
        components = segment.get("components") if isinstance(segment.get("components"), list) else []
        for index in range(start, end):
            local_index = index - start
            component = str(components[local_index]) if local_index < len(components) else f"dim{local_index}"
            dimensions.append(
                {
                    "index": index,
                    "key": f"{segment.get('name')}.{component}",
                    "label": _action_dimension_label(str(segment.get("name") or ""), component),
                    "group": _dimension_group(str(segment.get("name") or "")),
                    "unit": _component_unit(segment, component),
                    "segment": segment.get("name"),
                    "component": component,
                }
            )
    return dimensions or [dict(item) for item in ACTION_DIMENSIONS]


def _action_dimension_label(segment_name: str, component: str) -> str:
    if "left" in segment_name:
        prefix = "左手"
    elif "right" in segment_name:
        prefix = "右手"
    else:
        prefix = "动作"
    if "gripper" in segment_name:
        return "左夹爪" if "left" in segment_name else "右夹爪" if "right" in segment_name else "夹爪"
    return f"{prefix} {component}"


def _dimension_group(segment_name: str) -> str:
    if "left" in segment_name:
        return "left"
    if "right" in segment_name:
        return "right"
    return "action"


def _component_unit(segment: dict[str, Any], component: str) -> str:
    unit = str(segment.get("unit") or "")
    if component in {"qx", "qy", "qz", "qw"}:
        return "quat"
    if "normalized" in unit or "0_to_1" in unit:
        return "0-1"
    if unit.startswith("m"):
        return "m"
    return unit or "-"


def _bridge_summary(job: dict[str, Any]) -> dict[str, Any]:
    files = job.get("files") if isinstance(job.get("files"), list) else []
    reports = []
    training_values = []
    dropped = 0
    feature_schema = None
    lerobot_features = None
    for item in files:
        outputs = item.get("stage_outputs") if isinstance(item.get("stage_outputs"), dict) else {}
        if "training_eligible" in outputs:
            training_values.append(bool(outputs.get("training_eligible")))
        report_path = outputs.get("forge_bridge_report")
        if report_path:
            report = _read_json(Path(str(report_path)), {})
            if isinstance(report, dict):
                reports.append(report)
                training_values.append(bool(report.get("training_eligible", False)))
                dropped += int(report.get("dropped_terminal_step_count") or 0)
                if feature_schema is None and isinstance(report.get("feature_schema"), dict):
                    feature_schema = report["feature_schema"]
                if lerobot_features is None and isinstance(report.get("lerobot_features"), dict):
                    lerobot_features = report["lerobot_features"]
    return {
        "bridge_count": len(reports),
        "all_training_eligible": all(training_values) if training_values else True,
        "training_eligible_values": training_values,
        "terminal_dropped_steps": dropped,
        "modes": sorted({str(report.get("mode")) for report in reports if report.get("mode")}),
        "feature_schema": feature_schema,
        "lerobot_features": lerobot_features,
    }


def _alignment_summary(job: dict[str, Any]) -> dict[str, Any]:
    files = job.get("files") if isinstance(job.get("files"), list) else []
    reports = []
    avg_values: list[float] = []
    max_values: list[float] = []
    coverage_values: list[float] = []
    totals = {
        "missing_time_count": 0,
        "timeout_count": 0,
        "fallback_nearest_count": 0,
        "unavailable_count": 0,
        "terminal_dropped_steps": 0,
    }
    for item in files:
        outputs = item.get("stage_outputs") if isinstance(item.get("stage_outputs"), dict) else {}
        report_path = outputs.get("alignment_report")
        if not report_path:
            continue
        report = _read_json(Path(str(report_path)), {})
        if not isinstance(report, dict):
            continue
        reports.append(report)
        for stats in (report.get("field_stats") or {}).values():
            if not isinstance(stats, dict):
                continue
            avg = _as_float(stats.get("avg_dt_ms"))
            mx = _as_float(stats.get("max_dt_ms"))
            coverage = _as_float(stats.get("coverage_ratio"))
            if avg is not None:
                avg_values.append(avg)
            if mx is not None:
                max_values.append(mx)
            if coverage is not None:
                coverage_values.append(coverage)
        degrade = report.get("degradation_summary") if isinstance(report.get("degradation_summary"), dict) else {}
        totals["missing_time_count"] += int(degrade.get("missing_time_count") or 0)
        totals["timeout_count"] += int(degrade.get("timeout_count") or 0)
        totals["fallback_nearest_count"] += int(degrade.get("fallback_nearest_count") or 0)
        totals["unavailable_count"] += int(degrade.get("unavailable_count") or 0)
    bridge = _bridge_summary(job)
    totals["terminal_dropped_steps"] = int(bridge.get("terminal_dropped_steps") or 0)
    return {
        "report_count": len(reports),
        "avg_dt_ms": statistics.mean(avg_values) if avg_values else None,
        "max_dt_ms": max(max_values) if max_values else None,
        "min_tactile_coverage_ratio": min(coverage_values) if coverage_values else None,
        **totals,
    }


def _gripper_tactile_summary(job: dict[str, Any], alignment: dict[str, Any]) -> dict[str, Any]:
    files = job.get("files") if isinstance(job.get("files"), list) else []
    streams: list[dict[str, Any]] = []
    max_rate = 0.0
    max_stream = None
    for item in files:
        report = item.get("report") if isinstance(item.get("report"), dict) else {}
        for stream in report.get("gripper_topics") or []:
            if not isinstance(stream, dict):
                continue
            frames = int(stream.get("frame_count") or 0)
            interpolated = int(stream.get("interpolated_frames") or 0)
            rate = interpolated / frames if frames > 0 else 0.0
            name = str(stream.get("output_topic") or stream.get("image_topic") or "夹爪宽度")
            streams.append(
                {
                    "file": item.get("name"),
                    "stream": name,
                    "frame_count": frames,
                    "interpolated_frames": interpolated,
                    "missing_frames": int(stream.get("missing_frames") or 0),
                    "interpolation_rate": rate,
                }
            )
            if rate > max_rate:
                max_rate = rate
                max_stream = name
    return {
        "streams": streams,
        "max_gripper_interpolation_rate": max_rate if streams else None,
        "max_gripper_interpolation_stream": max_stream,
        "min_tactile_coverage_ratio": alignment.get("min_tactile_coverage_ratio"),
    }


def _storage_media_summary(
    job: dict[str, Any],
    dataset_dir: Path,
    inspect: dict[str, Any],
    dataset_size: dict[str, Any],
) -> dict[str, Any]:
    info_path = dataset_dir / "meta" / "info.json"
    info = _read_json(info_path, {})
    expected_frames = (
        _as_int(info.get("total_frames")) if isinstance(info, dict) else None
    ) or _as_int(dataset_size.get("frames")) or 0
    expected_fps = (
        _as_float(info.get("fps")) if isinstance(info, dict) else None
    ) or _as_float(dataset_size.get("fps"))

    dataset_total = _path_size(dataset_dir)
    data_total = _path_size(dataset_dir / "data")
    video_total = _path_size(dataset_dir / "videos")
    meta_total = _path_size(dataset_dir / "meta")
    raw = _raw_mcap_summary(job)
    parquet = _parquet_integrity(dataset_dir, expected_frames)
    videos = _video_integrity(
        dataset_dir=dataset_dir,
        info=info if isinstance(info, dict) else {},
        inspect=inspect,
        parquet=parquet,
        expected_frames=expected_frames,
        expected_fps=expected_fps,
        video_total_size=video_total,
    )

    storage_block_reasons = [] if info_path.exists() else ["缺少 meta/info.json，无法确认 LeRobot 数据集元信息。"]
    block_reasons = storage_block_reasons + list(parquet.get("block_reasons") or []) + list(videos.get("block_reasons") or [])
    review_reasons = list(parquet.get("review_reasons") or []) + list(videos.get("review_reasons") or [])
    raw_total = int(raw.get("total_size_bytes") or 0)
    compression_ratio = raw_total / dataset_total if raw_total > 0 and dataset_total > 0 else None
    decoded_frame_count = int(videos.get("decoded_frame_count") or 0)
    bytes_per_video_frame = video_total / decoded_frame_count if video_total > 0 and decoded_frame_count > 0 else None
    if bytes_per_video_frame is not None and bytes_per_video_frame < 500 and not block_reasons:
        review_reasons.append("mp4 平均每帧字节数极低，虽然帧数完整，也建议抽查是否过度压缩或近似空画面。")
    if compression_ratio is not None and compression_ratio > 2000 and not block_reasons:
        review_reasons.append(f"raw 到 LeRobot 压缩比约 {compression_ratio:.0f}x，明显高于常见视频压缩结果，建议复查导出字段。")

    if block_reasons:
        status = "block"
        summary = f"媒体/表格完整性存在阻断问题：{block_reasons[0]}"
    elif review_reasons:
        status = "review"
        summary = f"文件能读，但存在需要复查的问题：{review_reasons[0]}"
    else:
        prefix = (
            f"raw {_format_bytes(raw_total)} -> LeRobot {_format_bytes(dataset_total)}"
            if raw_total > 0
            else f"LeRobot {_format_bytes(dataset_total)}"
        )
        summary = (
            f"{prefix}；{videos.get('video_file_count', 0)} 个 mp4 与 "
            f"{expected_frames or parquet.get('total_rows') or '-'} frames 匹配。"
            "目录小不是直接问题：raw MCAP 含原始流和额外 topic，LeRobot 只保留训练字段，视频又经过 H.264 压缩。"
        )
        status = "pass"

    return {
        "status": status,
        "summary": summary,
        "risks": block_reasons + review_reasons,
        "explanation": "目录小不是直接问题：raw MCAP 含原始流和额外 topic，LeRobot 只保留训练字段，视频又经过 H.264 压缩。",
        "dataset_dir": str(dataset_dir),
        "dataset_total_size_bytes": dataset_total,
        "dataset_total_size_text": _format_bytes(dataset_total),
        "data_size_bytes": data_total,
        "data_size_text": _format_bytes(data_total),
        "video_total_size_bytes": video_total,
        "video_total_size_text": _format_bytes(video_total),
        "meta_size_bytes": meta_total,
        "meta_size_text": _format_bytes(meta_total),
        "raw_total_size_bytes": raw_total,
        "raw_total_size_text": _format_bytes(raw_total) if raw_total else "-",
        "raw_to_dataset_ratio": compression_ratio,
        "bytes_per_video_frame": bytes_per_video_frame,
        "expected_frames": expected_frames,
        "expected_fps": expected_fps,
        "parquet_total_rows": parquet.get("total_rows"),
        "parquet_row_check": parquet.get("row_check"),
        "video_file_count": videos.get("video_file_count", 0),
        "expected_video_file_count": videos.get("expected_video_file_count", 0),
        "video_frame_check": videos.get("frame_check"),
        "video_resolution_check": videos.get("resolution_check"),
        "video_fps_check": videos.get("fps_check"),
        "raw_files": raw.get("files", []),
        "parquet": parquet,
        "videos": videos,
    }


def _raw_mcap_summary(job: dict[str, Any]) -> dict[str, Any]:
    raw_paths: list[Path] = []
    seen: set[str] = set()
    files = job.get("files") if isinstance(job.get("files"), list) else []
    for item in files:
        if not isinstance(item, dict):
            continue
        raw = item.get("input_path") or item.get("source_path")
        if not raw:
            continue
        path = Path(str(raw)).expanduser()
        key = str(path)
        if key not in seen:
            seen.add(key)
            raw_paths.append(path)

    entries = []
    total = 0
    for path in raw_paths:
        exists = path.exists()
        size = path.stat().st_size if exists and path.is_file() else 0
        total += size
        entries.append(
            {
                "path": str(path),
                "name": path.name,
                "exists": exists,
                "size_bytes": size,
                "size_text": _format_bytes(size) if size else "-",
            }
        )
    return {"files": entries, "file_count": len(entries), "total_size_bytes": total, "total_size_text": _format_bytes(total) if total else "-"}


def _parquet_integrity(dataset_dir: Path, expected_frames: int) -> dict[str, Any]:
    files = sorted((dataset_dir / "data").glob("chunk-*/*.parquet"))
    block_reasons: list[str] = []
    review_reasons: list[str] = []
    rows = []
    total_rows = 0
    if not files:
        block_reasons.append("缺少 data/chunk-*/*.parquet，训练 action/state 表格没有写出。")
    if pq is None:
        review_reasons.append("当前环境没有 pyarrow，无法核对 parquet 行数。")
        return {
            "available": False,
            "files": [{"path": str(path), "relative_path": _relative_path(path, dataset_dir), "key": _chunk_file_key(path), "rows": None} for path in files],
            "file_count": len(files),
            "total_rows": None,
            "expected_frames": expected_frames,
            "row_check": "unknown",
            "block_reasons": block_reasons,
            "review_reasons": review_reasons,
        }

    for path in files:
        relative = _relative_path(path, dataset_dir)
        row = {"path": str(path), "relative_path": relative, "key": _chunk_file_key(path), "rows": 0, "episodes": [], "frame_index_min": None, "frame_index_max": None}
        try:
            parquet_file = pq.ParquetFile(path)
            row_count = int(parquet_file.metadata.num_rows)
            row["rows"] = row_count
            total_rows += row_count
            columns = set(parquet_file.schema_arrow.names)
            read_columns = [name for name in ("episode_index", "frame_index") if name in columns]
            if read_columns:
                table = pq.read_table(path, columns=read_columns)
                data = table.to_pydict()
                episodes = data.get("episode_index") or []
                frames = data.get("frame_index") or []
                if episodes:
                    row["episodes"] = sorted({int(value) for value in episodes})
                if frames:
                    row["frame_index_min"] = int(min(frames))
                    row["frame_index_max"] = int(max(frames))
        except Exception as exc:  # noqa: BLE001
            block_reasons.append(f"{relative} 无法读取：{type(exc).__name__}: {exc}")
        rows.append(row)

    row_check = "match"
    if expected_frames and total_rows != expected_frames:
        row_check = "mismatch"
        block_reasons.append(f"parquet 总行数 {total_rows} 与 meta/job frames {expected_frames} 不一致。")
    elif block_reasons:
        row_check = "failed"
    return {
        "available": True,
        "files": rows,
        "file_count": len(files),
        "total_rows": total_rows,
        "expected_frames": expected_frames,
        "row_check": row_check,
        "block_reasons": block_reasons,
        "review_reasons": review_reasons,
    }


def _video_integrity(
    *,
    dataset_dir: Path,
    info: dict[str, Any],
    inspect: dict[str, Any],
    parquet: dict[str, Any],
    expected_frames: int,
    expected_fps: float | None,
    video_total_size: int,
) -> dict[str, Any]:
    specs = _video_feature_specs(dataset_dir, info, inspect, expected_fps)
    parquet_files = [item for item in parquet.get("files", []) if isinstance(item, dict)]
    block_reasons: list[str] = []
    review_reasons: list[str] = []
    records = []
    decoded_frame_count = 0
    expected_count = len(specs) * len(parquet_files) if specs and parquet_files else 0
    expected_paths: set[str] = set()

    if not specs:
        block_reasons.append("meta/info.json 未声明 video feature，无法确认双目 mp4 是否完整。")

    for spec in specs:
        feature_total = 0
        for parquet_file in parquet_files:
            rows = _as_int(parquet_file.get("rows"))
            key = str(parquet_file.get("key") or "")
            if not key:
                continue
            video_path = dataset_dir / "videos" / str(spec["key"]) / f"{key}.mp4"
            expected_paths.add(str(video_path))
            record = _inspect_video_file(video_path, dataset_dir, spec, rows)
            records.append(record)
            if record.get("frame_count") is not None:
                frame_count = int(record.get("frame_count") or 0)
                decoded_frame_count += frame_count
                feature_total += frame_count
            block_reasons.extend(record.get("block_reasons") or [])
            review_reasons.extend(record.get("review_reasons") or [])
        spec["observed_total_frames"] = feature_total
        if expected_frames and feature_total and feature_total != expected_frames:
            block_reasons.append(f"{spec['key']} mp4 总帧数 {feature_total} 与 meta/job frames {expected_frames} 不一致。")

    actual_video_files = sorted((dataset_dir / "videos").glob("*/*/*.mp4"))
    extras = [path for path in actual_video_files if str(path) not in expected_paths]
    if specs and parquet_files and extras:
        review_reasons.append(f"发现 {len(extras)} 个未被 data parquet 索引的额外 mp4，建议确认是否为历史残留。")
    if specs and parquet_files:
        missing = [record for record in records if record.get("missing")]
        if missing:
            block_reasons.append(f"缺少 {len(missing)} 个期望 mp4。")
    elif not actual_video_files:
        block_reasons.append("缺少 videos/ 下的 mp4 文件。")

    if cv2 is None and actual_video_files:
        review_reasons.append("当前环境没有 OpenCV，无法打开 mp4 核对帧数、FPS、分辨率和首帧。")
    frame_check = "match" if not any(record.get("frame_mismatch") for record in records) and not block_reasons else "failed"
    fps_check = "match" if not any(record.get("fps_mismatch") for record in records) and not block_reasons else "failed"
    resolution_check = "match" if not any(record.get("resolution_mismatch") for record in records) and not block_reasons else "failed"
    if cv2 is None and actual_video_files:
        frame_check = fps_check = resolution_check = "unknown"

    return {
        "features": specs,
        "files": records,
        "extra_files": [_relative_path(path, dataset_dir) for path in extras],
        "video_file_count": len(actual_video_files),
        "expected_video_file_count": expected_count,
        "decoded_frame_count": decoded_frame_count,
        "frame_check": frame_check,
        "fps_check": fps_check,
        "resolution_check": resolution_check,
        "total_size_bytes": video_total_size,
        "total_size_text": _format_bytes(video_total_size),
        "block_reasons": _dedupe_strings(block_reasons),
        "review_reasons": _dedupe_strings(review_reasons),
    }


def _video_feature_specs(dataset_dir: Path, info: dict[str, Any], inspect: dict[str, Any], fallback_fps: float | None) -> list[dict[str, Any]]:
    specs: list[dict[str, Any]] = []
    features = info.get("features") if isinstance(info.get("features"), dict) else {}
    for key, meta in features.items():
        if not isinstance(meta, dict) or meta.get("dtype") != "video":
            continue
        shape = meta.get("shape") if isinstance(meta.get("shape"), list) else []
        video_info = meta.get("video_info") if isinstance(meta.get("video_info"), dict) else {}
        specs.append(
            {
                "key": str(key),
                "expected_height": _as_int(shape[0]) if len(shape) >= 1 else None,
                "expected_width": _as_int(shape[1]) if len(shape) >= 2 else None,
                "expected_fps": _as_float(video_info.get("video.fps") or meta.get("fps") or fallback_fps),
                "codec": video_info.get("video.codec"),
            }
        )
    actual_dirs = [path for path in sorted((dataset_dir / "videos").iterdir()) if path.is_dir()] if (dataset_dir / "videos").exists() else []
    known = {spec["key"] for spec in specs}
    for path in actual_dirs:
        if path.name in known:
            continue
        specs.append({"key": path.name, "expected_height": None, "expected_width": None, "expected_fps": fallback_fps, "codec": None})
    if specs:
        return specs

    cameras = inspect.get("cameras") if isinstance(inspect.get("cameras"), dict) else {}
    fallback_keys = []
    if "left" in cameras:
        fallback_keys.append("observation.images.left")
    if "right" in cameras:
        fallback_keys.append("observation.images.right")
    return [{"key": key, "expected_height": None, "expected_width": None, "expected_fps": fallback_fps, "codec": None} for key in fallback_keys]


def _inspect_video_file(path: Path, dataset_dir: Path, spec: dict[str, Any], expected_frames: int | None) -> dict[str, Any]:
    relative = _relative_path(path, dataset_dir)
    record: dict[str, Any] = {
        "path": str(path),
        "relative_path": relative,
        "video_key": spec.get("key"),
        "expected_frames": expected_frames,
        "expected_fps": spec.get("expected_fps"),
        "expected_width": spec.get("expected_width"),
        "expected_height": spec.get("expected_height"),
        "exists": path.exists(),
        "missing": False,
        "size_bytes": 0,
        "size_text": "-",
        "frame_count": None,
        "fps": None,
        "width": None,
        "height": None,
        "first_frame_mean": None,
        "first_frame_std": None,
        "block_reasons": [],
        "review_reasons": [],
    }
    if not path.exists():
        record["missing"] = True
        record["block_reasons"].append(f"缺少视频文件 {relative}。")
        return record
    record["size_bytes"] = path.stat().st_size
    record["size_text"] = _format_bytes(int(record["size_bytes"]))
    if cv2 is None:
        record["review_reasons"].append(f"{relative} 未做 OpenCV 打开校验。")
        return record

    capture = cv2.VideoCapture(str(path))
    try:
        if not capture.isOpened():
            record["block_reasons"].append(f"{relative} 无法被 OpenCV 打开。")
            return record
        frame_count = int(round(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0))
        fps = float(capture.get(cv2.CAP_PROP_FPS) or 0.0)
        width = int(round(capture.get(cv2.CAP_PROP_FRAME_WIDTH) or 0))
        height = int(round(capture.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0))
        ok, frame = capture.read()
    finally:
        capture.release()

    record.update({"frame_count": frame_count, "fps": fps, "width": width, "height": height})
    if expected_frames is not None and frame_count != expected_frames:
        record["frame_mismatch"] = True
        record["block_reasons"].append(f"{relative} 帧数 {frame_count} 与对应 parquet 行数 {expected_frames} 不一致。")
    expected_fps = _as_float(spec.get("expected_fps"))
    if expected_fps is not None and (fps <= 0 or abs(fps - expected_fps) > 0.5):
        record["fps_mismatch"] = True
        record["block_reasons"].append(f"{relative} FPS {fps:.2f} 与期望 {expected_fps:.2f} 不一致。")
    expected_width = _as_int(spec.get("expected_width"))
    expected_height = _as_int(spec.get("expected_height"))
    if expected_width and expected_height and (width != expected_width or height != expected_height):
        record["resolution_mismatch"] = True
        record["block_reasons"].append(f"{relative} 分辨率 {width}x{height} 与期望 {expected_width}x{expected_height} 不一致。")
    if not ok or frame is None:
        record["block_reasons"].append(f"{relative} 首帧无法读取。")
        return record
    mean = float(frame.mean())
    std = float(frame.std())
    record["first_frame_mean"] = mean
    record["first_frame_std"] = std
    if mean < 2.0 or mean > 253.0 or std < 1.0:
        record["review_reasons"].append(f"{relative} 首帧疑似黑屏、白屏或近似纯色。")
    return record


def _path_size(path: Path) -> int:
    try:
        if path.is_file():
            return path.stat().st_size
        if path.is_dir():
            total = 0
            for item in path.rglob("*"):
                try:
                    if item.is_file():
                        total += item.stat().st_size
                except OSError:
                    continue
            return total
    except OSError:
        return 0
    return 0


def _format_bytes(size: int | float | None) -> str:
    if size is None:
        return "-"
    value = float(size)
    if value <= 0:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB"]
    index = 0
    while value >= 1024 and index < len(units) - 1:
        value /= 1024
        index += 1
    if index == 0:
        return f"{int(value)} B"
    return f"{value:.1f} {units[index]}"


def _chunk_file_key(path: Path) -> str:
    if len(path.parts) >= 2:
        return f"{path.parent.name}/{path.stem}"
    return path.stem


def _relative_path(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _dedupe_strings(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def _action_saturation_summary(dataset_dir: Path, action_dimensions: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    if pq is None:
        return {"available": False, "reason": "pyarrow unavailable", "episodes": [], "top_dimensions": []}
    dimensions_meta = action_dimensions or ACTION_DIMENSIONS
    parquet_files = sorted((dataset_dir / "data").glob("chunk-*/*.parquet"))
    grouped: dict[int, list[list[float]]] = {}
    for path in parquet_files:
        try:
            table = pq.read_table(path, columns=["episode_index", "action"])
        except Exception:
            continue
        data = table.to_pydict()
        episodes = data.get("episode_index") or []
        actions = data.get("action") or []
        for episode_index, action in zip(episodes, actions):
            if not isinstance(action, list):
                continue
            grouped.setdefault(int(episode_index), []).append([float(value) for value in action])

    episode_results = []
    global_dim_rates: dict[int, list[float]] = {int(item["index"]): [] for item in dimensions_meta}
    for episode_index, actions in sorted(grouped.items()):
        result = _episode_saturation(episode_index, actions, dimensions_meta)
        episode_results.append(result)
        for dim in result["dimensions"]:
            global_dim_rates[int(dim["index"])].append(float(dim["saturation_rate"]))

    top_dimensions = []
    for dim in dimensions_meta:
        rates = global_dim_rates[int(dim["index"])]
        if not rates:
            continue
        rate = statistics.mean(rates)
        if rate <= 0.05:
            continue
        top_dimensions.append({**dim, "saturation_rate": rate})
    top_dimensions.sort(key=lambda item: item["saturation_rate"], reverse=True)
    return {
        "available": True,
        "note": "按 Forge 逻辑复算：每个 action 维度在自身观测 min/max 的 5% 边缘内即算贴边；这不是硬件物理限位证明。",
        "episodes": episode_results,
        "top_dimensions": top_dimensions[:8],
    }


def _episode_saturation(
    episode_index: int,
    actions: list[list[float]],
    action_dimensions: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if not actions:
        return {"episode_id": f"episode_{episode_index:06d}", "episode_index": episode_index, "overall_saturation": 0.0, "dimensions": [], "top_dimensions": []}
    dimensions_meta = action_dimensions or ACTION_DIMENSIONS
    dim_count = min(len(actions[0]), len(dimensions_meta))
    dimensions = []
    valid_rates = []
    for dim_index in range(dim_count):
        values = [row[dim_index] for row in actions if len(row) > dim_index and math.isfinite(row[dim_index])]
        if not values:
            rate = 0.0
            valid = False
        else:
            mn = min(values)
            mx = max(values)
            span = mx - mn
            valid = span > 1e-10
            if valid:
                margin = 0.05 * span
                saturated = sum(1 for value in values if value <= mn + margin or value >= mx - margin)
                rate = saturated / len(values)
                valid_rates.append(rate)
            else:
                rate = 0.0
        dim_meta = dimensions_meta[dim_index]
        dimensions.append({**dim_meta, "saturation_rate": rate, "valid": valid})
    top = [item for item in dimensions if item["saturation_rate"] > 0.05]
    top.sort(key=lambda item: item["saturation_rate"], reverse=True)
    overall = statistics.mean(valid_rates) if valid_rates else 0.0
    return {
        "episode_id": f"episode_{episode_index:06d}",
        "episode_index": episode_index,
        "overall_saturation": overall,
        "dimensions": dimensions,
        "top_dimensions": top[:6],
    }


def _episode_risks(quality: dict[str, Any], saturation: dict[str, Any]) -> list[dict[str, Any]]:
    sat_by_episode = {
        item.get("episode_id"): item
        for item in saturation.get("episodes", [])
        if isinstance(item, dict)
    }
    rows = []
    for ep in quality.get("per_episode") or []:
        if not isinstance(ep, dict):
            continue
        episode_id = str(ep.get("episode_id") or "")
        sat = sat_by_episode.get(episode_id, {})
        flags = ep.get("flags") if isinstance(ep.get("flags"), list) else []
        reasons = []
        if "saturated" in flags or (_as_float(ep.get("overall_saturation")) or 0.0) > 0.30:
            reasons.append("动作贴边")
        if "jerky" in flags or (_as_float(ep.get("ldlj")) or 0.0) < -25:
            reasons.append("动作抖动")
        if "gripper_chatter" in flags:
            reasons.append("夹爪抖动")
        if not reasons and (_as_float(ep.get("overall_score")) or 10.0) < 7.0:
            reasons.append("分数偏低")
        rows.append(
            {
                "episode_id": episode_id,
                "num_frames": ep.get("num_frames"),
                "overall_score": ep.get("overall_score"),
                "flags": flags,
                "overall_saturation": ep.get("overall_saturation"),
                "ldlj": ep.get("ldlj"),
                "gripper_chatter_rate": ep.get("gripper_chatter_rate"),
                "top_saturated_dimensions": sat.get("top_dimensions", []),
                "review_hint": "、".join(reasons) if reasons else "无明显复查点",
            }
        )
    return rows
