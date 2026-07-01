---
tags:
  - 附件
---

# ExperimentConfig (训练配置)

> [!abstract]
> `Pi05LoraTrainer.__init__` 接收的强类型 YAML 配置（来自 `pi05.common.config.schema.ExperimentConfig`），由 5 个子 dataclass 组成，是 trainer 与 `cli/train.py` 之间的唯一契约。

## 基本信息

| 属性 | 值 |
| --- | --- |
| 类名 | `ExperimentConfig` (frozen dataclass) |
| 加载方式 | `load_experiment_config(path)` from `pi05.common.config.__init__` |
| 位置 | `pi05_test/pi05/common/src/pi05/common/config/schema.py:197-244` |
| 现实含义 | 描述"这次训练用什么数据、跑哪个模型、LoRA 怎么配、优化器怎么走、日志打哪里" |

## 子配置清单

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `lora` | `LoraConfig` | LoRA rank/alpha/dropout/target_modules |
| `data` | `DataConfig` | 数据集路径 + chunk + image_size + state/action dim |
| `model` | `ModelConfig` | Pi0.5 预训练权重 + device + dtype + 变体 |
| `training` | `TrainingConfig` | batch_size/lr/epochs/grad_accum/warmup/grad_clip |
| `logging` | `LoggingConfig` | project_name/run_name/output_dir + TensorBoard |
| `raw` | `Mapping[str, Any]` | 原始 YAML 字典（不 repr） |

## YAML 顶层结构示例

```yaml
lora:
  rank: 16
  alpha: 32
  dropout: 0.05
  target_modules: [q_proj, k_proj, v_proj, o_proj]
data:
  dataset_path: /data/lr/pour_demo
  fps: 30
  chunk_size: 30
  image_size: 224
  state_dim: 26
  action_dim: 14
  cameras: [top, left_wrist, right_wrist]
model:
  pretrained_path: lerobot/pi05_base
  device: cuda:0
  dtype: bfloat16
  chunk_size: 30
  state_dim: 26
  action_dim: 14
  paligemma_variant: gemma_2b
  action_expert_variant: gemma_300m
training:
  batch_size: 4
  lr: 2.0e-4
  epochs: 10
  gradient_accumulation_steps: 4
  warmup_steps: 100
  checkpoint_freq_epochs: 1
  grad_clip_norm: 1.0
  mixed_precision: bf16
logging:
  project_name: pi05_pour
  run_name: v1
  output_dir: /workspace/runs
  use_tensorboard: true
  tensorboard_port: 6006
```

## 关键方法

| 方法 | 用途 |
| --- | --- |
| `ExperimentConfig.from_mapping(raw, base_dir=...)` | 从 dict 构造 |
| `load_experiment_config(path)` | 从 YAML 文件加载 |
| `to_tracker_config()` | 拍平为 `section.key` 形式的 tracker config |
| `run_summary()` | 训练启动时打印的 1 行 summary dict |

## 关键约束

- **frozen=True**：构造后不能再改
- **所有路径用 `Path`**：`dataset_path`, `output_dir`, `resume_from_checkpoint` 等
- **`chunk_size` 在 `data` 和 `model` 都出现**：必须保持一致（schema 不强制但运行时假设）
- 与 [[LoraConfig LoRA 配置]]、[[DataConfig 数据配置]]、[[ModelConfig 模型配置]]、[[TrainingConfig 训练配置]]、[[LoggingConfig 日志配置]] 配套
