# AlignedMcapWriteSummary

## 定义

`AlignedMcapWriteSummary` 是场景三 aligned MCAP 与 sidecar 写出动作的摘要对象。

## 所属位置

阶段二 Service 场景三，来源能力模块：[[对齐契约与配置定义]]。

## 现实语义

它回答“本次 aligned MCAP、alignment_index.parquet 和 alignment_report.json 写到了哪里、来自哪个 MCAP_A、是否成功、失败原因是什么”。

## 字段或取值

| 字段 | 类型 | 现实含义 |
|---|---|---|
| `input_mcap_a` | string / [[McapA]] | 输入 MCAP_A |
| `output_aligned_mcap` | string / [[AlignedMcap]] | 输出 aligned MCAP |
| `alignment_index_path` | string / [[AlignmentIndex]] | 输出 Parquet sidecar |
| `alignment_report_path` | string / [[AlignmentReport]] | 输出 JSON 报告 |
| `config_ref` | string / [[Scene3AlignmentConfig]] | 对齐配置引用 |
| `step_count` | integer | 写出的 step 数 |
| `field_count` | integer | 对齐字段数 |
| `status` | enum string | `completed` / `failed` |
| `failure_reason` | string/null | 失败原因 |
| `created_at` | string/null | 摘要创建时间 |
| `run_id` | string/null | 所属 run id |

## 有效性规则

- 成功时 `output_aligned_mcap`、`alignment_index_path` 和 `alignment_report_path` 必须存在。
- 失败时不得留下误导性的完整 aligned MCAP。
- 写出摘要不得替代 [[AlignmentIndex]] 或 [[AlignmentReport]]。

## 上游来源

- aligned MCAP 与 sidecar 写出器。
- [[Scene3AlignmentConfig]]。
- [[AlignmentIndex]]。
- [[AlignmentReport]]。

## 下游消费者

- 场景三完整 smoke test。
- 场景四输入索引。
- 人工复查。

## 不负责

- 不保存逐 step-field 明细。
- 不保存主数据 payload。
- 不决定训练质量。

## 相关链接

- [[AlignedMcap]]
- [[AlignmentIndex]]
- [[AlignmentReport]]
- [[Scene3AlignmentConfig]]
