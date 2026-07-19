#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path


REQUIRED_AGENT_FILES = [
    "00_INDEX.md",
    "01_L2功能边界.md",
    "02_pi05源码3.5层微元拆解.md",
    "03_ACT微元设计与协作.md",
    "03a_功能微元总览与组织结构.md",
    "04_L2验收机制.md",
    "05_人类验收机制.md",
    "06_types层设计.md",
    "07_config层设计.md",
    "08_repo层设计.md",
    "09_service层设计.md",
    "10_runtime层设计.md",
    "11_ui层设计.md",
]

OLD_LAYER_DIRS = {"types", "config", "repo", "service", "runtime", "ui"}

CONTAMINATION_TERMS = [
    "l2-01-types",
    "l2-02-config",
    "l2-03-assembly",
    "l2-04-publish",
    "l2-05-hardware",
    "ACT Contract Delta",
    "AS-IS Contract -> TO-BE Contract -> Contract Delta",
    "阶段二开发范式",
    "L2能力模块说明文件模板",
]

REQUIRED_HTML_VIEWS = [
    ("boundary", "功能边界"),
    ("pi05map", "Pi0.5 如何运作"),
    ("blueprint", "开发蓝图"),
    ("acceptance", "人类验收标准"),
]

REQUIRED_HTML_COMPONENTS = [
    (".reading-path", 'class="reading-path"', "HTML missing sample reading-path component"),
    (".lead", 'class="lead"', "HTML missing lead paragraph component"),
    (".figure", 'class="figure"', "HTML missing figure wrapper component"),
    (".dict", 'class="dict"', "HTML missing terminology dictionary component: .dict"),
    (".flow", 'class="flow"', "HTML missing four-step flow component: .flow"),
    (".trace", 'class="trace"', "HTML missing trace component: .trace"),
    (".tree", 'class="tree"', "HTML missing bundle tree component: .tree"),
    (".lpick", 'class="lpick"', "HTML missing six-layer radio picker component: .lpick"),
    (".classbox", 'class="classbox"', "HTML missing classbox component"),
    (".mu-list", 'class="mu-list"', "HTML missing micro-unit list component"),
    (".vfy", 'class="vfy"', "HTML missing dimension-4 numbered acceptance checklist: .vfy"),
    (".vfy-item", 'class="vfy-item"', "HTML missing dimension-4 acceptance checklist card: .vfy-item"),
    (".term", 'class="term"', "HTML missing dimension-4 .term terminal example block"),
    (".trtab", 'class="trtab"', "HTML missing dimension-4 .trtab translation table"),
]

OLD_REQUIRED_HTML_VIEW_LABELS = [
    "Over" + "view",
    "Data" + "flow",
    "Control/runtime " + "flow",
    "Failure/" + "fallback",
    "Metrics/status/" + "acceptance",
    "Boundary " + "contract",
]

ALLOWED_CONTAMINATION_CONTEXT = re.compile(
    r"(污染|旧|历史|废弃|作废|legacy|Legacy|只读|参考|不来自|不得|禁止|隔离|归档|"
    r"contamination|deprecated|read-only|archive|invalid|not from|old layer-based)",
    re.IGNORECASE,
)


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def infer_l2_id(package: Path) -> str:
    match = re.search(r"(l2-\d{2}-[a-z0-9-]+)", package.name)
    return match.group(1) if match else ""


def check_root(package: Path, errors: list[str]) -> None:
    allowed = {"L2架构交互可视化.html", "agent_context"}
    for child in package.iterdir():
        if child.name not in allowed:
            errors.append(f"unexpected root entry: {child.name}")
    for dirname in OLD_LAYER_DIRS:
        if (package / dirname).exists():
            errors.append(f"old six-layer design directory remains: {dirname}/")
    if not (package / "L2架构交互可视化.html").is_file():
        errors.append("missing root human HTML: L2架构交互可视化.html")
    if not (package / "agent_context").is_dir():
        errors.append("missing Agent context directory: agent_context/")


