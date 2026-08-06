# PoseFilterSegmentSummary

## 定义

`PoseFilterSegmentSummary` 是位姿滤波器对一个连续可靠 pose 片段的滤波摘要。

## 所属位置

阶段二 Service 场景二，来源能力模块：[[位姿滤波器]]。

## 现实语义

它回答“某个 topic 的哪一段被作为连续可靠片段处理、实际窗口是多少、是否执行滤波、片段内有多少样本被修改或拒绝”。它用于审计分段策略和窗口换算。

## 字段或取值

| 字段 | 类型 | 现实含义 |
|---|---|---|
| `segment_id` | string | 片段 id |
| `sample_refs` | list[[SignalSampleRef]] | 实际参与该片段计算的完整成员；是滤波成员关系的唯一依据 |
| `boundary_reasons` | list[string] | stream 起止、缺失、未修复样本或信号时间边界原因 |
| `source_topic` | string | 来源 pose topic |
| `start_sample_ref` | [[SignalSampleRef]] | 片段起点样本 |
| `end_sample_ref` | [[SignalSampleRef]] | 片段终点样本 |
| `sample_count` | integer | 片段样本数 |
| `median_dt_sec` | number/null | 片段内时间戳中位间隔 |
| `configured_window_duration_ms` | number | 配置时间窗口 |
| `actual_window_size_samples` | integer/null | 换算后的奇数样本窗口 |
| `polyorder` | integer | 实际使用阶数 |
| `status` | enum string | `filtered` / `kept_original_short_segment` / `skipped_invalid_time` |
| `filtered_count` | integer | 采用滤波值的样本数 |
| `guard_rejected_count` | integer | 被 guard 拒绝的样本数 |
| `reason` | string | 片段状态说明 |

## 有效性规则

- 片段不得跨越 [[MissingIntervalIssue]]。
- 片段不得包含 pose 相关 `unrepaired` / `skipped` 样本。
- `actual_window_size_samples` 必须为奇数，且大于 `polyorder`；无法满足时片段原样保留。
- `sample_count` 必须等于该片段内样本记录数量。
- window、短段判断、`polyorder`、summary 和最终结果必须引用调用方传入的同一个 [[PoseFilterConfig]]，业务函数不得重建默认配置。
- 滤波器不得再用首尾 `message_index` 范围推测成员。

## 上游来源

- [[PoseFilterInputSequence]]
- [[PoseFilterConfig]]
- [[MissingIntervalIssue]]
- [[SignalRepairResult]]

## 下游消费者

- [[PoseFilterResult]]
- 开发者功能检验项 `scene2_pose_filter`。
- Parquet 标注与验证报告生成器。

## 不负责

- 不承载样本级原值和滤波值；样本级审计使用 [[PoseFilterSampleRecord]]。
- 不定义 MCAP_A 写出格式。

## 当前未知问题

| 问题 | 当前处理 |
|---|---|
| 是否需要按左右臂单独汇总更多统计 | v1 按 `source_topic` 自然区分 |

## 相关链接

- [[PoseFilterSampleRecord]]
- [[PoseFilterResult]]
