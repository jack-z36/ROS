---
tags: [program-principle, source-annotation]
analysis: pi05-runtime-train-bundle
node: T03
---

# T03 构建 Pi0.5 LoRA 模型

> [!abstract]
> 加载或随机初始化 PI05Policy，校验 14D action schema，设置 feature specs，并 wrap LoRA。

| 属性 | 值 |
| --- | --- |
| 节点类型 | 数据计算类 |
| 源码实现 | `pi05_test/pi05/common/src/pi05/common/model/builder.py:34-152` |
| 输入数据 | 模型配置和LoRA配置 |
| 输出数据 | PEFT模型 |

## 关键行

| 行号 | 为什么重要 |
| --- | --- |
| 68-71 | action_dim 锁定为 14，并要求 max_action_dim 相等 |
| 101-127 | 从 pretrained config/model 加载 PI05Policy |
| 130-135 | 调整 action projection，并把 state/action normalizer 设为 identity |
| 137-152 | 创建 LoRA config，wrap PEFT，返回模型 |

