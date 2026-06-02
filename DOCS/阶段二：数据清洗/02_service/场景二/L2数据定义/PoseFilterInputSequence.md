# PoseFilterInputSequence

## 定义

`PoseFilterInputSequence` 是位姿滤波器消费的补全后 pose 序列语义输入。

## 所属位置

阶段二 Service 场景二，来源能力模块：[[位姿滤波器]]。

## 现实语义

它把 [[SignalRepairResult]] 中的 `output_sequence_refs` 解释为可滤波的 pose 序列输入，避免位姿滤波器直接猜测补全器 artifact 的具体文件格式。

## 字段或取值

| 字段 | 类型 | 现实含义 |
|---|---|---|
| `source_topic` | string | 来源 pose topic，必须保持与 cleaned MCAP / MCAP_A 对应 |
| `modality` | enum string | 固定为 `pose` |
| `time_domain` | enum string | `log_time` / `publish_time` / `header_stamp` |
| `samples` | list[object] | 按原始顺序排列的 [[ArmBaseTcpPose]] 样本 |
| `sample_refs` | list[[SignalSampleRef]] | 与 `samples` 一一对应的样本定位 |
| `repair_result_ref` | string / [[SignalRepairResult]] | 来源补全结果引用 |
| `missing_interval_issues` | list[[MissingIntervalIssue]] | 无样本缺失区间 |
| `blocked_sample_refs` | list[[SignalSampleRef]] | pose 相关 `unrepaired` / `skipped` 样本 |
| `timestamp_policy` | enum string | 固定 `preserve_original` |

## 有效性规则

- `samples`、`sample_refs` 必须一一对应，且数量相等。
- `timestamp_policy` 必须为 `preserve_original`。
- 样本排序必须沿用上游序列排序，不得重排。
- 任何 [[MissingIntervalIssue]] 和 pose 相关 `unrepaired` / `skipped` 样本必须作为滤波分段边界。
- 本对象只定义语义接口；`SignalRepairResult.output_sequence_refs` 的具体 artifact 格式由数据补全器 L3 固化。

## 上游来源

- [[SignalRepairResult]]
- [[SignalRepairRun]]
- [[SignalRepairSampleRecord]]
- [[MissingIntervalIssue]]
- [[ArmBaseTcpPose]]

## 下游消费者

- [[位姿滤波器]]。
- [[PoseFilterSegmentSummary]]。
- [[PoseFilterResult]]。

## 不负责

- 不承载触觉或夹爪序列。
- 不定义补全算法。
- 不修改 MCAP topic、时间戳或样本数量。
- 不表达最终训练 mask。

## 当前未知问题

| 问题 | 当前处理 |
|---|---|
| 补全后序列 artifact 的正式文件格式 | 由数据补全器 L3 固化；本定义只要求能映射为本语义对象 |
| `time_domain` 是否最终统一为一种 | v1 继承上游 `SignalSampleRef.time_domain` |

## 相关链接

- [[PoseFilterConfig]]
- [[PoseFilterResult]]
- [[SignalRepairResult]]
- [[SignalSampleRef]]
