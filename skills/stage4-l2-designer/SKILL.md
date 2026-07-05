---
name: stage4-l2-designer
description: Produce the fixed Stage 4 ACT L2 design package in this ROS repository. Use when designing one Stage 4 model_deploy L2 before L3 generation, especially to inspect Pi0.5 reference source internally, map source micro-units to the user's 3.5-layer cognitive framework, recommend ACT module functions/classes across types/config/repo/service/runtime/ui, create the L2 design docs, and draft L2 Gate plus human acceptance mechanisms.
---

# Stage4 L2 Designer

## Purpose

Use this skill for the first phase of a Stage 4 L2: turn one functional L2 boundary into a fixed design package that can later generate L3 tasks.

This skill does not execute L3 tasks. Use `stage4-l3-orchestrator` after the L2 design package and acceptance mechanism are confirmed.

## Required Context

Read these before producing artifacts:

1. `AGENTS.md`
2. `DOCS/02_约束/上下文加载/03_非具体编程规划加载规则.md`
3. `DOCS/02_约束/工作流/阶段四开发工作流/阶段四模型部署程序改造工作流.md`
4. `DOCS/02_约束/工作流/阶段四开发工作流/attachments/ACT代码树分层与产物落点约束.md`
5. `DOCS/02_约束/认知偏好/用户认知框架与讲解偏好.md`
6. The L1 task doc and L1 architecture doc under `DOCS/03_工程/阶段四：模型部署/02_l2_change_packages/`
7. Pi0.5 reference source under `DOCS/03_工程/阶段四：模型部署/pi05_old/pi05_test/pi05/`

Read `references/l2-output-contract.md` when creating or checking the final file tree.

## Current L2 Identity Rules

Only these Stage 4 ACT L2 ids are valid current L2 identities:

- `l2-01-external-contract`
- `l2-02-observation-snapshot`
- `l2-03-act-inference`
- `l2-04-action-smoothing`
- `l2-05-safety-guard`
- `l2-06-action-publisher`
- `l2-07-control-loop`

The old layer-based ids `l2-01-types`, `l2-02-config`, `l2-03-assembly`, `l2-04-publish`, and `l2-05-hardware` are legacy only. They may appear only when explaining archived material, never as the current L2 id, branch topic, dispatch group, acceptance directory, or design package identity.

Do not use these as authoritative L2 design sources:

- `DOCS/03_工程/阶段四：模型部署/02_l2_change_packages/_legacy_layer_based_act/`
- `DOCS/03_工程/阶段四：模型部署/03_tasks/_legacy_layer_based_act/`
- `DOCS/03_工程/阶段四：模型部署/03_tasks/_archived_pi05/`
- `DOCS/03_工程/阶段四：模型部署/01_contracts/*Contract Delta*`

Contracts may be consulted only as reference semantics for topic, shape, bundle, or hardware interfaces. They do not define the current L2 boundary.

`DOCS/03_工程/阶段四：模型部署/pi05_old/AGENTS.md` describes the archived Pi0.5 reference project. It is not the current Stage 4 ACT rule source. Its graph can help navigate Pi0.5 source, but final L2 design claims must cite actual Pi0.5 files/classes/functions and the current L1 architecture document.

## Inputs

Require or infer:

- L2 id and name, for example `L2-03 ObservationSnapshot 到 ACT ActionChunk 推理闭环`.
- Stable `l2_id`, which must be one of the current L2 identity rules.
- L2 functional boundary: inputs, outputs, responsibilities, non-responsibilities.
- Current ACT target root: `src/model_deploy/act/`.
- Pi0.5 reference root: `DOCS/03_工程/阶段四：模型部署/pi05_old/pi05_test/pi05/`.

If the L2 boundary is missing or ambiguous, ask the user before writing design files. If the L2 id is not in the current whitelist, stop and report the mismatch.

## Workflow

### 1. Confirm L2 Boundary

Restate the current L2 in this shape:

```text
L2:
Runtime responsibility:
Inputs:
Outputs:
Owns:
Does not own:
Upstream L2:
Downstream L2:
```

Proceed only when the boundary is clear enough to map source files.

