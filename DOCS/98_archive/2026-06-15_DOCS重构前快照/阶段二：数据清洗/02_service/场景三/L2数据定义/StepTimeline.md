# StepTimeline

## 定义

`StepTimeline` 是场景三按统一目标频率生成的 step 时间戳序列。

## 所属位置

阶段二 Service 场景三，来源能力模块：[[对齐契约与配置定义]]。

## 现实语义

它是所有字段对齐的共同参考时间轴。首版以左右图像共同有效时间范围为起止范围，在该区间内按 `target_step_hz=15` 默认生成均匀 step。

## 字段或取值

| 字段 | 类型 | 现实含义 |
|---|---|---|
| `timeline_id` | string | 本次时间轴标识 |
| `target_step_hz` | number | 默认 `15` |
| `start_time_ns` | integer | 左右图像共同有效区间开始时间 |
| `end_time_ns` | integer | 左右图像共同有效区间结束时间 |
| `step_count` | integer | 生成的 step 数 |
| `step_index` | integer | 从 0 开始的 step 序号 |
| `step_time_ns` | integer | 当前 step 的统一时间戳 |
| `range_policy` | enum string | 固定默认 `required_field_intersection` |
| `baseline_policy` | enum string | 固定默认 `stereo_image_intersection` |

## 有效性规则

- 首版只有左右图像字段参与 `start_time_ns` / `end_time_ns` 交集裁剪。
- 可选 topic 不参与时间范围裁剪。
- 在时间范围内生成的 step 即使某些字段超时，也不由场景三删除。
- 如果左右图像无共同有效区间，时间轴生成失败。

## 上游来源

- [[Scene3AlignmentConfig]]。
- MCAP_A 输入盘点与校验器输出的 topic 时间范围。

## 下游消费者

- 多策略字段对齐器。
- 对齐索引与报告数据生成器。
- aligned MCAP 与 sidecar 写出器。

## 不负责

- 不保存字段值。
- 不判断训练可用性。
- 不表达 episode 或 action 语义。

## 相关链接

- [[Scene3AlignmentConfig]]
- [[TargetFieldMapping]]
- [[AlignmentIndex]]
