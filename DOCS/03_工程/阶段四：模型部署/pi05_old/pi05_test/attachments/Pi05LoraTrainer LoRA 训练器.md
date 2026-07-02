---
tags:
  - 附件
---

# Pi05LoraTrainer (LoRA 训练器)

> [!abstract]
> 训练入口类，接收 `ExperimentConfig` 后负责装配 dataloader / Accelerator / 模型 / 优化器 / scheduler，然后跑 1 个 `_train_loop` 完成所有 epoch。

## 基本信息

| 属性 | 值 |
| --- | --- |
| 类名 | `Pi05LoraTrainer` |
| 所在文件 | `pi05_test/pi05/train/src/pi05/train/engine/trainer.py:75-319` |
| 入口函数 | `train_from_config(config)` (L322) |
| 现实含义 | 把 13 个外部 builder/checkpoint 工具拼成"一次完整的 LoRA fine-tune" |

## `run()` 装配顺序（L81-122）

| 步骤 | 行号 | 装配内容 |
| --- | --- | --- |
| 1 | 82 | `configure_logging()` |
| 2 | 83 | `set_training_seed(config.training.seed)` |
| 3 | 85 | `dataloader = build_train_dataloader(data_cfg, training_cfg)` |
| 4 | 86 | `num_training_steps = count_training_steps(dataloader, training_cfg)` |
| 5 | 88 | `accelerator = self._build_accelerator()` |
| 6 | 89 | `self._init_trackers(accelerator)` |
| 7 | 90-91 | `log_run_summary(LOGGER, config.run_summary())` |
| 8 | 93-96 | `model = build_pi05_with_lora(config, pretrained_path)` |
| 9 | 97 | `policy_config = get_pi05_policy_config(model)` |
| 10 | 98 | `policy_config.device = str(accelerator.device)` |
| 11 | 99 | `preprocessor, _ = make_pi05_pre_post_processors(policy_config, dataset_stats=None)` |
| 12 | 101 | `optimizer = build_optimizer(model, training_cfg)` |
| 13 | 102-106 | `lr_scheduler = build_lr_scheduler(optimizer, training_cfg, num_training_steps)` |
| 14 | 108-113 | `accelerator.prepare(model, optimizer, dataloader, lr_scheduler)` |
| 15 | 114 | `maybe_resume(accelerator, config.training.resume_from_checkpoint)` |
| 16 | 115-122 | `_train_loop(...)` |

## `_train_loop` 行为（L154-238）

```text
for epoch in range(train_cfg.epochs):
    for batch in dataloader:
        with accelerator.accumulate(model):
            processed = preprocessor(to_lerobot_pi05_batch(batch))
            loss, loss_dict = model(processed)
            accelerator.backward(loss)
            if accelerator.sync_gradients and grad_clip_norm is not None:
                grad_norm = accelerator.clip_grad_norm_(...)
            optimizer.step()
            lr_scheduler.step()
            optimizer.zero_grad(set_to_none=True)

        if accelerator.sync_gradients:
            total_steps += 1
            log_window.update(train_loss, lr, grad_norm)
            if total_steps % log_freq == 0:
                _flush_log_window(...)

    if (epoch+1) % checkpoint_freq_epochs == 0:
        save_epoch_adapter_checkpoint(...)

_flush_log_window(...)  # 训练结束最后一次 flush

if accelerator.is_main_process:
    final_adapter_dir = export_final_adapter(...)
    _maybe_export_deploy_bundle(...)
```

## 关键辅助类

| 类 | 行号 | 用途 |
| --- | --- | --- |
| `_AverageMeter` | 36-47 | 滑动平均一个标量 |
| `_LogWindow` | 50-72 | 多个 metric 的 `_AverageMeter` 字典，`log_freq` 步 flush 一次 |

## 关键设计决策

- **用 Accelerate 而不是原生 DDP**：单卡 / 多卡 / 混合精度 / TensorBoard 都用它
- **`accelerator.accumulate` 自动判断是否 sync_gradients**：gradient_accumulation 友好
- **preprocessor 一开始就构造**：`make_pi05_pre_post_processors` 把图像归一化、tokenize task 等都打包好
- **adapter checkpoint 只存 LoRA**：`save_pretrained` 只保存 PEFT adapter，不存 base Pi0.5 权重
- **可选导出 deploy bundle**：训练完调 `export_deploy_bundle`，让 model 立即能上机器人

## 关键约束

- **`gradient_accumulation_steps` 和 `accumulate` 配合**：Accelerate 会按这个步数自动切
- **`mixed_precision` 默认 `bf16`**：CUDA 可用时
- **`compile_model` 是 deploy 的事**：训练时不 compile
- **accelerator 决定单/多卡**：不用手动 wrap
- 与 [[ExperimentConfig 训练配置]]、[[build_pi05_with_lora 构造 Pi0.5+LoRA]]、[[Accelerate 分布式训练器]] 配套
