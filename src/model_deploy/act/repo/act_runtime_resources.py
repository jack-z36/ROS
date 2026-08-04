"""ACT runtime startup resources — the single frozen startup contract (deploy_056).

This module is the ONLY public owner of the L2-01 startup-resource contract
consumed by L2-02 (observation snapshot), L2-03 (ACT inference) and L2-06
(control loop):

- ``PolicyInputSpec``: frozen canonical policy input contract — state/action
  dimension, camera keys, image shapes / layout / dtype / value-range, and
  chunk size.
- ``ActRuntimeResources``: frozen aggregate of the loaded policy, the state /
  action normalizers, the single ``PolicyInputSpec``, and the cross-validation
  result.
- ``load_act_runtime_resources(config, *, load_policy)``: the single production
  aggregate entry.

Design rules (deploy_056, P0-01..04 / P0-06-config / P0-09-config):
- The ``PolicyInputSpec`` is derived ONCE from the production policy RAM
  metadata (bundle manifest + experiment_config).  Missing or conflicting
  metadata is a startup FAIL; config defaults never plug the hole.
- An empty / null ``bundle_dir`` fails fast — the loader never guesses a path.
- Policy weights are NOT loaded here (that belongs to L2-03).  Production passes
  a ``load_policy`` callback; tests inject a fake / double.  A module-level
  registered loader (``register_policy_loader``) supports the fake-policy-test
  runtime mode.

NOTE: ``config.schema`` is imported lazily inside the functions that raise
``DeployConfigError`` to avoid a config <-> repo import cycle at package load.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Mapping, Tuple

from model_deploy.act.repo.bundle_reader import check_bundle_files, resolve_checkpoint_path
from model_deploy.act.repo.experiment_config_loader import (
    ExperimentConfigLoadError,
    load_experiment_config,
)
from model_deploy.act.repo.manifest_parser import load_bundle_manifest
from model_deploy.act.repo.normalization import ActionStateNormalizer
from model_deploy.act.repo.normalizer_loader import load_bundle_normalizers

if TYPE_CHECKING:  # pragma: no cover - typing only, avoids import cycle
    from model_deploy.act.config.schema import DeployConfig

# ---------------------------------------------------------------------------
# Canonical policy input contract constants
# ---------------------------------------------------------------------------

IMAGE_LAYOUT = "CHW"
IMAGE_DTYPE = "float32"
IMAGE_VALUE_RANGE: Tuple[float, float] = (0.0, 1.0)
CANONICAL_CAMERA_KEYS: Tuple[str, ...] = ("left", "right")
STATE_DIM: int = 16
ACTION_DIM: int = 16

#: Production policy loader: given a bundle dir, return the loaded policy object.
#: L2-03 owns the real weight-loading implementation; this module only aggregates
#: the already-loaded policy.  Tests inject a fake / double.
PolicyLoader = Callable[[Path], Any]


def _cfg_error(msg: str) -> "DeployConfigError":
    """Lazily import and construct ``DeployConfigError`` (avoids import cycle)."""
    from model_deploy.act.config.schema import DeployConfigError

    return DeployConfigError(msg)


# ---------------------------------------------------------------------------
# Frozen contract objects
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PolicyInputSpec:
    """Frozen canonical policy input contract derived once at startup (deploy_056).

    Invariants enforced on construction:
    - ``state_dim`` / ``action_dim`` are exactly the 16D ACT contract.
    - ``camera_keys`` is non-empty, unique, and sorted (orderly).
    - ``image_shapes`` are exact CHW, three channels, positive H/W, one per camera.
    - ``image_layout`` is ``"CHW"``, ``image_dtype`` is ``"float32"``,
      ``image_value_range`` is ``(0.0, 1.0)``.
    - ``chunk_size`` is positive and must equal the config value (checked by the
      loader, since the spec does not hold the config).
    """

    state_key: str
    state_dim: int
    image_prefix: str
    camera_keys: Tuple[str, ...]
    image_shapes: Tuple[Tuple[int, int, int], ...]
    image_layout: str
    image_dtype: str
    image_value_range: Tuple[float, float]
    action_dim: int
    chunk_size: int

    def __post_init__(self) -> None:
        if not isinstance(self.state_key, str) or not self.state_key.strip():
            raise _cfg_error("PolicyInputSpec.state_key must be a non-empty string.")
        if self.state_dim != STATE_DIM:
            raise _cfg_error(
                f"PolicyInputSpec.state_dim must be {STATE_DIM}, got {self.state_dim}."
            )
        if not isinstance(self.image_prefix, str) or not self.image_prefix.strip():
            raise _cfg_error("PolicyInputSpec.image_prefix must be a non-empty string.")
        if not self.camera_keys:
            raise _cfg_error("PolicyInputSpec.camera_keys must be non-empty.")
        if sorted(self.camera_keys) != list(self.camera_keys):
            raise _cfg_error("PolicyInputSpec.camera_keys must be sorted (orderly).")
        if len(set(self.camera_keys)) != len(self.camera_keys):
            raise _cfg_error("PolicyInputSpec.camera_keys must be unique.")
        if self.image_layout != IMAGE_LAYOUT:
            raise _cfg_error(
                f"PolicyInputSpec.image_layout must be {IMAGE_LAYOUT!r}, got {self.image_layout!r}."
            )
        if self.image_dtype != IMAGE_DTYPE:
            raise _cfg_error(
                f"PolicyInputSpec.image_dtype must be {IMAGE_DTYPE!r}, got {self.image_dtype!r}."
            )
        if self.image_value_range != IMAGE_VALUE_RANGE:
            raise _cfg_error(
                f"PolicyInputSpec.image_value_range must be {IMAGE_VALUE_RANGE}, "
                f"got {self.image_value_range}."
            )
        if len(self.image_shapes) != len(self.camera_keys):
            raise _cfg_error(
                "PolicyInputSpec.image_shapes length must match camera_keys."
            )
        for shape in self.image_shapes:
            if (
                len(shape) != 3
                or shape[0] != 3
                or not isinstance(shape[1], int)
                or not isinstance(shape[2], int)
                or shape[1] <= 0
                or shape[2] <= 0
            ):
                raise _cfg_error(
                    f"PolicyInputSpec.image_shapes entries must be (3, H>0, W>0) CHW, "
                    f"got {shape}."
                )
        if self.action_dim != ACTION_DIM:
            raise _cfg_error(
                f"PolicyInputSpec.action_dim must be {ACTION_DIM}, got {self.action_dim}."
            )
        if self.chunk_size <= 0:
            raise _cfg_error("PolicyInputSpec.chunk_size must be positive.")


@dataclass(frozen=True)
class RuntimeResourceCrossCheck:
    """Result of the startup-resource cross-validation."""

    passed: bool
    issues: Tuple[str, ...]

    @property
    def is_pass(self) -> bool:
        return self.passed


@dataclass(frozen=True)
class ActRuntimeResources:
    """Frozen aggregate of the loaded startup resources for L2-02 / L2-03 / L2-06.

    Holds the already-loaded policy, the state / action normalizers, the single
    ``PolicyInputSpec``, and the cross-validation result.  Created once at
    startup; read-only thereafter.
    """

    policy: Any
    state_normalizer: ActionStateNormalizer
    action_normalizer: ActionStateNormalizer
    policy_input_spec: PolicyInputSpec
    bundle_dir: Path
    cross_check: RuntimeResourceCrossCheck


# ---------------------------------------------------------------------------
# Module-level policy loader hook (fake-policy-test runtime mode)
# ---------------------------------------------------------------------------

_POLICY_LOADER: PolicyLoader | None = None


def register_policy_loader(fn: PolicyLoader | None) -> None:
    """Register the production (or fake) policy loader used by ``load_act_runtime_resources``.

    Production (L2-03) registers the real weight loader at startup.  Tests / the
    fake-policy-test mode register a double.  Pass ``None`` to clear the
    registered loader.  This avoids loading weights inside the repo layer.
    """
    global _POLICY_LOADER
    _POLICY_LOADER = fn


# ---------------------------------------------------------------------------
# Production aggregate
# ---------------------------------------------------------------------------


def load_act_runtime_resources(
    config: "DeployConfig",
    *,
    load_policy: PolicyLoader | None = None,
) -> ActRuntimeResources:
    """Aggregate the frozen startup resources for L2-02 / L2-03 / L2-06.

    Steps:
    1. Resolve the bundle dir; empty / null -> stable FAIL (never guess a path).
    2. Verify the bundle structure and resolvable checkpoint.
    3. Read bundle metadata (manifest + experiment_config) and derive the
       ``PolicyInputSpec`` dimensions; missing / conflicting metadata -> FAIL.
    4. Cross-validate the spec against the config (state/action dim, chunk size).
    5. Load normalizers; verify 16D and match the spec.
    6. Load the policy via the injected / registered ``load_policy`` callback and
       return the frozen ``ActRuntimeResources`` aggregate.

    Args:
        config: A validated ``DeployConfig`` from ``load_deploy_config``.
        load_policy: Callback ``(bundle_dir) -> policy``.  Required to aggregate
            the loaded policy.  If ``None``, the module-level registered loader
            (``register_policy_loader``) is used; if still unavailable, a clear
            ``DeployConfigError`` is raised.
    """
    if config.bundle.resolved_bundle_dir is None:
        raise _cfg_error(
            "ActRuntimeResources requires a concrete bundle_dir; the configured "
            "bundle_dir is empty. Set bundle.bundle_dir before loading runtime "
            "resources (the loader never guesses a path)."
        )
    bundle_dir = config.bundle.resolved_bundle_dir.resolve()

    # 1. bundle structure + checkpoint
    missing = check_bundle_files(bundle_dir)
    if missing:
        raise _cfg_error(
            f"Bundle incomplete for runtime resources; missing: {', '.join(missing)}"
        )
    try:
        resolve_checkpoint_path(bundle_dir)
    except Exception as exc:  # noqa: BLE001 - surface any read/resolve failure
        raise _cfg_error(f"Bundle checkpoint unresolvable: {exc}") from exc

    # 2. metadata -> spec dimensions (config must match; never default-plug)
    manifest = load_bundle_manifest(bundle_dir)
    exp = _load_experiment_config_mapping(bundle_dir)

    state_dim = _metadata_int(manifest, exp, "state_dim")
    action_dim = _metadata_int(manifest, exp, "action_dim")
    chunk_size = _metadata_int(manifest, exp, "chunk_size")

    conflict: list[str] = []
    if state_dim != config.runtime.state_dim:
        conflict.append(
            f"metadata state_dim {state_dim} != config runtime.state_dim "
            f"{config.runtime.state_dim}"
        )
    if action_dim != config.runtime.action_dim:
        conflict.append(
            f"metadata action_dim {action_dim} != config runtime.action_dim "
            f"{config.runtime.action_dim}"
        )
    if chunk_size != config.runtime.chunk_size:
        conflict.append(
            f"metadata chunk_size {chunk_size} != config runtime.chunk_size "
            f"{config.runtime.chunk_size}"
        )
    if conflict:
        raise _cfg_error("PolicyInputSpec/Config dimension conflict: " + "; ".join(conflict))

    # 3. derive spec (camera / image info from config topics + image size)
    images = config.topics.observation.image_topics
    camera_keys = tuple(sorted(images.keys()))
    image_size = config.image.image_size
    image_shapes = tuple((3, image_size, image_size) for _ in camera_keys)
    spec = PolicyInputSpec(
        state_key=config.topics.observation.arm_state,
        state_dim=state_dim,
        image_prefix=f"{config.topics.namespace}/observation/image/",
        camera_keys=camera_keys,
        image_shapes=image_shapes,
        image_layout=IMAGE_LAYOUT,
        image_dtype=IMAGE_DTYPE,
        image_value_range=IMAGE_VALUE_RANGE,
        action_dim=action_dim,
        chunk_size=chunk_size,
    )

    # 4. normalizers
    state_norm, action_norm = load_bundle_normalizers(bundle_dir)
    norm_conflict: list[str] = []
    if state_norm.vector_dim != state_dim:
        norm_conflict.append(
            f"state normalizer dim {state_norm.vector_dim} != spec state_dim {state_dim}"
        )
    if action_norm.vector_dim != action_dim:
        norm_conflict.append(
            f"action normalizer dim {action_norm.vector_dim} != spec action_dim {action_dim}"
        )
    if norm_conflict:
        raise _cfg_error("Normalizer/spec dimension conflict: " + "; ".join(norm_conflict))

    # 5. policy (injected / registered loader)
    loader = load_policy or _POLICY_LOADER
    if loader is None:
        raise _cfg_error(
            "No policy loader available. Production must pass load_policy= or call "
            "register_policy_loader(...) before load_act_runtime_resources."
        )
    policy = loader(bundle_dir)

    return ActRuntimeResources(
        policy=policy,
        state_normalizer=state_norm,
        action_normalizer=action_norm,
        policy_input_spec=spec,
        bundle_dir=bundle_dir,
        cross_check=RuntimeResourceCrossCheck(passed=True, issues=()),
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _load_experiment_config_mapping(bundle_dir: Path) -> Mapping[str, Any]:
    """Load experiment_config.yaml as a mapping; return {} if missing/unparseable."""
    try:
        return load_experiment_config(bundle_dir / "experiment_config.yaml")
    except ExperimentConfigLoadError:
        return {}
    except Exception:  # noqa: BLE001 - any other read failure -> treat as absent
        return {}


def _metadata_int(
    manifest: Mapping[str, Any], exp: Mapping[str, Any], key: str
) -> int:
    """Resolve a required integer metadata field from manifest.model or experiment_config.

    The metadata is the single source of truth; config never provides a default.
    """
    value: Any = None
    model = manifest.get("model", {}) if isinstance(manifest, Mapping) else {}
    if isinstance(model, Mapping) and key in model:
        value = model[key]
    if value is None and isinstance(exp, Mapping) and key in exp:
        value = exp[key]
    if value is None:
        raise _cfg_error(
            f"Bundle metadata missing required field '{key}' for PolicyInputSpec "
            f"derivation (config defaults must not plug the hole)."
        )
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise _cfg_error(
            f"Bundle metadata field '{key}' must be an int, got {value!r}"
        ) from exc
