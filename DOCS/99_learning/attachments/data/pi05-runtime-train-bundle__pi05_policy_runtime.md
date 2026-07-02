---
tags: [program-principle, data-card]
analysis: pi05-runtime-train-bundle
---

# Pi05PolicyRuntime

> [!abstract]
> 部署侧运行时封装，持有模型、processor、normalizers、device、task、image names 和 action dim。

| 属性 | 值 |
| --- | --- |
| 源码名 | `Pi05PolicyRuntime` |
| 生产者 | T08 `load_policy_runtime()` |
| 消费者 | N05 `InferenceWorker` |
| 源码位置 | `pi05_test/pi05/deploy/src/pi05/deploy/models/policy_loader.py:27-78`; `policy_loader.py:110-155` |

## 生命周期

部署端用 bundle config 重建模型，加载 adapter，加载 normalizers，再返回 runtime。推理时 `predict_action_chunk()` 构造 batch、运行 policy、反归一化 action chunk。

