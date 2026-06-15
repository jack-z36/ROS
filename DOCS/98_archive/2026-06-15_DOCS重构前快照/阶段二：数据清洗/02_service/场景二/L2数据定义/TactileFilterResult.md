# TactileFilterResult

## 定义

`TactileFilterResult` 是触觉滤波器一次运行的聚合输出对象。

## 所属位置

阶段二 Service 场景二，来源能力模块：[[触觉滤波器]]。

## 现实语义

它回答“触觉序列在哪里被滤波、哪些片段被跳过或重置、滤波后序列在哪里、滤波前后差异摘要是什么”。

## 字段或取值

| 字段 | 类型 | 现实含义 |
|---|---|---|
| `input_repair_result_ref` | string / [[SignalRepairResult]] | 来源补全结果引用 |
| `tactile_filter_config_ref` | string / [[TactileFilterConfig]] | 本次滤波配置引用 |
| `input_sequence_refs` | list[[TactileFilterInputSequence]] | 输入触觉序列引用 |
| `output_sequence_refs` | object/list | 滤波后触觉序列 artifact 或内存引用 |
| `segment_summaries` | list[[TactileFilterSegmentSummary]] | 片段与 reset 摘要 |
| `sample_records` | list[[TactileFilterSampleRecord]] | 样本级审计记录 |
| `timestamp_policy` | enum string | 固定 `preserve_original` |
| `sample_count_before` | object | 各触觉 topic 输入样本数 |
| `sample_count_after` | object | 各触觉 topic 输出样本数 |
| `summary_by_topic` | object | 按 topic 汇总 filtered、kept、reset、skipped |
| `created_at` | string/null | 结果创建时间 |
| `run_id` | string/null | 所属 run id |

## 有效性规则

- `timestamp_policy` 必须为 `preserve_original`。
- 每个 topic 必须满足 `sample_count_before == sample_count_after`。
- 输出序列必须保持原 topic、时间戳、排序和样本数量。
- 主结构不得嵌入完整矩阵 diff；完整 diff 只能作为调试 artifact 引用。
- `segment_summaries` 必须覆盖所有可滤波片段。

## 上游来源

- [[SignalRepairResult]]
- [[TactileFilterConfig]]
- [[TactileFilterInputSequence]]
- [[触觉滤波器]]

## 下游消费者

- [[McapA|MCAP_A]] 生成器。
- Parquet 标注与验证报告生成器。
- 开发者功能检验项 `scene2_tactile_filter`。

## 不负责

- 不写 MCAP_A。
- 不决定最终训练 mask。
- 不重新表达异常检测或补全结果。

## 当前未知问题

| 问题 | 当前处理 |
|---|---|
| 生产模式是否保存完整样本级审计 | 开发者检验完整保存主审计；生产压缩策略后续由报告生成器 L2 对齐 |

## 相关链接

- [[TactileFilterConfig]]
- [[TactileFilterInputSequence]]
- [[TactileFilterSampleRecord]]
- [[TactileFilterSegmentSummary]]
- [[SignalRepairResult]]
