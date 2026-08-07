"""The canonical LeRobot feature contract used by data-clean.

The raw configuration is intentionally small and user-facing.  Every producer
must consume :func:`compile_lerobot_feature_contract`; this keeps dimension
order, names, offsets and provenance in one place.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re
from typing import Any, Mapping


MACHINE_NAME_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+$")
FEATURE_SCHEMA_VERSION = "compiled_lerobot_feature_contract_v2"


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
    default_display_name: str = ""
    group: str = ""
    data_role: str = ""
    default_dimension_names: tuple[str, ...] = ()

    @property
    def display_name(self) -> str:
        return self.default_display_name or self.id

    @property
    def dimension_names(self) -> tuple[str, ...]:
        return self.default_dimension_names or tuple(
            f"{self.id}.{component}" for component in self.components
        )


def _segment(
    *,
    id: str,
    source_field: str,
    dim: int,
    unit: str,
    semantic: str,
    required: bool,
    components: tuple[str, ...],
    time_offset_steps: int = 0,
    display_name: str,
    group: str,
    data_role: str,
) -> LeRobotFeatureSegment:
    return LeRobotFeatureSegment(
        id=id,
        source_field=source_field,
        dim=dim,
        unit=unit,
        semantic=semantic,
        required=required,
        components=components,
        time_offset_steps=time_offset_steps,
        default_display_name=display_name,
        group=group,
        data_role=data_role,
        default_dimension_names=tuple(f"{id}.{component}" for component in components),
    )


STATE_SEGMENT_DEFINITIONS: dict[str, LeRobotFeatureSegment] = {
    "left_tcp_pose": _segment(
        id="left_tcp_pose", source_field="left_tcp_pose", dim=7,
        unit="m + quaternion_xyzw",
        semantic="left TCP pose in the original Baton source frame at step t",
        required=True, components=("x", "y", "z", "qx", "qy", "qz", "qw"),
        display_name="左 TCP 位姿", group="tcp_pose", data_role="state",
    ),
    "right_tcp_pose": _segment(
        id="right_tcp_pose", source_field="right_tcp_pose", dim=7,
        unit="m + quaternion_xyzw",
        semantic="right TCP pose in the original Baton source frame at step t",
        required=True, components=("x", "y", "z", "qx", "qy", "qz", "qw"),
        display_name="右 TCP 位姿", group="tcp_pose", data_role="state",
    ),
    "left_gripper_width": _segment(
        id="left_gripper_width", source_field="left_gripper_width", dim=1,
        unit="normalized_0_to_1", semantic="left gripper width at step t",
        required=False, components=("width",),
        display_name="左夹爪宽度", group="gripper", data_role="state",
    ),
    "right_gripper_width": _segment(
        id="right_gripper_width", source_field="right_gripper_width", dim=1,
        unit="normalized_0_to_1", semantic="right gripper width at step t",
        required=False, components=("width",),
        display_name="右夹爪宽度", group="gripper", data_role="state",
    ),
    "tactile_left_gripper_1": _segment(
        id="tactile_left_gripper_1", source_field="tactile_left_gripper_1", dim=4,
        unit="mean_std_min_max", semantic="left gripper tactile sensor 1 summary at step t",
        required=False, components=("mean", "std", "min", "max"),
        display_name="左夹爪触觉 1", group="tactile", data_role="state",
    ),
    "tactile_left_gripper_2": _segment(
        id="tactile_left_gripper_2", source_field="tactile_left_gripper_2", dim=4,
        unit="mean_std_min_max", semantic="left gripper tactile sensor 2 summary at step t",
        required=False, components=("mean", "std", "min", "max"),
        display_name="左夹爪触觉 2", group="tactile", data_role="state",
    ),
    "tactile_right_gripper_1": _segment(
        id="tactile_right_gripper_1", source_field="tactile_right_gripper_1", dim=4,
        unit="mean_std_min_max", semantic="right gripper tactile sensor 1 summary at step t",
        required=False, components=("mean", "std", "min", "max"),
        display_name="右夹爪触觉 1", group="tactile", data_role="state",
    ),
    "tactile_right_gripper_2": _segment(
        id="tactile_right_gripper_2", source_field="tactile_right_gripper_2", dim=4,
        unit="mean_std_min_max", semantic="right gripper tactile sensor 2 summary at step t",
        required=False, components=("mean", "std", "min", "max"),
        display_name="右夹爪触觉 2", group="tactile", data_role="state",
    ),
}

ACTION_SEGMENT_DEFINITIONS: dict[str, LeRobotFeatureSegment] = {
    "left_tcp_pose_t_plus_1": _segment(
        id="left_tcp_pose_t_plus_1", source_field="left_tcp_pose", dim=7,
        unit="m + quaternion_xyzw",
        semantic="left source-frame absolute TCP target pose at step t+1",
        required=True, components=("x", "y", "z", "qx", "qy", "qz", "qw"),
        time_offset_steps=1, display_name="左 TCP 目标位姿 (t+1)",
        group="tcp_pose", data_role="action",
    ),
    "left_gripper_width_t_plus_1": _segment(
        id="left_gripper_width_t_plus_1", source_field="left_gripper_width", dim=1,
        unit="normalized_0_to_1", semantic="left gripper target width at step t+1",
        required=False, components=("width",), time_offset_steps=1,
        display_name="左夹爪目标宽度 (t+1)", group="gripper", data_role="action",
    ),
    "right_tcp_pose_t_plus_1": _segment(
        id="right_tcp_pose_t_plus_1", source_field="right_tcp_pose", dim=7,
        unit="m + quaternion_xyzw",
        semantic="right source-frame absolute TCP target pose at step t+1",
        required=True, components=("x", "y", "z", "qx", "qy", "qz", "qw"),
        time_offset_steps=1, display_name="右 TCP 目标位姿 (t+1)",
        group="tcp_pose", data_role="action",
    ),
    "right_gripper_width_t_plus_1": _segment(
        id="right_gripper_width_t_plus_1", source_field="right_gripper_width", dim=1,
        unit="normalized_0_to_1", semantic="right gripper target width at step t+1",
        required=False, components=("width",), time_offset_steps=1,
        display_name="右夹爪目标宽度 (t+1)", group="gripper", data_role="action",
    ),
}


@dataclass(frozen=True)
class CompiledFeatureDimension:
    index: int
    name: str
    segment_id: str
    component: str
    source_field: str
    unit: str
    semantic: str
    display_name: str
    group: str
    data_role: str
    time_offset_steps: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "index": self.index, "name": self.name, "segment_id": self.segment_id,
            "component": self.component, "source_field": self.source_field,
            "unit": self.unit, "semantic": self.semantic,
            "display_name": self.display_name, "group": self.group,
            "data_role": self.data_role, "time_offset_steps": self.time_offset_steps,
        }


@dataclass(frozen=True)
class CompiledFeatureLayout:
    key: str
    dimensions: tuple[CompiledFeatureDimension, ...]
    segments: tuple[LeRobotFeatureSegment, ...]

    @property
    def dim(self) -> int:
        return len(self.dimensions)

    @property
    def shape(self) -> tuple[int]:
        return (self.dim,)

    @property
    def names(self) -> tuple[str, ...]:
        return tuple(item.name for item in self.dimensions)

    @property
    def dimension_names(self) -> tuple[str, ...]:
        return self.names

    @property
    def total_dim(self) -> int:
        return self.dim

    @property
    def offsets(self) -> dict[str, tuple[int, int]]:
        return {
            segment.id: (
                _segment_offset(self, segment.id),
                _segment_offset(self, segment.id) + segment.dim,
            )
            for segment in self.segments
        }

    @property
    def fingerprint_payload(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "shape": list(self.shape),
            "segments": [
                {
                    "id": segment.id,
                    "source_field": segment.source_field,
                    "dim": segment.dim,
                    "unit": segment.unit,
                    "semantic": segment.semantic,
                    "required": segment.required,
                    "components": list(segment.components),
                    "time_offset_steps": segment.time_offset_steps,
                    "display_name": segment.display_name,
                    "group": segment.group,
                    "data_role": segment.data_role,
                    "dimension_names": list(
                        self.names[_segment_offset(self, segment.id):
                                   _segment_offset(self, segment.id) + segment.dim]
                    ),
                }
                for segment in self.segments
            ],
            "dimensions": [item.to_dict() for item in self.dimensions],
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.key,
            "shape": list(self.shape),
            "dim": self.dim,
            "names": list(self.names),
            "dimensions": [item.to_dict() for item in self.dimensions],
            "segments": [
                {
                    "id": segment.id,
                    "source_field": segment.source_field,
                    "offset": [
                        _segment_offset(self, segment.id),
                        _segment_offset(self, segment.id) + segment.dim,
                    ],
                    "dim": segment.dim,
                    "unit": segment.unit,
                    "semantic": segment.semantic,
                    "display_name": segment.display_name,
                    "group": segment.group,
                    "data_role": segment.data_role,
                    "required": segment.required,
                    "components": list(segment.components),
                    "time_offset_steps": segment.time_offset_steps,
                    "dimension_names": list(
                        self.names[_segment_offset(self, segment.id):
                                   _segment_offset(self, segment.id) + segment.dim]
                    ),
                }
                for segment in self.segments
            ],
        }


@dataclass(frozen=True)
class CompiledLeRobotFeatureContract:
    schema_version: str
    config: dict[str, Any]
    state: CompiledFeatureLayout
    action: CompiledFeatureLayout
    fingerprint: str

    @property
    def contract_fingerprint(self) -> str:
        return self.fingerprint

    @property
    def state_layout(self) -> CompiledFeatureLayout:
        return self.state

    @property
    def action_layout(self) -> CompiledFeatureLayout:
        return self.action

    @property
    def state_dim(self) -> int:
        return self.state.dim

    @property
    def action_dim(self) -> int:
        return self.action.dim

    @property
    def state_names(self) -> tuple[str, ...]:
        return self.state.names

    @property
    def action_names(self) -> tuple[str, ...]:
        return self.action.names

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "config": self.config,
            "observation.state": self.state.to_dict(),
            "action": self.action.to_dict(),
            "state": self.state.to_dict(),
            "contract_fingerprint": self.fingerprint,
            "fingerprint": self.fingerprint,
        }


class LeRobotFeatureConfigError(ValueError):
    """Raised when the Web-configurable LeRobot feature layout is invalid."""


DEFAULT_LEROBOT_FEATURES = {
    "schema_version": 2,
    "state_segments": [
        {
            "id": segment_id,
            "enabled": True,
            "dimension_names": list(segment.dimension_names),
        }
        for segment_id, segment in STATE_SEGMENT_DEFINITIONS.items()
    ],
    "action_segments": [
        {
            "id": segment_id,
            "enabled": True,
            "dimension_names": list(segment.dimension_names),
        }
        for segment_id, segment in ACTION_SEGMENT_DEFINITIONS.items()
    ],
}


def default_lerobot_features_config() -> dict[str, Any]:
    return json.loads(json.dumps(DEFAULT_LEROBOT_FEATURES, ensure_ascii=False))


def normalize_lerobot_features_config(data: Any | None) -> dict[str, Any]:
    """Migrate v1 layouts and validate the complete v2 user-facing config."""

    if data is None:
        raw = default_lerobot_features_config()
    elif not isinstance(data, Mapping):
        raise LeRobotFeatureConfigError("lerobot_features must be a mapping")
    else:
        raw = dict(data)

    try:
        source_version = int(raw.get("schema_version", 1))
    except (TypeError, ValueError) as exc:
        raise LeRobotFeatureConfigError("schema_version must be an integer") from exc
    if source_version not in {1, 2}:
        raise LeRobotFeatureConfigError(f"unsupported lerobot_features schema_version: {source_version}")

    normalized = {
        "schema_version": 2,
        "state_segments": _normalize_segment_list(
            raw.get("state_segments"), STATE_SEGMENT_DEFINITIONS, "state_segments",
            require_explicit_names=source_version == 2,
        ),
        "action_segments": _normalize_segment_list(
            raw.get("action_segments"), ACTION_SEGMENT_DEFINITIONS, "action_segments",
            require_explicit_names=source_version == 2,
        ),
    }
    _require_enabled_tcp_segments(normalized)
    _validate_layout_names(normalized)
    return normalized


def compile_lerobot_feature_contract(
    config: Any | None = None,
) -> CompiledLeRobotFeatureContract:
    normalized = normalize_lerobot_features_config(config)
    state = _compile_layout("observation.state", normalized["state_segments"], STATE_SEGMENT_DEFINITIONS)
    action = _compile_layout("action", normalized["action_segments"], ACTION_SEGMENT_DEFINITIONS)
    payload = {
        "schema_version": FEATURE_SCHEMA_VERSION,
        "config": normalized,
        "observation.state": state.fingerprint_payload,
        "action": action.fingerprint_payload,
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    fingerprint = hashlib.sha256(encoded).hexdigest()
    return CompiledLeRobotFeatureContract(
        schema_version=FEATURE_SCHEMA_VERSION,
        config=normalized,
        state=state,
        action=action,
        fingerprint=fingerprint,
    )


def enabled_state_segments(config: Any | None) -> list[LeRobotFeatureSegment]:
    return list(compile_lerobot_feature_contract(config).state.segments)


def enabled_action_segments(config: Any | None) -> list[LeRobotFeatureSegment]:
    return list(compile_lerobot_feature_contract(config).action.segments)


def lerobot_feature_schema(config: Any | None) -> dict[str, Any]:
    contract = compile_lerobot_feature_contract(config)
    return {
        "schema_version": contract.schema_version,
        "config": contract.config,
        "contract_fingerprint": contract.fingerprint,
        "fingerprint": contract.fingerprint,
        "observation.state": contract.state.to_dict(),
        "action": {
            **contract.action.to_dict(),
            "time_offset_steps": 1,
        },
    }


def tcp_pose_offsets(config: Any | None) -> dict[str, tuple[int, int]]:
    contract = compile_lerobot_feature_contract(config)
    offsets: dict[str, tuple[int, int]] = {}
    for segment in contract.state.segments:
        if segment.id in {"left_tcp_pose", "right_tcp_pose"}:
            start = _segment_offset(contract.state, segment.id)
            offsets[segment.id] = (start, start + segment.dim)
    return offsets


def _normalize_segment_list(
    value: Any,
    definitions: dict[str, LeRobotFeatureSegment],
    path: str,
    *,
    require_explicit_names: bool,
) -> list[dict[str, Any]]:
    if value is None:
        if require_explicit_names:
            raise LeRobotFeatureConfigError(f"{path} must be explicitly saved in schema_version 2")
        value = [
            {"id": segment_id, "enabled": True}
            for segment_id in definitions
        ]
    if not isinstance(value, list):
        raise LeRobotFeatureConfigError(f"{path} must be a list")
    seen: set[str] = set()
    result: list[dict[str, Any]] = []
    for index, item in enumerate(value):
        if not isinstance(item, Mapping):
            raise LeRobotFeatureConfigError(f"{path}[{index}] must be a mapping")
        segment_id = str(item.get("id", ""))
        if segment_id not in definitions:
            raise LeRobotFeatureConfigError(f"unknown {path} id: {segment_id}")
        if segment_id in seen:
            raise LeRobotFeatureConfigError(f"duplicate {path} id: {segment_id}")
        seen.add(segment_id)
        definition = definitions[segment_id]
        enabled = bool(item.get("enabled", True))
        names_value = item.get("dimension_names", item.get("names"))
        if names_value is None:
            if require_explicit_names:
                raise LeRobotFeatureConfigError(f"{path}[{index}].dimension_names must be explicit")
            names = list(definition.dimension_names)
        elif not isinstance(names_value, list):
            raise LeRobotFeatureConfigError(f"{path}[{index}].dimension_names must be a list")
        else:
            names = [str(name) for name in names_value]
        if len(names) != definition.dim:
            raise LeRobotFeatureConfigError(
                f"{path}[{index}].dimension_names must contain {definition.dim} names"
            )
        entry: dict[str, Any] = {
            "id": segment_id,
            "enabled": enabled,
            "dimension_names": names,
            "display_name": str(item.get("display_name", definition.display_name)),
            "semantic": str(item.get("semantic", definition.semantic)),
            "unit": str(item.get("unit", definition.unit)),
            "group": str(item.get("group", definition.group)),
            "data_role": str(item.get("data_role", definition.data_role)),
        }
        result.append(entry)
    for segment_id, definition in definitions.items():
        if segment_id not in seen:
            if require_explicit_names:
                raise LeRobotFeatureConfigError(f"{path} missing segment: {segment_id}")
            result.append({
                "id": segment_id,
                "enabled": definition.required,
                "dimension_names": list(definition.dimension_names),
                "display_name": definition.display_name,
                "semantic": definition.semantic,
                "unit": definition.unit,
                "group": definition.group,
                "data_role": definition.data_role,
            })
    return result


def _validate_layout_names(config: dict[str, Any]) -> None:
    for path in ("state_segments", "action_segments"):
        names: list[str] = []
        for index, item in enumerate(config[path]):
            for name_index, name in enumerate(item["dimension_names"]):
                if not name or not MACHINE_NAME_PATTERN.fullmatch(name):
                    raise LeRobotFeatureConfigError(
                        f"{path}[{index}].dimension_names[{name_index}] must use ASCII letters, numbers, _, ., or -"
                    )
                names.append(name)
        duplicates = sorted({name for name in names if names.count(name) > 1})
        if duplicates:
            raise LeRobotFeatureConfigError(f"duplicate dimension names in {path}: {duplicates}")


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


def _compile_layout(
    key: str,
    items: list[dict[str, Any]],
    definitions: dict[str, LeRobotFeatureSegment],
) -> CompiledFeatureLayout:
    dimensions: list[CompiledFeatureDimension] = []
    segments: list[LeRobotFeatureSegment] = []
    for item in items:
        if not item["enabled"]:
            continue
        definition = definitions[item["id"]]
        segment = LeRobotFeatureSegment(
            **{
                **definition.__dict__,
                "unit": item.get("unit", definition.unit),
                "semantic": item.get("semantic", definition.semantic),
                "default_display_name": item.get("display_name", definition.display_name),
                "group": item.get("group", definition.group),
                "data_role": item.get("data_role", definition.data_role),
                "default_dimension_names": tuple(item["dimension_names"]),
            }
        )
        segments.append(segment)
        offset = len(dimensions)
        for component_index, component in enumerate(segment.components):
            dimensions.append(
                CompiledFeatureDimension(
                    index=offset + component_index,
                    name=segment.dimension_names[component_index],
                    segment_id=segment.id,
                    component=component,
                    source_field=segment.source_field,
                    unit=segment.unit,
                    semantic=segment.semantic,
                    display_name=segment.display_name,
                    group=segment.group,
                    data_role=segment.data_role,
                    time_offset_steps=segment.time_offset_steps,
                )
            )
    return CompiledFeatureLayout(key=key, dimensions=tuple(dimensions), segments=tuple(segments))


def _segment_offset(layout: CompiledFeatureLayout, segment_id: str) -> int:
    for dimension in layout.dimensions:
        if dimension.segment_id == segment_id:
            return dimension.index
    raise KeyError(segment_id)
