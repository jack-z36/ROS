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

import json
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Mapping, Tuple

import numpy as np

from model_deploy.act.repo.bundle_reader import (
    check_bundle_files,
    is_bundle_dir,
    is_checkpoint_dir,
    resolve_checkpoint_path,
    resolve_pretrained_dir,
)
from model_deploy.act.repo.experiment_config_loader import (
    ExperimentConfigLoadError,
    load_experiment_config,
)
from model_deploy.act.repo.manifest_parser import load_bundle_manifest
from model_deploy.act.repo.normalization import ActionStateNormalizer
from model_deploy.act.repo.normalizer_loader import load_bundle_normalizers
from model_deploy.act.types.action_representation import (
    ActionRepresentationSpec,
    EXPECTED_ARM_ACTION_TYPE,
    EXPECTED_CHUNK_REFERENCE,
    EXPECTED_TRANSLATION_FRAME,
    EXPECTED_ROTATION_REPRESENTATION,
    EXPECTED_GRIPPER_ACTION_TYPE,
)

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
    ``PolicyInputSpec``, the frozen ``ActionRepresentationSpec`` read from the
    bundle manifest, and the cross-validation result.  Created once at startup;
    read-only thereafter.
    """

    policy: Any
    state_normalizer: ActionStateNormalizer
    action_normalizer: ActionStateNormalizer
    policy_input_spec: PolicyInputSpec
    action_representation_spec: ActionRepresentationSpec
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

    Two source layouts are auto-detected from ``config.bundle.bundle_dir``:

    - **bundle** — a packaged ``deploy_bundle/`` (``manifest.json`` present).
      The manifest self-describes the dimensions and the action representation;
      ``normalizers.json`` + ``experiment_config.yaml`` are read for structural
      gating; the manifest's ``action_representation`` is cross-validated
      field-by-field against ``deploy.yaml``.
    - **checkpoint** — a raw training checkpoint (``pretrained_model/config.json``
      present, e.g. ``.../checkpoints/100000``).  Dimensions are derived from
      ``config.json``; the action representation is taken from ``deploy.yaml``
      (the operator declares the checkpoint matches the relative-action contract
      by pointing the loader at it); the normalizer is a synthetic identity
      passthrough (the real MEAN_STD statistics live inside the policy wrapper).

    Args:
        config: A validated ``DeployConfig`` from ``load_deploy_config``.
        load_policy: Callback ``(source_dir) -> policy``.  For a bundle it
            receives the bundle dir; for a checkpoint it receives the resolved
            ``pretrained_model`` dir.  If ``None``, the module-level registered
            loader (``register_policy_loader``) is used; if still unavailable, a
            clear ``DeployConfigError`` is raised.
    """
    if config.bundle.resolved_bundle_dir is None:
        raise _cfg_error(
            "ActRuntimeResources requires a concrete bundle_dir; the configured "
            "bundle_dir is empty. Set bundle.bundle_dir before loading runtime "
            "resources (the loader never guesses a path)."
        )
    source_dir = config.bundle.resolved_bundle_dir.resolve()

    loader = load_policy or _POLICY_LOADER
    if loader is None:
        raise _cfg_error(
            "No policy loader available. Production must pass load_policy= or call "
            "register_policy_loader(...) before load_act_runtime_resources."
        )

    if is_bundle_dir(source_dir):
        return _load_bundle_resources(source_dir, config, loader)
    if is_checkpoint_dir(source_dir):
        return _load_checkpoint_resources(source_dir, config, loader)
    raise _cfg_error(
        f"bundle_dir {source_dir} is neither a packaged bundle (missing "
        f"manifest.json) nor a raw checkpoint (missing "
        f"pretrained_model/config.json). Set bundle.bundle_dir to a deploy_bundle "
        f"directory or a checkpoints/<step> directory."
    )


def _load_bundle_resources(
    bundle_dir: Path,
    config: "DeployConfig",
    loader: PolicyLoader,
) -> ActRuntimeResources:
    """Load runtime resources from a packaged bundle (manifest present)."""
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
    _check_dim_conflict(state_dim, action_dim, chunk_size, config)

    spec = _build_policy_input_spec(config, state_dim, action_dim, chunk_size)

    # 3. action representation from the bundle manifest, cross-validated
    #    field-by-field against the deploy config expectation.  The bundle
    #    must be self-describing: a missing ``action_representation`` block or
    #    any field mismatch (e.g. an old absolute-action checkpoint) fails
    #    fast.  Never guessed from action_dim, stats or the filename.
    action_repr_spec = _load_action_representation(manifest)
    _cross_check_action_representation(action_repr_spec, config)

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

    # 5. policy (loader receives the bundle dir; the closure resolves the
    #    pretrained dir from the manifest via resolve_pretrained_dir.)
    policy = loader(bundle_dir)

    return ActRuntimeResources(
        policy=policy,
        state_normalizer=state_norm,
        action_normalizer=action_norm,
        policy_input_spec=spec,
        action_representation_spec=action_repr_spec,
        bundle_dir=bundle_dir,
        cross_check=RuntimeResourceCrossCheck(passed=True, issues=()),
    )


