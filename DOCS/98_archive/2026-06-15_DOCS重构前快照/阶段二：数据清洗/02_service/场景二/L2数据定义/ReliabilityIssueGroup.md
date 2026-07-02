# ReliabilityIssueGroup

## 定义

`ReliabilityIssueGroup` 是从样本级异常派生出来的连续问题摘要，用于开发者展示、报告和后续标注。

## 所属位置

阶段二 Service 场景二，来源能力模块：[[异常值检测器]]。

## 现实语义

它把相邻或同因的 [[SampleReliabilityIssue]] 聚合为一段摘要，方便人查看和报告系统消费。它不是补全器的权威处理单元。

## 字段或取值

| 字段 | 类型 | 现实含义 |
|---|---|---|
| `group_id` | string | 聚合摘要 id |
| `source_topic` | string | 来源 topic |
| `modality` | enum string | `pose` / `tactile` / `gripper` |
| `issue_type` | string | 聚合的问题类型 |
| `start_time` | integer/float | 组内最早样本时间 |
| `end_time` | integer/float | 组内最晚样本时间 |
| `time_domain` | enum string | 时间域 |
| `sample_issue_ids` | list[string] | 组内样本级问题 id |
| `sample_count` | integer | 组内样本级问题数量 |
| `summary` | string | 人可读摘要 |

## 有效性规则

- 必须能追溯到一个或多个 [[SampleReliabilityIssue]]。
- 如果与样本级记录冲突，以样本级记录为准。
- 数据补全器不得把本对象作为主输入做修复。

## 上游来源

- [[SampleReliabilityIssue]]
- 异常检测器的聚合摘要逻辑。

## 下游消费者

- 开发者功能检验输出。
- Parquet 标注与验证报告生成器。
- 人工复查。

## 不负责

- 不决定自动补全。
- 不承载修复后的值。
- 不表达无样本缺失区间。

## 相关链接

- [[SampleReliabilityIssue]]
- [[SignalReliabilityDetectionResult]]
