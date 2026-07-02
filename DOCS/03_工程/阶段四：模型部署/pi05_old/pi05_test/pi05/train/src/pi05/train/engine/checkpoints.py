"""Checkpoint and final adapter export helpers."""

from __future__ import annotations

from pathlib import Path

import torch
from accelerate import Accelerator


def maybe_resume(accelerator: Accelerator, checkpoint_path: Path | None) -> None:
    if checkpoint_path is None:
        return
    checkpoint_path = checkpoint_path.expanduser().resolve()
    if not checkpoint_path.exists():
        raise FileNotFoundError(f"Resume checkpoint does not exist: {checkpoint_path}")
    accelerator.load_state(str(checkpoint_path))
    accelerator.print(f"Resumed training state from: {checkpoint_path}")


def save_epoch_adapter_checkpoint(
    accelerator: Accelerator,
    model: torch.nn.Module,
    run_output_dir: Path,
    epoch: int,
) -> Path:
    """Save an epoch-level LoRA adapter without optimizer/scheduler state."""
    adapter_dir = run_output_dir / f"checkpoint_epoch_{epoch}" / "adapter"
    if accelerator.is_main_process:
        _save_adapter(accelerator, model, adapter_dir)
        accelerator.print(f"Saved epoch LoRA adapter to: {adapter_dir}")
    accelerator.wait_for_everyone()
    return adapter_dir


def export_final_adapter(accelerator: Accelerator, model: torch.nn.Module, run_output_dir: Path) -> Path:
    run_output_dir.mkdir(parents=True, exist_ok=True)
    final_adapter_dir = run_output_dir / "final_adapter"
    if accelerator.is_main_process:
        _save_adapter(accelerator, model, final_adapter_dir)
        accelerator.print(f"Saved LoRA adapter to: {final_adapter_dir}")
    accelerator.wait_for_everyone()
    return final_adapter_dir


def _save_adapter(accelerator: Accelerator, model: torch.nn.Module, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    unwrapped_model = accelerator.unwrap_model(model)
    unwrapped_model.save_pretrained(output_dir)
