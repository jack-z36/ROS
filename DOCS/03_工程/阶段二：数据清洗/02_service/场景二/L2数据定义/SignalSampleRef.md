# SignalSampleRef

> 消费对象：阶段二 Scene2 开发与验收 Agent。权威性：新运行产物的消息身份契约；与旧 run JSON 冲突时以本文和 `schemas/reliability.py` 为准。上游来源：Scene2 边界修复实现与合同测试。不负责：step/episode 身份。读取时机：修改 Scene2 检测、修复、滤波或 MCAP_A 写回前。冲突处理：停止按列表位置写回，优先修复稳定引用链路。

`SignalSampleRef` 同时表达信号排序时间和源 MCAP 物理消息身份。

| 字段 | 语义 |
|---|---|
| `topic` | 显式 Scene2 白名单中的来源 topic |
| `message_index` | 源 MCAP `log_time_order=False` 物理遍历中，该 topic 从 0 开始的序号；任何分析排序都不得重算 |
| `timestamp` / `time_domain` | 只用于同 stream 信号排序，支持 `log_time` / `publish_time` / `header_stamp` |
| `log_time_ns` / `publish_time_ns` / `sequence` / `source_channel_id` | 写回时校验源消息身份 |
| `modality` | `pose` / `gripper` / `tactile` |

定位先使用 `topic + message_index`，命中后必须校验其余 MCAP 身份字段和信号时间。相同时间戳或 sequence 重复时仍只能命中一个物理消息。`field_path` 属于 issue/disposition，不属于消息引用；同一引用的 `pose.position` 与 `pose.orientation` 可独立处置。
