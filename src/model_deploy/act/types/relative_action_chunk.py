"""Internal ACT relative action chunk type."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from model_deploy.act.types.action_spec import ACTION_DIM


@dataclass(frozen=True)
class RelativeActionChunk:
    """Physical relative TCP actions before reference-state decoding."""

    actions: np.ndarray

    def __post_init__(self) -> None:
        if self.actions.ndim != 2:
            raise ValueError(f"actions must be 2D, got ndim={self.actions.ndim}")
        if self.actions.shape[1] != ACTION_DIM:
            raise ValueError(
                f"actions last dim must be {ACTION_DIM}, got {self.actions.shape[1]}"
            )
        if self.actions.dtype != np.float32:
            raise TypeError(
                f"actions dtype must be float32, got {self.actions.dtype}"
            )
        if not np.isfinite(self.actions).all():
            raise ValueError("actions contains NaN or Inf values")
        if self.actions.shape[0] == 0:
            raise ValueError("actions cannot be empty (0 rows)")
