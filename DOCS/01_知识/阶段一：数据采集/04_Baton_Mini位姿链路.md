# Baton Mini 位姿链路

Baton Mini 链路负责提供位姿模态。阶段一关注它如何发布原始位姿 topic；坐标转换、TCP 语义和训练侧 action 构造属于阶段二及之后的处理。

## 链路模型

```text
Baton Mini 设备
  -> SDK / ROS2 节点
  -> pose topic
  -> Octopus 录制
  -> raw MCAP
```

## 阶段边界

- 阶段一保留原始位姿消息。
- 阶段一不把原始位姿直接解释为训练 action。
- 位姿到 TCP、arm-base 或其他生产坐标语义的转换，属于阶段二知识与工程。
