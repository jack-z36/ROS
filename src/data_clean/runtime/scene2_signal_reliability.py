"""Runtime orchestration for scene 2 signal reliability detection."""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from typing import Callable, Iterable, Any

from repo.config.mcap_process_config import AppConfig, load_app_config
from repo.scene2_mcap_reader import load_scene2_signal_samples
from service.detectors import (
    ReliabilityDetectionConfig,
    detect_gripper_reliability,
    detect_pose_reliability,
    detect_tactile_reliability,
)
from schemas.reliability import SignalReliabilityDetectionResult
from schemas.scene2_samples import Scene2SignalSamples

from .run_directory_creator import create_run_directory


SampleLoader = Callable[[Path, AppConfig], Scene2SignalSamples]


def run_scene2_signal_reliability_detection(
    *,
    cleaned_mcap_path: str | Path,
    config_path: str | Path,
    run_root: str | Path = Path("src/data_clean/runs"),
    detection_config: ReliabilityDetectionConfig | None = None,
    sample_loader: SampleLoader | None = None,
) -> dict[str, Any]:
    cleaned_mcap = Path(cleaned_mcap_path)
    config_path = Path(config_path)
    run_root = Path(run_root)
    detection_config = detection_config or ReliabilityDetectionConfig()
    steps = ["create_run_directory"]
    errors: list[dict[str, str]] = []

    app_config = load_app_config(config_path)
    run_directory = create_run_directory(
        run_root=run_root,
        run_date=date.today(),
        target_scenes=["scene2"],
    )
    result_path = Path(run_directory.layout.outputs_dir.path) / "signal_reliability_detection_result.json"
    run_log_path = Path(run_directory.layout.run_log_path.path)

    try:
        if sample_loader is None:
            sample_loader = load_scene2_signal_samples
        samples = sample_loader(cleaned_mcap, app_config)
        steps.append("load_cleaned_mcap")

        pose_result = detect_pose_reliability(
            samples.pose,
            config=detection_config,
            input_cleaned_mcap=str(cleaned_mcap),
            rule_config_ref=str(config_path),
        )
        steps.append("detect_pose")
        gripper_result = detect_gripper_reliability(
            samples.gripper,
            config=detection_config,
            input_cleaned_mcap=str(cleaned_mcap),
            rule_config_ref=str(config_path),
        )
        steps.append("detect_gripper")
        tactile_result = detect_tactile_reliability(
            samples.tactile,
            config=detection_config,
            input_cleaned_mcap=str(cleaned_mcap),
            rule_config_ref=str(config_path),
        )
        steps.append("detect_tactile")

        aggregate = merge_detection_results(
            input_cleaned_mcap=str(cleaned_mcap),
            rule_config_ref=str(config_path),
            results=(pose_result, gripper_result, tactile_result),
            run_id=run_directory.run_id,
        )
        result_path.write_text(
            json.dumps(_jsonable(aggregate), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        steps.append("write_debug_result")
    except Exception as exc:
        errors.append({"type": type(exc).__name__, "message": str(exc)})
        aggregate = SignalReliabilityDetectionResult(
            input_cleaned_mcap=str(cleaned_mcap),
            rule_config_ref=str(config_path),
            run_id=run_directory.run_id,
        )

    outputs = {
        "run_dir": str(run_directory.run_dir),
        "signal_reliability_detection_result_json": str(result_path),
    }
    run_log = {
        "run_id": run_directory.run_id,
        "check_id": "scene2_signal_reliability_detect",
        "status": "failed" if errors else "success",
        "input": {"cleaned_mcap": str(cleaned_mcap)},
        "config": {
            "rule_config_ref": str(config_path),
            "temporary_override_saved": False,
        },
        "steps": steps + ["write_run_log"],
        "stats": {
            "pose_samples": len(getattr(locals().get("samples", None), "pose", [])),
            "gripper_samples": len(getattr(locals().get("samples", None), "gripper", [])),
            "tactile_samples": len(getattr(locals().get("samples", None), "tactile", [])),
            "summary_by_modality": aggregate.summary_by_modality,
            "sample_issue_count": len(aggregate.sample_issues),
            "missing_interval_issue_count": len(aggregate.missing_interval_issues),
        },
        "errors": errors,
        "outputs": outputs,
        "created_at": datetime.now().isoformat(),
    }
    run_log_path.write_text(
        json.dumps(_jsonable(run_log), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return {**run_log, "run_log_path": str(run_log_path)}


def merge_detection_results(
    *,
    input_cleaned_mcap: str,
    rule_config_ref: str,
    results: Iterable[SignalReliabilityDetectionResult],
    run_id: str,
) -> SignalReliabilityDetectionResult:
    sample_issues = []
    missing_interval_issues = []
    summary_by_modality: dict[str, Any] = {}
    for result in results:
        sample_issues.extend(result.sample_issues)
        missing_interval_issues.extend(result.missing_interval_issues)
        summary_by_modality.update(result.summary_by_modality)
    return SignalReliabilityDetectionResult(
        input_cleaned_mcap=input_cleaned_mcap,
        rule_config_ref=rule_config_ref,
        sample_issues=sample_issues,
        missing_interval_issues=missing_interval_issues,
        summary_by_modality=summary_by_modality,
        created_at=datetime.now().isoformat(),
        run_id=run_id,
    )


def _jsonable(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return _jsonable(asdict(value))
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    return value
