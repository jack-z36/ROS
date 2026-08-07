"""Tests for L2-03 primary stage three: action chunk post-processing.

Covers:
  6 independent micro-function unit tests (pass + fail paths)
  1 integration test for the full ``postprocess_action_chunk`` pipeline
"""

from __future__ import annotations

import numpy as np
import pytest
import torch

from model_deploy.act.repo.normalization import ActionStateNormalizer
from model_deploy.act.service.action_chunk_postprocess import (
    check_final_output_contract,
    check_raw_output_structure,
    postprocess_action_chunk,
    remove_batch_dim,
    to_cpu_float32_array,
    unnormalize_actions,
)
from model_deploy.act.types.relative_action_chunk import RelativeActionChunk
from model_deploy.act.types.action_spec import ACTION_DIM

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

CHUNK_SIZE: int = 10


def _make_valid_raw(normalized_value: float = 0.0) -> torch.Tensor:
    """Return a valid (1, CHUNK_SIZE, 16) float32 tensor."""
    return torch.full((1, CHUNK_SIZE, ACTION_DIM), normalized_value, dtype=torch.float32)


def _make_valid_numpy(physical_value: float = 0.5) -> np.ndarray:
    """Return a valid (CHUNK_SIZE, 16) float32 numpy array."""
    return np.full((CHUNK_SIZE, ACTION_DIM), physical_value, dtype=np.float32)


def _make_normalizer(shift: float = 0.0, scale: float = 1.0) -> ActionStateNormalizer:
    """Build a simple ActionStateNormalizer with known min/max.

    unnormalize maps normalized x to:  (x + 1) * 0.5 * range + min.
    With min = shift - scale, max = shift + scale, range = 2*scale:
        unnormalize(x) = (x + 1) * scale + (shift - scale) = x*scale + shift.
    """
    min_vals = np.full(ACTION_DIM, shift - scale, dtype=np.float32)
    max_vals = np.full(ACTION_DIM, shift + scale, dtype=np.float32)
    return ActionStateNormalizer(min_vals=min_vals, max_vals=max_vals)


class RecordingNormalizer:
    """Wrapper that delegates to a real normalizer and records call count."""

    def __init__(self, inner: ActionStateNormalizer) -> None:
        self._inner = inner
        self.call_count: int = 0
        self.last_input: np.ndarray | None = None

    def unnormalize(self, norm_data: np.ndarray) -> np.ndarray:
        self.call_count += 1
        self.last_input = np.asarray(norm_data, dtype=np.float32)
        return self._inner.unnormalize(norm_data)

    @property
    def vector_dim(self) -> int:
        return self._inner.vector_dim


# ---------------------------------------------------------------------------
# Micro ①: check_raw_output_structure
# ---------------------------------------------------------------------------


class TestCheckRawOutputStructure:
    """Unit tests for raw output structure validation."""

    def test_accepts_valid_tensor(self) -> None:
        raw = _make_valid_raw()
        result = check_raw_output_structure(raw, CHUNK_SIZE)
        assert result is raw

    def test_rejects_non_tensor(self) -> None:
        with pytest.raises(TypeError, match="torch.Tensor"):
            check_raw_output_structure(np.zeros((1, CHUNK_SIZE, 16)), CHUNK_SIZE)

    def test_rejects_wrong_rank(self) -> None:
        with pytest.raises(ValueError, match="rank 3"):
            check_raw_output_structure(torch.zeros(CHUNK_SIZE, 16), CHUNK_SIZE)

    def test_rejects_batch_not_one(self) -> None:
        with pytest.raises(ValueError, match="batch dim must be 1"):
            check_raw_output_structure(torch.zeros(3, CHUNK_SIZE, 16), CHUNK_SIZE)

    def test_rejects_wrong_chunk_size(self) -> None:
        with pytest.raises(ValueError, match="chunk dim must be"):
            check_raw_output_structure(torch.zeros(1, CHUNK_SIZE + 1, 16), CHUNK_SIZE)

    def test_rejects_wrong_action_dim(self) -> None:
        with pytest.raises(ValueError, match="action dim must be"):
            check_raw_output_structure(torch.zeros(1, CHUNK_SIZE, 15), CHUNK_SIZE)

    def test_rejects_nan(self) -> None:
        raw = _make_valid_raw()
        raw[0, 0, 0] = float("nan")
        with pytest.raises(ValueError, match="NaN or Inf"):
            check_raw_output_structure(raw, CHUNK_SIZE)

    def test_rejects_inf(self) -> None:
        raw = _make_valid_raw()
        raw[0, 0, 0] = float("inf")
        with pytest.raises(ValueError, match="NaN or Inf"):
            check_raw_output_structure(raw, CHUNK_SIZE)