def _load_checkpoint_resources(
    source_dir: Path,
    config: "DeployConfig",
    loader: PolicyLoader,
) -> ActRuntimeResources:
    """Load runtime resources from a raw training checkpoint (no manifest).

    ``source_dir`` may be a checkpoint root (``.../checkpoints/100000``) or the
    inner ``pretrained_model`` directory itself.  Dimensions are derived from
    ``pretrained_model/config.json``; the action representation is taken from
    ``deploy.yaml``; the normalizer is a synthetic identity passthrough.
    """
    pretrained_dir = resolve_pretrained_dir(source_dir)

    state_dim, action_dim, chunk_size = _load_checkpoint_config(pretrained_dir)
    _check_dim_conflict(state_dim, action_dim, chunk_size, config)

    spec = _build_policy_input_spec(config, state_dim, action_dim, chunk_size)
    action_repr_spec = _action_representation_spec_from_config(config)
    identity_state_norm = _build_identity_normalizer(state_dim)
    identity_action_norm = _build_identity_normalizer(action_dim)

    # The loader receives the resolved pretrained dir directly — it contains
    # config.json, model.safetensors and the exported preprocessor statistics.
    policy = loader(pretrained_dir)

    return ActRuntimeResources(
        policy=policy,
        state_normalizer=identity_state_norm,
        action_normalizer=identity_action_norm,
        policy_input_spec=spec,
        action_representation_spec=action_repr_spec,
        bundle_dir=source_dir,
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


# The five action-representation tokens read from manifest.json and
# cross-validated field-by-field against the deploy config expectation.
_ACTION_REPR_FIELDS: Tuple[str, ...] = (
    "arm_action_type",
    "chunk_reference",
    "translation_frame",
    "rotation_representation",
    "gripper_action_type",
)


def _load_action_representation(manifest: Mapping[str, Any]) -> ActionRepresentationSpec:
    """Read the self-describing action representation from the bundle manifest.

    The bundle must declare ``action_representation`` at the manifest top level.
    A missing block or a missing/empty field fails fast — the loader never
    guesses the representation from action_dim, stats, or the checkpoint
    filename.

    Args:
        manifest: The parsed ``manifest.json`` mapping.

    Returns:
        A frozen ``ActionRepresentationSpec`` carrying the five tokens.

    Raises:
        DeployConfigError: The manifest is missing ``action_representation``,
            a field, or a field value is not a non-empty string.
    """
    if not isinstance(manifest, Mapping) or "action_representation" not in manifest:
        raise _cfg_error(
            "Bundle manifest missing required 'action_representation' block; "
            "the bundle must self-describe its action semantics. Old "
            "absolute-action checkpoints cannot be loaded as relative action."
        )
    block = manifest["action_representation"]
    if not isinstance(block, Mapping):
        raise _cfg_error(
            "manifest.action_representation must be a mapping, got "
            f"{type(block).__name__}"
        )
    tokens: dict[str, str] = {}
    for field in _ACTION_REPR_FIELDS:
        if field not in block:
            raise _cfg_error(
                f"manifest.action_representation missing required field "
                f"'{field}'. The bundle must self-describe its action semantics."
            )
        value = block[field]
        if not isinstance(value, str) or not value.strip():
            raise _cfg_error(
                f"manifest.action_representation.{field} must be a non-empty "
                f"string, got {value!r}"
            )
        tokens[field] = value
    return ActionRepresentationSpec(**tokens)


def _cross_check_action_representation(
    spec: ActionRepresentationSpec,
    config: "DeployConfig",
) -> None:
    """Cross-validate the bundle representation spec against the deploy config.

    The deploy config holds the *expected* representation declared in
    ``deploy.yaml``; the bundle manifest carries the checkpoint's *actual*
    representation.  They must match field-by-field — any mismatch (e.g. an
    old absolute-action bundle, or a different translation frame / quaternion
    order) fails fast with a stable, field-named error.

    Args:
        spec:   ``ActionRepresentationSpec`` read from the bundle manifest.
        config: ``DeployConfig`` carrying the deploy-side expectation.

    Raises:
        DeployConfigError: Any of the five representation fields mismatch.
    """
    expected = config.action_representation.as_mapping()
    actual = spec.as_mapping()
    mismatch: list[str] = []
    for field in _ACTION_REPR_FIELDS:
        if actual[field] != expected[field]:
            mismatch.append(
                f"action_representation.{field}: bundle declares "
                f"{actual[field]!r} but deploy.yaml expects {expected[field]!r}"
            )
    if mismatch:
        raise _cfg_error(
            "Action representation contract conflict: " + "; ".join(mismatch)
        )


# ---------------------------------------------------------------------------
# Raw-checkpoint helpers (no manifest / normalizers.json / experiment_config)
# ---------------------------------------------------------------------------


def _load_checkpoint_config(pretrained_dir: Path) -> Tuple[int, int, int]:
    """Read ``(state_dim, action_dim, chunk_size)`` from a checkpoint config.json.

    The lerobot ACT ``pretrained_model/config.json`` carries the canonical
    dimensions: ``input_features["observation.state"].shape[0]`` for the
    state dimension, ``output_features["action"].shape[0]`` for the action
    dimension, and the top-level ``chunk_size``.  A missing field or a
    non-integer value fails fast — config defaults never plug the hole.
    """
    config_path = pretrained_dir / "config.json"
    if not config_path.is_file():
        raise _cfg_error(
            f"Checkpoint config.json not found: {config_path}. A raw checkpoint "
            f"must contain pretrained_model/config.json."
        )
    try:
        with config_path.open("r", encoding="utf-8") as fh:
            cfg = json.load(fh)
    except (json.JSONDecodeError, OSError) as exc:
        raise _cfg_error(
            f"Failed to read checkpoint config.json {config_path}: {exc}"
        ) from exc

    def _shape0(features: Any, key: str, label: str) -> int:
        if not isinstance(features, Mapping) or key not in features:
            raise _cfg_error(
                f"Checkpoint config.json missing {label} feature '{key}'."
            )
        shape = features[key].get("shape") if isinstance(features[key], Mapping) else None
        if not isinstance(shape, list) or len(shape) < 1:
            raise _cfg_error(
                f"Checkpoint config.json {label} feature '{key}' has no shape list."
            )
        try:
            return int(shape[0])
        except (TypeError, ValueError) as exc:
            raise _cfg_error(
                f"Checkpoint config.json {label} feature '{key}' shape[0] must be "
                f"an int, got {shape[0]!r}"
            ) from exc

    state_dim = _shape0(cfg.get("input_features"), "observation.state", "input")
    action_dim = _shape0(cfg.get("output_features"), "action", "output")
    chunk_raw = cfg.get("chunk_size")
    if chunk_raw is None:
        raise _cfg_error(
            "Checkpoint config.json missing required field 'chunk_size'."
        )
    try:
        chunk_size = int(chunk_raw)
    except (TypeError, ValueError) as exc:
        raise _cfg_error(
            f"Checkpoint config.json 'chunk_size' must be an int, got {chunk_raw!r}"
        ) from exc
    return state_dim, action_dim, chunk_size


def _build_identity_normalizer(dim: int) -> ActionStateNormalizer:
    """Build an identity-passthrough min-max normalizer of *dim*.

    This mirrors the ``normalizers.json`` shipped with a packaged bundle:
    ``min=0``, ``max=1`` and every index marked identity.  The real MEAN_STD
    statistics are applied inside ``LerobotActPolicyWrapper`` (read from the
    exported preprocessor safetensors), so the repo-layer normalizer is a
    structural no-op used only for dimensional gating.
    """
    return ActionStateNormalizer(
        min_vals=np.zeros(dim, dtype=np.float32),
        max_vals=np.ones(dim, dtype=np.float32),
        identity_indices=list(range(dim)),
    )


def _action_representation_spec_from_config(
    config: "DeployConfig",
) -> ActionRepresentationSpec:
    """Build the action representation spec from the deploy config alone.

    For a raw checkpoint there is no ``manifest.json`` to self-describe the
    action semantics.  The deploy config (``deploy.yaml``) is the single
    source of truth: pointing the loader at a trained checkpoint is the
    operator's declaration that the checkpoint matches the configured
    relative-action contract.
    """
    mapping = config.action_representation.as_mapping()
    return ActionRepresentationSpec(
        arm_action_type=mapping["arm_action_type"],
        chunk_reference=mapping["chunk_reference"],
        translation_frame=mapping["translation_frame"],
        rotation_representation=mapping["rotation_representation"],
        gripper_action_type=mapping["gripper_action_type"],
    )


def _check_dim_conflict(
    state_dim: int,
    action_dim: int,
    chunk_size: int,
    config: "DeployConfig",
) -> None:
    """Cross-check derived dimensions against ``config.runtime`` (shared by both
    bundle and checkpoint paths)."""
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
        raise _cfg_error(
            "PolicyInputSpec/Config dimension conflict: " + "; ".join(conflict)
        )


def _build_policy_input_spec(
    config: "DeployConfig",
    state_dim: int,
    action_dim: int,
    chunk_size: int,
) -> PolicyInputSpec:
    """Derive the ``PolicyInputSpec`` from config topics + image size + dims.

    Shared by the bundle and checkpoint loading paths.
    """
    images = config.topics.observation.image_topics
    camera_keys = tuple(sorted(images.keys()))
    image_size = config.image.image_size
    image_shapes = tuple((3, image_size, image_size) for _ in camera_keys)
    return PolicyInputSpec(
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
