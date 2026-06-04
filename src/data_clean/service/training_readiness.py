"""Training-readiness interpretation for LeRobot quality reports."""

from __future__ import annotations

import json
import math
import statistics
from pathlib import Path
from typing import Any

try:  # pyarrow is available in the data-clean environment, but keep reports robust.
    import pyarrow.parquet as pq
except Exception:  # pragma: no cover - environment fallback
    pq = None  # type: ignore[assignment]


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
    action_saturation = _action_saturation_summary(dataset_path)
    alignment = _alignment_summary(job)
    gripper = _gripper_tactile_summary(job, alignment)
    bridge = _bridge_summary(job)

    modules = [
        _format_module(job, quality_context, inspect_data, bridge),
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
        "action_dimension_labels": ACTION_DIMENSIONS,
        "action_saturation": action_saturation,
        "episode_risks": episode_risks,
        "alignment_summary": alignment,
        "gripper_summary": gripper,
        "bridge_summary": bridge,
        "subscore_explanations": SUBSCORE_EXPLANATIONS,
        "format_details": _format_details(quality_context, inspect_data, stats_data, flagged_data),
        "report_path": str(report_path),
    }
    _write_json_atomic(report_path, summary)
    return summary


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
        issues.append("生产标定未就绪，arm-base TCP 位姿不可作为正式训练输入。")

    state_dim = _shape_dim(inspect.get("observation_schema", {}).get("observation.state")) or _as_int((job.get("dataset_summary") or {}).get("state_dim"))
    action_dim = _shape_dim(inspect.get("action_schema")) or _as_int((job.get("dataset_summary") or {}).get("action_dim"))
    if state_dim != 32:
        issues.append(f"observation.state 维度不是 32，当前为 {state_dim or '-'}。")
    if action_dim != 16:
        issues.append(f"action 维度不是 16，当前为 {action_dim or '-'}。")

    status = "block" if issues else "pass"
    summary = "格式、formal 标定、双目图像、state/action 维度均满足当前训练输入契约。" if not issues else issues[0]
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
    for module_id in ("format_input", "action_health", "sync_quality", "gripper_tactile"):
        module = next((item for item in modules if item["id"] == module_id), None)
        if module:
            risks.extend(module.get("risks", []))
    return risks[:3] or ["未发现会阻止训练输入的技术风险。"]


def _next_actions(modules: list[dict[str, Any]]) -> list[str]:
    by_id = {module["id"]: module for module in modules}
    actions: list[str] = []
    if by_id.get("format_input", {}).get("status") == "block":
        actions.append("先修复格式、formal 标定或 training_eligible 问题，再重新生成 dataset。")
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


def _bridge_summary(job: dict[str, Any]) -> dict[str, Any]:
    files = job.get("files") if isinstance(job.get("files"), list) else []
    reports = []
    training_values = []
    dropped = 0
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
    return {
        "bridge_count": len(reports),
        "all_training_eligible": all(training_values) if training_values else True,
        "training_eligible_values": training_values,
        "terminal_dropped_steps": dropped,
        "modes": sorted({str(report.get("mode")) for report in reports if report.get("mode")}),
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


def _action_saturation_summary(dataset_dir: Path) -> dict[str, Any]:
    if pq is None:
        return {"available": False, "reason": "pyarrow unavailable", "episodes": [], "top_dimensions": []}
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
    global_dim_rates: dict[int, list[float]] = {item["index"]: [] for item in ACTION_DIMENSIONS}
    for episode_index, actions in sorted(grouped.items()):
        result = _episode_saturation(episode_index, actions)
        episode_results.append(result)
        for dim in result["dimensions"]:
            global_dim_rates[int(dim["index"])].append(float(dim["saturation_rate"]))

    top_dimensions = []
    for dim in ACTION_DIMENSIONS:
        rates = global_dim_rates[dim["index"]]
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


def _episode_saturation(episode_index: int, actions: list[list[float]]) -> dict[str, Any]:
    if not actions:
        return {"episode_id": f"episode_{episode_index:06d}", "episode_index": episode_index, "overall_saturation": 0.0, "dimensions": [], "top_dimensions": []}
    dim_count = min(len(actions[0]), len(ACTION_DIMENSIONS))
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
        dim_meta = ACTION_DIMENSIONS[dim_index]
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
