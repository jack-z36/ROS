"""Builders for datasets, dataloaders, optimizers, and schedulers."""

from __future__ import annotations

import math

import torch
from torch.optim import AdamW, Optimizer
from torch.utils.data import DataLoader
from transformers import get_cosine_schedule_with_warmup

from pi05.common.config.schema import DataConfig, TrainingConfig
from pi05.common.data.normalization import build_state_action_normalizers
from pi05.train.data.dataset import Pi05LeRobotDataset


def build_train_dataloader(data_cfg: DataConfig, train_cfg: TrainingConfig) -> DataLoader:
    dataset_path = data_cfg.resolved_dataset_path
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset path does not exist: {dataset_path}")

    bootstrap_dataset = Pi05LeRobotDataset(
        dataset_path=dataset_path,
        chunk_size=data_cfg.chunk_size,
        use_color_jitter=data_cfg.use_color_jitter,
        image_size=data_cfg.image_size,
        state_dim=data_cfg.state_dim,
        action_dim=data_cfg.action_dim,
        cameras=data_cfg.cameras,
    )
    state_normalizer, action_normalizer = build_state_action_normalizers(bootstrap_dataset.dataset)

    dataset = Pi05LeRobotDataset(
        dataset_path=dataset_path,
        chunk_size=data_cfg.chunk_size,
        use_color_jitter=data_cfg.use_color_jitter,
        image_size=data_cfg.image_size,
        state_dim=data_cfg.state_dim,
        action_dim=data_cfg.action_dim,
        cameras=data_cfg.cameras,
        state_normalizer=state_normalizer,
        action_normalizer=action_normalizer,
    )
    return DataLoader(
        dataset,
        batch_size=train_cfg.batch_size,
        shuffle=True,
        num_workers=data_cfg.num_workers,
        pin_memory=torch.cuda.is_available(),
        drop_last=False,
    )


def count_training_steps(dataloader: DataLoader, train_cfg: TrainingConfig) -> int:
    update_steps_per_epoch = math.ceil(len(dataloader) / train_cfg.gradient_accumulation_steps)
    if train_cfg.max_steps_per_epoch is not None:
        update_steps_per_epoch = min(update_steps_per_epoch, train_cfg.max_steps_per_epoch)
    return update_steps_per_epoch * train_cfg.epochs


def build_optimizer(model: torch.nn.Module, train_cfg: TrainingConfig) -> Optimizer:
    return AdamW(
        (param for param in model.parameters() if param.requires_grad),
        lr=train_cfg.lr,
    )


def build_lr_scheduler(optimizer: Optimizer, train_cfg: TrainingConfig, num_training_steps: int):
    return get_cosine_schedule_with_warmup(
        optimizer=optimizer,
        num_warmup_steps=train_cfg.warmup_steps,
        num_training_steps=num_training_steps,
    )
