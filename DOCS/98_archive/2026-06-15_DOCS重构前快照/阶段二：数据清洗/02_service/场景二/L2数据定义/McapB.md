# McapB

## 定义

`McapB` 是场景二第 6 功能模块生成的诊断 MCAP，文档和人工讨论中也称为 `MCAP_B`。

## 所属位置

阶段二 Service 场景二，来源能力模块：[[IK 求解与 MCAP_B 生成器]]。

## 现实语义

它只保存左右 RM65 机械臂 IK 成功帧的关节角序列，用于关节限制检查、MuJoCo 仿真和问题标注，不作为训练主数据。

## 字段或取值

| 内容 | 契约 |
|---|---|
| 来源 | [[McapA]] 与 [[IkSolveSummary]] |
| 左臂 topic | 建议 `/rm65_left/joint_states` |
| 右臂 topic | 建议 `/rm65_right/joint_states` |
| 消息类型 | `sensor_msgs/msg/JointState` |
| 关节名 | `joint1` 到 `joint6` 或后续配置中稳定命名 |
| 角度单位 | JointState `position` 使用 rad，sidecar 中保留 deg 审计 |
| 时间戳 | 使用来源 TCP pose 时间戳 |
| 失败帧 | 不写消息，由 [[IkSolveSummary]] 记录 |
| 默认落点 | `asset/阶段二：数据清洗/dev/mcap_validated/` |
| 默认命名 | `<stem>_mcap_b.mcap` |

## 有效性规则

- 只写 IK 成功帧。
- 不写 NaN 关节角，不复制上一帧关节角。
- 不保存 pose、触觉、夹爪或训练主数据。
- 必须有同级或 run 内 [[IkSolveSummary]] 解释输入、输出、失败帧和统计。

## 上游来源

- [[McapA]]
- [[Rm65IkSampleResult]]
- [[Rm65IkConfig]]

## 下游消费者

- 关节限制检查器。
- MuJoCo 仿真验证器。
- Parquet 标注与验证报告生成器。

## 不负责

- 不替代 MCAP_A。
- 不保存完整 IK 审计。
- 不决定 mask、episode 丢弃或 canonical dataset 结构。

## 相关链接

- [[IkSolveSummary]]
- [[Rm65IkSampleResult]]

