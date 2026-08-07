"""Temporary bimanual Forge bridge for LeRobot v3 format validation.

The Scene 3 aligned MCAP remains a semantic intermediate artifact. This bridge
builds a separate Forge-ready MCAP whose JointState vectors match the temporary
absolute-pose LeRobot contract used for format and quality smoke tests.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import yaml
from mcap.reader import make_reader
from mcap.writer import CompressionType, Writer
from mcap_ros2.writer import serialize_dynamic

from repo.ros2_codec import Ros2DynamicCodec
from schemas.lerobot_features import (
    CompiledLeRobotFeatureContract,
    compile_lerobot_feature_contract,
    lerobot_feature_schema,
    normalize_lerobot_features_config,
)
from schemas.ros2_schemas import SENSOR_MSGS_JOINT_STATE


class ForgeBridgeError(RuntimeError):
    """Raised when an aligned MCAP cannot produce a valid Forge bridge."""


@dataclass(frozen=True)
class ForgeBridgeConfig:
    """Validation and provenance controls for the temporary bridge."""

    mode: str = "formal"
    pose_source_profile: str = "formal"
    calibration_ready: bool = False
    max_pose_abs_m: float = 10.0
    lerobot_features: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if self.mode not in {"formal", "format-only"}:
            raise ValueError("mode must be 'formal' or 'format-only'")
        if self.pose_source_profile not in {"formal", "format-only"}:
            raise ValueError(
                "pose_source_profile must be 'formal' or 'format-only'"
            )
        if self.max_pose_abs_m <= 0:
            raise ValueError("max_pose_abs_m must be positive")
        normalize_lerobot_features_config(self.lerobot_features)


@dataclass(frozen=True)
class ForgeBridgeResult:
    """Paths and summary facts emitted by :func:`write_forge_bridge`."""

    forge_ready_mcap: str
    forge_topic_config: str
    forge_bridge_schema: str
    forge_bridge_report: str
    input_step_count: int
    output_step_count: int
    training_eligible: bool
    feature_contract_path: str = ""
    lineage_path: str = ""
    contract_fingerprint: str = ""


@dataclass(frozen=True)
class _ImagePayload:
    payload: bytes
    schema_name: str
    schema_encoding: str
    schema_data: bytes
    message_encoding: str


ALIGNED_TOPICS = {
    "image_left": "/gopro_left/image_raw",
    "image_right": "/gopro_right/image_raw",
    "left_tcp_pose": "/aligned/left_tcp_pose",
    "right_tcp_pose": "/aligned/right_tcp_pose",
    "left_gripper_width": "/aligned/left_gripper_width",
    "right_gripper_width": "/aligned/right_gripper_width",
    "tactile_left_gripper_1": "/aligned/tactile_left_gripper_1",
    "tactile_left_gripper_2": "/aligned/tactile_left_gripper_2",
    "tactile_right_gripper_1": "/aligned/tactile_right_gripper_1",
    "tactile_right_gripper_2": "/aligned/tactile_right_gripper_2",
}

FORGE_TOPICS = {
    "image_left": "/forge/observation/images/left",
    "image_right": "/forge/observation/images/right",
    "state": "/forge/observation/state",
    "action": "/forge/action",
}

STATE_SEGMENTS = [
    ("left_tcp_pose", 0, 7, "m + quaternion_xyzw"),
    ("right_tcp_pose", 7, 14, "m + quaternion_xyzw"),
    ("left_gripper_width", 14, 15, "normalized_0_to_1"),
    ("right_gripper_width", 15, 16, "normalized_0_to_1"),
    ("tactile_left_gripper_1", 16, 20, "mean_std_min_max"),
    ("tactile_left_gripper_2", 20, 24, "mean_std_min_max"),
    ("tactile_right_gripper_1", 24, 28, "mean_std_min_max"),
    ("tactile_right_gripper_2", 28, 32, "mean_std_min_max"),
]

ACTION_SEGMENTS = [
    ("left_tcp_pose_t_plus_1", 0, 7, "m + quaternion_xyzw"),
    ("left_gripper_width_t_plus_1", 7, 8, "normalized_0_to_1"),
    ("right_tcp_pose_t_plus_1", 8, 15, "m + quaternion_xyzw"),
    ("right_gripper_width_t_plus_1", 15, 16, "normalized_0_to_1"),
]


def write_forge_bridge(
    *,
    aligned_mcap_path: str | Path,
    output_dir: str | Path,
    config: ForgeBridgeConfig | None = None,
) -> ForgeBridgeResult:
    """Build ``forge_ready.mcap`` plus schema, config, and report sidecars."""

    active_config = config or ForgeBridgeConfig()
    aligned_path = Path(aligned_mcap_path).expanduser().resolve()
    output_path = Path(output_dir).expanduser().resolve()
    output_path.mkdir(parents=True, exist_ok=True)

    report_path = output_path / "forge_bridge_report.json"
    try:
        _validate_mode(active_config)
        streams = _load_aligned_streams(aligned_path)
        contract = compile_lerobot_feature_contract(active_config.lerobot_features)
        feature_config = contract.config
        required_fields = _required_stream_fields(contract)
        timestamps = _complete_step_timestamps(
            streams,
            required_fields=required_fields,
            require_all_aligned=active_config.mode == "formal",
        )
        if len(timestamps) < 2:
            raise ForgeBridgeError(
                "bridge_requires_at_least_two_complete_aligned_steps"
            )

        _continuous_pose_stream(streams["left_tcp_pose"], timestamps)
        _continuous_pose_stream(streams["right_tcp_pose"], timestamps)
        _validate_stream_values(streams, timestamps, active_config, required_fields)

        forge_ready_path = output_path / "forge_ready.mcap"
        lineage_path = output_path / "lineage.jsonl"
        _write_forge_ready_mcap(
            forge_ready_path, streams, timestamps, contract, lineage_path
        )

        feature_contract_path = output_path / "feature_contract.json"
        feature_contract_path.write_text(
            json.dumps(contract.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        topic_config_path = output_path / "forge_topic_config.yaml"
        topic_config_path.write_text(
            yaml.safe_dump(_topic_config_dict(contract), sort_keys=False),
            encoding="utf-8",
        )

        schema_path = output_path / "forge_bridge_schema.json"
        schema = _schema_dict(contract)
        schema_path.write_text(
            json.dumps(schema, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        training_eligible = active_config.mode == "formal"
        report = {
            "status": "completed",
            "created_at": _now_iso(),
            "input_aligned_mcap": str(aligned_path),
            "output_forge_ready_mcap": str(forge_ready_path),
            "mode": active_config.mode,
            "pose_source_profile": active_config.pose_source_profile,
            "calibration_ready": active_config.calibration_ready,
            "training_eligible": training_eligible,
            "input_complete_step_count": len(timestamps),
            "output_step_count": len(timestamps) - 1,
            "dropped_terminal_step_count": 1,
            "state_dim": schema["observation.state"]["shape"][0],
            "action_dim": schema["action"]["shape"][0],
            "action_semantics": "absolute_bimanual_tcp_pose_and_gripper_at_t_plus_1",
            "formal_action_semantics": "absolute_tcp_target_pose_for_training_side_relative_conversion",
            "lerobot_features": feature_config,
            "feature_schema": schema,
            "feature_contract": contract.to_dict(),
            "contract_fingerprint": contract.fingerprint,
            "feature_contract_path": str(feature_contract_path),
            "lineage_path": str(lineage_path),
            "aligned_topics": ALIGNED_TOPICS,
            "forge_topics": FORGE_TOPICS,
        }
        report_path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return ForgeBridgeResult(
            forge_ready_mcap=str(forge_ready_path),
            forge_topic_config=str(topic_config_path),
            forge_bridge_schema=str(schema_path),
            forge_bridge_report=str(report_path),
            input_step_count=len(timestamps),
            output_step_count=len(timestamps) - 1,
            training_eligible=training_eligible,
            feature_contract_path=str(feature_contract_path),
            lineage_path=str(lineage_path),
            contract_fingerprint=contract.fingerprint,
        )
    except Exception as exc:
        report_path.write_text(
            json.dumps(
                {
                    "status": "failed",
                    "created_at": _now_iso(),
                    "input_aligned_mcap": str(aligned_path),
                    "mode": active_config.mode,
                    "pose_source_profile": active_config.pose_source_profile,
                    "calibration_ready": active_config.calibration_ready,
                    "training_eligible": False,
                    "error": f"{type(exc).__name__}: {exc}",
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        if isinstance(exc, ForgeBridgeError):
            raise
        raise ForgeBridgeError(str(exc)) from exc


def _validate_mode(config: ForgeBridgeConfig) -> None:
    if config.mode != "formal":
        return
    if config.pose_source_profile != "formal":
        raise ForgeBridgeError("formal_mode_requires_source_frame_tcp_pose")
    if not config.calibration_ready:
        raise ForgeBridgeError("formal_mode_requires_calibration_ready")


def _load_aligned_streams(aligned_path: Path) -> dict[str, dict[int, Any]]:
    if not aligned_path.is_file():
        raise ForgeBridgeError(f"aligned_mcap_not_found: {aligned_path}")

    topic_to_field = {topic: field for field, topic in ALIGNED_TOPICS.items()}
    streams: dict[str, dict[int, Any]] = {
        field: {} for field in ALIGNED_TOPICS
    }
    codec = Ros2DynamicCodec()
    with aligned_path.open("rb") as fh:
        reader = make_reader(fh)
        for schema, channel, message in reader.iter_messages(
            log_time_order=False
        ):
            field_name = topic_to_field.get(channel.topic)
            if field_name is None:
                continue
            timestamp_ns = int(message.log_time)
            if timestamp_ns in streams[field_name]:
                raise ForgeBridgeError(
                    f"duplicate_aligned_step: field={field_name} timestamp_ns={timestamp_ns}"
                )
            if field_name.startswith("image_"):
                if schema is None:
                    raise ForgeBridgeError(
                        f"image_schema_missing: field={field_name}"
                    )
                value: Any = _ImagePayload(
                    payload=message.data,
                    schema_name=schema.name,
                    schema_encoding=schema.encoding,
                    schema_data=schema.data,
                    message_encoding=channel.message_encoding,
                )
            else:
                if schema is None:
                    raise ForgeBridgeError(
                        f"numeric_schema_missing: field={field_name}"
                    )
                decoded = codec.decode(schema, message)
                if field_name.endswith("gripper_width"):
                    value = [float(decoded.data)]
                else:
                    value = [float(item) for item in decoded.position]
            streams[field_name][timestamp_ns] = value
    return streams


def _complete_step_timestamps(
    streams: dict[str, dict[int, Any]],
    *,
    required_fields: set[str],
    require_all_aligned: bool,
) -> list[int]:
    missing_topics = [
        ALIGNED_TOPICS[field_name]
        for field_name, values in streams.items()
        if field_name in required_fields and not values
    ]
    if missing_topics:
        raise ForgeBridgeError(
            f"missing_required_aligned_topics: {', '.join(missing_topics)}"
        )
    timestamp_sets = [set(streams[field_name]) for field_name in sorted(required_fields)]
    if require_all_aligned and any(
        timestamps != timestamp_sets[0] for timestamps in timestamp_sets[1:]
    ):
        raise ForgeBridgeError("incomplete_required_aligned_steps")
    common_timestamps = set.intersection(*timestamp_sets)
    return sorted(common_timestamps)


def _continuous_pose_stream(
    pose_stream: dict[int, list[float]],
    timestamps: list[int],
) -> None:
    previous_quaternion: list[float] | None = None
    for timestamp_ns in timestamps:
        pose = pose_stream[timestamp_ns]
        if len(pose) != 7:
            raise ForgeBridgeError(
                f"pose_vector_dimension_mismatch: expected=7 actual={len(pose)}"
            )
        quaternion = _normalized_quaternion(pose[3:7])
        if (
            previous_quaternion is not None
            and _dot(previous_quaternion, quaternion) < 0.0
        ):
            quaternion = [-value for value in quaternion]
        pose[3:7] = quaternion
        previous_quaternion = quaternion


def _normalized_quaternion(quaternion: list[float]) -> list[float]:
    norm = math.sqrt(sum(value * value for value in quaternion))
    if not math.isfinite(norm) or norm <= 0.0:
        raise ForgeBridgeError("invalid_pose_quaternion")
    return [value / norm for value in quaternion]


def _dot(left: list[float], right: list[float]) -> float:
    return sum(a * b for a, b in zip(left, right, strict=True))


def _validate_stream_values(
    streams: dict[str, dict[int, Any]],
    timestamps: list[int],
    config: ForgeBridgeConfig,
    required_fields: set[str],
) -> None:
    expected_dims = {
        "left_tcp_pose": 7,
        "right_tcp_pose": 7,
        "left_gripper_width": 1,
        "right_gripper_width": 1,
        "tactile_left_gripper_1": 4,
        "tactile_left_gripper_2": 4,
        "tactile_right_gripper_1": 4,
        "tactile_right_gripper_2": 4,
    }
    for field_name, expected_dim in expected_dims.items():
        if field_name not in required_fields:
            continue
        for timestamp_ns in timestamps:
            values = streams[field_name][timestamp_ns]
            if len(values) != expected_dim:
                raise ForgeBridgeError(
                    f"vector_dimension_mismatch: field={field_name} "
                    f"expected={expected_dim} actual={len(values)}"
                )
            if not all(math.isfinite(value) for value in values):
                raise ForgeBridgeError(
                    f"non_finite_value: field={field_name} timestamp_ns={timestamp_ns}"
                )

    for field_name in ("left_gripper_width", "right_gripper_width"):
        if field_name not in required_fields:
            continue
        for timestamp_ns in timestamps:
            width = streams[field_name][timestamp_ns][0]
            if not 0.0 <= width <= 1.0:
                raise ForgeBridgeError(
                    f"gripper_width_out_of_range: field={field_name} value={width}"
                )

    if config.mode == "formal":
        for field_name in ("left_tcp_pose", "right_tcp_pose"):
            for timestamp_ns in timestamps:
                position = streams[field_name][timestamp_ns][:3]
                if any(abs(value) > config.max_pose_abs_m for value in position):
                    raise ForgeBridgeError(
                        f"pose_position_out_of_range: field={field_name} "
                        f"limit_m={config.max_pose_abs_m} values={position}"
                    )


def _write_forge_ready_mcap(
    output_path: Path,
    streams: dict[str, dict[int, Any]],
    timestamps: list[int],
    contract: CompiledLeRobotFeatureContract | dict[str, Any],
    lineage_path: Path | None = None,
) -> None:
    contract = _ensure_contract(contract)
    lineage_path = lineage_path or output_path.with_name("lineage.jsonl")
    joint_encoder = serialize_dynamic(
        "sensor_msgs/msg/JointState",
        SENSOR_MSGS_JOINT_STATE,
    )["sensor_msgs/msg/JointState"]
    with output_path.open("wb") as fh:
        writer = Writer(fh, compression=CompressionType.NONE)
        writer.start()
        joint_schema_id = writer.register_schema(
            "sensor_msgs/msg/JointState",
            "ros2msg",
            SENSOR_MSGS_JOINT_STATE.encode("utf-8"),
        )
        channels: dict[str, int] = {
            "state": writer.register_channel(
                FORGE_TOPICS["state"], "cdr", joint_schema_id
            ),
            "action": writer.register_channel(
                FORGE_TOPICS["action"], "cdr", joint_schema_id
            ),
        }
        for image_field in ("image_left", "image_right"):
            sample = streams[image_field][timestamps[0]]
            schema_id = writer.register_schema(
                sample.schema_name,
                sample.schema_encoding,
                sample.schema_data,
            )
            channels[image_field] = writer.register_channel(
                FORGE_TOPICS[image_field],
                sample.message_encoding,
                schema_id,
            )

        with lineage_path.open("w", encoding="utf-8") as lineage:
            for step_index, timestamp_ns in enumerate(timestamps[:-1]):
                next_timestamp_ns = timestamps[step_index + 1]
                for image_field in ("image_left", "image_right"):
                    sample = streams[image_field][timestamp_ns]
                    writer.add_message(
                        channel_id=channels[image_field],
                        log_time=timestamp_ns,
                        publish_time=timestamp_ns,
                        sequence=step_index,
                        data=sample.payload,
                    )
                state_values = _state_vector(streams, timestamp_ns, contract)
                writer.add_message(
                    channel_id=channels["state"],
                    log_time=timestamp_ns,
                    publish_time=timestamp_ns,
                    sequence=step_index,
                    data=joint_encoder(
                        _joint_state_message(
                            state_values, "observation.state", contract.state.names
                        )
                    ),
                )
                action_values = _action_vector(streams, next_timestamp_ns, contract)
                writer.add_message(
                    channel_id=channels["action"],
                    log_time=timestamp_ns,
                    publish_time=timestamp_ns,
                    sequence=step_index,
                    data=joint_encoder(
                        _joint_state_message(
                            action_values, "action", contract.action.names
                        )
                    ),
                )
                lineage.write(
                    json.dumps(
                        {
                            "episode_index": 0,
                            "step_index": step_index,
                            "output_timestamp_ns": timestamp_ns,
                            "state_timestamp_ns": timestamp_ns,
                            "action_source_timestamp_ns": next_timestamp_ns,
                            "action_source_step_index": step_index + 1,
                            "action_relation": "t+1",
                            "contract_fingerprint": contract.fingerprint,
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )
        writer.finish()


def _joint_state_message(
    values: list[float], frame_id: str, names: tuple[str, ...] | list[str] = ()
) -> Any:
    return SimpleNamespace(
        header=SimpleNamespace(
            stamp=SimpleNamespace(sec=0, nanosec=0),
            frame_id=frame_id,
        ),
        name=list(names),
        position=values,
        velocity=[],
        effort=[],
    )


def _state_vector(
    streams: dict[str, dict[int, Any]],
    timestamp_ns: int,
    contract: CompiledLeRobotFeatureContract | dict[str, Any],
) -> list[float]:
    contract = _ensure_contract(contract)
    values: list[float] = []
    for segment in contract.state.segments:
        values.extend(streams[segment.source_field][timestamp_ns])
    if len(values) != contract.state.dim:
        raise ForgeBridgeError(
            f"compiled state dimension mismatch: expected={contract.state.dim} actual={len(values)}"
        )
    return values


def _action_vector(
    streams: dict[str, dict[int, Any]],
    next_timestamp_ns: int,
    contract: CompiledLeRobotFeatureContract | dict[str, Any],
) -> list[float]:
    contract = _ensure_contract(contract)
    values: list[float] = []
    for segment in contract.action.segments:
        values.extend(streams[segment.source_field][next_timestamp_ns])
    if len(values) != contract.action.dim:
        raise ForgeBridgeError(
            f"compiled action dimension mismatch: expected={contract.action.dim} actual={len(values)}"
        )
    return values


def _schema_dict(contract: CompiledLeRobotFeatureContract | dict[str, Any]) -> dict[str, Any]:
    contract = _ensure_contract(contract)
    schema = lerobot_feature_schema(contract.config)
    return {
        "schema_version": "forge_bridge_bimanual_absolute_v1",
        "warning": "Temporary Forge bridge only; not the formal UMI relative action chunk schema.",
        "feature_schema_version": schema["schema_version"],
        "contract_fingerprint": contract.fingerprint,
        "feature_contract": contract.to_dict(),
        "observation.state": schema["observation.state"],
        "action": schema["action"],
        "images": {
            "observation.images.left": FORGE_TOPICS["image_left"],
            "observation.images.right": FORGE_TOPICS["image_right"],
        },
    }


def _topic_config_dict(contract: CompiledLeRobotFeatureContract | dict[str, Any]) -> dict[str, Any]:
    contract = _ensure_contract(contract)
    schema = lerobot_feature_schema(contract.config)
    return {
        "episodes": {"strategy": "single"},
        "fields": {
            "observation.state": {
                "topic": FORGE_TOPICS["state"],
                "field": "position",
                "target_shape": schema["observation.state"]["shape"],
                "names": list(contract.state.names),
                "contract_fingerprint": contract.fingerprint,
            },
            "action": {
                "topic": FORGE_TOPICS["action"],
                "field": "position",
                "target_shape": schema["action"]["shape"],
                "names": list(contract.action.names),
                "contract_fingerprint": contract.fingerprint,
            },
            "observation.images.left": {
                "topic": FORGE_TOPICS["image_left"],
            },
            "observation.images.right": {
                "topic": FORGE_TOPICS["image_right"],
            },
        },
        "sync": {
            "primary": "observation.state",
            "method": "nearest",
            "max_skew_ms": 1.0,
        },
    }


def _required_stream_fields(contract: CompiledLeRobotFeatureContract | dict[str, Any]) -> set[str]:
    contract = _ensure_contract(contract)
    fields = {"image_left", "image_right"}
    fields.update(segment.source_field for segment in contract.state.segments)
    fields.update(segment.source_field for segment in contract.action.segments)
    return fields


def _ensure_contract(
    value: CompiledLeRobotFeatureContract | dict[str, Any],
) -> CompiledLeRobotFeatureContract:
    return value if isinstance(value, CompiledLeRobotFeatureContract) else compile_lerobot_feature_contract(value)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
