# 阶段四开发工作流索引

本目录收纳阶段四模型部署程序开发工作流。新版工作流以「人类 HTML + Agent agent_context」双轨产物为理解和执行入口，再把每个功能模块作为一个 L2 线性开发闭环推进。

> [!info] 当前权威口径
> 旧版基于 AS-IS / TO-BE / Contract Delta 聚类 L2 改造包的工作流已归档到 `DOCS/98_archive/2026-07-05_阶段四旧开发工作流归档/阶段四开发工作流/`。当前阶段四第一版 ACT 开发，以本目录文件为权威。

## 工作流入口

| 任务 | 必读文件 |
|---|---|
| 规划、拆分或执行阶段四 ACT 部署程序开发 | `阶段四模型部署程序改造工作流.md` |
| 确认 ACT 代码树落点和依赖方向 | `attachments/ACT代码树分层与产物落点约束.md` |
| 生成阶段四 L3 微元任务 | `attachments/L3微元改造任务模板.md` |
| 设计 L2 Gate 和人工验收 | `attachments/人类验收关卡规则.md` |

## Skill 入口

| Agent 固定步骤 | Skill |
|---|---|
| 生成 / 维护 L2 人类 HTML 与 Agent `agent_context/` | `skills/stage4-l2-designer/` |
| 从已确认 L2 `agent_context/` 生成 L3 任务、dispatch、验收卡片 | `skills/stage4-l3-generator/` |
| 编排 L3 执行、验收、最多 3 轮迭代和 L2 Gate | `skills/stage4-l3-orchestrator/` |
| 执行阶段四 L3 原子提交、push、Gate 后合入 `model_deploy` | `skills/stage4-git-integrator/` |

## 核心边界

- L1 和 L2 产物都必须采用人类 HTML + Agent `agent_context/` 双轨结构。
- HTML 用于人类理解和提出优化建议；Agent 生成 L3、执行、验收和合入时以 `agent_context/` 为权威。
- 每个 L2 是一个功能模块闭环，不再按 `types / config / repo / service / runtime / ui` 目录层命名。
- `types / config / repo / service / runtime / ui` 是代码落点和依赖方向约束，不是任务边界。
- 每个 L2 必须先对照 Pi0.5 源码做功能范围匹配和 3.5 层微元拆解，再设计本模块涉及的六层产物，最后拆 L3。
- L3 是最小、可验证、可回滚的实现任务。
- 每个 L2 必须通过 L2 Gate 和人类验收签字后，才允许合入 `model_deploy`。

## 默认禁止

- 禁止直接套用阶段二 L2/L3 模板。
- 禁止把 `ControlLoop` 当作普通加工函数拆入某个 service L2。
- 禁止在无硬件环境下把 real-robot 行为写成通过。
- 禁止跳过 L2 Gate 或人类验收签字执行合入。
