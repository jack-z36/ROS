"""ActInferenceService: L2-03 orchestration entry point for ACT inference.

Holds four read-only dependencies injected by L2-01 and wired by L2-06.
Chains three primary stages (deploy_022, this module, deploy_023) to
convert ObservationSnapshot -> ActionChunk in one synchronous call.

Public entry point:
    predict_action_chunk(observation: ObservationSnapshot) -> ActionChunk
"""

from __future__ import annotations

from typing import Any, Dict

import torch

from model_deploy.act.config.schema import DeployConfig
from model_deploy.act.repo.normalization import ActionStateNormalizer
from model_deploy.act.service.action_chunk_postprocess import postprocess_action_chunk
from model_deploy.act.service.observation_batch import prepare_observation_batch
from model_deploy.act.types.action_chunk import ActionChunk
from model_deploy.act.types.action_spec import ACTION_DIM
from model_deploy.act.types.observation import ObservationSnapshot


# ---------------------------------------------------------------------------
# Primary stage 2: ACT forward inference
# ---------------------------------------------------------------------------


def run_act_inference(
    policy: object,
    batch: Dict[str, torch.Tensor],
) -> torch.Tensor:
    """Run a single ACT chunk forward pass under ``torch.no_grad()``.

    Calls ``policy.predict_action_chunk(batch)`` exactly once and returns
    the raw output tensor unchanged.  No unnormalization, shape repair,
    timing, or retry is performed.

    Args:
        policy: Loaded ACT policy exposing ``predict_action_chunk``.
        batch:  ACT observation batch on the policy device.

    Returns:
        Raw normalized action tensor, expected shape
        ``(1, chunk_size, ACTION_DIM)``.

    Raises:
        Propagates any exception from the policy forward pass.
    """
    with torch.no_grad():
        return policy.predict_action_chunk(batch)


# ---------------------------------------------------------------------------
# ActInferenceService
# ---------------------------------------------------------------------------


