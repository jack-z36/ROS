from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from typing import Any

from mcap.reader import make_reader

from repo.mcap_a_writer import MCAP_A_Writer
from repo.ros2_codec import Ros2DynamicCodec, inject_pose_fields, inject_tactile_fields
from schemas.mcap_a_writer import MCAP_A_WritePlan, MCAP_A_WriterConfig
from schemas.pose_filter import PoseFilterConfig
from schemas.tactile_filter import TactileFilterConfig
from service.detectors import ReliabilityDetectionConfig

from .run_directory_creator import create_run_directory
from .scene2_pose_filter import run_scene2_pose_filter
from .scene2_signal_reliability import SampleLoader, run_scene2_signal_reliability_detection
from .scene2_signal_repair import run_scene2_signal_repair
from .scene2_tactile_filter import run_scene2_tactile_filter


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
    run_root = Path(run_root)
    run_directory = create_run_directory(
        run_root=run_root,
        run_date=date.today(),
        target_scenes=["scene2"],
    )
    outputs_dir = Path(run_directory.layout.outputs_dir.path)
    artifacts_dir = outputs_dir / "artifacts"
    mcap_a_dir = artifacts_dir / "mcap_a"
    mcap_a_path = mcap_a_dir / f"{cleaned_mcap.stem}_mcap_a.mcap"
    summary_path = artifacts_dir / "mcap_a_write_summary.json"
    run_log_path = Path(run_directory.layout.run_log_path.path)
    steps = ["create_run_directory"]
    errors: list[dict[str, str]] = []

    detection_result: dict[str, Any] | None = None
    repair_result: dict[str, Any] | None = None
    pose_result: dict[str, Any] | None = None
    tactile_result: dict[str, Any] | None = None
    writer_result = None

    try:
        detection_result = run_scene2_signal_reliability_detection(
            cleaned_mcap_path=cleaned_mcap,
            config_path=config_path,
            run_root=run_root,
            detection_config=detection_config,
            sample_loader=sample_loader,
        )
        steps.append("run_signal_reliability_detection")
        _raise_if_failed(detection_result, "signal_reliability_detection_failed")

        repair_result = run_scene2_signal_repair(
            cleaned_mcap_path=cleaned_mcap,
            config_path=config_path,
            run_root=run_root,
            detection_config=detection_config,
            sample_loader=sample_loader,
        )
        steps.append("run_signal_repair")
        _raise_if_failed(repair_result, "signal_repair_failed")

        pose_result = run_scene2_pose_filter(
            cleaned_mcap_path=cleaned_mcap,
            config_path=config_path,
            run_root=run_root,
            detection_config=detection_config,
            pose_filter_config=pose_filter_config,
            sample_loader=sample_loader,
        )
        steps.append("run_pose_filter")
        _raise_if_failed(pose_result, "pose_filter_failed")

        tactile_result = run_scene2_tactile_filter(
            cleaned_mcap_path=cleaned_mcap,
            config_path=config_path,
            run_root=run_root,
            detection_config=detection_config,
            tactile_filter_config=tactile_filter_config,
            sample_loader=sample_loader,
        )
        steps.append("run_tactile_filter")
        _raise_if_failed(tactile_result, "tactile_filter_failed")

        plan, replacement_content = _build_write_plan_and_replacements(
            cleaned_mcap=cleaned_mcap,
            mcap_a_path=mcap_a_path,
            pose_result=pose_result,
            tactile_result=tactile_result,
        )
        plan.output_sequence_refs = {
            "signal_repair_result_ref": repair_result["outputs"]["signal_repair_result_json"],
            "pose_filter_result_ref": pose_result["outputs"]["pose_filter_result_json"],
            "tactile_filter_result_ref": tactile_result["outputs"]["tactile_filter_result_json"],
        }
        writer = MCAP_A_Writer(MCAP_A_WriterConfig(output_path=str(mcap_a_path), compression="none"), plan)
        writer_result = writer.execute_write_plan(plan, replacement_content=replacement_content)
        if not writer_result.success:
            raise RuntimeError("; ".join(writer_result.error_log))
        mcap_a_summary = mcap_a_path.parent / "mcap_a_write_summary.json"
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        if mcap_a_summary != summary_path:
            summary_path.write_text(mcap_a_summary.read_text(encoding="utf-8"), encoding="utf-8")
        steps.append("write_mcap_a")
    except Exception as exc:
        errors.append({"type": type(exc).__name__, "message": str(exc)})

    outputs = {
        "run_dir": str(run_directory.run_dir),
        "artifacts_dir": str(artifacts_dir),
        "mcap_a": str(mcap_a_path),
        "mcap_a_write_summary_json": str(summary_path),
        "signal_reliability_detection_result_json": _output(detection_result, "signal_reliability_detection_result_json"),
        "signal_repair_result_json": _output(repair_result, "signal_repair_result_json"),
        "pose_filter_result_json": _output(pose_result, "pose_filter_result_json"),
        "tactile_filter_result_json": _output(tactile_result, "tactile_filter_result_json"),
    }
    run_log = {
        "run_id": run_directory.run_id,
        "check_id": "scene2_mcap_a_writer",
        "status": "failed" if errors else "success",
        "input": {
            "cleaned_mcap": str(cleaned_mcap),
            "signal_repair_result": outputs["signal_repair_result_json"],
            "pose_filter_result": outputs["pose_filter_result_json"],
            "tactile_filter_result": outputs["tactile_filter_result_json"],
        },
        "config": {
            "rule_config_ref": str(config_path),
            "writer_output_dir": str(mcap_a_dir),
            "compression": compression,
            "temporary_override_saved": False,
        },
        "steps": steps + ["write_run_log"],
        "stats": {
            "writer_success": bool(writer_result and writer_result.success),
            "contract": _jsonable(writer_result.contract) if writer_result else None,
        },
        "errors": errors,
        "outputs": outputs,
        "created_at": datetime.now().isoformat(),
    }
    run_log_path.write_text(json.dumps(_jsonable(run_log), ensure_ascii=False, indent=2), encoding="utf-8")
    return {**run_log, "run_log_path": str(run_log_path)}


