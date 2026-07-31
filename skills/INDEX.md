# 项目 Skills 索引

本目录存放可复用的项目本地 Agent skills。Agent 应先从仓库根 `AGENTS.md` 选择任务类型；普通维护任务按 `DOCS/02_约束/上下文加载/06_普通代码维护加载规则.md` 读取本索引，并在任务与某项描述匹配时完整读取其 `SKILL.md`。

每项 skill 的适用边界以其自身 `SKILL.md` 为准。不要仅因本索引存在而加载无关 skill。

## UI 设计与动效（emilkowalski/skills）

以下八项从 [`emilkowalski/skills`](https://github.com/emilkowalski/skills) 的 `main` 分支（`70744e3816f1d93eafb697161a8b880a7384c5ff`）部署，面向 Web UI 的设计、动效和原型工作。

| Skill | 适用场景 | 入口 |
|---|---|---|
| animation-vocabulary | 为含糊的动效描述查找准确术语。 | [SKILL.md](animation-vocabulary/SKILL.md) |
| apple-design | 构建或评审手势、弹簧动效、拖拽、半透明材质和 Apple 风格交互。 | [SKILL.md](apple-design/SKILL.md) |
| emil-design-eng | 以设计工程视角提升 UI 细节、组件与动效决策。 | [SKILL.md](emil-design-eng/SKILL.md) |
| find-animation-opportunities | 只读审查 UI，找出真正值得加入动效的时机。 | [SKILL.md](find-animation-opportunities/SKILL.md) |
| improve-animations | 只读审计动效代码，并产出按优先级排序的改进计划。 | [SKILL.md](improve-animations/SKILL.md) |
| pick-ui-library | 显式调用时，为前端能力选择推荐库。 | [SKILL.md](pick-ui-library/SKILL.md) |
| prototype | 显式调用时，为同一 UI 构建可切换的多种设计方向。 | [SKILL.md](prototype/SKILL.md) |
| review-animations | 严格评审已有动效与 motion 代码。 | [SKILL.md](review-animations/SKILL.md) |

## 项目专用 skills

| Skill | 适用场景 | 入口 |
|---|---|---|
| read-hwk-tactile-uid | 读取已连接 HWK 触觉传感器 UID，并更新硬件身份映射。 | [SKILL.md](read-hwk-tactile-uid/SKILL.md) |
| stage4-l3-orchestrator | 编排阶段四模型部署的 L3 执行、验收和迭代。该类任务优先走 L3 加载规则。 | [SKILL.md](stage4-l3-orchestrator/SKILL.md) |
| update-knowledge-from-commits | 从 Git 提交更新稳定知识文档。 | [SKILL.md](update-knowledge-from-commits/SKILL.md) |
| update-routes-from-commits | 从 Git 提交维护路由文件、加载规则和索引。 | [SKILL.md](update-routes-from-commits/SKILL.md) |
