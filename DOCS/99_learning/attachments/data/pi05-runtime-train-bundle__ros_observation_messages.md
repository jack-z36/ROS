---
tags: [program-principle, data-card]
analysis: pi05-runtime-train-bundle
---

# ROS2观测消息

> [!abstract]
> ROS2 callback 收到的图像、关节、手和末端位姿消息，是部署链路的外部输入。

| 属性 | 值 |
| --- | --- |
| 数据名 | ROS2观测消息 |
| 数据类型 | `CompressedImage` / `Image` / `JointState` / `Point` / `Vector3` |
| 生产者 | 机器人 ROS2 topic |
| 消费者 | N02 观测字段采集与快照 |
| 源码位置 | `pi05_test/pi05/deploy/src/pi05/deploy/ros_nodes/pi05_vla_deploy_node.py:154-182` |

## 生命周期

每个 callback 将一个 topic payload 转换或转发给 `ObservationCollector`，随后尝试发布完整快照到 `SharedBuffer`。

## 约束

- 图像必须能解码成 RGB 并通过 `preprocess_rgb_image()`。
- 关节状态需要满足配置中的 proprioception 顺序。
- 任一必要字段缺失时，不会产生 `ObservationSnapshot`。

