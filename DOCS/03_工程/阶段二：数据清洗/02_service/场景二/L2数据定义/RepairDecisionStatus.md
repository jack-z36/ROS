# RepairDecisionStatus

## 定义

`RepairDecisionStatus` 是数据补全器对样本或 repair run 的处理状态枚举。

## 所属位置

阶段二 Service 场景二，来源能力模块：[[数据补全器]]。

## 现实语义

它回答“补全器最终对这个样本或连续异常 run 做了什么”。

## 字段或取值

| 取值 | 现实含义 |
|---|---|
| `repaired` | 已自动修复已有样本值 |
| `unrepaired` | 本来属于可处理对象，但因策略、邻居、混合可修复性等原因拒绝修复 |
| `skipped` | 按规则不处理，例如 `mark_only`、`drop_or_mask_candidate`、`inspect_required` 或缺失区间 |

## 有效性规则

- 每个 [[SignalRepairRun]] 和 [[SignalRepairSampleRecord]] 必须有一个状态。
- `repaired` 必须有实际 [[RepairMethod]] 和修复前后值或摘要。
- `unrepaired` 和 `skipped` 必须写明 reason。

## 上游来源

- [[SignalReliabilityDetectionResult]]
- [[SignalRepairPolicyConfig]]

## 下游消费者

- [[SignalRepairResult]]
- Parquet 标注与验证报告生成器。

## 不负责

- 不表达上游建议；上游建议使用 [[SuggestedRepairAction]]。
- 不表达具体修复算法；具体算法使用 [[RepairMethod]]。

## 相关链接

- [[SignalRepairResult]]
- [[RepairMethod]]
