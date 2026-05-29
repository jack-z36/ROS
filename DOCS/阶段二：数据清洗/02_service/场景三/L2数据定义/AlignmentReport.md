# AlignmentReport

## 定义

`AlignmentReport` 是场景三对齐结果的机器可读统计摘要，首版落盘为 `alignment_report.json`。

## 所属位置

阶段二 Service 场景三，来源能力模块：[[对齐契约与配置定义]]。

## 现实语义

它汇总本次对齐的输入、配置、step 数、各字段误差统计、缺失率、超时率、插值比例、聚合覆盖率和失败摘要。

## 字段或取值

| 字段 | 类型 | 现实含义 |
|---|---|---|
| `input_mcap_a` | string / [[McapA]] | 输入 MCAP_A |
| `mcap_a_write_summary_ref` | string / [[McapAWriteSummary]] | 上游写出摘要引用 |
| `config_ref` | string / [[Scene3AlignmentConfig]] | 本次对齐配置引用 |
| `step_timeline_summary` | object / [[StepTimeline]] | 时间轴摘要 |
| `field_stats` | object | 每个字段的误差、缺失、超时、fallback 和聚合统计 |
| `status_counts` | object | [[FieldAlignmentStatus]] 计数 |
| `output_aligned_mcap` | string / [[AlignedMcap]] | 输出 aligned MCAP 路径 |
| `alignment_index` | string / [[AlignmentIndex]] | 输出 alignment index 路径 |
| `status` | enum string | `completed` / `failed` |
| `failure_reason` | string/null | 失败原因 |
| `run_id` | string/null | 所属 run id |

## 有效性规则

- `AlignmentReport` 只保存统计摘要，不保存逐 step-field 明细。
- 逐 step-field 来源、原始时间戳、对齐方法和误差必须写入 [[AlignmentIndex]]。
- 成功时必须能引用 [[AlignedMcap]] 和 [[AlignmentIndex]]。
- 失败时必须说明失败原因，不能留下误导性的完整输出。

## 上游来源

- [[AlignmentIndex]]。
- [[StepTimeline]]。
- [[Scene3AlignmentConfig]]。
- [[McapAWriteSummary]]。

## 下游消费者

- aligned MCAP 与 sidecar 写出器。
- 场景四 quality report。
- 人工复查和场景三完整 smoke test。

## 不负责

- 不替代 [[AlignmentIndex]]。
- 不保存主数据 payload。
- 不决定 mask 或 episode 丢弃。

## 相关链接

- [[AlignmentIndex]]
- [[AlignedMcap]]
- [[Scene3AlignmentConfig]]
