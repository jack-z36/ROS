---
tags: [program-principle, data-card]
analysis: pi05-runtime-train-bundle
---

# ObservationSnapshot

> [!abstract]
> 冻结的策略观测对象，包含图像、结构化双臂状态、26D 编码状态和采集时间。

| 属性 | 值 |
| --- | --- |
| 数据名 | ObservationSnapshot |
| 源码名 | `ObservationSnapshot` |
| 数据结构 | `images`、`state`、`encoded_state`、`captured_at_s` |
| 生产者 | N02 观测字段采集与快照 |
| 消费者 | N03 共享运行态缓冲、N04 预取推理请求、T08 policy runtime |
| 源码位置 | `pi05_test/pi05/deploy/src/pi05/deploy/runtime/shared_buffer.py:23-31`; `observation_collector.py:75-103` |

## 定义

它是 policy 一次推理请求的观测边界。`ObservationCollector.snapshot()` 只有在所有图像和状态字段都齐全、且未超过 stale timeout 时才返回它。

## 约束

- `encoded_state` 是 canonical 26D bimanual state。
- 图像 tensor 被 clone，避免 callback 后续更新影响已提交请求。

