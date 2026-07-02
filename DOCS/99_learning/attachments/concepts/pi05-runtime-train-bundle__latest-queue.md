---
tags: [program-principle, concept]
analysis: pi05-runtime-train-bundle
---

# LatestQueue 实时丢旧保新队列

> [!abstract]
> `LatestQueue` 是实时部署链路的节流机制：慢消费者不会处理过期请求或过期结果。

## 在本代码库中的具体含义

`SharedBuffer` 用它承载 inference request 和 chunk result。`put_latest()` 在满时先丢最旧项，`get_latest_or_none()` 取最新项后清空旧项，源码在 `shared_buffer.py:71-94`。

## 和数据流的关系

- 相关节点：N03、N04、N05、N06
- 相关数据：InferenceRequest、ActionChunk

