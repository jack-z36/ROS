# L2 整体验收卡片：L2-04 action 处理与发布层

## 基本信息

| 字段 | 内容 |
|---|---|
| L2 | L2-04 action 处理与发布层 |
| L2 分支 | `model_deploy-l2-04-publish` |
| 验收卡片目录 | `DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-04-publish` |
| L2 验收结果 | `DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-04-publish/验收结果.md` |
| L2 整体报告 | `DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-04-publish/L2整体验收报告.md` |
| 运行验收重点 | safety guard、policy_action、metrics、sent_to_driver=false |

## Required L3 与验收卡片

| L3 | 验收模式 | 验收卡片 | 反馈状态 |
|---|---|---|---|
| deploy_013 safety_guard 改造为 policy-action 通用检查 | `direct-local` | `DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-04-publish/deploy_013_验收卡片.md` | 待汇总 |
| deploy_014 deploy_node 发布侧改造 | `static-review + downstream-l2` | `DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-04-publish/deploy_014_验收卡片.md` | 待汇总 |
| deploy_015 _publish_metrics 字段增强 | `static-review + downstream-l2` | `DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-04-publish/deploy_015_验收卡片.md` | 待汇总 |
| deploy_016 L2-04 单测与 shadow-run 验证 | `direct-local + env-blocked` | `DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-04-publish/deploy_016_验收卡片.md` | 待汇总 |

## L2 整体验收步骤

1. 读取本 L2 dispatch 索引，确认 required L3 全部完成或 blocked 原因清楚。
2. 读取每张 L3 验收卡片和对应反馈报告。
3. 汇总 L2 运行场景 S1/S2/... 的覆盖情况。
4. 区分 PASS_LOCAL、DEFER_TO_L2_GATE、BLOCKED_ENV、BLOCKED_HARDWARE_EXPECTED。
5. 生成 `L2整体验收报告.md`，并回填 `验收结果.md` 的 Gate 结论。

## 报告必须包含

- L3 验收反馈链接。
- L2 运行场景覆盖表。
- Ubuntu 22.04 无硬件条件下已验证项。
- 环境 blocked 项。
- 硬件 blocked 项和解除条件。
- 是否允许进入下一个 L2。
- 是否允许触发 L2 Git 自动同步。

## 结论规则

- 存在 `FAIL_LOCAL` 且未修复：L2 Gate 不通过。
- 存在 `BLOCKED_ENV`：L2 Gate 由主 Agent 判断是否可暂缓，不得自动宣称通过。
- 存在预期 `BLOCKED_HARDWARE_EXPECTED`：可以作为无硬件环境下的受限通过，但报告必须写明未做真机验收。
- L2-05 不得在无硬件环境下宣称 real-robot smoke test 通过。
