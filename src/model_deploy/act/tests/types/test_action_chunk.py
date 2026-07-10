"""Tests for ActionChunk frozen dataclass."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import numpy as np
import pytest

from model_deploy.act.types.action_chunk import ActionChunk
from model_deploy.act.types.action_spec import ACTION_DIM


# ---------------------------------------------------------------------------
# Valid construction
# ---------------------------------------------------------------------------


def test_valid_construction():
    """Legal (N,16) float32 finite array constructs successfully."""
    arr = np.zeros((5, ACTION_DIM), dtype=np.float32)
    chunk = ActionChunk(actions=arr)
    assert chunk.actions is arr
    assert chunk.actions.shape == (5, ACTION_DIM)
    assert chunk.actions.dtype == np.float32


def test_valid_single_row():
    """Single-row chunk is valid."""
    arr = np.ones((1, ACTION_DIM), dtype=np.float32)
    chunk = ActionChunk(actions=arr)
    assert chunk.actions.shape == (1, ACTION_DIM)


def test_valid_large_chunk():
    """Large chunk size is valid."""
    arr = np.random.randn(100, ACTION_DIM).astype(np.float32)
    chunk = ActionChunk(actions=arr)
    assert chunk.actions.shape == (100, ACTION_DIM)


# ---------------------------------------------------------------------------
# Invalid rank
# ---------------------------------------------------------------------------


def test_invalid_rank_1d():
    """1D array (16,) is rejected."""
    arr = np.zeros((ACTION_DIM,), dtype=np.float32)
    with pytest.raises(ValueError, match="ndim"):
        ActionChunk(actions=arr)


def test_invalid_rank_3d():
    """3D array is rejected."""
    arr = np.zeros((2, 3, ACTION_DIM), dtype=np.float32)
    with pytest.raises(ValueError, match="ndim"):
        ActionChunk(actions=arr)


# ---------------------------------------------------------------------------
# Invalid last dimension
# ---------------------------------------------------------------------------


def test_invalid_dim_too_small():
    """Last dim < 16 is rejected."""
    arr = np.zeros((5, 15), dtype=np.float32)
    with pytest.raises(ValueError, match="last dim"):
        ActionChunk(actions=arr)


def test_invalid_dim_too_large():
    """Last dim > 16 is rejected."""
    arr = np.zeros((5, 17), dtype=np.float32)
    with pytest.raises(ValueError, match="last dim"):
        ActionChunk(actions=arr)


# ---------------------------------------------------------------------------
# Invalid dtype
# ---------------------------------------------------------------------------


def test_invalid_dtype_float64():
    """float64 dtype is rejected."""
    arr = np.zeros((5, ACTION_DIM), dtype=np.float64)
    with pytest.raises(TypeError, match="dtype"):
        ActionChunk(actions=arr)


def test_invalid_dtype_int():
    """int dtype is rejected."""
    arr = np.zeros((5, ACTION_DIM), dtype=np.int32)
    with pytest.raises(TypeError, match="dtype"):
        ActionChunk(actions=arr)


# ---------------------------------------------------------------------------
# NaN / Inf
# ---------------------------------------------------------------------------


def test_nan_rejected():
    """NaN values are rejected."""
    arr = np.zeros((5, ACTION_DIM), dtype=np.float32)
    arr[2, 3] = np.nan
    with pytest.raises(ValueError, match="NaN"):
        ActionChunk(actions=arr)


def test_inf_rejected():
    """Inf values are rejected."""
    arr = np.zeros((5, ACTION_DIM), dtype=np.float32)
    arr[2, 3] = np.inf
    with pytest.raises(ValueError, match="NaN|Inf"):
        ActionChunk(actions=arr)


def test_neg_inf_rejected():
    """-Inf values are rejected."""
    arr = np.zeros((5, ACTION_DIM), dtype=np.float32)
    arr[2, 3] = -np.inf
    with pytest.raises(ValueError, match="NaN|Inf"):
        ActionChunk(actions=arr)


# ---------------------------------------------------------------------------
# Empty chunk
# ---------------------------------------------------------------------------


def test_empty_chunk_rejected():
    """0-row chunk is rejected."""
    arr = np.zeros((0, ACTION_DIM), dtype=np.float32)
    with pytest.raises(ValueError, match="empty"):
        ActionChunk(actions=arr)


# ---------------------------------------------------------------------------
# Frozen / immutable
# ---------------------------------------------------------------------------


def test_frozen_immutable():
    """Cannot reassign actions field after construction."""
    arr = np.zeros((5, ACTION_DIM), dtype=np.float32)
    chunk = ActionChunk(actions=arr)
    with pytest.raises(FrozenInstanceError):
        chunk.actions = np.ones((3, ACTION_DIM), dtype=np.float32)


# ---------------------------------------------------------------------------
# No runtime metadata
# ---------------------------------------------------------------------------


def test_no_runtime_metadata_fields():
    """ActionChunk has no runtime metadata fields or methods."""
    chunk = ActionChunk(actions=np.zeros((5, ACTION_DIM), dtype=np.float32))

    forbidden = [
        "obs_time",
        "infer_start_time",
        "ready_time",
        "action_dt",
        "request_id",
        "cursor",
        "latency",
        "error",
        "metrics",
        "aligned_index",
        "is_expired",
        "remaining_steps",
    ]
    for attr in forbidden:
        assert not hasattr(chunk, attr), f"ActionChunk must not have {attr}"
