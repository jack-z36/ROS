# Git 同步状态

## 消费 Agent

- 主 Agent

## 本文职责

本文只记录阶段四 Ralph / OpenCode 循环中的 L3 原子提交、push、pending push 和 L2 merge 状态。

## 不负责

本文不定义 Git 操作规则，不替代 `DOCS/02_约束/Git协作/` 下的 Git 约束，也不记录 L3 验收结论。

## 状态表

| 范围 | 分支 | 本地提交 | push 状态 | merge 状态 | 备注 |
|---|---|---|---|---|---|
| l2-01-types | `model_deploy-l2-01-types` | `bad739a` | 已推送或以远端状态为准 | 已合入 `model_deploy` | 以 Git 实际状态和 L2 验收结果为准 |
| l2-02-config | `model_deploy-l2-02-config` | `4c79b32` | 已推送或以远端状态为准 | 已合入 `model_deploy` | 以 Git 实际状态和 L2 验收结果为准 |
| l2-03-assembly | `model_deploy-l2-03-assembly` | `0a75f77`（L3 代码+dispatch）、`4c8080d`（L2 验收文档固化） | 已推送 `origin/model_deploy-l2-03-assembly` | 未合入 | L2 Gate 不通过（deploy_012 BLOCKED_ENV: torch 缺失）；待 torch 环境补齐重跑后放行合入 |
| l2-04-publish | `model_deploy-l2-04-publish` | 待记录 | 待记录 | 未合入 | L2 Gate 未通过 |
| l2-05-hardware | `model_deploy-l2-05-hardware` | 待记录 | 待记录 | 未合入 | L2 Gate 未通过 |

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

