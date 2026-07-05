# Git 同步状态

## 消费 Agent

- 主 Agent

## 本文职责

本文只记录阶段四 L2 循环中的 L3 原子提交、push、pending push 和 L2 merge 状态。

## 不负责

本文不定义 Git 操作规则，不替代 `DOCS/02_约束/Git协作/` 下的 Git 约束，也不记录 L3 验收结论或人类验收结论。

## 状态表

> [!warning] 2026-07-05 重置说明
> 旧 layer-based L2 Git 状态作废。当前只记录新版 7 个功能闭环 L2 的提交、push 和 merge 状态。旧 `l2-01-types` 等分支不得作为当前合入依据。

| 范围 | 三级分支 | 本地提交 | push 状态 | merge 状态 | 备注 |
|---|---|---|---|---|---|
| `l2-01-external-contract` | `feat/model_deploy/l2-01-external-contract` | 待生成 L3 | 待记录 | 未合入 | 新版 L2-01，未开始 |
| `l2-02-observation-snapshot` | `feat/model_deploy/l2-02-observation-snapshot` | 待生成 L3 | 待记录 | 未合入 | 新版 L2-02，未开始 |
| `l2-03-act-inference` | `feat/model_deploy/l2-03-act-inference` | 待生成 L3 | 待记录 | 未合入 | 新版 L2-03，未开始 |
| `l2-04-action-smoothing` | `feat/model_deploy/l2-04-action-smoothing` | 待生成 L3 | 待记录 | 未合入 | 新版 L2-04，未开始 |
| `l2-05-safety-guard` | `feat/model_deploy/l2-05-safety-guard` | 待生成 L3 | 待记录 | 未合入 | 新版 L2-05，未开始 |
| `l2-06-action-publisher` | `feat/model_deploy/l2-06-action-publisher` | 待生成 L3 | 待记录 | 未合入 | 新版 L2-06，未开始 |
| `l2-07-control-loop` | `feat/model_deploy/l2-07-control-loop` | 待生成 L3 | 待记录 | 未合入 | 新版 L2-07，未开始 |

## 合入前置条件

合入 `model_deploy` 前必须同时满足：
1. L2 Gate（AI 侧自动化验收）通过。
2. **人类验收签字通过**（`05_acceptance/<l2>/验收结果.md` 的「人类验收」段）。
3. 无 Git 阻断条件（冲突、分叉、超大文件等）。

规则见 `DOCS/02_约束/Git协作/阶段四：模型部署 Git操作规则.md` 和 `DOCS/02_约束/工作流/阶段四开发工作流/attachments/人类验收关卡规则.md`。

旧 layer-based L2 分支只允许作为历史参考，不得写入当前状态表或作为自动合入目标。

## Push 失败记录格式

当 L3 本地提交成功但 push 失败时，主 Agent 追加记录：

```text
时间：
L2：
L3：
本地提交：
目标分支：
push 命令：
失败摘要：
状态：pending_push
后续处理：
```
