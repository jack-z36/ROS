# SignalReliabilityIssue

## 定义

`SignalReliabilityIssue` 是场景二信号可靠性问题的统称，不再作为单一混合结构落地实现。

## 所属位置

阶段二 Service 场景二，来源能力模块：[[异常值检测器]]。

## 现实语义

它用于在文档和报告中统称“信号存在可靠性问题”。正式接口拆为两类主记录：

- [[SampleReliabilityIssue]]：已有样本点上的异常，是数据补全器的主输入。
- [[MissingIntervalIssue]]：没有样本可挂载的缺失区间，v1 数据补全器不插入新消息。

异常检测器的一次完整输出由 [[SignalReliabilityDetectionResult]] 承载。

## 字段或取值

本概念不直接定义字段。字段由下列原子定义承载：

| 记录 | 定位方式 | 主要消费者 |
|---|---|---|
| [[SampleReliabilityIssue]] | [[SignalSampleRef]] | 数据补全器、滤波器、报告生成器 |
| [[MissingIntervalIssue]] | `start_time` / `end_time` / `time_domain` | 数据补全器、报告生成器、场景四 |
| [[ReliabilityIssueGroup]] | 派生聚合时间范围 | 开发者验收、报告生成器 |

## 有效性规则

- 新 L2/L3 不得再把 `SignalReliabilityIssue` 当作可直接序列化的混合对象。
- 需要定位已有样本异常时，必须使用 [[SampleReliabilityIssue]]。
- 需要表达无样本缺失段时，必须使用 [[MissingIntervalIssue]]。
- 需要展示连续异常摘要时，必须使用 [[ReliabilityIssueGroup]]，且以点级记录为准。

## 上游来源

- [[CleanedMcap]]
- [[CommonFrameTcpPose]]
- [[GripperWidthSample]]
- [[TactilePressureFrame]]
- [[ReliabilityCheckRuleConfig]]

## 下游消费者

- 数据补全器消费 [[SignalReliabilityDetectionResult]] 中的 `sample_issues` 和 `missing_interval_issues`。
- 位姿滤波器和触觉滤波器参考补全后的结果与不可修复记录。
- Parquet 标注与验证报告生成器消费点级问题、缺失区间、聚合摘要和补全记录。

## 不负责

- 不直接承载修复后的值。
- 不直接决定 episode 丢弃或训练 mask。
- 不替代后续 IK、关节限制或 MuJoCo 问题记录。

## 当前未知问题

| 问题 | 当前处理 |
|---|---|
| 与最终 `annotations.parquet` 字段的一一映射 | 由 Parquet 标注与验证报告生成器 L2 固化 |

## 相关链接

- [[SampleReliabilityIssue]]
- [[MissingIntervalIssue]]
- [[SignalReliabilityDetectionResult]]
- [[ReliabilityIssueGroup]]
