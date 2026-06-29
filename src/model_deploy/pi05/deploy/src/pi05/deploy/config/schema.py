"""Typed YAML configuration for Pi0.5 deployment.

Deployment config is intentionally separate from training config. Real robot
deployment consumes only an exported bundle plus runtime/ROS settings.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

import yaml

from pi05.common.ros.topics import DEFAULT_NAMESPACE, Pi05CommandTopics, Pi05ObservationTopics


class DeployConfigError(ValueError):
    """Raised when deploy YAML is missing required fields or has invalid values."""


@dataclass(frozen=True)
class BundleConfig:
    """Runtime model bundle location."""

    bundle_dir: Path

    @property
    def resolved_bundle_dir(self) -> Path:
        return self.bundle_dir.expanduser().resolve()


@dataclass(frozen=True)
class RuntimeConfig:
    """Policy runtime scheduling and device settings."""

    mode: str = "dry-run"
    device: str = "cuda:0"
    secondary_device: str | None = None
    multi_gpu_strategy: str = "none"
    dtype: str = "bfloat16"
    inference_hz: float = 10.0
    control_hz: float = 30.0
    chunk_size: int = 30
    execute_horizon: int = 10
    prefetch_steps: int = 5
    blend_steps: int = 3
    action_dim: int = 16
    state_dim: int = 16
    max_action_age_sec: float = 0.45
    max_inference_requests: int = 1
    max_pending_chunks: int = 1
    fallback_policy: str = "hold_last_action"
    max_delta_per_step: float = 0.03
    warmup_steps: int = 2
    compile_model: bool = True
    compile_mode: str = "reduce-overhead"
    publish_metrics_hz: float = 1.0
    task: str = "bimanual manipulation"

    @property
    def publishes_command_topics(self) -> bool:
        return self.mode in {"shadow-run", "safe-run"}

    def __post_init__(self) -> None:
        if self.control_hz <= 0.0:
            raise DeployConfigError("runtime.control_hz must be positive.")
        if self.inference_hz <= 0.0:
            raise DeployConfigError("runtime.inference_hz must be positive.")
        if self.prefetch_steps < 0:
            raise DeployConfigError("runtime.prefetch_steps must be >= 0.")
        if self.blend_steps < 0:
            raise DeployConfigError("runtime.blend_steps must be >= 0.")
        if self.execute_horizon > self.chunk_size:
            raise DeployConfigError(
                f"runtime.execute_horizon ({self.execute_horizon}) must be <= runtime.chunk_size ({self.chunk_size})."
            )
        if self.prefetch_steps > self.execute_horizon:
            raise DeployConfigError(
                f"runtime.prefetch_steps ({self.prefetch_steps}) must be <= runtime.execute_horizon ({self.execute_horizon})."
            )
        if self.max_action_age_sec <= 0.0:
            raise DeployConfigError("runtime.max_action_age_sec must be positive.")
        if self.max_inference_requests < 1:
            raise DeployConfigError("runtime.max_inference_requests must be >= 1.")
        if self.max_pending_chunks < 1:
            raise DeployConfigError("runtime.max_pending_chunks must be >= 1.")
        if self.fallback_policy not in {"hold_last_action", "continue_old_chunk", "safe_stop"}:
            raise DeployConfigError(
                "runtime.fallback_policy must be one of: hold_last_action, continue_old_chunk, safe_stop."
            )


@dataclass(frozen=True)
class ObservationTopicsConfig:
    """ROS input topics consumed by the observation collector.

    TO-BE fields: fisheye stereo cameras, left/right TCP pose,
    left/right gripper state, and tactile reserved (optional).
    """

    left_fisheye_image: str
    right_fisheye_image: str
    left_fisheye_image_raw: str
    right_fisheye_image_raw: str
    left_tcp_pose: str
    right_tcp_pose: str
    left_gripper_state: str
    right_gripper_state: str
    tactile_l1: str | None = None
    tactile_l2: str | None = None
    tactile_r1: str | None = None
    tactile_r2: str | None = None


@dataclass(frozen=True)
class CommandTopicsConfig:
    """ROS command and telemetry topics produced by deployment.

    TO-BE: single policy_action topic instead of four joint/hand targets.
    """

    policy_action: str
    status: str
    metrics: str





@dataclass(frozen=True)
class TopicsConfig:
    """All ROS topic names used by deployment."""

    namespace: str
    observation: ObservationTopicsConfig
    command: CommandTopicsConfig


@dataclass(frozen=True)
class JointLimitsConfig:
    """Optional arm joint limits in radians."""

    enabled: bool = False
    left_min_rad: tuple[float, ...] = field(default_factory=tuple)
    left_max_rad: tuple[float, ...] = field(default_factory=tuple)
    right_min_rad: tuple[float, ...] = field(default_factory=tuple)
    right_max_rad: tuple[float, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class SafetyConfig:
    """Runtime safety checks applied after policy inference.
    
    TO-BE: TCP/width checks instead of joint-space checks.
    JointLimitsConfig is preserved as bridge parameter source.
    """

    max_tcp_delta_m: float = 0.05
    stale_observation_timeout_s: float = 0.5
    command_timeout_s: float = 0.45
    clamp_normalized_action: bool = True
    hold_last_action: bool = True
    gripper_width_min: float = 0.0
    gripper_width_max: float = 1.0
    joint_limits: JointLimitsConfig = field(default_factory=JointLimitsConfig)


@dataclass(frozen=True)
class ImageConfig:
    """Deployment image preprocessing settings."""

    image_size: int = 224
    resize_mode: str = "resize_pad"
    transport: str = "raw"


@dataclass(frozen=True)
class DeployConfig:
    """Complete Pi0.5 deployment configuration."""

    bundle: BundleConfig
    runtime: RuntimeConfig
    image: ImageConfig
    topics: TopicsConfig
    safety: SafetyConfig
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any], *, base_dir: Path) -> "DeployConfig":
        return _deploy_from_mapping(cls, raw, base_dir=base_dir)


def load_deploy_config(path: str | Path) -> DeployConfig:
    """Load a deployment config from YAML."""
    config_path = Path(path).expanduser().resolve()
    with config_path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    if not isinstance(raw, Mapping):
        raise DeployConfigError(f"Deploy config root must be a mapping, got {type(raw).__name__}")
    return DeployConfig.from_mapping(raw, base_dir=config_path.parent)


def _deploy_from_mapping(cls: type[DeployConfig], raw: Mapping[str, Any], *, base_dir: Path) -> DeployConfig:
    root = _mapping(raw, "<root>")
    namespace = _str(_mapping(root.get("topics", {}), "topics"), "namespace", default=DEFAULT_NAMESPACE)
    default_obs = Pi05ObservationTopics.with_namespace(namespace)
    default_cmd = Pi05CommandTopics.with_namespace(namespace)

    bundle_raw = _required_mapping(root, "bundle")
    runtime_raw = _mapping(root.get("runtime", {}), "runtime")
    image_raw = _mapping(root.get("image", {}), "image")
    topics_raw = _mapping(root.get("topics", {}), "topics")
    safety_raw = _mapping(root.get("safety", {}), "safety")

    return cls(
        bundle=BundleConfig(bundle_dir=_path(bundle_raw, "bundle_dir", base_dir=base_dir)),
        runtime=RuntimeConfig(
            mode=_choice(runtime_raw, "mode", {"dry-run", "shadow-run", "safe-run"}, default="dry-run"),
            device=_str(runtime_raw, "device", default="cuda:0"),
            secondary_device=_optional_str(runtime_raw, "secondary_device"),
            multi_gpu_strategy=_choice(runtime_raw, "multi_gpu_strategy", {"none", "auto"}, default="none"),
            dtype=_choice(runtime_raw, "dtype", {"float32", "float16", "bfloat16"}, default="bfloat16"),
            inference_hz=_positive_float(runtime_raw, "inference_hz", default=10.0),
            control_hz=_positive_float(runtime_raw, "control_hz", default=30.0),
            chunk_size=_positive_int(runtime_raw, "chunk_size", default=30),
            execute_horizon=_positive_int(runtime_raw, "execute_horizon", default=10),
            prefetch_steps=_non_negative_int(runtime_raw, "prefetch_steps", default=5),
            blend_steps=_non_negative_int(runtime_raw, "blend_steps", default=_int_value(runtime_raw, "chunk_blend_steps", default=3)),
            action_dim=_positive_int(runtime_raw, "action_dim", default=16),
            state_dim=_positive_int(runtime_raw, "state_dim", default=16),
            max_action_age_sec=_positive_float(runtime_raw, "max_action_age_sec", default=0.45),
            max_inference_requests=_positive_int(runtime_raw, "max_inference_requests", default=1),
            max_pending_chunks=_positive_int(runtime_raw, "max_pending_chunks", default=1),
            fallback_policy=_choice(
                runtime_raw,
                "fallback_policy",
                {"hold_last_action", "continue_old_chunk", "safe_stop"},
                default="hold_last_action",
            ),
            max_delta_per_step=_positive_float(runtime_raw, "max_delta_per_step", default=0.03),
            warmup_steps=_non_negative_int(runtime_raw, "warmup_steps", default=2),
            compile_model=_bool(runtime_raw, "compile_model", default=True),
            compile_mode=_str(runtime_raw, "compile_mode", default="reduce-overhead"),
            publish_metrics_hz=_positive_float(runtime_raw, "publish_metrics_hz", default=1.0),
            task=_str(runtime_raw, "task", default="bimanual manipulation"),
        ),
        image=ImageConfig(
            image_size=_positive_int(image_raw, "image_size", default=224),
            resize_mode=_choice(image_raw, "resize_mode", {"resize_pad", "resize_crop"}, default="resize_pad"),
            transport=_choice(image_raw, "transport", {"raw", "compressed", "both"}, default="raw"),
        ),
        topics=TopicsConfig(
            namespace=namespace,
            observation=_observation_topics(topics_raw, default_obs),
            command=_command_topics(topics_raw, default_cmd),
        ),
        safety=_safety_config(safety_raw, runtime_raw=runtime_raw),
        raw=dict(root),
    )

def _observation_topics(topics_raw: Mapping[str, Any], defaults: Pi05ObservationTopics) -> ObservationTopicsConfig:
    raw = _mapping(topics_raw.get("observation", {}), "topics.observation")
    return ObservationTopicsConfig(
        left_fisheye_image=_str(raw, "left_fisheye_image", default=defaults.left_fisheye_image),
        right_fisheye_image=_str(raw, "right_fisheye_image", default=defaults.right_fisheye_image),
        left_fisheye_image_raw=_str(raw, "left_fisheye_image_raw", default=defaults.left_fisheye_image.removesuffix("/compressed")),
        right_fisheye_image_raw=_str(raw, "right_fisheye_image_raw", default=defaults.right_fisheye_image.removesuffix("/compressed")),
        left_tcp_pose=_str(raw, "left_tcp_pose", default=defaults.left_tcp_pose),
        right_tcp_pose=_str(raw, "right_tcp_pose", default=defaults.right_tcp_pose),
        left_gripper_state=_str(raw, "left_gripper_state", default=defaults.left_gripper_state),
        right_gripper_state=_str(raw, "right_gripper_state", default=defaults.right_gripper_state),
        tactile_l1=_optional_str(raw, "tactile_l1"),
        tactile_l2=_optional_str(raw, "tactile_l2"),
        tactile_r1=_optional_str(raw, "tactile_r1"),
        tactile_r2=_optional_str(raw, "tactile_r2"),
    )


def _command_topics(topics_raw: Mapping[str, Any], defaults: Pi05CommandTopics) -> CommandTopicsConfig:
    raw = _mapping(topics_raw.get("command", {}), "topics.command")
    return CommandTopicsConfig(
        policy_action=_str(raw, "policy_action", default=defaults.policy_action),
        status=_str(raw, "status", default=defaults.status),
        metrics=_str(raw, "metrics", default=defaults.metrics),
    )





def _safety_config(raw: Mapping[str, Any], *, runtime_raw: Mapping[str, Any]) -> SafetyConfig:
    limits_raw = _mapping(raw.get("joint_limits", {}), "safety.joint_limits")
    return SafetyConfig(
        max_tcp_delta_m=_float(
            raw,
            "max_tcp_delta_m",
            default=_float(runtime_raw, "max_delta_per_step", default=0.03),
        ),
        stale_observation_timeout_s=_positive_float(raw, "stale_observation_timeout_s", default=0.5),
        command_timeout_s=_positive_float(raw, "command_timeout_s", default=0.45),
        clamp_normalized_action=_bool(raw, "clamp_normalized_action", default=True),
        hold_last_action=_bool(raw, "hold_last_action", default=True),
        gripper_width_min=_float(raw, "gripper_width_min", default=0.0),
        gripper_width_max=_float(raw, "gripper_width_max", default=1.0),
        joint_limits=JointLimitsConfig(
            enabled=_bool(limits_raw, "enabled", default=False),
            left_min_rad=tuple(_float_list(limits_raw, "left_min_rad", default=[])),
            left_max_rad=tuple(_float_list(limits_raw, "left_max_rad", default=[])),
            right_min_rad=tuple(_float_list(limits_raw, "right_min_rad", default=[])),
            right_max_rad=tuple(_float_list(limits_raw, "right_max_rad", default=[])),
        ),
    )


def _required_mapping(raw: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    if key not in raw:
        raise DeployConfigError(f"Missing required deploy config section: {key}")
    return _mapping(raw[key], key)


def _mapping(value: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise DeployConfigError(f"{name} must be a mapping, got {type(value).__name__}")
    return value


def _path(raw: Mapping[str, Any], key: str, *, base_dir: Path) -> Path:
    value = _str(raw, key)
    path = Path(value).expanduser()
    return path if path.is_absolute() else (base_dir / path)


def _str(raw: Mapping[str, Any], key: str, default: str | None = None) -> str:
    if key not in raw:
        if default is None:
            raise DeployConfigError(f"Missing required deploy config value: {key}")
        return default
    value = raw[key]
    if not isinstance(value, str):
        raise DeployConfigError(f"{key} must be a string, got {type(value).__name__}")
    return value


def _optional_str(raw: Mapping[str, Any], key: str) -> str | None:
    value = raw.get(key)
    if value in (None, ""):
        return None
    if not isinstance(value, str):
        raise DeployConfigError(f"{key} must be a string or null, got {type(value).__name__}")
    return value


def _choice(raw: Mapping[str, Any], key: str, choices: set[str], default: str) -> str:
    value = _str(raw, key, default=default)
    if value not in choices:
        raise DeployConfigError(f"{key} must be one of {sorted(choices)}, got {value!r}")
    return value


def _bool(raw: Mapping[str, Any], key: str, default: bool) -> bool:
    if key not in raw:
        return default
    value = raw[key]
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"1", "true", "yes", "y", "on"}:
            return True
        if lowered in {"0", "false", "no", "n", "off"}:
            return False
    raise DeployConfigError(f"{key} must be a boolean, got {value!r}")


def _positive_int(raw: Mapping[str, Any], key: str, default: int) -> int:
    value = int(raw.get(key, default))
    if value <= 0:
        raise DeployConfigError(f"{key} must be positive, got {value}")
    return value


def _non_negative_int(raw: Mapping[str, Any], key: str, default: int) -> int:
    value = int(raw.get(key, default))
    if value < 0:
        raise DeployConfigError(f"{key} must be non-negative, got {value}")
    return value


def _int_value(raw: Mapping[str, Any], key: str, default: int) -> int:
    return int(raw.get(key, default))


def _float(raw: Mapping[str, Any], key: str, default: float) -> float:
    try:
        return float(raw.get(key, default))
    except (TypeError, ValueError) as exc:
        raise DeployConfigError(f"{key} must be a float") from exc


def _positive_float(raw: Mapping[str, Any], key: str, default: float) -> float:
    value = _float(raw, key, default)
    if value <= 0.0:
        raise DeployConfigError(f"{key} must be positive, got {value}")
    return value


def _float_list(raw: Mapping[str, Any], key: str, default: list[float]) -> list[float]:
    value = raw.get(key, default)
    if not isinstance(value, list):
        raise DeployConfigError(f"{key} must be a list of floats")
    return [float(item) for item in value]
