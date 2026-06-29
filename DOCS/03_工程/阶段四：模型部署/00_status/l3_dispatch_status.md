# L3 调度状态摘要

## 消费 Agent

- 主 Agent

## 本文职责

本文只汇总阶段四 L3 的调度状态、依赖关系和下一步方向，作为主 Agent 恢复循环的摘要。

## 不负责

本文不替代 `03_tasks/task/dispatch/*.yaml`，不记录完整 L3 正文、验收日志或执行摘要。

## 当前摘要

| L2 | Dispatch | 摘要 |
|---|---|---|
| l2-01-types | `03_tasks/task/dispatch/l2-01-types.yaml` | 全组已标记 `synced` |
| l2-02-config | `03_tasks/task/dispatch/l2-02-config.yaml` | 全组已标记 `synced` |
| l2-03-assembly | `03_tasks/task/dispatch/l2-03-assembly.yaml` | 下一组待从 dispatch 中选择 ready L3 |
| l2-04-publish | `03_tasks/task/dispatch/l2-04-publish.yaml` | 等待 L2-03 Gate |
| l2-05-hardware | `03_tasks/task/dispatch/l2-05-hardware.yaml` | 等待 L2-04 Gate；`deploy_023` 默认 blocked |

## 维护规则

- L3 调度状态的权威来源是各 L2 dispatch。
- 主 Agent 每轮结束时应根据 dispatch 和验收结果更新本摘要。
- 如果本摘要与 dispatch 冲突，以 dispatch 为准。