def _raise_if_failed(result: dict[str, Any], reason: str) -> None:
    if result["status"] != "success":
        raise RuntimeError(reason)


def _output(result: dict[str, Any] | None, key: str) -> str | None:
    if result is None:
        return None
    value = result.get("outputs", {}).get(key)
    return str(value) if value is not None else None


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


def _build_write_plan_and_replacements(
    cleaned_mcap: Path,
    mcap_a_path: Path,
    pose_result: dict[str, Any],
    tactile_result: dict[str, Any],
) -> tuple[MCAP_A_WritePlan, dict[str, list[bytes]]]:
    """Read filter results, serialize filtered values to CDR, and build the write plan."""
    # 1. Load filter result JSONs
    pose_filter_path = Path(pose_result["outputs"]["pose_filter_result_json"])
    tactile_filter_path = Path(tactile_result["outputs"]["tactile_filter_result_json"])
    pose_filter_data = json.loads(pose_filter_path.read_text(encoding="utf-8"))
    tactile_filter_data = json.loads(tactile_filter_path.read_text(encoding="utf-8"))

    # 2. Build (topic, message_index) -> filtered value lookups
    pose_by_key: dict[tuple[str, int], dict] = {}
    for topic, entries in pose_filter_data.get("output_sequence_refs", {}).items():
        for entry in entries:
            ref = entry["sample_ref"]
            pose_by_key[(topic, ref["message_index"])] = entry

    tactile_by_key: dict[tuple[str, int], list[list[float]]] = {}
    for topic, entries in tactile_filter_data.get("output_sequence_refs", {}).items():
        for entry in entries:
            ref = entry["sample_ref"]
            matrix = entry.get("filtered_matrix")
            if matrix is not None:
                tactile_by_key[(topic, ref["message_index"])] = matrix

    pose_topics = {topic for topic, _ in pose_by_key}
    tactile_topics = {topic for topic, _ in tactile_by_key}
    replace_topics = pose_topics | tactile_topics

    if not replace_topics:
        plan = MCAP_A_WritePlan(
            source_mcap=str(cleaned_mcap),
            output_mcap=str(mcap_a_path),
            operations=[],
        )
        return plan, {}

    # 3. Read source MCAP, decode → inject → re-encode per replacement topic
    codec = Ros2DynamicCodec()
    replacement_content: dict[str, list[bytes]] = {topic: [] for topic in replace_topics}
    message_indexes: dict[str, int] = {}

    with cleaned_mcap.open("rb") as fh:
        reader = make_reader(fh)
        for schema, channel, message in reader.iter_messages(log_time_order=False):
            topic = channel.topic
            if topic not in replace_topics:
                continue
            if schema is None:
                raise RuntimeError(f"schema missing for replacement topic {topic}")

            index = message_indexes.get(topic, 0)
            message_indexes[topic] = index + 1
            decoded = codec.decode(schema, message)

            if topic in pose_topics:
                pose_entry = pose_by_key.get((topic, index))
                if pose_entry is not None:
                    pos = pose_entry["position"]
                    ori = pose_entry["orientation"]
                    injected = inject_pose_fields(
                        decoded,
                        schema.name,
                        (pos["x"], pos["y"], pos["z"], ori["x"], ori["y"], ori["z"], ori["w"]),
                    )
                    replacement_content[topic].append(codec.encode(schema, injected))
                else:
                    replacement_content[topic].append(message.data)

            elif topic in tactile_topics:
                matrix = tactile_by_key.get((topic, index))
                if matrix is not None:
                    injected = inject_tactile_fields(decoded, matrix)
                    replacement_content[topic].append(codec.encode(schema, injected))
                else:
                    replacement_content[topic].append(message.data)

    # 4. Build operations list
    operations = [
        {"operation": "replace", "topic": topic, "sequence_ref": f"filter://{topic}"}
        for topic in sorted(replace_topics)
    ]

    plan = MCAP_A_WritePlan(
        source_mcap=str(cleaned_mcap),
        output_mcap=str(mcap_a_path),
        operations=operations,
    )
    return plan, replacement_content