# ---------------------------------------------------------------------------
# Micro ②: remove_batch_dim
# ---------------------------------------------------------------------------


class TestRemoveBatchDim:
    """Unit tests for batch dimension removal."""

    def test_removes_batch_dim(self) -> None:
        inp = torch.ones(1, CHUNK_SIZE, ACTION_DIM)
        out = remove_batch_dim(inp)
        assert out.shape == (CHUNK_SIZE, ACTION_DIM)
        assert out.ndim == 2

    def test_correct_values(self) -> None:
        inp = torch.arange(1 * CHUNK_SIZE * ACTION_DIM, dtype=torch.float32).reshape(
            1, CHUNK_SIZE, ACTION_DIM
        )
        out = remove_batch_dim(inp)
        expected = inp[0]
        assert torch.equal(out, expected)

    def test_preserves_dtype(self) -> None:
        for dt in (torch.float32, torch.float64):
            inp = torch.ones(1, CHUNK_SIZE, ACTION_DIM, dtype=dt)
            out = remove_batch_dim(inp)
            assert out.dtype == dt


# ---------------------------------------------------------------------------
# Micro ③: unnormalize_actions
# ---------------------------------------------------------------------------


class TestUnnormalizeActions:
    """Unit tests for action unnormalization."""

    def test_calls_normalizer_exactly_once(self) -> None:
        inner = _make_normalizer()
        rec = RecordingNormalizer(inner)
        norm = torch.zeros(CHUNK_SIZE, ACTION_DIM)
        unnormalize_actions(norm, rec)
        assert rec.call_count == 1

    def test_passes_correct_shape(self) -> None:
        inner = _make_normalizer()
        rec = RecordingNormalizer(inner)
        norm = torch.full((CHUNK_SIZE, ACTION_DIM), 0.25)
        unnormalize_actions(norm, rec)
        assert rec.last_input is not None
        assert rec.last_input.shape == (CHUNK_SIZE, ACTION_DIM)

    def test_output_is_float32_numpy(self) -> None:
        inner = _make_normalizer()
        norm = torch.zeros(CHUNK_SIZE, ACTION_DIM)
        result = unnormalize_actions(norm, inner)
        assert isinstance(result, np.ndarray)
        assert result.dtype == np.float32

    def test_identity_normalizer(self) -> None:
        """Normalizer with min=-1, max=1 (range=2) maps x->x (since (x+1)*1-1=x)."""
        inner = _make_normalizer(shift=0.0, scale=1.0)
        norm = torch.full((CHUNK_SIZE, ACTION_DIM), 0.25)
        result = unnormalize_actions(norm, inner)
        expected = np.full((CHUNK_SIZE, ACTION_DIM), 0.25, dtype=np.float32)
        np.testing.assert_array_almost_equal(result, expected)

    def test_no_clamp_applied(self) -> None:
        """Values outside [-1,1] must NOT be clamped."""
        inner = _make_normalizer(shift=0.0, scale=1.0)
        norm = torch.full((CHUNK_SIZE, ACTION_DIM), 2.0)
        result = unnormalize_actions(norm, inner)
        # Without clamp, result should be 2.0, not 1.0
        expected = np.full((CHUNK_SIZE, ACTION_DIM), 2.0, dtype=np.float32)
        np.testing.assert_array_almost_equal(result, expected)


# ---------------------------------------------------------------------------
# Micro ④: to_cpu_float32_array
# ---------------------------------------------------------------------------


