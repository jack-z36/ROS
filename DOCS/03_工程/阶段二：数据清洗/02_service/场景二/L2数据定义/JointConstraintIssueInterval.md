# JointConstraintIssueInterval

## 定义

`JointConstraintIssueInterval` 是关节限制检查器输出的问题时间段。

## 所属位置

阶段二 Service 场景二，来源能力模块：[[关节限制检查器]]。

## 现实语义

它表示某一侧机械臂在一段时间内存在 IK 失败、关节角超限、速度超限、加速度超限或 workspace 问题，应由下游 `annotations.parquet` 标注为硬问题。

## 字段或取值

| 字段 | 类型 | 现实含义 |
|---|---|---|
| `arm_side` | enum `left` / `right` | 左臂或右臂 |
| `start_time_ns` | int | 问题开始时间 |
| `end_time_ns` | int | 问题结束时间 |
| `issue_type` | enum string | `ik_failed` / `joint_position_limit` / `joint_velocity_limit` / `joint_acceleration_limit` / `workspace_radius_limit` / `workspace_no_go_zone` |
| `severity` | enum string | 首版固定 `hard` |
| `related_joints` | list[string] | 涉及关节名，可为空 |
| `evidence_refs` | list[[JointConstraintSampleEvidence]] | 样本级证据引用 |
| `suggested_mask` | string | 首版默认 `drop_or_mask` |
| `reason` | string | 人可读原因摘要 |

## 有效性规则

- `start_time_ns <= end_time_ns`。
- 区间必须由样本级证据或上游 `IkSolveSummary.failure_intervals` 聚合而来。
- 首版所有问题均按硬问题输出，不降级为仅人工复查。

## 上游来源

- [[McapB]]
- [[IkSolveSummary]]
- [[JointConstraintSampleEvidence]]

## 下游消费者

- Parquet 标注与验证报告生成器。
- 场景四 masks 和 robot constraint report。

## 不负责

- 不保存完整 JointState payload。
- 不决定最终 episode 是否删除。

## 相关链接

- [[JointConstraintConfig]]
- [[JointConstraintCheckResult]]

