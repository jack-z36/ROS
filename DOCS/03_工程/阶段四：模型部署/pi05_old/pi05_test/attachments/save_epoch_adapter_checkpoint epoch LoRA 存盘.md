---
tags:
  - 附件
---

# save_epoch_adapter_checkpoint (epoch LoRA 存盘)

> [!abstract]
> 每个 `checkpoint_freq_epochs` 触发一次：把 LoRA adapter（不含 base 权重）保存到 `run_output_dir/checkpoint_epoch_{N}/adapter/`，main_process 写、其它进程 wait。

## 基本信息

| 属性 | 值 |
| --- | --- |
| 函数名 | `save_epoch_adapter_checkpoint` |
| 所在文件 | `pi05_test/pi05/train/src/pi05/train/engine/checkpoints.py:21-33` |
| 调用位置 | `trainer.py:221`（每个 epoch 末尾） |
| 现实含义 | "训练到一半想看看效果如何" — 不需要存完整 base，只存 LoRA |

## 行为

```python
def save_epoch_adapter_checkpoint(
    accelerator: Accelerator,
    model: torch.nn.Module,
    run_output_dir: Path,
    epoch: int,
) -> Path:
    adapter_dir = run_output_dir / f"checkpoint_epoch_{epoch}" / "adapter"
    if accelerator.is_main_process:
        _save_adapter(accelerator, model, adapter_dir)
        accelerator.print(f"Saved epoch LoRA adapter to: {adapter_dir}")
    accelerator.wait_for_everyone()
    return adapter_dir
```

## 内部 `_save_adapter`

```python
def _save_adapter(accelerator, model, output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)
    unwrapped_model = accelerator.unwrap_model(model)  # 拿掉 DDP 包装
    unwrapped_model.save_pretrained(output_dir)
```

`unwrapped_model.save_pretrained` 是 PEFT 接口，只存 LoRA adapter 的 `adapter_model.safetensors` + `adapter_config.json`。

## 关键约束

- **只存 adapter，不存 optim/sched**：与 `maybe_resume` 行为不同
- **epoch 编号是 1-indexed**：传 `(epoch + 1)`
- **多卡时 main_process 写**：其他进程等
- 与 [[_train_loop 核心训练循环]]、[[maybe_resume 恢复训练]]、[[export_deploy_bundle 部署 bundle 导出]] 配套
