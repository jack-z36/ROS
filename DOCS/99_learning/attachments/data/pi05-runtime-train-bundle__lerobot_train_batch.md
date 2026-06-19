---
tags: [program-principle, data-card]
analysis: pi05-runtime-train-bundle
---

# LeRobot训练batch

> [!abstract]
> dataloader 产出的 batch，经本地 adapter 转成官方 PI0.5 processor 期望的输入 schema。

| 属性   | 值                                                               |
| ---- | --------------------------------------------------------------- |
| 生产者  | T02 dataloader                                                  |
| 消费者  | T04 训练 batch 前处理和反传                                             |
| 源码位置 | `pi05_test/pi05/train/src/pi05/train/engine/trainer.py:175-183` |

## 约束

第一次 batch 会读取并打印 `batch["state"].shape[-1]` 作为 state_dim 观察点。

