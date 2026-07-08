#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


SKILL_PATH = "skills/stage4-l3-orchestrator/SKILL.md"


def find_stage4(root: Path) -> Path:
    for path in (root / "DOCS").rglob("03_tasks"):
        if "\u9636\u6bb5\u56db" in str(path):
            return path.parent
    raise SystemExit("Cannot locate Stage 4 03_tasks directory")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate minimal Stage 4 sub-agent prompts.")
    parser.add_argument("--role", required=True, choices=["executor", "acceptor", "l2-acceptor"])
    parser.add_argument("--task", help="L3 task path for executor role")
    parser.add_argument("--card", help="L3 acceptance card path for acceptor role")
    parser.add_argument("--task-id", help="Deploy task id, e.g. deploy_013")
    parser.add_argument("--l2", help="L2 group, e.g. l2-04-publish")
    parser.add_argument("--round", default="1", help="Acceptance round number")
    return parser.parse_args()


def read_title(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    match = re.search(r"^# (.+)$", text, re.MULTILINE)
    return match.group(1).strip() if match else path.name


def resolve_task(root: Path, l2: str | None, task_id: str | None) -> str:
    if not l2 or not task_id:
        raise SystemExit("--task or both --l2 and --task-id are required")
    stage4 = find_stage4(root)
    active_dir = stage4 / "03_tasks" / "task" / "active" / l2
    matches = sorted(active_dir.glob(f"{task_id}_*.md"))
    if not matches:
        raise SystemExit(f"Cannot locate task {task_id} under {l2}")
    return matches[0].relative_to(root).as_posix()


def resolve_card(root: Path, l2: str | None, task_id: str | None) -> str:
    if not l2 or not task_id:
        raise SystemExit("--card or both --l2 and --task-id are required")
    stage4 = find_stage4(root)
    card = stage4 / "03_tasks" / "cards" / l2 / f"{task_id}_验收卡片.md"
    if not card.exists():
        raise SystemExit(f"Cannot locate acceptance card for {task_id} under {l2}")
    return card.relative_to(root).as_posix()


def executor_prompt(task: str) -> str:
    return f"""Use $stage4-l3-orchestrator at `{SKILL_PATH}` as an execution sub-agent.

Assigned L3 task:

```text
{task}
```

Instructions:

1. Read `AGENTS.md`.
2. Read the skill, then read only the assigned L3 file and the context listed inside that file.
3. Validate task identity and dispatch YAML before editing.
4. Implement only the assigned L3.
5. Run the L3's local validation when possible.
6. Update the L3 success criteria and execution summary.
7. Do not edit dispatch indexes, do not choose another L3, and do not perform Git sync.

Final response: list changed files, validation commands, results, unverified items, and whether an acceptance card should be run next.
"""


def acceptor_prompt(card: str, round_number: str) -> str:
    return f"""Use $stage4-l3-orchestrator at `{SKILL_PATH}` as an acceptance sub-agent.

Assigned L3 acceptance card:

```text
{card}
```

Acceptance round: {round_number}

Instructions:

1. Read `AGENTS.md`.
2. Read the skill, then read the assigned acceptance card first.
3. Read only the L3 file, execution summary, allowed code/diff, and logs referenced by the card.
4. Follow the card's `acceptance_mode`.
5. Do not edit source, tests, dispatch, cards, task files, or Git state.
6. Write feedback to the path specified by the card.
7. Use one conclusion only: `PASS_LOCAL`, `FAIL_LOCAL`, `BLOCKED_ENV`, `BLOCKED_HARDWARE_EXPECTED`, or `DEFER_TO_L2_GATE`.
8. If the conclusion is `PASS_LOCAL`, do not archive files yourself; report that the main Agent must move the matching L3 task file to `DOCS/03_工程/阶段四：模型部署/03_tasks/completed/<l2>/`.

Final response: report the conclusion, feedback path, failed checks if any, and concrete fix requests for the execution sub-agent.
"""


def l2_acceptor_prompt(root: Path, l2: str) -> str:
    stage4 = find_stage4(root)
    card = stage4 / "03_tasks" / "cards" / l2 / f"{l2}_整体验收卡片.md"
    return f"""Use $stage4-l3-orchestrator at `{SKILL_PATH}` as an L2 acceptance sub-agent.

Assigned L2 acceptance card:

```text
{card.relative_to(root).as_posix()}
```

Instructions:

1. Read `AGENTS.md`.
2. Read the skill, then read the assigned L2 acceptance card.
3. Read the L2 dispatch index, all referenced L3 acceptance feedback files, and `05_acceptance/{l2}/验收结果.md`.
4. Summarize L3 acceptance status and L2 scenario coverage.
5. Generate `05_acceptance/{l2}/L2整体验收报告.md`.
6. Do not edit source code or perform Git sync.

Final response: report whether the L2 is locally accepted, blocked by environment, blocked by hardware, or failed.
"""


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = parse_args()
    root = Path.cwd()
    if args.role == "executor":
        task = args.task or resolve_task(root, args.l2, args.task_id)
        print(executor_prompt(task))
    elif args.role == "acceptor":
        card = args.card or resolve_card(root, args.l2, args.task_id)
        print(acceptor_prompt(card, args.round))
    else:
        if not args.l2:
            raise SystemExit("--l2 is required for l2-acceptor")
        print(l2_acceptor_prompt(root, args.l2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
