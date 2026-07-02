# PoseFilterResult

## 定义

`PoseFilterResult` 是位姿滤波器一次运行的聚合输出对象。

## 所属位置

阶段二 Service 场景二，来源能力模块：[[位姿滤波器]]。

## 现实语义

它回答“这次对哪些补全后 pose 序列做了滤波、使用了什么参数、哪些样本被修改、哪些样本因边界或 guard 保留原值、滤波后序列在哪里”。

## 字段或取值

| 字段 | 类型 | 现实含义 |
|---|---|---|
| `input_repair_result_ref` | string / [[SignalRepairResult]] | 来源数据补全结果引用 |
| `pose_filter_config_ref` | string / [[PoseFilterConfig]] | 本次滤波配置引用 |
| `input_sequence_refs` | list[[PoseFilterInputSequence]] / list[string] | 输入 pose 序列引用 |
| `output_sequence_refs` | object/list | 滤波后 pose 序列 artifact 或内存引用 |
| `segment_summaries` | list[[PoseFilterSegmentSummary]] | 分段和窗口换算摘要 |
| `sample_records` | list[[PoseFilterSampleRecord]] | 样本级滤波审计 |
| `timestamp_policy` | enum string | 固定 `preserve_original` |
| `sample_count_before` | object | 各 pose topic 输入样本数 |
| `sample_count_after` | object | 各 pose topic 输出样本数 |
| `summary_by_topic` | object | 按 topic 汇总 filtered/kept/rejected/skipped |
| `created_at` | string/null | 结果创建时间 |
| `run_id` | string/null | 所属 run id |

## 有效性规则

- `timestamp_policy` 必须为 `preserve_original`。
- 每个 pose topic 必须满足 `sample_count_before == sample_count_after`。
- 不得在本对象中塞入完整 MCAP。
- 修改任何样本值时，必须能追溯到 [[PoseFilterSampleRecord]]。
- 任何 guard 拒绝必须保留候选滤波值和拒绝原因。

## 上游来源

- [[SignalRepairResult]]
- [[PoseFilterInputSequence]]
- [[PoseFilterConfig]]

## 下游消费者

- [[McapA|MCAP_A]] 生成器。
- Parquet 标注与验证报告生成器。
- 开发者功能检验项 `scene2_pose_filter`。

## 不负责

- 不写 MCAP_A。
- 不处理触觉或夹爪滤波。
- 不决定最终训练 mask。
- 不执行 IK、关节限制或 MuJoCo 仿真。

## 当前未知问题

| 问题 | 当前处理 |
|---|---|
| 滤波后序列 artifact 的正式文件格式 | v1 与补全器 `output_sequence_refs` 语义保持一致，由实现 L3 固化 |
| 是否在生产模式保存完整 `sample_records` | v1 开发者检验完整保存，生产压缩策略后续确认 |

## 相关链接

- [[PoseFilterConfig]]
- [[PoseFilterInputSequence]]
- [[PoseFilterSampleRecord]]
- [[PoseFilterSegmentSummary]]
- [[SignalRepairResult]]
- [[McapA]]