class ActInferenceService:
    """Thin orchestration class for ObservationSnapshot -> ActionChunk inference.

    Holds four read-only dependencies (config, two normalizers, policy) plus
    a derived ``input_spec``.  Owns no scheduling state, queue, cursor,
    metrics, or fallback logic.

    The single public method ``predict_action_chunk`` is the only interface
    that L2-06 is allowed to call on L2-03.
    """

    def __init__(
        self,
        config: DeployConfig,
        state_normalizer: ActionStateNormalizer,
        action_normalizer: ActionStateNormalizer,
        policy: object,
    ) -> None:
        """Create the inference service from four L2-01 injected dependencies.

        Derives ``input_spec`` from the loaded policy's RAM metadata,
        resolves the inference device from policy parameters, and validates
        that the four dependencies form a consistent contract.

        Args:
            config:             Frozen ``DeployConfig`` from L2-01.
            state_normalizer:   Normalizer instance (``normalize`` direction).
            action_normalizer:  Normalizer instance (``unnormalize`` direction).
            policy:             Loaded ACT policy exposing
                                ``predict_action_chunk``.

        Raises:
            AttributeError: Policy does not expose ``predict_action_chunk``.
            ValueError:    Dimension mismatch between config, normalizers,
                           and policy metadata.
        """
        self._config = config
        self._state_normalizer = state_normalizer
        self._action_normalizer = action_normalizer
        self._policy = policy

        # Derive input_spec from policy RAM metadata
        self._input_spec = self._derive_input_spec()

        # Resolve inference device from policy parameters
        self._device = self._resolve_device()

        # Validate contract consistency
        self._validate_contract()

    # -- input_spec derivation --------------------------------------------

    def _derive_input_spec(self) -> Dict[str, Any]:
        """Derive read-only input specification from policy RAM metadata.

        Inspects ``policy.config.input_features`` for state/image keys and
        shapes, ``policy.config.output_features`` for ``action_dim``, and
        ``policy.config.chunk_size`` for the chunk size.

        Falls back to ``DeployConfig`` and ``ACTION_DIM`` defaults when
        policy metadata is incomplete.
        """
        policy = self._policy
        policy_cfg = getattr(policy, "config", None)

        # -- chunk_size --
        chunk_size = self._config.runtime.chunk_size
        if policy_cfg is not None:
            chunk_size = getattr(policy_cfg, "chunk_size", chunk_size)

        # -- input features --
        input_features: Dict[str, Any] = {}
        if policy_cfg is not None:
            input_features = getattr(policy_cfg, "input_features", {}) or {}

        # -- state --
        state_key = "observation.state"
        state_dim = ACTION_DIM
        state_feat = input_features.get(state_key)
        if state_feat is not None and hasattr(state_feat, "shape"):
            state_dim = state_feat.shape[0]

        # -- images --
        image_prefix = "observation.images."
        camera_keys: list[str] = []
        image_shapes: Dict[str, tuple] = {}

        for key, feat in input_features.items():
            if key.startswith(image_prefix):
                camera_name = key[len(image_prefix):]
                camera_keys.append(camera_name)
                if hasattr(feat, "shape"):
                    image_shapes[camera_name] = feat.shape

        # -- action_dim --
        action_dim = ACTION_DIM
        output_features: Dict[str, Any] = {}
        if policy_cfg is not None:
            output_features = getattr(policy_cfg, "output_features", {}) or {}
        action_feat = output_features.get("action")
        if action_feat is not None and hasattr(action_feat, "shape"):
            action_dim = action_feat.shape[0]

        return {
            "state_dim": state_dim,
            "state_key": state_key,
            "camera_keys": camera_keys,
            "image_prefix": image_prefix,
            "image_shapes": image_shapes,
            "action_dim": action_dim,
            "chunk_size": chunk_size,
        }

    def _resolve_device(self) -> torch.device:
        """Resolve inference device from the loaded policy's parameters.

        Falls back to ``DeployConfig`` device when the policy has no
        parameters (e.g. a mock/stub).
        """
        try:
            return next(self._policy.parameters()).device
        except (StopIteration, AttributeError):
            return torch.device(self._config.runtime.device)

    # -- contract validation ----------------------------------------------

    def _validate_contract(self) -> None:
        """Validate that the four dependencies form a consistent contract.

        Checks:

        1. Policy exposes ``predict_action_chunk`` (callable).
        2. State normalizer ``vector_dim`` matches policy ``state_dim``.
        3. Action normalizer ``vector_dim`` matches policy ``action_dim``.

        Raises:
            AttributeError: Policy missing ``predict_action_chunk``.
            ValueError:    Dimension mismatch between normalizers and
                           policy metadata.
        """
        # 1. predict_action_chunk must be callable
        if not callable(getattr(self._policy, "predict_action_chunk", None)):
            raise AttributeError(
                "Loaded policy does not expose a callable "
                "'predict_action_chunk'. L2-03 requires "
                "`policy.predict_action_chunk(batch)` for chunk inference."
            )

        # 2. state normalizer dimension
        state_dim = self._input_spec["state_dim"]
        if self._state_normalizer.vector_dim != state_dim:
            raise ValueError(
                f"state_normalizer vector_dim "
                f"({self._state_normalizer.vector_dim}) does not match "
                f"policy state_dim ({state_dim})"
            )

        # 3. action normalizer dimension
        action_dim = self._input_spec["action_dim"]
        if self._action_normalizer.vector_dim != action_dim:
            raise ValueError(
                f"action_normalizer vector_dim "
                f"({self._action_normalizer.vector_dim}) does not match "
                f"policy action_dim ({action_dim})"
            )

    # -- public entry point -----------------------------------------------

    def predict_action_chunk(
        self, observation: ObservationSnapshot
    ) -> ActionChunk:
        """Convert an ObservationSnapshot into an ActionChunk synchronously.

        Chains three primary stages:

        1. ``prepare_observation_batch``  -- snapshot -> device batch
           (deploy_022)
        2. ``run_act_inference``           -- batch -> raw tensor
           (this module)
        3. ``postprocess_action_chunk``    -- raw tensor -> ActionChunk
           (deploy_023)

        Any stage failure propagates immediately; no partial ActionChunk is
        ever returned.

        Args:
            observation: Validated ``ObservationSnapshot`` from L2-02.

        Returns:
            ``ActionChunk`` carrying only the physical action array.

        Raises:
            Propagates exceptions from any failing stage.
        """
        # Stage 1: prepare observation batch
        batch = prepare_observation_batch(
            observation,
            self._state_normalizer,
            self._input_spec,
            self._device,
        )

        # Stage 2: ACT forward inference
        raw_chunk = run_act_inference(self._policy, batch)

        # Stage 3: post-process to ActionChunk
        return postprocess_action_chunk(
            raw_chunk,
            self._action_normalizer,
            self._input_spec["chunk_size"],
        )
