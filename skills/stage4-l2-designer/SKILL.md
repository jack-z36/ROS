---
name: stage4-l2-designer
description: Produce and maintain the Stage 4 ACT L2 design package in this ROS repository. Use when designing, optimizing, reviewing, or migrating one Stage 4 model_deploy L2 before L3 generation, especially to inspect Pi0.5 reference source internally, map source micro-units to the user's 3.5-layer cognitive framework, recommend ACT module functions/classes across types/config/repo/service/runtime/ui, create Agent-consumable atomic Markdown under agent_context/, create a human-consumable interactive SVG-heavy HTML visualization, and draft L2 Gate plus human acceptance mechanisms.
---

# Stage4 L2 Designer

## Purpose

Use this skill for the L2 design phase of Stage 4 ACT deployment work. It turns one functional L2 boundary into two separated products:

- a low-density human HTML entrypoint with interactive diagrams;
- high-density Agent Markdown under `agent_context/`.

This skill does not execute L3 tasks. Use `stage4-l3-orchestrator` only after the L2 design package and acceptance mechanism are confirmed.

## Required Context

Read these before producing or changing artifacts:

1. `AGENTS.md`
2. `DOCS/02_约束/上下文加载/03_非具体编程规划加载规则.md`
3. `DOCS/02_约束/工作流/阶段四开发工作流/阶段四模型部署程序改造工作流.md`
4. `DOCS/02_约束/工作流/阶段四开发工作流/attachments/ACT代码树分层与产物落点约束.md`
5. `DOCS/02_约束/认知偏好/用户认知框架与讲解偏好.md`
6. `DOCS/03_工程/阶段四：模型部署/02_implement/00_L1_ACT部署程序任务文档.md`
7. `DOCS/03_工程/阶段四：模型部署/02_implement/01_L1_ACT功能模块边界.md`
8. `DOCS/03_工程/阶段四：模型部署/02_implement/02_L1_ACT功能模块协作架构.md`
9. Pi0.5 reference source under `DOCS/03_工程/阶段四：模型部署/pi05_old/pi05_test/pi05/`

Read `references/l2-output-contract.md` when creating, migrating, or checking the final file tree.

Use `DOCS/03_工程/阶段四：模型部署/02_implement/ACT架构交互可视化.html` only as a visual quality reference. Do not copy ACT-wide content into a single-L2 visualization.

## Current L2 Identity Rules

Only these Stage 4 ACT L2 ids are valid:

- `l2-01-external-contract`
- `l2-02-observation-snapshot`
- `l2-03-act-inference`
- `l2-04-action-smoothing`
- `l2-05-safety-guard`
- `l2-06-action-publisher`
- `l2-07-control-loop`

The old layer-based ids `l2-01-types`, `l2-02-config`, `l2-03-assembly`, `l2-04-publish`, and `l2-05-hardware` are legacy only. They may appear only in contamination checks, deprecation notes, or explicit read-only reference context.

Do not use these as authoritative L2 design sources:

- `DOCS/03_工程/阶段四：模型部署/02_implement/归档/`
- `DOCS/03_工程/阶段四：模型部署/03_tasks/归档/_legacy_layer_based_act/`
- `DOCS/03_工程/阶段四：模型部署/03_tasks/归档/_archived_pi05/`
- `DOCS/03_工程/阶段四：模型部署/01_contracts/*Contract Delta*`

Contracts may be consulted only as reference semantics for topic, shape, bundle, or hardware interfaces. They do not define the current L2 boundary.

## Output Shape

Create or maintain exactly this L2 package shape:

```text
DOCS/03_工程/阶段四：模型部署/02_implement/<l2_id>_<l2_name>/
├── L2架构交互可视化.html
└── agent_context/
    ├── 00_INDEX.md
    ├── 01_L2功能边界.md
    ├── 02_pi05源码3.5层微元拆解.md
    ├── 03_ACT微元设计与协作.md
    ├── 04_L2验收机制.md
    ├── 05_人类验收机制.md
    ├── 06_types层设计.md
    ├── 07_config层设计.md
    ├── 08_repo层设计.md
    ├── 09_service层设计.md
    ├── 10_runtime层设计.md
    └── 11_ui层设计.md
```

The package root is for humans. Keep all Agent Markdown inside `agent_context/`. Do not create `types/`, `config/`, `repo/`, `service/`, `runtime/`, or `ui/` subdirectories in the L2 design package.

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

Stop for user confirmation before continuing. The boundary must come from the L1 task document and L1 Agent architecture documents, not from Contract Delta files, HTML visualization, legacy cards, or old dispatch files.

### 2. Inspect Pi0.5 Source

Search Pi0.5 source for files, classes, functions, config keys, topics, queues, buffers, and runtime entry points that implement the same or adjacent responsibility.

