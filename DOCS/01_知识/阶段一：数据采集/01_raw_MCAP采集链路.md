# raw MCAP 采集链路

raw MCAP 是阶段一的核心数据产物。它保存 Octopus 录制到的 ROS2 topic 日志，是后续阶段二清洗、对齐和训练格式桥接的输入。

## 数据流

```text
传感器节点
  -> ROS2 topic
  -> Octopus recording
  -> raw MCAP
```

raw MCAP 保留传感器原始消息、topic 名称、时间戳和 schema。它不保证不同 topic 已经对齐，也不保证数据已经满足训练输入语义。

## 与阶段二关系

阶段二读取 raw MCAP 后，逐步生成 cleaned MCAP、MCAP_A、aligned MCAP 和训练格式桥接产物。阶段一不得提前把阶段二的清洗、滤波、对齐或 action 语义混入采集层。

## 判断标准

- 能通过 Octopus 录制得到 `.mcap` 文件。
- MCAP 内包含目标传感器 topic。
- topic 数据能被后续解析或回放。
