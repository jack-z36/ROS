---
tags:
  - 附件
---

# _train_loop (核心训练循环)

> [!abstract]
> `Pi05LoraTrainer` 的核心方法（L154-238）：跑 N 个 epoch、每个 batch 走 forward+backward+optim step、按 `log_freq` flush 日志、按 `checkpoint_freq_epochs` 存 adapter、最后导 final_adapter + 可选 deploy_bundle。

## 基本信息

| 属性 | 值 |
| --- | --- |
| 方法 | `Pi05LoraTrainer._train_loop` (private) |
| 所在文件 | `trainer.py:154-238` |
| 调用方 | `Pi05LoraTrainer.run` (L115-122) |
| 现实含义 | 整个训练的"业务循环"——其它代码都只是装配 |

## 详细步骤

### 初始化（L164-171）

```python
train_cfg = self.config.training
log_cfg = self.config.logging
run_output_dir = log_cfg.run_output_dir
model.train()
total_steps = 0
state_dim: int | None = None
log_window = _LogWindow()
```

### 训练循环（L172-218）

```text
for epoch in range(train_cfg.epochs):
    epoch_steps = 0
    for batch in dataloader:
        if state_dim is None:
            state_dim = int(batch["state"].shape[-1])  # 从第一批探测
            accelerator.print(f"[train] state_dim={state_dim}")

        grad_norm_value: float | None = None
        with accelerator.accumulate(model):                    # ① gradient accum
            processed_batch = preprocessor(to_lerobot_pi05_batch(batch))  # ② 转换
            loss, loss_dict = model(processed_batch)            # ③ forward
            accelerator.backward(loss)                          # ④ backward
            if accelerator.sync_gradients and train_cfg.grad_clip_norm is not None:
                grad_norm = accelerator.clip_grad_norm_(model.parameters(), train_cfg.grad_clip_norm)
                grad_norm_value = self._to_float(grad_norm)
            optimizer.step()                                    # ⑤ optim
            lr_scheduler.step()                                # ⑥ lr
            optimizer.zero_grad(set_to_none=True)

        if accelerator.sync_gradients:
            total_steps += 1
            epoch_steps += 1
            log_window.update(train_loss=..., lr=..., grad_norm=...)  # ⑦ record

            if total_steps % log_cfg.log_freq == 0:
                self._flush_log_window(...)                      # ⑧ log

        if max_steps_per_epoch reached:
            break
```

### 收尾（L220-238）

```text
if (epoch + 1) % checkpoint_freq_epochs == 0:
    save_epoch_adapter_checkpoint(accelerator, model, run_output_dir, epoch+1)

_flush_log_window(...)  # 最后一次 flush

if accelerator.is_main_process:
    final_adapter_dir = export_final_adapter(accelerator, model, run_output_dir)
    _maybe_export_deploy_bundle(accelerator, final_adapter_dir)
```

### 异常路径（L236-238）

```text
finally:
    if log_cfg.use_tensorboard:
        accelerator.end_training()  # 关掉 TensorBoard writer
```

## 关键设计决策

- **state_dim 探测**：从第一个 batch 的 `state` tensor shape 自动探测，**比 YAML 写死更鲁棒**
- **`accumulate` 上下文管理器**：由 Accelerate 决定是否 sync_gradients
- **grad clip 在 sync 时才做**：gradient accum 期间 clip 没意义
- **`zero_grad(set_to_none=True)`**：节省内存（PyTorch ≥ 1.7）
- **`_maybe_export_deploy_bundle` 容错**：导出失败只打 warning，不中断训练
- **flush_log_window 至少 1 步**：避免空 log

## 关键约束

- **`max_steps_per_epoch` 是 step 而非 epoch**：1 step = 1 optim update（不等同于 1 batch）
- **`checkpoint_freq_epochs` 存 LoRA adapter 不存 optim**：节省磁盘
- **`end_training()` 必须调**：否则 TensorBoard writer 句柄泄漏
- 与 [[Pi05LoraTrainer LoRA 训练器]]、[[save_epoch_adapter_checkpoint epoch LoRA 存盘]]、[[export_deploy_bundle 部署 bundle 导出]] 配套
