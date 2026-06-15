# ROS 话题与命名模型

阶段一通过 ROS2 topic 连接各个传感器和 Octopus。topic 命名、namespace、frame_id 和消息类型会影响后续录制、清洗和训练数据构建。

## 核心概念

- topic 是 Octopus 发现和录制数据的基本入口。
- namespace 用于区分左右设备、不同模态或不同节点实例。
- frame_id 表示消息所属坐标或传感器框架。
- 消息类型决定后续解析和转换方式。

## 稳定性边界

设备路径如 `/dev/videoX`、`/dev/ttyUSBX` 不应被理解为稳定身份。稳定身份策略属于约束或工程实现，不写入本知识页作为执行规则。
