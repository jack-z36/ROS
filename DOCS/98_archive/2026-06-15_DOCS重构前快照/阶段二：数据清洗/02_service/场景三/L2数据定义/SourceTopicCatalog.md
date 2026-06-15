# SourceTopicCatalog

## 定义

`SourceTopicCatalog` 是场景三对 MCAP_A 输入 topic 和目标字段映射结果的结构化盘点对象。

## 所属位置

阶段二 Service 场景三，来源能力模块：[[MCAP_A输入盘点与校验器]]。

## 现实语义

它回答“本次 MCAP_A 中实际有哪些 topic、每个 topic 的消息类型和时间范围是什么、这些 topic 是否能匹配 [[TargetFieldMapping]] 中声明的目标字段、哪些 topic 只是未映射的只读输入事实”。

## 字段或取值

| 字段 | 类型 | 现实含义 |
|---|---|---|
| `source_mcap_a` | string / [[McapA]] | 被盘点的 MCAP_A 路径或引用 |
| `summary_ref` | string / [[McapAWriteSummary]] | 本次 MCAP_A 对应的写出摘要引用 |
| `config_ref` | string / [[Scene3AlignmentConfig]] | 本次盘点使用的配置引用 |
| `topic_entries` | list[object] | MCAP_A 中按真实 topic 组织的盘点条目 |
| `field_entries` | list[object] | 按 [[TargetFieldMapping]] 组织的字段匹配条目 |
| `unmapped_topics` | list[string] | 存在于 MCAP_A 但未出现在 `target_fields` 中的只读 topic |
| `baseline_topic_status` | object | 左右图像基准 topic 的存在性、类型、样本数和时间戳状态 |
| `baseline_intersection_start_ns` | integer/null | 左右图像共同有效时间范围开始时间 |
| `baseline_intersection_end_ns` | integer/null | 左右图像共同有效时间范围结束时间 |
| `has_baseline_intersection` | bool | 左右图像是否存在共同有效时间范围 |
| `created_at` | string/null | catalog 创建时间 |

`topic_entries` 中每个条目至少表达：

| 字段 | 类型 | 现实含义 |
|---|---|---|
| `topic` | string | MCAP_A 中的真实 topic 名称 |
| `message_type` | string | ROS 消息类型或 MCAP schema name |
| `sample_count` | integer | topic 消息数量 |
| `start_time_ns` | integer/null | topic 第一条消息时间 |
| `end_time_ns` | integer/null | topic 最后一条消息时间 |
| `timestamp_order` | enum string | `ordered` / `duplicate_only` / `out_of_order` / `empty` |
| `matched_field_names` | list[string] | 匹配到的目标字段名 |
| `is_baseline_topic` | bool | 是否属于左右图像基准 topic |
| `is_unmapped_topic` | bool | 是否未被任何目标字段配置引用 |

`field_entries` 中每个条目至少表达：

| 字段 | 类型 | 现实含义 |
|---|---|---|
| `field_name` | string | [[TargetFieldMapping]] 中声明的字段名 |
| `source_topic` | string | 字段期望读取的 MCAP_A topic |
| `expected_message_type` | string | 配置声明的消息类型 |
| `actual_message_type` | string/null | MCAP_A 实际消息类型 |
| `modality` | enum string | `image` / `pose` / `tactile` / `gripper` |
| `required_for_timeline` | bool | 是否参与时间轴起止裁剪 |
| `availability` | enum string | `available` / `missing_topic` / `type_mismatch` / `timestamp_unusable` / `empty_topic` |
| `sample_count` | integer | 实际样本数，缺失时为 0 |
| `start_time_ns` | integer/null | 实际起始时间 |
| `end_time_ns` | integer/null | 实际结束时间 |
| `timestamp_order` | enum string | 对应 topic 时间戳状态 |
| `blocking` | bool | 该字段问题是否阻塞场景三继续运行 |
| `notes` | list[string] | 调试说明或 warning |

## 有效性规则

- `source_mcap_a` 必须引用场景二定义的 [[McapA]]，不得新增 `ValidatedMcap` 或类似输入对象。
- `summary_ref` 必须引用场景二定义的 [[McapAWriteSummary]]。
- 左右图像基准 topic 来自 [[Scene3AlignmentConfig]].`baseline_image_topics` 和 [[TargetFieldMapping]]。
- 左右图像基准 topic 缺失、为空、时间戳乱序或无共同有效时间范围时，catalog 仍可生成，但必须把对应 `field_entries.blocking=true`，并由 [[McapAInputValidationSummary]] 判定不可消费。
- 非基准字段缺失、类型不匹配、时间戳乱序或不可用不阻塞主链路，必须记录为 `availability` 和 warning。
- 未出现在 `target_fields` 中的 MCAP_A topic 必须进入 `unmapped_topics`，只用于只读盘点和调试，不参与 [[StepTimeline]] 或字段对齐。
- 本对象只计算左右图像基准共同有效时间范围元数据，不生成 step 序列。

## 上游来源

- [[McapA]]
- [[McapAWriteSummary]]
- [[Scene3AlignmentConfig]]
- [[TargetFieldMapping]]
- [[MCAP_A输入盘点与校验器]]

## 下游消费者

- 统一 Step 时间轴生成器。
- 多策略字段对齐器。
- 对齐索引与报告数据生成器。
- aligned MCAP 与 sidecar 写出器。
- 开发者功能检验项 `scene3_mcap_a_input_check`。

## 不负责

- 不保存 MCAP 消息值。
- 不生成 [[StepTimeline]]。
- 不表达 step-field 级别的对齐结果。
- 不决定训练 mask、episode 构建或 canonical dataset schema。
- 不替代 [[McapAWriteSummary]] 的上游写出追溯。

## 相关链接

- [[MCAP_A输入盘点与校验器]]
- [[McapAInputValidationSummary]]
- [[McapA]]
- [[McapAWriteSummary]]
- [[Scene3AlignmentConfig]]
- [[TargetFieldMapping]]
- [[StepTimeline]]
