# TactilePressureFrame

## 定义

`TactilePressureFrame` 是场景二从 cleaned MCAP 中读取的单帧触觉压力矩阵语义对象，来源于 `hwk_pressure_interfaces/msg/PressureFrame`。

## 所属位置

阶段二 Service 场景二，首个消费能力模块：[[异常值检测器]]。

## 现实语义

它对应 4 路触觉 topic 的一帧压力读数：

- `/pressure/left_hand/gripper_1`
- `/pressure/left_hand/gripper_2`
- `/pressure/right_hand/gripper_1`
- `/pressure/right_hand/gripper_2`

## 字段或取值

| 字段 | 类型 | 现实含义 |
|---|---|---|
| `topic` | string | 来源触觉 topic |
| `log_time` | integer | MCAP log time |
| `publish_time` | integer | MCAP publish time |
| `hand` | string | `left_hand` 或 `right_hand` |
| `gripper` | string | `gripper_1` 或 `gripper_2` |
| `rows` | integer | 压力矩阵行数 |
| `cols` | integer | 压力矩阵列数 |
| `data` | list[integer] | row-major 展平后的 `uint16` 压力矩阵 |
| `raw_payload` | bytes/list[integer] | 原始 payload，仅用于排障追溯 |

## 有效性规则

- `rows` 和 `cols` 必须大于 0。
- `len(data)` 应等于 `rows * cols`；不一致时不静默修复，必须生成 [[SignalReliabilityIssue]]。
- 默认硬件配置预期矩阵尺寸为 `6x15`；实际判定以 cleaned MCAP 中的消息和配置为准。
- `raw_payload` 不能替代 `data` 成为业务检测入口。

## 上游来源

- 场景一 cleaned MCAP 保留的 `hwk_pressure_interfaces/msg/PressureFrame` topic。
- 阶段一触觉驱动 `hwk_pressure_driver`。

## 下游消费者

- [[异常值检测器]]
- 数据补全器
- 触觉滤波器
- Parquet 标注与验证报告生成器

## 不负责

- 不负责定义触觉滤波后的新 topic。
- 不负责解释压力值的物理单位或接触语义。
- 不负责决定异常片段是否进入训练 mask。

## 当前未知问题

| 问题 | 当前处理 |
|---|---|
| 压力值的物理单位和绝对合理范围 | v1 只做结构、缺失、突变、饱和和全零类检测；物理阈值保留为配置项 |
| 触觉真实接触变化与异常尖峰的区分阈值 | 写入 [[ReliabilityCheckRuleConfig]]，后续通过真实数据调参 |

## 相关链接

- [[SignalReliabilityIssue]]
- [[IssueTimeSegment]]
- [[IssueEvidence]]

