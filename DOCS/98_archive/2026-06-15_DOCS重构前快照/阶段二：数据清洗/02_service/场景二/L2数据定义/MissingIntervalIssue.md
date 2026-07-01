# MissingIntervalIssue

## 定义

`MissingIntervalIssue` 是场景二异常检测器输出的缺失区间问题记录，用于表达某个 topic 在一段时间内没有样本可挂载。

## 所属位置

阶段二 Service 场景二，来源能力模块：[[异常值检测器]]。

## 现实语义

它表示“这段时间本应有消息，但实际没有消息”。因为没有已有样本点，v1 数据补全器不插入新消息，只把它记录为未处理缺失区间或后续 mask 候选。

## 字段或取值

| 字段 | 类型 | 现实含义 |
|---|---|---|
| `issue_id` | string | 缺失区间问题 id |
| `source_topic` | string | 缺失发生的 topic |
| `modality` | enum string | `pose` / `tactile` / `gripper` |
| `start_time` | integer/float | 缺失区间起始时间 |
| `end_time` | integer/float | 缺失区间结束时间 |
| `time_domain` | enum string | `log_time` / `publish_time` / `header_stamp` |
| `missing_sample_estimate` | integer/null | 估计缺失样本数 |
| `severity` | enum string | `info` / `warning` / `error` / `critical` |
| `suggested_action` | [[SuggestedRepairAction]] | 理论处理建议 |
| `reason` | string | 人可读原因摘要 |

## 有效性规则

- `end_time` 必须大于 `start_time`。
- `time_domain` 必须显式填写。
- 即使 `suggested_action` 是 `repairable_interpolate` 或 `repairable_hold`，v1 数据补全器也不得新增消息。
- 数据补全器寻找合法邻居时不得跨越未处理的 `MissingIntervalIssue`。

## 上游来源

- cleaned MCAP 消息时间序列。
- [[ReliabilityCheckRuleConfig]] 中的缺失段规则。

## 下游消费者

- [[SignalRepairResult]]
- Parquet 标注与验证报告生成器。
- 场景四 mask 与质量报告。

## 不负责

- 不定位已有异常样本；已有样本异常使用 [[SampleReliabilityIssue]]。
- 不定义重采样或插入消息策略。
- 不替代场景三时间轴对齐。

## 相关链接

- [[SignalReliabilityDetectionResult]]
- [[SuggestedRepairAction]]
- [[SignalRepairResult]]
