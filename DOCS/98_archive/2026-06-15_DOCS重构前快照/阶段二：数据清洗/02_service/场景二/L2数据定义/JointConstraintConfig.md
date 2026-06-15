# JointConstraintConfig

## 定义

`JointConstraintConfig` 是场景二关节限制检查器使用的 RM65/R65M 4代 6DOF 机器人约束配置。

## 所属位置

阶段二 Service 场景二，来源能力模块：[[关节限制检查器]]。

## 现实语义

它把官网核实后的关节角、最大角速度、工作半径和可配置加速度阈值落成机器可读配置，使 L3 执行端不需要再访问官网。

## 字段或取值

| 字段 | 类型 | 默认值 / 来源 | 现实含义 |
|---|---|---|---|
| `robot_model_label` | string | `R65M 4代 6DOF` | 用户实际机械臂型号标签 |
| `sdk_arm_model` | string | `RM_MODEL_RM_65_E` | 睿尔曼 Python SDK `Algo` 机械臂枚举 |
| `sdk_force_type` | string | `RM_MODEL_RM_B_E` | 标准版 force type 默认值 |
| `joint_min_deg` | float[6] | `[-178, -130, -135, -178, -128, -360]` | 关节最小角度，单位 deg |
| `joint_max_deg` | float[6] | `[178, 130, 135, 178, 128, 360]` | 关节最大角度，单位 deg |
| `joint_max_velocity_deg_s` | float[6] | `[180, 180, 225, 225, 225, 225]` | 各关节最大角速度，单位 deg/s |
| `joint_max_acceleration_deg_s2` | float[6] | 必须由配置或 SDK/API 查询结果提供 | 各关节最大角加速度，单位 deg/s^2 |
| `workspace_radius_mm` | float | `610` | 标准版工作半径，单位 mm |
| `large_gap_ms` | float | 配置提供 | 连续成功片段最大允许相邻时间差 |
| `hard_issue_suggested_mask` | string | `drop_or_mask` | 关节限制问题的默认 mask 建议 |
| `threshold_source_refs` | list[string] | 官方 URL / 本地摘录路径 | 阈值来源引用 |

## 有效性规则

- 角度、速度、工作半径默认值来自官网 RM65 系列参数页，执行 L3 不需要再次联网查询。
- `joint_max_acceleration_deg_s2` 不得写死为不可覆盖常量；缺少配置或 SDK/API 查询结果时，涉及加速度检查的任务必须 strict 失败或跳过并写明原因。
- 所有关节数组长度必须为 6。
- 角度单位统一为 deg，速度单位统一为 deg/s，加速度单位统一为 deg/s^2，MCAP_B 中 rad 输入必须先转换。

## 上游来源

- [RM65 Series Parameters and D-H Model](https://develop.realman-robotics.com/en/robot4th/robotParameter/RM65OntologyParameters/)
- [Python Algorithm Interface Configuration algo](https://develop.realman-robotics.com/en/robot4th/apipython/classes/algo/)
- [Python Joint Configuration Query](https://develop.realman-robotics.com/en/robot4th/apipython/classes/jointsConfigQuery/)

## 下游消费者

- [[JointConstraintCheckResult]]
- [[JointConstraintIssueInterval]]
- 关节限制检查器 L3。

## 不负责

- 不保存真实机械臂 IP、账号或在线连接状态。
- 不定义 MuJoCo 模型。
- 不决定 canonical dataset 的最终 episode 丢弃策略。

## 相关链接

- [[McapB]]
- [[IkSolveSummary]]
- [[JointConstraintCheckResult]]

