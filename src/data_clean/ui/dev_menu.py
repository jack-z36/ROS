"""Developer menu for Stage 2 service scenario checks."""

from __future__ import annotations

import argparse
from collections.abc import Callable
from pathlib import Path
from typing import Any

from runtime.scene2_mcap_a_writer import run_scene2_mcap_a_writer
from runtime.scene2_pose_filter import run_scene2_pose_filter
from runtime.scene2_signal_reliability import run_scene2_signal_reliability_detection
from runtime.scene2_signal_repair import run_scene2_signal_repair
from runtime.scene2_tactile_filter import run_scene2_tactile_filter
from ui.scene1_dev_checks import (
    run_scene1_arm_base_pose_transform,
    run_scene1_common_pose_transform,
    run_scene1_frame_alignment_config,
    run_scene1_gripper_calibration_config,
    run_scene1_gripper_width_extract,
    run_scene1_output_contract_validate,
    run_scene1_smoke_test,
    save_frame_alignment_to_production,
)

MenuRunner = Callable[[argparse.Namespace], int]
Scene1Runner = Callable[[str | Path], Any]


def _latest_mcap(input_dir: Path) -> Path | None:
    files = sorted((path for path in input_dir.glob("*.mcap") if path.is_file()), key=lambda path: path.stat().st_mtime, reverse=True)
    return files[0] if files else None


def _run_scene1_frame_alignment_check(args: argparse.Namespace) -> int:
    print()
    print("*** [已废弃] scene1_frame_alignment_config ***")
    print()
    print("此检验项已废弃。common_frame / FrameAlignmentConfig 配置生成")
    print("路线已从主路线移除。新路线改为由用户直接输入 work_frame_")
    print("in_arm_base_pose，不再需要生成 common_from_left/right_start。")
    print()
    print("此功能保留仅用于检查既有配置的历史兼容性。")
    print()

    answer = input("继续检查旧配置？[y/N]: ").strip().lower()
    if answer not in {"y", "yes"}:
        print("已取消。")
        return 0

    try:
        dev_run = run_scene1_frame_alignment_config(Path(args.config))
    except Exception as exc:
        print(f"配置检查失败: {exc}")
        return 1

    print()
    save_answer = input("是否保存检查结果到正式配置？[y/N]: ").strip().lower()
    if save_answer in {"y", "yes"}:
        try:
            save_frame_alignment_to_production(dev_run, Path(args.config))
        except Exception as exc:
            print(f"保存失败: {exc}")
            return 1
    else:
        print("保留临时配置，未写入正式配置。")
    return 0


def _scene1_runner(check_id: str, runner: Scene1Runner) -> MenuRunner:
    def wrapped(args: argparse.Namespace) -> int:
        print()
        print(f"运行 {check_id} ...")
        try:
            dev_run = runner(Path(args.config))
        except Exception as exc:
            print(f"检验失败: {exc}")
            return 1
        return 0 if getattr(dev_run, "status", "success") == "success" else 1

    return wrapped


def run_scene2_signal_reliability_check(args: argparse.Namespace) -> int:
    configured_input_dir = Path(args.cleaned_mcap_dir) if args.cleaned_mcap_dir else Path("asset/阶段二：数据清洗/dev/mcap_cleaned")
    default_mcap = _latest_mcap(configured_input_dir)
    prompt = "请输入 cleaned MCAP 路径"
    if default_mcap is not None:
        prompt += f" [默认: {default_mcap}]"
    prompt += ": "
    selected = input(prompt).strip()
    if selected:
        cleaned_mcap = Path(selected)
    elif default_mcap is not None:
        cleaned_mcap = default_mcap
    else:
        print("未找到 cleaned MCAP 小样本，请输入有效路径后重试。")
        return 1

    result = run_scene2_signal_reliability_detection(
        cleaned_mcap_path=cleaned_mcap,
        config_path=Path(args.config),
        run_root=Path(args.run_root),
    )
    print("场景二异常检测完成" if result["status"] == "success" else "场景二异常检测失败")
    print(f"  run_dir: {result['outputs']['run_dir']}")
    print(f"  result: {result['outputs']['signal_reliability_detection_result_json']}")
    print(f"  run_log: {result['run_log_path']}")
    return 0 if result["status"] == "success" else 1


