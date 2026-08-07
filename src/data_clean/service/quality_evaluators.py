"""The five independent v2 quality evaluators."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from schemas.quality import (
    QUALITY_METRIC_IDS,
    QUALITY_POLICY_VERSION,
    QualityEvidenceCompleteness,
    QualityEvidenceContext,
    QualityMetricResult,
    QualityStatus,
)


QUALITY_THRESHOLDS = {
    "temporal_warn_ms": 33.4,
    "temporal_fail_ms": 100.0,
    "trajectory_warn_flagged_ratio": 0.10,
    "learnability_warn_saturation_ratio": 0.20,
    "learnability_fail_saturation_ratio": 0.50,
}


class QualityEvaluator(Protocol):
    metric_id: str

    def evaluate(self, context: QualityEvidenceContext) -> QualityMetricResult: ...


@dataclass(frozen=True)
class _BaseEvaluator:
    metric_id: str
    required_sources: tuple[str, ...]

    def completeness(self, context: QualityEvidenceContext) -> QualityEvidenceCompleteness:
        available = tuple(source for source in self.required_sources if context.has(source))
        missing = tuple(source for source in self.required_sources if not context.has(source))
        return QualityEvidenceCompleteness(
            complete=not missing,
            required_sources=self.required_sources,
            available_sources=available,
            missing_sources=missing,
        )

    def result(
        self,
        context: QualityEvidenceContext,
        *,
        status: QualityStatus,
        score: float | None,
        rationale: str,
        summary: str,
        impact_scope: tuple[str, ...],
        training_impact: tuple[str, ...],
        remediation: tuple[str, ...],
        traces: tuple[Any, ...] = (),
    ) -> QualityMetricResult:
        return QualityMetricResult(
            metric_id=self.metric_id,
            status=status.value,
            score=score,
            rationale=rationale,
            summary=summary,
            impact_scope=impact_scope,
            training_impact=training_impact,
            remediation=remediation,
            traces=traces,
            evidence_completeness=self.completeness(context),
            contract_fingerprint=context.contract_fingerprint,
            policy_version=QUALITY_POLICY_VERSION,
        )


class FieldSemanticConsistencyEvaluator:
    metric_id = QUALITY_METRIC_IDS[0]

    def evaluate(self, context: QualityEvidenceContext) -> QualityMetricResult:
        base = _BaseEvaluator(self.metric_id, ("feature_contract", "dataset_info"))
        contract = context.contract
        info = context.evidence.get("dataset_info")
        if not contract or not isinstance(info, dict):
            return base.result(
                context, status=QualityStatus.WARN, score=None,
                rationale="feature contract 或最终 dataset info 缺失，无法完成字段语义闭环。",
                summary="字段语义证据不完整，需要复查。",
                impact_scope=("feature schema",), training_impact=("无法确认训练输入字段与 Bridge 语义一致。",),
                remediation=("保留并发布 feature_contract.json，重新运行格式门禁。",),
                traces=(context.trace("feature_contract"), context.trace("dataset_info")),
            )
        state = contract.get("observation.state") or contract.get("state") or {}
        action = contract.get("action") or {}
        features = info.get("features") if isinstance(info.get("features"), dict) else {}
        mismatches: list[str] = []
        for key, layout in (("observation.state", state), ("action", action)):
            actual = features.get(key) if isinstance(features, dict) else None
            if not isinstance(actual, dict):
                mismatches.append(f"{key} missing")
                continue
            if list(actual.get("shape", [])) != list(layout.get("shape", [])):
                mismatches.append(f"{key} shape")
            if list(actual.get("names", [])) != list(layout.get("names", [])):
                mismatches.append(f"{key} names")
        if mismatches:
            return base.result(
                context, status=QualityStatus.FAIL, score=0.0,
                rationale="最终 dataset 的 feature metadata 与 compiled contract 不一致：" + ", ".join(mismatches),
                summary="字段名称、顺序或 shape 与契约不一致。",
                impact_scope=("observation.state", "action"), training_impact=("训练侧可能读取错误字段或错误 shape。",),
                remediation=("使用同一 compiled contract 重新执行 Bridge 和官方导出。",),
                traces=(context.trace("feature_contract"), context.trace("dataset_info")),
            )
        return base.result(
            context, status=QualityStatus.PASS, score=1.0,
            rationale="dataset metadata 的 state/action names 与 shape 均匹配 compiled contract。",
            summary="字段语义和输出 metadata 一致。", impact_scope=("feature schema",),
            training_impact=("训练输入字段可按当前 contract 解释。",), remediation=(),
            traces=(context.trace("feature_contract"), context.trace("dataset_info")),
        )


class MultimodalTemporalConsistencyEvaluator:
    metric_id = QUALITY_METRIC_IDS[1]

    def evaluate(self, context: QualityEvidenceContext) -> QualityMetricResult:
        base = _BaseEvaluator(self.metric_id, ("alignment_report", "dataset_info"))
        report = context.evidence.get("alignment_report")
        if not isinstance(report, dict) or not context.has("dataset_info"):
            return base.result(
                context, status=QualityStatus.WARN, score=None,
                rationale="alignment report 或 dataset info 缺失。", summary="多模态时间一致性证据不完整。",
                impact_scope=("images", "pose", "gripper", "tactile"),
                training_impact=("时间错位可能使视觉与动作配对错误。",),
                remediation=("重新生成 Scene3 alignment report 并补齐最终 dataset metadata。",),
                traces=(context.trace("alignment_report"), context.trace("dataset_info")),
            )
        max_dt = _first_number(report, ("max_dt_ms", "max_time_error_ms", "max_abs_dt_ms"))
        if max_dt is not None and max_dt > QUALITY_THRESHOLDS["temporal_fail_ms"]:
            status, score = QualityStatus.FAIL, 0.0
        elif max_dt is not None and max_dt > QUALITY_THRESHOLDS["temporal_warn_ms"]:
            status, score = QualityStatus.WARN, 0.5
        else:
            status, score = QualityStatus.PASS, 1.0
        return base.result(
            context, status=status, score=score,
            rationale=f"alignment report maximum time error={max_dt if max_dt is not None else 'not reported'} ms。",
            summary="多模态时间轴通过阈值检查。" if status == QualityStatus.PASS else "多模态时间误差需要复查。",
            impact_scope=("episode step alignment",),
            training_impact=("时间误差会影响视觉-状态-动作配对。",),
            remediation=("检查 Scene3 时间域选择、fallback 和缺失 step。",) if status != QualityStatus.PASS else (),
            traces=(context.trace("alignment_report"),),
        )


class ActionCausalConsistencyEvaluator:
    metric_id = QUALITY_METRIC_IDS[2]

    def evaluate(self, context: QualityEvidenceContext) -> QualityMetricResult:
        base = _BaseEvaluator(self.metric_id, ("bridge_lineage",))
        records = context.evidence.get("bridge_lineage")
        if not isinstance(records, list) or not records:
            return base.result(
                context, status=QualityStatus.WARN, score=None,
                rationale="Bridge lineage 缺失，无法证明 action 来源于同一 episode 的未来 step。",
                summary="动作因果 lineage 不完整。", impact_scope=("action",),
                training_impact=("无法确认 action 是 t+1 绝对目标；训练前需要人工复查。",),
                remediation=("重新生成带 lineage.jsonl 的 Bridge。",),
                traces=(context.trace("bridge_lineage"),),
            )
        errors: list[str] = []
        for record in records:
            state = _int(record.get("state_timestamp_ns"))
            action = _int(record.get("action_source_timestamp_ns"))
            relation = record.get("action_relation")
            state_step = _int(record.get("step_index"))
            action_step = _int(record.get("action_source_step_index"))
            if relation != "t+1" or (state is not None and action is not None and action <= state):
                errors.append("action source is not a future t+1 sample")
            if state_step is not None and action_step is not None and action_step != state_step + 1:
                errors.append("action source step index is not state step + 1")
            if record.get("episode_index") is None:
                errors.append("episode index missing")
        if errors:
            return base.result(
                context, status=QualityStatus.FAIL, score=0.0,
                rationale="；".join(sorted(set(errors))), summary="动作存在错误未来索引或跨 episode 因果关系。",
                impact_scope=("action", "episode boundary"),
                training_impact=("动作监督可能泄漏未来错误帧或跨 episode。",),
                remediation=("丢弃错误 bridge，按同 episode t+1 规则重建并复验 lineage。",),
                traces=(context.trace("bridge_lineage"),),
            )
        return base.result(
            context, status=QualityStatus.PASS, score=1.0,
            rationale=f"验证 {len(records)} 条 lineage 均满足同 episode t+1 关系。",
            summary="动作因果关系通过。", impact_scope=("action",),
            training_impact=("action 可解释为当前 step 的下一 step 绝对目标。",), remediation=(),
            traces=(context.trace("bridge_lineage"),),
        )


class TrajectoryFidelityEvaluator:
    metric_id = QUALITY_METRIC_IDS[3]

    def evaluate(self, context: QualityEvidenceContext) -> QualityMetricResult:
        base = _BaseEvaluator(self.metric_id, ("forge_quality",))
        quality = context.evidence.get("forge_quality")
        if not isinstance(quality, dict):
            return base.result(
                context, status=QualityStatus.WARN, score=None,
                rationale="Forge quality evidence 缺失。", summary="轨迹保真度缺少底层质量证据。",
                impact_scope=("trajectory",), training_impact=("无法判断滤波、修复和动作轨迹是否变形。",),
                remediation=("运行 Forge quality，并保留 Scene2 filter report 作为来源。",),
                traces=(context.trace("forge_quality"),),
            )
        flagged = quality.get("per_episode") if isinstance(quality.get("per_episode"), list) else []
        flags = quality.get("flags") if isinstance(quality.get("flags"), list) else []
        episodes = max(1, _int(quality.get("num_episodes")) or len(flagged) or 1)
        flagged_count = len([item for item in flagged if isinstance(item, dict) and item.get("flags")])
        flagged_count = max(flagged_count, len(flags) if flags else 0)
        ratio = flagged_count / episodes
        status = QualityStatus.WARN if ratio > QUALITY_THRESHOLDS["trajectory_warn_flagged_ratio"] else QualityStatus.PASS
        return base.result(
            context, status=status, score=max(0.0, 1.0 - ratio),
            rationale=f"Forge flagged episode ratio={ratio:.3f}。", summary="轨迹质量需要复查。" if status != QualityStatus.PASS else "轨迹保真度未发现超阈值风险。",
            impact_scope=("trajectory",), training_impact=("滤波或修复造成的轨迹变形会降低动作监督质量。",),
            remediation=("对 flagged episode 回看 Scene2 修复/滤波报告和原始轨迹。",) if status != QualityStatus.PASS else (),
            traces=(context.trace("forge_quality"), context.trace("forge_flagged")),
        )


class ActionLearnabilityEvaluator:
    metric_id = QUALITY_METRIC_IDS[4]

    def evaluate(self, context: QualityEvidenceContext) -> QualityMetricResult:
        base = _BaseEvaluator(self.metric_id, ("forge_quality", "dataset_info"))
        quality = context.evidence.get("forge_quality")
        if not isinstance(quality, dict) or not context.has("dataset_info"):
            return base.result(
                context, status=QualityStatus.WARN, score=None,
                rationale="动作质量或 dataset info 缺失。", summary="动作可学习性证据不完整。",
                impact_scope=("action", "dataset scale"), training_impact=("无法确认动作幅度、饱和度和样本规模是否适合训练。",),
                remediation=("补齐 Forge quality、最终 dataset info 和动作统计。",),
                traces=(context.trace("forge_quality"), context.trace("dataset_info")),
            )
        saturation = _first_number(quality, ("action_saturation_ratio", "saturation_ratio", "action_clip_ratio"))
        if saturation is None:
            return base.result(
                context, status=QualityStatus.WARN, score=None,
                rationale="Forge quality 未提供固定动作饱和度指标。", summary="动作可学习性需要人工复查。",
                impact_scope=("action",), training_impact=("动作退化或贴边风险未被量化。",),
                remediation=("增加动作统计或检查动作分布与夹爪边界。",),
                traces=(context.trace("forge_quality"),),
            )
        if saturation >= QUALITY_THRESHOLDS["learnability_fail_saturation_ratio"]:
            status, score = QualityStatus.FAIL, 0.0
        elif saturation >= QUALITY_THRESHOLDS["learnability_warn_saturation_ratio"]:
            status, score = QualityStatus.WARN, 0.5
        else:
            status, score = QualityStatus.PASS, 1.0
        return base.result(
            context, status=status, score=score,
            rationale=f"action saturation ratio={saturation:.3f}。", summary="动作分布存在退化风险。" if status != QualityStatus.PASS else "动作可学习性指标通过。",
            impact_scope=("action",), training_impact=("动作贴边会降低模型可学习性和泛化。",),
            remediation=("检查动作裁剪、单位和数据集覆盖范围。",) if status != QualityStatus.PASS else (),
            traces=(context.trace("forge_quality"),),
        )


def default_quality_evaluators() -> tuple[QualityEvaluator, ...]:
    return (
        FieldSemanticConsistencyEvaluator(),
        MultimodalTemporalConsistencyEvaluator(),
        ActionCausalConsistencyEvaluator(),
        TrajectoryFidelityEvaluator(),
        ActionLearnabilityEvaluator(),
    )


def evaluate_quality_metrics(
    context: QualityEvidenceContext,
    evaluators: tuple[QualityEvaluator, ...] | None = None,
) -> tuple[QualityMetricResult, ...]:
    active = evaluators or default_quality_evaluators()
    if tuple(item.metric_id for item in active) != QUALITY_METRIC_IDS:
        raise ValueError("quality pipeline must execute exactly the five fixed evaluators")
    return tuple(item.evaluate(context) for item in active)


def _int(value: Any) -> int | None:
    try:
        return None if value is None else int(value)
    except (TypeError, ValueError):
        return None


def _first_number(value: Any, keys: tuple[str, ...]) -> float | None:
    if isinstance(value, dict):
        for key in keys:
            candidate = value.get(key)
            if isinstance(candidate, (int, float)):
                return float(candidate)
        for nested in value.values():
            found = _first_number(nested, keys)
            if found is not None:
                return found
    elif isinstance(value, list):
        for nested in value:
            found = _first_number(nested, keys)
            if found is not None:
                return found
    return None
