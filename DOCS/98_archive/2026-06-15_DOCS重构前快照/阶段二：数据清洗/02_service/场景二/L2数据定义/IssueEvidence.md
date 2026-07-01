# IssueEvidence

## 定义

`IssueEvidence` 是支撑 [[SignalReliabilityIssue]] 的点级或统计证据摘要。

## 所属位置

阶段二 Service 场景二，来源能力模块：[[异常值检测器]]。

## 现实语义

它回答“为什么这个时间段被判定为异常”，用于自动化测试、人工复查和后续报告展示。它服务于解释，不作为下游处理的主索引。

## 字段或取值

| 字段 | 类型 | 现实含义 |
|---|---|---|
| `evidence_type` | enum string | `sample` / `statistic` / `rule` |
| `sample_time` | integer/float/null | 触发异常的样本时间 |
| `metric` | string | 触发指标，例如 `position_delta`、`matrix_max`、`nan_count` |
| `value` | number/string/list/null | 实际观测值 |
| `threshold` | number/string/list/null | 触发阈值或规则名 |
| `summary` | string | 人可读证据摘要 |

## 有效性规则

- 每条证据必须说明 `evidence_type` 和 `summary`。
- 如果证据来自具体样本，应填写 `sample_time`。
- 证据可以被截断摘要化；不得要求报告保存全部原始序列。

## 上游来源

- [[ReliabilityCheckRuleConfig]]
- cleaned MCAP 中的位姿、触觉和夹爪样本。

## 下游消费者

- Parquet 标注与验证报告生成器。
- 开发者功能检验输出。
- 人工复查。

## 不负责

- 不负责定义主问题时间段。
- 不负责给出修复策略。
- 不负责保存完整原始 payload。

## 当前未知问题

| 问题 | 当前处理 |
|---|---|
| 每条问题最多保留多少 evidence | v1 由实现配置限制，避免报告过大 |

## 相关链接

- [[SignalReliabilityIssue]]
- [[IssueTimeSegment]]

