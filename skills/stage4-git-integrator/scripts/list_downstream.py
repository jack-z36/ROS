#!/usr/bin/env python3
"""List downstream L2 branches and their worktree status for Stage 4 merges.

Outputs a JSON or human-readable list of:
- downstream L2 IDs
- their feature branch names
- worktree path (if exists)
- current merge status (ahead/behind model_deploy)
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple


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

L2_TO_BRANCH: Dict[str, str] = {
    "l2-01-external-contract": "feat/model_deploy/l2-01-external-contract-design",
    "l2-02-observation-snapshot": "feat/model_deploy/l2-02-observation-snapshot",
    "l2-03-act-inference": "feat/model_deploy/l2-03-act-inference",
    "l2-04-safety-guard": "feat/model_deploy/l2-04-safety-guard",
    "l2-05-action-publisher": "feat/model_deploy/l2-05-action-publisher",
    "l2-06-control-loop": "feat/model_deploy/l2-06-control-loop",
}

INTEGRATION_BRANCH = "model_deploy"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def run_git(args: List[str], cwd: Path | None = None) -> str:
    cmd = ["git"]
    if cwd is not None:
        cmd += ["-C", str(cwd)]
    cmd += args
    try:
        return subprocess.check_output(cmd, text=True).strip()
    except subprocess.CalledProcessError as exc:
        return f"ERROR: {exc}"


def find_repo_root(start: Path) -> Path:
    """Find the main git repository root (shared across all worktrees).

    In a linked worktree, ``git rev-parse --git-common-dir`` returns the
    shared ``.git`` directory (e.g. ``/home/hit/ROS/.git``).  The main
    checkout is its parent.
    """
    try:
        common = subprocess.check_output(
            ["git", "rev-parse", "--git-common-dir"],
            text=True, cwd=str(start)
        ).strip()
        return Path(common).parent
    except Exception:
        # Fallback: show-toplevel
        try:
            top = subprocess.check_output(
                ["git", "rev-parse", "--show-toplevel"],
                text=True, cwd=str(start)
            ).strip()
            return Path(top)
        except Exception:
            return start


def _parse_worktree_list(repo_root: Path) -> dict[str, Path]:
    """Parse ``git worktree list`` into {path_str: Path}.

    Each line of output looks like::

        /home/hit/ROS   cd51af7 [model_deploy]
        /home/hit/ROS/worktrees/l2-03-act-inference  dd2973c [feat/...]

    The first whitespace-separated token is the absolute worktree path.
    """
    result: dict[str, Path] = {}
    try:
        raw = subprocess.check_output(
            ["git", "worktree", "list"],
            text=True, cwd=str(repo_root)
        )
    except Exception:
        return result

    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        # Split on whitespace — the path is the first token
        tokens = line.split()
        if tokens:
            wt_path = Path(tokens[0])
            result[str(wt_path)] = wt_path
    return result


def get_worktree_path(l2_id: str, repo_root: Path) -> Optional[Path]:
    """Return the worktree path if one exists for this L2.

    Uses ``git worktree list`` from the real repo root, then matches
    against the expected directory name ``worktrees/<l2_id>``.
    """
    real_root = find_repo_root(repo_root)
    wt_map = _parse_worktree_list(real_root)
    base = real_root / "worktrees"

    # Exact match: worktrees/<l2_id>
    candidate = base / l2_id
    if str(candidate) in wt_map:
        return candidate

    # Fuzzy match: scan worktrees/ for a directory whose tail matches l2_id
    if base.is_dir():
        for child in sorted(base.iterdir()):
            if child.is_dir() and child.name == l2_id:
                if str(child) in wt_map:
                    return child

    return None


def get_merge_status(worktree: Path, target: str = INTEGRATION_BRANCH) -> Dict[str, int]:
    """Return ahead/behind counts vs *target*."""
    branch = run_git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=worktree)
    base = run_git(["merge-base", target, branch], cwd=worktree)

    ahead = run_git(
        ["rev-list", "--count", f"{base}..{branch}"], cwd=worktree
    )
    behind = run_git(
        ["rev-list", "--count", f"{branch}..{target}"], cwd=worktree
    )

    try:
        return {"ahead": int(ahead), "behind": int(behind)}
    except (ValueError, TypeError):
        return {"ahead": -1, "behind": -1}


def get_downstream_l2s(current_l2: str) -> List[str]:
    """Return L2 IDs with higher index."""
    try:
        idx = L2_ORDER.index(current_l2)
    except ValueError:
        return []
    return list(L2_ORDER[idx + 1:])


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(
        description="List downstream L2 branches for Stage 4 merges"
    )
    parser.add_argument(
        "--l2", required=True,
        help="Current L2 ID (e.g. l2-02-observation-snapshot)"
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Output machine-readable JSON"
    )
    parser.add_argument(
        "--shell", action="store_true",
        help="Output space-separated branch names for shell loops"
    )
    args = parser.parse_args()

    repo_root = Path.cwd()
    downstream = get_downstream_l2s(args.l2)

    if not downstream:
        if args.json:
            print(json.dumps({"downstream": [], "message": "no downstream L2s — this is the last L2"}))
        elif args.shell:
            print("")
        else:
            print("(none — this is the last L2, no downstream branches)")
        return 0

    results: List[Dict] = []

    for ds_l2 in downstream:
        branch = L2_TO_BRANCH.get(ds_l2, f"feat/model_deploy/{ds_l2}")
        wt = get_worktree_path(ds_l2, repo_root)
        status = get_merge_status(wt) if wt else {"ahead": -1, "behind": -1}

        info: Dict = {
            "l2_id": ds_l2,
            "branch": branch,
            "worktree": str(wt) if wt else None,
            "ahead_of_model_deploy": status["ahead"],
            "behind_model_deploy": status["behind"],
        }
        results.append(info)

    if args.json:
        print(json.dumps({"downstream": results}, indent=2, ensure_ascii=False))
    elif args.shell:
        # Output space-separated L2 IDs for shell for-loops
        # Also output branch names on second line
        l2_ids = " ".join(ds for ds in downstream)
        branches = " ".join(L2_TO_BRANCH.get(ds, f"feat/model_deploy/{ds}") for ds in downstream)
        worktrees = " ".join(str(r["worktree"]) if r["worktree"] else "" for r in results)
        print(f"L2_IDS='{l2_ids}'")
        print(f"BRANCHES='{branches}'")
        print(f"WORKTREES='{worktrees}'")
    else:
        # Human-readable
        print(f"{'L2 ID':<32} {'Branch':<48} {'Ahead':>5} {'Behind':>6}  Worktree")
        print("-" * 110)
        for r in results:
            wt_marker = "✓" if r["worktree"] else "✗"
            ahead = str(r["ahead_of_model_deploy"]) if r["ahead_of_model_deploy"] >= 0 else "?"
            behind = str(r["behind_model_deploy"]) if r["behind_model_deploy"] >= 0 else "?"
            print(
                f"{r['l2_id']:<32} {r['branch']:<48} {ahead:>5} {behind:>6}  "
                f"{wt_marker} {r['worktree'] or '(no worktree)'}"
            )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
