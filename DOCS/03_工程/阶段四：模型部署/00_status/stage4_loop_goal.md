# 阶段四循环目标状态

## 消费 Agent

- 主 Agent

## 本文职责

本文只记录当前 Ralph / OpenCode 循环的阶段四子目标和完成边界。

## 不负责

本文不记录 L2 / L3 当前进度、Git 同步状态、验收日志或具体执行命令。

## 当前子目标

当前循环目标已经重置为新版 ACT 功能闭环 L2 主线：

```text
l2-01-external-contract
→ l2-02-observation-snapshot
→ l2-03-act-inference
→ l2-04-safety-guard
→ l2-05-action-publisher
→ l2-06-control-loop
```

`l2-04-action-smoothing` 已从第一版循环目标移除。Action 平滑、smoothstep blend、跨 chunk 融合和 RTC 类对齐均为后续优化方向，不作为当前循环完成条件。

旧 `l2-01-types`、`l2-02-config`、`l2-03-assembly`、`l2-04-publish`、`l2-05-hardware` 以及 `deploy_022` / `deploy_023` 目标作废，只能作为 legacy 历史参考。

当前最近子目标是：为 `l2-01-external-contract` 生成新版 L2 设计目录、dispatch、验收卡片和 acceptance 目录，然后再进入 L3 执行。

## 完成边界

当前循环完成的最小标准：

- 6 个新版功能闭环 L2 均按顺序完成 L2 Gate。
- 每个 L2 均具备人类验收记录。
- 每个 L2 的 L3 均来自新版 active / dispatch / cards / acceptance 路径。
- 旧 layer-based L2 不再作为循环恢复、调度或合入依据。
