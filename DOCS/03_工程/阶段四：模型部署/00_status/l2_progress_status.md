# L2 进度状态摘要

## 消费 Agent

- 主 Agent
- L2 Gate agent

## 本文职责

本文只汇总阶段四各 L2 的 Gate、人类验收、阻塞和下游放行状态，作为循环恢复摘要。

## 不负责

本文不替代各 L2 的 `验收结果.md`、`L2整体验收报告.md`、`人类验收清单.md`、dispatch 或验收日志。

## 当前 L2 状态

> [!warning] 2026-07-03 重置说明
> 原 Pi0.5 版 L2/L3 已归档（`03_tasks/_archived_pi05/`）。第一版切换为 ACT，5 个 L2 全部针对 ACT 从零重写，进度全部重置为「未开始」。原表中 l2-01/l2-02 的 PASS 记录是基于 Pi0.5 改造的乐观记录，代码实际未落地（当前代码仍是原始 Pi0.5 26D/14D），作废。

| L2 | L2 文档 | 三级分支 | Gate 状态 | 人类验收 | 下游放行 | 备注 |
|---|---|---|---|---|---|---|
| l2-01-types | [[L2-01-ACT Types层]] | `feat/model_deploy/l2-01-types` | 未开始 | 未开始 | 允许 L2-02 | ACT Types 16D 地基 |
| l2-02-config | [[L2-02-ACT Config层]] | `feat/model_deploy/l2-02-config` | 未开始 | 未开始 | 允许 L2-03 | ACT Config（/act/* topic、dim 16） |
| l2-03-assembly | [[L2-03-ACT数据装配与模型加载]] | `feat/model_deploy/l2-03-assembly` | 未开始 | 未开始 | 不允许 L2-04 | ACT policy_loader + observation_collector；依赖 ACT bundle |
| l2-04-publish | [[L2-04-ACT action处理与发布]] | `feat/model_deploy/l2-04-publish` | 未开始 | 未开始 | 不允许 L2-05 | ACT 推理发布链路；依赖 L2-03 |
| l2-05-hardware | [[L2-05-ACT硬件执行栈]] | `feat/model_deploy/l2-05-hardware` | 未开始 | 未开始 | 不适用 | 硬件栈；最高风险，真机验收默认 blocked |

## 验收与合入流程

每个 L2 必须依次通过：
1. **L2 Gate（AI 侧自动化）**：产出 `05_acceptance/<l2>/验收结果.md` 和 `L2整体验收报告.md`。
2. **人类验收关卡**：用户按 `05_acceptance/<l2>/人类验收清单.md` 亲自运行测试并签字。

只有两者都通过，才允许执行 Gate 后合入流程（merge --no-ff 到 model_deploy + 删三级分支）。规则见 `DOCS/02_约束/工作流/阶段四开发工作流/attachments/人类验收关卡规则.md`。

## 维护规则

- Gate 状态必须能追溯到对应 `05_acceptance/<l2>/验收结果.md`。
- 人类验收签字必须在该文件的「人类验收」段，含勾选通过 + 用户名 + 日期。
- 本表只是摘要；若与验收结果冲突，以验收结果为准。
