---
tags: [program-principle, source-annotation]
analysis: pi05-runtime-train-bundle
node: N04
---

# N04 预取推理请求

> [!abstract]
> 控制循环根据 active chunk 游标决定是否预取下一次 policy 推理。

| 属性 | 值 |
| --- | --- |
| 节点类型 | 流程编排类 |
| 源码实现 | `pi05_test/pi05/deploy/src/pi05/deploy/runtime/control_loop.py:169-195` |
| 输入数据 | 最新 ObservationSnapshot |
| 输出数据 | InferenceRequest |

## 关键行

| 行号 | 为什么重要 |
| --- | --- |
| 170-177 | pending、blend、未到预取点时直接返回 |
| 178-181 | 没有可用观测时只记录 fallback 信息 |
| 182-191 | 创建 request 并放入 LatestQueue |

