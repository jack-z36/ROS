---
name: stage4-l3-generator
description: Generate Stage 4 ACT L3 micro-task packages from a confirmed L2 design package in this ROS repository. Use when creating or regenerating L3 task Markdown, dispatch YAML, acceptance cards, executor/acceptor input boundaries, or L2 Gate contribution notes from a Stage 4 L2 agent_context directory. This skill does not execute L3 tasks and does not perform Git operations.
---

# Stage4 L3 Generator

## Purpose

Use this skill after a Stage 4 L2 design package has been confirmed by the user and is ready to become L3 implementation tasks.

This skill generates the L3 three-piece package:

- L3 task files under `DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/<l2_id>/`
- dispatch YAML under `DOCS/03_工程/阶段四：模型部署/03_tasks/task/dispatch/<l2_id>.yaml`
- acceptance cards under `DOCS/03_工程/阶段四：模型部署/03_tasks/cards/<l2_id>/`

It does not execute L3 tasks. Use `skills/stage4-l3-orchestrator/` after generation.

## Required Context

Read these before generating or changing L3 files:

1. `AGENTS.md`
2. `DOCS/02_约束/上下文加载/03_非具体编程规划加载规则.md`
3. `DOCS/02_约束/工作流/阶段四开发工作流/阶段四模型部署程序改造工作流.md`
4. `DOCS/02_约束/工作流/阶段四开发工作流/attachments/L3微元改造任务模板.md`
5. `DOCS/02_约束/工作流/阶段四开发工作流/attachments/ACT代码树分层与产物落点约束.md`
6. `DOCS/03_工程/阶段四：模型部署/02_implement/agent_context/00_INDEX.md`
7. `DOCS/03_工程/阶段四：模型部署/02_implement/agent_context/02_L1_ACT功能模块边界.md`
8. `DOCS/03_工程/阶段四：模型部署/02_implement/agent_context/03_L1_ACT功能模块协作架构.md`
9. Target L2 package `agent_context/00_INDEX.md` through `agent_context/11_ui层设计.md`

## Preconditions

Before writing L3 files:

- The target `l2_id` must be one of the current Stage 4 ACT L2 IDs.
- The target L2 package must pass `skills/stage4-l2-designer/scripts/validate_l2_design_package.py`.
- The target L2 `agent_context/03_ACT微元设计与协作.md`, `04_L2验收机制.md`, and `05_人类验收机制.md` must contain user-confirmed design and acceptance semantics.
- HTML is not an L3 generation source. Use it only to understand the human view.

Run:

```bash
python3 skills/stage4-l3-generator/scripts/validate_l3_generation_inputs.py DOCS/03_工程/阶段四：模型部署/02_implement/<l2_id>_<中文短名>
```

## Generation Rules

For each L3:

- Use `attachments/L3微元改造任务模板.md` as the task template.
- Keep the task small enough for one atomic commit, but large enough to verify.
- Include exactly one primary `task_id` such as `deploy_001`.
- Declare allowed and forbidden paths explicitly.
- Map each implementation item to the relevant L2 `agent_context/06_*` through `11_*` design file.
- Choose an acceptance mode from `direct-local`, `static-review`, `downstream-l2`, `env-blocked`, or `hardware-blocked`.
- Create a matching acceptance card for every task.
- Add each task to the dispatch YAML with `acceptance_round_limit: 3`.
- State the L3 contribution to L2 Gate.

Do not generate tasks from old layer-based L2 IDs, Contract Delta files, archived dispatch, or Stage 2 templates.

## Output Shape

```text
DOCS/03_工程/阶段四：模型部署/03_tasks/
├── task/
│   ├── active/<l2_id>/<deploy_id>_<short_name>.md
│   └── dispatch/<l2_id>.yaml
└── cards/<l2_id>/<deploy_id>_验收卡片.md
```

If generating the L2 acceptance card, place it at:

```text
DOCS/03_工程/阶段四：模型部署/03_tasks/cards/<l2_id>/<l2_id>_整体验收卡片.md
```

## Validation

After generating or changing L3 files, run:

```bash
python3 skills/stage4-l3-orchestrator/scripts/validate_stage4_l3_cards.py
```

If validation fails, fix task/card/dispatch consistency before handing off to `stage4-l3-orchestrator`.

## Handoff

End with:

- target L2 package path;
- generated task files;
- generated dispatch file;
- generated acceptance cards;
- validation command result;
- open user decisions;
- whether L3 execution is ready for `skills/stage4-l3-orchestrator/`.
