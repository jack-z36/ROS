"""Runtime orchestration for the five-metric dataset quality report."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
from typing import Any

from repo.quality_report_repository import QualityReportRepository
from schemas.quality import (
    QUALITY_POLICY_VERSION,
    QUALITY_REPORT_VERSION,
    DatasetQualityReportV2,
)
from service.quality_evidence import QualityEvidenceCollector
from service.quality_evaluators import QUALITY_THRESHOLDS, evaluate_quality_metrics


class DatasetQualityPipelineError(RuntimeError):
    pass


class DatasetQualityPipeline:
    def __init__(
        self,
        *,
        dataset_dir: str | Path,
        reports_dir: str | Path,
        fps: float,
        job: dict[str, Any] | None = None,
        forge_executable: str | Path | None = None,
    ) -> None:
        self.dataset_dir = Path(dataset_dir).expanduser().resolve()
        self.reports_dir = Path(reports_dir).expanduser().resolve()
        self.fps = float(fps)
        self.job = job or {}
        configured = Path(forge_executable).expanduser() if forge_executable else None
        self.forge = str(configured) if configured and configured.exists() else shutil.which("forge")
        self.repository = QualityReportRepository(self.reports_dir)

    def run(self) -> dict[str, Any]:
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        forge = self._run_forge()
        context = QualityEvidenceCollector(
            dataset_dir=self.dataset_dir,
            reports_dir=self.reports_dir,
            job=self.job,
        ).collect()
        if context.contract is not None:
            _atomic_json(self.reports_dir / "feature_contract.json", context.contract)
        metrics = evaluate_quality_metrics(context)
        decision = _decision(metrics)
        report = DatasetQualityReportV2(
            decision=decision,
            summary=_summary(decision, metrics),
            metrics=metrics,
            contract_fingerprint=context.contract_fingerprint or self.job.get("contract_fingerprint"),
            dataset_dir=str(self.dataset_dir),
            thresholds=dict(QUALITY_THRESHOLDS),
            generated_at=datetime.now(timezone.utc).isoformat(),
        )
        path = self.repository.write(report)
        result = report.to_dict()
        result.update(
            {
                "report_path": str(path),
                "trace_index_path": str(self.repository.trace_index_path),
                "feature_contract_path": str(self.reports_dir / "feature_contract.json") if context.contract is not None else None,
                "forge": forge,
                "evidence_sources": context.sources,
                "missing_evidence": sorted(context.missing_sources),
            }
        )
        inspect_data = _read_json(self.reports_dir / "forge_inspect.json", {})
        quality_data = _read_json(self.reports_dir / "forge_quality.json", {})
        flagged_data = _read_json(self.reports_dir / "forge_quality_flagged.json", [])
        result.update(
            {
                "inspect_report": str(self.reports_dir / "forge_inspect.json"),
                "quality_report": str(self.reports_dir / "forge_quality.json"),
                "flagged_report": str(self.reports_dir / "forge_quality_flagged.json"),
                "num_episodes": inspect_data.get("num_episodes") if isinstance(inspect_data, dict) else None,
                "total_frames": inspect_data.get("total_frames") if isinstance(inspect_data, dict) else None,
                "format": inspect_data.get("format") if isinstance(inspect_data, dict) else None,
                "overall_score": quality_data.get("overall_score") if isinstance(quality_data, dict) else None,
                "subscores": quality_data.get("subscores", {}) if isinstance(quality_data, dict) else {},
                "per_episode": quality_data.get("per_episode", []) if isinstance(quality_data, dict) else [],
                "flags": quality_data.get("flags", []) if isinstance(quality_data, dict) else [],
                "flagged_count": len(flagged_data) if isinstance(flagged_data, list) else 0,
                "warnings": [forge.get("error")] if forge.get("error") else [],
            }
        )
        _atomic_json(self.reports_dir / "quality_visual_summary.json", result)
        return result

    def _run_forge(self) -> dict[str, Any]:
        inspect_path = self.reports_dir / "forge_inspect.json"
        quality_path = self.reports_dir / "forge_quality.json"
        flagged_path = self.reports_dir / "forge_quality_flagged.json"
        if not self.forge:
            message = "forge executable not found"
            _atomic_json(inspect_path, {"status": "unavailable", "error": message})
            _atomic_json(quality_path, {"status": "unavailable", "error": message})
            _atomic_json(flagged_path, [])
            return {"status": "unavailable", "error": message}
        inspect_proc = subprocess.run(
            [self.forge, "inspect", str(self.dataset_dir), "--output", "json", "--deep"],
            text=True, capture_output=True, check=False,
            env={**os.environ, "COLUMNS": "100000"},
        )
        _write_process_json(inspect_path, inspect_proc)
        quality_proc = subprocess.run(
            [self.forge, "quality", str(self.dataset_dir), "--fps", str(self.fps),
             "--export", str(quality_path), "--export-flagged", str(flagged_path)],
            text=True, capture_output=True, check=False,
        )
        if not quality_path.exists():
            _write_process_json(quality_path, quality_proc)
        if not flagged_path.exists():
            _atomic_json(flagged_path, [])
        return {
            "status": "success" if inspect_proc.returncode == 0 and quality_proc.returncode == 0 else "warn",
            "inspect_returncode": inspect_proc.returncode,
            "quality_returncode": quality_proc.returncode,
            "inspect_path": str(inspect_path),
            "quality_path": str(quality_path),
            "flagged_path": str(flagged_path),
            "stderr": (inspect_proc.stderr + quality_proc.stderr)[-8000:],
        }


def run_dataset_quality_pipeline(**kwargs: Any) -> dict[str, Any]:
    return DatasetQualityPipeline(**kwargs).run()


def _decision(metrics: tuple[Any, ...]) -> str:
    hard = metrics[:3]
    if any(item.status == "fail" for item in hard):
        return "block"
    if any(item.status in {"warn", "fail"} or not item.evidence_completeness.complete for item in metrics):
        return "review"
    return "ready"


def _summary(decision: str, metrics: tuple[Any, ...]) -> str:
    if decision == "ready":
        return "五项数据质量指标全部通过，可进入训练前复查。"
    failed = [item.metric_id for item in metrics if item.status == "fail"]
    warned = [item.metric_id for item in metrics if item.status == "warn"]
    if failed:
        return "硬门禁指标失败：" + ", ".join(failed) + "。"
    return "证据不完整或存在复查项：" + ", ".join(warned) + "。"


def _write_process_json(path: Path, process: subprocess.CompletedProcess[str]) -> None:
    text = process.stdout.strip() or process.stderr.strip()
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        value = {"status": "failed", "returncode": process.returncode, "output": text}
    _atomic_json(path, value)


def _atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def _read_json(path: Path, fallback: Any) -> Any:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return fallback
    return value