The boundary must come from the L1 task document and L1 Agent architecture document. Do not infer the current L2 boundary from Contract Delta files, HTML visualization, legacy L2 cards, or old dispatch files.

### 2. Inspect Pi0.5 Source

Search Pi0.5 source for files, classes, functions, config keys, topics, queues, buffers, and runtime entry points that implement the same or adjacent responsibility.

Prefer `rg` and direct source reads. Do not summarize from memory.

Pi0.5 source is a structure reference. Reuse decisions must be rewritten through the current ACT L1/L2 responsibility boundary; do not copy Pi0.5 task boundaries or topic namespaces as current ACT design.

Use source range matching as an internal working step only. Do not create a standalone `源码范围匹配` document.

Fold source evidence into the 3.5-layer source micro-unit document:

- Relevant file/class/function inventory.
- 3.5-layer micro-unit table using the user's categories:
  - 数据
  - 计算函数
  - 内部状态更新函数
  - 数据读写函数
  - 编排函数
- class packaging table: class, internal state, lifecycle, concurrency, reason for class.
- Reuse decision: `直接复用 / 结构复用 / 参考理解 / 不复用`.

Do not bulk-copy source files. Quote only short targeted snippets when needed to identify an interface.

### 3. Recommend ACT Design

Map the Pi0.5 findings into ACT design recommendations.

For every recommended ACT micro-unit, specify:

- 3.5-layer type.
- Target layer: `types / config / repo / service / runtime / ui`.
- Target file path under `src/model_deploy/act/`.
- Function or class decision.
- Inputs, outputs, side effects.
- Upstream/downstream dependencies.
- Reasoning and Pi0.5 reference.

Flag anything that needs user judgment, especially:

- Whether a stateful object should be a class.
- Whether `ControlLoop.tick()` owns scheduling or a service owns computation.
- Whether a Pi0.5 behavior should be reused structurally or rejected for ACT.
- Whether a validation requires ROS, bundle, or hardware.

### 4. Interaction Checkpoint

Present the ACT recommendation as a draft for user review before generating L3.

If the user corrects the design, update the L2 design docs accordingly. Do not generate L3 in this skill.

### 5. Write the L2 Design Package

Create or update:

```text
DOCS/03_工程/阶段四：模型部署/02_l2_change_packages/<l2_id>_<l2_name>/
├── 00_L2功能边界.md
├── 01_pi05源码3.5层微元拆解.md
├── 02_ACT微元设计与协作.md
├── 03_L2验收机制.md
├── 04_人类验收机制.md
├── types/
├── config/
├── repo/
├── service/
├── runtime/
└── ui/
```

Each six-layer subfolder must contain one or more design `.md` files for target functions/classes, or a `README.md` explaining that the L2 has no artifact in that layer.

Every design package must include `l2_id`, `l2_design_dir`, L1 task doc path, L1 Agent architecture doc path, and a legacy / Contract Delta / Stage 2 template contamination check.

### 6. Design Acceptance

Produce both:

- `03_L2验收机制.md`: AI-side L2 Gate, required L3 list draft, local/mock/dry-run/shadow-run checks, blocked items, pass/fail criteria.
- `04_人类验收机制.md`: human runnable checklist, commands, inputs, observation points, pass/fail phenomena, signature location, hardware safety notes.

Human acceptance must never mark real-robot behavior as passed without real hardware, explicit authorization, emergency stop readiness, and shadow-run evidence.

## Output Rules

- Do not create L3 task files.
- Do not modify `src/model_deploy/act/` implementation files.
- Do not edit Pi0.5 reference source.
- Keep L2 design docs in `DOCS/03_工程/阶段四：模型部署/02_l2_change_packages/`.
- Do not create or update design packages under `_legacy_layer_based_act/`.
- Do not use Contract Delta files as the L2 boundary or task source.
- Do not use Stage 2 L2 templates for Stage 4 ACT L2 design.
- Make diagrams when they clarify dataflow, state ownership, or `ControlLoop` scheduling.
- Treat `types/config/repo/service/runtime/ui` as code placement boundaries, not L2 task boundaries.

## Handoff

End with:

- Created/updated L2 design package path.
- Pi0.5 files inspected.
- ACT files proposed.
- Open user decisions.
- Whether the design is ready for L3 generation.
