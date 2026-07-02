# TactileFilterConfig

## 定义

`TactileFilterConfig` 是触觉滤波器一次运行使用的配置对象，定义逐 cell 时间滤波的算法、默认参数、接触变化边界和调试输出开关。

## 所属位置

阶段二 Service 场景二，来源能力模块：[[触觉滤波器]]。

## 现实语义

它回答“触觉压力矩阵如何被平滑、哪些变化不允许跨越平滑、开发者调试时是否输出完整矩阵 diff”。

## 字段或取值

| 字段 | 类型 | 现实含义 |
|---|---|---|
| `algorithm` | enum string | v1 固定为 `median_ema` |
| `median_window` | integer | 逐 cell 短窗口中值滤波窗口，默认 `3` |
| `ema_alpha` | number | EMA 权重，默认 `0.35` |
| `contact_reset_threshold` | number/null | 判断真实接触变化并重置 EMA 的帧级变化阈值 |
| `contact_reset_metric` | enum string | 接触变化判定指标，默认 `mean_abs_delta` |
| `preserve_shape` | boolean | 固定 `true` |
| `timestamp_policy` | enum string | 固定 `preserve_original` |
| `emit_full_diff_in_dev` | boolean | 开发者调试模式是否输出完整矩阵 diff |

## 有效性规则

- `algorithm` v1 只允许 `median_ema`。
- `median_window` 必须是大于等于 3 的奇数。
- `ema_alpha` 必须在 `(0, 1]` 范围内。
- `contact_reset_threshold` 在生产默认值未确认前必须允许配置覆盖；L3 测试可使用固定保守阈值。
- `timestamp_policy` 必须为 `preserve_original`。
- 本配置不得启用空间卷积、重采样或 shape 改写。

## 上游来源

- 开发者入口临时覆盖配置。
- 后续场景二生产配置。
- [[触觉滤波器]] 默认配置。

## 下游消费者

- [[TactileFilterInputSequence]]
- [[TactileFilterSegmentSummary]]
- [[TactileFilterResult]]
- 开发者功能检验项 `scene2_tactile_filter`

## 不负责

- 不定义触觉异常检测阈值；异常检测由 [[ReliabilityCheckRuleConfig]] 负责。
- 不定义补全策略；补全由 [[SignalRepairPolicyConfig]] 负责。
- 不决定训练 mask 或 episode 丢弃。

## 当前未知问题

| 问题 | 当前处理 |
|---|---|
| 生产级 `contact_reset_threshold` | 先保留配置槽位，真实数据调参后固化 |
| 不同触觉 topic 是否需要独立参数 | v1 使用统一默认参数，保留后续扩展 |

## 相关链接

- [[触觉滤波器]]
- [[TactileFilterResult]]
- [[SignalRepairResult]]
