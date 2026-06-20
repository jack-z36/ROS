# L2 整体验收卡片：L2-02 Config 层重构

## 基本信息

| 字段 | 内容 |
|---|---|
| L2 | L2-02 Config 层重构 |
| L2 分支 | `model_deploy-l2-02-config` |
| 验收卡片目录 | `DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-02-config` |
| L2 验收结果 | `DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-02-config/验收结果.md` |
| L2 整体报告 | `DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-02-config/L2整体验收报告.md` |
| 运行验收重点 | 配置加载、默认值、非法配置失败 |

## Required L3 与验收卡片

| L3 | 验收模式 | 验收卡片 | 反馈状态 |
|---|---|---|---|
| deploy_005 重构 observation topic 字段为鱼眼/TCP/gripper | `direct-local` | `DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-02-config/deploy_005_验收卡片.md` | 待汇总 |
| deploy_006 command topic 重构 + 删除 Bridge/Mux config | `direct-local` | `DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-02-config/deploy_006_验收卡片.md` | 待汇总 |
| deploy_007 RuntimeConfig 默认维度 + SafetyConfig 重构 | `direct-local` | `DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-02-config/deploy_007_验收卡片.md` | 待汇总 |
| deploy_008 deploy.yaml 更新 + Config 层单测 | `direct-local` | `DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-02-config/deploy_008_验收卡片.md` | 待汇总 |

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
