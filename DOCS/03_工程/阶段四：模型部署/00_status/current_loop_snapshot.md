# 当前循环快照

## 消费 Agent

- 主 Agent

## 本文职责

本文只记录上一轮 Ralph / OpenCode 循环结束后的恢复点和下一步建议。

## 不负责

本文不替代 dispatch、验收结果、Git 同步状态或 L2 Gate 报告。

## 当前恢复点

| 字段 | 内容 |
|---|---|
| 更新时间 | 2026-07-05（北京时间） |
| 当前目标 L2 | 未选择；等待新版 L2 设计目录、dispatch 和 acceptance 生成 |
| 当前主线 | 新版 ACT 7 个功能闭环 L2 |
| 上游 Gate | 全部未开始 |
| 下一步 | 从 `l2-01-external-contract` 开始生成新版 L2 设计目录、dispatch、验收卡片和 acceptance 目录；不得恢复旧 `l2-01-types` 等 layer-based 任务 |
| Git 前置 | 修改和提交范围必须落到 `src/model_deploy/act/` 与当前新版 L2 工程文档；Pi0.5 只读参考 |
| 阻塞项 | 当前没有可执行 L3；旧 active L3 已隔离，必须先按新版 L2 流程重新生成 |
| 旧流程状态 | 旧 `l2-01-types`、`l2-02-config`、`l2-03-assembly`、`l2-04-publish`、`l2-05-hardware` 状态作废，不得作为循环恢复依据 |

## 维护规则

- 每轮结束前，主 Agent 必须更新本文件或明确说明无法更新的原因。
- 如果本文件与权威状态冲突，以 dispatch、验收结果和 Git 状态为准。
