# 阶段四循环状态索引

## 消费 Agent

- 全部 Agent

## 本文职责

本文只说明阶段四 `00_status/` 目录中各状态文件的用途、权威关系和读取入口。

## 不负责

本文不承载通用行为规则、L3 任务正文、验收日志全文、Git 操作规则或历史复盘。

## 目录定位

`00_status/` 存放阶段四 Ralph / OpenCode 循环的当前状态上下文。它帮助各类 Agent 恢复真实进度，但不替代 dispatch、验收日志或 L2 Gate 结论。

## 状态文件入口

| 文件 | 原子职责 | 消费 Agent |
|---|---|---|
| `stage4_loop_goal.md` | 当前循环子目标和终点 | 主 Agent |
| `l2_progress_status.md` | L2 Gate、阻塞、下游放行状态摘要 | 主 Agent / L2 Gate agent |
| `l3_dispatch_status.md` | L3 状态、wave、依赖和下一步摘要 | 主 Agent |
| `git_sync_status.md` | L3 commit、push、pending push、L2 merge 状态 | 主 Agent |
| `hardware_block_status.md` | 真机 blocked 条件和 `deploy_023` 交接条件 | 主 Agent / L2 Gate agent |
| `current_loop_snapshot.md` | 上一轮结束恢复点和下一步建议 | 主 Agent |

## 权威关系

| 信息 | 权威来源 |
|---|---|
| L3 调度状态 | `DOCS/03_工程/阶段四：模型部署/03_tasks/task/dispatch/*.yaml` |
| L3 验收证据 | `DOCS/03_工程/阶段四：模型部署/05_acceptance/<l2>/logs/` |
| L2 Gate 结论 | `DOCS/03_工程/阶段四：模型部署/05_acceptance/<l2>/验收结果.md` 和 `L2整体验收报告.md` |
| Git 同步状态 | `DOCS/03_工程/阶段四：模型部署/00_status/git_sync_status.md` |
| 循环恢复摘要 | `DOCS/03_工程/阶段四：模型部署/00_status/current_loop_snapshot.md` |

旧 layer-based ACT 产物已隔离到 `_legacy_layer_based_act/`，不得作为上述权威来源。旧 `l2-01-types`、`l2-02-config`、`l2-03-assembly`、`l2-04-publish`、`l2-05-hardware` 只能作为废弃说明或历史参考出现。

## 维护规则

- 状态摘要必须能追溯到权威来源。
- 状态摘要不得覆盖或改写验收日志事实。
- 如果状态摘要与 dispatch、验收结果或 Git 状态冲突，以权威来源为准，并由主 Agent更新摘要。
- 状态摘要不得重新引用旧 layer-based L2 作为当前目标。