def check_agent_context(package: Path, errors: list[str]) -> None:
    agent_dir = package / "agent_context"
    if not agent_dir.is_dir():
        return
    for filename in REQUIRED_AGENT_FILES:
        if not (agent_dir / filename).is_file():
            errors.append(f"missing Agent Markdown: agent_context/{filename}")
    for child in agent_dir.iterdir():
        if child.is_file() and child.suffix == ".md" and child.name not in REQUIRED_AGENT_FILES:
            errors.append(f"unexpected Agent Markdown: agent_context/{child.name}")

    index = agent_dir / "00_INDEX.md"
    if not index.is_file():
        return
    text = index.read_text(encoding="utf-8")
    for filename in REQUIRED_AGENT_FILES[1:]:
        if filename not in text:
            errors.append(f"00_INDEX.md does not route to {filename}")
    if "L2架构交互可视化.html" not in text:
        errors.append("00_INDEX.md does not reference the human HTML entry")
    if "HTML-MD 语义对齐表" not in text:
        errors.append("00_INDEX.md missing HTML-MD semantic alignment table")
    required_alignment_headers = [
        "HTML view id",
        "HTML view label",
        "Human-visible meaning",
        "Authoritative Markdown",
        "Required Markdown section",
        "Markdown-only detail",
    ]
    for header in required_alignment_headers:
        if header not in text:
            errors.append(f"00_INDEX.md semantic alignment table missing column: {header}")


def check_html(package: Path, l2_id: str, errors: list[str]) -> None:
    html_path = package / "L2架构交互可视化.html"
    if not html_path.is_file():
        return
    text = html_path.read_text(encoding="utf-8")
    lower = text.lower()
    if "<!doctype html>" not in lower:
        errors.append("HTML missing <!doctype html>")
    if "<svg" not in lower:
        errors.append("HTML missing inline SVG")
    if "agent_context" not in text:
        errors.append("HTML does not reference agent_context/")
    if l2_id and l2_id not in text:
        errors.append(f"HTML missing stable l2_id: {l2_id}")
    if not any(marker in lower for marker in ('type="radio"', "<details", "class=\"view", "data-view")):
        errors.append("HTML missing simple interaction controls")
    if re.search(r"https?://|//fonts\.|@import", text):
        errors.append("HTML appears to reference network resources")

    for view_id in ("v1", "v2", "v3", "v4"):
        if not re.search(rf'<input\b[^>]*\bid=["\']{view_id}["\'][^>]*\btype=["\']radio["\']', text):
            errors.append(f"HTML missing approved radio tab input: {view_id}")

    for view_class, label in REQUIRED_HTML_VIEWS:
        if not re.search(rf'<section\b[^>]*class=["\'][^"\']*\b{view_class}\b[^"\']*["\']', text):
            errors.append(f"HTML missing approved four-dimension view section: {view_class}")
        if label not in text:
            errors.append(f"HTML missing approved four-dimension tab/heading label: {label}")

    for _, marker, message in REQUIRED_HTML_COMPONENTS:
        if marker not in text:
            errors.append(message)

    for old_label in OLD_REQUIRED_HTML_VIEW_LABELS:
        if old_label in text:
            errors.append(f"HTML appears to use old six-view label instead of approved sample dimensions: {old_label}")

    source_refs = re.findall(r'data-agent-source=["\']([^"\']+)["\']', text)
    if not source_refs:
        errors.append("HTML missing data-agent-source references on views")
        return
    if len(source_refs) < len(REQUIRED_HTML_VIEWS):
        errors.append("HTML must have data-agent-source on each of the four approved dimension views")
    agent_dir = package / "agent_context"
    index_text = (agent_dir / "00_INDEX.md").read_text(encoding="utf-8") if (agent_dir / "00_INDEX.md").is_file() else ""
    for source in source_refs:
        if not source.startswith("agent_context/"):
            errors.append(f"HTML data-agent-source must start with agent_context/: {source}")
            continue
        file_part = source.split("#", 1)[0]
        source_path = package / file_part
        if not source_path.is_file():
            errors.append(f"HTML data-agent-source file does not exist: {source}")
        if file_part not in index_text:
            errors.append(f"00_INDEX.md semantic alignment table does not mention HTML source: {file_part}")


def section_text(text: str, view_class: str, next_view_class: str | None = None) -> str:
    """Return one approved view's HTML without requiring an HTML parser dependency."""
    start = re.search(
        rf'<section\b[^>]*class=["\'][^"\']*\b{view_class}\b[^"\']*["\'][^>]*>',
        text,
    )
    if start is None:
        return ""
    end = (
        re.search(
            rf'<section\b[^>]*class=["\'][^"\']*\b{next_view_class}\b[^"\']*["\'][^>]*>',
            text[start.end():],
        )
        if next_view_class
        else None
    )
    return text[start.start(): start.end() + end.start()] if end else text[start.start():]