def run_scene2_signal_repair_check(args: argparse.Namespace) -> int:
    configured_input_dir = Path(args.cleaned_mcap_dir) if args.cleaned_mcap_dir else Path("asset/阶段二：数据清洗/dev/mcap_cleaned")
    default_mcap = _latest_mcap(configured_input_dir)
    prompt = "请输入 cleaned MCAP 路径"
    if default_mcap is not None:
        prompt += f" [默认: {default_mcap}]"
    prompt += ": "
    selected = input(prompt).strip()
    if selected:
        cleaned_mcap = Path(selected)
    elif default_mcap is not None:
        cleaned_mcap = default_mcap
    else:
        print("未找到 cleaned MCAP 小样本，请输入有效路径后重试。")
        return 1

    result = run_scene2_signal_repair(
        cleaned_mcap_path=cleaned_mcap,
        config_path=Path(args.config),
        run_root=Path(args.run_root),
    )
    print("场景二数据补全完成" if result["status"] == "success" else "场景二数据补全失败")
    print(f"  run_dir: {result['outputs']['run_dir']}")
    print(f"  result: {result['outputs']['signal_repair_result_json']}")
    print(f"  repaired_sequences: {result['outputs']['repaired_sequences_dir']}")
    print(f"  run_log: {result['run_log_path']}")
    return 0 if result["status"] == "success" else 1


def run_scene2_pose_filter_check(args: argparse.Namespace) -> int:
    configured_input_dir = Path(args.cleaned_mcap_dir) if args.cleaned_mcap_dir else Path("asset/阶段二：数据清洗/dev/mcap_cleaned")
    default_mcap = _latest_mcap(configured_input_dir)
    prompt = "请输入 cleaned MCAP 路径"
    if default_mcap is not None:
        prompt += f" [默认: {default_mcap}]"
    prompt += ": "
    selected = input(prompt).strip()
    if selected:
        cleaned_mcap = Path(selected)
    elif default_mcap is not None:
        cleaned_mcap = default_mcap
    else:
        print("未找到 cleaned MCAP 小样本，请输入有效路径后重试。")
        return 1

    result = run_scene2_pose_filter(
        cleaned_mcap_path=cleaned_mcap,
        config_path=Path(args.config),
        run_root=Path(args.run_root),
    )
    print("场景二位姿滤波完成" if result["status"] == "success" else "场景二位姿滤波失败")
    print(f"  run_dir: {result['outputs']['run_dir']}")
    print(f"  result: {result['outputs']['pose_filter_result_json']}")
    print(f"  diff_summary: {result['outputs']['pose_filter_diff_summary_json']}")
    print(f"  filtered_pose_sequences: {result['outputs']['filtered_pose_sequences_dir']}")
    print(f"  run_log: {result['run_log_path']}")
    print()
    print("  坐标语义:")
    print("    input_pose_frame: left_arm_base/right_arm_base")
    print("    output_pose_frame: left_arm_base/right_arm_base")
    print("    common_frame_to_robot_base: not required")
    return 0 if result["status"] == "success" else 1


def run_scene2_tactile_filter_check(args: argparse.Namespace) -> int:
    configured_input_dir = Path(args.cleaned_mcap_dir) if args.cleaned_mcap_dir else Path("asset/阶段二：数据清洗/dev/mcap_cleaned")
    default_mcap = _latest_mcap(configured_input_dir)
    prompt = "请输入 cleaned MCAP 路径"
    if default_mcap is not None:
        prompt += f" [默认: {default_mcap}]"
    prompt += ": "
    selected = input(prompt).strip()
    if selected:
        cleaned_mcap = Path(selected)
    elif default_mcap is not None:
        cleaned_mcap = default_mcap
    else:
        print("未找到 cleaned MCAP 小样本，请输入有效路径后重试。")
        return 1

    result = run_scene2_tactile_filter(
        cleaned_mcap_path=cleaned_mcap,
        config_path=Path(args.config),
        run_root=Path(args.run_root),
    )
    print("场景二触觉滤波完成" if result["status"] == "success" else "场景二触觉滤波失败")
    print(f"  run_dir: {result['outputs']['run_dir']}")
    print(f"  result: {result['outputs']['tactile_filter_result_json']}")
    print(f"  diff_summary: {result['outputs']['tactile_filter_diff_summary_json']}")
    print(f"  filtered_tactile_sequences: {result['outputs']['filtered_tactile_sequences_dir']}")
    print(f"  run_log: {result['run_log_path']}")
    return 0 if result["status"] == "success" else 1


def run_scene2_mcap_a_writer_check(args: argparse.Namespace) -> int:
    configured_input_dir = Path(args.cleaned_mcap_dir) if args.cleaned_mcap_dir else Path("asset/阶段二：数据清洗/dev/mcap_cleaned")
    default_mcap = _latest_mcap(configured_input_dir)
    prompt = "请输入 cleaned MCAP 路径"
    if default_mcap is not None:
        prompt += f" [默认: {default_mcap}]"
    prompt += ": "
    selected = input(prompt).strip()
    if selected:
        cleaned_mcap = Path(selected)
    elif default_mcap is not None:
        cleaned_mcap = default_mcap
    else:
        print("未找到 cleaned MCAP 小样本，请输入有效路径后重试。")
        return 1

    result = run_scene2_mcap_a_writer(
        cleaned_mcap_path=cleaned_mcap,
        config_path=Path(args.config),
        run_root=Path(args.run_root),
    )
    print("场景二 MCAP_A 写出完成" if result["status"] == "success" else "场景二 MCAP_A 写出失败")
    print(f"  run_dir: {result['outputs']['run_dir']}")
    print(f"  mcap_a: {result['outputs']['mcap_a']}")
    print(f"  summary: {result['outputs']['mcap_a_write_summary_json']}")
    print(f"  run_log: {result['run_log_path']}")
    print()
    print("  当前路线:")
    print("    IK: not in current route")
    print("    MCAP_B: not in current route")
    print("    joint_limit_check: not in current route")
    print("    arm_base_input: arm-base TCP pose topics consumed from cleaned MCAP")
    return 0 if result["status"] == "success" else 1


