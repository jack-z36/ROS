from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from typing import Any

from repo.config.mcap_process_config import load_app_config
from repo.mcap_a_writer import MCAP_A_Writer
from schemas.mcap_a_writer import MCAP_A_MessageReplacement, MCAP_A_WritePlan, MCAP_A_WriterConfig
from schemas.pose_filter import PoseFilterConfig, PoseFilterSampleStatus
from schemas.repair import RepairDecisionStatus
from schemas.scene2_streams import Scene2RunContext
from schemas.tactile_filter import TactileFilterConfig, TactileFilterSampleStatus
from service.detectors import ReliabilityDetectionConfig

from .run_directory_creator import create_run_directory
from .scene2_pose_filter import compute_pose_filter
from .scene2_signal_reliability import SampleLoader, load_scene2_signal_samples
from .scene2_signal_repair import _run_detection, compute_signal_repair
from .scene2_tactile_filter import compute_tactile_filter


def run_scene2_mcap_a_writer(
    *,
    cleaned_mcap_path: str | Path,
    config_path: str | Path,
    run_root: str | Path = Path("src/data_clean/runs"),
    detection_config: ReliabilityDetectionConfig | None = None,
    pose_filter_config: PoseFilterConfig | None = None,
    tactile_filter_config: TactileFilterConfig | None = None,
    sample_loader: SampleLoader | None = None,
    compression: str = "none",
) -> dict[str, Any]:
    cleaned_mcap = Path(cleaned_mcap_path)
    config_path = Path(config_path)
    detection_config = detection_config or ReliabilityDetectionConfig()
    pose_filter_config = pose_filter_config or PoseFilterConfig()
    tactile_filter_config = tactile_filter_config or TactileFilterConfig()
    app_config = load_app_config(config_path)
    run_directory = create_run_directory(run_root=Path(run_root), run_date=date.today(), target_scenes=["scene2"])
    outputs_dir = Path(run_directory.layout.outputs_dir.path)
    artifacts_dir = outputs_dir / "artifacts"
    mcap_a_dir = artifacts_dir / "mcap_a"
    mcap_a_path = mcap_a_dir / f"{cleaned_mcap.stem}_mcap_a.mcap"
    summary_path = artifacts_dir / "mcap_a_write_summary.json"
    run_log_path = Path(run_directory.layout.run_log_path.path)
    detection_path = outputs_dir / "signal_reliability_detection_result.json"
    repair_path = outputs_dir / "signal_repair_result.json"
    pose_path = outputs_dir / "pose_filter_result.json"
    tactile_path = outputs_dir / "tactile_filter_result.json"
    steps = ["create_run_directory"]
    errors: list[dict[str, str]] = []
    writer_result = None

    snapshot = {
        "scene2": {
            "streams": [_jsonable(stream) for stream in app_config.scene2_streams],
            "detection": _jsonable(detection_config),
            "pose_filter": _jsonable(pose_filter_config),
            "tactile_filter": _jsonable(tactile_filter_config),
        }
    }
    stat = cleaned_mcap.stat() if cleaned_mcap.exists() else None
    context = Scene2RunContext(
        run_id=run_directory.run_id,
        input_cleaned_mcap=str(cleaned_mcap),
        input_identity={
            "size_bytes": stat.st_size if stat else None,
            "mtime_ns": stat.st_mtime_ns if stat else None,
        },
        config_snapshot=snapshot,
    )

    try:
        samples = (sample_loader or load_scene2_signal_samples)(cleaned_mcap, app_config)
        context.stream_inventory = getattr(samples, "inventory", None)
        steps.append("load_scene2_inventory_and_samples_once")

        detection_result = _run_detection(
            samples=samples,
            cleaned_mcap=cleaned_mcap,
            config_path=config_path,
            detection_config=detection_config,
            run_id=run_directory.run_id,
        )
        detection_result.run_context = context
        _write_json(detection_path, detection_result)
        steps.append("detect_once")

        repair_result = compute_signal_repair(
            samples=samples,
            detection_result=detection_result,
            config_path=config_path,
            run_id=run_directory.run_id,
        )
        repair_result.run_context = context
        _write_json(repair_path, repair_result)
        steps.append("repair_once")

        pose_result = compute_pose_filter(
            samples=samples,
            detection_result=detection_result,
            repair_result=repair_result,
            pose_filter_config=pose_filter_config,
            repair_result_ref=repair_path,
            run_id=run_directory.run_id,
        )
        pose_result.run_context = context
        _write_json(pose_path, pose_result)
        steps.append("filter_pose")

        tactile_result = compute_tactile_filter(
            samples=samples,
            detection_result=detection_result,
            repair_result=repair_result,
            tactile_filter_config=tactile_filter_config,
            repair_result_ref=repair_path,
            run_id=run_directory.run_id,
        )
        tactile_result.run_context = context
        _write_json(tactile_path, tactile_result)
        steps.append("filter_tactile")

        replacements = _build_stable_replacements(repair_result, pose_result, tactile_result)
        replacement_topics = sorted({item.sample_ref.topic for item in replacements})
        plan = MCAP_A_WritePlan(
            source_mcap=str(cleaned_mcap),
            output_mcap=str(mcap_a_path),
            operations=[
                {"operation": "replace", "topic": topic, "sequence_ref": f"stable-ref://{topic}"}
                for topic in replacement_topics
            ],
            output_sequence_refs={
                "signal_repair_result_ref": str(repair_path),
                "pose_filter_result_ref": str(pose_path),
                "tactile_filter_result_ref": str(tactile_path),
            },
            run_id=run_directory.run_id,
            run_context=context,
        )
        writer = MCAP_A_Writer(MCAP_A_WriterConfig(output_path=str(mcap_a_path), compression="none"), plan)
        writer_result = writer.execute_write_plan(plan, replacements=replacements)
        if not writer_result.success:
            raise RuntimeError("; ".join(writer_result.error_log))
        generated_summary = mcap_a_path.parent / "mcap_a_write_summary.json"
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(generated_summary.read_text(encoding="utf-8"), encoding="utf-8")
        steps.append("stream_copy_write_and_validate")
    except Exception as exc:
        errors.append({"type": type(exc).__name__, "message": str(exc)})

    outputs = {
        "run_dir": str(run_directory.run_dir),
        "artifacts_dir": str(artifacts_dir),
        "mcap_a": str(mcap_a_path),
        "mcap_a_write_summary_json": str(summary_path),
        "signal_reliability_detection_result_json": str(detection_path),
        "signal_repair_result_json": str(repair_path),
        "pose_filter_result_json": str(pose_path),
        "tactile_filter_result_json": str(tactile_path),
    }
    run_log = {
        "run_id": run_directory.run_id,
        "check_id": "scene2_mcap_a_writer",
        "status": "failed" if errors else "success",
        "input": {"cleaned_mcap": str(cleaned_mcap)},
        "config": {"config_snapshot": snapshot, "compression": compression, "temporary_override_saved": False},
        "stream_inventory": _jsonable(context.stream_inventory),
        "steps": steps + ["write_run_log"],
        "stats": {
            "writer_success": bool(writer_result and writer_result.success),
            "contract": _jsonable(writer_result.contract) if writer_result else None,
        },
        "errors": errors,
        "outputs": outputs,
        "created_at": datetime.now().isoformat(),
    }
    _write_json(run_log_path, run_log)
    return {**run_log, "run_log_path": str(run_log_path)}


