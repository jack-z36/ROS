# McapAWriteSummary

## 定义

`McapAWriteSummary` 是 MCAP_A 生成器一次写出动作的 sidecar JSON 摘要对象。

## 所属位置

阶段二 Service 场景二，来源能力模块：[[MCAP_A生成器]]。

## 现实语义

它回答“这次 MCAP_A 从哪个 cleaned MCAP 生成、用了哪些上游结果、替换了哪些 topic、复制了哪些 topic、是否成功、失败原因是什么”。它用于追溯，不进入 MCAP_A 主数据 topic。

## 字段或取值

| 字段 | 类型 | 现实含义 |
|---|---|---|
| `input_cleaned_mcap` | string / [[CleanedMcap]] | 来源 cleaned MCAP 路径或引用 |
| `output_mcap_a` | string / [[McapA]] | 写出的 MCAP_A 路径 |
| `write_config_ref` | string / [[McapAWriteConfig]] | 本次写出配置引用 |
| `signal_repair_result_ref` | string / [[SignalRepairResult]] | 补全结果引用 |
| `pose_filter_result_ref` | string / [[PoseFilterResult]] | 位姿滤波结果引用 |
| `tactile_filter_result_ref` | string / [[TactileFilterResult]] | 触觉滤波结果引用 |
| `replaced_topic_stats` | object | arm-base TCP pose / tactile / gripper 被替换 topic 的样本统计 |
| `copied_topic_stats` | object | 原样复制 topic 的样本统计 |
| `timestamp_policy` | enum string | 固定 `preserve_original` |
| `topic_policy` | enum string | 固定 `preserve_cleaned_topics` |
| `status` | enum string | `completed` / `failed` |
| `failure_reason` | string/null | 失败原因，成功时为空 |
| `created_at` | string/null | 摘要创建时间 |
| `run_id` | string/null | 所属 run id |

## 有效性规则

- 成功时 `output_mcap_a` 必须存在，且 `failure_reason` 为空。
- 失败时不得生成误导性的完整 MCAP_A；如存在临时文件必须清理或显式标记。
- `signal_repair_result_ref`、`pose_filter_result_ref`、`tactile_filter_result_ref` 是 strict 写出必需引用。
- `replaced_topic_stats` 必须区分 pose、tactile、gripper。
- `copied_topic_stats` 必须能说明未处理 topic 原样复制数量。
- 摘要不得嵌入完整 MCAP 消息或完整样本级审计记录。

## 上游来源

- [[CleanedMcap]]
- [[SignalRepairResult]]
- [[PoseFilterResult]]
- [[TactileFilterResult]]
- [[McapAWriteConfig]]
- MCAP_A 生成器

## 下游消费者

- Parquet 标注与验证报告生成器。
- 场景三时间轴对齐的输入索引。
- 开发者功能检验项 `scene2_mcap_a_writer`。
- 场景二完整 smoke test。

## 不负责

- 不替代 [[SignalRepairResult]]、[[PoseFilterResult]] 或 [[TactileFilterResult]] 的详细审计。
- 不保存关节角、IK、关节限制或 MuJoCo 结果。
- 不决定最终训练 mask 或 episode 丢弃。

## 相关链接

- [[McapA]]
- [[McapAWriteConfig]]
- [[SignalRepairResult]]
- [[PoseFilterResult]]
- [[TactileFilterResult]]
