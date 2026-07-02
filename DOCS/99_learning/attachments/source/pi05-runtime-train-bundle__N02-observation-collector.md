---
tags: [program-principle, source-annotation]
analysis: pi05-runtime-train-bundle
node: N02
---

# N02 观测字段采集与快照

> [!abstract]
> 收集最新图像和机器人状态，字段齐全且不过期时构造 `ObservationSnapshot`。

| 属性 | 值 |
| --- | --- |
| 节点类型 | 数据计算类 |
| 源码实现 | `pi05_test/pi05/deploy/src/pi05/deploy/runtime/observation_collector.py:20-103` |
| 输入数据 | [[attachments/data/pi05-runtime-train-bundle__ros_observation_messages|ROS2观测消息]] |
| 输出数据 | [[attachments/data/pi05-runtime-train-bundle__observation_snapshot|ObservationSnapshot]] |

## 关键行

| 行号 | 为什么重要 |
| --- | --- |
| 43-73 | 各类 update 方法只更新局部字段和时间戳 |
| 75-81 | 快照前检查 required fields 和 stale timeout |
| 88-103 | 构造 `BimanualState`、编码为 26D，并返回快照 |

## 容易误解

它不负责推理，也不负责发布；它只是把异步 topic 字段变成一次可用观测。

