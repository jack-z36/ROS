"""Collect quality evidence without making a quality decision."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from schemas.quality import QualityEvidenceContext


class QualityEvidenceCollector:
    """Map known reports and artifacts into a single in-memory context."""

    def __init__(
        self,
        *,
        dataset_dir: str | Path,
        reports_dir: str | Path,
        job: dict[str, Any] | None = None,
    ) -> None:
        self.dataset_dir = Path(dataset_dir).expanduser().resolve()
        self.reports_dir = Path(reports_dir).expanduser().resolve()
        self.job = job or {}

    def collect(self) -> QualityEvidenceContext:
        evidence: dict[str, Any] = {}
        sources: dict[str, str] = {}
        missing: set[str] = set()

        def load(source: str, path: Path, *, default: Any = None) -> Any:
            if not path.is_file():
                missing.add(source)
                return default
            try:
                value = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                missing.add(source)
                return default
            evidence[source] = value
            sources[source] = str(path)
            missing.discard(source)
            return value

        for name, filename in (
            ("forge_inspect", "forge_inspect.json"),
            ("forge_quality", "forge_quality.json"),
            ("forge_flagged", "forge_quality_flagged.json"),
            ("alignment_report", "alignment_report.json"),
            ("scene1_report", "scene1_report.json"),
            ("scene2_detection", "scene2_detection_report.json"),
            ("scene2_repair", "scene2_repair_report.json"),
            ("scene2_filter", "scene2_filter_report.json"),
            ("official_compatibility", "official_compatibility.json"),
        ):
            load(name, self.reports_dir / filename)

        for source, patterns in (
            ("cleaned_mcap", ("*cleaned*.mcap", "01_cleaned/**/*.mcap")),
            ("mcap_a", ("*mcap_a*.mcap", "02_mcap_a/**/*.mcap")),
            ("aligned_mcap", ("*aligned*.mcap", "03_aligned/**/*.mcap")),
            ("forge_ready_mcap", ("forge_ready.mcap", "04_forge_bridge/**/forge_ready.mcap")),
        ):
            candidates: list[Path] = []
            for pattern in patterns:
                candidates.extend(self.reports_dir.glob(pattern))
            if candidates:
                path = sorted({item.resolve() for item in candidates if item.is_file()})[0]
                evidence[source] = {"path": str(path)}
                sources[source] = str(path)
            else:
                missing.add(source)

        for source, pattern in (
            ("bridge_schema", "**/forge_bridge_schema.json"),
            ("bridge_report", "**/forge_bridge_report.json"),
            ("bridge_topic_config", "**/forge_topic_config.yaml"),
        ):
            candidates = sorted(path for path in self.reports_dir.glob(pattern) if path.is_file())
            if candidates:
                if path_value := _read_json(candidates[0]):
                    evidence[source] = path_value
                    sources[source] = str(candidates[0])
                else:
                    missing.add(source)
            else:
                missing.add(source)

        contract_path = self.dataset_dir / "meta/feature_contract.json"
        contract = load("feature_contract", contract_path)
        if contract is None:
            contract = self.job.get("feature_contract")
            if isinstance(contract, dict):
                evidence["feature_contract"] = contract
                sources["feature_contract"] = "job.feature_contract"
                missing.discard("feature_contract")
            else:
                sidecars = sorted(self.reports_dir.rglob("feature_contract.json"))
                if sidecars:
                    contract = load("feature_contract", sidecars[0])
        if isinstance(contract, dict):
            evidence["feature_contract"] = contract
            contract_fingerprint = contract.get("contract_fingerprint") or contract.get("fingerprint")
        else:
            contract_fingerprint = self.job.get("contract_fingerprint")

        dataset_info = load("dataset_info", self.dataset_dir / "meta/info.json")
        lineage_records: list[dict[str, Any]] = []
        lineage_paths = sorted(self.reports_dir.rglob("lineage.jsonl"))
        for path in lineage_paths:
            try:
                for line in path.read_text(encoding="utf-8").splitlines():
                    if line.strip():
                        value = json.loads(line)
                        if isinstance(value, dict):
                            lineage_records.append(value)
            except (OSError, json.JSONDecodeError):
                continue
        if lineage_records:
            evidence["bridge_lineage"] = lineage_records
            sources["bridge_lineage"] = str(lineage_paths[0])
        else:
            missing.add("bridge_lineage")

        dataset_present = self.dataset_dir.is_dir()
        evidence["dataset"] = {
            "path": str(self.dataset_dir),
            "present": dataset_present,
            "info": dataset_info,
        }
        if not dataset_present:
            missing.add("dataset")

        # Preserve all discovered reports as a convenience to evaluators that
        # need a newer scene-specific report without changing the collector API.
        for path in sorted(self.reports_dir.rglob("*.json")):
            key = path.stem
            if key not in evidence:
                value = _read_json(path)
                if value is not None:
                    evidence[key] = value
                    sources[key] = str(path)
                    missing.discard(key)

        return QualityEvidenceContext(
            dataset_dir=self.dataset_dir,
            reports_dir=self.reports_dir,
            evidence=evidence,
            sources=sources,
            missing_sources=missing,
            contract=contract if isinstance(contract, dict) else None,
            contract_fingerprint=str(contract_fingerprint) if contract_fingerprint else None,
        )


def collect_quality_evidence(
    *,
    dataset_dir: str | Path,
    reports_dir: str | Path,
    job: dict[str, Any] | None = None,
) -> QualityEvidenceContext:
    return QualityEvidenceCollector(
        dataset_dir=dataset_dir,
        reports_dir=reports_dir,
        job=job,
    ).collect()


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
