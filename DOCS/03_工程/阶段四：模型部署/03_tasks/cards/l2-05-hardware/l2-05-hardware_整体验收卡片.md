# L2 整体验收卡片：L2-05 硬件执行栈

## 基本信息

| 字段 | 内容 |
|---|---|
| L2 | L2-05 硬件执行栈 |
| L2 分支 | `model_deploy-l2-05-hardware` |
| 验收卡片目录 | `DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-05-hardware` |
| L2 验收结果 | `DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-05-hardware/验收结果.md` |
| L2 整体报告 | `DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-05-hardware/L2整体验收报告.md` |
| 运行验收重点 | bridge、IK、width 映射、真机 smoke test 阻断条件 |

## Required L3 与验收卡片

| L3 | 验收模式 | 验收卡片 | 反馈状态 |
|---|---|---|---|
| deploy_017 command_bridge_sender_node 骨架 | `direct-local` | `DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-05-hardware/deploy_017_验收卡片.md` | 待汇总 |
| deploy_018 bridge 接入 IK 预检 + workspace 检查 | `static-review + hardware-blocked` | `DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-05-hardware/deploy_018_验收卡片.md` | 待汇总 |
| deploy_019 bridge width→angle 映射 + mode/gate 控制 | `direct-local` | `DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-05-hardware/deploy_019_验收卡片.md` | 待汇总 |
| deploy_020 rm65_driver_node（状态发布 + 命令执行） | `static-review + hardware-blocked` | `DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-05-hardware/deploy_020_验收卡片.md` | 待汇总 |
| deploy_021 elephant_gripper_node（状态发布 + 命令执行 + 标定） | `static-review + hardware-blocked` | `DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-05-hardware/deploy_021_验收卡片.md` | 待汇总 |
| deploy_022 新 launch + shadow-run 全链路验证 | `direct-local + env-blocked` | `DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-05-hardware/deploy_022_验收卡片.md` | 待汇总 |
| deploy_023 real-robot smoke test（safe-run + 急停） | `hardware-blocked` | `DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-05-hardware/deploy_023_验收卡片.md` | 待汇总 |

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
