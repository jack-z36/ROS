---
tags: [program-principle, source-annotation]
analysis: pi05-runtime-train-bundle
node: N08
---

# N08 ROS2 命令发布与 metrics

> [!abstract]
> 将 `ControlCommand` 发布到左右臂、左右手 topic，并周期发布 metrics/status。

| 属性 | 值 |
| --- | --- |
| 节点类型 | 外部接口类 |
| 源码实现 | `pi05_test/pi05/deploy/src/pi05/deploy/ros_nodes/pi05_vla_deploy_node.py:196-218` |
| 输入数据 | ControlCommand、RuntimeMetrics |
| 输出数据 | ROS2 command topics、status、metrics |

## 关键行

| 行号 | 为什么重要 |
| --- | --- |
| 196-207 | dry-run 分支只打印命令，不发硬件 topic |
| 208-211 | 发布左右臂 JointState 和左右手 Float64 |
| 213-218 | 合并 SharedBuffer metrics 和 ControlLoop status 后发布 |

