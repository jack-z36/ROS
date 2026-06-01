"""Runtime orchestration for scene 2 signal reliability detection."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from typing import Callable, Iterable, Any

from mcap.reader import make_reader

from repo.config.mcap_process_config import AppConfig, load_app_config
from repo.ros2_codec import (
    Ros2DynamicCodec,
    extract_pose_fields,
    select_alignment_timestamp,
)
from service.detectors import (
    GripperSample,
    PoseSample,
    ReliabilityDetectionConfig,
    TactilePressureFrame,
    detect_gripper_reliability,
    detect_pose_reliability,
    detect_tactile_reliability,
)
from schemas.reliability import SignalReliabilityDetectionResult

from .run_directory_creator import create_run_directory


@dataclass(frozen=True)
class Scene2SignalSamples:
    pose: list[PoseSample]
    gripper: list[GripperSample]
    tactile: list[TactilePressureFrame]


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


def load_scene2_signal_samples(cleaned_mcap_path: str | Path, config: AppConfig) -> Scene2SignalSamples:
    cleaned_mcap = Path(cleaned_mcap_path)
    if not cleaned_mcap.is_file():
        raise FileNotFoundError(f"cleaned MCAP not found: {cleaned_mcap}")

    pose_topics: dict[str, str] = {}
    for stream in config.pose_streams:
        pose_topics[stream.input_topic] = stream.msg_type
        pose_topics[stream.output_topic] = stream.msg_type
    gripper_topics = {stream.output_topic for stream in config.gripper_streams}
    pose_samples: list[PoseSample] = []
    gripper_samples: list[GripperSample] = []
    tactile_frames: list[TactilePressureFrame] = []
    message_indexes: dict[str, int] = {}
    codec = Ros2DynamicCodec()

    with cleaned_mcap.open("rb") as fh:
        reader = make_reader(fh)
        for schema, channel, message in reader.iter_messages(log_time_order=True):
            topic = channel.topic
            index = message_indexes.get(topic, 0)
            message_indexes[topic] = index + 1
            if schema is None:
                continue
            if topic in pose_topics:
                decoded = codec.decode(schema, message)
                selected_timestamp = select_alignment_timestamp(
                    schema,
                    message,
                    codec=codec,
                    decoded_message=decoded,
                )
                x, y, z, qx, qy, qz, qw = extract_pose_fields(decoded, pose_topics[topic])
                pose_samples.append(
                    PoseSample(
                        topic=topic,
                        timestamp_ns=selected_timestamp.timestamp_ns,
                        message_index=index,
                        position=(x, y, z),
                        orientation_xyzw=(qx, qy, qz, qw),
                        time_domain=selected_timestamp.time_domain,
                    )
                )
            elif topic in gripper_topics:
                decoded = codec.decode(schema, message)
                selected_timestamp = select_alignment_timestamp(
                    schema,
                    message,
                    codec=codec,
                    decoded_message=decoded,
                )
                gripper_samples.append(
                    GripperSample(
                        topic=topic,
                        timestamp_ns=selected_timestamp.timestamp_ns,
                        message_index=index,
                        value=float(decoded.data),
                        time_domain=selected_timestamp.time_domain,
                    )
                )
            elif _is_tactile_topic(topic):
                decoded = codec.decode(schema, message)
                selected_timestamp = select_alignment_timestamp(
                    schema,
                    message,
                    codec=codec,
                    decoded_message=decoded,
                )
                tactile_frames.append(
                    _tactile_frame_from_message(
                        topic,
                        selected_timestamp.timestamp_ns,
                        index,
                        decoded,
                        selected_timestamp.time_domain,
                    )
                )

    return Scene2SignalSamples(pose=pose_samples, gripper=gripper_samples, tactile=tactile_frames)


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


def _is_tactile_topic(topic: str) -> bool:
    lowered = topic.lower()
    return "pressure" in lowered or "tactile" in lowered


def _tactile_frame_from_message(
    topic: str,
    timestamp_ns: int,
    index: int,
    message: Any,
    time_domain: str = "log_time",
) -> TactilePressureFrame:
    rows = int(getattr(message, "rows", getattr(message, "height", 0)))
    cols = int(getattr(message, "cols", getattr(message, "width", 0)))
    data = [int(value) for value in list(getattr(message, "data", []))]
    parts = [part for part in topic.strip("/").split("/") if part]
    return TactilePressureFrame(
        topic=topic,
        timestamp_ns=timestamp_ns,
        message_index=index,
        hand=parts[-2] if len(parts) >= 2 else "unknown",
        gripper=parts[-1] if parts else "unknown",
        rows=rows,
        cols=cols,
        data=data,
        time_domain=time_domain,
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
