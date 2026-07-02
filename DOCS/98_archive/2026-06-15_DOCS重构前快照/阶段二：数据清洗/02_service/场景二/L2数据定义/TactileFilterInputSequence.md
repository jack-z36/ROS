# TactileFilterInputSequence

## 定义

`TactileFilterInputSequence` 是触觉滤波器从 [[SignalRepairResult]] 中解释出的单 topic 补全后触觉序列语义接口。

## 所属位置

阶段二 Service 场景二，来源能力模块：[[触觉滤波器]]。

## 现实语义

它用于隔离 `SignalRepairResult.output_sequence_refs` 的物理 artifact 格式不稳定问题，让触觉滤波器只依赖稳定的触觉序列语义。

## 字段或取值

| 字段 | 类型 | 现实含义 |
|---|---|---|
| `sequence_id` | string | 输入序列 id |
| `source_topic` | string | 来源触觉 topic |
| `modality` | enum string | 固定 `tactile` |
| `time_domain` | enum string | `log_time` / `publish_time` / `header_stamp` |
| `frames` | list[[TactilePressureFrame]] / ref | 补全后的触觉帧序列或其引用 |
| `source_repair_result_ref` | string / [[SignalRepairResult]] | 来源补全结果 |
| `source_sequence_ref` | string/null | `output_sequence_refs` 中对应触觉序列引用 |
| `sample_count` | integer | 样本数 |
| `rows` | integer | 矩阵行数 |
| `cols` | integer | 矩阵列数 |

## 有效性规则

- `modality` 必须为 `tactile`。
- `sample_count` 必须等于 `frames` 可解析样本数。
- 每帧必须满足 `rows * cols == len(data)`；否则本序列不可滤波并进入错误记录。
- 同一序列内 shape 必须一致；shape 变化不得被静默滤波。
- `timestamp_policy` 由 [[SignalRepairResult]] 和 [[TactileFilterResult]] 固定为 `preserve_original`。

## 上游来源

- [[SignalRepairResult]]
- [[TactilePressureFrame]]
- [[数据补全器]]

## 下游消费者

- [[TactileFilterSegmentSummary]]
- [[TactileFilterSampleRecord]]
- [[TactileFilterResult]]

## 不负责

- 不承诺 `output_sequence_refs` 的文件格式。
- 不包含完整滤波结果。
- 不定义触觉接触类别或语义标签。

## 当前未知问题

| 问题 | 当前处理 |
|---|---|
| `output_sequence_refs` 的正式 artifact 格式 | 本对象只固化语义接口，具体读取由 L3 对齐上游实现 |

## 相关链接

- [[SignalRepairResult]]
- [[TactilePressureFrame]]
- [[触觉滤波器]]
