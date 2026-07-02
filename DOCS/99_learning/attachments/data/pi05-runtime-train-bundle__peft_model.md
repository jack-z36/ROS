---
tags: [program-principle, data-card]
analysis: pi05-runtime-train-bundle
---

# PEFT模型

> [!abstract]
> 由 `PI05Policy` 包装 LoRA adapter 后返回的训练模型。

| 属性 | 值 |
| --- | --- |
| 生产者 | T03 构建 Pi0.5 LoRA 模型 |
| 消费者 | T04 训练循环、T05 adapter 保存 |
| 源码位置 | `pi05_test/pi05/common/src/pi05/common/model/builder.py:137-152` |

## 约束

构建时会设置 state/action normalization 为 identity，并启用 gradient checkpointing 的 best-effort hook。

