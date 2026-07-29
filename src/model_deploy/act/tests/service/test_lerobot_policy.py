"""Tests for the lerobot ACT deployment adapter (service/lerobot_policy.py).

Covers the pure reorder/expand helpers and the LerobotActPolicyWrapper
end-to-end math using a fake policy — no lerobot import required.
"""

from __future__ import annotations

import numpy as np
import pytest
import torch

from model_deploy.act.service.lerobot_policy import (
    DEPLOY_ACTION_DIM,
    DEPLOY_STATE_DIM,
    MODEL_STATE_DIM,
    NORMALIZATION_EPS,
    TRAIN_TO_DEPLOY_ACTION_INDEX,
    LerobotActPolicyWrapper,
    expand_state_to_model_dim,
    make_lerobot_policy_loader,
    reorder_train_action_to_deploy,
)

STATE_KEY = "/act/observation/arm_state"
IMAGE_PREFIX = "/act/observation/image/"
CAMERAS = ("left", "right")
MODEL_HW = (480, 640)


# ---------------------------------------------------------------------------
# reorder / expand helpers
# ---------------------------------------------------------------------------


def test_reorder_moves_grippers_to_deploy_slots():
    train = torch.arange(16, dtype=torch.float32).unsqueeze(0)
    deploy = reorder_train_action_to_deploy(train)
    # deploy order: [L_tcp7, R_tcp7, L_grip, R_grip]
    assert deploy[0, :7].tolist() == list(range(0, 7))
    assert deploy[0, 7:14].tolist() == list(range(8, 15))
    assert deploy[0, 14].item() == 7.0   # L_grip: train slot 7 -> deploy slot 14
    assert deploy[0, 15].item() == 15.0  # R_grip stays at slot 15


def test_reorder_index_is_a_permutation():
    assert sorted(TRAIN_TO_DEPLOY_ACTION_INDEX) == list(range(16))


def test_reorder_rejects_wrong_last_dim():
    with pytest.raises(ValueError):
        reorder_train_action_to_deploy(torch.zeros(1, 15))


def test_expand_state_appends_tactile_fill():
    state = torch.ones(2, DEPLOY_STATE_DIM)
    fill = torch.full((16,), 5.0)
    out = expand_state_to_model_dim(state, fill)
    assert out.shape == (2, MODEL_STATE_DIM)
    assert torch.equal(out[:, :16], state)
    assert (out[:, 16:] == 5.0).all()


def test_expand_state_rejects_wrong_shape():
    with pytest.raises(ValueError):
        expand_state_to_model_dim(torch.zeros(2, 32), torch.zeros(16))


# ---------------------------------------------------------------------------
# LerobotActPolicyWrapper (fake policy, deterministic statistics)
# ---------------------------------------------------------------------------


class _FakePolicy(torch.nn.Module):
    """Records the received batch and returns a fixed normalized chunk."""

    def __init__(self, chunk: torch.Tensor) -> None:
        super().__init__()
        self.dummy = torch.nn.Parameter(torch.zeros(1))
        self.chunk = chunk
        self.seen_batch = None

    def predict_action_chunk(self, batch):
        self.seen_batch = batch
        return self.chunk


def _stats():
    stats = {
        "observation.state.mean": torch.arange(
            MODEL_STATE_DIM, dtype=torch.float32),
        "observation.state.std": torch.full((MODEL_STATE_DIM,), 2.0),
        "action.mean": torch.full((DEPLOY_ACTION_DIM,), 1.0),
        "action.std": torch.full((DEPLOY_ACTION_DIM,), 3.0),
    }
    for cam in CAMERAS:
        stats[f"observation.images.{cam}.mean"] = torch.full((3, 1, 1), 0.5)
        stats[f"observation.images.{cam}.std"] = torch.full((3, 1, 1), 0.25)
    return stats


def _wrapper(chunk):
    policy = _FakePolicy(chunk)
    wrapper = LerobotActPolicyWrapper(
        policy,
        _stats(),
        state_key=STATE_KEY,
        image_prefix=IMAGE_PREFIX,
        camera_keys=CAMERAS,
        image_hw=MODEL_HW,
    )
    return wrapper, policy


def _deploy_batch(image_size: int = 64):
    batch = {STATE_KEY: torch.zeros(1, DEPLOY_STATE_DIM)}
    for cam in CAMERAS:
        batch[f"{IMAGE_PREFIX}{cam}"] = torch.rand(1, 3, image_size, image_size)
    return batch


