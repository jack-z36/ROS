# FieldAlignmentStatus

## 定义

`FieldAlignmentStatus` 是场景三逐 step-field 对齐结果的状态枚举。

## 所属位置

阶段二 Service 场景三，来源能力模块：[[对齐契约与配置定义]]。

## 现实语义

它让下游区分某个字段在某个 step 上是正常对齐、插值、聚合、fallback，还是缺失、超时或输入无效。

## 字段或取值

| 取值 | 现实含义 |
|---|---|
| `aligned` | 字段按默认策略正常对齐 |
| `interpolated` | 字段通过插值得到 |
| `aggregated` | 字段通过窗口聚合得到 |
| `fallback_nearest` | 默认策略不可用，按配置 fallback 到最近邻 |
| `missing_time` | 对应时间窗口没有可用样本 |
| `timeout` | 找到样本但时间误差超过阈值 |
| `unavailable` | 字段或 topic 不可用 |
| `invalid_input` | 来源消息、配置或上游摘要无效 |

## 有效性规则

- `status` 不替代 `alignment_method`；两者必须可同时记录。
- fallback 情况必须填写 `fallback_reason`。
- 图像必需字段超时不删除 step，只记录 `timeout`。
- 可选字段缺失不裁剪时间轴，只记录 `missing_time` 或 `unavailable`。

## 上游来源

- [[FieldAlignmentStrategy]]。
- 多策略字段对齐器。

## 下游消费者

- [[AlignmentIndex]]。
- [[AlignmentReport]]。
- 场景四 masks 和 quality report。

## 不负责

- 不定义严重程度。
- 不定义训练 mask 类型。
- 不决定整段 episode 是否丢弃。

## 相关链接

- [[FieldAlignmentStrategy]]
- [[AlignmentIndex]]
