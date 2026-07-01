---
tags:
  - 附件
  - pi05
  - deploy
---

# ROS观测输入通道

> [!abstract]
> 硬件观测进入部署节点的 ROS 入口

## 基本信息

| 属性 | 值 |
| --- | --- |
| 变量名 | `config.topics.observation.*` |
| 参考系 | 不适用；这是程序数据流节点，不是几何坐标变换结果 |
| 相对原点 | 不适用 |
| 物理锚点 | 通信契约 |
| 阶段属性 | 原始输入 |
| 是否最终输出 | 否 |
| 数据类型 | `ROS topic names / messages` |
| 数据结构 | 多个 ROS topic 共同承载图像、关节、手爪和 EE 位姿字段 |
| 所在文件 | `pi05_test/pi05/deploy/src/pi05/deploy/config/schema.py:94-116` |
| 现实含义 | 硬件观测进入部署节点的 ROS 入口 |

## 关键澄清

### 1. 它在哪个参考系下？

不适用。这里的“参考系”不是机器人空间坐标系，而是程序流水线中的数据阶段。

### 2. 它相对哪个原点？

不适用。它不是空间点或位姿变换结果。

### 3. 它对应哪个物理点 / 物理对象？

通信契约。如果它是缓存、请求或 batch，则无对应物理点，这是纯数学对象 / 程序容器。

### 4. 它是不是最终输出？

否。

### 5. 它不是什么？

它不应被误解为“整个推理程序的最终命令”。只有 ROS 控制命令输出才是下游执行系统真正收到的命令。

## 对应源码

```python
class ObservationTopicsConfig: top_image, proprioception, hand states, ee position/rpy topics
```

## 一句话说清楚

> 硬件观测进入部署节点的 ROS 入口

## 在数据流中的位置

- 上游：外部硬件观测源
- 下游：Pi05VlaDeployNode subscriptions
