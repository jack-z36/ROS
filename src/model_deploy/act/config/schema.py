"""ACT deployment configuration — typed schema, validators, assembly,
contract cross-validation, and YAML loading orchestration.

Provides frozen dataclasses (deploy_008), ``from_mapping`` (deploy_008),
``check_bundle_contract`` / ``check_normalizer_contract`` (deploy_009),
``load_deploy_config`` (deploy_009), and C7 ``CommandOutputConfig``
(deploy_041).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence, Tuple

import yaml

from model_deploy.act.repo.bundle_reader import (
    BUNDLE_SCHEMA_VERSION,
    check_bundle_files,
    resolve_checkpoint_path,
)
from model_deploy.act.repo.experiment_config_loader import (
    EXPERIMENT_CONFIG_NAME,
    load_experiment_config,
)
from model_deploy.act.repo.manifest_parser import load_bundle_manifest
from model_deploy.act.repo.normalization import ActionStateNormalizer
from model_deploy.act.repo.normalizer_loader import load_bundle_normalizers
from model_deploy.act.types.contract_result import (
    BundleContractResult,
    NormalizerContractResult,
)


# ---------------------------------------------------------------------------
# Exception
# ---------------------------------------------------------------------------


class DeployConfigError(ValueError):
    """Raised when deploy config is missing required fields or has invalid values."""


# ---------------------------------------------------------------------------
# Frozen dataclasses — configuration sections
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class BundleConfig:
    """Runtime model bundle location.

    ``bundle_dir`` may be ``None`` to support the default config and a
    controlled fake harness.  A ``None`` bundle means "no production resource
    loader" — ``load_act_runtime_resources`` must then fail fast rather than
    guess a path (deploy_056 / P0-01).
    """

    bundle_dir: Path | None

    @property
    def resolved_bundle_dir(self) -> Path | None:
        if self.bundle_dir is None:
            return None
        return self.bundle_dir.expanduser().resolve()


@dataclass(frozen=True)
class RuntimeConfig:
    """Policy runtime scheduling and device settings.

    Action-smoothing fields are intentionally absent — the first ACT version
    does not implement action smoothing.
    """

    mode: str = "dry-run"
    device: str = "cuda:0"
    inference_hz: float = 10.0
    control_hz: float = 30.0
    chunk_size: int = 30
    execute_horizon: int = 10
    prefetch_steps: int = 5
    action_dim: int = 16
    state_dim: int = 16
    max_action_age_sec: float = 0.45
    max_observation_age_sec: float = 1.0
    max_inference_requests: int = 1
    max_pending_chunks: int = 1
    fallback_policy: str = "hold_last_action"
    max_delta_per_step: float = 0.01
    warmup_steps: int = 2
    compile_model: bool = True
    compile_mode: str = "reduce-overhead"
    publish_metrics_hz: float = 1.0
    task: str = "bimanual manipulation"
    # Optional physical-response motion contract for real-run.  Keep the
    # schema default conservative; a deployment config must opt out explicitly.
    response_motion_check_enabled: bool = True
    response_timeout_sec: float = 0.5
    hold_window_sec: float = 0.2
    epsilon_move_translation_m: float = 0.001
    epsilon_move_rotation_rad: float = 0.01
    epsilon_move_gripper: float = 0.01
    epsilon_hold_translation_m: float = 0.001
    epsilon_hold_rotation_rad: float = 0.01
    epsilon_hold_gripper: float = 0.01

    @property
    def publishes_command_topics(self) -> bool:
        return self.mode == "real-run"

    def __post_init__(self) -> None:
        if self.mode not in {"dry-run", "real-run"}:
            raise DeployConfigError(
                "runtime.mode must be one of: dry-run, real-run."
            )
        if self.control_hz <= 0.0:
            raise DeployConfigError("runtime.control_hz must be positive.")
        if self.inference_hz <= 0.0:
            raise DeployConfigError("runtime.inference_hz must be positive.")
        if self.prefetch_steps < 0:
            raise DeployConfigError("runtime.prefetch_steps must be >= 0.")
        if self.execute_horizon > self.chunk_size:
            raise DeployConfigError(
                f"runtime.execute_horizon ({self.execute_horizon}) must be <= "
                f"runtime.chunk_size ({self.chunk_size})."
            )
        if self.prefetch_steps > self.execute_horizon:
            raise DeployConfigError(
                f"runtime.prefetch_steps ({self.prefetch_steps}) must be <= "
                f"runtime.execute_horizon ({self.execute_horizon})."
            )
        if self.max_action_age_sec <= 0.0:
            raise DeployConfigError("runtime.max_action_age_sec must be positive.")
        if self.max_observation_age_sec <= 0.0:
            raise DeployConfigError("runtime.max_observation_age_sec must be positive.")
        if self.max_inference_requests != 1:
            raise DeployConfigError(
                "runtime.max_inference_requests must be exactly 1 "
                "(single in-flight inference request)."
            )
        if self.max_pending_chunks != 1:
            raise DeployConfigError(
                "runtime.max_pending_chunks must be exactly 1 (single pending chunk)."
            )
        if self.fallback_policy not in {"hold_last_action", "continue_old_chunk", "safe_stop"}:
            raise DeployConfigError(
                "runtime.fallback_policy must be one of: "
                "hold_last_action, continue_old_chunk, safe_stop."
            )
        response_values = (
            self.response_timeout_sec,
            self.hold_window_sec,
            self.epsilon_move_translation_m,
            self.epsilon_move_rotation_rad,
            self.epsilon_move_gripper,
            self.epsilon_hold_translation_m,
            self.epsilon_hold_rotation_rad,
            self.epsilon_hold_gripper,
        )
        if any(not math.isfinite(float(v)) or float(v) < 0.0 for v in response_values):
            raise DeployConfigError("runtime response thresholds must be finite and non-negative")
        if self.response_timeout_sec <= 0.0 or self.hold_window_sec <= 0.0:
            raise DeployConfigError(
                "runtime.response_timeout_sec and runtime.hold_window_sec must be positive"
            )
        if not isinstance(self.response_motion_check_enabled, bool):
            raise DeployConfigError(
                "runtime.response_motion_check_enabled must be bool"
            )


# Canonical logical policy camera keys that every observation config must ship.
_CANONICAL_CAMERA_KEYS: tuple[str, ...] = ("left", "right")

# Default canonical camera key -> ROS topic mapping (kept in sync with the
# legacy left_image / right_image default values for backward compatibility).
_DEFAULT_IMAGE_MAPPING: tuple[tuple[str, str], ...] = (
    ("left", "/act/observation/image/left_gripper_fisheye"),
    ("right", "/act/observation/image/right_gripper_fisheye"),
)


@dataclass(frozen=True)
class ObservationTopicsConfig:
    """ROS input topics consumed by the observation collector (ACT namespace).

    ``images`` is the canonical, read-only logical policy camera key -> ROS
    topic mapping (deploy_056 / P0-09-config).  The legacy ``left_image`` /
    ``right_image`` fields are retained so existing code keeps importing them,
    but a real config must use ``images``; the loader rejects mixing the two
    or omitting the canonical ``images`` mapping.
    """

    arm_state: str = "/act/observation/arm_state"
    left_image: str = "/act/observation/image/left_gripper_fisheye"
    right_image: str = "/act/observation/image/right_gripper_fisheye"
    left_tcp_pose: str = "/act/observation/arm/left_tcp_pose"
    right_tcp_pose: str = "/act/observation/arm/right_tcp_pose"
    left_gripper_state: str = "/act/observation/gripper/left_state"
    right_gripper_state: str = "/act/observation/gripper/right_state"
    images: tuple[tuple[str, str], ...] = field(default=_DEFAULT_IMAGE_MAPPING)

    @property
    def image_topics(self) -> dict[str, str]:
        return {key: topic for key, topic in self.images}

    @property
    def camera_keys(self) -> tuple[str, ...]:
        return tuple(key for key, _ in self.images)


@dataclass(frozen=True)
class CommandTopicsConfig:
    """ROS command and telemetry topics produced by deployment (ACT namespace)."""

    policy_action: str = "/act/policy_action"
    left_arm_target: str = "/act/command/arm/left_target"
    right_arm_target: str = "/act/command/arm/right_target"
    left_gripper_target: str = "/act/command/gripper/left_target"
    right_gripper_target: str = "/act/command/gripper/right_target"
    status: str = "/act/command/status"
    metrics: str = "/act/metrics"


@dataclass(frozen=True)
class TopicsConfig:
    """All ROS topic names used by ACT deployment."""

    namespace: str = "/act"
    observation: ObservationTopicsConfig = field(default_factory=ObservationTopicsConfig)
    command: CommandTopicsConfig = field(default_factory=CommandTopicsConfig)


# Legacy SafetyConfig YAML keys removed in deploy_032 (destructive migration).
# Callers must use the ActionDomain-aligned field names below.
_SAFETY_LEGACY_KEYS = frozenset(
    {
        "max_tcp_delta_per_step",
        "hand_min",
        "hand_max",
        "quaternion_check",
    }
)


@dataclass(frozen=True)
class SafetyConfig:
    """Runtime safety policy applied after policy inference (ACT version).

    Thresholds are in the deployment ActionDomain:
    - translation in meters, rotation in radians
    - gripper range/step in the same domain as ActionSpec gripper (default 0~1)
    - quaternion_norm_tolerance is unitless

    Joint limits, F100 register domains (e.g. 0~100 / 300~1000), and
    bridge/mux fields are intentionally absent.
    """

    max_translation_step_m: float = 0.01
    max_rotation_step_rad: float = 0.05
    gripper_min: float = 0.0
    gripper_max: float = 1.0
    max_gripper_step: float = 0.2
    quaternion_norm_tolerance: float = 1e-3
    pose_frame: str = "base"
    quaternion_order: str = "xyzw"
    gripper_domain: str = "normalized_0_1"

    def __post_init__(self) -> None:
        if self.max_translation_step_m <= 0.0:
            raise DeployConfigError(
                f"max_translation_step_m must be positive, got {self.max_translation_step_m}"
            )
        if self.max_rotation_step_rad <= 0.0:
            raise DeployConfigError(
                f"max_rotation_step_rad must be positive, got {self.max_rotation_step_rad}"
            )
        if self.gripper_min > self.gripper_max:
            raise DeployConfigError(
                f"gripper_min ({self.gripper_min}) must be <= gripper_max ({self.gripper_max})"
            )
        if self.max_gripper_step < 0.0:
            raise DeployConfigError(
                f"max_gripper_step must be >= 0, got {self.max_gripper_step}"
            )
        if self.quaternion_norm_tolerance <= 0.0:
            raise DeployConfigError(
                "quaternion_norm_tolerance must be positive, "
                f"got {self.quaternion_norm_tolerance}"
            )
        if self.quaternion_order != "xyzw":
            raise DeployConfigError(
                f"quaternion_order must be 'xyzw', got {self.quaternion_order!r}"
            )


@dataclass(frozen=True)
class ImageConfig:
    """Deployment image preprocessing settings."""

    image_size: int = 224
    resize_mode: str = "resize_pad"
    transport: str = "raw"


@dataclass(frozen=True)
class CommandOutputConfig:
    """Command-output mapping + the human master switch for L2-05 (C7, deploy_041).

    The master switch ``command_output_enabled`` is a startup-only decision:
    it defaults to ``False`` and is set explicitly by the CLI caller (L2-06).
    It must never be read from ``deploy.yaml`` — a persisted ``enabled`` key is
    rejected so an old config file can never silently turn on real commands.

    All remaining fields are the static output mapping loaded from YAML.
    """

    command_output_enabled: bool = False
    left_pose_frame_id: str = "left_arm_base"
    right_pose_frame_id: str = "right_arm_base"
    gripper_deadband: float = 0.01
    gripper_min_publish_interval_s: float = 0.05
    qos_depth: int = 10

    def __post_init__(self) -> None:
        if not isinstance(self.command_output_enabled, bool):
            raise TypeError(
                f"CommandOutputConfig.command_output_enabled must be bool, "
                f"got {type(self.command_output_enabled)!r}"
            )
        if self.left_pose_frame_id != "left_arm_base":
            raise DeployConfigError(
                "command_output.left_pose_frame_id must be 'left_arm_base'"
            )
        if self.right_pose_frame_id != "right_arm_base":
            raise DeployConfigError(
                "command_output.right_pose_frame_id must be 'right_arm_base'"
            )
        if not math.isfinite(self.gripper_deadband) or self.gripper_deadband < 0.0:
            raise DeployConfigError(
                "command_output.gripper_deadband must be finite and >= 0"
            )
        if self.gripper_deadband > 1.0:
            raise DeployConfigError(
                "command_output.gripper_deadband must not exceed normalized span 1.0"
            )
        if not math.isfinite(self.gripper_min_publish_interval_s) or (
            self.gripper_min_publish_interval_s < 0.0
        ):
            raise DeployConfigError(
                "command_output.gripper_min_publish_interval_s must be finite and >= 0"
            )
        if not isinstance(self.qos_depth, int) or isinstance(self.qos_depth, bool):
            raise TypeError(
                f"command_output.qos_depth must be int, got {type(self.qos_depth)!r}"
            )
        if self.qos_depth <= 0:
            raise DeployConfigError("command_output.qos_depth must be a positive integer")


@dataclass(frozen=True)
class DeployConfig:
    """Complete ACT deployment configuration.

    Bridge and mux sections are intentionally absent — ACT does not use them.
    """

    bundle: BundleConfig
    runtime: RuntimeConfig
    image: ImageConfig
    topics: TopicsConfig
    safety: SafetyConfig
    command_output: CommandOutputConfig = field(default_factory=CommandOutputConfig)
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False)

    def __post_init__(self) -> None:
        enabled = self.command_output.command_output_enabled
        if self.runtime.mode == "real-run" and not enabled:
            raise DeployConfigError(
                "runtime.mode=real-run requires the startup-only "
                "--enable-command-output confirmation"
            )
        if self.runtime.mode == "dry-run" and enabled:
            raise DeployConfigError(
                "--enable-command-output requires runtime.mode=real-run; "
                "dry-run can never publish hardware commands"
            )
        if self.safety.max_translation_step_m > 0.01:
            raise DeployConfigError(
                "safety.max_translation_step_m must be <= RM65 driver limit 0.01"
            )
        if self.runtime.max_delta_per_step > 0.01:
            raise DeployConfigError(
                "runtime.max_delta_per_step must be <= RM65 driver limit 0.01"
            )
        if self.safety.max_rotation_step_rad > 0.05:
            raise DeployConfigError(
                "safety.max_rotation_step_rad must be <= RM65 driver limit 0.05"
            )
        if (
            self.safety.gripper_min != 0.0
            or self.safety.gripper_max != 1.0
            or self.safety.gripper_domain != "normalized_0_1"
        ):
            raise DeployConfigError(
                "ACT and elephant_gripper command domain must be normalized [0,1]"
            )

    @classmethod
    def from_mapping(
        cls,
        raw: Mapping[str, Any],
        *,
        base_dir: Path,
        command_output_enabled: bool = False,
    ) -> "DeployConfig":
        return _deploy_from_mapping(
            raw, base_dir=base_dir, command_output_enabled=command_output_enabled
        )


# ---------------------------------------------------------------------------
# Assembly (orchestration)
# ---------------------------------------------------------------------------


def _deploy_from_mapping(
    raw: Mapping[str, Any],
    *,
    base_dir: Path,
    command_output_enabled: bool = False,
) -> DeployConfig:
    """Assemble a DeployConfig from a raw mapping.

    Assembly order is fixed: bundle → runtime → image → topics → safety →
    command_output → raw. The command-output master switch is taken only from
    the explicit *command_output_enabled* argument (default ``False``); it is
    never read from YAML.
    """
    root = _mapping(raw, "<root>")
    namespace = _str(_mapping(root.get("topics", {}), "topics"), "namespace", default="/act")

    bundle_raw = _required_mapping(root, "bundle")
    runtime_raw = _mapping(root.get("runtime", {}), "runtime")
    image_raw = _mapping(root.get("image", {}), "image")
    topics_raw = _mapping(root.get("topics", {}), "topics")
    safety_raw = _mapping(root.get("safety", {}), "safety")
    command_output_raw = _mapping(root.get("command_output", {}), "command_output")

    obs_raw = _mapping(topics_raw.get("observation", {}), "topics.observation")
    cmd_raw = _mapping(topics_raw.get("command", {}), "topics.command")

    obs_images, obs_left, obs_right = _observation_images_from_raw(obs_raw)

    return DeployConfig(
        bundle=BundleConfig(
            bundle_dir=_path_or_none(bundle_raw, "bundle_dir", base_dir=base_dir),
        ),
        runtime=RuntimeConfig(
            mode=_choice(runtime_raw, "mode", {"dry-run", "real-run"}, default="dry-run"),
            device=_str(runtime_raw, "device", default="cuda:0"),
            inference_hz=_positive_float(runtime_raw, "inference_hz", default=10.0),
            control_hz=_positive_float(runtime_raw, "control_hz", default=30.0),
            chunk_size=_positive_int(runtime_raw, "chunk_size", default=30),
            execute_horizon=_positive_int(runtime_raw, "execute_horizon", default=10),
            prefetch_steps=_non_negative_int(runtime_raw, "prefetch_steps", default=5),
            action_dim=_positive_int(runtime_raw, "action_dim", default=16),
            state_dim=_positive_int(runtime_raw, "state_dim", default=16),
            max_action_age_sec=_positive_float(runtime_raw, "max_action_age_sec", default=0.45),
            max_observation_age_sec=_positive_float(runtime_raw, "max_observation_age_sec", default=1.0),
            max_inference_requests=_exactly_one_int(runtime_raw, "max_inference_requests"),
            max_pending_chunks=_exactly_one_int(runtime_raw, "max_pending_chunks"),
            fallback_policy=_choice(
                runtime_raw,
                "fallback_policy",
                {"hold_last_action", "continue_old_chunk", "safe_stop"},
                default="hold_last_action",
            ),
            max_delta_per_step=_positive_float(runtime_raw, "max_delta_per_step", default=0.01),
            warmup_steps=_non_negative_int(runtime_raw, "warmup_steps", default=2),
            compile_model=_bool(runtime_raw, "compile_model", default=True),
            compile_mode=_str(runtime_raw, "compile_mode", default="reduce-overhead"),
            publish_metrics_hz=_positive_float(runtime_raw, "publish_metrics_hz", default=1.0),
            task=_str(runtime_raw, "task", default="bimanual manipulation"),
            response_motion_check_enabled=_bool(
                runtime_raw, "response_motion_check_enabled", default=True
            ),
            response_timeout_sec=_positive_float(runtime_raw, "response_timeout_sec", default=0.5),
            hold_window_sec=_positive_float(runtime_raw, "hold_window_sec", default=0.2),
            epsilon_move_translation_m=_non_negative_float(runtime_raw, "epsilon_move_translation_m", default=0.001),
            epsilon_move_rotation_rad=_non_negative_float(runtime_raw, "epsilon_move_rotation_rad", default=0.01),
            epsilon_move_gripper=_non_negative_float(runtime_raw, "epsilon_move_gripper", default=0.01),
            epsilon_hold_translation_m=_non_negative_float(runtime_raw, "epsilon_hold_translation_m", default=0.001),
            epsilon_hold_rotation_rad=_non_negative_float(runtime_raw, "epsilon_hold_rotation_rad", default=0.01),
            epsilon_hold_gripper=_non_negative_float(runtime_raw, "epsilon_hold_gripper", default=0.01),
        ),
        image=ImageConfig(
            image_size=_positive_int(image_raw, "image_size", default=224),
            resize_mode=_choice(image_raw, "resize_mode", {"resize_pad", "resize_crop"}, default="resize_pad"),
            transport=_choice(image_raw, "transport", {"raw", "compressed", "both"}, default="raw"),
        ),
        topics=TopicsConfig(
            namespace=namespace,
            observation=ObservationTopicsConfig(
                arm_state=_str(obs_raw, "arm_state", default="/act/observation/arm_state"),
                left_image=obs_left,
                right_image=obs_right,
                left_tcp_pose=_str(obs_raw, "left_tcp_pose", default="/act/observation/arm/left_tcp_pose"),
                right_tcp_pose=_str(obs_raw, "right_tcp_pose", default="/act/observation/arm/right_tcp_pose"),
                left_gripper_state=_str(obs_raw, "left_gripper_state", default="/act/observation/gripper/left_state"),
                right_gripper_state=_str(obs_raw, "right_gripper_state", default="/act/observation/gripper/right_state"),
                images=obs_images,
            ),
            command=CommandTopicsConfig(
                policy_action=_str(cmd_raw, "policy_action", default="/act/policy_action"),
                left_arm_target=_str(cmd_raw, "left_arm_target", default="/act/command/arm/left_target"),
                right_arm_target=_str(cmd_raw, "right_arm_target", default="/act/command/arm/right_target"),
                left_gripper_target=_str(cmd_raw, "left_gripper_target", default="/act/command/gripper/left_target"),
                right_gripper_target=_str(cmd_raw, "right_gripper_target", default="/act/command/gripper/right_target"),
                status=_str(cmd_raw, "status", default="/act/command/status"),
                metrics=_str(cmd_raw, "metrics", default="/act/metrics"),
            ),
        ),
        safety=_safety_from_mapping(safety_raw),
        command_output=_command_output_from_mapping(
            command_output_raw, command_output_enabled=command_output_enabled
        ),
        raw=dict(root),
    )


def _safety_from_mapping(safety_raw: Mapping[str, Any]) -> SafetyConfig:
    """Parse and validate the ``safety:`` section into an immutable SafetyConfig.

    Destructive migration (deploy_032): legacy keys
    ``max_tcp_delta_per_step`` / ``hand_min`` / ``hand_max`` / ``quaternion_check``
    are rejected with a clear error so meter-scale thresholds are never silently
    reinterpreted as joint radians or F100 register domains.
    """
    present_legacy = sorted(k for k in _SAFETY_LEGACY_KEYS if k in safety_raw)
    if present_legacy:
        raise DeployConfigError(
            "safety section uses removed legacy keys "
            f"{present_legacy}; migrate to ActionDomain fields: "
            "max_translation_step_m, max_rotation_step_rad, gripper_min, "
            "gripper_max, max_gripper_step, quaternion_norm_tolerance "
            "(optional: pose_frame, quaternion_order, gripper_domain). "
            "Do not map hand_min/hand_max 300~1000 hardware registers into "
            "the gripper training domain."
        )

    return SafetyConfig(
        max_translation_step_m=_positive_float(
            safety_raw, "max_translation_step_m", default=0.01
        ),
        max_rotation_step_rad=_positive_float(
            safety_raw, "max_rotation_step_rad", default=0.05
        ),
        gripper_min=_float(safety_raw, "gripper_min", default=0.0),
        gripper_max=_float(safety_raw, "gripper_max", default=1.0),
        max_gripper_step=_non_negative_float(
            safety_raw, "max_gripper_step", default=0.2
        ),
        quaternion_norm_tolerance=_positive_float(
            safety_raw, "quaternion_norm_tolerance", default=1e-3
        ),
        pose_frame=_str(safety_raw, "pose_frame", default="base"),
        quaternion_order=_str(safety_raw, "quaternion_order", default="xyzw"),
        gripper_domain=_str(safety_raw, "gripper_domain", default="normalized_0_1"),
    )


def _command_output_from_mapping(
    command_output_raw: Mapping[str, Any],
    *,
    command_output_enabled: bool,
) -> CommandOutputConfig:
    """Parse and validate the ``command_output:`` section into a C7 config.

    The human master switch ``command_output_enabled`` is NOT read from YAML —
    it is supplied by the startup caller (default ``False``). A persisted
    ``enabled`` key in ``deploy.yaml`` is rejected so an old config file can
    never silently turn on real command output.
    """
    if not isinstance(command_output_enabled, bool):
        raise DeployConfigError(
            "command_output_enabled must be a bool supplied by the startup caller"
        )
    if "enabled" in command_output_raw:
        raise DeployConfigError(
            "command_output.enabled must not appear in deploy.yaml; it is a "
            "startup-only decision set explicitly by the CLI caller "
            "(--enable-command-output)."
        )
    removed_keys = sorted(
        key
        for key in (
            "pose_frame_id",
            "gripper_input_min",
            "gripper_input_max",
            "gripper_output_min",
            "gripper_output_max",
        )
        if key in command_output_raw
    )
    if removed_keys:
        raise DeployConfigError(
            "command_output uses removed keys "
            f"{removed_keys}; use left_pose_frame_id/right_pose_frame_id and "
            "normalized [0,1] gripper commands"
        )

    return CommandOutputConfig(
        command_output_enabled=command_output_enabled,
        left_pose_frame_id=_str(
            command_output_raw, "left_pose_frame_id", default="left_arm_base"
        ),
        right_pose_frame_id=_str(
            command_output_raw, "right_pose_frame_id", default="right_arm_base"
        ),
        gripper_deadband=_non_negative_float(
            command_output_raw, "gripper_deadband", default=0.01
        ),
        gripper_min_publish_interval_s=_non_negative_float(
            command_output_raw, "gripper_min_publish_interval_s", default=0.05
        ),
        qos_depth=_positive_int(command_output_raw, "qos_depth", default=10),
    )


# ---------------------------------------------------------------------------
# Typed validators (module-private)
# ---------------------------------------------------------------------------


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


def _path_or_none(raw: Mapping[str, Any], key: str, *, base_dir: Path) -> Path | None:
    """Resolve a bundle path, tolerating an unset / null / empty value.

    Returns ``None`` when the key is absent or null/empty so the default
    deploy.yaml and controlled fake harness can omit ``bundle_dir``.  A
    ``None`` bundle is a deliberate "no production resource loader" signal —
    ``load_act_runtime_resources`` fails fast on it instead of guessing a path.
    """
    if key not in raw:
        return None
    value = raw[key]
    if value is None or (isinstance(value, str) and value.strip() == ""):
        return None
    if not isinstance(value, str):
        raise DeployConfigError(
            f"bundle.{key} must be a string path or null, got {type(value).__name__}"
        )
    path = Path(value).expanduser()
    return path if path.is_absolute() else (base_dir / path)


def _exactly_one_int(raw: Mapping[str, Any], key: str, default: int = 1) -> int:
    """Read an int field that must be exactly 1 (single in-flight request / chunk)."""
    value = int(raw.get(key, default))
    if value != 1:
        raise DeployConfigError(f"{key} must be exactly 1, got {value}")
    return value


def _image_mapping_from_raw(raw: Any) -> tuple[tuple[str, str], ...]:
    """Validate the canonical ``images`` mapping and return sorted key/topic pairs."""
    if not isinstance(raw, Mapping):
        raise DeployConfigError(
            "topics.observation.images must be a mapping of camera key -> ROS topic."
        )
    if not raw:
        raise DeployConfigError("topics.observation.images must be non-empty.")
    pairs: list[tuple[str, str]] = []
    for key, topic in raw.items():
        if not isinstance(key, str) or not key.strip():
            raise DeployConfigError("topics.observation.images keys must be non-empty strings.")
        if not isinstance(topic, str) or not topic.strip():
            raise DeployConfigError(
                f"topics.observation.images[{key!r}] must be a non-empty ROS topic string."
            )
        pairs.append((key, topic))
    pairs.sort(key=lambda p: p[0])
    keys = [k for k, _ in pairs]
    if len(keys) != len(set(keys)):
        raise DeployConfigError("topics.observation.images has duplicate camera keys.")
    missing = [c for c in _CANONICAL_CAMERA_KEYS if c not in keys]
    if missing:
        raise DeployConfigError(
            f"topics.observation.images missing canonical camera key(s): {missing}"
        )
    return tuple(pairs)


def _observation_images_from_raw(
    obs_raw: Mapping[str, Any],
) -> tuple[tuple[tuple[str, str], ...], str, str]:
    """Resolve the observation image mapping, enforcing the legacy/ canonical rule.

    Returns ``(images_mapping, left_image, right_image)``.  Raises when the
    config mixes legacy ``left_image``/``right_image`` with the canonical
    ``images`` mapping, or uses legacy keys without the canonical mapping.
    """
    has_legacy = ("left_image" in obs_raw) or ("right_image" in obs_raw)
    has_images = "images" in obs_raw
    if has_legacy and has_images:
        raise DeployConfigError(
            "topics.observation cannot mix legacy left_image/right_image with the "
            "canonical `images` mapping; migrate to `images`."
        )
    if has_legacy and not has_images:
        raise DeployConfigError(
            "topics.observation uses legacy left_image/right_image without the "
            "canonical `images` mapping; `images` is required (canonical camera missing)."
        )
    images = _image_mapping_from_raw(obs_raw["images"]) if has_images else _DEFAULT_IMAGE_MAPPING
    left = _str(obs_raw, "left_image", default="/act/observation/image/left_gripper_fisheye")
    right = _str(obs_raw, "right_image", default="/act/observation/image/right_gripper_fisheye")
    return images, left, right


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


def _non_negative_float(raw: Mapping[str, Any], key: str, default: float) -> float:
    value = _float(raw, key, default)
    if value < 0.0:
        raise DeployConfigError(f"{key} must be non-negative, got {value}")
    return value


def _float_list(raw: Mapping[str, Any], key: str, default: list[float]) -> list[float]:
    value = raw.get(key, default)
    if not isinstance(value, list):
        raise DeployConfigError(f"{key} must be a list of floats")
    return [float(item) for item in value]


# ============================================================================
# deploy_009 — contract cross-validation and config orchestration
# ============================================================================


def check_bundle_contract(
    bundle_dir: Path,
    manifest: Mapping[str, Any],
    required_files: Sequence[str] | None = None,
) -> BundleContractResult:
    """Check that a bundle directory contains all required files and a compatible manifest.

    Args:
        bundle_dir: Path to the bundle root directory.
        manifest: The parsed manifest dict (from ``load_bundle_manifest``).
        required_files: File/directory names that must exist.  Defaults to the
            standard ACT bundle set: ``manifest.json``, ``normalizers.json``,
            ``experiment_config.yaml``, ``adapter``.

    Returns:
        A ``BundleContractResult`` with ``passed=True`` if all checks pass.
    """
    if required_files is None:
        required_files = ("manifest.json", "normalizers.json", "experiment_config.yaml", "adapter")

    bundle_dir = Path(bundle_dir).expanduser().resolve()
    missing = check_bundle_files(bundle_dir)

    # Also verify checkpoint is resolvable
    try:
        resolve_checkpoint_path(bundle_dir)
    except Exception:
        missing.append("checkpoint")

    # Manifest schema_version compatibility
    schema_version = manifest.get("schema_version")
    schema_ok = schema_version == BUNDLE_SCHEMA_VERSION

    reasons: list[str] = []
    if missing:
        reasons.append(f"Missing bundle files: {', '.join(missing)}")
    if not schema_ok:
        reasons.append(
            f"Manifest schema_version {schema_version!r} != expected {BUNDLE_SCHEMA_VERSION}"
        )

    if reasons:
        return BundleContractResult(
            passed=False,
            reason="; ".join(reasons),
            missing_files=tuple(missing),
            schema_version=schema_version,
        )

    return BundleContractResult(
        passed=True,
        reason="Bundle contract checks passed",
        missing_files=(),
        schema_version=schema_version,
    )


def check_normalizer_contract(
    state_normalizer: ActionStateNormalizer,
    action_normalizer: ActionStateNormalizer,
    expected_dim: int = 16,
) -> NormalizerContractResult:
    """Check that state and action normalizer dimensions match the 16D contract.

    Args:
        state_normalizer: State normalizer loaded from the bundle.
        action_normalizer: Action normalizer loaded from the bundle.
        expected_dim: Expected vector dimension (default 16 for ACT).

    Returns:
        A ``NormalizerContractResult`` with ``passed=True`` if both normalizers
        have ``vector_dim == expected_dim``.
    """
    state_dim = state_normalizer.vector_dim
    action_dim = action_normalizer.vector_dim

    reasons: list[str] = []
    if state_dim != expected_dim:
        reasons.append(
            f"State normalizer dimension is {state_dim}, expected {expected_dim}"
        )
    if action_dim != expected_dim:
        reasons.append(
            f"Action normalizer dimension is {action_dim}, expected {expected_dim}"
        )

    if reasons:
        return NormalizerContractResult(
            passed=False,
            reason="; ".join(reasons),
            expected_dim=expected_dim,
            actual_dim=max(state_dim, action_dim),
        )

    return NormalizerContractResult(
        passed=True,
        reason="Normalizer dimensions match the 16D contract",
        expected_dim=expected_dim,
        actual_dim=expected_dim,
    )


def load_deploy_config(
    path: str | Path, *, command_output_enabled: bool = False
) -> DeployConfig:
    """Load a deployment configuration from a YAML file with full contract validation.

    Orchestration order:
    1. Parse YAML → validate root is a mapping.
    2. Construct ``DeployConfig`` via ``from_mapping``.
    3. If ``bundle_dir`` is set, load bundle artifacts and run contract checks.
    4. Return the validated ``DeployConfig``.

    Args:
        path: Path to ``deploy.yaml``.
        command_output_enabled: The human master switch for real command output.
            It is a startup-only decision supplied by the CLI caller (default
            ``False``); it is never read from YAML (deploy_056 / P0-06-config).

    Returns:
        A fully validated ``DeployConfig``.

    Raises:
        DeployConfigError: If the YAML is invalid, the root is not a mapping,
            or any contract check fails.
    """
    config_path = Path(path).expanduser().resolve()
    with config_path.open("r", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh)

    if not isinstance(raw, Mapping):
        raise DeployConfigError(
            f"Deploy config root must be a mapping, got {type(raw).__name__}"
        )

    config = DeployConfig.from_mapping(
        raw, base_dir=config_path.parent, command_output_enabled=command_output_enabled
    )

    # Contract cross-validation (only when a concrete bundle_dir exists)
    bundle_dir = config.bundle.resolved_bundle_dir
    if bundle_dir is not None and bundle_dir.exists():
        manifest = load_bundle_manifest(bundle_dir)

        # Bundle file contract
        bundle_result = check_bundle_contract(bundle_dir, manifest)
        if not bundle_result.is_pass:
            raise DeployConfigError(bundle_result.reason)

        # Normalizer dimension contract
        state_norm, action_norm = load_bundle_normalizers(bundle_dir)
        norm_result = check_normalizer_contract(state_norm, action_norm, expected_dim=16)
        if not norm_result.is_pass:
            raise DeployConfigError(norm_result.reason)

    return config
