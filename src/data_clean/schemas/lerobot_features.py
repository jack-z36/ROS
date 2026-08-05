from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class LeRobotFeatureSegment:
    id: str
    source_field: str
    dim: int
    unit: str
    semantic: str
    required: bool
    components: tuple[str, ...]
    time_offset_steps: int = 0


STATE_SEGMENT_DEFINITIONS: dict[str, LeRobotFeatureSegment] = {
    "left_tcp_pose": LeRobotFeatureSegment(
        id="left_tcp_pose",
        source_field="left_tcp_pose",
        dim=7,
        unit="m + quaternion_xyzw",
        semantic="left TCP pose in the original Baton source frame at step t",
        required=True,
        components=("x", "y", "z", "qx", "qy", "qz", "qw"),
    ),
    "right_tcp_pose": LeRobotFeatureSegment(
        id="right_tcp_pose",
        source_field="right_tcp_pose",
        dim=7,
        unit="m + quaternion_xyzw",
        semantic="right TCP pose in the original Baton source frame at step t",
        required=True,
        components=("x", "y", "z", "qx", "qy", "qz", "qw"),
    ),
    "left_gripper_width": LeRobotFeatureSegment(
        id="left_gripper_width",
        source_field="left_gripper_width",
        dim=1,
        unit="normalized_0_to_1",
        semantic="left gripper width at step t",
        required=False,
        components=("width",),
    ),
    "right_gripper_width": LeRobotFeatureSegment(
        id="right_gripper_width",
        source_field="right_gripper_width",
        dim=1,
        unit="normalized_0_to_1",
        semantic="right gripper width at step t",
        required=False,
        components=("width",),
    ),
    "tactile_left_gripper_1": LeRobotFeatureSegment(
        id="tactile_left_gripper_1",
        source_field="tactile_left_gripper_1",
        dim=4,
        unit="mean_std_min_max",
        semantic="left gripper tactile sensor 1 summary at step t",
        required=False,
        components=("mean", "std", "min", "max"),
    ),
    "tactile_left_gripper_2": LeRobotFeatureSegment(
        id="tactile_left_gripper_2",
        source_field="tactile_left_gripper_2",
        dim=4,
        unit="mean_std_min_max",
        semantic="left gripper tactile sensor 2 summary at step t",
        required=False,
        components=("mean", "std", "min", "max"),
    ),
    "tactile_right_gripper_1": LeRobotFeatureSegment(
        id="tactile_right_gripper_1",
        source_field="tactile_right_gripper_1",
        dim=4,
        unit="mean_std_min_max",
        semantic="right gripper tactile sensor 1 summary at step t",
        required=False,
        components=("mean", "std", "min", "max"),
    ),
    "tactile_right_gripper_2": LeRobotFeatureSegment(
        id="tactile_right_gripper_2",
        source_field="tactile_right_gripper_2",
        dim=4,
        unit="mean_std_min_max",
        semantic="right gripper tactile sensor 2 summary at step t",
        required=False,
        components=("mean", "std", "min", "max"),
    ),
}

ACTION_SEGMENT_DEFINITIONS: dict[str, LeRobotFeatureSegment] = {
    "left_tcp_pose_t_plus_1": LeRobotFeatureSegment(
        id="left_tcp_pose_t_plus_1",
        source_field="left_tcp_pose",
        dim=7,
        unit="m + quaternion_xyzw",
        semantic="left source-frame absolute TCP target pose at step t+1",
        required=True,
        components=("x", "y", "z", "qx", "qy", "qz", "qw"),
        time_offset_steps=1,
    ),
    "left_gripper_width_t_plus_1": LeRobotFeatureSegment(
        id="left_gripper_width_t_plus_1",
        source_field="left_gripper_width",
        dim=1,
        unit="normalized_0_to_1",
        semantic="left gripper target width at step t+1",
        required=False,
        components=("width",),
        time_offset_steps=1,
    ),
    "right_tcp_pose_t_plus_1": LeRobotFeatureSegment(
        id="right_tcp_pose_t_plus_1",
        source_field="right_tcp_pose",
        dim=7,
        unit="m + quaternion_xyzw",
        semantic="right source-frame absolute TCP target pose at step t+1",
        required=True,
        components=("x", "y", "z", "qx", "qy", "qz", "qw"),
        time_offset_steps=1,
    ),
    "right_gripper_width_t_plus_1": LeRobotFeatureSegment(
        id="right_gripper_width_t_plus_1",
        source_field="right_gripper_width",
        dim=1,
        unit="normalized_0_to_1",
        semantic="right gripper target width at step t+1",
        required=False,
        components=("width",),
        time_offset_steps=1,
    ),
}

DEFAULT_LEROBOT_FEATURES = {
    "schema_version": 1,
    "state_segments": [
        {"id": segment_id, "enabled": True}
        for segment_id in STATE_SEGMENT_DEFINITIONS
    ],
    "action_segments": [
        {"id": segment_id, "enabled": True}
        for segment_id in ACTION_SEGMENT_DEFINITIONS
    ],
}


class LeRobotFeatureConfigError(ValueError):
    """Raised when the Web-configurable LeRobot feature layout is invalid."""


