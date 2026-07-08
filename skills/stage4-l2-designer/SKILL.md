---
name: stage4-l2-designer
description: Produce and maintain the Stage 4 ACT L2 design package in this ROS repository. Use when designing, optimizing, reviewing, or migrating one Stage 4 model_deploy L2 before L3 generation, especially to inspect Pi0.5 reference source internally, map source micro-units to the user's 3.5-layer cognitive framework, recommend ACT module functions/classes across types/config/repo/service/runtime/ui, create Agent-consumable atomic Markdown under agent_context/, create a human-consumable four-dimension interactive HTML visualization aligned with the approved L2 HTML sample pattern, and draft L2 Gate plus human acceptance mechanisms.
---

# Stage4 L2 Designer

## Purpose

Use this skill for the L2 design phase of Stage 4 ACT deployment work. It turns one functional L2 boundary into two separated but semantically aligned products:

- a low-density human HTML entrypoint with interactive diagrams;
- high-density Agent Markdown under `agent_context/`.

The HTML is a visual projection of the Markdown, not an independent source of truth. Any change to HTML logic, views, labels, relationships, dataflow, failure path, boundary, or Gate semantics must be reflected in the authoritative Markdown at the same time.

This skill does not generate or execute L3 tasks. Use `stage4-l3-generator` after the L2 design package and acceptance mechanism are confirmed, then use `stage4-l3-orchestrator` to execute and accept generated L3 tasks.

## Required Context

Read these before producing or changing artifacts:

1. `AGENTS.md`
2. `DOCS/02_约束/上下文加载/03_非具体编程规划加载规则.md`
3. `DOCS/02_约束/工作流/阶段四开发工作流/阶段四模型部署程序改造工作流.md`
4. `DOCS/02_约束/工作流/阶段四开发工作流/attachments/ACT代码树分层与产物落点约束.md`
5. `DOCS/02_约束/认知偏好/用户认知框架与讲解偏好.md`
6. `DOCS/03_工程/阶段四：模型部署/02_implement/agent_context/00_INDEX.md`
7. `DOCS/03_工程/阶段四：模型部署/02_implement/agent_context/01_L1_ACT部署程序任务文档.md`
8. `DOCS/03_工程/阶段四：模型部署/02_implement/agent_context/02_L1_ACT功能模块边界.md`
9. `DOCS/03_工程/阶段四：模型部署/02_implement/agent_context/03_L1_ACT功能模块协作架构.md`
10. Pi0.5 reference source under `DOCS/03_工程/阶段四：模型部署/pi05_old/pi05_test/pi05/`

Read `references/l2-output-contract.md` when creating, migrating, or checking the final file tree.

Use `DOCS/03_工程/阶段四：模型部署/02_implement/ACT架构交互可视化.html` only as a visual quality reference. Do not copy ACT-wide content into a single-L2 visualization.

## Current L2 Identity Rules

Only these Stage 4 ACT L2 ids are valid current L2 identities:

- `l2-01-external-contract`
- `l2-02-observation-snapshot`
- `l2-03-act-inference`
- `l2-04-safety-guard`
- `l2-05-action-publisher`
- `l2-06-control-loop`

`l2-04-action-smoothing` is not a current first-version L2 identity. Action smoothing, smoothstep blending, cross-chunk fusion, and RTC-style alignment are follow-up optimization directions, not first-version L2 Gate scope.

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

## Semantic Alignment Rule

HTML and Markdown must be semantically one-to-one:

- Every HTML view must have an authoritative Markdown source in `agent_context/`.
- Every HTML view must be a compressed visual version of the corresponding Markdown section, never a separate design.
- Every HTML relationship, arrow, state owner, failure path, runtime path, Gate signal, or boundary statement must be traceable to a Markdown section.
- If HTML logic changes, update the authoritative Markdown in the same change.
- If Markdown semantics change, update the HTML projection in the same change or explicitly mark the HTML stale in both `00_INDEX.md` and the HTML note.

Implement this alignment mechanically:

- `agent_context/00_INDEX.md` must contain a `HTML-MD 语义对齐表`.
- Each row maps one HTML view id/label to authoritative Markdown file(s), Markdown section(s), and the extra detail that exists only in Markdown.
- Each HTML view root element should include `data-agent-source="agent_context/<file>.md#<section-or-anchor>"`.
- Each HTML view should visibly mention the relevant `agent_context` file in a compact source note or side panel.

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

`00_INDEX.md` is the Agent routing and alignment entry. It must describe:

- each Markdown file's responsibility;
- when to read it;
- HTML vs Markdown authority;
- `HTML-MD 语义对齐表`;
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
- follow the approved L2 HTML sample pattern: four radio-driven dimensions, not six generic architecture views;
- low text density: show core relationships, not complete Agent implementation detail;
- visual-first: use inline SVG diagrams, visual cards, arrows, swimlanes, state panels, code trace blocks, directory trees, classbox cards, and acceptance cards as appropriate;
- interactive: use pure CSS radio tabs, layer radio panes, `<details>`, hover states, and no-build controls; do not require a dev server;
- cite `agent_context/00_INDEX.md` and the relevant Agent Markdown files as authoritative;
- add `data-agent-source` on each view root and keep it aligned with `00_INDEX.md`;
- state clearly that HTML is not used for L3 generation.

Required top-level skeleton:

```text
header: h1 + subtitle + note that HTML is not L3 authority
input[type=radio]#v1..#v4
nav.tabs with labels:
  1 功能边界
  2 Pi0.5 如何运作
  3 开发蓝图
  4 人类验收标准
.views with exactly these four root sections:
  section.view.boundary[data-agent-source=...]
  section.view.pi05map[data-agent-source=...]
  section.view.blueprint[data-agent-source=...]
  section.view.acceptance[data-agent-source=...]
```

Each dimension section must include:

- `<div class="reading-path">...</div>`;
- `<p class="lead">...</p>`;
- at least one SVG figure or an equivalent sample-pattern visual component;
- a final `<p class="src">权威来源：...</p>` listing the authoritative `agent_context` files and sections.

Use these dimension responsibilities:

| Dimension | Question answered | Required sample-pattern components |
|---|---|---|
| `boundary` / 维度1 功能边界 | 做什么 / 不做什么 / 输入输出契约是什么？ | status/positioning SVG, startup processing SVG, responsible vs non-responsible boundary-wall SVG, data contract cards |
| `pi05map` / 维度2 Pi0.5 如何运作 | 参考源码如何运行，用白话讲清楚。 | plain-language callout, `details` terminology dictionary `.dict`, four-step `.flow`, `.trace`, bundle `.tree`, core-question cards |
| `blueprint` / 维度3 开发蓝图 | 代码如何分层，每层有哪些 micro-units？ | runtime/assembly SVG, six-layer `.lpick` radio panes, `.classbox` + `.mu-list` micro-unit breakdown, no-artifact layer panes |
| `acceptance` / 维度4 人类验收标准 | 怎么验证，跑什么，看到什么算通过或失败？ | sample-style `.vfy` groups, `.vfy-item` cards, command blocks, pass/fail phenomena, rationale links |

Do not reintroduce the old six-view contract as required HTML structure. Those architecture-report ideas may appear only as content inside the four approved dimensions when useful.

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
