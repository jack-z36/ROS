#!/usr/bin/env python3
"""Validate a single L2's L3 generation outputs.

Usage:
    python3 validate_l3_generation_outputs.py <l2_id>

Checks:
- Task file identity (task_id == filename == body L3 number)
- dispatch YAML field validity (group, branch, integration_branch, mode, status, risk)
- Cross-reference validity (depends_on, blocks, can_run_parallel_with, must_run_after)
- Blocks/depends_on bidirectional consistency
- Card file existence and content
- Dispatch YAML structural consistency
- L2 acceptance card existence
- No cross-L2 ID pollution
"""

from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path

VALID_L2_IDS = {
    "l2-01-external-contract",
    "l2-02-observation-snapshot",
    "l2-03-act-inference",
    "l2-04-safety-guard",
    "l2-05-action-publisher",
    "l2-06-control-loop",
}

VALID_MODES = {
    "direct-local",
    "static-review",
    "downstream-l2",
    "hardware-blocked",
    "env-blocked",
}

VALID_STATUSES = {"ready", "blocked", "waiting_user"}
VALID_ROBOT_RISKS = {"none", "dry-run-only", "hardware-blocked", "real-robot"}

DISAPTCH_REQUIRED_FIELDS = [
    "cards_dir:",
    "l2_acceptance_card:",
    "l2_acceptance_report:",
    "acceptance_round_limit: 3",
]


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def task_id_from_filename(path: Path) -> str:
    match = re.search(r"(deploy_\d{3})", path.name)
    return match.group(1) if match else ""


def first_yaml_match(pattern: str, text: str) -> str:
    """Extract first value from YAML key: value line in dispatch block."""
    match = re.search(rf"^\s*{pattern}\s*:?\s*(.+)", text, re.MULTILINE)
    return match.group(1).strip() if match else ""


def yaml_list_values(key: str, text: str) -> list[str]:
    """Extract YAML list like `depends_on: [a, b]` or `depends_on: []`."""
    match = re.search(rf"^\s*{key}\s*:\s*\[(.*?)\]", text, re.MULTILINE)
    if not match:
        return []
    raw = match.group(1).strip()
    if not raw:
        return []
    return [v.strip() for v in raw.split(",")]


def body_l3_id(text: str) -> str:
    """Extract 'L3 编号：deploy_NNN' from body."""
    match = re.search(r"L3 编号：\s*(deploy_\d{3})", text)
    return match.group(1) if match else ""


