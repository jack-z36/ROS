---
tags: [program-principle, source-annotation]
analysis: pi05-runtime-train-bundle
node: T04
---

# T04 训练 batch 前处理和反传

> [!abstract]
> 将本地 batch 映射进 PI0.5 processor，计算 loss，执行 backward、clip、optimizer 和 scheduler step。

| 属性 | 值 |
| --- | --- |
| 节点类型 | 数据计算类 |
| 源码实现 | `pi05_test/pi05/train/src/pi05/train/engine/trainer.py:180-191` |
| 输入数据 | LeRobot训练batch、PEFT模型 |
| 输出数据 | 训练后模型 |

## 关键行

| 行号 | 为什么重要 |
| --- | --- |
| 182-183 | batch adapter 后交给 preprocessor，再喂给 model |
| 185-188 | backward 和可选 gradient clipping |
| 189-191 | optimizer step、scheduler step、清梯度 |

