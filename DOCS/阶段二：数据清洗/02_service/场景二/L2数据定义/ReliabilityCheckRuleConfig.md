# ReliabilityCheckRuleConfig

## 定义

`ReliabilityCheckRuleConfig` 是场景二 P0 预处理链路中异常检测规则和阈值的配置概念。

## 所属位置

阶段二 Service 场景二，首个消费能力模块：[[异常值检测器]]。

## 现实语义

它承载位姿、触觉和夹爪异常检测所需的阈值、开关和策略，使规则可以通过配置调参，而不是写死在实现里。

## 字段或取值

| 配置块 | 字段 | 现实含义 |
|---|---|---|
| `common` | `max_gap_sec` | 判定缺失段的最大采样间隔 |
| `common` | `duplicate_time_policy` | 重复时间戳处理策略 |
| `pose` | `max_position_jump_m` | 位姿位置跳变阈值 |
| `pose` | `max_linear_velocity_mps` | 线速度异常阈值 |
| `pose` | `max_linear_accel_mps2` | 加速度异常阈值 |
| `pose` | `quat_norm_tolerance` | 四元数归一性容忍度 |
| `tactile` | `expected_rows` / `expected_cols` | 触觉矩阵预期尺寸 |
| `tactile` | `spike_delta_threshold` | 单帧尖峰阈值 |
| `tactile` | `saturation_ratio_threshold` | 大面积饱和判定比例 |
| `tactile` | `zero_ratio_threshold` | 大面积全零判定比例 |
| `gripper` | `min_value` / `max_value` | 归一化夹爪宽度值域 |
| `gripper` | `max_width_jump` | 夹爪宽度跳变阈值 |
| `gripper` | `stuck_duration_sec` | 长时间不变化判定阈值 |

## 有效性规则

- 所有启用的数值阈值必须为有限数。
- 触觉默认矩阵尺寸可参考 `6x15`，但必须允许配置覆盖。
- 规则配置缺失时，功能检验应失败或进入 `inspect_required`，不得静默使用不可追溯默认值。

## 上游来源

- 场景二生产配置或开发者入口临时覆盖。
- 真实数据调参结论。

## 下游消费者

- [[异常值检测器]]
- 后续补全器和滤波器可复用其中的时间间隔、不可修复片段和阈值策略。

## 不负责

- 不负责保存检测结果。
- 不负责定义 MCAP_A 写出路径。
- 不负责 IK、关节限制或 MuJoCo 配置。

## 当前未知问题

| 问题 | 当前处理 |
|---|---|
| 各阈值的生产默认值 | L2 先定义配置槽位，具体默认值由后续 L3 结合样例数据确定 |
| 配置文件正式路径 | 待 Runtime/run 目录和场景二配置体系接入时固化 |

## 相关链接

- [[SignalReliabilityIssue]]
- [[SuggestedRepairAction]]
- [[TactilePressureFrame]]

