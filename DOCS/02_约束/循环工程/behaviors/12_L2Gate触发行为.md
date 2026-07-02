# L2 Gate 触发行为

## 消费 Agent

- 主 Agent

## 本文职责

本文只约束主 Agent 何时可以启动 L2 Gate agent。

## 不负责

本文不执行 L2 Gate 汇总、不生成 L2 验收报告、不合入 `model_deploy`。

## 触发条件

目标 L2 的 required L3 必须全部处于以下状态之一：

- `committed`
- `synced`
- 可解释 `BLOCKED_ENV`
- 可解释 `BLOCKED_HARDWARE_EXPECTED`
- 可由 L2 Gate 覆盖的 `DEFER_TO_L2_GATE`

## 派发内容

启动 L2 Gate agent 时，只提供：

- `DOCS/02_约束/循环工程/04_L2Gate行为约束.md`
- `DOCS/02_约束/循环工程/behaviors/15_L2Gate汇总行为.md`
- 目标 L2 dispatch
- 目标 L2 整体验收卡片
- 目标 L2 `验收结果.md`
- 目标 L2 L3 验收日志
- Git 和硬件 blocked 状态

## 禁止事项

- 禁止 required L3 未可解释完成时启动 Gate。
- 禁止 Gate 未通过时进入依赖它的下游 L2。

