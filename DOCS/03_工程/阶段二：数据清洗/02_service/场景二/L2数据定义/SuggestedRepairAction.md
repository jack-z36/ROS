# SuggestedRepairAction

## 定义

`SuggestedRepairAction` 是异常值检测器给数据补全器、滤波器和标注生成器的处理建议枚举。

## 所属位置

阶段二 Service 场景二，来源能力模块：[[异常值检测器]]。

## 现实语义

它描述检测器对当前问题的建议。它不是改值授权，也不是修复计算入口；新运行必须先产生字段级 `RepairDisposition`，只有 `AUTO_REPAIR` 才允许计算。

## 字段或取值

| 取值 | 现实含义 | 典型下游 |
|---|---|---|
| `repairable_interpolate` | 可用插值修复 | 数据补全器 |
| `repairable_hold` | 可用邻近值或短段保持修复 | 数据补全器 |
| `mark_only` | 不建议补全，只保留标记 | 滤波器、标注生成器 |
| `drop_or_mask_candidate` | 严重异常，后续考虑 mask 或丢弃 | 标注生成器、场景四 |
| `inspect_required` | 规则无法可靠判断，需要人工复查 | 开发者验收、报告 |

## 有效性规则

- 异常值检测器必须为每条 [[SampleReliabilityIssue]] 和 [[MissingIntervalIssue]] 填写一个建议。
- 对 [[SampleReliabilityIssue]]，任何枚举值都不能绕过字段级 `RepairDisposition`；`inspect_required` 必须成为人工复查/非自动处置。
- 对 [[MissingIntervalIssue]]，即使建议为 `repairable_interpolate` 或 `repairable_hold`，v1 数据补全器也不得新增消息。
- `mark_only`、`drop_or_mask_candidate` 和 `inspect_required` 不得被补全器静默改写为修复成功；当前实现也不执行 `repairable_hold`。
- [[RepairMethod]] 记录补全器实际做了什么，不得用本枚举替代。

## 上游来源

- [[ReliabilityCheckRuleConfig]]
- [[异常值检测器]] 的检测规则。

## 下游消费者

- 数据补全器。
- 位姿滤波器。
- 触觉滤波器。
- Parquet 标注与验证报告生成器。

## 不负责

- 不负责记录修复后的值。
- 不负责表达实际修复方法，实际方法由 [[RepairMethod]] 表达。
- 不负责定义最终 mask 类型。
- 不负责替代人工验收判断。

## 当前未知问题

| 问题 | 当前处理 |
|---|---|
| 是否需要更细的修复动作枚举 | v1 保持最小枚举，后续由补全器 L2 扩展 |

## 相关链接

- [[SampleReliabilityIssue]]
- [[MissingIntervalIssue]]
- [[IssueEvidence]]
- [[RepairMethod]]
