---
tags: [program-principle, source-annotation]
analysis: pi05-runtime-train-bundle
node: N01
---

# N01 ROS2 部署节点编排

> [!abstract]
> 创建 collector、SharedBuffer、SafetyGuard、ControlLoop、policy runtime 和 InferenceWorker，并绑定 ROS2 subscription/publisher/timer。

| 属性 | 值 |
| --- | --- |
| 节点类型 | 流程编排类 |
| 源码实现 | `pi05_test/pi05/deploy/src/pi05/deploy/ros_nodes/pi05_vla_deploy_node.py:29-94` |
| 输入数据 | `DeployConfig` |
| 输出数据 | runtime 对象图 |

## 代码块解释

| 行号 | 作用 |
| --- | --- |
| 35-46 | 根据配置创建 image preprocess、collector、shared buffer、safety guard |
| 47-65 | 创建 `ControlLoop` 并注入队列、观测 provider、安全过滤器和频率参数 |
| 68-83 | 加载 bundle policy runtime，再启动后台 `InferenceWorker` |
| 85-89 | 创建 ROS2 订阅、发布器、timer，并启动推理线程 |

## 容易误解

它不是直接运行模型的地方；真正推理在 `InferenceWorker` 和 `Pi05PolicyRuntime` 中。

