---
tags: [program-principle, data-card]
analysis: pi05-runtime-train-bundle
---

# InferenceRequest

> [!abstract]
> 控制循环提交给后台推理线程的单次请求，用 request id 和触发游标绑定一次观测。

| 属性 | 值 |
| --- | --- |
| 源码名 | `InferenceRequest` |
| 字段 | `observation`、`obs_time`、`request_id`、`trigger_step` |
| 生产者 | N04 预取推理请求 |
| 消费者 | N05 后台 policy 推理 |
| 源码位置 | `pi05_test/pi05/deploy/src/pi05/deploy/runtime/shared_buffer.py:61-68`; `control_loop.py:169-195` |

## 约束

控制循环已有 pending chunk、正在 blend、或 active chunk 还没到预取游标时不会提交新请求。

