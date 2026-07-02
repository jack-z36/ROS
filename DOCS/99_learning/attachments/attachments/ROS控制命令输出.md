---
tags:
  - 附件
  - pi05
  - deploy
---

# ROS控制命令输出

> [!abstract]
> 部署节点对下游执行系统发布的真正控制命令

## 基本信息

| 属性 | 值 |
| --- | --- |
| 变量名 | `left_arm_pub, right_arm_pub, left_hand_pub, right_hand_pub` |
| 参考系 | 不适用；这是程序数据流节点，不是几何坐标变换结果 |
| 相对原点 | 不适用 |
| 物理锚点 | 通信契约 / 最终输出 |
| 阶段属性 | 最终输出 |
| 是否最终输出 | 是 |
| 数据类型 | `JointState / Float64 ROS messages` |
| 数据结构 | 左臂 JointState + 右臂 JointState + 左手 Float64 + 右手 Float64 |
| 所在文件 | `pi05_test/pi05/deploy/src/pi05/deploy/ros_nodes/pi05_vla_deploy_node.py:196-211` |
| 现实含义 | 部署节点对下游执行系统发布的真正控制命令 |

## 关键澄清

### 1. 它在哪个参考系下？

不适用。这里的“参考系”不是机器人空间坐标系，而是程序流水线中的数据阶段。

### 2. 它相对哪个原点？

不适用。它不是空间点或位姿变换结果。

### 3. 它对应哪个物理点 / 物理对象？

通信契约 / 最终输出。如果它是缓存、请求或 batch，则无对应物理点，这是纯数学对象 / 程序容器。

### 4. 它是不是最终输出？

是。

### 5. 它不是什么？

它不应被误解为“整个推理程序的最终命令”。只有 ROS 控制命令输出才是下游执行系统真正收到的命令。

## 对应源码

```python
self.left_arm_pub.publish(_joint_msg(command.action.left_arm)); self.left_hand_pub.publish(Float64(...))
```

## 一句话说清楚

> 部署节点对下游执行系统发布的真正控制命令

## 在数据流中的位置

- 上游：安全后双臂动作
- 下游：下游机械臂 / 手爪执行系统
