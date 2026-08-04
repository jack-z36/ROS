"""ActionChunk frozen value object for ACT model deployment.

Represents a chunk of physical actions output by the ACT inference pipeline.
Pure data type -- no runtime metadata, no lifecycle management.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from model_deploy.act.types.action_spec import ACTION_DIM


@dataclass(frozen=True)
class ActionChunk:
    """Immutable chunk of physical actions from ACT inference.

    This is the only cross-module output type from L2-03 to L2-06.  It carries
    only the raw action array; runtime metadata belongs in L2-06.

    Attributes:
        actions: float32 ndarray of shape ``(chunk_size, ACTION_DIM)``.
            Each row is a complete 16D physical action.
    """

    actions: np.ndarray

    def __post_init__(self) -> None:
        """Validate the actions array at construction time."""
        # ndim == 2
        if self.actions.ndim != 2:
            raise ValueError(
                f"actions must be 2D, got ndim={self.actions.ndim}"
            )

        # shape[1] == ACTION_DIM (16)
        if self.actions.shape[1] != ACTION_DIM:
            raise ValueError(
                f"actions last dim must be {ACTION_DIM}, got {self.actions.shape[1]}"
            )

        # dtype == float32
        if self.actions.dtype != np.float32:
            raise TypeError(
                f"actions dtype must be float32, got {self.actions.dtype}"
            )

        # all elements finite
        if not np.isfinite(self.actions).all():
            raise ValueError("actions contains NaN or Inf values")

        # row count > 0
        if self.actions.shape[0] == 0:
            raise ValueError("actions cannot be empty (0 rows)")
