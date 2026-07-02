# SignalSampleRef

## 定义

`SignalSampleRef` 是场景二用于稳定定位 cleaned MCAP 中某个已有消息样本的引用对象。

## 所属位置

阶段二 Service 场景二，来源能力模块：[[异常值检测器]]。

## 现实语义

它回答“哪一个 topic 的哪一条消息有问题”。异常检测器用它定位已有样本异常；数据补全器用它在原始时间戳结构不变的前提下替换样本值。

## 字段或取值

| 字段 | 类型 | 现实含义 |
|---|---|---|
| `source_topic` | string | 来源 MCAP topic |
| `modality` | enum string | `pose` / `tactile` / `gripper` |
| `time_domain` | enum string | `log_time` / `publish_time` / `header_stamp` |
| `timestamp` | integer/float | 当前样本在 `time_domain` 下的时间 |
| `message_index` | integer | 同一 `source_topic` 内从 0 开始的消息序号 |
| `field_path` | string/null | 异常字段路径，例如 `pose.position`、`pose.orientation`、`tactile.frame`、`gripper.value` |

## 有效性规则

- `source_topic`、`modality`、`time_domain`、`timestamp` 和 `message_index` 必填。
- `message_index` 必须在同一 topic 内稳定定位，不能跨 topic 复用。
- `field_path` 只说明异常发生字段，不代表补全器必须按字段级替换。
- 同一 `source_topic + message_index + modality` 可对应多个不同 `field_path` 的异常。

## 上游来源

- cleaned MCAP 消息序列。
- [[异常值检测器]] 的逐 topic 遍历逻辑。

## 下游消费者

- [[SampleReliabilityIssue]]
- [[SignalRepairRun]]
- [[SignalRepairSampleRecord]]

## 不负责

- 不表达异常类型或严重程度。
- 不表达缺失区间，因为缺失区间没有样本可引用。
- 不定义最终 episode 或 step index。

## 相关链接

- [[SampleReliabilityIssue]]
- [[MissingIntervalIssue]]
- [[SignalRepairResult]]
