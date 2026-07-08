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

VALID_L2_IDS = {
    "l2-01-external-contract",
    "l2-02-observation-snapshot",
    "l2-03-act-inference",
    "l2-04-safety-guard",
    "l2-05-action-publisher",
    "l2-06-control-loop",
}


def infer_l2_id(package: Path) -> str:
    match = re.search(r"(l2-\d{2}-[a-z0-9-]+)", package.name)
    return match.group(1) if match else ""


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: validate_l3_generation_inputs.py <l2_design_package_dir>", file=sys.stderr)
        return 2

    package = Path(sys.argv[1]).resolve()
    errors: list[str] = []

    if not package.is_dir():
        print(f"ERROR: package directory does not exist: {package}", file=sys.stderr)
        return 2

    l2_id = infer_l2_id(package)
    if l2_id not in VALID_L2_IDS:
        errors.append(f"invalid or missing current Stage 4 l2_id in package name: {package.name}")

    if not (package / "L2架构交互可视化.html").is_file():
        errors.append("missing human HTML: L2架构交互可视化.html")

    agent_dir = package / "agent_context"
    if not agent_dir.is_dir():
        errors.append("missing agent_context/")
    else:
        for filename in REQUIRED_AGENT_FILES:
            if not (agent_dir / filename).is_file():
                errors.append(f"missing agent_context/{filename}")
        for filename in ("03_ACT微元设计与协作.md", "04_L2验收机制.md", "05_人类验收机制.md"):
            path = agent_dir / filename
            if path.is_file():
                text = path.read_text(encoding="utf-8")
                if "待确认" in text or "TODO" in text:
                    errors.append(f"agent_context/{filename} still contains TODO/待确认 markers")

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print(f"PASS stage4 L3 generation inputs: {package.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
