# SignalRepairResult

## 定义

`SignalRepairResult` 是数据补全器一次运行的聚合输出对象。

## 所属位置

阶段二 Service 场景二，来源能力模块：[[数据补全器]]。

## 现实语义

它回答“哪些异常样本被自动修复、哪些拒绝修复、哪些缺失区间没有处理、修复后序列在哪里”。它是追溯记录，不是完整数据容器。

## 字段或取值

| 字段 | 类型 | 现实含义 |
|---|---|---|
| `input_detection_result_ref` | string / [[SignalReliabilityDetectionResult]] | 输入异常检测结果引用 |
| `repair_policy_config_ref` | string / [[SignalRepairPolicyConfig]] | 本次修复策略配置引用 |
| `repair_runs` | list[[SignalRepairRun]] | run 级补全决策记录 |
| `unhandled_missing_interval_records` | list[object] | v1 未插消息的缺失区间记录 |
| `output_sequence_refs` | object/list | 修复后序列 artifact 或内存引用 |
| `timestamp_policy` | enum string | 固定 `preserve_original` |
| `sample_count_before` | object | 各 topic 输入样本数 |
| `sample_count_after` | object | 各 topic 输出样本数 |
| `summary_by_modality` | object | 按三模态汇总 repaired/unrepaired/skipped |
| `created_at` | string/null | 结果创建时间 |
| `run_id` | string/null | 所属 run id |

## 有效性规则

- `timestamp_policy` 必须为 `preserve_original`。
- 每个 topic 必须满足 `sample_count_before == sample_count_after`。
- 不得在本对象中塞入完整三模态序列。
- `output_sequence_refs` 只能引用修复后序列 artifact 或内存对象。
- 所有未处理的 [[MissingIntervalIssue]] 必须可追溯记录。

## 上游来源

- [[SignalReliabilityDetectionResult]]
- [[SignalRepairPolicyConfig]]
- [[数据补全器]]

## 下游消费者

- 位姿滤波器。
- 触觉滤波器。
- MCAP_A 生成器。
- Parquet 标注与验证报告生成器。
- 开发者功能检验项 `scene2_signal_repair`。

## 不负责

- 不重新发现异常。
- 不负责滤波。
- 不负责写 MCAP_A。
- 不负责场景三时间轴对齐。

## 相关链接

- [[SignalRepairRun]]
- [[SignalRepairSampleRecord]]
- [[RepairDecisionStatus]]
- [[RepairMethod]]
