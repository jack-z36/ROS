"""Raw-checkpoint direct-load tests.

Covers the second source layout accepted by ``load_act_runtime_resources``:
a raw training checkpoint directory (``.../checkpoints/<step>`` carrying
``pretrained_model/config.json``) is loaded directly, without first building a
packaged ``deploy_bundle``.

The checkpoint path derives its dimensions from ``pretrained_model/config.json``,
takes the action-representation contract from ``deploy.yaml`` (no manifest to
cross-validate), and uses a synthetic identity normalizer (the real MEAN_STD
statistics live inside the policy wrapper).  The injected loader receives the
resolved ``pretrained_model`` directory directly.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from model_deploy.act.config.schema import DeployConfig, DeployConfigError
from model_deploy.act.repo import load_act_runtime_resources
from model_deploy.act.repo.bundle_reader import (
    BundleStructureError,
    is_bundle_dir,
    is_checkpoint_dir,
    resolve_pretrained_dir,
)


# ---------------------------------------------------------------------------
# Fixture builders
# ---------------------------------------------------------------------------


def _make_checkpoint(
    base: Path,
    *,
    state_dim: int = 16,
    action_dim: int = 16,
    chunk_size: int = 100,
    with_pretrained_subdir: bool = True,
) -> Path:
    """Create a mock raw-checkpoint directory.

    When *with_pretrained_subdir* is ``True`` the layout is
    ``<base>/pretrained_model/config.json`` (mirrors a real
    ``.../checkpoints/100000/``).  When ``False`` the ``config.json`` is
    written directly under ``<base>`` (mirrors the caller pointing at the
    inner ``pretrained_model/`` directory itself).
    """
    base.mkdir(parents=True, exist_ok=True)
    if with_pretrained_subdir:
        pretrained = base / "pretrained_model"
    else:
        pretrained = base
    pretrained.mkdir(parents=True, exist_ok=True)

    config = {
        "type": "act",
        "chunk_size": chunk_size,
        "input_features": {
            "observation.state": {"type": "STATE", "shape": [state_dim]},
            "observation.images.left": {"type": "VISUAL", "shape": [3, 480, 640]},
            "observation.images.right": {"type": "VISUAL", "shape": [3, 480, 640]},
        },
        "output_features": {
            "action": {"type": "ACTION", "shape": [action_dim]},
        },
    }
    (pretrained / "config.json").write_text(json.dumps(config), encoding="utf-8")
    # Placeholder weight + stats files (the fake loader does not read them).
    (pretrained / "model.safetensors").write_text("dummy")
    return base


def _config_for_source(
    source_dir: Path,
    *,
    state_dim: int = 16,
    action_dim: int = 16,
    chunk_size: int = 100,
) -> DeployConfig:
    raw = {
        "bundle": {"bundle_dir": str(source_dir)},
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


class _RecordingLoader:
    """Fake policy loader that records the directory it receives."""

    def __init__(self) -> None:
        self.received: Path | None = None

    def __call__(self, source_dir: Path):
        self.received = Path(source_dir)
        return ("fake-policy", source_dir.name)


# ---------------------------------------------------------------------------
# Layout detection
# ---------------------------------------------------------------------------


class TestLayoutDetection:
    def test_checkpoint_root_detected(self, tmp_path: Path) -> None:
        ckpt = _make_checkpoint(tmp_path / "ckpt")
        assert is_checkpoint_dir(ckpt) is True
        # A checkpoint root is not a bundle (no manifest.json).
        assert is_bundle_dir(ckpt) is False

    def test_pretrained_model_dir_detected(self, tmp_path: Path) -> None:
        ckpt = _make_checkpoint(tmp_path / "ckpt", with_pretrained_subdir=False)
        # The inner pretrained_model/ directory is itself a checkpoint dir.
        assert is_checkpoint_dir(ckpt) is True

    def test_empty_dir_is_neither(self, tmp_path: Path) -> None:
        empty = tmp_path / "empty"
        empty.mkdir()
        assert is_checkpoint_dir(empty) is False
        assert is_bundle_dir(empty) is False


# ---------------------------------------------------------------------------
# resolve_pretrained_dir
# ---------------------------------------------------------------------------


class TestResolvePretrainedDir:
    def test_checkpoint_root_resolves_inner_pretrained(self, tmp_path: Path) -> None:
        ckpt = _make_checkpoint(tmp_path / "ckpt")
        pretrained = resolve_pretrained_dir(ckpt)
        assert pretrained == (ckpt / "pretrained_model").resolve()
        assert (pretrained / "config.json").is_file()

    def test_pretrained_dir_resolves_to_itself(self, tmp_path: Path) -> None:
        ckpt = _make_checkpoint(tmp_path / "ckpt", with_pretrained_subdir=False)
        pretrained = resolve_pretrained_dir(ckpt)
        assert pretrained == ckpt.resolve()
        assert (pretrained / "config.json").is_file()

    def test_unknown_dir_raises(self, tmp_path: Path) -> None:
        empty = tmp_path / "empty"
        empty.mkdir()
        with pytest.raises(BundleStructureError):
            resolve_pretrained_dir(empty)


# ---------------------------------------------------------------------------
# load_act_runtime_resources — checkpoint path
# ---------------------------------------------------------------------------


class TestCheckpointDirectLoad:
    def test_loads_from_checkpoint_root(self, tmp_path: Path) -> None:
        ckpt = _make_checkpoint(tmp_path / "ckpt", chunk_size=100)
        cfg = _config_for_source(ckpt, chunk_size=100)
        loader = _RecordingLoader()

        res = load_act_runtime_resources(cfg, load_policy=loader)

        # The loader receives the resolved pretrained_model directory, not the
        # checkpoint root.
        assert loader.received == (ckpt / "pretrained_model").resolve()
        assert res.policy == ("fake-policy", "pretrained_model")
        # Dimensions derived from config.json.
        assert res.policy_input_spec.state_dim == 16
        assert res.policy_input_spec.action_dim == 16
        assert res.policy_input_spec.chunk_size == 100

    def test_loads_from_inner_pretrained_dir(self, tmp_path: Path) -> None:
        ckpt = _make_checkpoint(tmp_path / "ckpt", with_pretrained_subdir=False, chunk_size=100)
        cfg = _config_for_source(ckpt, chunk_size=100)
        loader = _RecordingLoader()

        res = load_act_runtime_resources(cfg, load_policy=loader)

        # When the caller points directly at pretrained_model/, the loader
        # receives that same directory.
        assert loader.received == ckpt.resolve()
        assert res.policy_input_spec.chunk_size == 100

    def test_identity_normalizer_is_passthrough(self, tmp_path: Path) -> None:
        ckpt = _make_checkpoint(tmp_path / "ckpt", chunk_size=100)
        cfg = _config_for_source(ckpt, chunk_size=100)

        res = load_act_runtime_resources(cfg, load_policy=lambda d: "p")

        # The synthetic identity normalizer must be a true passthrough: any
        # finite vector maps to itself (so unnormalize is a no-op).
        sample = np.arange(16, dtype=np.float32)
        np.testing.assert_array_equal(res.state_normalizer.normalize(sample), sample)
        np.testing.assert_array_equal(res.action_normalizer.unnormalize(sample), sample)
        assert res.state_normalizer.vector_dim == 16
        assert res.action_normalizer.vector_dim == 16

    def test_action_representation_taken_from_config(self, tmp_path: Path) -> None:
        ckpt = _make_checkpoint(tmp_path / "ckpt", chunk_size=100)
        cfg = _config_for_source(ckpt, chunk_size=100)

        res = load_act_runtime_resources(cfg, load_policy=lambda d: "p")

        # The spec mirrors the deploy.yaml relative-action defaults.
        spec = res.action_representation_spec
        assert spec.arm_action_type == "relative_tcp_pose"
        assert spec.chunk_reference == "inference_observation"
        assert spec.translation_frame == "tcp_local"
        assert spec.rotation_representation == "quaternion_xyzw"
        assert spec.gripper_action_type == "absolute"

    def test_chunk_size_conflict_fails_fast(self, tmp_path: Path) -> None:
        ckpt = _make_checkpoint(tmp_path / "ckpt", chunk_size=100)
        # deploy.yaml declares chunk_size=30 but config.json says 100.
        cfg = _config_for_source(ckpt, chunk_size=30)

        with pytest.raises(DeployConfigError, match="chunk_size 100 != config runtime.chunk_size 30"):
            load_act_runtime_resources(cfg, load_policy=lambda d: "p")

    def test_state_dim_conflict_fails_fast(self, tmp_path: Path) -> None:
        ckpt = _make_checkpoint(tmp_path / "ckpt", state_dim=16, chunk_size=100)
        # deploy.yaml declares state_dim=14 but config.json says 16.
        cfg = _config_for_source(ckpt, state_dim=14, action_dim=16, chunk_size=100)

        with pytest.raises(DeployConfigError, match="state_dim 16 != config runtime.state_dim 14"):
            load_act_runtime_resources(cfg, load_policy=lambda d: "p")

    def test_missing_chunk_size_in_config_json_fails_fast(self, tmp_path: Path) -> None:
        ckpt = _make_checkpoint(tmp_path / "ckpt", chunk_size=100)
        # Corrupt the config.json: drop chunk_size.
        cfg_path = ckpt / "pretrained_model" / "config.json"
        data = json.loads(cfg_path.read_text())
        del data["chunk_size"]
        cfg_path.write_text(json.dumps(data))
        cfg = _config_for_source(ckpt, chunk_size=100)

        with pytest.raises(DeployConfigError, match="missing required field 'chunk_size'"):
            load_act_runtime_resources(cfg, load_policy=lambda d: "p")

    def test_neither_bundle_nor_checkpoint_fails_fast(self, tmp_path: Path) -> None:
        empty = tmp_path / "empty"
        empty.mkdir()
        cfg = _config_for_source(empty, chunk_size=100)

        with pytest.raises(DeployConfigError, match="neither a packaged bundle"):
            load_act_runtime_resources(cfg, load_policy=lambda d: "p")

    def test_missing_pretrained_config_fails_fast(self, tmp_path: Path) -> None:
        # A directory that looks like a checkpoint (has pretrained_model/) but
        # the config.json is missing inside it.
        ckpt = tmp_path / "ckpt"
        (ckpt / "pretrained_model").mkdir(parents=True)
        cfg = _config_for_source(ckpt, chunk_size=100)

        with pytest.raises(DeployConfigError):
            load_act_runtime_resources(cfg, load_policy=lambda d: "p")


# ---------------------------------------------------------------------------
# Regression: bundle path still works alongside the new checkpoint path
# ---------------------------------------------------------------------------


class TestBundlePathStillWorks:
    """The pre-existing bundle loading path must remain unchanged."""

    def _make_bundle(self, base: Path, *, chunk_size: int = 30) -> Path:
        import yaml

        bundle = base / "bundle"
        bundle.mkdir()
        (bundle / "adapter").mkdir()
        (bundle / "checkpoint.pt").write_text("dummy")
        manifest = {
            "schema_version": 1,
            "model": {
                "state_dim": 16,
                "action_dim": 16,
                "chunk_size": chunk_size,
                "pretrained_path": "adapter/pretrained_model",
            },
            "action_representation": {
                "arm_action_type": "relative_tcp_pose",
                "chunk_reference": "inference_observation",
                "translation_frame": "tcp_local",
                "rotation_representation": "quaternion_xyzw",
                "gripper_action_type": "absolute",
            },
        }
        (bundle / "manifest.json").write_text(json.dumps(manifest))
        normalizers = {
            "state": {"min": [0.0] * 16, "max": [1.0] * 16, "identity_indices": []},
            "action": {"min": [-1.0] * 16, "max": [1.0] * 16, "identity_indices": []},
        }
        (bundle / "normalizers.json").write_text(json.dumps(normalizers))
        (bundle / "experiment_config.yaml").write_text(
            yaml.safe_dump({"state_dim": 16, "action_dim": 16, "chunk_size": chunk_size})
        )
        return bundle

    def test_bundle_loads_and_loader_receives_bundle_dir(self, tmp_path: Path) -> None:
        bundle = self._make_bundle(tmp_path, chunk_size=30)
        cfg = _config_for_source(bundle, chunk_size=30)
        loader = _RecordingLoader()

        res = load_act_runtime_resources(cfg, load_policy=loader)

        # Bundle mode: the loader receives the bundle dir (the closure then
        # resolves the pretrained dir from the manifest).
        assert loader.received == bundle.resolve()
        assert res.policy_input_spec.chunk_size == 30
        assert is_bundle_dir(bundle) is True