Prefer `rg` and direct source reads. Do not summarize from memory.

Source range matching is an internal working step only. Do not create a standalone `源码范围匹配` document. Fold useful evidence into `agent_context/02_pi05源码3.5层微元拆解.md`:

- exact Pi0.5 paths, classes, functions, constants, and entry points;
- 3.5-layer micro-unit table using `数据 / 计算函数 / 内部状态更新函数 / 数据读写函数 / 编排函数`;
- class packaging table with state, lifecycle, concurrency, and ACT recommendation;
- reuse decision: `直接复用 / 结构复用 / 参考理解 / 不复用`.

Pi0.5 is a structure reference. Reuse decisions must be rewritten through the current ACT L1/L2 boundary.

### 3. Recommend ACT Design

Map the Pi0.5 findings into ACT recommendations.

For every ACT micro-unit, specify:

- 3.5-layer type;
- target layer: `types / config / repo / service / runtime / ui`;
- target file path under `src/model_deploy/act/`;
- function or class decision;
- inputs, outputs, and side effects;
- upstream/downstream dependencies;
- reasoning and Pi0.5 reference.

Stop for user confirmation after recommending ACT micro-units, class/function decisions, Pi0.5 reuse decisions, and six-layer landing points.

### 4. Write Agent Context

Write high-density Markdown under `agent_context/`.

`00_INDEX.md` is the Agent routing entry. It must describe:

- each Markdown file's responsibility;
- when to read it;
- HTML vs Markdown authority;
- contamination checks.

Macro design files must carry the full detail needed by later Agents. Do not compress Agent Markdown for human readability.

Six-layer design is represented by six files directly under `agent_context/`, not by six directories. If a layer adds no source artifact, keep its file and write:

```text
本 L2 不在该层新增源码产物。
原因：
验收如何确认：
```

### 5. Write Human HTML

Create `L2架构交互可视化.html` as the only root-level human entrypoint.

Rules:

- standalone `<!doctype html>` file with inline CSS and no network dependencies;
- low text density: show core relationships, not implementation detail;
- visual-first: use inline SVG diagrams, visual cards, arrows, swimlanes, or state panels;
- interactive: include radio tabs, toggles, `<details>`, hover states, or equivalent no-build interaction;
- cite `agent_context/00_INDEX.md` and the relevant Agent Markdown files as authoritative;
- state clearly that HTML is not used for L3 generation.

Required views:

- Overview: this L2 in the Stage 4 ACT collaboration graph;
- Dataflow: external inputs, RAM objects, queues/topics, outputs, ownership;
- Control/runtime flow: timer, worker, callback, service call, or `ControlLoop.tick()` interactions;
- Failure/fallback: validation failures, stale data, rejected actions, blocked hardware, status propagation;
- Metrics/status/acceptance: observable counters, topics, logs, commands, pass/fail phenomena;
- Boundary contract: responsibilities, non-responsibilities, target files, acceptance coverage.

If a view is not meaningful for the L2, keep the view and explain why in one compact visual note.

Stop for user confirmation after drafting the HTML information hierarchy and L2 Gate/human acceptance design.

### 6. Design Acceptance

Produce both:

- `agent_context/04_L2验收机制.md`: AI-side L2 Gate, required L3 draft, local/mock/dry-run/shadow-run checks, blocked items, pass/fail criteria.
- `agent_context/05_人类验收机制.md`: human runnable checklist, commands, inputs, observation points, pass/fail phenomena, signature location, hardware safety notes.

Human acceptance must never mark real-robot behavior as passed without real hardware, explicit authorization, emergency stop readiness, and shadow-run evidence.

## Validation

After creating or migrating a package, run:

```bash
python3 skills/stage4-l2-designer/scripts/validate_l2_design_package.py DOCS/03_工程/阶段四：模型部署/02_implement/<l2_id>_<l2_name>
```

Also inspect any reported contamination manually before treating the package as ready for L3 generation.

## Output Rules

- Do not create L3 task files.
- Do not modify `src/model_deploy/act/` implementation files.
- Do not edit Pi0.5 reference source.
- Do not place Agent Markdown in the L2 package root.
- Do not create six-layer subdirectories in the L2 design package.
- Do not create or update design packages under `02_implement/归档/` or old layer-based directories.
- Do not use Contract Delta files as the L2 boundary or task source.
- Do not use Stage 2 L2 templates for Stage 4 ACT L2 design.
- Treat `types/config/repo/service/runtime/ui` as code placement boundaries, not L2 task boundaries.

## Handoff

End with:

- L2 design package path;
- human HTML path;
- Agent context path;
- Pi0.5 files inspected;
- ACT files proposed;
- open user decisions;
- validation command result;
- whether the design is ready for L3 generation.
