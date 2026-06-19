---
tags:
  - term-explainer
  - pi05
  - data-definition
source: [[部署推理数据流框架|部署推理数据流框架]]
---

# Pi05VlaDeployNode

> [!abstract] 核心定义
> Pi0.5 VLA 部署端 ROS2 主节点，组装订阅、观测缓冲、推理线程、控制循环和命令发布。

## 数据结构

| 字段名 | 类型 | 含义 | 是否必填 |
|--------|------|------|----------|
| `collector` | ObservationCollector | 聚合传感器观测 | 是 |
| `shared_buffer` | SharedBuffer | 线程间共享观测和动作块 | 是 |
| `inference_worker` | InferenceWorker | 后台推理线程 | 是 |
| `control_loop` | ControlLoop | 高频控制调度 | 是 |

> [!info] 结构说明
> 它是 deploy runtime 的组装根节点，不是单一数值函数。

## 具体数值示例

> [!example]- 点击展开具体数据实例
> ```json
>
> {
>   "node": "pi05_vla_deploy_node",
>   "collector": "ObservationCollector",
>   "worker": "InferenceWorker",
>   "loop": "ControlLoop"
> }
> ```
>
> 该示例展示该术语在 [[部署推理数据流框架|部署推理数据流框架]] 中承担的数据契约角色。

## 具象隐喻

> [!tip] 生活场景类比
> 像机器人乐队指挥：一边听各种传感器，一边协调模型、安全和执行器。