def find_stage4(root: Path) -> Path:
    for path in (root / "DOCS").rglob("03_tasks"):
        if "阶段四" in str(path):
            return path.parent
    raise SystemExit("Cannot locate Stage 4 03_tasks directory")


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: validate_l3_generation_outputs.py <l2_id>", file=sys.stderr)
        return 2

    l2_id = sys.argv[1]
    if l2_id not in VALID_L2_IDS:
        print(f"ERROR: invalid l2_id: {l2_id}", file=sys.stderr)
        return 2

    root = Path.cwd()
    stage4 = find_stage4(root)

    active_dir = stage4 / "03_tasks" / "task" / "active" / l2_id
    completed_dir = stage4 / "03_tasks" / "completed" / l2_id
    cards_dir = stage4 / "03_tasks" / "cards" / l2_id
    dispatch_file = stage4 / "03_tasks" / "task" / "dispatch" / f"{l2_id}.yaml"

    errors: list[str] = []

    # ── 0. Locate task files across the normal mixed lifecycle ──
    # PASS_LOCAL archives one task at a time, so an L2 can legitimately have
    # completed and still-active tasks at the same moment.  Validate the union
    # instead of treating the two directories as mutually exclusive.
    active_task_files = sorted(active_dir.glob("deploy_*.md"))
    completed_task_files = (
        sorted(completed_dir.glob("deploy_*.md")) if completed_dir.is_dir() else []
    )
    task_files = sorted(active_task_files + completed_task_files)
    if not task_files:
        errors.append(f"no deploy_*.md task files in active/ or completed/ for {l2_id}")
        for e in errors:
            print(f"ERROR: {e}")
        return 1

    task_locations: dict[str, list[Path]] = defaultdict(list)
    for task_file in task_files:
        task_locations[task_id_from_filename(task_file)].append(task_file)
    for task_id, locations in task_locations.items():
        if task_id and len(locations) > 1:
            errors.append(
                f"{task_id} exists in both lifecycle directories: "
                f"{[rel(path, root) for path in locations]}"
            )

    # ── 1. First pass: collect all valid IDs and validate per-task identity/metadata ──
    valid_local_ids: set[str] = set()
    task_id_to_file: dict[str, Path] = {}
    task_texts: dict[str, str] = {}  # tid -> full text

    for tf in task_files:
        tid = task_id_from_filename(tf)
        if not tid:
            errors.append(f"{rel(tf, root)}: no deploy_NNN in filename")
            continue
        valid_local_ids.add(tid)
        task_id_to_file[tid] = tf

        text = tf.read_text(encoding="utf-8")
        task_texts[tid] = text
        rel_tf = rel(tf, root)
        expected_task_path = f"DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/{l2_id}/{tf.name}"

        # 1a. Identity
        body_id = body_l3_id(text)
        yaml_id = first_yaml_match("task_id", text)
        yaml_task_file = first_yaml_match("task_file", text)

        if body_id and tid != body_id:
            errors.append(f"{rel_tf}: body L3 编号={body_id} != filename={tid}")
        if yaml_id and tid != yaml_id:
            errors.append(f"{rel_tf}: dispatch.task_id={yaml_id} != filename={tid}")
        # task_file must point to active/ path (completed tasks keep active/ ref)
        completed_alt = f"DOCS/03_工程/阶段四：模型部署/03_tasks/completed/{l2_id}/{tf.name}"
        if yaml_task_file and yaml_task_file not in (expected_task_path, completed_alt):
            errors.append(f"{rel_tf}: dispatch.task_file={yaml_task_file}, expected={expected_task_path}")

        # 1b. Group / branch / integration
        yaml_group = first_yaml_match("group", text)
        yaml_branch = first_yaml_match("branch", text)
        yaml_int = first_yaml_match("integration_branch", text)

        if yaml_group and yaml_group != l2_id:
            errors.append(f"{rel_tf}: dispatch.group={yaml_group} != {l2_id}")
        if yaml_branch and yaml_branch != f"feat/model_deploy/{l2_id}":
            errors.append(f"{rel_tf}: dispatch.branch={yaml_branch}, expected feat/model_deploy/{l2_id}")
        if yaml_int and yaml_int != "model_deploy":
            errors.append(f"{rel_tf}: dispatch.integration_branch={yaml_int} != model_deploy")

        # 1c. Mode / round / status / risk
        yaml_mode = first_yaml_match("acceptance_mode", text)
        yaml_round = first_yaml_match("acceptance_round_limit", text)
        yaml_status = first_yaml_match("dispatch_status", text)
        yaml_risk = first_yaml_match("robot_risk", text)

        if yaml_mode and yaml_mode not in VALID_MODES:
            errors.append(f"{rel_tf}: invalid acceptance_mode={yaml_mode}")
        if yaml_round and yaml_round != "3":
            errors.append(f"{rel_tf}: acceptance_round_limit={yaml_round} (must be 3)")
        if yaml_status and yaml_status not in VALID_STATUSES:
            errors.append(f"{rel_tf}: invalid dispatch_status={yaml_status}")
        if yaml_risk and yaml_risk not in VALID_ROBOT_RISKS:
            errors.append(f"{rel_tf}: invalid robot_risk={yaml_risk}")

        # 1d. Card
        card_path_s = first_yaml_match("acceptance_card", text)
        if not card_path_s:
            errors.append(f"{rel_tf}: missing acceptance_card")
        else:
            card_path = root / card_path_s
            if not card_path.exists():
                errors.append(f"{rel_tf}: acceptance_card file missing: {card_path_s}")
            else:
                card_text = card_path.read_text(encoding="utf-8")
                if f"| L3 编号 | `{tid}` |" not in card_text:
                    errors.append(f"{rel(tf, root)}: card id mismatch (expected | L3 编号 | `{tid}` |)")
                if yaml_mode and f"| 验收模式 | `{yaml_mode}` |" not in card_text:
                    errors.append(f"{rel(tf, root)}: card mode mismatch (expected | 验收模式 | `{yaml_mode}` |)")
                if yaml_mode == "direct-local" and "```bash" not in card_text:
                    errors.append(f"{rel(tf, root)}: direct-local card lacks ```bash block")

        # 1e. Self-reference (checked in first pass; cross-refs in second pass)
        blocks = yaml_list_values("blocks", text)
        deps = yaml_list_values("depends_on", text)
        if tid in blocks:
            errors.append(f"{rel_tf}: self-referencing in blocks")
        if tid in deps:
            errors.append(f"{rel_tf}: self-referencing in depends_on")

    if not valid_local_ids:
        for e in errors:
            print(f"ERROR: {e}")
        return 1

    # ── 1e (second pass). Cross-reference validity ──
    # Must run after all valid_local_ids are collected.
    for tf in task_files:
        tid = task_id_from_filename(tf)
        text = task_texts[tid]
        rel_tf = rel(tf, root)
        for ref_field in ("depends_on", "must_run_after", "can_run_parallel_with", "blocks"):
            refs = yaml_list_values(ref_field, text)
            for ref in refs:
                if not ref:
                    continue
                if not re.match(r"^deploy_\d{3}$", ref):
                    errors.append(f"{rel_tf}: {ref_field} contains invalid format: {ref}")
                    continue
                if ref not in valid_local_ids:
                    errors.append(f"{rel_tf}: {ref_field} references unknown task_id {ref} "
                                  f"(valid in {l2_id}: {sorted(valid_local_ids)})")

    # ── 2. Cross-task consistency ──
    for tf in task_files:
        tid = task_id_from_filename(tf)
        text = tf.read_text(encoding="utf-8")
        blocks = yaml_list_values("blocks", text)

        for blocked_id in blocks:
            if blocked_id not in task_id_to_file:
                continue  # already caught above
            dep_text = task_id_to_file[blocked_id].read_text(encoding="utf-8")
            dep_deps = yaml_list_values("depends_on", dep_text)
            if tid not in dep_deps:
                errors.append(f"{rel(tf, root)}: {tid}.blocks contains {blocked_id}, "
                              f"but {blocked_id}.depends_on does not include {tid}")

    # ── 3. Dispatch YAML validation ──
    if not dispatch_file.is_file():
        errors.append(f"dispatch YAML missing: {rel(dispatch_file, root)}")
    else:
        dt = dispatch_file.read_text(encoding="utf-8")
        for field in DISAPTCH_REQUIRED_FIELDS:
            if field not in dt:
                errors.append(f"{rel(dispatch_file, root)}: missing required field: {field.strip(':')}")

        # dispatch l2 card existence
        l2_card_s = first_yaml_match("l2_acceptance_card", dt)
        if l2_card_s and not (root / l2_card_s).exists():
            errors.append(f"{rel(dispatch_file, root)}: L2 acceptance card missing: {l2_card_s}")

        # task/card/mode count
        task_count = len(re.findall(r"^    deploy_\d{3}:", dt, flags=re.MULTILINE))
        card_count = len(re.findall(r"^      acceptance_card:", dt, flags=re.MULTILINE))
        mode_count = len(re.findall(r"^      acceptance_mode:", dt, flags=re.MULTILINE))
        if task_count != card_count or task_count != mode_count:
            errors.append(f"{rel(dispatch_file, root)}: task/card/mode count mismatch: "
                          f"{task_count}/{card_count}/{mode_count}")

        # dispatch declares the same tasks as the active+completed union
        dispatch_task_ids: set[str] = set(re.findall(r"^    (deploy_\d{3}):", dt, flags=re.MULTILINE))
        extra_in_dispatch = dispatch_task_ids - valid_local_ids
        missing_from_dispatch = valid_local_ids - dispatch_task_ids
        if extra_in_dispatch:
            errors.append(f"{rel(dispatch_file, root)}: dispatch declares tasks not in active/completed: "
                          f"{sorted(extra_in_dispatch)}")
        if missing_from_dispatch:
            errors.append(f"{rel(dispatch_file, root)}: active/completed has tasks not in dispatch: "
                          f"{sorted(missing_from_dispatch)}")

        # wave consistency: every task_id in waves must exist
        wave_tasks = set(re.findall(r"tasks:\s*\[([^\]]+)\]", dt))
        wave_ids: set[str] = set()
        for block in wave_tasks:
            wave_ids.update(re.findall(r"(deploy_\d{3})", block))
        missing_in_waves = valid_local_ids - wave_ids
        if missing_in_waves:
            errors.append(f"{rel(dispatch_file, root)}: tasks not assigned to any wave: "
                          f"{sorted(missing_in_waves)}")
        ghost_in_waves = wave_ids - valid_local_ids
        if ghost_in_waves:
            errors.append(f"{rel(dispatch_file, root)}: wave references unknown tasks: "
                          f"{sorted(ghost_in_waves)}")

    # ── 4. Card directory consistency ──
    if cards_dir.is_dir():
        active_card_ids = set()
        for tf in task_files:
            text = tf.read_text(encoding="utf-8")
            card_s = first_yaml_match("acceptance_card", text)
            if card_s and "/" in card_s:
                cid = task_id_from_filename(Path(card_s))
                if cid:
                    active_card_ids.add(cid)

        card_files = sorted(cards_dir.glob("deploy_*.md"))
        card_ids = {task_id_from_filename(c) for c in card_files}
        card_ids.discard("")

        missing_cards = valid_local_ids - card_ids
        extra_cards = card_ids - valid_local_ids
        if missing_cards:
            errors.append(f"cards/{l2_id}: missing card for: {sorted(missing_cards)}")
        if extra_cards:
            errors.append(f"cards/{l2_id}: extra cards with no matching task: {sorted(extra_cards)}")

    # ── 5. L2 overall acceptance card ──
    l2_card_expected = cards_dir / f"{l2_id}_整体验收卡片.md"
    if not l2_card_expected.exists():
        # try without L2 prefix if needed
        alternatives = list(cards_dir.glob("*整体验收卡片.md"))
        if not alternatives:
            errors.append(f"L2 overall acceptance card missing in {rel(cards_dir, root)}")

    # ── 6. Cross-L2 pollution check ──
    # Ensure no task references IDs from other L2 ranges.
    # L2-NN tasks use deploy IDs in range [(NN-1)*10+1, NN*10].
    l2_number = int(l2_id[3:5])  # 01..06
    min_id = (l2_number - 1) * 10 + 1   # L2-01 -> 001, L2-02 -> 011, ...
    max_id = l2_number * 10              # L2-01 -> 010, L2-02 -> 020, ...

    for tf in task_files:
        text = tf.read_text(encoding="utf-8")
        for ref_field in ("depends_on", "must_run_after", "can_run_parallel_with", "blocks"):
            refs = yaml_list_values(ref_field, text)
            for ref in refs:
                if not ref or not re.match(r"^deploy_\d{3}$", ref):
                    continue
                ref_num = int(ref[-3:])
                if ref_num < min_id or ref_num > max_id:
                    errors.append(f"{rel(tf, root)}: {ref_field} references {ref} "
                                  f"outside expected range {min_id:03d}-{max_id:03d} for {l2_id}")

    # ── Result ──
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        print(f"\n{len(errors)} validation error(s) found for {l2_id}")
        return 1

    print(f"PASS stage4 L3 generation outputs: {l2_id}")
    print(f"  Tasks: {len(task_files)}")
    print(f"  Dispatch: {rel(dispatch_file, root)} ({len(valid_local_ids)} tasks)")
    card_file_count = len(list(cards_dir.glob("deploy_*.md"))) if cards_dir.is_dir() else 0
    print(f"  Cards: {card_file_count} + L2 overall")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
