---
name: stage4-l1-designer
description: Produce and maintain the Stage 4 ACT L1 cross-module design package in this ROS repository. Use when designing, reviewing, or migrating the top-level ACT architecture documentation — creating the 4 agent_context Markdown files (task, boundary, collaboration, INDEX) and the interactive cross-module HTML pipeline visualization (ACT架构交互可视化.html). This skill covers the L1 system overview that defines all L2 modules, their boundaries, collaboration architecture, and shared data contracts. For single-L2 deep-dive design packages with 12 agent_context files + 4-dimension HTML, use stage4-l2-designer.
---

# Stage4 L1 Designer

## Purpose

Produce the Stage 4 ACT L1 cross-module design package — the single source of truth for how all N L2 modules fit together. This skill generates:

- **Agent-consumable Markdown** under `agent_context/`: 4 files covering the system task, per-module boundaries, and collaboration architecture.
- **Human-consumable HTML**: a zero-JS interactive pipeline visualization (`{{SYSTEM}}架构交互可视化.html`) with SVG main figure, module selector bar, and detail panels.

This is the **L1 foundation** that all L2 design packages inherit from. Use `stage4-l2-designer` after this package is confirmed to design individual L2 modules.

## Required Context

Before any L1 design work, read in order:

1. `AGENTS.md`
2. `DOCS/02_约束/上下文加载/03_非具体编程规划加载规则.md`
3. Existing L1 design package (if any):
   - `DOCS/03_工程/阶段四：模型部署/02_implement/agent_context/00_INDEX.md`
   - `DOCS/03_工程/阶段四：模型部署/02_implement/agent_context/01_L1_ACT部署程序任务文档.md`
   - `DOCS/03_工程/阶段四：模型部署/02_implement/agent_context/02_L1_ACT功能模块边界.md`
   - `DOCS/03_工程/阶段四：模型部署/02_implement/agent_context/03_L1_ACT功能模块协作架构.md`
4. Existing L1 HTML reference:
   - `DOCS/03_工程/阶段四：模型部署/02_implement/ACT架构交互可视化.html`
5. For L2 modules already designed, their `agent_context/01_L2功能边界.md` files to ensure L1 consistency.

## L1 vs L2 Scope

| Aspect | L1 (this skill) | L2 (stage4-l2-designer) |
|---|---|---|
| Scope | Cross-module system overview | Single module deep-dive |
| agent_context files | 4 (INDEX, task, boundary, collaboration) | 12 (INDEX, boundary, pi05map, micro-units, acceptance × 2, 6 layer files) |
| HTML | 1 pipeline SVG + N detail panels | 4 tabbed dimensions (boundary, pi05map, blueprint, acceptance) |
| Key questions | "What are the modules and how do they work together?" | "How does this specific module work internally?" |
| Object ownership | Defines who owns what across all modules | Implements single module's ownership contract |
| Downstream consumer | stage4-l2-designer (all L2s) | stage4-l3-generator (per L2) |

## Current L1 Identity Rules

- The current L1 system is "ACT 部署程序" with 6 L2 modules: `l2-01-external-contract`, `l2-02-observation-snapshot`, `l2-03-act-inference`, `l2-04-safety-guard`, `l2-05-action-publisher`, `l2-06-control-loop`.
- Legacy layer-based L2 IDs (`l2-01-types`, `l2-02-config`, `l2-03-assembly`, `l2-04-publish`, `l2-05-hardware`) are **forbidden** as identity or authority.
- Old "ACT Contract Delta" or "AS-IS → TO-BE → Contract Delta" patterns are **forbidden**.
- `DOCS/03_工程/阶段四：模型部署/02_implement/归档/` is read-only; must not be edited or used as authority.
- Action smoothing, cross-chunk fusion, RTC, and complex time alignment are out of scope for v1; must not appear in L1 docs.

## Output Shape

The L1 package lands under the implement directory:

```text
DOCS/03_工程/阶段四：模型部署/02_implement/
├── {{SYSTEM}}架构交互可视化.html          # Human interactive HTML
└── agent_context/                           # Agent-authoritative Markdown
    ├── 00_INDEX.md                          # Routing hub
    ├── 01_L1_{{SYSTEM}}部署程序任务文档.md   # Task document
    ├── 02_L1_{{SYSTEM}}功能模块边界.md       # Module boundary document
    └── 03_L1_{{SYSTEM}}功能模块协作架构.md   # Collaboration architecture
```

## Workflow

### 1. Scope Discovery

Ask the user to confirm:
- Is this a new L1 package from scratch, or an update to the existing ACT L1?
- If updating: which sections need changes? (new L2 added? boundaries revised? collaboration flow changed?)
- Target directory: default to `DOCS/03_工程/阶段四：模型部署/02_implement/`.

Stop and wait for user confirmation before proceeding.

### 2. Module Inventory Interview

If creating from scratch or adding modules, interview the user for each L2:

| Question | Example Answer |
|---|---|
| L2 ID (stable) | `l2-03-act-inference` |
| Chinese boundary name | ObservationSnapshot 到 ActionChunk 业务计算 |
| One-line responsibility | 使用已注入的配置、normalizer 和 policy，把 snapshot 同步计算为 ActionChunk |
| Color (hex) | `#7c3aed` |
| Role type | 启动资源 / RAM业务 / ROS输出 / 中央运行 |
| Inputs (what it consumes) | DeployConfig, state_normalizer, action_normalizer, ACT policy, ObservationSnapshot |
| Outputs (what it produces) | ActionChunk (chunk_size, 16) float32 |
| Responsibilities (bullets) | ... |
| Non-responsibilities (bullets with delegation) | ... |
| State it holds | 只读持有 L2-01 注入的配置/normalizer/policy 引用 |
| Failure boundary | policy 计算失败返回明确错误，不返回伪造 chunk |
| Completion criteria | 不创建线程和 queue 的单测中可验证同步业务转换 |

