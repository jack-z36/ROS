#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path


VALID_MODES = {
    "direct-local",
    "static-review",
    "downstream-l2",
    "hardware-blocked",
    "env-blocked",
}


def find_stage4(root: Path) -> Path:
    for path in (root / "DOCS").rglob("03_tasks"):
        if "\u9636\u6bb5\u56db" in str(path):
            return path.parent
    raise SystemExit("Cannot locate Stage 4 03_tasks directory")


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def task_identity(path: Path) -> str:
    match = re.search(r"deploy_\d{3}", path.name)
    return match.group(0) if match else ""


def first_match(pattern: str, text: str) -> str:
    match = re.search(pattern, text, re.MULTILINE)
    return match.group(1).strip() if match else ""


def main() -> int:
    root = Path.cwd()
    stage4 = find_stage4(root)
    active_root = stage4 / "03_tasks" / "task" / "active"
    completed_root = stage4 / "03_tasks" / "completed"
    dispatch_root = stage4 / "03_tasks" / "task" / "dispatch"
    cards_root = stage4 / "03_tasks" / "cards"

    errors: list[str] = []
    modes: dict[str, str] = {}
    active_files = sorted(active_root.rglob("deploy_*.md"))
    completed_files = sorted(completed_root.rglob("deploy_*.md")) if completed_root.exists() else []
    task_files = active_files + completed_files

    seen_task_ids: dict[str, str] = {}
    for task_file in task_files:
        task_id_s = task_identity(task_file)
        if not task_id_s:
            continue
        previous = seen_task_ids.get(task_id_s)
        if previous:
            errors.append(f"{task_id_s} exists in multiple task locations: {previous}, {rel(task_file, root)}")
        seen_task_ids[task_id_s] = rel(task_file, root)

    for task_file in task_files:
        text = task_file.read_text(encoding="utf-8")
        task_id_s = task_identity(task_file)
        if not task_id_s:
            errors.append(f"{rel(task_file, root)} has no deploy id in filename")
            continue
        body_id = first_match(r"L3 编号：\s*(deploy_\d{3})", text)
        yaml_id = first_match(r"task_id:\s*(deploy_\d{3})", text)
        task_file_yaml = first_match(r"task_file:\s*(.+)", text)
        card_path_s = first_match(r"acceptance_card:\s*(.+)", text)
        mode = first_match(r"acceptance_mode:\s*([a-z-]+)", text)
        round_limit = first_match(r"acceptance_round_limit:\s*(\d+)", text)

        if task_id_s != body_id or task_id_s != yaml_id:
            errors.append(f"{rel(task_file, root)} id mismatch: filename={task_id_s} body={body_id} yaml={yaml_id}")
        expected_paths = {rel(task_file, root)}
        if completed_root in task_file.parents:
            l2 = task_file.parent.name
            expected_paths.add(rel(active_root / l2 / task_file.name, root))
        if task_file_yaml not in expected_paths:
            errors.append(f"{task_id_s} task_file mismatch: {task_file_yaml}")
        if mode not in VALID_MODES:
            errors.append(f"{task_id_s} invalid acceptance_mode: {mode}")
        if round_limit != "3":
            errors.append(f"{task_id_s} acceptance_round_limit must be 3")
        if not card_path_s:
            errors.append(f"{task_id_s} missing acceptance_card")
            continue

        card_path = root / card_path_s
        if not card_path.exists():
            errors.append(f"{task_id_s} missing card file: {card_path_s}")
            continue
        card = card_path.read_text(encoding="utf-8")
        if f"| L3 编号 | `{task_id_s}` |" not in card:
            errors.append(f"{task_id_s} card id mismatch")
        if f"| 验收模式 | `{mode}` |" not in card:
            errors.append(f"{task_id_s} card mode mismatch")
        if mode == "direct-local" and "```bash" not in card:
            errors.append(f"{task_id_s} direct-local card lacks bash command block")
        if mode == "static-review" and "静态评审清单" not in card:
            errors.append(f"{task_id_s} static-review card lacks checklist")
        if "hardware-blocked" in card and "不能写成真机通过" not in card:
            errors.append(f"{task_id_s} hardware-blocked card lacks no-hardware warning")
        modes[task_id_s] = mode

    if modes and all(mode == "direct-local" for mode in modes.values()):
        errors.append("all L3 tasks are direct-local; expected mixed acceptance modes")
    if modes and "deploy_023" in modes and modes.get("deploy_023") != "hardware-blocked":
        errors.append("deploy_023 must be hardware-blocked")

    for dispatch_file in sorted(dispatch_root.glob("*.yaml")):
        text = dispatch_file.read_text(encoding="utf-8")
        for field in ("cards_dir:", "l2_acceptance_card:", "l2_acceptance_report:", "acceptance_round_limit: 3"):
            if field not in text:
                errors.append(f"{rel(dispatch_file, root)} missing {field}")
        l2_card_s = first_match(r"l2_acceptance_card:\s*(.+)", text)
        if l2_card_s and not (root / l2_card_s).exists():
            errors.append(f"{rel(dispatch_file, root)} missing L2 acceptance card file: {l2_card_s}")
        task_count = len(re.findall(r"^    deploy_\d{3}:", text, flags=re.MULTILINE))
        card_count = len(re.findall(r"^      acceptance_card:", text, flags=re.MULTILINE))
        mode_count = len(re.findall(r"^      acceptance_mode:", text, flags=re.MULTILINE))
        if task_count != card_count or task_count != mode_count:
            errors.append(f"{rel(dispatch_file, root)} task/card/mode count mismatch: {task_count}/{card_count}/{mode_count}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print(
        "PASS stage4 L3 acceptance cards: "
        f"{len(active_files)} active L3 tasks, {len(completed_files)} completed L3 tasks"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
