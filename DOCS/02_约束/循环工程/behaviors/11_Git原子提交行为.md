# Git 原子提交行为

## 消费 Agent

- 主 Agent

## 本文职责

本文只约束主 Agent 如何对单个 L3 执行原子提交和 push 失败记录。

## 不负责

本文不定义全局 Git 底线、L2 Gate 合入完整流程或 L3 实现。

## 必读前置

- `DOCS/02_约束/Git协作/Git操作规则.md`
- `DOCS/02_约束/Git协作/阶段四：模型部署 Git操作规则.md`
- `DOCS/02_约束/循环工程/07_Git原子提交规则.md`

## 提交条件

- L3 已进入 `accepted_local`。
- 当前分支是该 L3 所属 L2 分支。
- 工作区只包含当前 L3 允许范围内的改动。
- 共享文件归属和串行顺序已明确。

## 禁止事项

- 禁止 `git add -A`。
- 禁止 `git commit --amend`。
- 禁止 force push。
- 禁止在 `model_deploy` 上提交 L3。
- 禁止混合多个 L2 改动。

## Push 失败

本地 commit 成功但 push 失败时：

- 写入 `00_status/git_sync_status.md`。
- 标记为 `pending_push`。
- 使用 docs-only 小提交持久化 pending push 记录。
- 不得 amend 已有 L3 commit。

