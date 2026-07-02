---
tags:
  - 附件
  - pi05
  - deploy
---

# 策略推理batch

> [!abstract]
> 把 ObservationSnapshot 转成 LeRobot/Pi05 policy 可接受的输入格式

## 基本信息

| 属性 | 值 |
| --- | --- |
| 变量名 | `batch` |
| 参考系 | 不适用；这是程序数据流节点，不是几何坐标变换结果 |
| 相对原点 | 不适用 |
| 物理锚点 | 纯数学对象 / 模型输入容器 |
| 阶段属性 | 模型输入前中间态 |
| 是否最终输出 | 否 |
| 数据类型 | `dict[str, Any]` |
| 数据结构 | 包含 observation.state、task 和多路 observation.images.* tensor 的字典 |
| 所在文件 | `pi05_test/pi05/deploy/src/pi05/deploy/models/policy_loader.py:80-95` |
| 现实含义 | 把 ObservationSnapshot 转成 LeRobot/Pi05 policy 可接受的输入格式 |

## 关键澄清

### 1. 它在哪个参考系下？

不适用。这里的“参考系”不是机器人空间坐标系，而是程序流水线中的数据阶段。

### 2. 它相对哪个原点？

不适用。它不是空间点或位姿变换结果。

### 3. 它对应哪个物理点 / 物理对象？

纯数学对象 / 模型输入容器。如果它是缓存、请求或 batch，则无对应物理点，这是纯数学对象 / 程序容器。

### 4. 它是不是最终输出？

否。

### 5. 它不是什么？

它不应被误解为“整个推理程序的最终命令”。只有 ROS 控制命令输出才是下游执行系统真正收到的命令。

## 对应源码

```python
batch = {"observation.state": state, "task": self.task}; batch[f"observation.images.{image_name}"] = ...
```

## 一句话说清楚

> 把 ObservationSnapshot 转成 LeRobot/Pi05 policy 可接受的输入格式

## 在数据流中的位置

- 上游：完整策略观测快照
- 下游：policy.predict_action_chunk
