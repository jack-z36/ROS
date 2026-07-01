# McapAInputValidationSummary

## 定义

`McapAInputValidationSummary` 是场景三对一次 MCAP_A 输入盘点与校验动作生成的结构化结论摘要。

## 所属位置

阶段二 Service 场景三，来源能力模块：[[MCAP_A输入盘点与校验器]]。

## 现实语义

它回答“这次 MCAP_A 和对应写出摘要是否可信、是否满足场景三建立统一时间轴的最低条件、哪些问题会阻塞场景三继续运行、哪些问题只是下游字段可用性 warning”。

## 字段或取值

| 字段 | 类型 | 现实含义 |
|---|---|---|
| `input_mcap_a` | string / [[McapA]] | 被校验的 MCAP_A 路径或引用 |
| `mcap_a_write_summary` | string / [[McapAWriteSummary]] | 对应 MCAP_A 写出摘要路径或引用 |
| `config_ref` | string / [[Scene3AlignmentConfig]] | 本次校验使用的配置引用 |
| `catalog_ref` | string / [[SourceTopicCatalog]] | 本次盘点生成的 topic catalog 引用 |
| `status` | enum string | `consumable` / `not_consumable` |
| `hard_fail_reasons` | list[string] | 阻塞场景三继续运行的原因 |
| `warnings` | list[string] | 不阻塞主链路但需要下游注意的问题 |
| `summary_consistency_status` | enum string | `consistent` / `missing` / `unreadable` / `status_failed` / `path_mismatch` / `policy_mismatch` |
| `baseline_topics_present` | bool | 左右图像基准 topic 是否都存在 |
| `baseline_topics_ordered` | bool | 左右图像基准 topic 时间戳是否可用 |
| `has_baseline_intersection` | bool | 左右图像是否存在共同有效时间范围 |
| `baseline_intersection_start_ns` | integer/null | 左右图像共同有效区间开始时间 |
| `baseline_intersection_end_ns` | integer/null | 左右图像共同有效区间结束时间 |
| `required_field_failures` | list[string] | 基准或时间轴必需字段失败列表 |
| `optional_field_warnings` | list[string] | 非基准字段缺失、类型不匹配或乱序列表 |
| `unmapped_topic_count` | integer | 未映射只读 topic 数量 |
| `created_at` | string/null | 摘要创建时间 |
| `run_id` | string/null | 所属开发者 run id |

## 有效性规则

- `input_mcap_a` 必须引用场景二定义的 [[McapA]]。
- `mcap_a_write_summary` 必须引用场景二定义的 [[McapAWriteSummary]]。
- 当 `status=consumable` 时，`hard_fail_reasons` 必须为空，`summary_consistency_status` 必须为 `consistent`，且 `has_baseline_intersection=true`。
- 当任一 hard fail 规则触发时，`status` 必须为 `not_consumable`。
- `warnings` 和 `optional_field_warnings` 不得改变 `status`，只影响下游字段可用性和人工复查。
- `baseline_intersection_start_ns` / `baseline_intersection_end_ns` 只表达共同有效时间范围元数据，不代表已生成 [[StepTimeline]]。

hard fail 规则固定为：

| reason | 触发条件 |
|---|---|
| `missing_mcap_a` | MCAP_A 路径缺失或文件不可读 |
| `missing_mcap_a_write_summary` | 写出摘要路径缺失 |
| `unreadable_mcap_a_write_summary` | 写出摘要无法解析 |
| `summary_not_completed` | [[McapAWriteSummary]].`status` 不是 `completed` |
| `summary_output_path_mismatch` | [[McapAWriteSummary]].`output_mcap_a` 与本次输入 MCAP_A 不一致 |
| `summary_policy_mismatch` | [[McapAWriteSummary]].`timestamp_policy` 或 `topic_policy` 不符合 [[McapA]] 契约 |
| `missing_baseline_topic` | 左右图像基准 topic 任一缺失 |
| `baseline_topic_out_of_order` | 左右图像基准 topic 时间戳乱序 |
| `missing_baseline_intersection` | 左右图像不存在共同有效时间范围 |

## 上游来源

- [[McapA]]
- [[McapAWriteSummary]]
- [[Scene3AlignmentConfig]]
- [[TargetFieldMapping]]
- [[SourceTopicCatalog]]
- [[MCAP_A输入盘点与校验器]]

## 下游消费者

- 统一 Step 时间轴生成器。
- 多策略字段对齐器。
- 对齐索引与报告数据生成器。
- 开发者功能检验项 `scene3_mcap_a_input_check`。
- 场景三完整 smoke test。

## 不负责

- 不保存完整 topic 明细；完整 topic 和字段盘点由 [[SourceTopicCatalog]] 表达。
- 不保存 MCAP 消息值。
- 不生成 [[StepTimeline]]。
- 不决定每个 step 是否可用于训练。
- 不替代 [[AlignmentReport]] 或 [[AlignedMcapWriteSummary]]。

## 相关链接

- [[MCAP_A输入盘点与校验器]]
- [[SourceTopicCatalog]]
- [[McapA]]
- [[McapAWriteSummary]]
- [[Scene3AlignmentConfig]]
- [[TargetFieldMapping]]
- [[StepTimeline]]
