"""Main training loop for Pi0.5 LoRA fine-tuning."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import torch
from accelerate import Accelerator
from lerobot.policies.pi05.processor_pi05 import make_pi05_pre_post_processors

from pi05.common.config.schema import ExperimentConfig
from pi05.common.model.builder import build_pi05_with_lora, get_pi05_policy_config
from pi05.common.runtime.bundle import export_deploy_bundle
from pi05.train.engine.batches import to_lerobot_pi05_batch
from pi05.train.engine.builders import (
    build_lr_scheduler,
    build_optimizer,
    build_train_dataloader,
    count_training_steps,
)
from pi05.train.engine.checkpoints import (
    export_final_adapter,
    maybe_resume,
    save_epoch_adapter_checkpoint,
)
from pi05.train.utils.logging import configure_logging, log_run_summary
from pi05.train.utils.seed import set_training_seed
from pi05.train.utils.tensorboard import launch_tensorboard


LOGGER = logging.getLogger(__name__)


@dataclass
class _AverageMeter:
    total: float = 0.0
    count: int = 0

    def update(self, value: float) -> None:
        self.total += value
        self.count += 1

    @property
    def avg(self) -> float:
        return 0.0 if self.count == 0 else self.total / self.count


class _LogWindow:
    def __init__(self) -> None:
        self._meters: dict[str, _AverageMeter] = {}

    def update(self, **metrics: float | None) -> None:
        for key, value in metrics.items():
            if value is None:
                continue
            meter = self._meters.setdefault(key, _AverageMeter())
            meter.update(float(value))

    def as_dict(self) -> dict[str, float]:
        return {key: meter.avg for key, meter in self._meters.items() if meter.count > 0}

    @property
    def count(self) -> int:
        if not self._meters:
            return 0
        first_meter = next(iter(self._meters.values()))
        return first_meter.count

    def reset(self) -> None:
        self._meters.clear()


class Pi05LoraTrainer:
    """Coordinates config, Accelerate, model/data builders, and the train loop."""

    def __init__(self, config: ExperimentConfig) -> None:
        self.config = config

    def run(self) -> None:
        configure_logging()
        set_training_seed(self.config.training.seed)

        dataloader = build_train_dataloader(self.config.data, self.config.training)
        num_training_steps = count_training_steps(dataloader, self.config.training)

        accelerator = self._build_accelerator()
        self._init_trackers(accelerator)
        if accelerator.is_main_process:
            log_run_summary(LOGGER, self.config.run_summary())

        model = build_pi05_with_lora(
            config=self.config,
            pretrained_path=self.config.model.pretrained_path,
        )
        policy_config = get_pi05_policy_config(model)
        policy_config.device = str(accelerator.device)
        preprocessor, _ = make_pi05_pre_post_processors(policy_config, dataset_stats=None)

        optimizer = build_optimizer(model, self.config.training)
        lr_scheduler = build_lr_scheduler(
            optimizer=optimizer,
            train_cfg=self.config.training,
            num_training_steps=num_training_steps,
        )

        model, optimizer, dataloader, lr_scheduler = accelerator.prepare(
            model,
            optimizer,
            dataloader,
            lr_scheduler,
        )
        maybe_resume(accelerator, self.config.training.resume_from_checkpoint)
        self._train_loop(
            accelerator=accelerator,
            model=model,
            dataloader=dataloader,
            preprocessor=preprocessor,
            optimizer=optimizer,
            lr_scheduler=lr_scheduler,
        )

    def _build_accelerator(self) -> Accelerator:
        train_cfg = self.config.training
        log_cfg = self.config.logging
        mixed_precision = train_cfg.mixed_precision
        if mixed_precision is None:
            mixed_precision = "bf16" if torch.cuda.is_available() else "no"

        return Accelerator(
            gradient_accumulation_steps=train_cfg.gradient_accumulation_steps,
            mixed_precision=mixed_precision,
            log_with="tensorboard" if log_cfg.use_tensorboard else None,
            project_dir=str(log_cfg.resolved_tensorboard_dir) if log_cfg.use_tensorboard else None,
        )

    def _init_trackers(self, accelerator: Accelerator) -> None:
        log_cfg = self.config.logging
        if not log_cfg.use_tensorboard:
            return
        accelerator.init_trackers(
            project_name=log_cfg.project_name,
            config=self.config.to_tracker_config(),
            init_kwargs={"tensorboard": {"flush_secs": 10}},
        )
        if accelerator.is_main_process and log_cfg.tensorboard_auto_launch:
            launch_tensorboard(
                logdir=log_cfg.resolved_tensorboard_dir,
                host=log_cfg.tensorboard_host,
                port=log_cfg.tensorboard_port,
            )

    def _train_loop(
        self,
        *,
        accelerator: Accelerator,
        model: torch.nn.Module,
        dataloader: Any,
        preprocessor: Any,
        optimizer: torch.optim.Optimizer,
        lr_scheduler: Any,
    ) -> None:
        train_cfg = self.config.training
        log_cfg = self.config.logging
        run_output_dir = log_cfg.run_output_dir

        model.train()
        total_steps = 0
        state_dim: int | None = None
        log_window = _LogWindow()
        try:
            for epoch in range(train_cfg.epochs):
                epoch_steps = 0
                for batch in dataloader:
                    if state_dim is None:
                        state_dim = int(batch["state"].shape[-1])
                        accelerator.print(f"[train] state_dim={state_dim}")

                    grad_norm_value: float | None = None
                    with accelerator.accumulate(model):
                        processed_batch = preprocessor(to_lerobot_pi05_batch(batch))
                        loss, loss_dict = model(processed_batch)

                        accelerator.backward(loss)
                        if accelerator.sync_gradients and train_cfg.grad_clip_norm is not None:
                            grad_norm = accelerator.clip_grad_norm_(model.parameters(), train_cfg.grad_clip_norm)
                            grad_norm_value = self._to_float(grad_norm)
                        optimizer.step()
                        lr_scheduler.step()
                        optimizer.zero_grad(set_to_none=True)

                    if accelerator.sync_gradients:
                        total_steps += 1
                        epoch_steps += 1
                        log_window.update(
                            train_loss=self._resolve_loss_value(loss, loss_dict),
                            lr=self._get_lr(optimizer, lr_scheduler),
                            grad_norm=grad_norm_value,
                        )

                        if total_steps % log_cfg.log_freq == 0:
                            self._flush_log_window(
                                accelerator=accelerator,
                                epoch=epoch,
                                total_steps=total_steps,
                                log_window=log_window,
                            )

                    if (
                        train_cfg.max_steps_per_epoch is not None
                        and epoch_steps >= train_cfg.max_steps_per_epoch
                    ):
                        accelerator.print(
                            f"[train] reached max_steps_per_epoch={train_cfg.max_steps_per_epoch}; "
                            f"ending epoch {epoch}"
                        )
                        break

                if (epoch + 1) % train_cfg.checkpoint_freq_epochs == 0:
                    save_epoch_adapter_checkpoint(accelerator, model, run_output_dir, epoch + 1)

            self._flush_log_window(
                accelerator=accelerator,
                epoch=train_cfg.epochs - 1,
                total_steps=total_steps,
                log_window=log_window,
            )

            if accelerator.is_main_process:
                final_adapter_dir = export_final_adapter(accelerator, model, run_output_dir)
                self._maybe_export_deploy_bundle(
                    accelerator=accelerator,
                    final_adapter_dir=final_adapter_dir,
                )
        finally:
            if log_cfg.use_tensorboard:
                accelerator.end_training()

    def _maybe_export_deploy_bundle(
        self,
        *,
        accelerator: Accelerator,
        final_adapter_dir,
    ) -> None:
        try:
            bundle_dir = export_deploy_bundle(
                self.config,
                adapter_dir=final_adapter_dir,
                output_dir=self.config.logging.run_export_dir,
                overwrite=True,
            )
        except Exception as exc:  # pragma: no cover
            accelerator.print(f"[train] warning: failed to export deploy bundle: {exc}")
            return
        accelerator.print(f"[train] exported deploy bundle to: {bundle_dir}")

    def _flush_log_window(
        self,
        *,
        accelerator: Accelerator,
        epoch: int,
        total_steps: int,
        log_window: _LogWindow,
    ) -> None:
        if log_window.count == 0 or total_steps == 0:
            return
        payload = log_window.as_dict()
        if self.config.logging.use_tensorboard:
            accelerator.log(payload, step=total_steps)
        if accelerator.is_main_process:
            self._log_train_step(
                accelerator=accelerator,
                epoch=epoch,
                total_steps=total_steps,
                metrics=payload,
                window_size=log_window.count,
            )
        log_window.reset()

    @staticmethod
    def _get_lr(optimizer: torch.optim.Optimizer, lr_scheduler: Any) -> float:
        if lr_scheduler is not None and hasattr(lr_scheduler, "get_last_lr"):
            last_lr = lr_scheduler.get_last_lr()
            if last_lr:
                return float(last_lr[0])
        return float(optimizer.param_groups[0]["lr"])

    @staticmethod
    def _resolve_loss_value(loss: torch.Tensor, loss_dict: dict[str, Any]) -> float:
        return Pi05LoraTrainer._to_float(loss_dict.get("loss", loss))

    @staticmethod
    def _to_float(value: Any) -> float:
        if isinstance(value, torch.Tensor):
            return float(value.detach().item())
        return float(value)

    @staticmethod
    def _log_train_step(
        *,
        accelerator: Accelerator,
        epoch: int,
        total_steps: int,
        metrics: dict[str, float],
        window_size: int,
    ) -> None:
        parts = [
            f"epoch={epoch:03d}",
            f"step={total_steps:06d}",
            f"avg_over={window_size}",
        ]
        if "train_loss" in metrics:
            parts.append(f"train_loss={metrics['train_loss']:.6f}")
        if "grad_norm" in metrics:
            parts.append(f"grad_norm={metrics['grad_norm']:.4f}")
        if "lr" in metrics:
            parts.append(f"lr={metrics['lr']:.2e}")
        accelerator.print(" ".join(parts))


def train_from_config(config: ExperimentConfig) -> None:
    Pi05LoraTrainer(config).run()
