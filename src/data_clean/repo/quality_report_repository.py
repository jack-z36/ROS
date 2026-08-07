"""Durable storage for the v2 quality report and trace index."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from schemas.quality import DatasetQualityReportV2


class QualityReportRepositoryError(RuntimeError):
    pass


class QualityReportRepository:
    def __init__(self, reports_dir: str | Path):
        self.reports_dir = Path(reports_dir).expanduser().resolve()

    @property
    def report_path(self) -> Path:
        return self.reports_dir / "dataset_quality_report_v2.json"

    @property
    def trace_index_path(self) -> Path:
        return self.reports_dir / "quality_trace_index.json"

    def write(self, report: DatasetQualityReportV2 | dict[str, Any]) -> Path:
        payload = report.to_dict() if isinstance(report, DatasetQualityReportV2) else report
        if payload.get("report_version") != "dataset_quality_report_v2":
            raise QualityReportRepositoryError("only dataset_quality_report_v2 may be written")
        _atomic_write(self.report_path, payload)
        traces = {
            "report_version": payload["report_version"],
            "quality_policy_version": payload.get("quality_policy_version"),
            "contract_fingerprint": payload.get("contract_fingerprint"),
            "metrics": {
                metric.get("metric_id"): metric.get("traces", [])
                for metric in payload.get("metrics", [])
                if isinstance(metric, dict)
            },
        }
        _atomic_write(self.trace_index_path, traces)
        return self.report_path

    def read(self) -> dict[str, Any] | None:
        if not self.report_path.is_file():
            return None
        try:
            value = json.loads(self.report_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise QualityReportRepositoryError(f"invalid quality report: {self.report_path}") from exc
        if not isinstance(value, dict):
            raise QualityReportRepositoryError("quality report must be a JSON object")
        return value

    def read_trace_index(self) -> dict[str, Any] | None:
        if not self.trace_index_path.is_file():
            return None
        value = json.loads(self.trace_index_path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else None

    def rewrite_path_prefix(self, old: str | Path, new: str | Path) -> None:
        old_text, new_text = str(Path(old).resolve()), str(Path(new).resolve())
        for path in (self.report_path, self.trace_index_path):
            if not path.is_file():
                continue
            data = json.loads(path.read_text(encoding="utf-8"))
            _atomic_write(path, _replace_prefix(data, old_text, new_text))


def _atomic_write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def _replace_prefix(value: Any, old: str, new: str) -> Any:
    if isinstance(value, dict):
        return {key: _replace_prefix(item, old, new) for key, item in value.items()}
    if isinstance(value, list):
        return [_replace_prefix(item, old, new) for item in value]
    if isinstance(value, str) and (value == old or value.startswith(old + os.sep)):
        return new + value[len(old):]
    return value
