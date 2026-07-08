"""Tests for normalization.py — ActionStateNormalizer (used by deploy_005)."""

import numpy as np
import pytest

from model_deploy.act.repo.normalization import ActionStateNormalizer


class TestActionStateNormalizer:
    def test_construct_and_fields(self) -> None:
        n = ActionStateNormalizer(min_vals=np.zeros(16), max_vals=np.ones(16))
        assert n.vector_dim == 16
        assert n.min_vals.shape == (16,)
        assert n.max_vals.shape == (16,)
        assert n.range_vals.shape == (16,)
        assert n.identity_mask.shape == (16,)
        assert n.non_zero_mask.shape == (16,)

    def test_normalize_basic(self) -> None:
        n = ActionStateNormalizer(min_vals=[0, 0], max_vals=[10, 10])
        result = n.normalize([5, 5])
        assert result.shape == (2,)
        np.testing.assert_allclose(result, [0.0, 0.0], atol=1e-6)

    def test_normalize_batch(self) -> None:
        n = ActionStateNormalizer(min_vals=[0, 0], max_vals=[10, 10])
        result = n.normalize([[0, 0], [10, 10]])
        np.testing.assert_allclose(result, [[-1, -1], [1, 1]], atol=1e-6)

    def test_unnormalize_basic(self) -> None:
        n = ActionStateNormalizer(min_vals=[0, 0], max_vals=[10, 10])
        result = n.unnormalize([0.0, 1.0])
        np.testing.assert_allclose(result, [5.0, 10.0], atol=1e-6)

    def test_roundtrip(self) -> None:
        n = ActionStateNormalizer(min_vals=np.zeros(16, dtype=np.float32), max_vals=np.ones(16, dtype=np.float32))
        original = np.random.randn(16).astype(np.float32) * 5
        normalized = n.normalize(original)
        restored = n.unnormalize(normalized)
        np.testing.assert_allclose(restored, original, atol=1e-5)

    def test_zero_range_dimension(self) -> None:
        n = ActionStateNormalizer(min_vals=[0, 5], max_vals=[0, 5])
        result = n.normalize([0, 5])
        assert result[0] == 0.0
        assert result[1] == 0.0

    def test_identity_indices(self) -> None:
        n = ActionStateNormalizer(min_vals=[0, 0, 0], max_vals=[10, 10, 10], identity_indices=[2])
        result = n.normalize([5, 5, 7])
        np.testing.assert_allclose(result[:2], [0, 0], atol=1e-6)
        assert result[2] == 7.0  # identity — passed through

    def test_call(self) -> None:
        n = ActionStateNormalizer(min_vals=[0], max_vals=[10])
        assert np.allclose(n([5]), n.normalize([5]))

    def test_dimension_mismatch_raises(self) -> None:
        n = ActionStateNormalizer(min_vals=[0, 0], max_vals=[1, 1])
        with pytest.raises(ValueError):
            n.normalize([1, 2, 3])

    def test_constructor_dim_mismatch_raises(self) -> None:
        with pytest.raises(ValueError, match="must contain"):
            ActionStateNormalizer(min_vals=[0, 0], max_vals=[1, 2, 3])