class TestToCpuFloat32Array:
    """Unit tests for CPU float32 array conversion."""

    def test_from_tensor(self) -> None:
        t = torch.ones(CHUNK_SIZE, ACTION_DIM, dtype=torch.float32)
        arr = to_cpu_float32_array(t)
        assert isinstance(arr, np.ndarray)
        assert arr.dtype == np.float32
        assert arr.shape == (CHUNK_SIZE, ACTION_DIM)
        assert arr.flags["C_CONTIGUOUS"]

    def test_from_numpy(self) -> None:
        a = np.ones((CHUNK_SIZE, ACTION_DIM), dtype=np.float32)
        arr = to_cpu_float32_array(a)
        assert arr.dtype == np.float32
        assert arr.flags["C_CONTIGUOUS"]

    def test_from_numpy_non_float32(self) -> None:
        a = np.ones((CHUNK_SIZE, ACTION_DIM), dtype=np.float64)
        arr = to_cpu_float32_array(a)
        assert arr.dtype == np.float32

    def test_from_tensor_non_float32(self) -> None:
        t = torch.ones(CHUNK_SIZE, ACTION_DIM, dtype=torch.float64)
        arr = to_cpu_float32_array(t)
        assert arr.dtype == np.float32

    def test_ensures_c_contiguous(self) -> None:
        # Create an F-contiguous array via transpose
        a = np.ones((ACTION_DIM, CHUNK_SIZE), dtype=np.float32).T  # not C-contiguous
        arr = to_cpu_float32_array(a)
        assert arr.flags["C_CONTIGUOUS"]


# ---------------------------------------------------------------------------
# Micro ⑤: check_final_output_contract
# ---------------------------------------------------------------------------


class TestCheckFinalOutputContract:
    """Unit tests for final output contract validation."""

    def test_accepts_valid_array(self) -> None:
        check_final_output_contract(_make_valid_numpy(), CHUNK_SIZE)  # no raise

    def test_rejects_wrong_ndim(self) -> None:
        with pytest.raises(ValueError, match="must be 2D"):
            check_final_output_contract(np.zeros((1, CHUNK_SIZE, 16), dtype=np.float32), CHUNK_SIZE)

    def test_rejects_wrong_rows(self) -> None:
        with pytest.raises(ValueError, match="rows"):
            check_final_output_contract(
                np.zeros((CHUNK_SIZE + 1, ACTION_DIM), dtype=np.float32), CHUNK_SIZE
            )

    def test_rejects_wrong_action_dim(self) -> None:
        with pytest.raises(ValueError, match="last dim"):
            check_final_output_contract(
                np.zeros((CHUNK_SIZE, ACTION_DIM - 1), dtype=np.float32), CHUNK_SIZE
            )

    def test_rejects_non_float32(self) -> None:
        with pytest.raises(TypeError, match="float32"):
            check_final_output_contract(
                np.zeros((CHUNK_SIZE, ACTION_DIM), dtype=np.float64), CHUNK_SIZE
            )

    def test_rejects_nan(self) -> None:
        arr = _make_valid_numpy()
        arr[0, 0] = float("nan")
        with pytest.raises(ValueError, match="NaN or Inf"):
            check_final_output_contract(arr, CHUNK_SIZE)

    def test_rejects_inf(self) -> None:
        arr = _make_valid_numpy()
        arr[0, 0] = float("inf")
        with pytest.raises(ValueError, match="NaN or Inf"):
            check_final_output_contract(arr, CHUNK_SIZE)


# ---------------------------------------------------------------------------
# Micro ⑥ + Integration: postprocess_action_chunk
# ---------------------------------------------------------------------------


