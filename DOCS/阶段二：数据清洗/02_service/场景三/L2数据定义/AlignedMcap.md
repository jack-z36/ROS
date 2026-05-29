# AlignedMcap

## 定义

`AlignedMcap` 是场景三按统一 step 时间轴写出的对齐后主数据 MCAP。

## 所属位置

阶段二 Service 场景三，来源能力模块：[[对齐契约与配置定义]]。

## 现实语义

它是场景三输出，不是输入。输入是场景二 [[McapA]] / validated MCAP。`AlignedMcap` 的每个输出 topic 只保留已经完成时间对齐后的主数据，消息时间戳统一为 step 时间。

## 字段或取值

| 内容 | 契约 |
|---|---|
| 输入来源 | [[McapA]]，只读不改 |
| 默认落点 | `asset/阶段二：数据清洗/dev/mcap_aligned/` |
| 默认命名 | `<mcap_a_stem>_aligned.mcap` |
| topic 命名 | 首版保留原语义 topic 名 |
| 时间戳 | 使用 [[StepTimeline]] 的 `step_time_ns` |
| 主数据 | 图像、位姿、触觉、夹爪等完成对齐后的消息 |
| 来源追溯 | 通过 [[AlignmentIndex]] 表达 |
| 统计摘要 | 通过 [[AlignmentReport]] 表达 |

## 有效性规则

- 不保留 MCAP_A 中原始异步时间戳下的完整数据流。
- 不修改、覆盖或回写 [[McapA]]。
- 不把逐字段来源、原始时间戳、对齐方法、误差、missing、timeout 或 fallback 只写进 MCAP；这些事实必须写入 [[AlignmentIndex]]。
- 不提前改成 canonical observation/action topic，避免侵入场景四 schema。
- 对 `missing_time`、`timeout` 或 `unavailable` 的 step-field 不写空占位消息，也不复用上一有效值；缺失事实只通过 [[AlignmentIndex]] 表达。
- 只有 `aligned`、`interpolated`、`aggregated` 或 `fallback_nearest` 等有可写值 / 可写引用的字段结果才进入 aligned MCAP。

## 上游来源

- [[McapA]]。
- [[StepTimeline]]。
- 多策略字段对齐器。
- [[Scene3AlignmentConfig]]。
- [[FieldAlignmentResult]]。

## 下游消费者

- 场景四 LeRobotDataset v3 构建。
- 场景三完整 smoke test。
- 人工复查。

## 不负责

- 不保存原始异步 MCAP_A 全量数据流。
- 不定义 canonical dataset schema。
- 不决定训练 mask。
- 不表达缺失字段的空值语义。

## 相关链接

- [[McapA]]
- [[StepTimeline]]
- [[AlignmentIndex]]
- [[AlignmentReport]]
- [[AlignedMcapWriteSummary]]
