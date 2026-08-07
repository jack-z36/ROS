from __future__ import annotations

import json
from pathlib import Path

from repo.quality_report_repository import QualityReportRepository
from runtime.dataset_quality_pipeline import _decision
from schemas.lerobot_features import compile_lerobot_feature_contract
from service.quality_evidence import QualityEvidenceCollector
from service.quality_evaluators import evaluate_quality_metrics


def _evidence_tree(tmp_path: Path, *, bad_lineage: bool = False) -> tuple[Path, Path]:
    dataset = tmp_path / "dataset"
    reports = tmp_path / "reports"
    (dataset / "meta").mkdir(parents=True)
    reports.mkdir()
    contract = compile_lerobot_feature_contract(None)
    (dataset / "meta/feature_contract.json").write_text(json.dumps(contract.to_dict()), encoding="utf-8")
    (dataset / "meta/info.json").write_text(
        json.dumps({
            "features": {
                "observation.state": {"shape": [32], "names": list(contract.state_names)},
                "action": {"shape": [16], "names": list(contract.action_names)},
            }
        }),
        encoding="utf-8",
    )
    (reports / "alignment_report.json").write_text(json.dumps({"max_dt_ms": 1}), encoding="utf-8")
    (reports / "forge_quality.json").write_text(json.dumps({"num_episodes": 1, "action_saturation_ratio": 0.01}), encoding="utf-8")
    state, action = (2, 1) if bad_lineage else (1, 2)
    (reports / "lineage.jsonl").write_text(
        json.dumps({
            "episode_index": 0, "step_index": 0, "action_source_step_index": 1,
            "state_timestamp_ns": state, "action_source_timestamp_ns": action,
            "action_relation": "t+1",
        }) + "\n",
        encoding="utf-8",
    )
    return dataset, reports


def test_quality_report_has_exactly_five_metrics_and_ready_decision(tmp_path: Path) -> None:
    dataset, reports = _evidence_tree(tmp_path)
    context = QualityEvidenceCollector(dataset_dir=dataset, reports_dir=reports).collect()
    metrics = evaluate_quality_metrics(context)
    assert len(metrics) == 5
    assert _decision(metrics) == "ready"
    repository = QualityReportRepository(reports)
    assert repository.trace_index_path.name == "quality_trace_index.json"


def test_missing_evidence_is_warn_and_review(tmp_path: Path) -> None:
    dataset, reports = _evidence_tree(tmp_path)
    (reports / "lineage.jsonl").unlink()
    context = QualityEvidenceCollector(dataset_dir=dataset, reports_dir=reports).collect()
    metrics = evaluate_quality_metrics(context)
    assert metrics[2].status == "warn"
    assert _decision(metrics) == "review"


def test_bad_t_plus_one_lineage_blocks_on_hard_metric(tmp_path: Path) -> None:
    dataset, reports = _evidence_tree(tmp_path, bad_lineage=True)
    context = QualityEvidenceCollector(dataset_dir=dataset, reports_dir=reports).collect()
    metrics = evaluate_quality_metrics(context)
    assert metrics[2].status == "fail"
    assert _decision(metrics) == "block"
