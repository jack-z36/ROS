---
tags:
  - 附件
---

# Accelerate (分布式训练器)

> [!abstract]
> HuggingFace `accelerate` 库：Pi0.5 训练用的"统一包装器"，屏蔽单卡 / DDP / DeepSpeed / FSDP 的细节，提供 `prepare / backward / sync_gradients / clip_grad_norm_ / log / save_state` 等统一 API。

## 基本信息

| 属性 | 值 |
| --- | --- |
| 类名 | `accelerate.Accelerator` |
| 所在文件 | （HuggingFace accelerate 库，`Pi05LoraTrainer` 通过 `from accelerate import Accelerator` 引入） |
| 实例位置 | `trainer.py:88`（`_build_accelerator`） |
| 现实含义 | 单卡能跑、几行配置就能切多卡 + bf16 + grad accum + TensorBoard |

## `_build_accelerator` 构造（trainer.py:124-136）

```python
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
```

## 关键方法在 trainer.py 中的使用

| 方法 | 用途 | 位置 |
| --- | --- | --- |
| `accelerator.prepare(model, optimizer, dataloader, scheduler)` | 把 model/optimizer/dataloader 移动到正确 device，包成 DDP/FSDP 等 | L108-113 |
| `accelerator.accumulate(model)` | 上下文管理器：判断是否到 sync 步 | L181 |
| `accelerator.backward(loss)` | 替代 `loss.backward()`，兼容多卡 + fp16 | L185 |
| `accelerator.sync_gradients` | bool：当前是否 sync（gradient accum 友好） | L186, 193 |
| `accelerator.clip_grad_norm_(params, norm)` | gradient clipping | L187 |
| `accelerator.log(payload, step=...)` | 写入 TensorBoard / W&B 等 tracker | L270 |
| `accelerator.print(...)` | 仅主进程打印 | L178, 214 |
| `accelerator.is_main_process` | bool | L90, 147, 230, 271 |
| `accelerator.load_state(checkpoint_dir)` | 恢复训练 | `checkpoints.maybe_resume` |
| `accelerator.unwrap_model(model)` | 拿掉 DDP 包装，导出时用 | `checkpoints._save_adapter` L48 |
| `accelerator.wait_for_everyone()` | 同步多卡 | `checkpoints._save_adapter` |
| `accelerator.init_trackers(...)` | 初始化 TensorBoard | L142 |
| `accelerator.end_training()` | 收尾 | L238 |

## `mixed_precision` 取值

| 值 | 含义 |
| --- | --- |
| `"no"` | 不混精度，纯 fp32 |
| `"fp16"` | float16（带 GradScaler） |
| `"bf16"` | bfloat16（推荐，A100/H100/4090 都支持） |
| `"fp8"` | float8（Hopper 架构） |

trainer 默认：CUDA 可用时 `bf16`，否则 `no`。

## 关键约束

- **prepare 后不能再用 `.to(device)`**：accelerator 已管理设备
- **unwrap_model 才能 save_pretrained**：DDP/FSDP 包装的 model 没有 `save_pretrained` 直接调用
- **multi-GPU 时只能 main_process 写文件**：`is_main_process` 包裹所有 IO（save/print）
- 与 [[Pi05LoraTrainer LoRA 训练器]] 配套
