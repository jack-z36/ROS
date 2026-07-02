---
tags: [program-principle, data-card]
analysis: pi05-runtime-train-bundle
---

# 训练后模型

> [!abstract]
> 经过 loss、backward、optimizer step 和 lr scheduler step 更新后的 PEFT 模型。

| 属性 | 值 |
| --- | --- |
| 生产者 | T04 训练 batch 前处理和反传 |
| 消费者 | T05 保存 epoch/final adapter |
| 源码位置 | `pi05_test/pi05/train/src/pi05/train/engine/trainer.py:180-221` |

## 约束

只有在 `accelerator.sync_gradients` 时才累计 step、日志和 epoch step。

