# TargetFieldMapping

## 定义

`TargetFieldMapping` 是场景三把 MCAP_A topic 映射到对齐输出字段的配置条目。

## 所属位置

阶段二 Service 场景三，来源能力模块：[[对齐契约与配置定义]]。

## 现实语义

它说明每个要对齐的字段来自哪个 MCAP_A topic、属于哪种模态、是否参与时间轴裁剪，以及默认使用什么对齐策略。

## 字段或取值

| 字段 | 类型 | 现实含义 |
|---|---|---|
| `field_name` | string | 字段语义名，例如 `image_left`、`tcp_pose_right` |
| `source_topic` | string | MCAP_A 中的来源 topic |
| `output_topic` | string | aligned MCAP 中的输出 topic，首版默认保留语义 topic 名 |
| `message_type` | string | ROS 消息类型 |
| `modality` | enum string | `image` / `pose` / `tactile` / `gripper` |
| `side` | enum string/null | `left` / `right` / null |
| `required_for_timeline` | bool | 是否参与 step 时间轴起止裁剪 |
| `strategy` | [[FieldAlignmentStrategy]] | 字段默认对齐策略 |
| `max_dt_ms` | number/null | 最近邻或插值允许的时间阈值 |

## 有效性规则

- 首版左右图像字段 `required_for_timeline=true`。
- 首版位姿、触觉、夹爪字段 `required_for_timeline=false`。
- 图像字段不允许插值。
- aligned MCAP 首版不提前改成 canonical observation topic；输出 topic 保留语义 topic 名。

## 上游来源

- [[McapA]] 的 topic 结构。
- [[Scene3AlignmentConfig]]。
- 场景一图像、位姿和夹爪 topic 契约。

## 下游消费者

- MCAP_A 输入盘点与校验器。
- 统一 Step 时间轴生成器。
- 多策略字段对齐器。
- [[AlignmentIndex]]。

## 不负责

- 不保存具体样本值。
- 不表达 step 级对齐结果。
- 不定义场景四 canonical 字段 schema。

## 相关链接

- [[Scene3AlignmentConfig]]
- [[FieldAlignmentStrategy]]
- [[AlignmentIndex]]
