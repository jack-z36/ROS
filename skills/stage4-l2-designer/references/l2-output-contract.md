# Stage 4 L2 Design Output Contract

Use this reference when creating, migrating, or checking a Stage 4 L2 design package.

## Required File Tree

```text
DOCS/03_工程/阶段四：模型部署/02_implement/<l2_id>_<l2_name>/
├── L2架构交互可视化.html
└── agent_context/
    ├── 00_INDEX.md
    ├── 01_L2功能边界.md
    ├── 02_pi05源码3.5层微元拆解.md
    ├── 03_ACT微元设计与协作.md
    ├── 03a_功能微元总览与组织结构.md
    ├── 04_L2验收机制.md
    ├── 05_人类验收机制.md
    ├── 06_types层设计.md
    ├── 07_config层设计.md
    ├── 08_repo层设计.md
    ├── 09_service层设计.md
    ├── 10_runtime层设计.md
    └── 11_ui层设计.md
```

The root is the human entry surface. All Agent Markdown must live in `agent_context/`. Do not create `types/`, `config/`, `repo/`, `service/`, `runtime/`, or `ui/` directories inside the L2 design package.

## Valid L2 Identity

Current valid `l2_id` values:

- `l2-01-external-contract`
- `l2-02-observation-snapshot`
- `l2-03-act-inference`
- `l2-04-safety-guard`
- `l2-05-action-publisher`
- `l2-06-control-loop`

`l2-04-action-smoothing` is not a valid first-version L2 identity. Treat action smoothing, smoothstep blending, cross-chunk fusion, and RTC-style alignment as follow-up optimization scope unless the L1 documents are explicitly redesigned again.

Old `l2-01-types`, `l2-02-config`, `l2-03-assembly`, `l2-04-publish`, and `l2-05-hardware` are invalid current L2 identities. They may appear only inside explicit contamination checks, deprecation notes, or read-only history/reference statements.

## Semantic Alignment Contract

HTML and Markdown are a paired product:

- HTML is the human projection.
- `agent_context/*.md` is the Agent source of truth.
- Every HTML view must map to one or more Markdown files and sections.
- Every semantic change in HTML must be applied to Markdown in the same change.
- Every semantic change in Markdown must update the corresponding HTML view, or both `00_INDEX.md` and HTML must mark HTML as stale.

`agent_context/00_INDEX.md` must contain a section titled exactly:

```text
## HTML-MD 语义对齐表
```

The table must include these columns:

| HTML view id | HTML view label | Human-visible meaning | Authoritative Markdown | Required Markdown section | Markdown-only detail |
|---|---|---|---|---|---|

Each HTML view root must include:

```html
<section class="view ..." data-agent-source="agent_context/<file>.md#<section-or-anchor>">
```

The `data-agent-source` file must exist. The file path must also appear in `00_INDEX.md`.

## agent_context/00_INDEX.md

Must include:

- `l2_id` and human-readable L2 name.
- Human HTML entry path.
- Statement that `agent_context/*.md` is authoritative for Agent work.
- Route table mapping reading purpose to file.
- `HTML-MD 语义对齐表`.
- Contamination check terms and allowed context.
- Statement that HTML is not used for L3 generation.

## agent_context/01_L2功能边界.md

Must include:

- `l2_id`, `l2_design_dir`, and human-readable L2 name.
- L1 task doc path.
- L1 Agent boundary doc path and collaboration doc path.
- Legacy / Contract Delta / Stage 2 template contamination check.
- One-sentence runtime responsibility.
- Inputs.
- Outputs.
- Responsibilities.
- Non-responsibilities.
- Upstream and downstream L2s.
- Completion criteria.
- Questions still requiring user decision.

## agent_context/02_pi05源码3.5层微元拆解.md

Must classify source contents using the user's 3.5-layer vocabulary:

| Micro-unit type | Required details |
|---|---|
| 数据 | Constants, fields, dimensions, buffers, config objects. |
| 计算函数 | RAM-in, RAM-out transformations. |
| 内部状态更新函数 | Buffer, queue, cache, metrics, state mutation. |
| 数据读写函数 | File, ROS topic, model weight, hardware, network boundary. |
| 编排函数 | Timing, order, concurrency, failure handling. |

Also include a class packaging table:

| class | state | packaged micro-units | lifecycle/concurrency | why class | ACT recommendation |
|---|---|---|---|---|---|

Source range matching is an internal working step. Do not create a separate source range matching file. Preserve useful results by including exact Pi0.5 paths, object names, existing capabilities, ACT gaps, reuse decisions, and risks inside the micro-unit tables.

## agent_context/03_ACT微元设计与协作.md

Must include:

| ACT micro-unit | 3.5 type | target layer | target file | function/class | inputs | outputs | side effects | Pi0.5 reference |
|---|---|---|---|---|---|---|---|---|

Must also include an internal collaboration explanation:

