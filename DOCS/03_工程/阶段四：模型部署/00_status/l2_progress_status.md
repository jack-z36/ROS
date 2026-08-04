# L2 进度状态摘要

## 消费 Agent

- 主 Agent
- L2 Gate agent

## 本文职责

本文只汇总阶段四各 L2 的 Gate、人类验收、阻塞和下游放行状态，作为循环恢复摘要。

## 不负责

本文不替代各 L2 的 `验收结果.md`、`L2整体验收报告.md`、`人类验收清单.md`、dispatch 或验收日志。

## 当前 L2 状态

> [!warning] 2026-07-07 修正说明
> 阶段四 ACT 第一版主线已修正为“6 个运行时功能闭环 L2”。独立 `l2-04-action-smoothing` 从第一版移除，action 平滑降级为后续优化方向。旧 `l2-01-types`、`l2-02-config`、`l2-03-assembly`、`l2-04-publish`、`l2-05-hardware` 全部作废，只能在 `_legacy_layer_based_act/` 或废弃说明中出现。旧状态不得作为循环恢复依据。

| L2 ID | L2 名称 | L2 设计目录 | Dispatch | Acceptance | 三级分支 | Gate 状态 | 人类验收 | 下游放行 |
|---|---|---|---|---|---|---|---|---|
| `l2-01-external-contract` | 外部参数加载与契约校验闭环 | `02_implement/l2-01-external-contract_外部参数加载与契约校验闭环/` | `03_tasks/task/dispatch/l2-01-external-contract.yaml` | `05_acceptance/l2-01-external-contract/` | `feat/model_deploy/l2-01-external-contract` | 未开始 | 未开始 | 不允许 L2-02 |
| `l2-02-observation-snapshot` | 传感器订阅与 ObservationSnapshot 组装闭环 | `02_implement/l2-02-observation-snapshot_ObservationSnapshot组装闭环/` | `03_tasks/task/dispatch/l2-02-observation-snapshot.yaml` | `05_acceptance/l2-02-observation-snapshot/` | `feat/model_deploy/l2-02-observation-snapshot` | 未开始 | 未开始 | 不允许 L2-03 |
| `l2-03-act-inference` | ObservationSnapshot 到 ACT ActionChunk 推理闭环 | `02_implement/l2-03-act-inference_ACT推理闭环/` | `03_tasks/task/dispatch/l2-03-act-inference.yaml` | `05_acceptance/l2-03-act-inference/` | `feat/model_deploy/l2-03-act-inference` | 未开始 | 未开始 | 不允许 L2-04 |
| `l2-04-safety-guard` | 单步 Action 安全检查闭环 | `02_implement/l2-04-safety-guard_单步Action安全检查闭环/` | `03_tasks/task/dispatch/l2-04-safety-guard.yaml` | `05_acceptance/l2-04-safety-guard/` | `feat/model_deploy/l2-04-safety-guard` | 未开始 | 未开始 | 不允许 L2-05 |
| `l2-05-action-publisher` | 单步 Action 到执行器 Topic 适配发送闭环 | `02_implement/l2-05-action-publisher_执行器Topic适配发送闭环/` | `03_tasks/task/dispatch/l2-05-action-publisher.yaml` | `05_acceptance/l2-05-action-publisher/` | `feat/model_deploy/l2-05-action-publisher` | 未开始 | 未开始 | 不允许 L2-06 |
| `l2-06-control-loop` | ControlLoop 中央运行调度闭环 | `02_implement/l2-06-control-loop_ControlLoop中央调度闭环/` | `03_tasks/task/dispatch/l2-06-control-loop.yaml` | `05_acceptance/l2-06-control-loop/` | `feat/model_deploy/l2-06-control-loop` | 未开始 | 未开始 | 不适用 |

## 验收与合入流程

每个 L2 必须依次通过：
1. **L2 Gate（AI 侧自动化）**：产出 `05_acceptance/<l2>/验收结果.md` 和 `L2整体验收报告.md`。
2. **人类验收关卡**：用户按 `05_acceptance/<l2>/人类验收清单.md` 亲自运行测试并签字。

只有两者都通过，才允许执行 Gate 后合入流程（merge --no-ff 到 model_deploy + 删三级分支）。规则见 `DOCS/02_约束/工作流/阶段四开发工作流/attachments/人类验收关卡规则.md`。

## 维护规则

- Gate 状态必须能追溯到对应 `05_acceptance/<l2>/验收结果.md`。
- 人类验收签字必须在该文件的「人类验收」段，含勾选通过 + 用户名 + 日期。
- 本表只是摘要；若与验收结果冲突，以验收结果为准。
- 旧 layer-based L2 状态不得重新写入本表。
