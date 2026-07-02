---
tags:
  - 附件
---

# LoraConfig (LoRA 配置)

> [!abstract]
> `ExperimentConfig.lora` 子配置：LoRA 低秩适配器的 rank / alpha / dropout / target_modules。Pi0.5 微调的"只训少量参数"开关。

## 基本信息

| 属性 | 值 |
| --- | --- |
| 类名 | `LoraConfig` (frozen dataclass) |
| 位置 | `pi05_test/pi05/common/src/pi05/common/config/schema.py:19-33` |
| 现实含义 | "哪几个线性层用 LoRA 替换 + 秩多大" — 决定可训练参数量和显存 |

## 字段

| 字段 | 类型 | 约束 | 含义 |
| --- | --- | --- | --- |
| `rank` | `int` | `> 0` | LoRA 秩，越大表达力越强但参数越多 |
| `alpha` | `int` | `> 0` | 缩放系数，实际缩放 = `alpha / rank` |
| `dropout` | `float` | `[0.0, 1.0]` | LoRA 内的 dropout |
| `target_modules` | `str \| tuple[str, ...]` | 非空 | 要替换的线性层名（PEFT 约定） |

## target_modules 常用取值

| 值 | 含义 |
| --- | --- |
| `"all-linear"` | PEFT 默认：所有 nn.Linear 都加 LoRA |
| `("q_proj", "k_proj", "v_proj", "o_proj")` | 只训 attention |
| `("q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj")` | attention + MLP |
| `"q,k,v,o,gate,up,down"` | 同上但简写 |

## 校验（`from_mapping` 末尾隐式）

- `rank > 0` → `_positive_int`
- `alpha > 0` → `_positive_int`
- `dropout ∈ [0, 1]` → `_float(min=0, max=1)`
- `target_modules` 字符串或非空 list → `_str_or_str_list`

## 在数据流中的位置

```text
YAML lora: { rank, alpha, dropout, target_modules }
    ↓
LoraConfig.from_mapping(raw)  ←  ExperimentConfig.lora
    ↓
build_pi05_with_lora(config, pretrained_path)
    ↓
peft.get_peft_model(base_model, LoraConfig(...))  ←  Pi0.5 + LoRA
```

## 关键约束

- **不冻结 base**：`train_expert_only` 是 `ModelConfig` 的字段，不在 LoRA；`build_pi05_with_lora` 自己处理
- **`alpha / rank` 比值控制 LoRA 影响**：通常 `alpha = 2 * rank` (经验值)
- **target_modules 必须用 PaliGemma/Gemma 的实际层名**：见 `lerobot.policies.pi05` 模型定义
- 与 [[Pi05LoraTrainer LoRA 训练器]] 配套
