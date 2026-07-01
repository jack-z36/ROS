# JointConstraintCheckResult

## 定义

`JointConstraintCheckResult` 是关节限制检查器一次运行的聚合结果。

## 所属位置

阶段二 Service 场景二，来源能力模块：[[关节限制检查器]]。

## 现实语义

它汇总本次读取哪个 MCAP_B 和 IkSolveSummary、使用哪些约束阈值、发现哪些样本证据和问题时间段。

## 字段或取值

| 字段 | 类型 | 现实含义 |
|---|---|---|
| `input_mcap_b` | string / [[McapB]] | 来源 MCAP_B |
| `input_ik_solve_summary` | string / [[IkSolveSummary]] | 来源 IK sidecar |
| `constraint_config_ref` | string / [[JointConstraintConfig]] | 本次约束配置 |
| `continuous_success_segments` | list[object] | 连续 IK 成功片段摘要 |
| `sample_evidence` | list[[JointConstraintSampleEvidence]] | 样本级证据 |
| `issue_intervals` | list[[JointConstraintIssueInterval]] | 下游消费的问题时间段 |
| `summary_by_issue_type` | object | 按问题类型统计 |
| `status` | enum `completed` / `failed` | 检查状态 |
| `failure_reason` | string/null | 整体失败原因 |

## 有效性规则

- `issue_intervals` 必须能追溯到 `sample_evidence` 或 `IkSolveSummary.failure_intervals`。
- 读取 MCAP_B 但缺少 IkSolveSummary 时必须失败，因为 IK 失败帧不会写入 MCAP_B。
- 所有输出时间戳必须位于 MCAP_B / IkSolveSummary 的输入时间域内。

## 上游来源

- [[McapB]]
- [[IkSolveSummary]]
- [[JointConstraintConfig]]

## 下游消费者

- Parquet 标注与验证报告生成器。
- 开发者功能检验项 `scene2_joint_constraint_check`。
- 场景四 masks 和 robot constraint report。

## 不负责

- 不修改 MCAP_A 或 MCAP_B。
- 不执行 MuJoCo 仿真。
- 不决定训练 mask 的最终落点。

## 相关链接

- [[JointConstraintConfig]]
- [[JointConstraintIssueInterval]]
- [[JointConstraintSampleEvidence]]