```text
Creation order:
State owner:
Pure RAM calculations:
External boundary reads/writes:
Runtime orchestration point:
Failure propagation:
```

This file is the main bridge from Pi0.5 source understanding to ACT implementation design. It must mark unresolved class/function, state ownership, runtime, or hardware decisions as blocking until user-confirmed.

## agent_context/03a_功能微元总览与组织结构.md

Must be the single source of truth for the L2 functional-micro-unit system:

- A/B/C total counts and numbering convention.
- One table mapping every unit to its 3.25/3.375/3.5 type, parent and responsibility.
- Runtime call tree and overall collaboration trace.
- Upstream reused objects explicitly marked as not newly numbered.
- Statement that implementation, L3, validation and HTML blueprint work must read this file first when referring to unit IDs.

## agent_context/04_L2验收机制.md

Must include:

- L2 Gate objective.
- Required L3 list draft.
- Verification layers: unit/import/mock/dry-run/shadow-run/real-robot.
- Commands or command placeholders.
- Test inputs.
- Observation points.
- Pass phenomena.
- Fail phenomena.
- Blocked items.
- Whether downstream L2 may start.
- Whether Git merge to `model_deploy` is allowed.

## agent_context/05_人类验收机制.md

Must include:

- Human acceptance checklist.
- cwd and command for each item.
- Required environment or hardware.
- Test input.
- Observation point.
- Pass phenomenon.
- Fail phenomenon and debug entry.
- Risk level.
- Signature location in `05_acceptance/<l2>/验收结果.md`.

Use this signature shape:

```markdown
## 人类验收

- 验收人：<用户名>
- 验收日期：YYYY-MM-DD
- 验收结论：[ ] 已通过  [ ] 不通过
- 逐项结果：
  - 验收项 1：<命令> -> <通过现象> -> [ ] 通过
- 备注：
```

## Six-Layer Design Files

The six files are:

- `06_types层设计.md`
- `07_config层设计.md`
- `08_repo层设计.md`
- `09_service层设计.md`
- `10_runtime层设计.md`
- `11_ui层设计.md`

Each file must include:

- Target source path or explicit "no artifact in this layer".
- Layer responsibility.
- File responsibility.
- Class design.
- Function design.
- Inputs and outputs.
- Side effects.
- Dependency direction.
- Statement that the file's task boundary is inherited from the current L1/L2 functional boundary, not from old layer-based L2 cards.
- Pi0.5 reference.
- Acceptance coverage.

When a layer file describes a 3.5 micro-unit or its fields, use the user's cognitive presentation contract:

| 3.5 type | Required representation |
|---|---|
| 数据 | For every variable/field: variable name, internal storage structure, and internal stored data type. Dataclasses list fields individually; arrays state shape and element dtype; Enum lists allowed values. |
| 计算函数 | RAM input object type + shape/structure; RAM output or exception; explicit statement that it does not read/write process-external resources. |
| 内部状态更新函数 | The RAM object/variable modified and how it changes (replace, append, accumulate, clear, etc.). |
| 数据读写函数 | External boundary (path/topic/handle/endpoint) and the object read into RAM or written out, with type + shape/structure. |
| 编排函数 | Call condition, ordered steps, skip condition, and failure propagation. |

The same representation must appear in dimension-3 图③ `.mu-list`; human HTML may compress wording but must not merge these distinct types into a generic “field/type” or “input/output” description.

If a layer adds no source artifact, the corresponding file must still exist and include:

```text
本 L2 不在该层新增源码产物。
原因：
验收如何确认：
```

## L2架构交互可视化.html

Must be a standalone static HTML document that helps a human inspect this L2 quickly.

Required properties:

- root-level file named exactly `L2架构交互可视化.html`;
- self-contained `<!doctype html>` file with inline CSS and no network dependencies;
- clear title, subtitle, and note that `agent_context/*.md` is authoritative if HTML conflicts with Markdown;
- visual-first, low-text presentation using inline SVG diagrams, visual cards, arrows, swimlanes, state panels, or similar graphics;
- interaction through radio tabs, toggles, `<details>`, hover states, or equivalent no-build controls;
- explicit references to `agent_context/00_INDEX.md` and relevant Agent Markdown files;
- `data-agent-source` on every HTML view root;
- stable `l2_id`.

The HTML must follow the approved L2 sample pattern, not the older six-view architecture report pattern. Use exactly four top-level dimensions:

```text
header: h1 + subtitle + authority note
input[type=radio]#v1..#v4
nav.tabs:
  1 功能边界
  2 Pi0.5 如何运作
  3 开发蓝图
  4 人类验收标准
.views:
  section.view.boundary
  section.view.pi05map
  section.view.blueprint
  section.view.acceptance
```

Each dimension root section must include `data-agent-source`, a `reading-path`, a `lead` paragraph, visual content, and a final `<p class="src">权威来源：...</p>`.

