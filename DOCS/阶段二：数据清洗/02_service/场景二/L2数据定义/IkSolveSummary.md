# IkSolveSummary

## 定义

`IkSolveSummary` 是 IK 求解与 MCAP_B 生成器一次运行的 sidecar JSON 摘要对象。

## 所属位置

阶段二 Service 场景二，来源能力模块：[[IK 求解与 MCAP_B 生成器]]。

## 现实语义

它回答“这次从哪个 MCAP_A 读取 TCP pose、用了哪些 common->base 外参和 RM65 IK 配置、哪些样本求解成功、哪些样本失败、MCAP_B 写了哪些消息”。

## 字段或取值

| 字段 | 类型 | 现实含义 |
|---|---|---|
| `input_mcap_a` | string / [[McapA]] | 来源 MCAP_A |
| `output_mcap_b` | string / [[McapB]] | 输出 MCAP_B |
| `ik_config_ref` | string / [[Rm65IkConfig]] | 本次 IK 配置引用 |
| `common_to_base_transform_ref` | string / [[CommonToRobotBaseTransform]] | 本次坐标转换外参引用 |
| `sdk_source` | string | SDK 来源和版本信息 |
| `sample_records` | list[[Rm65IkSampleResult]] | 覆盖每个输入 pose 的逐样本结果 |
| `failure_intervals` | list | 按左右臂聚合的 IK 失败时间段 |
| `written_topic_stats` | object | 左右 JointState 写出统计 |
| `status` | enum string | `completed` / `failed` |
| `failure_reason` | string/null | 整体失败原因 |
| `run_id` | string/null | 所属 run id |

## 有效性规则

- `sample_records` 必须覆盖每个输入 TCP pose 样本。
- 失败样本必须有 `failure_reason`。
- `failure_intervals` 只能由失败样本聚合而来。
- 成功时 `output_mcap_b` 必须存在；整体失败时不得留下误导性完整 MCAP_B。
- 不嵌入完整 MCAP 消息 payload。

## 上游来源

- [[McapA]]
- [[CommonToRobotBaseTransform]]
- [[Rm65IkConfig]]
- [[Rm65IkSampleResult]]

## 下游消费者

- 关节限制检查器。
- MuJoCo 仿真验证器。
- Parquet 标注与验证报告生成器。
- 开发者功能检验项 `scene2_ik_mcap_b_writer`。

## 不负责

- 不保存训练 mask。
- 不替代 MCAP_B 中的 JointState 序列。
- 不执行关节速度、加速度或碰撞检查。

## 相关链接

- [[McapB]]
- [[Rm65IkSampleResult]]
- [[Rm65IkConfig]]

