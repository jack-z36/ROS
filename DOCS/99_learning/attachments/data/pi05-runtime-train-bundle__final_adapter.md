---
tags: [program-principle, data-card]
analysis: pi05-runtime-train-bundle
---

# final_adapter

> [!abstract]
> 训练完成后导出的 LoRA adapter 目录，是 bundle 的模型权重输入。

| 属性 | 值 |
| --- | --- |
| 源码名 | `final_adapter_dir` |
| 生产者 | T05 `export_final_adapter()` |
| 消费者 | T06 `export_deploy_bundle()` |
| 源码位置 | `pi05_test/pi05/train/src/pi05/train/engine/checkpoints.py:36-49`; `trainer.py:230-256` |

## 约束

保存时先 `accelerator.unwrap_model(model)`，再调用 `save_pretrained(output_dir)`。

