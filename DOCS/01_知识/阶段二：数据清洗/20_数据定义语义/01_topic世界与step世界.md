# topic 世界与 step 世界

## topic 世界

raw MCAP、cleaned MCAP、MCAP_A 和 aligned MCAP 都属于 MCAP / ROS2 topic 世界。它们按 topic 存放消息，每个 topic 有自己的频率、时间戳、schema 和可用性状态。

topic 世界的核心问题是：图像、位姿、触觉和夹爪宽度不天然对齐，也不天然拥有训练框架需要的 step 结构。

## step 世界

训练数据需要按统一 step 组织：

```text
step_t = observation_t + action_t
```

阶段二的关键工作是把多 topic 原始日志逐步整理为可解释、可验证、可追溯的 step 级语义。

## observation / action

`observation` 表示当前 step 的观测状态，当前主要来自双目图像、双臂 TCP pose、夹爪宽度和触觉统计。

`action` 表示训练侧消费的动作目标。当前阶段二 action 语义是下一 step 的双臂绝对 TCP 目标和可选夹爪目标；差分或相对化属于训练侧策略，不在阶段二内强行改写。

## 对 L2/L3 的影响

生成阶段二 L2 能力模块或数据定义时，应先判断概念属于 topic 世界、step 世界还是 LeRobotDataset v3 世界。不要把三套语义混在一个字段定义里。

## 详细内容

- 场景三对齐源码类型：`src/data_clean/schemas/step_timeline.py`
- 字段对齐源码类型：`src/data_clean/schemas/field_alignment.py`
- aligned MCAP 报告类型：`src/data_clean/schemas/aligned_mcap_report.py`
