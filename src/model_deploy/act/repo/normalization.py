"""Min-max normalizer for ACT state and action vectors.

Preserves the Pi0.5 ActionStateNormalizer structure: constructor signature,
field names, normalize/unnormalize methods. Uses numpy instead of torch to
avoid heavy ML dependencies in the contract-check layer.
"""

from __future__ import annotations

from typing import Iterable, Sequence

import numpy as np


class ActionStateNormalizer:
    """Min-max normalizer for state or action vectors.

    The forward mapping is:
        y = 2 * (x - min) / (max - min) - 1

    For degenerate dimensions where ``max == min``, the normalized value is
    forced to ``0.0`` to avoid division by zero.

    Constructor signature and field names are preserved from Pi0.5:
        ``min_vals``, ``max_vals``, ``range_vals``, ``identity_mask``,
        ``vector_dim``, ``normalize(data)``, ``unnormalize(norm_data)``.
    """

    def __init__(
        self,
        min_vals: np.ndarray | Iterable[float],
        max_vals: np.ndarray | Iterable[float],
        identity_indices: Sequence[int] | np.ndarray | None = None,
    ) -> None:
        self.min_vals = self._as_vector(min_vals, name="min_vals")
        self.vector_dim = int(self.min_vals.shape[0])
        self.max_vals = self._as_vector(max_vals, name="max_vals", expected_dim=self.vector_dim)
        self.range_vals = self.max_vals - self.min_vals
        self.non_zero_mask = self.range_vals != 0.0
        self.identity_mask = self._build_identity_mask(identity_indices)

    def normalize(self, data: np.ndarray | Iterable[float]) -> np.ndarray:
        """Normalize data to the closed interval [-1, 1].

        Args:
            data: Array whose last dimension must equal ``vector_dim``.

        Returns:
            Normalized ``np.ndarray`` with same shape as input, dtype float32.
        """
        arr = self._as_array(data)
        # Broadcast 1-D parameter vectors to match the input shape
        normalized = np.where(
            self.non_zero_mask,
            2.0 * (arr - self.min_vals) / self.range_vals - 1.0,
            0.0,
        )
        normalized = np.where(self.identity_mask, arr, normalized)
        return normalized.astype(np.float32)

    def unnormalize(self, norm_data: np.ndarray | Iterable[float]) -> np.ndarray:
        """Restore normalized data back to the original physical scale.

        Args:
            norm_data: Array whose last dimension must equal ``vector_dim``.

        Returns:
            Un-normalized ``np.ndarray`` with same shape as input, dtype float32.
        """
        arr = self._as_array(norm_data)
        restored = np.where(
            self.non_zero_mask,
            (arr + 1.0) * 0.5 * self.range_vals + self.min_vals,
            self.min_vals,
        )
        restored = np.where(self.identity_mask, arr, restored)
        return restored.astype(np.float32)

    def __call__(self, data: np.ndarray | Iterable[float]) -> np.ndarray:
        return self.normalize(data)

    # ------------------------------------------------------------------
    # Internal helpers (preserved structure from Pi0.5)
    # ------------------------------------------------------------------

    @staticmethod
    def _as_vector(
        values: np.ndarray | Iterable[float],
        name: str,
        expected_dim: int | None = None,
    ) -> np.ndarray:
        arr = np.asarray(values, dtype=np.float32).ravel()
        if expected_dim is not None and arr.shape[0] != expected_dim:
            raise ValueError(
                f"{name} must contain {expected_dim} values, got {arr.shape[0]}"
            )
        return arr

    def _as_array(self, data: np.ndarray | Iterable[float]) -> np.ndarray:
        arr = np.asarray(data, dtype=np.float32)
        if arr.shape[-1] != self.vector_dim:
            raise ValueError(
                f"Expected last dimension to be {self.vector_dim}, got {arr.shape}"
            )
        return arr

    def _build_identity_mask(
        self,
        identity_indices: Sequence[int] | np.ndarray | None,
    ) -> np.ndarray:
        mask = np.zeros(self.vector_dim, dtype=bool)
        if identity_indices is None:
            return mask
        indices = np.asarray(identity_indices)
        if indices.dtype == bool:
            indices = indices.ravel()
            if indices.shape[0] != self.vector_dim:
                raise ValueError(
                    f"identity mask must contain {self.vector_dim} values, "
                    f"got {indices.shape[0]}"
                )
            return indices.astype(bool)
        for idx in indices.ravel().tolist():
            idx = int(idx)
            if idx < 0 or idx >= self.vector_dim:
                raise ValueError(
                    f"identity index {idx} is outside vector dim {self.vector_dim}"
                )
            mask[idx] = True
        return mask


def make_identity_normalizer(vector_dim: int) -> ActionStateNormalizer:
    """Build a deployment passthrough normalizer for native LeRobot checkpoints.

    LeRobot's MEAN_STD statistics are consumed by the policy wrapper.  The
    surrounding deployment contract still expects an ``ActionStateNormalizer``
    object, so this helper makes that boundary explicit without reinterpreting
    MEAN_STD statistics as min-max values.
    """
    if not isinstance(vector_dim, int) or isinstance(vector_dim, bool) or vector_dim <= 0:
        raise ValueError(f"vector_dim must be a positive integer, got {vector_dim!r}")
    values = np.arange(vector_dim, dtype=np.int64)
    return ActionStateNormalizer(
        min_vals=np.zeros(vector_dim, dtype=np.float32),
        max_vals=np.ones(vector_dim, dtype=np.float32),
        identity_indices=values,
    )
