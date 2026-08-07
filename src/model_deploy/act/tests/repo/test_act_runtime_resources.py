"""deploy_056 repo startup-resource tests — PolicyInputSpec / ActRuntimeResources.

Covers the single frozen startup-resource contract owned by L2-01:
- ``PolicyInputSpec`` frozen invariants (16D, camera keys, CHW, float32, [0,1]).
- ``load_act_runtime_resources`` derives the spec once from bundle metadata,
  cross-validates against config, loads 16D normalizers, and aggregates the
  policy via an injected fake loader (no GPU / artifact in tests).
- fail-fast on missing metadata, normalizer conflict, config/metadata mismatch,
  and empty bundle.
"""

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from model_deploy.act.config.schema import DeployConfig, DeployConfigError
from model_deploy.act.repo import (
    ActRuntimeResources,
    PolicyInputSpec,
    load_act_runtime_resources,
    register_policy_loader,
)
from model_deploy.act.repo.act_runtime_resources import (
    ACTION_DIM,
    IMAGE_DTYPE,
    IMAGE_LAYOUT,
    IMAGE_VALUE_RANGE,
    STATE_DIM,
)


def _make_bundle(
    base: Path,
    *,
    state_dim: int = 16,
    action_dim: int = 16,
    chunk_size: int = 30,
    missing: set[str] | None = None,
) -> Path:
    """Create a mock production bundle directory (no real weights)."""
    import json

    import yaml

    missing = missing or set()
    bundle = base / "bundle"
    bundle.mkdir()

    if "adapter" not in missing:
        (bundle / "adapter").mkdir()
    if "checkpoint" not in missing:
        (bundle / "checkpoint.pt").write_text("dummy")

    manifest = {"schema_version": 1, "model": {}}
    if "state_dim" not in missing:
        manifest["model"]["state_dim"] = state_dim
    if "action_dim" not in missing:
        manifest["model"]["action_dim"] = action_dim
    if "chunk_size" not in missing:
        manifest["model"]["chunk_size"] = chunk_size
    # Self-describing action representation (relative-action contract).
    # Default to the expected relative block unless explicitly omitted.
    if "action_representation" not in missing:
        manifest["action_representation"] = {
            "arm_action_type": "relative_tcp_pose",
            "chunk_reference": "inference_observation",
            "translation_frame": "tcp_local",
            "rotation_representation": "quaternion_xyzw",
            "gripper_action_type": "absolute",
        }
    (bundle / "manifest.json").write_text(json.dumps(manifest))

    normalizers = {
        "state": {"min": [0.0] * state_dim, "max": [1.0] * state_dim, "identity_indices": []},
        "action": {"min": [-1.0] * action_dim, "max": [1.0] * action_dim, "identity_indices": []},
    }
    (bundle / "normalizers.json").write_text(json.dumps(normalizers))

    exp: dict = {}
    if "state_dim" not in missing:
        exp["state_dim"] = state_dim
    if "action_dim" not in missing:
        exp["action_dim"] = action_dim
    if "chunk_size" not in missing:
        exp["chunk_size"] = chunk_size
    (bundle / "experiment_config.yaml").write_text(yaml.safe_dump(exp))

    return bundle


def _config_for_bundle(bundle_dir: Path, *, state_dim: int = 16, action_dim: int = 16, chunk_size: int = 30) -> DeployConfig:
    raw = {
        "bundle": {"bundle_dir": str(bundle_dir)},
        "runtime": {
            "mode": "dry-run",
            "control_hz": 30.0,
            "inference_hz": 10.0,
            "chunk_size": chunk_size,
            "execute_horizon": 10,
            "state_dim": state_dim,
            "action_dim": action_dim,
            "fallback_policy": "hold_last_action",
        },
        "image": {"image_size": 224},
        "topics": {"namespace": "/act"},
        "safety": {},
    }
    return DeployConfig.from_mapping(raw, base_dir=Path("/tmp"))


def _fake_loader(bundle_dir: Path):
    return ("fake-policy", bundle_dir.name)


# ---------------------------------------------------------------------------
# PolicyInputSpec invariants
# ---------------------------------------------------------------------------


