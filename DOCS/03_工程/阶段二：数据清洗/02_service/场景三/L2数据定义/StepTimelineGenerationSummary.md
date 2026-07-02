# StepTimelineGenerationSummary

## 定义

`StepTimelineGenerationSummary` 是场景三统一 Step 时间轴生成动作的结构化结论摘要。

## 所属位置

阶段二 Service 场景三，来源能力模块：[[统一Step时间轴生成器]]。

## 现实语义

它回答“本次是否成功从上游输入盘点结果和场景三配置生成 [[StepTimeline]]、使用了哪些起止边界和频率参数、失败时为什么不能生成时间轴”。

## 字段或取值

| 字段 | 类型 | 现实含义 |
|---|---|---|
| `status` | enum string | `generated` / `failed` |
| `failure_reasons` | list[string] | 不能生成时间轴的原因 |
| `source_topic_catalog_ref` | string / [[SourceTopicCatalog]] | 本次使用的 topic catalog 引用 |
| `input_validation_summary_ref` | string / [[McapAInputValidationSummary]] | 本次使用的输入校验摘要引用 |
| `config_ref` | string / [[Scene3AlignmentConfig]] | 本次使用的场景三配置引用 |
| `timeline_ref` | string / [[StepTimeline]] / null | 成功生成的时间轴引用 |
| `target_step_hz` | number | 本次实际使用的目标 step 频率 |
| `baseline_intersection_start_ns` | integer/null | 上游确认的左右图像共同有效区间开始时间 |
| `baseline_intersection_end_ns` | integer/null | 上游确认的左右图像共同有效区间结束时间 |
| `range_policy` | enum string | 首版固定 `required_field_intersection` |
| `baseline_policy` | enum string | 首版固定 `stereo_image_intersection` |
| `timestamp_rounding_policy` | enum string | 首版固定 `rational_accumulation_round_to_ns` |
| `include_start` | bool | 首版固定 `true` |
| `force_include_end` | bool | 首版固定 `false` |
| `step_count` | integer | 成功生成的 step 数，失败时为 0 |
| `first_step_time_ns` | integer/null | 第一条 step 时间戳 |
| `last_step_time_ns` | integer/null | 最后一条 step 时间戳 |
| `created_at` | string/null | 摘要创建时间 |
| `run_id` | string/null | 所属开发者 run id |

`failure_reasons` 固定取值至少包括：

| reason | 触发条件 |
|---|---|
| `input_not_consumable` | [[McapAInputValidationSummary]].`status` 不是 `consumable` |
| `missing_baseline_intersection` | 上游未提供有效 baseline intersection |
| `invalid_target_step_hz` | [[Scene3AlignmentConfig]].`target_step_hz` 小于或等于 0 |
| `invalid_time_range` | `baseline_intersection_start_ns` 大于 `baseline_intersection_end_ns` |

## 有效性规则

- 当 `status=generated` 时，`failure_reasons` 必须为空，`timeline_ref` 必须非空，`step_count` 必须大于或等于 1。
- 当 `status=failed` 时，`timeline_ref` 必须为空，`step_count` 必须为 0，`failure_reasons` 必须至少包含一个 reason。
- `baseline_intersection_start_ns <= baseline_intersection_end_ns` 时允许生成 1 个 step。
- `first_step_time_ns` 必须等于 `baseline_intersection_start_ns`。
- `last_step_time_ns` 不得大于 `baseline_intersection_end_ns`。
- `timestamp_rounding_policy` 必须表达为有理数累计后取整到纳秒，避免固定截断或固定四舍五入周期带来的长期漂移。

## 上游来源

- [[SourceTopicCatalog]]
- [[McapAInputValidationSummary]]
- [[Scene3AlignmentConfig]]
- [[统一Step时间轴生成器]]

## 下游消费者

- 开发者功能检验项 `scene3_step_timeline_check`。
- 多策略字段对齐器。
- 对齐索引与报告数据生成器。
- aligned MCAP 与 sidecar 写出器。
- 场景三完整 smoke test。

## 不负责

- 不保存完整 step 时间戳序列；完整时间轴由 [[StepTimeline]] 表达。
- 不保存 MCAP 消息值。
- 不表达 step-field 级别对齐结果。
- 不决定 step 是否可用于训练。
- 不替代 [[AlignmentReport]] 或 [[AlignedMcapWriteSummary]]。

## 相关链接

- [[统一Step时间轴生成器]]
- [[StepTimeline]]
- [[SourceTopicCatalog]]
- [[McapAInputValidationSummary]]
- [[Scene3AlignmentConfig]]
- [[AlignmentIndex]]
