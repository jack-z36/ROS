# Scene3AlignmentConfig

## 定义

`Scene3AlignmentConfig` 是场景三 MCAP 多 topic 时间轴对齐使用的配置对象。

## 所属位置

阶段二 Service 场景三，来源能力模块：[[对齐契约与配置定义]]。

## 现实语义

它回答“场景三以哪些 topic 生成统一 step 时间轴、目标频率是多少、各字段采用什么对齐策略、阈值和输出路径如何确定”。

## 字段或取值

| 字段 | 类型 | 现实含义 |
|---|---|---|
| `input_mcap_a` | string / [[McapA]] | 场景二输出的 MCAP_A 输入路径 |
| `mcap_a_write_summary` | string / [[McapAWriteSummary]] | 上游 MCAP_A 写出摘要路径 |
| `target_step_hz` | number | 默认 `15`，统一 step 时间轴目标频率 |
| `baseline_image_topics` | list[string] | 默认 `[/gopro_left/image_raw, /gopro_right/image_raw]` |
| `required_timeline_fields` | list[string] | 默认只包含左右图像字段 |
| `target_fields` | list[[TargetFieldMapping]] | 需要投影到 step 的字段映射 |
| `image_max_dt_ms` | number/null | 默认 `1000 / target_step_hz / 2`，可配置覆盖 |
| `pose_strategy` | enum string | 默认 `interpolation_slerp` |
| `pose_fallback_strategy` | enum string | 默认 `nearest_neighbor` |
| `tactile_strategy` | enum string | 默认 `window_aggregate` |
| `gripper_strategy` | enum string | 默认 `follow_image_nearest` |
| `output_dir` | string | 默认 `asset/阶段二：数据清洗/dev/03_aligned_mcap/` |
| `allow_cli_override` | bool | 开发者入口是否允许本次运行临时覆盖配置 |

## 有效性规则

- `target_step_hz` 必须大于 0。
- `baseline_image_topics` 首版必须同时包含左右图像 topic。
- 首版只有左右图像参与时间范围裁剪；位姿、触觉和夹爪不参与裁剪。
- 默认 `image_max_dt_ms` 由 `target_step_hz` 推导；显式配置值必须大于 0。
- CLI 临时覆盖只对本次运行生效，不默认写回配置文件。

## 上游来源

- 场景二 [[McapA]] 和 [[McapAWriteSummary]]。
- 场景三对齐契约与配置定义。
- 开发者入口的本次运行临时覆盖。

## 下游消费者

- MCAP_A 输入盘点与校验器。
- 统一 Step 时间轴生成器。
- 多策略字段对齐器。
- 对齐索引与报告数据生成器。
- aligned MCAP 与 sidecar 写出器。

## 不负责

- 不保存实际对齐结果。
- 不保存 MCAP 消息内容。
- 不决定训练 mask、episode 构建或 canonical dataset schema。

## 当前未知问题

| 问题 | 当前处理 |
|---|---|
| 正式配置文件名和 schema 文件名 | 后续 L3 按代码目录结构落定 |

## 相关链接

- [[McapA]]
- [[McapAWriteSummary]]
- [[TargetFieldMapping]]
- [[StepTimeline]]
- [[FieldAlignmentStrategy]]
- [[AlignedMcap]]
