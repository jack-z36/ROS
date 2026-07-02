---
tags: [program-principle, data-card]
analysis: pi05-runtime-train-bundle
---

# ActionChunk

> [!abstract]
> policy 一次推理返回的多步 action 序列，是后台推理线程和高频控制循环之间的核心数据。

| 属性 | 值 |
| --- | --- |
| 源码名 | `ActionChunk` |
| 数据结构 | `actions` 二维数组、`obs_time`、`infer_start_time`、`ready_time`、`action_dt`、`request_id` |
| 生产者 | N05 后台 policy 推理 |
| 消费者 | N06 chunk 消费、blend、fallback |
| 源码位置 | `pi05_test/pi05/deploy/src/pi05/deploy/runtime/shared_buffer.py:34-58`; `inference_worker.py:74-86` |

## 约束

- `actions` 必须是 rank=2，第二维等于 `action_dim`。
- chunk 年龄不能超过 `max_action_age_s`。
- 对齐索引太靠近 chunk 末尾会被丢弃。

