# SignalRepairSampleRecord

## 定义

`SignalRepairSampleRecord` 是数据补全器对单个样本在某个 repair run 中的处理记录。

## 所属位置

阶段二 Service 场景二，来源能力模块：[[数据补全器]]。

## 现实语义

它回答“这个样本最终是否被改、怎么改、原始值和修复后值是什么、为什么没改”。它挂在 [[SignalRepairRun]] 下。

## 字段或取值

| 字段 | 类型 | 现实含义 |
|---|---|---|
| `sample_record_id` | string | 样本修复记录 id |
| `repair_run_id` | string | 所属 run |
| `sample_ref` | [[SignalSampleRef]] | 样本定位 |
| `source_issue_ids` | list[string] | 对应样本级异常 id |
| `status` | [[RepairDecisionStatus]] | 样本处理状态 |
| `repair_method` | [[RepairMethod]] | 实际修复方法 |
| `original_value` | object/string/null | 原始值或摘要 |
| `repaired_value` | object/string/null | 修复后值或摘要 |
| `value_summary` | object/null | 触觉等大 payload 的统计摘要 |
| `clamped` | boolean | gripper 修复后是否发生 clamp |
| `fallback_reason` | string/null | 插值降级 hold 的原因 |
| `debug_artifact_ref` | string/null | 可选调试 artifact 引用 |
| `reason` | string | 成功、拒绝或跳过原因 |

## 有效性规则

- pose 和 gripper 必须保存完整原始值和修复后值。
- tactile 主记录默认只保存 shape、min、max、mean、changed_cell_count 等摘要。
- tactile 完整矩阵 diff 只在开发者调试模式输出，不进入主结构。
- `repaired` 状态必须包含实际修复方法和修复后值或摘要。
- `unrepaired` / `skipped` 必须包含 reason。

## 上游来源

- [[SignalRepairRun]]
- 原始 cleaned MCAP 样本。
- 修复后内存序列或调试 artifact。

## 下游消费者

- [[SignalRepairResult]]
- Parquet 标注与验证报告生成器。
- 开发者功能检验项 `scene2_signal_repair`。

## 不负责

- 不承载完整三模态修复后序列。
- 不决定最终 mask。

## 相关链接

- [[SignalRepairRun]]
- [[SignalRepairResult]]
- [[RepairMethod]]
