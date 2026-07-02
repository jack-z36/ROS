# TactileFilterSampleRecord

## 定义

`TactileFilterSampleRecord` 是触觉滤波器对单个触觉样本的滤波审计记录。

## 所属位置

阶段二 Service 场景二，来源能力模块：[[触觉滤波器]]。

## 现实语义

它回答“这一帧触觉矩阵是否被滤波、是否因边界或接触变化保留原值、滤波前后差异摘要是什么”。

## 字段或取值

| 字段 | 类型 | 现实含义 |
|---|---|---|
| `sample_record_id` | string | 样本审计记录 id |
| `segment_id` | string | 所属滤波片段 |
| `sample_ref` | [[SignalSampleRef]] | 样本定位 |
| `source_topic` | string | 来源触觉 topic |
| `status` | enum string | `filtered` / `kept_original` / `skipped_boundary` / `ema_reset` / `invalid_shape` |
| `filter_method` | enum string | `median_ema` / `no_op` |
| `shape` | object | `rows`、`cols`、`cell_count` |
| `original_summary` | object | 原矩阵 min、max、mean 等摘要 |
| `filtered_summary` | object/null | 滤波后矩阵摘要 |
| `diff_summary` | object/null | changed_cell_count、mean_abs_delta、max_abs_delta |
| `contact_reset` | boolean | 当前样本是否触发 EMA 重置 |
| `debug_artifact_ref` | string/null | 开发者调试模式完整矩阵 diff 引用 |
| `reason` | string | 处理原因 |

## 有效性规则

- 主记录默认不得保存完整矩阵 diff。
- `filtered` 状态必须包含 `filtered_summary` 和 `diff_summary`。
- `kept_original`、`skipped_boundary`、`invalid_shape` 必须包含 reason。
- `contact_reset=true` 时不得把 reset 前 EMA 状态跨到 reset 后样本。
- 完整矩阵 diff 只允许通过 `debug_artifact_ref` 引用开发者调试产物。

## 上游来源

- [[TactileFilterInputSequence]]
- [[TactileFilterConfig]]
- [[SignalRepairRun]]
- [[MissingIntervalIssue]]

## 下游消费者

- [[TactileFilterResult]]
- Parquet 标注与验证报告生成器。
- 开发者功能检验项 `scene2_tactile_filter`。

## 不负责

- 不承载完整滤波后序列。
- 不判断接触是否有效。
- 不决定 mask。

## 相关链接

- [[TactileFilterResult]]
- [[TactileFilterSegmentSummary]]
- [[SignalSampleRef]]
