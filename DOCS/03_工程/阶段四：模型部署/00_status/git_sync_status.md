# Git 同步状态

## 消费 Agent

- 主 Agent

## 本文职责

本文只记录阶段四 L2 循环中的 L3 原子提交、push、pending push 和 L2 merge 状态。

## 不负责

本文不定义 Git 操作规则，不替代 `DOCS/02_约束/Git协作/` 下的 Git 约束，也不记录 L3 验收结论或人类验收结论。

## 状态表

> [!warning] 2026-07-03 重置说明
> 原表记录的是 Pi0.5 版 L2 的提交/merge 状态（l2-01/l2-02 声称已合入）。第一版切换为 ACT 后，旧 L2/L3 已归档，5 个 L2 全部针对 ACT 从零重写，提交状态全部重置。原 Pi0.5 的 commit 记录保留在 Git 历史中，但不再作为当前主线依据。

| 范围 | 三级分支 | 本地提交 | push 状态 | merge 状态 | 备注 |
|---|---|---|---|---|---|
| l2-01-types | `feat/model_deploy/l2-01-types` | 待记录 | 待记录 | 未合入 | ACT 版，未开始 |
| l2-02-config | `feat/model_deploy/l2-02-config` | 待记录 | 待记录 | 未合入 | ACT 版，未开始 |
| l2-03-assembly | `feat/model_deploy/l2-03-assembly` | 待记录 | 待记录 | 未合入 | ACT 版，未开始 |
| l2-04-publish | `feat/model_deploy/l2-04-publish` | 待记录 | 待记录 | 未合入 | ACT 版，未开始 |
| l2-05-hardware | `feat/model_deploy/l2-05-hardware` | 待记录 | 待记录 | 未合入 | ACT 版，未开始 |

## 合入前置条件

合入 `model_deploy` 前必须同时满足：
1. L2 Gate（AI 侧自动化验收）通过。
2. **人类验收签字通过**（`05_acceptance/<l2>/验收结果.md` 的「人类验收」段）。
3. 无 Git 阻断条件（冲突、分叉、超大文件等）。

规则见 `DOCS/02_约束/Git协作/阶段四：模型部署 Git操作规则.md` 和 `DOCS/02_约束/工作流/阶段四开发工作流/attachments/人类验收关卡规则.md`。

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
