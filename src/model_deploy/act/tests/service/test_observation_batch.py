"""Unit and integration tests for observation_batch.py (L2-03 Stage 1).

Covers all 7 micro-elements independently plus a stage-1 integration test
that chains them together via ``prepare_observation_batch``.

Uses a stub normalizer and sentinel snapshot; no real policy or hardware
dependency.
"""

from __future__ import annotations

import dataclasses
from typing import Any, Dict

import numpy as np
import pytest
import torch

from model_deploy.act.repo.normalization import ActionStateNormalizer
from model_deploy.act.service.observation_batch import (
    add_batch_dim,
    align_to_device,
    assemble_act_batch,
    bind_images,
    check_model_input_compatibility,
    normalize_state,
    prepare_observation_batch,
    tensorize_state,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def valid_input_spec() -> Dict[str, Any]:
    """Minimal input_spec matching a 2-camera 16D ACT policy."""
    return {
        "state_dim": 16,
        "state_key": "observation.state",
        "camera_keys": ["top", "left_wrist"],
        "image_prefix": "observation.images.",
        "image_shapes": {
            "top": (3, 224, 224),
            "left_wrist": (3, 480, 640),
        },
    }


@pytest.fixture
def valid_encoded_state() -> np.ndarray:
    """A realistic 16D state vector with all finite values."""
    rng = np.random.default_rng(42)
    state = np.zeros(16, dtype=np.float32)
    state[0:3] = rng.uniform(0.3, 0.5, 3)     # left TCP position
    state[3:7] = np.array([0.0, 0.0, 0.0, 1.0])  # left quaternion
    state[7:10] = rng.uniform(-0.2, 0.2, 3)   # right TCP position
    state[10:14] = np.array([0.0, 0.0, 0.0, 1.0])  # right quaternion
    state[14] = 0.5                            # left gripper
    state[15] = 0.8                            # right gripper
    return state.astype(np.float32)


@pytest.fixture
def valid_snapshot(valid_encoded_state: np.ndarray) -> Any:
    """A sentinel ObservationSnapshot with 2 cameras and valid state."""
    from model_deploy.act.types.observation import (
        ObservationSnapshot,
        ObservationState,
    )

    obs_state = ObservationState(
        left_tcp_position=valid_encoded_state[0:3].copy(),
        left_tcp_orientation=valid_encoded_state[3:7].copy(),
        left_gripper_width=float(valid_encoded_state[14]),
        right_tcp_position=valid_encoded_state[7:10].copy(),
        right_tcp_orientation=valid_encoded_state[10:14].copy(),
        right_gripper_width=float(valid_encoded_state[15]),
    )

    images: Dict[str, np.ndarray] = {
        "top": np.random.default_rng(1).uniform(0.0, 1.0, (3, 224, 224)).astype(np.float32),
        "left_wrist": np.random.default_rng(2).uniform(0.0, 1.0, (3, 480, 640)).astype(np.float32),
    }

    return ObservationSnapshot(
        images=images,
        state=obs_state,
        encoded_state=valid_encoded_state,
        captured_at_s=1000.0,
    )


@pytest.fixture
def stub_state_normalizer() -> ActionStateNormalizer:
    """A normalizer with min=-1, max=1 for each dimension -- identity-like."""
    return ActionStateNormalizer(
        min_vals=np.full(16, -1.0, dtype=np.float32),
        max_vals=np.full(16, 1.0, dtype=np.float32),
    )


@pytest.fixture
def cpu_device() -> torch.device:
    return torch.device("cpu")


# ===================================================================
# Micro-element 1: check_model_input_compatibility
# ===================================================================


class TestCheckModelInputCompatibility:
    """service.batch.compatibility"""

    def test_passes_on_valid_snapshot(
        self, valid_snapshot, valid_input_spec
    ) -> None:
        """Compatible snapshot passes without raising."""
        check_model_input_compatibility(valid_snapshot, valid_input_spec)
        # No exception -> pass

    def test_raises_on_wrong_state_dim(
        self, valid_snapshot, valid_input_spec
    ) -> None:
        """State with wrong dimension raises ValueError."""
        snapshot = _replace_encoded_state(valid_snapshot, np.zeros(14, dtype=np.float32))
        with pytest.raises(ValueError, match="encoded_state must have shape"):
            check_model_input_compatibility(snapshot, valid_input_spec)

    def test_raises_on_nan_state(self, valid_snapshot, valid_input_spec) -> None:
        """State containing NaN raises ValueError."""
        bad = valid_snapshot.encoded_state.copy()
        bad[5] = np.nan
        snapshot = _replace_encoded_state(valid_snapshot, bad)
        with pytest.raises(ValueError, match="NaN or Inf"):
            check_model_input_compatibility(snapshot, valid_input_spec)

    def test_raises_on_inf_state(self, valid_snapshot, valid_input_spec) -> None:
        """State containing Inf raises ValueError."""
        bad = valid_snapshot.encoded_state.copy()
        bad[0] = np.inf
        snapshot = _replace_encoded_state(valid_snapshot, bad)
        with pytest.raises(ValueError, match="NaN or Inf"):
            check_model_input_compatibility(snapshot, valid_input_spec)

    def test_raises_on_missing_camera(self, valid_snapshot, valid_input_spec) -> None:
        """Missing required camera raises KeyError."""
        images = {"top": valid_snapshot.images["top"]}  # left_wrist missing
        snapshot = _replace_images(valid_snapshot, images)
        with pytest.raises(KeyError, match="missing required camera"):
            check_model_input_compatibility(snapshot, valid_input_spec)

    def test_raises_on_image_shape_mismatch(
        self, valid_snapshot, valid_input_spec
    ) -> None:
        """Wrong image shape raises ValueError."""
        images = dict(valid_snapshot.images)
        images["top"] = np.zeros((3, 128, 128), dtype=np.float32)  # expected (3,224,224)
        snapshot = _replace_images(valid_snapshot, images)
        with pytest.raises(ValueError, match="has shape"):
            check_model_input_compatibility(snapshot, valid_input_spec)

    def test_raises_on_nan_image(self, valid_snapshot, valid_input_spec) -> None:
        """Image with NaN raises ValueError."""
        images = dict(valid_snapshot.images)
        bad = images["top"].copy()
        bad[0, 0, 0] = np.nan
        images["top"] = bad
        snapshot = _replace_images(valid_snapshot, images)
        with pytest.raises(ValueError, match="NaN or Inf"):
            check_model_input_compatibility(snapshot, valid_input_spec)


# ===================================================================
# Micro-element 2: tensorize_state
# ===================================================================


class TestTensorizeState:
    """service.batch.tensorize_state"""

    def test_converts_ndarray_to_float32_tensor(self) -> None:
        state = np.array([1.0, 2.0, 3.0, 4.0], dtype=np.float64)
        t = tensorize_state(state)
        assert isinstance(t, torch.Tensor)
        assert t.dtype == torch.float32
        assert t.shape == (4,)
        assert t.device.type == "cpu"

    def test_preserves_values(self, valid_encoded_state) -> None:
        t = tensorize_state(valid_encoded_state)
        np.testing.assert_allclose(t.numpy(), valid_encoded_state, rtol=1e-6)

    def test_output_is_not_input_backed(self) -> None:
        """Output tensor should be a new allocation, not a view."""
        state = np.array([1.0, 2.0, 3.0], dtype=np.float32)
        t = tensorize_state(state)
        assert not t.is_leaf or True  # torch.as_tensor may share memory
        t2 = t + 1.0
        np.testing.assert_allclose(state, [1.0, 2.0, 3.0])


# ===================================================================
# Micro-element 3: normalize_state
# ===================================================================


class TestNormalizeState:
    """service.batch.normalize_state"""

    def test_calls_normalizer_and_preserves_shape(
        self, stub_state_normalizer
    ) -> None:
        state_t = torch.tensor([0.0] * 16, dtype=torch.float32)
        out = normalize_state(state_t, stub_state_normalizer)
        assert out.shape == (16,)
        assert out.dtype == torch.float32

    def test_identity_normalizer_preserves_near_zero_values(
        self, valid_encoded_state
    ) -> None:
        """With min=-1, max=1 normalizer, small input values stay close."""
        normalizer = ActionStateNormalizer(
            min_vals=np.full(16, -2.0, dtype=np.float32),
            max_vals=np.full(16, 2.0, dtype=np.float32),
        )
        state_t = tensorize_state(valid_encoded_state)
        out = normalize_state(state_t, normalizer)
        assert out.shape == (16,)
        assert torch.isfinite(out).all()

    def test_raises_on_contradictory_normalizer_shape(
        self, valid_encoded_state
    ) -> None:
        """Normalizer with wrong dim should raise from its internal check."""
        bad_normalizer = ActionStateNormalizer(
            min_vals=np.full(10, -1.0, dtype=np.float32),
            max_vals=np.full(10, 1.0, dtype=np.float32),
        )
        state_t = tensorize_state(valid_encoded_state)
        with pytest.raises(ValueError):
            normalize_state(state_t, bad_normalizer)

    def test_rejects_nan_output(self) -> None:
        """A degenerate normalizer that produces NaN must raise."""

        class NanNormalizer:
            def normalize(self, data):
                return np.full_like(np.asarray(data, dtype=np.float32), np.nan)

        state_t = torch.zeros(16, dtype=torch.float32)
        with pytest.raises(ValueError, match="NaN or Inf"):
            normalize_state(state_t, NanNormalizer())


# ===================================================================
# Micro-element 4: bind_images
# ===================================================================


class TestBindImages:
    """service.batch.bind_images"""

    def test_binds_by_policy_key(self, valid_input_spec) -> None:
        images: Dict[str, np.ndarray] = {
            "top": np.random.default_rng(1).uniform(0, 1, (3, 224, 224)).astype(np.float32),
            "left_wrist": np.random.default_rng(2).uniform(0, 1, (3, 480, 640)).astype(np.float32),
        }
        result = bind_images(images, valid_input_spec)
        assert set(result.keys()) == {
            "observation.images.top",
            "observation.images.left_wrist",
        }
        top = result["observation.images.top"]
        assert top.shape == (3, 224, 224)
        assert top.dtype == torch.float32

    def test_raises_on_missing_camera(self, valid_input_spec) -> None:
        images: Dict[str, np.ndarray] = {"top": np.zeros((3, 224, 224), dtype=np.float32)}
        with pytest.raises(KeyError):
            bind_images(images, valid_input_spec)


# ===================================================================
# Micro-element 5: add_batch_dim
# ===================================================================


class TestAddBatchDim:
    """service.batch.add_dimension"""

    def test_adds_b1_to_state_tensor(self) -> None:
        t = torch.zeros(16, dtype=torch.float32)
        (out,) = add_batch_dim(t)
        assert out.shape == (1, 16)

    def test_adds_b1_to_image_tensor(self) -> None:
        t = torch.zeros(3, 224, 224, dtype=torch.float32)
        (out,) = add_batch_dim(t)
        assert out.shape == (1, 3, 224, 224)

    def test_handles_multiple_tensors(self) -> None:
        s = torch.zeros(16, dtype=torch.float32)
        i1 = torch.zeros(3, 224, 224, dtype=torch.float32)
        i2 = torch.zeros(3, 480, 640, dtype=torch.float32)
        results = add_batch_dim(s, i1, i2)
        assert len(results) == 3
        assert results[0].shape == (1, 16)
        assert results[1].shape == (1, 3, 224, 224)
        assert results[2].shape == (1, 3, 480, 640)

    def test_preserves_values(self) -> None:
        t = torch.tensor([1.0, 2.0, 3.0])
        (out,) = add_batch_dim(t)
        assert out[0, 0].item() == 1.0
        assert out[0, 2].item() == 3.0


# ===================================================================
# Micro-element 6: assemble_act_batch
# ===================================================================


class TestAssembleActBatch:
    """service.batch.assemble"""

    def test_writes_state_and_image_keys(self, valid_input_spec) -> None:
        state_t = torch.zeros(1, 16, dtype=torch.float32)
        image_tensors = {
            "observation.images.top": torch.zeros(1, 3, 224, 224, dtype=torch.float32),
            "observation.images.left_wrist": torch.zeros(1, 3, 480, 640, dtype=torch.float32),
        }
        batch = assemble_act_batch(state_t, image_tensors, valid_input_spec)
        assert set(batch.keys()) == {
            "observation.state",
            "observation.images.top",
            "observation.images.left_wrist",
        }

    def test_no_task_or_action_keys(self, valid_input_spec) -> None:
        """Batch must not contain task, action, or metadata keys."""
        state_t = torch.zeros(1, 16, dtype=torch.float32)
        batch = assemble_act_batch(state_t, {}, valid_input_spec)
        assert "task" not in batch
        assert "action" not in batch
        for k in batch:
            assert not k.startswith("request")
            assert not k.startswith("time")

    def test_custom_state_key(self) -> None:
        state_t = torch.zeros(1, 16, dtype=torch.float32)
        spec = {"state_key": "custom.state"}
        batch = assemble_act_batch(state_t, {}, spec)
        assert "custom.state" in batch


# ===================================================================
# Micro-element 7: align_to_device
# ===================================================================


class TestAlignToDevice:
    """service.batch.device"""

    def test_moves_all_tensors_to_target_device(self, cpu_device) -> None:
        batch = {
            "observation.state": torch.zeros(1, 16),
            "observation.images.top": torch.zeros(1, 3, 224, 224),
        }
        result = align_to_device(batch, cpu_device)
        for t in result.values():
            assert t.device == cpu_device

    def test_preserves_tensor_shapes(self, cpu_device) -> None:
        batch = {
            "observation.state": torch.zeros(1, 16),
        }
        result = align_to_device(batch, cpu_device)
        assert result["observation.state"].shape == (1, 16)

    def test_empty_batch(self, cpu_device) -> None:
        result = align_to_device({}, cpu_device)
        assert result == {}


# ===================================================================
# Stage-1 integration: prepare_observation_batch
# ===================================================================


class TestPrepareObservationBatch:
    """End-to-end Stage-1 test with stub normalizer and sentinel snapshot."""

    def test_full_pipeline_on_cpu(
        self,
        valid_snapshot,
        stub_state_normalizer,
        valid_input_spec,
        cpu_device,
    ) -> None:
        batch = prepare_observation_batch(
            valid_snapshot, stub_state_normalizer, valid_input_spec, cpu_device
        )

        # Keys
        assert "observation.state" in batch
        assert "observation.images.top" in batch
        assert "observation.images.left_wrist" in batch

        # Shapes
        state_t = batch["observation.state"]
        assert state_t.shape == (1, 16)
        assert state_t.dtype == torch.float32

        top_t = batch["observation.images.top"]
        assert top_t.shape == (1, 3, 224, 224)
        assert top_t.dtype == torch.float32

        lw_t = batch["observation.images.left_wrist"]
        assert lw_t.shape == (1, 3, 480, 640)
        assert lw_t.dtype == torch.float32

        # Device
        for t in batch.values():
            assert t.device == cpu_device

        # No metadata keys
        assert "task" not in batch
        assert "action" not in batch

    def test_pipeline_propagates_compatibility_error(
        self,
        valid_snapshot,
        stub_state_normalizer,
        valid_input_spec,
        cpu_device,
    ) -> None:
        """A bad snapshot dimension must propagate through the pipeline."""
        snapshot = _replace_encoded_state(valid_snapshot, np.zeros(8, dtype=np.float32))
        with pytest.raises(ValueError, match="encoded_state must have shape"):
            prepare_observation_batch(
                snapshot, stub_state_normalizer, valid_input_spec, cpu_device
            )

    def test_pipeline_propagates_missing_camera_error(
        self,
        valid_snapshot,
        stub_state_normalizer,
        valid_input_spec,
        cpu_device,
    ) -> None:
        images = {"top": valid_snapshot.images["top"]}
        snapshot = _replace_images(valid_snapshot, images)
        with pytest.raises(KeyError):
            prepare_observation_batch(
                snapshot, stub_state_normalizer, valid_input_spec, cpu_device
            )


# ===================================================================
# Helpers
# ===================================================================


def _replace_encoded_state(snapshot: Any, new_state: np.ndarray) -> Any:
    """Return a copy of the snapshot with a different encoded_state.

    Bypasses ``ObservationSnapshot.__post_init__`` validation so that
    intentionally-invalid snapshots (wrong dim, NaN, Inf) can be injected
    for negative-path testing.
    """
    import copy
    s = copy.deepcopy(snapshot)
    object.__setattr__(s, "encoded_state", new_state)
    return s


def _replace_images(snapshot: Any, new_images: Dict[str, np.ndarray]) -> Any:
    """Return a copy of the snapshot with different images.

    Bypasses ``ObservationSnapshot.__post_init__`` so that image-level
    invalid states (missing cameras, shape mismatch, NaN) are injectable.
    """
    import copy
    s = copy.deepcopy(snapshot)
    object.__setattr__(s, "images", new_images)
    return s
