# McapAWriteConfig

## 定义

`McapAWriteConfig` 是 MCAP_A 生成器一次写出动作使用的配置对象。

## 所属位置

阶段二 Service 场景二，来源能力模块：[[MCAP_A生成器]]。

## 现实语义

它回答“MCAP_A 写到哪里、如何命名、哪些上游结果是必需的、如何处理 topic 替换和失败”。它不是运行结果，也不保存实际 MCAP 消息。

## 字段或取值

| 字段 | 类型 | 现实含义 |
|---|---|---|
| `output_dir` | string | 默认 `asset/阶段二：数据清洗/dev/mcap_validated/` |
| `filename_policy` | enum string | 默认 `derive_from_cleaned_stem` |
| `filename_suffix` | string | 默认 `_mcap_a.mcap` |
| `topic_policy` | enum string | 固定 `preserve_cleaned_topics` |
| `strict_required_inputs` | bool | 默认 `true`，缺少必需上游结果则失败 |
| `write_summary_sidecar` | bool | 默认 `true`，写出 [[McapAWriteSummary]] |
| `scene2_streams` | list[object] | 生产配置只读白名单；每项包含 `topic`、`modality`、`required`，单任务不可扩张 |
| `allow_overwrite` | bool | 默认 `false`，避免覆盖已有 validated 产物 |
| `temp_file_suffix` | string | 写出半成品临时后缀，例如 `.tmp` |

## 有效性规则

- `topic_policy` 首版只允许 `preserve_cleaned_topics`。
- `strict_required_inputs` 首版必须为 `true`。
- 默认输出目录必须位于 `asset/阶段二：数据清洗/dev/mcap_validated/`，开发者功能检验可临时覆盖到独立 run 输出目录。
- 默认不得覆盖已有 MCAP_A；如实现允许覆盖，必须显式配置并写入运行日志。
- 配置不得要求写入 processed topic、audit topic 或 MCAP metadata 审计块。
- 2 路 `/baton_mini_*/tcp_pose` 和 2 路 `/gopro_*/gripper_width` 必需；4 路 `/pressure/...` tactile 默认可选。

## 上游来源

- MCAP_A 生成器 L2。
- 开发者入口 `scene2_mcap_a_writer` 的临时覆盖。

## 下游消费者

- MCAP_A 生成器。
- 开发者功能检验项 `scene2_mcap_a_writer`。
- L3 `service_s2_018` 和 `service_s2_020`。

## 不负责

- 不保存 [[McapA]] 文件内容。
- 不保存 [[McapAWriteSummary]] 结果统计。
- 不决定场景三、场景四或训练导出策略。

## 相关链接

- [[McapA]]
- [[McapAWriteSummary]]
- [[SignalRepairResult]]
- [[PoseFilterResult]]
- [[TactileFilterResult]]
