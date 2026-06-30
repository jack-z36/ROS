# SignalRepairPolicyConfig

## 定义

`SignalRepairPolicyConfig` 是数据补全器的修复策略配置对象。

## 所属位置

阶段二 Service 场景二，来源能力模块：[[数据补全器]]。

## 现实语义

它承载“什么情况下允许自动修复、用什么方法修、哪些情况必须拒绝”的策略。它与 [[ReliabilityCheckRuleConfig]] 解耦，后者只负责异常检测规则。

## 字段或取值

| 配置块 | 字段 | 现实含义 |
|---|---|---|
| `pose` | `default_max_interpolate_gap_sec` / `default_max_hold_gap_sec` | pose 默认 gap 上限 |
| `pose.position` | `max_interpolate_gap_sec` / `max_hold_gap_sec` | position 替换单位 gap 上限 |
| `pose.orientation` | `max_interpolate_gap_sec` / `max_hold_gap_sec` | orientation 替换单位 gap 上限 |
| `pose.orientation` | `method` | 固定为 `slerp` |
| `tactile.frame` | `max_interpolate_gap_sec` / `max_hold_gap_sec` | 触觉整帧替换 gap 上限 |
| `tactile.frame` | `allow_full_frame_interpolate` | 是否允许整帧逐元素插值 |
| `tactile.frame` | `debug_diff_artifact_enabled` | 是否输出完整矩阵 diff artifact |
| `gripper.value` | `max_interpolate_gap_sec` / `max_hold_gap_sec` | 夹爪替换 gap 上限 |
| `gripper.value` | `clamp_min` / `clamp_max` | 修复后值域，默认 `[0, 1]` |
| `fallback` | `allow_interpolate_to_hold_fallback` | 是否允许插值失败时降级 hold |
| `run_grouping` | `max_run_gap_sec_by_modality` | repair run 聚合时允许的最大相邻间隔 |

## 有效性规则

- 所有启用的 gap 上限必须为有限非负数。
- 替换单位级配置优先于模态默认配置。
- `repairable_hold` 不得通过配置升级为插值。
- 同一 pose run 中 position 或 orientation 任一替换单位不满足策略，整个 pose run 必须拒绝自动修复。
- 默认建议关闭 `allow_interpolate_to_hold_fallback`，由开发者显式打开。

## 上游来源

- 场景二生产配置或开发者入口临时覆盖。
- 真实数据调参结论。

## 下游消费者

- [[数据补全器]]
- [[SignalRepairResult]]
- 开发者功能检验项 `scene2_signal_repair`。

## 不负责

- 不定义异常检测阈值。
- 不定义 MCAP_A 写出路径。
- 不负责 IK、关节限制或 MuJoCo 配置。

## 当前未知问题

| 问题 | 当前处理 |
|---|---|
| 各 gap 的生产默认值 | L2 只定义配置槽位，后续 L3 结合样例数据设置保守默认 |
| 配置文件正式路径 | 待 Runtime/run 目录和场景二配置体系接入时固化 |

## 相关链接

- [[RepairMethod]]
- [[SignalRepairResult]]
- [[ReliabilityCheckRuleConfig]]
