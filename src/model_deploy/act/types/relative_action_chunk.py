"""RelativeActionChunk frozen value object for ACT model deployment.

Represents a chunk of *relative* actions output by the ACT inference pipeline
*before* they are decoded into absolute base-frame TCP targets.

``RelativeActionChunk`` is an **L2-03-internal** type: it is produced by the
postprocess stage and consumed only by ``RelativeTcpActionDecoder`` inside
``ActInferenceService``.  It must never cross into ``ControlLoop`` /
``SafetyGuard`` / the publish layer — those downstream stages only ever see the
decoded absolute ``ActionChunk``.

Each row is a 16D action in deploy order ``[L_tcp7, R_tcp7, L_grip, R_grip]``
where the two ``tcp7`` segments are *relative* TCP poses (translation + xyzw
quaternion) expressed against the inference-moment reference, and the two
gripper fields are *absolute* targets carried through unchanged.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from model_deploy.act.types.action_spec import ACTION_DIM


@dataclass(frozen=True)
class RelativeActionChunk:
    """Immutable chunk of relative actions from ACT inference (L2-03-internal).

    This type lives only inside the model inference boundary.  It carries only
    the raw action array; runtime metadata belongs in L2-06.  Downstream
    modules (``ControlLoop``, ``SafetyGuard``, ``ActionOutputAdapter``) consume
    the decoded absolute ``ActionChunk`` and must never receive a
    ``RelativeActionChunk``.

    Attributes:
        actions: float32 ndarray of shape ``(chunk_size, ACTION_DIM)``.
            Each row is a 16D action whose arm segments are relative TCP poses
            and whose gripper segments are absolute targets.
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
