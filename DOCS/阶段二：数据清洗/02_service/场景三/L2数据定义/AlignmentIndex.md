# AlignmentIndex

## 定义

`AlignmentIndex` 是场景三写出的逐 step-field 对齐事实 sidecar 表，首版落盘为 `alignment_index.parquet`。

## 所属位置

阶段二 Service 场景三，来源能力模块：[[对齐契约与配置定义]]。

## 现实语义

它记录每个 step 上每个字段来自哪个 source topic、原始时间戳是什么、采用什么对齐方法、时间误差多少，以及是否发生 missing、timeout 或 fallback。

## 字段或取值

| 字段 | 类型 | 现实含义 |
|---|---|---|
| `step_index` | integer | 统一 step 序号 |
| `step_time_ns` | integer | 统一 step 时间戳 |
| `field_name` | string | 对齐字段名 |
| `source_topic` | string/null | 来源 topic |
| `output_topic` | string/null | aligned MCAP 输出 topic |
| `source_time_ns` | integer/null | 被采用的来源样本时间戳 |
| `alignment_method` | string | 实际使用的方法 |
| `status` | [[FieldAlignmentStatus]] | 对齐状态 |
| `dt_ms` | number/null | 来源时间与 step 时间的差值 |
| `neighbor_before_time_ns` | integer/null | 插值前邻居时间 |
| `neighbor_after_time_ns` | integer/null | 插值后邻居时间 |
| `window_start_time_ns` | integer/null | 聚合窗口开始时间 |
| `window_end_time_ns` | integer/null | 聚合窗口结束时间 |
| `sample_count` | integer/null | 聚合或匹配使用的样本数 |
| `coverage_ratio` | number/null | 聚合窗口覆盖率 |
| `fallback_reason` | string/null | fallback 原因 |
| `message_ref` | string/null | 对齐输出消息引用或定位信息 |

## 有效性规则

- 每个 `step_index + field_name` 最多一条主记录。
- 图像、位姿、触觉、夹爪字段都必须能用 `status` 表达结果。
- `AlignmentIndex` 是场景四构建 step index 和 masks 的主要输入之一。
- `AlignmentIndex` 不嵌入完整图像、完整位姿序列或触觉矩阵。

## 上游来源

- [[StepTimeline]]。
- [[TargetFieldMapping]]。
- 多策略字段对齐器。

## 下游消费者

- 对齐索引与报告数据生成器。
- aligned MCAP 与 sidecar 写出器。
- 场景四 LeRobotDataset v3 构建、masks 和 quality report。

## 不负责

- 不保存主数据 payload。
- 不替代 [[AlignmentReport]] 汇总统计。
- 不决定训练样本是否可用。

## 相关链接

- [[StepTimeline]]
- [[FieldAlignmentStatus]]
- [[AlignmentReport]]
- [[AlignedMcap]]
