"""Production lerobot ACT policy loader + deployment adapter (L2-03).

Bridges the deployment 16D physical contract to the trained lerobot ACT
model contract.  The trained model (UMI_ACT, lerobot v0.5.x export) differs
from the deployment pipeline in four ways, all of which are absorbed HERE so
the rest of the pipeline keeps its frozen 16D physical contract:

1. Batch keys      deploy uses ROS-topic-style keys
                   (``/act/observation/arm_state``,
                   ``/act/observation/image/left``) while the model expects
                   lerobot keys (``observation.state``,
                   ``observation.images.left``).
2. State dim       deploy state is 16D physical
                   ``[L_tcp7, R_tcp7, L_grip, R_grip]``; the model expects
                   32D — same first 16 plus 16 tactile statistics.  The robot
                   has no tactile sensors, so the tactile block is filled
                   with the training MEAN (=> exactly 0 after MEAN_STD
                   normalization).
3. Normalization   the deployed bundle normalizers are identity passthrough;
                   the real MEAN_STD normalize / unnormalize (training
                   statistics from the exported preprocessor safetensors,
                   ``(x - mean) / (std + eps)`` / ``x * std + mean``,
                   eps=1e-8) happens inside this wrapper.
4. Action order    the model outputs the TRAINING action order
                   ``[L_tcp7, L_grip, R_tcp7, R_grip]`` while deploy expects
                   ``[L_tcp7, R_tcp7, L_grip, R_grip]`` — the wrapper
                   reorders every chunk (verified against the exported
                   normalization statistics: gripper 0..1 range sits at
                   indices 7 and 15 in the training order).

Additionally the wrapper resizes incoming square images (deploy image_size)
to the model's expected (H, W) (e.g. 480x640) with bilinear interpolation
and applies the per-channel image MEAN_STD statistics.

Heavy imports (lerobot, safetensors) are deferred into the loader function
so importing this module stays cheap and works in test environments without
the ML stack.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Dict, Mapping, Tuple

import torch

if TYPE_CHECKING:
    from model_deploy.act.config.schema import DeployConfig

# MEAN_STD epsilon used by the lerobot exported preprocessor.
NORMALIZATION_EPS: float = 1e-8

# Dimensional contract: deploy pipeline is 16D physical, the trained model
# consumes/produces 32D state and 16D action (training order).
MODEL_STATE_DIM: int = 32
DEPLOY_STATE_DIM: int = 16
DEPLOY_ACTION_DIM: int = 16

# Training action order [L_tcp7, L_grip, R_tcp7, R_grip] -> deploy order
# [L_tcp7, R_tcp7, L_grip, R_grip].  Verified against the exported
# normalization statistics (gripper 0..1 range at train indices 7 and 15).
TRAIN_TO_DEPLOY_ACTION_INDEX: Tuple[int, ...] = (
    0, 1, 2, 3, 4, 5, 6, 8, 9, 10, 11, 12, 13, 14, 7, 15,
)

# The exported preprocessor safetensors carrying the MEAN_STD statistics
# (the step number in the filename varies per export).
STATS_FILE_GLOB: str = "policy_preprocessor_step_*_normalizer_processor.safetensors"


class LerobotBundleError(RuntimeError):
    """Raised when the lerobot bundle contents violate the expected contract."""


def reorder_train_action_to_deploy(actions: torch.Tensor) -> torch.Tensor:
    """Reorder the last dim from the TRAINING action order to the deploy order.

    Args:
        actions: Tensor ``(..., 16)`` in training order
            ``[L_tcp7, L_grip, R_tcp7, R_grip]``.

    Returns:
        Tensor ``(..., 16)`` in deploy order ``[L_tcp7, R_tcp7, L_grip, R_grip]``.
    """
    if actions.shape[-1] != DEPLOY_ACTION_DIM:
        raise ValueError(
            f"actions last dim must be {DEPLOY_ACTION_DIM}, got {actions.shape}")
    index = torch.as_tensor(
        TRAIN_TO_DEPLOY_ACTION_INDEX, dtype=torch.long, device=actions.device)
    return actions.index_select(-1, index)


def expand_state_to_model_dim(
    state16: torch.Tensor,
    tactile_fill: torch.Tensor,
) -> torch.Tensor:
    """Expand a deploy 16D state batch to the 32D model state.

    The first 16 dims are identical in order between deploy and training
    (verified against the exported statistics).  The tactile block is filled
    with *tactile_fill* (the training mean -> normalizes to exactly 0).

    Args:
        state16:      ``(B, 16)`` physical state batch.
        tactile_fill: ``(16,)`` fill values for the tactile block.

    Returns:
        ``(B, 32)`` model state batch.
    """
    if state16.ndim != 2 or state16.shape[1] != DEPLOY_STATE_DIM:
        raise ValueError(
            f"state16 must have shape (B, {DEPLOY_STATE_DIM}), got "
            f"{tuple(state16.shape)}")
    fill = tactile_fill.to(device=state16.device, dtype=state16.dtype)
    fill = fill.unsqueeze(0).expand(state16.shape[0], -1)
    return torch.cat([state16, fill], dim=1)


class LerobotActPolicyWrapper:
    """Adapts the raw lerobot ACTPolicy to the deployment L2-03 contract.

    Exposes exactly the two attributes the pipeline relies on:
    ``predict_action_chunk(batch) -> (1, chunk_size, 16)`` physical-deploy-order
    tensor, and ``parameters()`` for device resolution.
    """

    def __init__(
        self,
        policy: Any,
        stats: Mapping[str, torch.Tensor],
        *,
        state_key: str,
        image_prefix: str,
        camera_keys: Tuple[str, ...],
        image_hw: Tuple[int, int],
    ) -> None:
        """Build the adapter.

        Args:
            policy:       Loaded ``lerobot`` ACTPolicy (eval mode, on device).
            stats:        MEAN_STD statistics tensors keyed lerobot-style
                          (``observation.state.mean`` (32,), ``action.std``
                          (16,), ``observation.images.<cam>.mean`` (3,1,1), …).
            state_key:    Deploy batch key holding the ``(1, 16)`` state.
            image_prefix: Deploy batch key prefix for camera images.
            camera_keys:  Logical camera names (``("left", "right")``).
            image_hw:     Model-expected image (H, W), e.g. ``(480, 640)``.
        """
        self._policy = policy
        self._state_key = state_key
        self._image_prefix = image_prefix
        self._camera_keys = tuple(camera_keys)
        self._image_hw = (int(image_hw[0]), int(image_hw[1]))

        device = next(policy.parameters()).device
        as_dev = lambda t: t.to(device=device, dtype=torch.float32)  # noqa: E731

        state_mean = as_dev(stats["observation.state.mean"])
        state_std = as_dev(stats["observation.state.std"])
        if state_mean.shape != (MODEL_STATE_DIM,):
            raise LerobotBundleError(
                f"observation.state.mean must be ({MODEL_STATE_DIM},), got "
                f"{tuple(state_mean.shape)}")
        self._state_mean = state_mean
        self._state_std = state_std
        self._tactile_fill = state_mean[DEPLOY_STATE_DIM:].clone()

        action_mean = as_dev(stats["action.mean"])
        action_std = as_dev(stats["action.std"])
        if action_mean.shape != (DEPLOY_ACTION_DIM,):
            raise LerobotBundleError(
                f"action.mean must be ({DEPLOY_ACTION_DIM},), got "
                f"{tuple(action_mean.shape)}")
        self._action_mean = action_mean
        self._action_std = action_std

        self._image_stats = {}
        for cam in self._camera_keys:
            mean = as_dev(stats[f"observation.images.{cam}.mean"])
            std = as_dev(stats[f"observation.images.{cam}.std"])
            self._image_stats[cam] = (mean, std)

    def parameters(self):
        return self._policy.parameters()

    def predict_action_chunk(self, batch: Dict[str, torch.Tensor]) -> torch.Tensor:
        """Deploy batch -> physical action chunk in deploy order.

        Steps: key translation, 16->32 state expansion, MEAN_STD normalize,
        image resize + MEAN_STD, model forward, action unnormalize,
        train->deploy action reorder.

        Args:
            batch: ``{state_key: (1, 16) physical, <image_prefix><cam>:
                   (1, 3, S, S) float32 [0, 1]}`` on the policy device.

        Returns:
            ``(1, chunk_size, 16)`` float32 physical actions, deploy order.
        """
        state16 = batch[self._state_key]
        state32 = expand_state_to_model_dim(state16, self._tactile_fill)
        state_norm = (state32 - self._state_mean) / (
            self._state_std + NORMALIZATION_EPS)

        model_batch = {"observation.state": state_norm}
        for cam in self._camera_keys:
            img = batch[f"{self._image_prefix}{cam}"]
            if tuple(img.shape[-2:]) != self._image_hw:
                img = torch.nn.functional.interpolate(
                    img, size=self._image_hw, mode="bilinear",
                    align_corners=False)
            mean, std = self._image_stats[cam]
            model_batch[f"observation.images.{cam}"] = (img - mean) / (
                std + NORMALIZATION_EPS)

        normalized_actions = self._policy.predict_action_chunk(model_batch)

        physical = normalized_actions * self._action_std + self._action_mean
        return reorder_train_action_to_deploy(physical).to(torch.float32)


def _load_normalization_stats(pretrained_dir: Path) -> Dict[str, torch.Tensor]:
    """Load the exported MEAN_STD statistics safetensors from *pretrained_dir*."""
    from safetensors import safe_open

    candidates = sorted(pretrained_dir.glob(STATS_FILE_GLOB))
    if not candidates:
        raise LerobotBundleError(
            f"No normalization statistics file matching {STATS_FILE_GLOB!r} in "
            f"{pretrained_dir}")
    stats = {}
    with safe_open(str(candidates[0]), framework="pt") as fh:
        for key in fh.keys():
            stats[key] = fh.get_tensor(key)
    return stats


def make_lerobot_policy_loader(config: "DeployConfig") -> Callable[[Path], Any]:
    """Build the production ``load_policy`` callback for ``load_act_runtime_resources``.

    The returned closure performs all heavy work (lerobot import, weight load,
    statistics load, contract checks) only when invoked, so building the
    factory itself is side-effect free.

    Args:
        config: Validated ``DeployConfig`` (provides batch key names, camera
            keys, and the runtime device / chunk size to cross-check).

    Returns:
        ``loader(bundle_dir) -> LerobotActPolicyWrapper``.
    """
    state_key = config.topics.observation.arm_state
    image_prefix = f"{config.topics.namespace}/observation/image/"
    camera_keys = tuple(sorted(config.topics.observation.image_topics.keys()))
    device = config.runtime.device
    expected_chunk_size = config.runtime.chunk_size

    def _load(bundle_dir: Path) -> LerobotActPolicyWrapper:
        from lerobot.policies.act.modeling_act import ACTPolicy

        from model_deploy.act.repo.bundle_reader import resolve_checkpoint_path

        checkpoint = resolve_checkpoint_path(bundle_dir)
        pretrained_dir = checkpoint if checkpoint.is_dir() else checkpoint.parent

        policy = ACTPolicy.from_pretrained(str(pretrained_dir))
        policy.to(device)
        policy.eval()

        if int(policy.config.chunk_size) != int(expected_chunk_size):
            raise LerobotBundleError(
                f"Model chunk_size {policy.config.chunk_size} != config "
                f"runtime.chunk_size {expected_chunk_size}")
        image_features = dict(policy.config.image_features)
        expected_keys = {f"observation.images.{cam}" for cam in camera_keys}
        if set(image_features.keys()) != expected_keys:
            raise LerobotBundleError(
                f"Model image features {sorted(image_features)} != expected "
                f"{sorted(expected_keys)}")
        first_shape = next(iter(image_features.values())).shape
        image_hw = (int(first_shape[1]), int(first_shape[2]))

        stats = _load_normalization_stats(pretrained_dir)

        return LerobotActPolicyWrapper(
            policy,
            stats,
            state_key=state_key,
            image_prefix=image_prefix,
            camera_keys=camera_keys,
            image_hw=image_hw,
        )

    return _load
