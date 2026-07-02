# IssueTimeSegment

## 定义

`IssueTimeSegment` 是旧版场景二异常检测接口中的通用时间段对象，已迁移为废弃概念。

## 所属位置

阶段二 Service 场景二，首个来源能力模块：[[异常值检测器]]。

## 现实语义

旧版设计把单个异常点、连续异常样本和缺失区间都统一表达为时间段。新设计已改为样本级主接口：

- 已有样本异常使用 [[SampleReliabilityIssue]] 和 [[SignalSampleRef]]。
- 无样本缺失区间使用 [[MissingIntervalIssue]]。
- 展示和报告聚合摘要使用 [[ReliabilityIssueGroup]]。

新 L2/L3 不应继续引用本概念作为通用必填接口。

## 字段或取值

| 字段 | 类型 | 现实含义 |
|---|---|---|
本文件不再定义新接口字段。保留字段仅供读取历史文档时理解：

| 旧字段 | 新去向 |
|---|---|
| `start_time` / `end_time` / `time_domain` | [[MissingIntervalIssue]] 或 [[ReliabilityIssueGroup]] 内嵌字段 |
| `sample_count` | [[ReliabilityIssueGroup]] 内嵌字段 |
| `open_start` / `open_end` | 如仍需要，后续在 [[MissingIntervalIssue]] 中扩展 |

## 有效性规则

- 新文档不得把本对象作为 [[SampleReliabilityIssue]] 的字段。
- 若遇到旧文档中的 `IssueTimeSegment`，应按语义迁移到 [[MissingIntervalIssue]] 或 [[ReliabilityIssueGroup]]。

## 上游来源

- 旧版 [[异常值检测器]] 设计。

## 下游消费者

- 仅供理解历史记录和迁移旧文档。

## 不负责

- 不负责新接口设计。
- 不负责数据补全器输入。
- 不负责报告聚合；报告聚合使用 [[ReliabilityIssueGroup]]。

## 当前未知问题

| 问题 | 当前处理 |
|---|---|
| 是否彻底删除本文件 | 暂不删除，作为历史迁移说明保留 |

## 相关链接

- [[SampleReliabilityIssue]]
- [[MissingIntervalIssue]]
- [[ReliabilityIssueGroup]]
