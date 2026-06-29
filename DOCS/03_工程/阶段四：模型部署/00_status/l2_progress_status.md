# L2 进度状态摘要

## 消费 Agent

- 主 Agent
- L2 Gate agent

## 本文职责

本文只汇总阶段四各 L2 的 Gate、阻塞和下游放行状态，作为循环恢复摘要。

## 不负责

本文不替代各 L2 的 `验收结果.md`、`L2整体验收报告.md`、dispatch 或验收日志。

## 当前 L2 状态

| L2 | L2 分支 | Gate 状态 | 下游放行 | 备注 |
|---|---|---|---|---|
| l2-01-types | `model_deploy-l2-01-types` | PASS | 允许 L2-02 | 以 `05_acceptance/l2-01-types/验收结果.md` 为准 |
| l2-02-config | `model_deploy-l2-02-config` | PASS | 允许 L2-03 | 以 `05_acceptance/l2-02-config/验收结果.md` 为准 |
| l2-03-assembly | `model_deploy-l2-03-assembly` | 未通过 | 不允许 L2-04 | required L3 待执行或待验收 |
| l2-04-publish | `model_deploy-l2-04-publish` | 未通过 | 不允许 L2-05 | 依赖 L2-03 Gate |
| l2-05-hardware | `model_deploy-l2-05-hardware` | 未通过 | 不适用 | 当前无真机循环最多推进到 deploy_022 |

## 维护规则

- Gate 状态必须能追溯到对应 `05_acceptance/<l2>/验收结果.md`。
- 本表只是摘要；若与验收结果冲突，以验收结果为准。

