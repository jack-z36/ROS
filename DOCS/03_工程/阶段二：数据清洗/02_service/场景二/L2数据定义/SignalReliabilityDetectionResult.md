# SignalReliabilityDetectionResult

## 定义

`SignalReliabilityDetectionResult` 是异常值检测器一次运行的聚合输出对象。

## 所属位置

阶段二 Service 场景二，来源能力模块：[[异常值检测器]]。

## 现实语义

它回答“这次 cleaned MCAP 可靠性检测发现了哪些样本级异常、哪些缺失区间、有哪些展示用问题组，以及使用了哪份规则配置”。

## 字段或取值

| 字段 | 类型 | 现实含义 |
|---|---|---|
| `input_cleaned_mcap` | string | 输入 cleaned MCAP 路径或引用 |
| `rule_config_ref` | string / [[ReliabilityCheckRuleConfig]] | 本次使用的检测规则配置引用 |
| `sample_issues` | list[[SampleReliabilityIssue]] | 已有样本点异常列表 |
| `missing_interval_issues` | list[[MissingIntervalIssue]] | 无样本缺失区间列表 |
| `issue_groups` | list[[ReliabilityIssueGroup]] | 可选展示/报告聚合摘要 |
| `summary_by_modality` | object | 按 `pose` / `tactile` / `gripper` 汇总的问题统计 |
| `created_at` | string/null | 结果创建时间 |
| `run_id` | string/null | 所属 run id |

## 有效性规则

- `sample_issues`、`missing_interval_issues` 和 `issue_groups` 可为空但字段必须存在。
- `issue_groups` 只能引用已存在的 `sample_issues`。
- `rule_config_ref` 必须可追溯，不能只写“默认配置”。
- 输出对象不得包含修复后的值。

## 上游来源

- [[CleanedMcap]]
- [[ReliabilityCheckRuleConfig]]
- [[异常值检测器]]

## 下游消费者

- 数据补全器。
- 位姿滤波器和触觉滤波器。
- Parquet 标注与验证报告生成器。
- 开发者功能检验项 `scene2_signal_reliability_detect`。

## 不负责

- 不负责修复或滤波。
- 不负责写 MCAP_A。
- 不负责定义最终 mask。

## 相关链接

- [[SampleReliabilityIssue]]
- [[MissingIntervalIssue]]
- [[ReliabilityIssueGroup]]
- [[SignalRepairResult]]
