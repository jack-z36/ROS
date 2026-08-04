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
from model_deploy.act.repo.act_runtime_resources import PolicyInputSpec
from model_deploy.act.repo.normalization import ActionStateNormalizer
from model_deploy.act.service.action_chunk_postprocess import postprocess_action_chunk
from model_deploy.act.service.observation_batch import prepare_observation_batch
from model_deploy.act.types.action_chunk import ActionChunk
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
    the single canonical ``input_spec`` injected by L2-01 / L2-06.  Owns no
    scheduling state or runtime-ownership responsibility.

    The single public method ``predict_action_chunk`` is the only interface
    that L2-06 is allowed to call on L2-03.
    """

    def __init__(
        self,
        config: DeployConfig,
        state_normalizer: ActionStateNormalizer,
        action_normalizer: ActionStateNormalizer,
        policy: object,
        input_spec: PolicyInputSpec,
    ) -> None:
        """Create the inference service from four L2-01 injected dependencies
        plus the single canonical ``PolicyInputSpec`` (deploy_056).

        The ``input_spec`` is the SAME frozen object produced once by
        ``load_act_runtime_resources`` and consumed by L2-02 / L2-06.  The
        service stores it by identity (no copy, no re-derivation) and exposes
        it read-only via the ``input_spec`` property.  Missing or conflicting
        metadata is a startup failure in L2-01, so L2-03 never falls back to
        ``DeployConfig`` or ``ACTION_DIM`` defaults to plug the contract.

        Resolves the inference device from policy parameters and validates
        that the four dependencies form a consistent contract.

        Args:
            config:             Frozen ``DeployConfig`` from L2-01 (used only
                                for the inference device when the policy
                                exposes none).
            state_normalizer:   Normalizer instance (``normalize`` direction).
            action_normalizer:  Normalizer instance (``unnormalize`` direction).
            policy:             Loaded ACT policy exposing
                                ``predict_action_chunk``.
            input_spec:         Canonical frozen ``PolicyInputSpec`` injected by
                                L2-01 / L2-06; must be the identical object fed
                                to L2-02 and L2-06.

        Raises:
            AttributeError: Policy does not expose ``predict_action_chunk``.
            ValueError:    Dimension mismatch between normalizers and
                           ``input_spec``.
        """
        self._config = config
        self._state_normalizer = state_normalizer
        self._action_normalizer = action_normalizer
        self._policy = policy
        self._input_spec = input_spec

        # Resolve inference device from policy parameters
        self._device = self._resolve_device()

        # Validate contract consistency
        self._validate_contract()

    # -- public read-only seam --------------------------------------------

    @property
    def input_spec(self) -> PolicyInputSpec:
        """The canonical frozen ``PolicyInputSpec`` injected at construction.

        Returns the exact object passed to the constructor (identity), never a
        copy or a re-derived mapping.  L2-06 may assert
        ``service.input_spec is resources.policy_input_spec``.
        """
        return self._input_spec

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
        state_dim = self.input_spec.state_dim
        if self._state_normalizer.vector_dim != state_dim:
            raise ValueError(
                f"state_normalizer vector_dim "
                f"({self._state_normalizer.vector_dim}) does not match "
                f"policy state_dim ({state_dim})"
            )

        # 3. action normalizer dimension
        action_dim = self.input_spec.action_dim
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
            self.input_spec,
            self._device,
        )

        # Stage 2: ACT forward inference
        raw_chunk = run_act_inference(self._policy, batch)

        # Stage 3: post-process to ActionChunk
        return postprocess_action_chunk(
            raw_chunk,
            self._action_normalizer,
            self.input_spec.chunk_size,
        )
