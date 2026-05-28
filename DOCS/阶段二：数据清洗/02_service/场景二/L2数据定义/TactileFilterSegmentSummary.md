# TactileFilterSegmentSummary

## 定义

`TactileFilterSegmentSummary` 是触觉滤波器对一个连续可靠触觉片段的窗口、边界和统计摘要。

## 所属位置

阶段二 Service 场景二，来源能力模块：[[触觉滤波器]]。

## 现实语义

它表达“这一段触觉样本为什么可以一起滤波、在哪里因为缺失、未修复样本或真实接触变化被切开或重置”。

## 字段或取值

| 字段 | 类型 | 现实含义 |
|---|---|---|
| `segment_id` | string | 片段 id |
| `source_topic` | string | 来源触觉 topic |
| `start_sample_ref` | [[SignalSampleRef]] | 片段起始样本 |
| `end_sample_ref` | [[SignalSampleRef]] | 片段结束样本 |
| `sample_count` | integer | 片段样本数 |
| `rows` | integer | 触觉矩阵行数 |
| `cols` | integer | 触觉矩阵列数 |
| `median_window` | integer | 实际中值窗口 |
| `ema_alpha` | number | 实际 EMA 权重 |
| `reset_points` | list[[SignalSampleRef]] | EMA 重置点 |
| `boundary_reasons` | list[string] | 片段边界原因 |
| `summary_stats` | object | 片段滤波统计 |

## 有效性规则

- 片段不得跨越 [[MissingIntervalIssue]]。
- 片段不得包含 tactile 相关 `unrepaired` / `skipped` 样本。
- shape 不一致必须切断或失败，不得在同一片段内滤波。
- `reset_points` 只重置 EMA 状态，不改变样本数量或时间戳。

## 上游来源

- [[TactileFilterInputSequence]]
- [[SignalRepairResult]]
- [[MissingIntervalIssue]]
- [[SignalRepairRun]]
- [[TactileFilterConfig]]

## 下游消费者

- [[TactileFilterResult]]
- Parquet 标注与验证报告生成器。
- 开发者功能检验项 `scene2_tactile_filter`。

## 不负责

- 不保存每帧完整矩阵。
- 不决定滤波后 MCAP 写出路径。
- 不替代样本级审计。

## 相关链接

- [[TactileFilterSampleRecord]]
- [[TactileFilterConfig]]
- [[MissingIntervalIssue]]
