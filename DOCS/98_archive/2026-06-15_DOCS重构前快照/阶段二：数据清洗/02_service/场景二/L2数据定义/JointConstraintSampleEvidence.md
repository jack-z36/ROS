# JointConstraintSampleEvidence

## 定义

`JointConstraintSampleEvidence` 是关节限制检查器为单个时间点或相邻样本对记录的违规证据。

## 所属位置

阶段二 Service 场景二，来源能力模块：[[关节限制检查器]]。

## 现实语义

它回答“是哪一侧、哪个时间点、哪个关节或 TCP 位姿触发了什么限制，以及实际值和阈值是多少”。

## 字段或取值

| 字段 | 类型 | 现实含义 |
|---|---|---|
| `arm_side` | enum `left` / `right` | 左臂或右臂 |
| `timestamp_ns` | int | 证据时间戳 |
| `source` | enum string | `mcap_b` / `ik_solve_summary` / `robot_base_tcp_pose` |
| `issue_type` | enum string | 违规类型 |
| `joint_name` | string/null | 涉及关节，workspace 问题可为空 |
| `actual_value` | float/null | 实际值 |
| `threshold_value` | float/null | 阈值 |
| `unit` | string | `deg` / `deg/s` / `deg/s^2` / `mm` |
| `sdk_return_code` | int/null | 睿尔曼 SDK 限位函数返回码 |
| `reason` | string | 稳定 reason |

## 有效性规则

- 如果 `issue_type` 是关节类问题，必须有 `joint_name`、`actual_value`、`threshold_value` 和 `unit`。
- 如果来源是 SDK 限位函数，必须保留 `sdk_return_code`。
- 证据只保存诊断值，不嵌入完整 MCAP 消息。

## 上游来源

- [[McapB]]
- [[IkSolveSummary]]
- [[RobotBaseTcpPose]]
- [[JointConstraintConfig]]

## 下游消费者

- [[JointConstraintIssueInterval]]
- [[JointConstraintCheckResult]]
- 开发者功能检验项 `scene2_joint_constraint_check`。

## 不负责

- 不作为下游标注表的最终行结构。
- 不保存 MuJoCo 碰撞或力矩证据。

## 相关链接

- [[JointConstraintIssueInterval]]
- [[JointConstraintCheckResult]]

