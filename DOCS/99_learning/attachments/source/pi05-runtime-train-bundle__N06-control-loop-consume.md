---
tags: [program-principle, source-annotation]
analysis: pi05-runtime-train-bundle
node: N06
---

# N06 chunk 消费、blend、fallback

> [!abstract]
> 高频 tick 不等待模型，消费已有 chunk、预取新 chunk、在 chunk 边界 blend，并在无动作时 fallback。

| 属性 | 值 |
| --- | --- |
| 节点类型 | 流程编排类 |
| 源码实现 | `pi05_test/pi05/deploy/src/pi05/deploy/runtime/control_loop.py:112-333` |
| 输入数据 | ActionChunk、ObservationSnapshot |
| 输出数据 | raw 14D action、ControlCommand 或 None |

## 关键行

| 行号 | 为什么重要 |
| --- | --- |
| 112-138 | `tick()` 的核心顺序：收结果、提交请求、取 raw action、安全过滤 |
| 151-167 | 从 result queue 收 chunk 并做 usable 校验 |
| 197-222 | 从 active chunk 或 blend 结果取下一条动作 |
| 290-314 | smoothstep blend 两个 chunk 的边界动作 |
| 316-333 | safe_stop 或 hold_last_action fallback |

