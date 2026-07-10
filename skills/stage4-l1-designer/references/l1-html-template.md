# L1 Interactive HTML Visualization Template

This reference documents the structure of `{{SYSTEM}}架构交互可视化.html` — the L1 cross-module interactive HTML. Use the existing `ACT架构交互可视化.html` as the concrete reference implementation; clone its CSS, SVG layout, and interaction patterns, changing only the content.

## Key Invariants

1. **Zero JavaScript** — all interactivity via CSS `:checked` + sibling selectors
2. **CSS custom properties** for all colors (`:root { --m01: #HEX; ... }`)
3. **SVG** with `viewBox`, `<defs>/<marker>` for arrows, `<g>` groups with semantic classes
4. **System font stack**: `system-ui, -apple-system, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif`
5. **Responsive**: `@media (max-width: 820px)` breakpoints
6. **No external dependencies** — zero CDN links, zero npm packages

## HTML Skeleton

```html
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{{SYSTEM}} 部署程序 · L2 协作主线与模块边界</title>
  <style>
    :root {
      --bg: #f6f7f9; --ink: #1f2937; --muted: #667085; --line: #d0d5dd; --panel: #ffffff;
      --config: #2563eb;   /* L2-01 color */
      --obs: #0f766e;      /* L2-02 color */
      --model: #7c3aed;    /* L2-03 color */
      --safety: #c2410c;   /* L2-04 color */
      --output: #047857;   /* L2-05 color */
      --ctrl: #344054;     /* L2-06 color */
      --warn: #b42318; --ok: #047857;
    }
    /* ... full CSS from reference file ... */
  </style>
</head>
<body>
  <div class="page">
    <header>
      <h1>{{SYSTEM}} 部署程序 · L2 协作主线与模块边界</h1>
      <p class="subtitle">{{ONE_PARAGRAPH_SUMMARY}}</p>
      <div class="note">{{AUTHORITY_NOTE: HTML is human entry; MD is authoritative}}</div>
    </header>

    <div class="viz">
      <!-- N hidden radio inputs, one per module -->
      <input id="m01" name="mod" type="radio">
      <input id="m02" name="mod" type="radio">
      ...
      <input id="m0N" name="mod" type="radio" checked>

      <!-- SVG main figure -->
      <div class="figure">
        <svg viewBox="0 0 {{W}} {{H}}" role="img">
          <defs>
            <marker id="arrow" viewBox="0 0 10 10" markerWidth="10" markerHeight="10" refX="9" refY="5" orient="auto">
              <path d="M0,0 L10,5 L0,10 z" fill="#475467"></path>
            </marker>
          </defs>
          <!-- L2-01 top bar (config injection) -->
          <!-- External input box -->
          <!-- Main pipeline nodes (L2-02 to L2-05) -->
          <!-- External output box -->
          <!-- Edges with numbered callout markers -->
          <!-- L2-06 bottom scheduling bar -->
        </svg>
      </div>

      <!-- Glossary + legend -->
      <div class="gloss">...</div>

      <p class="hint">↓ 点击模块查看其功能边界（主图保持可见，选中节点高亮）</p>

      <!-- Module selector bar -->
      <div class="modbar">
        <label for="m01"><i class="mdot" style="background:var(--config)"></i>L2-01 {{SHORT_NAME}}</label>
        ...
      </div>

      <!-- Detail panels (one per module, identical structure) -->
      <div class="bpanel p01">
        <div class="bp-head"><h3>L2-01 {{FULL_NAME}}</h3><code>{{l2_id}}</code></div>
        <div class="bp-grid">
          <div class="bp-cell def full">
            <p class="bp-label">功能定义</p>
            <p>{{PARAGRAPH}}</p>
          </div>
          <div class="bp-cell io">
            <p class="bp-label">输入</p>
            <p>{{LIST}}</p>
          </div>
          <div class="bp-cell io">
            <p class="bp-label">输出</p>
            <p>{{LIST}}</p>
          </div>
          <div class="bp-cell resp">
            <p class="bp-label">负责内容</p>
            <ul>...</ul>
          </div>
          <div class="bp-cell noresp">
            <p class="bp-label">不负责内容</p>
            <ul>...</ul>
          </div>
        </div>
      </div>
      <!-- Repeat .bpanel for each module -->

      <!-- Bottom callout -->
      <div class="callout">{{V1_SCOPE_WARNING}}</div>
    </div>
  </div>
</body>
</html>
```

