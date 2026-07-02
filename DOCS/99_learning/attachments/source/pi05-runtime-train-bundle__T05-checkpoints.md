---
tags: [program-principle, source-annotation]
analysis: pi05-runtime-train-bundle
node: T05
---

# T05 保存 epoch/final adapter

> [!abstract]
> 保存 LoRA adapter，不保存完整 optimizer/scheduler 状态。

| 属性 | 值 |
| --- | --- |
| 节点类型 | 数据读写类 |
| 源码实现 | `pi05_test/pi05/train/src/pi05/train/engine/checkpoints.py:21-49` |
| 输入数据 | 训练后模型 |
| 输出数据 | final_adapter |

## 关键行

| 行号 | 为什么重要 |
| --- | --- |
| 21-33 | 按 epoch 保存 `checkpoint_epoch_N/adapter` |
| 36-43 | 训练完成保存 `final_adapter` |
| 46-49 | unwrap model 后调用 `save_pretrained()` |

