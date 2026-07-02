---
tags: [program-principle, source-annotation]
analysis: pi05-runtime-train-bundle
node: T02
---

# T02 Trainer 编排构建器和训练循环

> [!abstract]
> 统一组织 dataloader、Accelerate、模型构建、optimizer/scheduler、resume 和训练循环。

| 属性 | 值 |
| --- | --- |
| 节点类型 | 流程编排类 |
| 源码实现 | `pi05_test/pi05/train/src/pi05/train/engine/trainer.py:75-123` |
| 输入数据 | ExperimentConfig |
| 输出数据 | PEFT模型、训练过程 |

## 关键行

| 行号 | 为什么重要 |
| --- | --- |
| 81-89 | 配置日志、随机种子、dataloader、training steps 和 accelerator |
| 93-100 | 构建 LoRA 模型并创建 PI0.5 preprocessor |
| 101-114 | 构建 optimizer/scheduler，交给 accelerator，并可 resume |
| 115-122 | 进入 `_train_loop()` |

