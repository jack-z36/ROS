---
tags: [program-principle, data-card]
analysis: pi05-runtime-train-bundle
---

# 模型配置和LoRA配置

> [!abstract]
> 控制 Pi0.5 backbone、维度、attention、chunk 和 LoRA target/rank 的配置集合。

| 属性 | 值 |
| --- | --- |
| 生产者 | T02 Trainer |
| 消费者 | T03 `build_pi05_with_lora()` |
| 源码位置 | `pi05_test/pi05/common/src/pi05/common/model/builder.py:52-72`; `builder.py:137-152` |

## 约束

`action_dim` 锁定为 14；`max_action_dim` 必须等于 `action_dim`。这保证训练输出和部署安全过滤的动作结构一致。

