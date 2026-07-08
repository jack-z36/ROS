#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path


VALID_L2_IDS = {
    "l2-01-external-contract",
    "l2-02-observation-snapshot",
    "l2-03-act-inference",
    "l2-04-safety-guard",
    "l2-05-action-publisher",
    "l2-06-control-loop",
}


def run_git(args: list[str]) -> str:
    return subprocess.check_output(["git", *args], text=True).strip()


def human_acceptance_passed(path: Path) -> bool:
    if not path.is_file():
        return False
    text = path.read_text(encoding="utf-8")
    return (
        "## 人类验收" in text
        and "验收人：" in text
        and "验收日期：" in text
        and re.search(r"验收结论：.*\[x\]\s*已通过", text, re.IGNORECASE)
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--l2", required=True, choices=sorted(VALID_L2_IDS))
    parser.add_argument("--mode", required=True, choices=["l3-commit", "merge"])
    args = parser.parse_args()

    root = Path.cwd()
    errors: list[str] = []

    branch = run_git(["branch", "--show-current"])
    if branch == "model_deploy":
        if args.mode != "merge":
            errors.append("current branch is model_deploy; L3 commits must happen on a feature branch")
    elif not re.match(r"^(feat|fix|docs|chore|spike)/model_deploy/.+", branch):
        errors.append(f"current branch is not a Stage 4 feature branch: {branch}")

    status = run_git(["status", "--short"])
    suspicious = [
        line for line in status.splitlines()
        if line and not line.endswith("/") and ".zcode/" not in line
    ]
    if args.mode == "merge" and suspicious:
        errors.append("worktree has pending changes; merge requires clean or expected staged state")

    if args.mode == "merge":
        acceptance = root / "DOCS" / "03_工程" / "阶段四：模型部署" / "05_acceptance" / args.l2 / "验收结果.md"
        if not human_acceptance_passed(acceptance):
            errors.append(f"human acceptance is missing or not passed: {acceptance}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print(f"PASS stage4 git preflight: mode={args.mode} l2={args.l2} branch={branch}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
