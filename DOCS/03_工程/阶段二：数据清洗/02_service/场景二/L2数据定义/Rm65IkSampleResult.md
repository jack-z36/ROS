# Rm65IkSampleResult

## 定义

`Rm65IkSampleResult` 是对一个 `RobotBaseTcpPose` 样本调用睿尔曼 RM65 IK 后得到的逐样本诊断结果。

## 所属位置

阶段二 Service 场景二，来源能力模块：[[IK 求解与 MCAP_B 生成器]]。

## 现实语义

它记录某一时刻、某一侧机械臂的 IK 是否成功、使用了哪个 seed、成功时得到哪些关节角、失败时为什么失败。

## 字段或取值

| 字段 | 类型 | 现实含义 |
|---|---|---|
| `arm_side` | enum `left` / `right` | 左臂或右臂 |
| `source_pose_ref` | [[RobotBaseTcpPose]] | 输入 base-frame TCP pose 引用 |
| `timestamp_ns` | int | 来源 pose 时间戳 |
| `status` | enum string | `success` / `failed` / `invalid_input` / `sdk_error` |
| `failure_reason` | string/null | 失败原因，成功时为空 |
| `seed_joint_deg` | float[6] | 本次传给 SDK 的 `q_in`，单位 deg |
| `joint_deg` | float[6]/null | 成功求解出的关节角，单位 deg |
| `sdk_return_code` | int/null | 睿尔曼 SDK 返回码 |
| `output_topic` | string/null | 成功时写入 MCAP_B 的 JointState topic |
| `message_written` | bool | 本样本是否写入 MCAP_B |

## 有效性规则

- 成功时 `joint_deg` 必须存在且长度为 6。
- 失败时 `joint_deg` 必须为空，`message_written=false`。
- 失败样本不得写 NaN 关节角，不得复制上一帧关节角。
- 失败样本不得推进下一帧 seed。

## 上游来源

- [[RobotBaseTcpPose]]
- [[Rm65IkConfig]]
- 睿尔曼 Python SDK `Algo`。

## 下游消费者

- [[McapB]]
- [[IkSolveSummary]]
- 关节限制检查器。
- Parquet 标注与验证报告生成器。

## 不负责

- 不表达关节速度或加速度。
- 不表达 MuJoCo 碰撞或力矩。
- 不决定是否丢弃 episode。

## 相关链接

- [[RobotBaseTcpPose]]
- [[Rm65IkConfig]]
- [[McapB]]
- [[IkSolveSummary]]