def check_sample_pattern(package: Path, errors: list[str]) -> None:
    """Guard the L2-04-derived four-dimension shape beyond marker-only checks."""
    html_path = package / "L2架构交互可视化.html"
    if not html_path.is_file():
        return
    text = html_path.read_text(encoding="utf-8")
    sections = {
        "boundary": section_text(text, "boundary", "pi05map"),
        "pi05map": section_text(text, "pi05map", "blueprint"),
        "blueprint": section_text(text, "blueprint", "acceptance"),
        "acceptance": section_text(text, "acceptance"),
    }
    for view, content in sections.items():
        if not content:
            continue
        if 'class="reading-path"' not in content:
            errors.append(f"dimension {view} missing its own .reading-path")
        if 'class="lead"' not in content:
            errors.append(f"dimension {view} missing its own .lead")
        if 'class="src"' not in content:
            errors.append(f"dimension {view} missing its own authoritative .src note")

    boundary = sections["boundary"]
    if boundary:
        if "<svg" in boundary.lower():
            errors.append("dimension 1 boundary must use io-flow and must not contain <svg>")
        for marker, message in [
            ('class="io-flow"', "dimension 1 missing .io-flow"),
            ('class="io-col input"', "dimension 1 missing input .io-col"),
            ('class="io-module"', "dimension 1 missing central .io-module"),
            ('class="io-col output"', "dimension 1 missing output .io-col"),
            ('class="pipe"', "dimension 1 missing .pipe check-chain"),
            ('class="io-card ok"', "dimension 1 missing output .io-card.ok"),
            ('class="nested-detail"', "dimension 1 missing folded boundary detail: .nested-detail"),
        ]:
            if marker not in boundary:
                errors.append(message)

    blueprint = sections["blueprint"]
    if blueprint:
        if "03a_功能微元总览与组织结构.md" not in blueprint:
            errors.append("dimension 3 must cite 03a_功能微元总览与组织结构.md for A/B/C organization")
        for marker, message in [
            ("<svg", "dimension 3 missing runtime swimlane SVG (图①)"),
            ("stroke-dasharray", "dimension 3 runtime SVG missing dashed injection/failure distinction"),
            ('class="ovtab"', "dimension 3 missing A/B/C overview table: .ovtab (图②)"),
            ('class="layer-head A"', "dimension 3 missing A-layer overview table header"),
            ('class="layer-head B"', "dimension 3 missing B-layer overview table header"),
            ('class="layer-head C"', "dimension 3 missing C-layer overview table header"),
            ('class="lpick"', "dimension 3 missing six-layer picker: .lpick (图③)"),
            ('class="ltabs"', "dimension 3 missing six-layer labels: .ltabs"),
            ('class="data-table"', "dimension 3 missing data-micro-unit field table: .data-table"),
            ("内部存储结构", "dimension 3 data table must distinguish internal storage structure"),
            ("内部存储的数据类型", "dimension 3 data table must distinguish internal stored data type"),
        ]:
            if marker not in blueprint:
                errors.append(message)
        if "图②" not in blueprint or "图③" not in blueprint:
            errors.append("dimension 3 must include both A/B/C overview (图②) and six-layer landing (图③)")
        if len(re.findall(r'<table\b[^>]*class=["\'][^"\']*\bovtab\b[^"\']*["\']', blueprint)) != 3:
            errors.append("dimension 3 must contain exactly three .ovtab tables for A/B/C")
        if len(re.findall(r'<input\b[^>]*\bname=["\']layer["\'][^>]*\btype=["\']radio["\']', blueprint)) != 6:
            errors.append("dimension 3 must contain exactly six name=layer radio controls")
        if len(re.findall(r'<div\b[^>]*class=["\'][^"\']*\blpane\b[^"\']*["\']', blueprint)) != 6:
            errors.append("dimension 3 must contain exactly six .lpane layer panels")

    acceptance = sections["acceptance"]
    if acceptance:
        for marker, message in [
            ('class="vfy"', "dimension 4 missing .vfy checklist"),
            ('class="vfy-item"', "dimension 4 missing .vfy-item checklist cards"),
            ('class="term"', "dimension 4 missing .term terminal sample"),
            ('class="trtab"', "dimension 4 missing .trtab translation table"),
            ('class="t-loc"', "dimension 4 terminal sample missing FAIL location block: .t-loc"),
        ]:
            if marker not in acceptance:
                errors.append(message)


