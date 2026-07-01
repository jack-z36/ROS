---
tags: [program-principle, source-annotation]
analysis: pi05-runtime-train-bundle
node: N03
---

# N03 共享运行态缓冲

> [!abstract]
> 在线程之间保存最新观测、推理请求队列、chunk 结果队列和 metrics。

| 属性 | 值 |
| --- | --- |
| 节点类型 | 数据读写类 |
| 源码实现 | `pi05_test/pi05/deploy/src/pi05/deploy/runtime/shared_buffer.py:156-242` |
| 输入数据 | ObservationSnapshot、InferenceRequest、ActionChunk |
| 输出数据 | 最新观测、pending chunk、RuntimeMetrics |

## 关键行

| 行号 | 为什么重要 |
| --- | --- |
| 165-169 | 建立锁、最新观测、request/result LatestQueue 和 metrics |
| 171-185 | 写入和读取最新观测，可按 max age 过滤 |
| 187-242 | 所有 record 方法都在锁内更新 metrics |

## 容易误解

它不是无限队列；配合 `LatestQueue` 的语义是实时系统中保新丢旧。

