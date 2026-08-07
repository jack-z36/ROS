"""Stable types for the v2 dataset-quality decision boundary."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any


QUALITY_POLICY_VERSION = "dataset_quality_policy_v1"
QUALITY_REPORT_VERSION = "dataset_quality_report_v2"
QUALITY_METRIC_IDS = (
    "field_semantic_consistency",
    "multimodal_temporal_consistency",
    "action_causal_consistency",
    "trajectory_fidelity",
    "action_learnability",
)


class QualityStatus(StrEnum):
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"


@dataclass(frozen=True)
class QualityTraceRef:
    source: str
    path: str | None = None
    locator: str | None = None
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "path": self.path,
            "locator": self.locator,
            "detail": self.detail,
        }


@dataclass(frozen=True)
class QualityEvidenceCompleteness:
    complete: bool
    required_sources: tuple[str, ...] = ()
    available_sources: tuple[str, ...] = ()
    missing_sources: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "complete": self.complete,
            "required_sources": list(self.required_sources),
            "available_sources": list(self.available_sources),
            "missing_sources": list(self.missing_sources),
        }


@dataclass(frozen=True)
class QualityMetricResult:
    metric_id: str
    status: str
    score: float | None
    rationale: str
    summary: str
    impact_scope: tuple[str, ...] = ()
    training_impact: tuple[str, ...] = ()
    remediation: tuple[str, ...] = ()
    traces: tuple[QualityTraceRef, ...] = ()
    evidence_completeness: QualityEvidenceCompleteness = field(
        default_factory=lambda: QualityEvidenceCompleteness(False)
    )
    contract_fingerprint: str | None = None
    policy_version: str = QUALITY_POLICY_VERSION

    def __post_init__(self) -> None:
        if self.metric_id not in QUALITY_METRIC_IDS:
            raise ValueError(f"unknown quality metric: {self.metric_id}")
        if self.status not in {item.value for item in QualityStatus}:
            raise ValueError(f"invalid quality status: {self.status}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "metric_id": self.metric_id,
            "status": self.status,
            "score": self.score,
            "rationale": self.rationale,
            "summary": self.summary,
            "impact_scope": list(self.impact_scope),
            "training_impact": list(self.training_impact),
            "remediation": list(self.remediation),
            "traces": [item.to_dict() for item in self.traces],
            "evidence_completeness": self.evidence_completeness.to_dict(),
            "contract_fingerprint": self.contract_fingerprint,
            "quality_policy_version": self.policy_version,
        }


@dataclass
class QualityEvidenceContext:
    dataset_dir: Path
    reports_dir: Path
    evidence: dict[str, Any]
    sources: dict[str, str] = field(default_factory=dict)
    missing_sources: set[str] = field(default_factory=set)
    contract: dict[str, Any] | None = None
    contract_fingerprint: str | None = None

    def has(self, source: str) -> bool:
        return source in self.evidence and self.evidence[source] not in (None, {}, [], "")

    def trace(self, source: str, locator: str | None = None, detail: str = "") -> QualityTraceRef:
        return QualityTraceRef(
            source=source,
            path=self.sources.get(source),
            locator=locator,
            detail=detail,
        )


@dataclass(frozen=True)
class DatasetQualityReportV2:
    decision: str
    summary: str
    metrics: tuple[QualityMetricResult, ...]
    contract_fingerprint: str | None
    dataset_dir: str
    report_version: str = QUALITY_REPORT_VERSION
    quality_policy_version: str = QUALITY_POLICY_VERSION
    thresholds: dict[str, Any] = field(default_factory=dict)
    generated_at: str | None = None
    legacy_fallback: bool = False

    def __post_init__(self) -> None:
        ids = tuple(item.metric_id for item in self.metrics)
        if ids != QUALITY_METRIC_IDS:
            raise ValueError(f"quality report must contain exactly {QUALITY_METRIC_IDS}, got {ids}")
        if self.decision not in {"ready", "review", "block"}:
            raise ValueError(f"invalid quality decision: {self.decision}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "report_version": self.report_version,
            "quality_policy_version": self.quality_policy_version,
            "decision": self.decision,
            "summary": self.summary,
            "dataset_dir": self.dataset_dir,
            "contract_fingerprint": self.contract_fingerprint,
            "thresholds": self.thresholds,
            "metrics": [item.to_dict() for item in self.metrics],
            "generated_at": self.generated_at,
            "legacy_fallback": self.legacy_fallback,
        }
