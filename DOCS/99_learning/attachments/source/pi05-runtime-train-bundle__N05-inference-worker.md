---
tags: [program-principle, source-annotation]
analysis: pi05-runtime-train-bundle
node: N05
---

# N05 后台 policy 推理

> [!abstract]
> 后台线程消费 `InferenceRequest`，调用 policy runtime，产出 `ActionChunk`。

| 属性 | 值 |
| --- | --- |
| 节点类型 | 数据计算类 |
| 源码实现 | `pi05_test/pi05/deploy/src/pi05/deploy/runtime/inference_worker.py:15-91` |
| 输入数据 | InferenceRequest |
| 输出数据 | ActionChunk |

## 关键行

| 行号 | 为什么重要 |
| --- | --- |
| 47-61 | 循环获取最新请求，并按 inference_hz 限频 |
| 63-72 | 调用 `predict_action_chunk()`，异常只记录错误 |
| 74-86 | 包装 ActionChunk、记录 latency、写入 result queue |