class TestPolicyInputSpecInvariants:
    def _valid(self, **overrides) -> PolicyInputSpec:
        base = dict(
            state_key="/act/observation/arm_state",
            state_dim=16,
            image_prefix="/act/observation/image/",
            camera_keys=("left", "right"),
            image_shapes=((3, 224, 224), (3, 224, 224)),
            image_layout="CHW",
            image_dtype="float32",
            image_value_range=(0.0, 1.0),
            action_dim=16,
            chunk_size=30,
        )
        base.update(overrides)
        return PolicyInputSpec(**base)

    def test_valid_spec(self) -> None:
        spec = self._valid()
        assert spec.state_dim == STATE_DIM
        assert spec.action_dim == ACTION_DIM
        assert spec.image_layout == IMAGE_LAYOUT
        assert spec.image_dtype == IMAGE_DTYPE
        assert spec.image_value_range == IMAGE_VALUE_RANGE

    def test_frozen(self) -> None:
        spec = self._valid()
        with pytest.raises(FrozenInstanceError):
            spec.state_key = "x"  # type: ignore[misc]

    def test_bad_state_dim_rejected(self) -> None:
        with pytest.raises(DeployConfigError):
            self._valid(state_dim=26)

    def test_unsorted_camera_keys_rejected(self) -> None:
        with pytest.raises(DeployConfigError):
            self._valid(camera_keys=("right", "left"))

    def test_duplicate_camera_keys_rejected(self) -> None:
        with pytest.raises(DeployConfigError):
            self._valid(camera_keys=("left", "left"))

    def test_non_chw_shape_rejected(self) -> None:
        with pytest.raises(DeployConfigError):
            self._valid(image_shapes=((224, 224, 3), (3, 224, 224)))

    def test_nonpositive_shape_rejected(self) -> None:
        with pytest.raises(DeployConfigError):
            self._valid(image_shapes=((3, 0, 224), (3, 224, 224)))

    def test_wrong_dtype_rejected(self) -> None:
        with pytest.raises(DeployConfigError):
            self._valid(image_dtype="uint8")

    def test_wrong_value_range_rejected(self) -> None:
        with pytest.raises(DeployConfigError):
            self._valid(image_value_range=(0.0, 255.0))

    def test_nonpositive_chunk_rejected(self) -> None:
        with pytest.raises(DeployConfigError):
            self._valid(chunk_size=0)


# ---------------------------------------------------------------------------
# load_act_runtime_resources
# ---------------------------------------------------------------------------


class TestLoadActRuntimeResources:
    def test_derives_spec_and_aggregates_policy(self, tmp_path: Path) -> None:
        bundle = _make_bundle(tmp_path)
        cfg = _config_for_bundle(bundle)
        res = load_act_runtime_resources(cfg, load_policy=_fake_loader)

        assert isinstance(res, ActRuntimeResources)
        spec = res.policy_input_spec
        assert spec.state_dim == 16 and spec.action_dim == 16
        assert spec.camera_keys == ("left", "right")
        assert spec.image_shapes == ((3, 224, 224), (3, 224, 224))
        assert spec.image_layout == "CHW"
        # policy aggregated via fake loader
        assert res.policy == ("fake-policy", "bundle")
        # normalizers loaded and 16D
        assert res.state_normalizer.vector_dim == 16
        assert res.action_normalizer.vector_dim == 16
        assert res.cross_check.is_pass
        assert res.bundle_dir == bundle.resolve()

    def test_frozen_aggregate(self, tmp_path: Path) -> None:
        bundle = _make_bundle(tmp_path)
        cfg = _config_for_bundle(bundle)
        res = load_act_runtime_resources(cfg, load_policy=_fake_loader)
        with pytest.raises(FrozenInstanceError):
            res.policy = None  # type: ignore[misc]

    def test_registered_loader_used_when_no_inline(self, tmp_path: Path) -> None:
        bundle = _make_bundle(tmp_path)
        cfg = _config_for_bundle(bundle)
        register_policy_loader(_fake_loader)
        try:
            res = load_act_runtime_resources(cfg)
            assert res.policy == ("fake-policy", "bundle")
        finally:
            register_policy_loader(None)  # clear

    def test_no_loader_raises(self, tmp_path: Path) -> None:
        bundle = _make_bundle(tmp_path)
        cfg = _config_for_bundle(bundle)
        register_policy_loader(None)  # ensure clean state
        with pytest.raises(DeployConfigError, match="No policy loader"):
            load_act_runtime_resources(cfg)

    def test_missing_metadata_fails(self, tmp_path: Path) -> None:
        bundle = _make_bundle(tmp_path, missing={"state_dim"})
        cfg = _config_for_bundle(bundle)
        with pytest.raises(DeployConfigError, match="missing required field"):
            load_act_runtime_resources(cfg, load_policy=_fake_loader)

    def test_normalizer_dim_mismatch_fails(self, tmp_path: Path) -> None:
        bundle = _make_bundle(tmp_path, state_dim=14, action_dim=14)
        # config still declares 16 -> metadata dim 14 != config 16 conflict
        cfg = _config_for_bundle(bundle)
        with pytest.raises(DeployConfigError, match="dimension conflict"):
            load_act_runtime_resources(cfg, load_policy=_fake_loader)

    def test_config_metadata_chunk_mismatch_fails(self, tmp_path: Path) -> None:
        bundle = _make_bundle(tmp_path, chunk_size=50)
        cfg = _config_for_bundle(bundle, chunk_size=30)
        with pytest.raises(DeployConfigError, match="dimension conflict"):
            load_act_runtime_resources(cfg, load_policy=_fake_loader)

    def test_empty_bundle_fails_fast(self, tmp_path: Path) -> None:
        cfg = DeployConfig.from_mapping(
            {
                "bundle": {"bundle_dir": None},
                "runtime": {"mode": "dry-run", "state_dim": 16, "action_dim": 16, "fallback_policy": "hold_last_action"},
                "image": {"image_size": 224},
                "topics": {"namespace": "/act"},
                "safety": {},
            },
            base_dir=Path("/tmp"),
        )
        with pytest.raises(DeployConfigError, match="bundle_dir is empty"):
            load_act_runtime_resources(cfg, load_policy=_fake_loader)