def check_dim3_classbox_nesting(package: Path, errors: list[str]) -> None:
    """排版铁律#0: every .classbox in dimension 3 must live inside the .lpick region.

    A six-layer tab must reveal its layer's full micro-unit breakdown inline. Placing a
    .classbox (or a duplicate <h3>…微元拆解</h3>) after the .lpick closing </div> is the
    regression seen in l2-04 — the content is hidden until the user clicks a tab AND scrolls
    down. This check fails if any .classbox appears in the blueprint section after the .lpick.
    """
    html_path = package / "L2架构交互可视化.html"
    if not html_path.is_file():
        return
    lines = html_path.read_text(encoding="utf-8").splitlines()

    start = end = None
    for i, line in enumerate(lines):
        if re.search(r'<section\b[^>]*class="[^"]*\bblueprint\b', line):
            start = i
        elif start is not None and re.search(r'<section\b[^>]*class="[^"]*\bacceptance\b', line):
            end = i
            break
    if start is None or end is None:
        return  # structural view checks elsewhere already flag a missing blueprint section

    # Locate the .lpick region and its matching close via div-depth tracking.
    lpick_open = None
    for i in range(start, end):
        if 'class="lpick"' in lines[i]:
            lpick_open = i
            break
    if lpick_open is None:
        errors.append("dimension 3 (.blueprint) missing .lpick six-layer radio region")
        return

    depth = 0
    lpick_close = None
    for i in range(lpick_open, end):
        depth += len(re.findall(r"<div\b", lines[i])) - len(re.findall(r"</div>", lines[i]))
        if depth == 0 and i > lpick_open:
            lpick_close = i
            break
    if lpick_close is None:
        errors.append("dimension 3 .lpick region is not closed before .acceptance")
        return

    after_classboxes = 0
    for i in range(lpick_close + 1, end):
        if 'class="classbox' in lines[i]:
            after_classboxes += 1
    if after_classboxes:
        errors.append(
            f"dimension 3 has {after_classboxes} .classbox(es) after the .lpick region — "
            "all classboxes must live inside their layer pane within .lpick (排版铁律#0)"
        )


def check_contamination(package: Path, errors: list[str]) -> None:
    for path in sorted(package.rglob("*")):
        if not path.is_file() or path.suffix not in {".md", ".html"}:
            continue
        text = path.read_text(encoding="utf-8")
        for lineno, line in enumerate(text.splitlines(), start=1):
            for term in CONTAMINATION_TERMS:
                if term in line and not ALLOWED_CONTAMINATION_CONTEXT.search(line):
                    errors.append(
                        f"{rel(path, package)}:{lineno} uses legacy/template term without allowed context: {term}"
                    )


def check_sync(package: Path, errors: list[str]) -> None:
    """Run sync_check.sh and report its semantic failures through this validator."""
    import subprocess

    sync_script = Path(__file__).resolve().parent / "sync_check.sh"
    if not sync_script.is_file():
        errors.append("sync: sync_check.sh not found — cannot verify HTML↔MD semantic alignment")
        return
    try:
        result = subprocess.run(
            ["bash", str(sync_script), str(package)],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except subprocess.TimeoutExpired:
        errors.append("sync: sync_check.sh timed out")
        return
    except OSError as exc:
        errors.append(f"sync: failed to run sync_check.sh: {exc}")
        return
    if result.returncode != 0:
        for line in result.stdout.splitlines():
            line = line.strip()
            if "FAIL" in line or "MISSING" in line:
                errors.append(f"sync: {line}")


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: validate_l2_design_package.py <l2_design_package_dir>", file=sys.stderr)
        return 2

    package = Path(sys.argv[1]).resolve()
    if not package.is_dir():
        print(f"ERROR: package directory does not exist: {package}", file=sys.stderr)
        return 2

    errors: list[str] = []
    l2_id = infer_l2_id(package)
    if not l2_id:
        errors.append(f"cannot infer l2_id from package directory name: {package.name}")

    check_root(package, errors)
    check_agent_context(package, errors)
    check_html(package, l2_id, errors)
    check_sample_pattern(package, errors)
    check_dim3_classbox_nesting(package, errors)
    check_contamination(package, errors)
    check_sync(package, errors)

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print(f"PASS stage4 L2 design package: {package.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
