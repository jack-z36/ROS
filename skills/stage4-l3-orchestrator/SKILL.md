---
name: stage4-l3-orchestrator
description: Coordinate Stage 4 model_deploy L3 micro-task execution and acceptance in this ROS repository. Use when Codex, Claude Code, or OpenCode needs to act as the main Agent for Stage 4 L3 dispatch, spawn execution sub-agents from L3 task files, spawn acceptance sub-agents from acceptance cards, validate L3/card/dispatch metadata, run up to three execute-review iterations, or produce L2 acceptance reports under DOCS/03_工程/阶段四：模型部署.
---

# Stage4 L3 Orchestrator

## Purpose

Use this skill to coordinate Stage 4 `model_deploy` L3 work without loading unnecessary global context into sub-agents.

The main Agent owns dispatch and iteration. Execution sub-agents read one L3 task file. Acceptance sub-agents read one acceptance card. L2 acceptance sub-agents read one L2 acceptance card.

## Core Inputs

Prefer a Stage 4 dispatch index:

```text
DOCS/03_工程/阶段四：模型部署/03_tasks/task/dispatch/<l2>.yaml
```

Required related paths:

```text
DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/<l2>/<deploy_id>_*.md
DOCS/03_工程/阶段四：模型部署/03_tasks/cards/<l2>/<deploy_id>_验收卡片.md
DOCS/03_工程/阶段四：模型部署/03_tasks/cards/<l2>/<l2>_整体验收卡片.md
DOCS/03_工程/阶段四：模型部署/05_acceptance/<l2>/
```

## Main Agent Workflow

1. Read `AGENTS.md`, then `DOCS/02_约束/上下文加载/04_L3微元任务执行加载规则.md`.
2. Read the target L2 dispatch index.
3. Run:

```bash
python skills/stage4-l3-orchestrator/scripts/validate_stage4_l3_cards.py
```

4. Select executable L3 tasks by `wave`, `depends_on`, `dispatch_status`, and `conflict_scope`.
5. Spawn at most `max_parallel_agents` execution sub-agents when write scopes do not overlap.
6. Generate execution prompts with:

```bash
python skills/stage4-l3-orchestrator/scripts/make_stage4_subagent_prompt.py --role executor --task <L3_TASK_PATH>
```

7. After an execution sub-agent finishes, spawn an acceptance sub-agent for the matching card:

```bash
python skills/stage4-l3-orchestrator/scripts/make_stage4_subagent_prompt.py --role acceptor --card <L3_CARD_PATH> --round <N>
```

8. If the acceptance result is `FAIL_LOCAL`, return the feedback to the same execution sub-agent or a new execution sub-agent with the same L3 ownership.
9. Stop after three execute-review rounds for the same L3 and escalate to the main Agent.
10. When all required L3 tasks for one L2 are complete or explicitly blocked, run L2 acceptance:

```bash
python skills/stage4-l3-orchestrator/scripts/make_stage4_subagent_prompt.py --role l2-acceptor --l2 <l2>
```

## Execution Sub-Agent Rules

Give an execution sub-agent exactly one L3 file.

The execution sub-agent must:

- Read only the assigned L3 and the context listed in that L3.
- Validate task identity before editing.
- Respect allowed and forbidden files.
- Run the L3's local validation when possible.
- Update the L3 execution summary and success criteria.
- Not edit dispatch indexes.
- Not select another L3.
- Not perform Git sync.

## Acceptance Sub-Agent Rules

Give an acceptance sub-agent exactly one L3 acceptance card.

The acceptance sub-agent must:

- Read the acceptance card first.
- Read the referenced L3 file, execution summary, allowed code/diff, and logs.
- Follow `acceptance_mode`.
- Run local commands only for `direct-local` when the environment supports them.
- Use static review for `static-review`.
- Return `DEFER_TO_L2_GATE` for `downstream-l2` when no standalone closure exists.
- Return `BLOCKED_ENV` when Ubuntu lacks ROS, bundle, SDK, or dependencies.
- Return `BLOCKED_HARDWARE_EXPECTED` for real hardware checks in no-hardware environments.
- Never edit source, tests, dispatch, cards, or Git state.

Allowed conclusions:

```text
PASS_LOCAL
FAIL_LOCAL
BLOCKED_ENV
BLOCKED_HARDWARE_EXPECTED
DEFER_TO_L2_GATE
```

Write feedback to:

```text
DOCS/03_工程/阶段四：模型部署/05_acceptance/<l2>/logs/<deploy_id>_acceptance_round_<n>.md
```

## Acceptance Modes

Read `references/acceptance_modes.md` when the acceptance mode or conclusion is unclear.

Summary:

- `direct-local`: run local unit/import/config/mock/dry-run command and record observations.
- `static-review`: inspect diff, interfaces, boundaries, and execution summary; no command required.
- `downstream-l2`: verify contribution and defer full runtime proof to a later L3 or L2 Gate.
- `hardware-blocked`: review code/risk only; real hardware behavior remains blocked.
- `env-blocked`: record missing Ubuntu dependency; do not call it a failure or a pass.

## Conflict Rules

Do not parallelize two execution sub-agents when any overlap exists in:

- `conflict_scope.files`
- `conflict_scope.modules`
- `conflict_scope.config_keys`
- `conflict_scope.hardware_paths`

Acceptance sub-agents are read-only and may run in parallel, but they must not write the same feedback file.

## Stop Conditions

Stop dispatching and report when:

- L3 file, dispatch task, and acceptance card disagree.
- `acceptance_mode` is missing.
- The current branch does not match the L2 branch.
- A dependency is not complete or explicitly waived.
- A task is `blocked` or `waiting_user`.
- Three execute-review rounds fail for the same L3.
- A real-robot task lacks blocked conditions or tries to claim hardware success without hardware.

## Resources

- `scripts/validate_stage4_l3_cards.py`: validate L3, dispatch, and acceptance-card consistency.
- `scripts/make_stage4_subagent_prompt.py`: generate minimal prompts for executor, acceptor, and L2 acceptor roles.
- `references/acceptance_modes.md`: detailed mode and conclusion rules.
