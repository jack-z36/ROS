---
tags:
  - 附件
---

# maybe_resume (恢复训练)

> [!abstract]
> 检查 `TrainingConfig.resume_from_checkpoint`，如果不为 None 就从该目录 load_state（model + optimizer + scheduler + dataloader 状态），否则跳过。

## 基本信息

| 属性 | 值 |
| --- | --- |
| 函数名 | `maybe_resume` |
| 所在文件 | `pi05_test/pi05/train/src/pi05/train/engine/checkpoints.py:11-18` |
| 调用位置 | `trainer.py:114` |
| 现实含义 | "训练被 kill 了 / 想继续训" → 从断点继续 |

## 行为

```python
def maybe_resume(accelerator: Accelerator, checkpoint_path: Path | None) -> None:
    if checkpoint_path is None:
        return
    checkpoint_path = checkpoint_path.expanduser().resolve()
    if not checkpoint_path.exists():
        raise FileNotFoundError(f"Resume checkpoint does not exist: {checkpoint_path}")
    accelerator.load_state(str(checkpoint_path))
    accelerator.print(f"Resumed training state from: {checkpoint_path}")
```

## 与 epoch checkpoint 的区别

| 维度 | maybe_resume 加载的 checkpoint | save_epoch_adapter_checkpoint 存的 checkpoint |
| --- | --- | --- |
| 内容 | model + optim + sched + dataloader | **只** LoRA adapter |
| 文件格式 | `accelerator.save_state` 的标准布局 | `adapter_model.safetensors` + `adapter_config.json` |
| 大小 | 完整 optim state（巨大） | < 100MB |
| 用途 | 中断恢复 | 部署导出 + epoch 评估 |

⚠️ **两者目录不通用**：`maybe_resume` 不能从 epoch checkpoint 恢复（缺 optim state），`save_pretrained` 出来的 adapter 也不能恢复训练。

## 关键约束

- **`checkpoint_path` 必须是 `accelerator.save_state` 输出的目录**：不是 LoRA adapter 目录
- **训练参数必须完全一致**：batch_size / grad_accum / mixed_precision 等改了可能恢复出问题
- **`is_main_process` 不包裹**：Accelerate 内置处理
- 与 [[Pi05LoraTrainer LoRA 训练器]] 配套