Repeat for each module. Stop after each module to confirm accuracy.

### 3. Shared Contract Definition

Define cross-module invariants:
- Shared data dimensions (e.g., 16D state/action)
- Segment semantics (e.g., [0:3] left TCP position in m)
- Unit conventions (m for positions, (x,y,z,w) for quaternions, [0,1] for internal gripper)
- Scale conversion boundaries (who converts external scales to internal, who converts back)

### 4. Collaboration Architecture Interview

Ask and record:
- **Startup sequence**: ordered steps, resource propagation, failure at each step
- **Steady-state data flow**: main pipeline from ROS input → observation → inference → safety → publish → ROS output
- **Object ownership**: for each key object, who creates, who maintains, who reads
- **Sync/async boundaries**: which calls are synchronous, which run on independent axes
- **Failure propagation**: for each failure source, who detects, what's returned, who handles fallback
- **Running modes**: dry-run, shadow-run, safe-run behaviors
- **Shutdown sequence**: safe stop order

### 5. Generate agent_context Markdown

Generate the 4 files in this order (each depends on the previous for consistency):

1. `agent_context/01_L1_{{SYSTEM}}部署程序任务文档.md` — task document
2. `agent_context/02_L1_{{SYSTEM}}功能模块边界.md` — boundary document
3. `agent_context/03_L1_{{SYSTEM}}功能模块协作架构.md` — collaboration architecture
4. `agent_context/00_INDEX.md` — index (last, cross-references all others)

For section templates, see [references/l1-md-templates.md](references/l1-md-templates.md). For concrete examples, read the existing L1 files at `DOCS/03_工程/阶段四：模型部署/02_implement/agent_context/`.

**Invariant**: every Markdown file must preserve the `> [!info]` header callout declaring document responsibility, the Obsidian-style admonition syntax, table-based structured data, and explicit "NOT responsible" delegation patterns.

### 6. Generate HTML Visualization

Generate `{{SYSTEM}}架构交互可视化.html`. **Read the reference file first** — open `DOCS/03_工程/阶段四：模型部署/02_implement/ACT架构交互可视化.html` and clone its structure exactly, changing only content.

For the HTML skeleton and SVG layout conventions, see [references/l1-html-template.md](references/l1-html-template.md).

Key invariants when generating HTML:
- **Zero JavaScript** — all interactivity via CSS `:checked` + sibling selectors
- **One radio input per L2 module** (`<input id="m01" name="mod" type="radio">`)
- **One detail panel per L2 module** (`<div class="bpanel p01">`)
- **CSS :checked rules** for highlighting selected node and showing selected panel
- **SVG** with proper `viewBox`, `<defs>/<marker>`, edge numbering
- **`data-agent-source`** attributes on views pointing to authoritative MD files
- Each panel must have identical structure: `bp-head` → `bp-grid` → `bp-cell.def` → `bp-cell.io × 2` → `bp-cell.resp` → `bp-cell.noresp`

### 7. Validate

Run the structural validator:

```bash
python3 skills/stage4-l1-designer/scripts/validate_l1_design_package.py DOCS/03_工程/阶段四：模型部署/02_implement/
```

Manual validation checks:
- Every L2 ID in `00_INDEX.md` appears in `02_*功能模块边界.md`
- Every L2 in the boundary doc's boundary matrix matches the HTML SVG nodes
- HTML module count = INDEX module count = boundary doc module count
- Object ownership table in `03_*协作架构.md` has no gaps — every key object has creator/maintainer/consumer
- Failure propagation chain in `03_*协作架构.md` covers every failure source from every L2
- Pollution check in `00_INDEX.md` covers all forbidden legacy terms
- No two L2s claim "拥有" (ownership) of the same responsibility

If validation fails, fix issues and re-validate. Do not proceed to handoff until validation passes.

## Semantic Alignment Rule

The L1 HTML and agent_context Markdown must stay bidirectionally aligned. This is a hard constraint:

- Every L2 detail panel in the HTML must correspond to exactly one `## X.` section in `02_L1_*功能模块边界.md`.
- Every SVG edge label and glossary entry in the HTML must correspond to a collaboration path described in `03_L1_*功能模块协作架构.md`.
- HTML is the human-projectable view; Markdown is the agent-authoritative view. When they conflict, Markdown wins, and the HTML must be updated.
- `00_INDEX.md` must contain an `HTML-MD 语义对齐表` (see existing for format) that maps each HTML element to its authoritative MD section and notes what Markdown detail the HTML omits.

## Output Rules

- Do **not** generate L3 tasks. This skill produces L1 design documentation only.
- Do **not** edit any file under `DOCS/03_工程/阶段四：模型部署/02_implement/l2-*/`. L2 packages are `stage4-l2-designer` territory.
- Do **not** create new `src/` code files. This is documentation, not implementation.
- Do **not** reference `DOCS/98_archive/` or `DOCS/99_learning/` unless the user explicitly asks for historical material.
- Do **not** use legacy layer-based L2 IDs or old Contract Delta terminology except in explicit pollution-check or deprecation context.
- Do **not** fix L2-03 through L2-06 internal class names, function signatures, or file structures in L1 docs — only cross-module contracts.

## Handoff

After completion, report:

- L1 system name and module count
- Files created or updated, with paths relative to repo root
- L2 IDs covered
- Validation result (pass/fail + any remaining warnings)
- Any sections intentionally left as placeholders (marked `<!-- TODO -->`)
- Suggested next step: "Run `stage4-l2-designer` to design individual L2 modules" or "Review HTML in browser and confirm alignment"
