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
    (".vfy-item", 'class="vfy-item"', "HTML missing sample acceptance card component: .vfy-item"),
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
    check_contamination(package, errors)

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print(f"PASS stage4 L2 design package: {package.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