class TestPostprocessActionChunk:
    """Integration tests for the full primary stage three pipeline."""

    def test_happy_path(self) -> None:
        norm = _make_normalizer(shift=0.0, scale=1.0)
        raw = torch.full((1, CHUNK_SIZE, ACTION_DIM), 0.25, dtype=torch.float32)
        chunk = postprocess_action_chunk(raw, norm, CHUNK_SIZE)
        assert isinstance(chunk, RelativeActionChunk)
        assert chunk.actions.shape == (CHUNK_SIZE, ACTION_DIM)
        assert chunk.actions.dtype == np.float32
        np.testing.assert_array_almost_equal(
            chunk.actions, np.full((CHUNK_SIZE, ACTION_DIM), 0.25, dtype=np.float32)
        )

    def test_normalizer_called_once(self) -> None:
        inner = _make_normalizer()
        rec = RecordingNormalizer(inner)
        raw = torch.zeros(1, CHUNK_SIZE, ACTION_DIM)
        postprocess_action_chunk(raw, rec, CHUNK_SIZE)
        assert rec.call_count == 1

    def test_propagates_structure_check_failure(self) -> None:
        norm = _make_normalizer()
        with pytest.raises(ValueError, match="rank 3"):
            postprocess_action_chunk(torch.zeros(CHUNK_SIZE, 16), norm, CHUNK_SIZE)

    def test_propagates_nan_failure(self) -> None:
        norm = _make_normalizer()
        raw = _make_valid_raw()
        raw[0, 0, 0] = float("nan")
        with pytest.raises(ValueError, match="NaN or Inf"):
            postprocess_action_chunk(raw, norm, CHUNK_SIZE)

    def test_propagates_wrong_chunk_size(self) -> None:
        norm = _make_normalizer()
        raw = torch.zeros(1, CHUNK_SIZE + 2, ACTION_DIM)
        with pytest.raises(ValueError, match="chunk dim"):
            postprocess_action_chunk(raw, norm, CHUNK_SIZE)

    def test_does_not_clamp(self) -> None:
        norm = _make_normalizer(shift=0.0, scale=1.0)
        raw = torch.full((1, CHUNK_SIZE, ACTION_DIM), 2.5, dtype=torch.float32)
        chunk = postprocess_action_chunk(raw, norm, CHUNK_SIZE)
        np.testing.assert_array_almost_equal(
            chunk.actions, np.full((CHUNK_SIZE, ACTION_DIM), 2.5, dtype=np.float32)
        )

    def test_does_not_truncate_longer_output(self) -> None:
        """Longer output must be *rejected*, not silently truncated."""
        norm = _make_normalizer()
        raw = torch.zeros(1, CHUNK_SIZE + 1, ACTION_DIM)
        with pytest.raises(ValueError, match="chunk dim"):
            postprocess_action_chunk(raw, norm, CHUNK_SIZE)

    def test_does_not_fill_shorter_output(self) -> None:
        """Shorter output must be *rejected*, not padded."""
        norm = _make_normalizer()
        raw = torch.zeros(1, CHUNK_SIZE - 1, ACTION_DIM)
        with pytest.raises(ValueError, match="chunk dim"):
            postprocess_action_chunk(raw, norm, CHUNK_SIZE)

    def test_action_chunk_has_no_runtime_fields(self) -> None:
        norm = _make_normalizer()
        raw = torch.zeros(1, CHUNK_SIZE, ACTION_DIM)
        chunk = postprocess_action_chunk(raw, norm, CHUNK_SIZE)
        # RelativeActionChunk must only have `actions` -- no runtime metadata
        assert not hasattr(chunk, "obs_time")
        assert not hasattr(chunk, "infer_start_time")
        assert not hasattr(chunk, "ready_time")
        assert not hasattr(chunk, "request_id")
        assert not hasattr(chunk, "cursor")

    def test_all_actions_finite_in_happy_path(self) -> None:
        norm = _make_normalizer()
        raw = torch.randn(1, CHUNK_SIZE, ACTION_DIM)
        chunk = postprocess_action_chunk(raw, norm, CHUNK_SIZE)
        assert np.isfinite(chunk.actions).all()

    def test_correct_shape_preserved(self) -> None:
        norm = _make_normalizer()
        for n in (1, 10, 100):
            raw = torch.randn(1, n, ACTION_DIM)
            chunk = postprocess_action_chunk(raw, norm, n)
            assert chunk.actions.shape == (n, ACTION_DIM)
