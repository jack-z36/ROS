---
tags:
  - 附件
---

# build_pi05_with_lora (构造 Pi0.5+LoRA)

> [!abstract]
> 在 `lerobot/pi05_base` 预训练权重上叠加 PEFT LoRA 适配器，返回一个 `PeftModel`；`Pi05LoraTrainer` 在 `run()` 第 93-96 行调它构造模型。

## 基本信息

| 属性 | 值 |
| --- | --- |
| 函数名 | `build_pi05_with_lora` |
| 所在文件 | `pi05_test/pi05/common/src/pi05/common/model/builder.py` (Common Community 4) |
| 调用位置 | `trainer.py:93-96` |
| 现实含义 | 把"通用 Pi0.5 大模型" 变成"你任务专精的小模型"，只训 < 1% 参数 |

## 典型输入

```python
config = ExperimentConfig(...)  # 含 lora + model 字段
pretrained_path = "lerobot/pi05_base"  # 或本地 path
```

## 输出

```python
PeftModel  # PEFT 包装的 base model
```

## 关键行为（推断 / 通过 trainer.py 调用关系）

1. 加载 `lerobot/pi05_base` 预训练权重（huggingface hub 或本地）
2. 构造 `peft.LoraConfig(rank=config.lora.rank, alpha=config.lora.alpha, dropout=config.lora.dropout, target_modules=config.lora.target_modules)`
3. `peft.get_peft_model(base_model, lora_config)` → `PeftModel`
4. 如果 `model.train_expert_only=True`，冻结 base PaliGemma，只留 action expert 可训
5. 如果 `model.gradient_checkpointing=True`，启用 gradient checkpointing 省显存
6. 如果 `model.allow_random_init_peft=True`，允许从随机初始化（无 pretrained）启动

## 关键参数（来自 `ModelConfig`）

| 字段 | 含义 |
| --- | --- |
| `pretrained_path` | 预训练权重路径 |
| `device` | 模型所在设备 |
| `dtype` | `bfloat16` / `float16` / `float32` |
| `gradient_checkpointing` | 是否启用 gradient checkpointing |
| `train_expert_only` | 是否只训 action expert |
| `allow_random_init_peft` | 是否允许随机初始化 PEFT（无预训练） |
| `paligemma_variant` | `gemma_2b` 等 |
| `action_expert_variant` | `gemma_300m` 等 |

## 在数据流中的位置

```text
lerobot/pi05_base  (HF hub or local)
    ↓
build_pi05_with_lora(config, pretrained_path)
    ↓
PeftModel  (PaliGemma 冻结 + LoRA 可训)
    ↓
get_pi05_policy_config(model)  →  policy_config
    ↓
make_pi05_pre_post_processors(policy_config)  →  preprocessor
    ↓
Pi05LoraTrainer._train_loop
```

## 关键约束

- **target_modules 必须与 PEFT 约定一致**：见 [[LoraConfig LoRA 配置]]
- **dtype 锁死**：训练一旦 bfloat16 启动，整轮都是 bfloat16
- **gradient checkpointing 必开**：Pi0.5 ~3B 参数，bf16 + LoRA 也很难不 ckpt
- **train_expert_only 加速**：冻结 vision-language 只训 action expert 时参数更少
- 与 [[Pi05LoraTrainer LoRA 训练器]]、[[LoraConfig LoRA 配置]]、[[make_pi05_pre_post_processors LeRobot PI0.5 preprocessor]] 配套