def _build_stable_replacements(repair_result: Any, pose_result: Any, tactile_result: Any) -> list[MCAP_A_MessageReplacement]:
    repaired_keys = {
        (record.sample_ref.topic, record.sample_ref.message_index)
        for run in repair_result.repair_runs
        for record in run.sample_records
        if record.status is RepairDecisionStatus.REPAIRED
    }
    replacements: dict[tuple[str, int], MCAP_A_MessageReplacement] = {}
    for record in pose_result.sample_records:
        key = (record.sample_ref.topic, record.sample_ref.message_index)
        if record.status is PoseFilterSampleStatus.FILTERED or key in repaired_keys:
            replacements[key] = MCAP_A_MessageReplacement(record.sample_ref, "pose", record.final_value)
    for topic_entries in tactile_result.output_sequence_refs.values():
        for entry in topic_entries:
            ref = entry["sample_ref"]
            key = (ref.topic, ref.message_index)
            if entry.get("filtered_matrix") is not None and (
                entry.get("status") in {TactileFilterSampleStatus.FILTERED.value, TactileFilterSampleStatus.EMA_RESET.value}
                or key in repaired_keys
            ):
                replacements[key] = MCAP_A_MessageReplacement(ref, "tactile.frame", entry["filtered_matrix"])
    for run in repair_result.repair_runs:
        if run.replacement_unit != "gripper.value":
            continue
        for record in run.sample_records:
            if record.status is RepairDecisionStatus.REPAIRED:
                value = record.value_summary.get("value")
                replacements[(record.sample_ref.topic, record.sample_ref.message_index)] = MCAP_A_MessageReplacement(
                    record.sample_ref, "gripper.value", value
                )
    return list(replacements.values())


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_jsonable(value), ensure_ascii=False, indent=2), encoding="utf-8")


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