def default_lerobot_features_config() -> dict[str, Any]:
    return {
        "schema_version": DEFAULT_LEROBOT_FEATURES["schema_version"],
        "state_segments": [dict(item) for item in DEFAULT_LEROBOT_FEATURES["state_segments"]],
        "action_segments": [dict(item) for item in DEFAULT_LEROBOT_FEATURES["action_segments"]],
    }


def normalize_lerobot_features_config(data: Any | None) -> dict[str, Any]:
    raw = default_lerobot_features_config()
    if data is None:
        return raw
    if not isinstance(data, dict):
        raise LeRobotFeatureConfigError("lerobot_features must be a mapping")
    normalized = {
        "schema_version": int(data.get("schema_version", 1)),
        "state_segments": _normalize_segment_list(
            data.get("state_segments"),
            STATE_SEGMENT_DEFINITIONS,
            "state_segments",
        ),
        "action_segments": _normalize_segment_list(
            data.get("action_segments"),
            ACTION_SEGMENT_DEFINITIONS,
            "action_segments",
        ),
    }
    _require_enabled_tcp_segments(normalized)
    return normalized


def enabled_state_segments(config: Any | None) -> list[LeRobotFeatureSegment]:
    normalized = normalize_lerobot_features_config(config)
    return _enabled_segments(normalized["state_segments"], STATE_SEGMENT_DEFINITIONS)


def enabled_action_segments(config: Any | None) -> list[LeRobotFeatureSegment]:
    normalized = normalize_lerobot_features_config(config)
    return _enabled_segments(normalized["action_segments"], ACTION_SEGMENT_DEFINITIONS)


def lerobot_feature_schema(config: Any | None) -> dict[str, Any]:
    normalized = normalize_lerobot_features_config(config)
    state = _segment_schema(enabled_state_segments(normalized))
    action = _segment_schema(enabled_action_segments(normalized))
    return {
        "schema_version": "web_lerobot_features_v1",
        "config": normalized,
        "observation.state": {
            "shape": [sum(item["dim"] for item in state)],
            "segments": state,
        },
        "action": {
            "shape": [sum(item["dim"] for item in action)],
            "time_offset_steps": 1,
            "segments": action,
        },
    }


def tcp_pose_offsets(config: Any | None) -> dict[str, tuple[int, int]]:
    schema = lerobot_feature_schema(config)
    offsets: dict[str, tuple[int, int]] = {}
    for segment in schema["observation.state"]["segments"]:
        if segment["name"] in {"left_tcp_pose", "right_tcp_pose"}:
            start, end = segment["offset"]
            offsets[segment["name"]] = (int(start), int(end))
    return offsets


def _normalize_segment_list(
    value: Any,
    definitions: dict[str, LeRobotFeatureSegment],
    path: str,
) -> list[dict[str, Any]]:
    if value is None:
        defaults = STATE_SEGMENT_DEFINITIONS if path == "state_segments" else ACTION_SEGMENT_DEFINITIONS
        return [{"id": segment_id, "enabled": True} for segment_id in defaults]
    if not isinstance(value, list):
        raise LeRobotFeatureConfigError(f"{path} must be a list")
    seen: set[str] = set()
    result: list[dict[str, Any]] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise LeRobotFeatureConfigError(f"{path}[{index}] must be a mapping")
        segment_id = str(item.get("id", ""))
        if segment_id not in definitions:
            raise LeRobotFeatureConfigError(f"unknown {path} id: {segment_id}")
        if segment_id in seen:
            raise LeRobotFeatureConfigError(f"duplicate {path} id: {segment_id}")
        seen.add(segment_id)
        result.append({"id": segment_id, "enabled": bool(item.get("enabled", True))})
    for segment_id, spec in definitions.items():
        if segment_id not in seen:
            result.append({"id": segment_id, "enabled": spec.required})
    return result


def _require_enabled_tcp_segments(config: dict[str, Any]) -> None:
    required = {
        "state_segments": ("left_tcp_pose", "right_tcp_pose"),
        "action_segments": ("left_tcp_pose_t_plus_1", "right_tcp_pose_t_plus_1"),
    }
    for key, segment_ids in required.items():
        enabled = {item["id"] for item in config[key] if item["enabled"]}
        for segment_id in segment_ids:
            if segment_id not in enabled:
                raise LeRobotFeatureConfigError(f"{key}.{segment_id} is required")


def _enabled_segments(
    items: list[dict[str, Any]],
    definitions: dict[str, LeRobotFeatureSegment],
) -> list[LeRobotFeatureSegment]:
    return [definitions[item["id"]] for item in items if item["enabled"]]


def _segment_schema(segments: list[LeRobotFeatureSegment]) -> list[dict[str, Any]]:
    offset = 0
    result: list[dict[str, Any]] = []
    for segment in segments:
        end = offset + segment.dim
        result.append(
            {
                "name": segment.id,
                "source_field": segment.source_field,
                "offset": [offset, end],
                "dim": segment.dim,
                "unit": segment.unit,
                "semantic": segment.semantic,
                "required": segment.required,
                "components": list(segment.components),
                "time_offset_steps": segment.time_offset_steps,
            }
        )
        offset = end
    return result
