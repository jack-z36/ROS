# FieldAlignmentResult

## 定义

`FieldAlignmentResult` 是场景三多策略字段对齐器输出的内存态逐 step-field 对齐结果。

## 所属位置

阶段二 Service 场景三，来源能力模块：[[多策略字段对齐器]]。

## 现实语义

它回答“某个字段在某个统一 step 上到底从哪个来源样本、哪个插值邻居或哪个聚合窗口得到结果，以及该结果是否正常、超时、缺失、fallback 或不可用”。

## 字段或取值

| 字段 | 类型 | 现实含义 |
|---|---|---|
| `step_index` | integer | 统一 step 序号 |
| `step_time_ns` | integer | 当前 step 的统一时间戳 |
| `field_name` | string | [[TargetFieldMapping]] 中声明的目标字段名 |
| `source_topic` | string/null | 被采用的 MCAP_A 来源 topic |
| `output_topic` | string/null | 后续 aligned MCAP 预计写出的 topic |
| `source_time_ns` | integer/null | 被采用的来源样本时间戳 |
| `alignment_method` | string | 本字段本 step 实际使用的对齐方法 |
| `status` | [[FieldAlignmentStatus]] | 对齐状态 |
| `dt_ms` | number/null | 来源样本时间与 `step_time_ns` 的差值 |
| `neighbor_before_time_ns` | integer/null | 插值前邻居时间 |
| `neighbor_after_time_ns` | integer/null | 插值后邻居时间 |
| `window_start_time_ns` | integer/null | 聚合窗口开始时间 |
| `window_end_time_ns` | integer/null | 聚合窗口结束时间 |
| `sample_count` | integer/null | 匹配、插值或聚合使用的样本数 |
| `coverage_ratio` | number/null | 触觉窗口覆盖率 |
| `fallback_reason` | string/null | fallback 原因 |
| `message_ref` | string/null | 原始消息引用或定位信息 |
| `derived_value` | object/null | pose、gripper、触觉聚合等轻量派生值 |
| `notes` | list[string] | 调试说明或 warning |

## 有效性规则

- 每个 `step_index + field_name` 最多生成一条主结果。
- 图像字段成功对齐时只保存 `message_ref` 和对齐元数据，不内联图像 payload。
- pose 插值、四元数 slerp、夹爪最近邻值和触觉窗口聚合值允许在 `derived_value` 中内联，供写出器生成 aligned MCAP。
- `derived_value` 只承载轻量值，不保存完整图像、完整触觉原始序列或大 payload。
- 当 `status=fallback_nearest` 时，必须填写 `fallback_reason`。
- 当 `status=aggregated` 时，必须填写窗口起止、`sample_count` 和 `coverage_ratio`。
- 当字段在 [[SourceTopicCatalog]] 中不可用时，必须输出 `status=unavailable`，不得阻塞其他字段对齐。
- 本对象不替代 [[AlignmentIndex]]；第 5 模块负责将它汇总和规范化为最终 sidecar 数据。

## 上游来源

- [[StepTimeline]]
- [[SourceTopicCatalog]]
- [[McapAInputValidationSummary]]
- [[Scene3AlignmentConfig]]
- [[TargetFieldMapping]]
- [[FieldAlignmentStrategy]]
- 多策略字段对齐器。

## 下游消费者

- 对齐索引与报告数据生成器。
- aligned MCAP 与 sidecar 写出器。
- 开发者功能检验项 `scene3_field_alignment_check`。
- 场景三完整 smoke test。

## 不负责

- 不保存最终 Parquet sidecar。
- 不保存完整主数据 payload。
- 不汇总统计报告。
- 不决定训练 mask、episode 构建或 canonical dataset 可用性。
- 不修改 MCAP_A。

## 相关链接

- [[多策略字段对齐器]]
- [[StepTimeline]]
- [[TargetFieldMapping]]
- [[FieldAlignmentStatus]]
- [[AlignmentIndex]]
- [[AlignmentReport]]
