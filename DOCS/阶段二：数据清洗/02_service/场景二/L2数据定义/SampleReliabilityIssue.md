# SampleReliabilityIssue

## 定义

`SampleReliabilityIssue` 是场景二异常检测器输出的样本级可靠性问题记录，用于表达某个已有样本点存在异常。

## 所属位置

阶段二 Service 场景二，来源能力模块：[[异常值检测器]]。

## 现实语义

它不是被修改后的数据，而是“某个 cleaned MCAP 已有消息样本存在可靠性问题”的结构化判断。数据补全器以它作为主输入，并按同 topic、同样本聚合后决定是否修复。

## 字段或取值

| 字段 | 类型 | 现实含义 |
|---|---|---|
| `issue_id` | string | 单条样本级问题记录 id |
| `sample_ref` | [[SignalSampleRef]] | 异常样本定位 |
| `issue_type` | enum string | 异常类型 |
| `severity` | enum string | `info` / `warning` / `error` / `critical` |
| `suggested_action` | [[SuggestedRepairAction]] | 对该样本的处理建议 |
| `reason` | string | 人可读原因摘要 |
| `evidence` | list[[IssueEvidence]] | 点级或统计证据 |

## 有效性规则

- `sample_ref`、`issue_type`、`severity`、`suggested_action` 必填。
- `suggested_action` 是建议，不代表异常检测器已经修改数据。
- 同一样本允许存在多条不同 `field_path` 或 `issue_type` 的记录。
- 数据补全器必须先按 `source_topic + time_domain + timestamp + message_index + modality` 聚合同一样本问题，再做一次修复决策。

## 上游来源

- [[CleanedMcap]]
- [[CommonFrameTcpPose]]
- [[GripperWidthSample]]
- [[TactilePressureFrame]]
- [[ReliabilityCheckRuleConfig]]

## 下游消费者

- [[SignalRepairResult]]
- 位姿滤波器和触觉滤波器。
- Parquet 标注与验证报告生成器。

## 不负责

- 不承载无样本缺失段；缺失段使用 [[MissingIntervalIssue]]。
- 不直接承载修复后的值。
- 不决定最终 episode 丢弃或训练 mask。

## 相关链接

- [[SignalSampleRef]]
- [[IssueEvidence]]
- [[SuggestedRepairAction]]
- [[SignalReliabilityDetectionResult]]
