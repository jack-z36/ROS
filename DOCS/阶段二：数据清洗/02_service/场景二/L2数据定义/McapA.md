# McapA

## 定义

`McapA` 是场景二 P0 预处理链路写出的主数据 MCAP，文档和人工讨论中也称为 `MCAP_A`。

## 所属位置

阶段二 Service 场景二，来源能力模块：MCAP_A 生成器。

## 现实语义

它承载经过异常检测、可修复异常补全、位姿滤波和触觉滤波后的训练语义主数据，是场景三时间轴对齐的直接输入之一。

## 字段或取值

| 内容 | 契约 |
|---|---|
| 来源 | [[CleanedMcap]] |
| 位姿 topic | 保留 cleaned MCAP 的 topic 结构，写入补全/滤波后的位姿值 |
| 触觉 topic | 保留 cleaned MCAP 的触觉 topic 结构，写入补全/滤波后的触觉值 |
| 夹爪 topic | 保留 cleaned MCAP 的夹爪 topic 结构，必要时写入补全后的夹爪值 |
| 时间结构 | 不改变 topic 名称和时间戳结构 |
| 追溯信息 | 通过问题记录、修复日志和验证报告追溯修改原因 |

## 有效性规则

- 不保存关节角序列；关节角属于后续 MCAP_B 诊断产物。
- 不静默删除异常片段；不可修复问题必须继续进入标注或报告。
- 若修改任何序列值，必须能追溯到 [[SignalReliabilityIssue]]、修复策略或滤波摘要。

## 上游来源

- [[SignalReliabilityIssue]]
- 数据补全器
- 位姿滤波器
- 触觉滤波器

## 下游消费者

- IK 求解与 MCAP_B 生成器。
- 场景三时间轴对齐。
- Parquet 标注与验证报告生成器。

## 不负责

- 不负责保存 IK、关节限制或 MuJoCo 诊断结果。
- 不负责生成 canonical dataset、episode 或 step index。
- 不负责决定最终训练 mask。

## 当前未知问题

| 问题 | 当前处理 |
|---|---|
| 正式文件名、默认落点和与 `dev/mcap_validated/` 的对应关系 | 由 MCAP_A 生成器 L2 固化 |
| 是否长期保留 `ValidatedMcap` 作为别名 | 暂时以 `McapA` 作为场景二主数据原子定义 |

## 相关链接

- [[CleanedMcap]]
- [[SignalReliabilityIssue]]
- [[TactilePressureFrame]]

