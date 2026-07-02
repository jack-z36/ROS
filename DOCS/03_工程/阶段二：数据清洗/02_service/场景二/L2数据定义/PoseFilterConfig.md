# PoseFilterConfig

## 定义

`PoseFilterConfig` 是场景二位姿滤波器的参数配置对象，用于控制补全后 pose 序列的平滑算法、时间窗口换算、短片段策略和过度平滑 guard。

## 所属位置

阶段二 Service 场景二，来源能力模块：[[位姿滤波器]]。

## 现实语义

它回答“本次位姿滤波用什么算法、窗口多大、姿态如何处理、什么时候拒绝滤波结果”。它只描述滤波参数，不承载输入序列或滤波结果。

## 字段或取值

| 字段 | 类型 | 现实含义 |
|---|---|---|
| `algorithm` | enum string | 固定首版默认 `savgol` |
| `window_duration_ms` | number | 对外配置的时间窗口，默认 `200` |
| `polyorder` | integer | Savitzky-Golay 多项式阶数，默认 `2` |
| `time_window_conversion` | enum string | 固定首版默认 `median_dt_to_odd_samples` |
| `short_segment_policy` | enum string | 固定首版默认 `adaptive_window_then_keep_original` |
| `position_guard_max_delta_m` | number | 位置滤波前后最大允许差异，默认 `0.02` |
| `orientation_guard_max_delta_deg` | number | 姿态滤波前后最大允许角度差，默认 `5` |
| `orientation_filter_space` | enum string | 固定首版默认 `continuous_quaternion_to_rotvec` |
| `segment_boundary_policy` | enum string | 固定首版默认 `missing_or_unrepaired_pose_breaks_segment` |

## 有效性规则

- `algorithm` 首版只允许 `savgol`。
- `window_duration_ms` 必须为有限正数。
- `polyorder` 必须为非负整数，且实际样本窗口必须大于 `polyorder`。
- 时间窗口换算不得改变原始时间戳、排序或样本数量。
- guard 阈值必须为有限非负数；超过阈值的样本不得采用滤波值。
- 姿态输出四元数必须归一化。

## 上游来源

- 场景二生产配置或开发者入口临时覆盖。
- [[数据补全器]] 输出的 [[SignalRepairResult]]。
- 真实样本调参结论。

## 下游消费者

- [[位姿滤波器]]。
- [[PoseFilterResult]]。
- 开发者功能检验项 `scene2_pose_filter`。

## 不负责

- 不定义异常检测阈值。
- 不定义数据补全策略。
- 不定义 MCAP_A 写出路径。
- 不负责 IK、关节限制或 MuJoCo 配置。

## 当前未知问题

| 问题 | 当前处理 |
|---|---|
| 生产默认参数是否需要按不同 topic 或左右臂拆分 | v1 使用统一默认参数，后续可扩展 topic 级覆盖 |
| 是否需要 Butterworth 或移动窗口 fallback | v1 不做，保留为后续配置扩展 |

## 相关链接

- [[PoseFilterInputSequence]]
- [[PoseFilterSampleRecord]]
- [[PoseFilterResult]]
- [[SignalRepairResult]]