def test_wrapper_translates_keys_and_expands_state():
    chunk = torch.zeros(1, 5, DEPLOY_ACTION_DIM)
    wrapper, policy = _wrapper(chunk)
    wrapper.predict_action_chunk(_deploy_batch())
    seen = policy.seen_batch
    assert set(seen.keys()) == {
        "observation.state",
        "observation.images.left",
        "observation.images.right",
    }
    assert seen["observation.state"].shape == (1, MODEL_STATE_DIM)


def test_wrapper_state_normalization_and_tactile_zero():
    chunk = torch.zeros(1, 5, DEPLOY_ACTION_DIM)
    wrapper, policy = _wrapper(chunk)
    wrapper.predict_action_chunk(_deploy_batch())
    state_norm = policy.seen_batch["observation.state"][0]
    stats = _stats()
    mean = stats["observation.state.mean"]
    std = stats["observation.state.std"]
    # first 16 dims: raw zeros -> (0 - mean) / (std + eps)
    expected = (0.0 - mean[:16]) / (std[:16] + NORMALIZATION_EPS)
    assert torch.allclose(state_norm[:16], expected, atol=1e-6)
    # tactile block filled with the training mean -> exactly 0 after norm
    assert torch.allclose(state_norm[16:], torch.zeros(16), atol=1e-6)


def test_wrapper_resizes_and_normalizes_images():
    chunk = torch.zeros(1, 5, DEPLOY_ACTION_DIM)
    wrapper, policy = _wrapper(chunk)
    batch = {STATE_KEY: torch.zeros(1, DEPLOY_STATE_DIM)}
    for cam in CAMERAS:
        batch[f"{IMAGE_PREFIX}{cam}"] = torch.full((1, 3, 64, 64), 2.0)
    wrapper.predict_action_chunk(batch)
    for cam in CAMERAS:
        img = policy.seen_batch[f"observation.images.{cam}"]
        # resized to the model (H, W)
        assert img.shape == (1, 3) + MODEL_HW
        # constant image stays constant under bilinear resize; then MEAN_STD:
        # (2.0 - 0.5) / (0.25 + eps) = 6.0
        assert torch.allclose(
            img, torch.full_like(img, (2.0 - 0.5) / (0.25 + NORMALIZATION_EPS)),
            atol=1e-4)


def test_wrapper_unnormalizes_and_reorders_actions():
    # normalized model output: train slot 7 (L_grip) = 2.0, slot 15 = -1.0
    normalized = torch.zeros(1, 4, DEPLOY_ACTION_DIM)
    normalized[..., 7] = 2.0
    normalized[..., 15] = -1.0
    wrapper, _ = _wrapper(normalized)
    out = wrapper.predict_action_chunk(_deploy_batch())
    assert out.shape == (1, 4, DEPLOY_ACTION_DIM)
    assert out.dtype == torch.float32
    # unnormalize: x * std + mean = x * 3 + 1; then train->deploy reorder
    np.testing.assert_allclose(out[0, 0, 14].item(), 7.0, rtol=1e-5)   # 2*3+1
    np.testing.assert_allclose(out[0, 0, 15].item(), -2.0, rtol=1e-5)  # -1*3+1
    # all other slots: 0*3+1 = 1
    assert torch.allclose(
        out[0, 0, :14], torch.full((14,), 1.0), atol=1e-5)


def test_wrapper_rejects_bad_stats_shape():
    stats = _stats()
    stats["observation.state.mean"] = torch.zeros(16)  # must be 32
    with pytest.raises(Exception):
        LerobotActPolicyWrapper(
            _FakePolicy(torch.zeros(1, 1, DEPLOY_ACTION_DIM)),
            stats,
            state_key=STATE_KEY,
            image_prefix=IMAGE_PREFIX,
            camera_keys=CAMERAS,
            image_hw=MODEL_HW,
        )


# ---------------------------------------------------------------------------
# loader factory
# ---------------------------------------------------------------------------


def test_make_loader_is_side_effect_free():
    from model_deploy.act.config.schema import DeployConfig

    raw = {
        "bundle": {"bundle_dir": "/nonexistent/bundle"},
        "runtime": {"state_dim": 16, "action_dim": 16, "chunk_size": 100},
        "image": {"image_size": 640},
    }
    config = DeployConfig.from_mapping(
        raw, base_dir="/tmp", command_output_enabled=False)
    loader = make_lerobot_policy_loader(config)
    assert callable(loader)