Required dimensions:

| Dimension | Required content | Typical authoritative Markdown |
|---|---|---|
| `boundary` / 维度1 功能边界 | Explain what this L2 does and does not do. Use a single **图① 消费 → 功能模块 → 产出** `.io-flow`（left `.io-card` inputs with `.io-src` badges, center `.io-module` with the main entry function + `.pipe`, right `.io-card ok` output contract）. **No `<svg>` in dimension 1.** Old positioning / boundary-wall / contract SVG and the `.grid.g2` 负责/不负责 card pair are forbidden; fold that content into `.nested-detail` inside the relevant `.io-card`. | `01_L2功能边界.md` |
| `pi05map` / 维度2 Pi0.5 如何运作 | Explain the matching Pi0.5 source in plain language. Use a terminology dictionary `.dict`, four-step `.flow`, trace block `.trace`, bundle directory `.tree`, source-difference callouts, and core-question cards. | `02_pi05源码3.5层微元拆解.md` |
| `blueprint` / 维度3 开发蓝图 | Use three distinct visual representations: **图①** horizontal runtime SVG swimlane with numbered typed nodes, dashed compile-time injection banner, red dashed reject-stop branches, explicit result return arrow, legend and collaboration callout; **图②** exactly three A/B/C `.ovtab` tables (编号 / 名称 / 类型 / 基础介绍) from `03a`, each with colored count header; **图③** exactly six `types/config/repo/service/runtime/ui` radio tabs and panes, with `.classbox` + `.mu-list` for products and reason + owner + acceptance for no-product panes. Every `数据` `.mu` uses a three-column field table: 变量名 / 内部存储结构 / 内部存储的数据类型; the other four 3.5 types use their distinct behavior labels. **Every `.classbox` must live inside its layer's `.lpane` within the `.lpick` region；no `.classbox` and no extra `<h3>` after the `.lpick` closing tag**（so clicking a six-layer tab reveals the full micro-unit breakdown inline）. | `03a_功能微元总览与组织结构.md`, `03_ACT微元设计与协作.md`, `06-11_*层设计.md` |
| `acceptance` / 维度4 人类验收标准 | Explain how a human verifies the L2 with numbered `.vfy-item` cards: item 1 gives one `.sh` script command; item 2 contains a `.term` terminal example（layered grouping with FAIL `.t-loc` location）and `.trtab` translation table（label → layer → complete file→class→micro-unit location chain → PASS meaning / FAIL where to look）; later items retain distinct boundary, landing, coordination and hardware-blocked checks. | `04_L2验收机制.md`, `05_人类验收机制.md` |

The old six-view labels from the architecture-report pattern must not be required or used as top-level view labels. Their semantics may be folded into the four approved dimensions.

The HTML must not:

- Pull scripts, fonts, styles, images, or CSS from the network.
- Use bitmap images as the default visualization method; prefer inline SVG.
- Copy ACT-wide example content as if it were this L2's design.
- Use Contract Delta, legacy L2 ids, or Stage 2 templates as the current boundary.
- Hide unresolved design decisions that remain blocking.

## Required Interaction Checkpoints

During L2 design, stop for user confirmation at these checkpoints:

1. L2 boundary: inputs, outputs, responsibilities, non-responsibilities, upstream/downstream.
2. ACT micro-units and class/function design: Pi0.5 reuse decision and six-layer landing points.
3. HTML information hierarchy and L2 Gate: what humans inspect, what Agents read, and how Gate passes.

## Ready For L3 Criteria

The L2 is ready for L3 generation only when:

- Pi0.5 source range is mapped.
- Pi0.5 3.5-layer source micro-units are explained.
- ACT micro-units and class/function decisions are confirmed by the user.
- All 13 `agent_context/` files exist, including the A/B/C overview and organization authority.
- `00_INDEX.md` contains a valid `HTML-MD 语义对齐表`.
- Each HTML view has a valid `data-agent-source` reference to existing Agent Markdown.
- L2 Gate exists.
- Human acceptance mechanism exists.
- Human HTML visualization exists and aligns with the Markdown design docs.
- Open user decisions are either resolved or explicitly marked as blocking.
- The package passed the legacy / Contract Delta / Stage 2 template contamination check.

## Validation

Run:

```bash
python3 skills/stage4-l2-designer/scripts/validate_l2_design_package.py DOCS/03_工程/阶段四：模型部署/02_implement/<l2_id>_<l2_name>
```

Expected result:

- root contains only `L2架构交互可视化.html` and `agent_context/`;
- all 13 fixed Markdown files exist;
- no six-layer subdirectories exist;
- HTML contains doctype, the four approved radio dimensions, sample-pattern visual components, `agent_context` references, stable L2 id, and valid `data-agent-source` links;
- `00_INDEX.md` contains the semantic alignment table;
- legacy and Contract Delta terms appear only in allowed contamination/deprecation/read-only contexts.