## SVG Layout Convention

For an N-module pipeline (default: 6):

```
        ┌────────── L2-01 (top, centered, ~420px wide) ──────────┐
        │  config lines (dotted) drop down to each module         │
        └──────────────────────────────────────────────────────────┘

┌────────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌────────┐
│ 外部   │→│L2-02│→│L2-03│→│L2-04│→│L2-05│→│ 外部   │
│ 输入   │ │ 观测 │ │ 推理 │ │ 安全 │ │ 输出 │ │ 执行   │
└────────┘ └──────┘ └──────┘ └──────┘ └──────┘ └────────┘
        ↑         ↑          ↑          ↑          ↑
        └─────────┴──────────┴──────────┴──────────┘
                  L2-06 (bottom bar, full-width, ~857px)
```

- viewBox: `0 0 1140 322` (adjust width if N ≠ 6)
- Module boxes: ~150px wide, ~86px tall, ~60px gaps
- L2-01: wider (~420px), y=10, height=44, centered
- L2-06: y=240, height=58, full-width bar
- Colored left accent strips: 7px wide on each box
- Numbered callout circles: r=8, on edges

## Edge Class Conventions

| Edge type | CSS class | Stroke style | Use case |
|-----------|-----------|-------------|----------|
| Sync data | `.e-data` | solid #667085 | Forward data flow between modules |
| Control call | `.e-control` | dashed #344054 | L2-06 scheduling calls to modules |
| Async axis | `.e-async` | dashed var(--model) | Async inference path |
| External topic | `.e-topic` | solid var(--output) | ROS topic publish |
| Config injection | `.e-config` | dotted var(--config), thin | Startup resource injection |

## CSS Selector Rules (one set per module)

```css
/* Highlight selected module node */
#m01:checked ~ .figure svg .n01 .nbox { stroke: var(--config); stroke-width: 2.8; }

/* Show selected module's detail panel */
#m01:checked ~ .bpanel.p01 { display: block; }

/* Highlight selected module's tab in modbar */
#m01:checked ~ .modbar label[for="m01"] { color: var(--ink); font-weight: 650; border-color: var(--ctrl); }
```

## Detail Panel Structure (identical for every module)

Each `.bpanel` contains:
- `bp-head`: `<h3>` title + `<code>` l2_id
- `bp-grid` (2-column grid):
  - `bp-cell.def.full` — 功能定义 (spans both columns)
  - `bp-cell.io` × 2 — 输入 / 输出
  - `bp-cell.resp` — 负责内容 (green markers)
  - `bp-cell.noresp` — 不负责内容 (red-tinted, red markers)

## Numbered Callout Markers

Each edge has a numbered circle marker:
```html
<g class="cmark"><circle cx="{{X}}" cy="{{Y}}" r="8"></circle><text x="{{X}}" y="{{Y+3}}" text-anchor="middle">{{N}}</text></g>
```

Numbers 1–5: forward edges (L2-06 → modules, left to right)
Numbers 6–9: upward state edges (L2-06 ← modules)
Glossary `<dl>` pairs each number with its description.

## Generation Pre-Flight

Before generating the HTML:
1. Read the reference `ACT架构交互可视化.html` (at `DOCS/03_工程/阶段四：模型部署/02_implement/ACT架构交互可视化.html`)
2. Clone its CSS block entirely — only change `:root` color variables
3. Clone its SVG structure — change node positions if N ≠ 6
4. Fill content from user interview answers
5. Verify each `data-agent-source` attribute points to correct MD file
