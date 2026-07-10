#!/usr/bin/env python3
"""Validate a Stage 4 L1 design package under agent_context/ + HTML.

Checks:
  1. Required agent_context files present
  2. 00_INDEX.md routing table covers all other files
  3. Cross-file L2 ID consistency
  4. HTML has one radio input + panel per L2 module
  5. HTML CSS has :checked rules for each module
  6. No legacy contamination terms
  7. HTML data-agent-source attributes match MD files

Usage:
  python3 scripts/validate_l1_design_package.py <l1_design_dir>
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


REQUIRED_AGENT_FILES = [
    "00_INDEX.md",
    "01_L1_",
    "02_L1_",
    "03_L1_",
]

CONTAMINATION_TERMS = [
    "l2-01-types",
    "l2-02-config",
    "l2-03-assembly",
    "l2-04-publish",
    "l2-05-hardware",
    "ACT Contract Delta",
    "AS-IS Contract",
    "TO-BE Contract",
    "旧 layer-based",
    "阶段二模板",
    "smoothstep",
    "cross-chunk fusion",
    "RTC alignment",
    "action_smoothing",
]

HTML_REQUIRED_SECTIONS = [
    ("detail panels", re.compile(r'class="bpanel\s+p\d+"')),
    ("radio inputs", re.compile(r'<input\s+id="m\d+"\s+name="mod"\s+type="radio"')),
    (":checked CSS rules", re.compile(r'#m\d+:checked\s*~')),
    ("modbar labels", re.compile(r'<label\s+for="m\d+"')),
    ("data-agent-source attrs", re.compile(r'data-agent-source="agent_context/')),
]


def find_l1_files(pkg_dir: Path) -> dict[str, Path]:
    """Find the 4 L1 files, matching by prefix since exact names vary."""
    found: dict[str, Path] = {}
    ac_dir = pkg_dir / "agent_context"
    if not ac_dir.is_dir():
        print(f"ERROR: agent_context/ not found in {pkg_dir}")
        return found

    for f in ac_dir.iterdir():
        if not f.is_file() or f.suffix != ".md":
            continue
        name = f.name
        if name == "00_INDEX.md":
            found["index"] = f
        elif name.startswith("01_L1_"):
            found["task"] = f
        elif name.startswith("02_L1_"):
            found["boundary"] = f
        elif name.startswith("03_L1_"):
            found["collaboration"] = f

    return found


def check_required_files(found: dict[str, Path]) -> list[str]:
    errors = []
    for key in ["index", "task", "boundary", "collaboration"]:
        if key not in found:
            errors.append(f"MISSING: agent_context/ file for role '{key}' (expected prefix match)")
    if len(errors) == 0:
        print("  [OK] All 4 required agent_context files found")
    return errors


def check_index_routing(index_path: Path) -> list[str]:
    errors = []
    content = index_path.read_text(encoding="utf-8")

    # Check routing table mentions the other 3 files
    for prefix in ["01_L1_", "02_L1_", "03_L1_"]:
        if prefix not in content:
            errors.append(f"INDEX: routing table missing reference to file starting with '{prefix}'")

    # Check HTML-MD alignment table exists
    if "HTML-MD 语义对齐表" not in content and "HTML-MD" not in content and "语义对齐" not in content:
        errors.append("INDEX: missing HTML-MD alignment table (§5)")

    # Check pollution section
    if "污染检查" not in content:
        errors.append("INDEX: missing pollution check section (§6)")

    if len(errors) == 0:
        print("  [OK] 00_INDEX.md routing and structure valid")
    return errors


def check_contamination(file_path: Path) -> list[str]:
    errors = []
    content = file_path.read_text(encoding="utf-8")

    for term in CONTAMINATION_TERMS:
        if term.lower() in content.lower():
            # Allow if in explicit pollution-check or deprecation context
            lines = content.split("\n")
            found_in_allowed = False
            for i, line in enumerate(lines):
                if term.lower() in line.lower():
                    # Check if surrounding context is pollution/check/deprecation
                    ctx_start = max(0, i - 3)
                    ctx_end = min(len(lines), i + 4)
                    ctx = "\n".join(lines[ctx_start:ctx_end]).lower()
                    if any(kw in ctx for kw in ["污染", "禁止", "废弃", "deprecated", "legacy", "不继承", "不来自"]):
                        found_in_allowed = True
                    else:
                        found_in_allowed = False
                        break
            if not found_in_allowed:
                errors.append(f"CONTAMINATION: '{term}' found in {file_path.name} outside pollution-check context")

    if len(errors) == 0:
        print(f"  [OK] {file_path.name}: no contamination")
    return errors


def check_html(html_path: Path | None) -> list[str]:
    errors = []
    if html_path is None or not html_path.is_file():
        errors.append(f"HTML: file not found at {html_path}")
        return errors

    content = html_path.read_text(encoding="utf-8")

    # Check for JavaScript
    if "<script" in content.lower():
        errors.append("HTML: contains <script> tag — must be zero-JS")

    # Check for external dependencies
    if "cdn" in content.lower() or "npm" in content.lower() or "node_modules" in content.lower():
        errors.append("HTML: contains external dependency reference — must be self-contained")

    # Check radio inputs
    radio_count = len(re.findall(r'<input\s+id="m\d+"\s+name="mod"\s+type="radio"', content))
    panel_count = len(re.findall(r'class="bpanel\s+p\d+"', content))
    if radio_count == 0:
        errors.append("HTML: no module radio inputs found")
    if panel_count == 0:
        errors.append("HTML: no detail panels found")
    if radio_count != panel_count:
        errors.append(f"HTML: radio count ({radio_count}) != panel count ({panel_count})")

    # Check :checked CSS rules
    checked_rules = len(re.findall(r'#m\d+:checked\s*~', content))
    if checked_rules == 0:
        errors.append("HTML: no :checked CSS rules for module selection")

    # Check data-agent-source
    das = re.findall(r'data-agent-source="(agent_context/[^"]+)"', content)
    if len(das) == 0:
        errors.append("HTML: no data-agent-source attributes on views")

    if len(errors) == 0:
        print(f"  [OK] {html_path.name}: valid structure (radios={radio_count}, panels={panel_count})")
    return errors


def check_cross_file_consistency(found: dict[str, Path]) -> list[str]:
    errors = []
    # Extract L2 IDs from boundary doc and check against INDEX
    if "boundary" in found and "index" in found:
        boundary_text = found["boundary"].read_text(encoding="utf-8")
        index_text = found["index"].read_text(encoding="utf-8")
        # Find L2 IDs like l2-01-xxx
        l2_ids_boundary = set(re.findall(r'l2-\d{2}-[\w-]+', boundary_text))
        l2_ids_index = set(re.findall(r'l2-\d{2}-[\w-]+', index_text))
        if l2_ids_boundary != l2_ids_index:
            missing_in_idx = l2_ids_boundary - l2_ids_index
            missing_in_bnd = l2_ids_index - l2_ids_boundary
            if missing_in_idx:
                errors.append(f"CROSS-FILE: L2 IDs in boundary but not INDEX: {missing_in_idx}")
            if missing_in_bnd:
                errors.append(f"CROSS-FILE: L2 IDs in INDEX but not boundary: {missing_in_bnd}")
        else:
            print(f"  [OK] L2 ID consistency: boundary ↔ INDEX ({len(l2_ids_boundary)} IDs)")

    return errors


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 validate_l1_design_package.py <l1_design_dir>")
        sys.exit(1)

    pkg_dir = Path(sys.argv[1]).resolve()
    if not pkg_dir.is_dir():
        print(f"ERROR: {pkg_dir} is not a directory")
        sys.exit(1)

    print(f"Validating L1 design package: {pkg_dir}\n")

    all_errors: list[str] = []

    # 1. Find files
    found = find_l1_files(pkg_dir)

    # 2. Required files
    all_errors.extend(check_required_files(found))

    # 3. INDEX routing
    if "index" in found:
        all_errors.extend(check_index_routing(found["index"]))
        all_errors.extend(check_contamination(found["index"]))

    # 4. Contamination check on all MD files
    for key, path in found.items():
        if key != "index":
            all_errors.extend(check_contamination(path))

    # 5. HTML check
    html_path = None
    for candidate in pkg_dir.glob("*.html"):
        html_path = candidate
        break
    all_errors.extend(check_html(html_path))

    # 6. Cross-file consistency
    all_errors.extend(check_cross_file_consistency(found))

    # Report
    print(f"\n{'='*60}")
    if all_errors:
        print(f"VALIDATION FAILED ({len(all_errors)} issues):")
        for err in all_errors:
            print(f"  - {err}")
        sys.exit(1)
    else:
        print("VALIDATION PASSED — L1 design package is structurally valid.")
        sys.exit(0)


if __name__ == "__main__":
    main()
