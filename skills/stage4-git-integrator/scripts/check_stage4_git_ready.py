#!/usr/bin/env python3
"""Stage 4 Git preflight — check branch, worktree health, and gate readiness.

Modes:
    clean-commit  — verify feature branch is clean enough to commit
    merge         — verify Gate, human acceptance, and model_deploy readiness
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Set, Tuple

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

L2_ORDER: Tuple[str, ...] = (
    "l2-01-external-contract",
    "l2-02-observation-snapshot",
    "l2-03-act-inference",
    "l2-04-safety-guard",
    "l2-05-action-publisher",
    "l2-06-control-loop",
)

VALID_L2_IDS: Set[str] = set(L2_ORDER)

L2_TO_BRANCH: Dict[str, str] = {
    "l2-01-external-contract": "feat/model_deploy/l2-01-external-contract-design",
    "l2-02-observation-snapshot": "feat/model_deploy/l2-02-observation-snapshot",
    "l2-03-act-inference": "feat/model_deploy/l2-03-act-inference",
    "l2-04-safety-guard": "feat/model_deploy/l2-04-safety-guard",
    "l2-05-action-publisher": "feat/model_deploy/l2-05-action-publisher",
    "l2-06-control-loop": "feat/model_deploy/l2-06-control-loop",
}

INTEGRATION_BRANCH = "model_deploy"

# Files/patterns that are safe to leave untracked
SAFE_UNTRACKED_PATTERNS = (
    ".zcode/",
    "__pycache__/",
    ".pytest_cache/",
    "*.pyc",
    "worktrees/",
)

# Files that are known merge artifacts and should be removed
MERGE_ARTIFACT_FILES = (
    "html要求.md",
    "html要求.html",
)

# Directories where stale files may appear after cross-worktree merges
STALE_DIRS_TEMPLATES = (
    "DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/{l2}/",
    "DOCS/03_工程/阶段四：模型部署/03_tasks/completed/{l2}/",
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def run_git(args: List[str], cwd: Path | None = None) -> str:
    cmd = ["git"]
    if cwd is not None:
        cmd += ["-C", str(cwd)]
    cmd += args
    return subprocess.check_output(cmd, text=True).strip()


def try_run_git(args: List[str], cwd: Path | None = None) -> str:
    """Run git; return empty string on failure."""
    try:
        return run_git(args, cwd=cwd)
    except subprocess.CalledProcessError:
        return ""


def is_stage4_feature_branch(branch: str) -> bool:
    return bool(re.match(r"^(feat|fix|docs|chore|spike)/model_deploy/.+", branch))


def file_is_safe_untracked(name: str) -> bool:
    for pat in SAFE_UNTRACKED_PATTERNS:
        if pat.endswith("/") and (name.startswith(pat) or f"/{pat}" in name):
            return True
        if pat.startswith("*") and name.endswith(pat[1:]):
            return True
    return False


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


def get_downstream_l2s(l2_id: str) -> List[str]:
    """Return L2 IDs with higher index than *l2_id*."""
    try:
        idx = L2_ORDER.index(l2_id)
    except ValueError:
        return []
    return list(L2_ORDER[idx + 1:])


def check_worktree_exists(l2_id: str, repo_root: Path) -> bool:
    """Check if a worktree exists for this L2."""
    wt_path = repo_root / "worktrees" / l2_id
    if wt_path.is_dir():
        wt_list = try_run_git(["worktree", "list"], cwd=repo_root)
        return str(wt_path) in wt_list
    return False


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Stage 4 Git preflight checker"
    )
    parser.add_argument(
        "--l2", required=True, choices=sorted(VALID_L2_IDS),
        help="Current L2 ID"
    )
    parser.add_argument(
        "--mode", required=True,
        choices=["clean-commit", "merge"],
        help="Check mode"
    )
    args = parser.parse_args()

    root = Path.cwd()
    errors: List[str] = []
    warnings: List[str] = []

    # --- Branch check ---
    branch = run_git(["branch", "--show-current"])
    expected = L2_TO_BRANCH.get(args.l2, "")

    if branch == INTEGRATION_BRANCH:
        if args.mode == "clean-commit":
            errors.append(
                "current branch is model_deploy; "
                "clean-commit must happen on a feature branch"
            )
    elif not is_stage4_feature_branch(branch):
        errors.append(
            f"current branch is not a Stage 4 feature branch: {branch}"
        )

    if expected and branch != expected:
        warnings.append(
            f"current branch '{branch}' does not match expected "
            f"'{expected}' for {args.l2}"
        )

    # --- Remote / user checks ---
    remotes = run_git(["remote", "-v"])
    if "origin\thttps://github.com/jack-z36/ROS.git" not in remotes:
        errors.append(
            f"unexpected remote: expected origin → "
            f"https://github.com/jack-z36/ROS.git"
        )

    user = run_git(["config", "user.name"])
    email = run_git(["config", "user.email"])
    if user != "jack-z36":
        errors.append(f"unexpected git user: {user}")
    if email != "jack-z36@users.noreply.github.com":
        errors.append(f"unexpected git email: {email}")

    # --- Worktree status ---
    status_raw = run_git(["status", "--short"])
    status_lines = [l for l in status_raw.splitlines() if l.strip()]

    staged = [l for l in status_lines if not l.startswith(" ") and not l.startswith("?")]
    modified = [l for l in status_lines if l.startswith(" M") or l.startswith(" D")]
    untracked = [l for l in status_lines if l.startswith("??")]

    # Check for merge artifacts
    for line in untracked:
        fname = line[3:].strip()
        if fname in MERGE_ARTIFACT_FILES or any(
            fname.endswith(artifact) for artifact in MERGE_ARTIFACT_FILES
        ):
            warnings.append(
                f"untracked merge artifact should be removed: {fname}"
            )

    # Check for suspicious untracked files
    suspicious_untracked = [
        l for l in untracked
        if not file_is_safe_untracked(l[3:].strip())
        and l[3:].strip() not in MERGE_ARTIFACT_FILES
    ]
    if suspicious_untracked:
        warnings.append(
            f"untracked files outside safe patterns: "
            + ", ".join(l[3:].strip() for l in suspicious_untracked)
        )

    # For merge mode, worktree must be clean
    if args.mode == "merge":
        if modified:
            errors.append(
                f"worktree has uncommitted modifications — "
                f"run clean-commit first"
            )
        if staged:
            errors.append(
                f"worktree has staged changes — commit or unstage first"
            )

    # --- Downstream worktree health (merge mode) ---
    if args.mode == "merge":
        downstream = get_downstream_l2s(args.l2)
        for ds_l2 in downstream:
            if check_worktree_exists(ds_l2, root):
                wt_path = root / "worktrees" / ds_l2
                ds_status = try_run_git(["status", "--short"], cwd=wt_path)
                if ds_status:
                    ds_lines = [l for l in ds_status.splitlines() if l.strip()]
                    ds_modified = [
                        l for l in ds_lines
                        if not l.startswith("?") and not l.startswith(" ")
                    ]
                    if ds_modified:
                        warnings.append(
                            f"downstream worktree {ds_l2} has uncommitted "
                            f"changes that may conflict"
                        )
            else:
                warnings.append(
                    f"downstream L2 {ds_l2} has no worktree at "
                    f"worktrees/{ds_l2}/"
                )

    # --- Human acceptance (merge mode) ---
    if args.mode == "merge":
        acceptance = (
            root / "DOCS" / "03_工程" / "阶段四：模型部署"
            / "05_acceptance" / args.l2 / "验收结果.md"
        )
        if not human_acceptance_passed(acceptance):
            errors.append(
                f"human acceptance is missing or not passed: {acceptance}"
            )

    # --- Output ---
    if warnings:
        for w in warnings:
            print(f"WARNING: {w}")

    if errors:
        for e in errors:
            print(f"ERROR: {e}")
        return 1

    # Summary
    downstream_list = get_downstream_l2s(args.l2)
    ds_branches = [f"feat/model_deploy/{d}" for d in downstream_list]
    print(f"PASS stage4 git preflight: mode={args.mode} l2={args.l2} branch={branch}")
    print(f"  integration: {INTEGRATION_BRANCH}")
    print(f"  downstream:  {', '.join(ds_branches) if ds_branches else '(none — last L2)'}")
    print(f"  worktrees:   {', '.join(downstream_list) if downstream_list else '(none)'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
