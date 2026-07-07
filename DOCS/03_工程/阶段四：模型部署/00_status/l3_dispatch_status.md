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
| `l2-01-external-contract` | `03_tasks/task/dispatch/l2-01-external-contract.yaml` | 未生成；需先完成新版 L2 设计和 L3 生成 |
| `l2-02-observation-snapshot` | `03_tasks/task/dispatch/l2-02-observation-snapshot.yaml` | 未生成；等待 L2-01 Gate |
| `l2-03-act-inference` | `03_tasks/task/dispatch/l2-03-act-inference.yaml` | 未生成；等待 L2-02 Gate |
| `l2-04-safety-guard` | `03_tasks/task/dispatch/l2-04-safety-guard.yaml` | 未生成；等待 L2-03 Gate |
| `l2-05-action-publisher` | `03_tasks/task/dispatch/l2-05-action-publisher.yaml` | 未生成；等待 L2-04 Gate |
| `l2-06-control-loop` | `03_tasks/task/dispatch/l2-06-control-loop.yaml` | 未生成；等待 L2-05 Gate |

> [!warning] 旧调度作废
> 旧 layer-based dispatch 已隔离到 `03_tasks/_legacy_layer_based_act/`，不得作为当前调度来源。

## 维护规则

- L3 调度状态的权威来源是各 L2 dispatch。
- 主 Agent 每轮结束时应根据 dispatch 和验收结果更新本摘要。
- 如果本摘要与 dispatch 冲突，以 dispatch 为准。
- 旧 `l2-01-types` 等 ID 不得重新写入当前摘要，除非位于明确废弃说明中。