SCENE1_CHECKS: list[tuple[str, str, MenuRunner]] = [
    ("scene1_frame_alignment_config", "[已废弃] 位姿转换配置生成", _run_scene1_frame_alignment_check),
    ("scene1_arm_base_pose_transform", "arm-base 位姿转换（新链路，不再依赖 common_frame）", _scene1_runner("scene1_arm_base_pose_transform", run_scene1_arm_base_pose_transform)),
    ("scene1_common_pose_transform", "位姿转换（旧链路，common_frame 兼容）", _scene1_runner("scene1_common_pose_transform", run_scene1_common_pose_transform)),
    ("scene1_gripper_width_extract", "夹爪开合提取", _scene1_runner("scene1_gripper_width_extract", run_scene1_gripper_width_extract)),
    ("scene1_gripper_calibration_config", "夹爪开合配置生成", _scene1_runner("scene1_gripper_calibration_config", run_scene1_gripper_calibration_config)),
    ("scene1_output_contract_validate", "检查配置报告是否完整", _scene1_runner("scene1_output_contract_validate", run_scene1_output_contract_validate)),
    ("scene1_smoke_test", "全场景测试", _scene1_runner("scene1_smoke_test", run_scene1_smoke_test)),
]

SCENE2_CHECKS: list[tuple[str, str, MenuRunner]] = [
    ("scene2_signal_reliability_detect", "异常检测：位姿/夹爪/触觉", run_scene2_signal_reliability_check),
    ("scene2_signal_repair", "数据补全：repair run 与三模态补全", run_scene2_signal_repair_check),
    ("scene2_pose_filter", "位姿滤波：SG 平滑与 guard 审计", run_scene2_pose_filter_check),
    ("scene2_tactile_filter", "触觉滤波：中值 EMA 平滑与 diff 审计", run_scene2_tactile_filter_check),
    ("scene2_mcap_a_writer", "MCAP_A 写出：完整场景二验证链路", run_scene2_mcap_a_writer_check),
]

SCENE_MENUS: list[tuple[str, str, list[tuple[str, str, MenuRunner]]]] = [
    ("scene1", "场景一：提取夹爪开合以及位姿转换", SCENE1_CHECKS),
    ("scene2", "场景二：硬件数据可靠性验证", SCENE2_CHECKS),
    ("scene3", "场景三：MCAP 多 topic 时间轴对齐", []),
    ("scene4", "场景四：构建标准 canonical dataset", []),
    ("scene5", "场景五：模型训练格式导出器", []),
]


def _choose_index(count: int, prompt: str) -> int | None:
    choice = input(prompt).strip().lower()
    if choice in {"q", "quit", "exit"}:
        return None
    try:
        index = int(choice)
    except ValueError:
        print(f"无效选择: {choice}")
        return None
    if not 1 <= index <= count:
        print(f"选择超出范围: {choice}")
        return None
    return index - 1


def run_dev_menu(args: argparse.Namespace) -> int:
    print("开发者引导界面")
    for index, (_scene_id, label, _checks) in enumerate(SCENE_MENUS, start=1):
        print(f"  {index}. {label}")
    print("  q. 退出")
    scene_index = _choose_index(len(SCENE_MENUS), "选择场景: ")
    if scene_index is None:
        return 0

    _scene_id, scene_label, checks = SCENE_MENUS[scene_index]
    if not checks:
        print(f"{scene_label} 暂无功能检验项。")
        return 1

    print(scene_label)
    for index, (check_id, label, _runner) in enumerate(checks, start=1):
        print(f"  {index}. {check_id} - {label}")
    print("  q. 退出")
    check_index = _choose_index(len(checks), "选择功能检验项: ")
    if check_index is None:
        return 0
    _check_id, _label, runner = checks[check_index]
    return runner(args)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="阶段二开发者引导菜单。")
    parser.add_argument("--config", required=True, help="数据清洗配置文件。")
    parser.add_argument("--run-root", default="src/data_clean/runs", help="调试 run 目录根路径。")
    parser.add_argument("--cleaned-mcap-dir", default="asset/阶段二：数据清洗/dev/mcap_cleaned", help="cleaned MCAP 默认搜索目录。")
    return parser


def main(argv: list[str] | None = None) -> int:
    return run_dev_menu(build_parser().parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
