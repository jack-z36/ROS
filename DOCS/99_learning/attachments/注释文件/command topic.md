---
tags:
  - term-explainer
  - pi05
  - data-read-write
source: [[部署推理数据流框架|部署推理数据流框架]]
---

# command topic

> [!abstract] 核心定义
> ROS2 中用于发布控制命令的 topic，在这里承载左臂、右臂、左手、右手命令。

## 数据流向

| 方向 | 数据源 | 具体内容 | 格式/类型 |
|------|--------|----------|-----------|
| 写入 | Pi05VlaDeployNode._control_tick() | JointState / Float64 | ROS2 message |
| 读取 | downstream controller / bridge | command message | ROS2 subscription |

> [!note] 注
> 这里只保留该术语实际涉及的读写方向。

## 读写逻辑

1. **写入阶段**：将 `BimanualAction` 拆成四路 ROS message 并 publish。
2. **读取阶段**：执行侧节点订阅对应 command topic 并驱动硬件或下游控制栈。

## 数据流图

```mermaid
flowchart LR
    A[_control_tick] -->|发布| B[command topic]
    B -->|订阅| C[executor/bridge]
```

## 具象隐喻

> [!tip] 生活场景类比
> 像工厂广播频道：中控室分别通知左臂、右臂和两只手该做什么。
