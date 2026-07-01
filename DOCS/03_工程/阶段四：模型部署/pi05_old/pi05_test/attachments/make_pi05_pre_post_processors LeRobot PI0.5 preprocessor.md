---
tags:
  - 附件
---

# make_pi05_pre_post_processors (LeRobot PI0.5 preprocessor)

> [!abstract]
> LeRobot 上游 `lerobot.policies.pi05.processor_pi05` 提供的工厂函数：构造 PI0.5 模型的"前处理 + 后处理"对——把 `{observation.state, observation.images.*, task, action}` 字典转成模型真正吃的 tensors。

## 基本信息

| 属性 | 值 |
| --- | --- |
| 函数名 | `make_pi05_pre_post_processors` |
| 来源 | `lerobot.policies.pi05.processor_pi05`（vendored 在 `third_party/lerobot`） |
| 调用位置 | `trainer.py:99` |
| 现实含义 | 把"自然语言 + 图像 + 数值" 编码成 PaliGemma + action expert 能吃的格式 |

## 调用

```python
preprocessor, postprocessor = make_pi05_pre_post_processors(
    policy_config,
    dataset_stats=None,  # 我们用 builder 算的 normalizer，不在这里传
)
```

`postprocessor` 在训练时不使用，部署时反归一化用。

## preprocessor 内部职责（推断 / 通过 LeRobot 文档）

1. **图像归一化**：缩放到 224×224、归一化到 ImageNet 均值/方差
2. **状态归一化**：用 `dataset_stats` 里的 mean / std 把 26D state 标准化
3. **动作归一化**：用 `dataset_stats` 里的 mean / std 把 14D action 标准化
4. **task tokenize**：用 PaliGemma tokenizer 把 task 字符串转成 input_ids + attention_mask
5. **拼 batch**：把上述字段按 PI0.5 期望的 key（`observation.state`, `observation.images.*`, `observation.language.tokens` 等）打包

## `dataset_stats` 为何传 `None`

我们用本地 `Pi05LeRobotDataset` 自带的 normalizer（在 `__getitem__` 里归一化 state / action），所以 `make_pi05_pre_post_processors` 不需要再做归一化。LeRobot 的 preprocessor 只负责图像 resize + tokenizer 编码。

## 在数据流中的位置

```text
batch (dataloader 输出，未归一化的 tensor)
    ↓
to_lerobot_pi05_batch  →  model_batch (key rename)
    ↓
preprocessor(model_batch)  →  processed_batch (PaliGemma 格式)
    ↓
model(processed_batch)  →  loss, loss_dict
```

## 关键约束

- **`policy_config.device` 必须设置**：在 `trainer.py:98` 显式赋值 `str(accelerator.device)`
- **`preprocessor` 内含 tokenizer 缓存**：PaliGemma tokenizer 一次性加载，之后每帧很快
- **dataset_stats 与 dataset 自带 normalizer 不能双跑**：否则会归一化两次
- 与 [[build_pi05_with_lora 构造 Pi0.5+LoRA]]、[[to_lerobot_pi05_batch batch 字段名转换]] 配套
