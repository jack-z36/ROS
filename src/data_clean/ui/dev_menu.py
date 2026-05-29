"""Developer menu for Stage 2 service scenario checks."""

from __future__ import annotations

import argparse
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any

from runtime.scene2_mcap_a_writer import run_scene2_mcap_a_writer
from runtime.scene2_pose_filter import run_scene2_pose_filter
from runtime.scene2_signal_reliability import run_scene2_signal_reliability_detection
from runtime.scene2_signal_repair import run_scene2_signal_repair
from runtime.scene2_tactile_filter import run_scene2_tactile_filter
from runtime.scene3_mcap_a_input_check import run_scene3_mcap_a_input_check
from runtime.scene3_alignment_report_check import run_scene3_alignment_report_check
from runtime.scene3_field_alignment_check import run_scene3_field_alignment_check
from runtime.scene3_aligned_mcap_write_check import run_scene3_aligned_mcap_write_check
from runtime.scene3_full_flow_check import run_scene3_full_flow_check
from runtime.scene3_step_timeline_check import run_scene3_step_timeline_check
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
SCENE3_DEFAULT_ALIGNED_OUTPUT_ROOT = Path("/home/hit/ROS/asset/阶段二：数据清洗/dev/03_aligned_mcap")


def scene3_default_aligned_output_dir(
    check_id: str | None = None,
    *,
    now: datetime | None = None,
) -> Path:
    """Return a per-run default Scene 3 aligned MCAP output directory."""
    _ = check_id
    timestamp = (now or datetime.now()).strftime("%m-%d-%H:%M")
    return SCENE3_DEFAULT_ALIGNED_OUTPUT_ROOT / timestamp


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


def run_scene3_mcap_a_input_check_check(args: argparse.Namespace) -> int:
    """Interactive runner for scene3_mcap_a_input_check developer entry."""
    import json

    from schemas.alignment_config import Scene3AlignmentConfig

    default_mcap_a = None
    if args.cleaned_mcap_dir:
        import glob
        mcap_dir = Path(args.cleaned_mcap_dir)
        if mcap_dir.is_dir():
            mcap_files = sorted(mcap_dir.glob("*mcap_a*.mcap"))
            if mcap_files:
                default_mcap_a = mcap_files[-1]

    prompt_mcap = "请输入 MCAP_A 路径"
    if default_mcap_a is not None:
        prompt_mcap += f" [默认: {default_mcap_a}]"
    prompt_mcap += ": "
    selected_mcap = input(prompt_mcap).strip()
    if selected_mcap:
        mcap_a_path = Path(selected_mcap)
    elif default_mcap_a is not None:
        mcap_a_path = default_mcap_a
    else:
        print("未找到 MCAP_A 小样本，请输入有效路径后重试。")
        return 1

    default_summary = mcap_a_path.parent / "mcap_a_write_summary.json"
    prompt_summary = f"请输入 mcap_a_write_summary.json 路径 [默认: {default_summary}]: "
    selected_summary = input(prompt_summary).strip()
    if selected_summary:
        summary_path = Path(selected_summary)
    elif default_summary.exists():
        summary_path = default_summary
    else:
        summary_path = default_summary.parent / "mcap_a_write_summary.json"

    config = Scene3AlignmentConfig()

    result = run_scene3_mcap_a_input_check(
        mcap_a_path=mcap_a_path,
        summary_path=summary_path,
        config=config,
        run_root=Path(args.run_root),
    )

    status_text = "完成" if result["status"] == "success" else "失败"
    print(f"场景三 MCAP_A 输入检验{status_text}")
    print(f"  run_dir: {result['outputs']['run_dir']}")
    print(f"  catalog: {result['outputs']['source_topic_catalog_json']}")
    print(f"  validation_summary: {result['outputs']['mcap_a_input_validation_summary_json']}")
    print(f"  run_log: {result['run_log_path']}")

    v = result.get("validation", {})
    if v.get("hard_fail_reasons"):
        print(f"  hard_fail: {', '.join(v['hard_fail_reasons'])}")
    if v.get("warnings"):
        print(f"  warnings: {', '.join(v['warnings'])}")
    if v.get("optional_field_warnings"):
        print(f"  optional_field_warnings: {', '.join(v['optional_field_warnings'])}")

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

def run_scene3_step_timeline_check_check(args: argparse.Namespace) -> int:
    """Interactive runner for scene3_step_timeline_check developer entry."""
    import json

    from schemas.alignment_config import Scene3AlignmentConfig

    default_catalog = None
    default_validation = None
    if args.cleaned_mcap_dir:
        mcap_dir = Path(args.cleaned_mcap_dir)
        if mcap_dir.is_dir():
            catalog_files = sorted(mcap_dir.glob("*catalog*.json"))
            if catalog_files:
                default_catalog = catalog_files[-1]
            val_files = sorted(mcap_dir.glob("*validation_summary*.json"))
            if val_files:
                default_validation = val_files[-1]

    prompt_catalog = "请输入 source_topic_catalog.json 路径"
    if default_catalog is not None:
        prompt_catalog += f" [默认: {default_catalog}]"
    prompt_catalog += ": "
    selected_catalog = input(prompt_catalog).strip()
    if selected_catalog:
        catalog_path = Path(selected_catalog)
    elif default_catalog is not None:
        catalog_path = default_catalog
    else:
        print("未找到 source_topic_catalog.json 小样本，请输入有效路径后重试。")
        return 1

    prompt_val = "请输入 mcap_a_input_validation_summary.json 路径"
    if default_validation is not None:
        prompt_val += f" [默认: {default_validation}]"
    prompt_val += ": "
    selected_val = input(prompt_val).strip()
    if selected_val:
        validation_path = Path(selected_val)
    elif default_validation is not None:
        validation_path = default_validation
    else:
        validation_path = catalog_path.parent / "mcap_a_input_validation_summary.json"

    config = Scene3AlignmentConfig()

    hz_input = input(f"请输入 target_step_hz [默认: {config.target_step_hz}]: ").strip()
    if hz_input:
        try:
            config.target_step_hz = int(hz_input)
        except ValueError:
            print(f"无效频率: {hz_input}，使用默认 {config.target_step_hz}")

    result = run_scene3_step_timeline_check(
        catalog_path=catalog_path,
        validation_summary_path=validation_path,
        config=config,
        run_root=Path(args.run_root),
    )

    status_text = "完成" if result["status"] == "success" else "失败"
    print(f"场景三 Step 时间轴检验{status_text}")
    print(f"  run_dir: {result['outputs']['run_dir']}")
    if result["outputs"].get("step_timeline_json"):
        print(f"  step_timeline: {result['outputs']['step_timeline_json']}")
    if result["outputs"].get("step_timeline_generation_summary_json"):
        print(f"  generation_summary: {result['outputs']['step_timeline_generation_summary_json']}")
    print(f"  run_log: {result['run_log_path']}")

    if result.get("step_count") is not None:
        print(f"  step_count: {result['step_count']}")
        if result.get("first_step_time_ns") is not None:
            print(f"  first_step_time_ns: {result['first_step_time_ns']}")
        if result.get("last_step_time_ns") is not None:
            print(f"  last_step_time_ns: {result['last_step_time_ns']}")

    if result.get("failure_reasons"):
        print(f"  失败原因: {', '.join(result['failure_reasons'])}")

    return 0 if result["status"] == "success" else 1


def run_scene3_field_alignment_check_check(args: argparse.Namespace) -> int:
    """Interactive runner for scene3_field_alignment_check developer entry."""
    import json

    from schemas.alignment_config import Scene3AlignmentConfig

    default_catalog = None
    default_validation = None
    default_timeline = None
    if args.cleaned_mcap_dir:
        mcap_dir = Path(args.cleaned_mcap_dir)
        if mcap_dir.is_dir():
            catalog_files = sorted(mcap_dir.glob("*catalog*.json"))
            if catalog_files:
                default_catalog = catalog_files[-1]
            val_files = sorted(mcap_dir.glob("*validation_summary*.json"))
            if val_files:
                default_validation = val_files[-1]
            tl_files = sorted(mcap_dir.glob("*step_timeline*.json"))
            if tl_files:
                default_timeline = tl_files[-1]

    prompt_catalog = "请输入 source_topic_catalog.json 路径"
    if default_catalog is not None:
        prompt_catalog += f" [默认: {default_catalog}]"
    prompt_catalog += ": "
    selected_catalog = input(prompt_catalog).strip()
    if selected_catalog:
        catalog_path = Path(selected_catalog)
    elif default_catalog is not None:
        catalog_path = default_catalog
    else:
        print("未找到 source_topic_catalog.json 小样本，请输入有效路径后重试。")
        return 1

    prompt_val = "请输入 mcap_a_input_validation_summary.json 路径"
    if default_validation is not None:
        prompt_val += f" [默认: {default_validation}]"
    prompt_val += ": "
    selected_val = input(prompt_val).strip()
    if selected_val:
        validation_path = Path(selected_val)
    elif default_validation is not None:
        validation_path = default_validation
    else:
        validation_path = catalog_path.parent / "mcap_a_input_validation_summary.json"

    prompt_tl = "请输入 step_timeline.json 路径"
    if default_timeline is not None:
        prompt_tl += f" [默认: {default_timeline}]"
    prompt_tl += ": "
    selected_tl = input(prompt_tl).strip()
    if selected_tl:
        timeline_path = Path(selected_tl)
    elif default_timeline is not None:
        timeline_path = default_timeline
    else:
        timeline_path = catalog_path.parent / "step_timeline.json"

    config = Scene3AlignmentConfig()

    hz_input = input(f"请输入 target_step_hz [默认: {config.target_step_hz}]: ").strip()
    if hz_input:
        try:
            config.target_step_hz = int(hz_input)
        except ValueError:
            print(f"无效频率: {hz_input}，使用默认 {config.target_step_hz}")

    result = run_scene3_field_alignment_check(
        catalog_path=catalog_path,
        validation_summary_path=validation_path,
        timeline_path=timeline_path,
        config=config,
        field_samples={},
        run_root=Path(args.run_root),
    )

    status_text = "完成" if result["status"] == "success" else "失败"
    print(f"场景三字段对齐检验{status_text}")
    print(f"  run_dir: {result['outputs']['run_dir']}")
    if result["outputs"].get("field_alignment_results_json"):
        print(f"  field_alignment_results: {result['outputs']['field_alignment_results_json']}")
    print(f"  run_log: {result['run_log_path']}")

    sc = result.get("status_counts", {})
    if sc:
        print(f"  字段对齐状态计数: {sc}")
    if result.get("field_count") is not None:
        print(f"  目标字段数: {result['field_count']}")

    if result.get("failure_reasons"):
        print(f"  失败原因: {', '.join(result['failure_reasons'])}")

    return 0 if result["status"] == "success" else 1


def run_scene3_alignment_report_check_check(args: argparse.Namespace) -> int:
    """Interactive runner for scene3_alignment_report_check developer entry."""
    import json

    from schemas.alignment_config import Scene3AlignmentConfig

    default_results = None
    default_catalog = None
    default_validation = None
    default_timeline = None
    if args.cleaned_mcap_dir:
        mcap_dir = Path(args.cleaned_mcap_dir)
        if mcap_dir.is_dir():
            results_files = sorted(mcap_dir.glob("*alignment_results*.json"))
            if results_files:
                default_results = results_files[-1]
            catalog_files = sorted(mcap_dir.glob("*catalog*.json"))
            if catalog_files:
                default_catalog = catalog_files[-1]
            val_files = sorted(mcap_dir.glob("*validation_summary*.json"))
            if val_files:
                default_validation = val_files[-1]
            tl_files = sorted(mcap_dir.glob("*step_timeline*.json"))
            if tl_files:
                default_timeline = tl_files[-1]

    prompt_results = "请输入 field_alignment_results.json 路径"
    if default_results is not None:
        prompt_results += f" [默认: {default_results}]"
    prompt_results += ": "
    selected_results = input(prompt_results).strip()
    if selected_results:
        results_path = Path(selected_results)
    elif default_results is not None:
        results_path = default_results
    else:
        print("未找到 field_alignment_results.json 小样本，请输入有效路径后重试。")
        return 1

    prompt_catalog = "请输入 source_topic_catalog.json 路径"
    if default_catalog is not None:
        prompt_catalog += f" [默认: {default_catalog}]"
    prompt_catalog += ": "
    selected_catalog = input(prompt_catalog).strip()
    if selected_catalog:
        catalog_path = Path(selected_catalog)
    elif default_catalog is not None:
        catalog_path = default_catalog
    else:
        print("未找到 source_topic_catalog.json 小样本，请输入有效路径后重试。")
        return 1

    prompt_val = "请输入 mcap_a_input_validation_summary.json 路径"
    if default_validation is not None:
        prompt_val += f" [默认: {default_validation}]"
    prompt_val += ": "
    selected_val = input(prompt_val).strip()
    if selected_val:
        validation_path = Path(selected_val)
    elif default_validation is not None:
        validation_path = default_validation
    else:
        validation_path = catalog_path.parent / "mcap_a_input_validation_summary.json"

    prompt_tl = "请输入 step_timeline.json 路径"
    if default_timeline is not None:
        prompt_tl += f" [默认: {default_timeline}]"
    prompt_tl += ": "
    selected_tl = input(prompt_tl).strip()
    if selected_tl:
        timeline_path = Path(selected_tl)
    elif default_timeline is not None:
        timeline_path = default_timeline
    else:
        timeline_path = catalog_path.parent / "step_timeline.json"

    config = Scene3AlignmentConfig()

    hz_input = input(f"请输入 target_step_hz [默认: {config.target_step_hz}]: ").strip()
    if hz_input:
        try:
            config.target_step_hz = int(hz_input)
        except ValueError:
            print(f"无效频率: {hz_input}，使用默认 {config.target_step_hz}")

    result = run_scene3_alignment_report_check(
        field_alignment_results_path=results_path,
        timeline_path=timeline_path,
        catalog_path=catalog_path,
        validation_summary_path=validation_path,
        config=config,
        run_root=Path(args.run_root),
    )

    status_text = "完成" if result["status"] == "success" else "失败"
    print(f"场景三对齐报告检验{status_text}")
    print(f"  run_dir: {result['outputs']['run_dir']}")
    if result["outputs"].get("alignment_index_preview_json"):
        print(f"  alignment_index_preview: {result['outputs']['alignment_index_preview_json']}")
    if result["outputs"].get("alignment_report_draft_json"):
        print(f"  alignment_report_draft: {result['outputs']['alignment_report_draft_json']}")
    print(f"  run_log: {result['run_log_path']}")

    if result.get("record_count") is not None:
        print(f"  index record_count: {result['record_count']}")
    if result.get("report_status"):
        print(f"  report_status: {result['report_status']}")

    return 0 if result["status"] == "success" else 1


def run_scene3_aligned_mcap_write_check_check(args: argparse.Namespace) -> int:
    """Interactive runner for scene3_aligned_mcap_write_check developer entry."""
    from pathlib import Path

    default_mcap = None
    if args.cleaned_mcap_dir:
        mcap_dir = Path(args.cleaned_mcap_dir)
        if mcap_dir.is_dir():
            mcap_files = sorted(mcap_dir.glob("*mcap_a*.mcap"))
            if mcap_files:
                default_mcap = mcap_files[-1]

    prompt_mcap = "请输入 MCAP_A 路径"
    if default_mcap is not None:
        prompt_mcap += f" [默认: {default_mcap}]"
    prompt_mcap += ": "
    selected_mcap = input(prompt_mcap).strip()
    if selected_mcap:
        mcap_a_path = Path(selected_mcap)
    elif default_mcap is not None:
        mcap_a_path = default_mcap
    else:
        print("未找到 MCAP_A 小样本，请输入有效路径后重试。")
        return 1

    default_output = scene3_default_aligned_output_dir(
        "scene3_aligned_mcap_write_check"
    )
    prompt_output = f"请输入调试输出目录 [默认: {default_output}]: "
    selected_output = input(prompt_output).strip()
    if selected_output:
        output_dir = Path(selected_output)
    else:
        output_dir = default_output

    print()
    print(f"MCAP_A: {mcap_a_path}")
    print(f"输出目录: {output_dir}")
    print()

    result = run_scene3_aligned_mcap_write_check(
        source_mcap_path=mcap_a_path,
        output_dir=output_dir,
        run_root=Path(args.run_root),
    )

    status_text = "完成" if result["status"] == "success" else "失败"
    print(f"场景三 aligned MCAP 写出检验{status_text}")
    print(f"  run_dir: {result['outputs'].get('run_dir', 'N/A')}")
    outputs = result.get("outputs", {})
    if outputs.get("aligned_mcap"):
        print(f"  aligned_mcap: {outputs['aligned_mcap']}")
    if outputs.get("alignment_index"):
        print(f"  alignment_index: {outputs['alignment_index']}")
    if outputs.get("alignment_report"):
        print(f"  alignment_report: {outputs['alignment_report']}")
    if outputs.get("write_summary"):
        print(f"  write_summary: {outputs['write_summary']}")
    print(f"  run_log: {result.get('run_log_path', 'N/A')}")

    summary = result.get("summary", {})
    if summary:
        print(f"  write_status: {summary.get('status', 'N/A')}")
        if summary.get("failure_reason"):
            print(f"  failure_reason: {summary['failure_reason']}")

    if outputs.get("aligned_mcap") or outputs.get("alignment_index"):
        print()
        print("  已写出 aligned MCAP 相关产物，请检查上述产物完整性。")

    return 0 if result["status"] == "success" else 1


def run_scene3_full_flow_check_check(args: argparse.Namespace) -> int:
    """Interactive runner for the Scene 3 full-flow developer entry."""
    from schemas.alignment_config import Scene3AlignmentConfig

    default_mcap_a = None
    if args.cleaned_mcap_dir:
        mcap_dir = Path(args.cleaned_mcap_dir)
        if mcap_dir.is_dir():
            mcap_files = sorted(mcap_dir.glob("*mcap_a*.mcap"))
            if mcap_files:
                default_mcap_a = mcap_files[-1]

    prompt_mcap = "请输入 MCAP_A 路径"
    if default_mcap_a is not None:
        prompt_mcap += f" [默认: {default_mcap_a}]"
    prompt_mcap += ": "
    selected_mcap = input(prompt_mcap).strip()
    if selected_mcap:
        mcap_a_path = Path(selected_mcap)
    elif default_mcap_a is not None:
        mcap_a_path = default_mcap_a
    else:
        print("未找到 MCAP_A 小样本，请输入有效路径后重试。")
        return 1

    default_summary = mcap_a_path.parent / "mcap_a_write_summary.json"
    prompt_summary = f"请输入 mcap_a_write_summary.json 路径 [默认: {default_summary}]: "
    selected_summary = input(prompt_summary).strip()
    if selected_summary:
        summary_path = Path(selected_summary)
    else:
        summary_path = default_summary

    default_output = scene3_default_aligned_output_dir("scene3_full_flow_check")
    prompt_output = f"请输入 aligned 输出目录 [默认: {default_output}]: "
    selected_output = input(prompt_output).strip()
    if selected_output:
        output_dir = Path(selected_output)
    else:
        output_dir = default_output

    config = Scene3AlignmentConfig()
    hz_input = input(f"请输入 target_step_hz [默认: {config.target_step_hz}]: ").strip()
    if hz_input:
        try:
            config.target_step_hz = int(hz_input)
        except ValueError:
            print(f"无效频率: {hz_input}，使用默认 {config.target_step_hz}")

    print()
    print("开始运行场景三全流程验证 ...")
    print(f"  MCAP_A: {mcap_a_path}")
    print(f"  summary: {summary_path}")
    print(f"  aligned 输出目录: {output_dir}")
    print()

    result = run_scene3_full_flow_check(
        mcap_a_path=mcap_a_path,
        summary_path=summary_path,
        output_dir=output_dir,
        config=config,
        run_root=Path(args.run_root),
    )

    status_text = "完成" if result["status"] == "success" else "失败"
    print(f"场景三全流程验证{status_text}")
    print(f"  run_dir: {result['outputs']['run_dir']}")
    for stage_id, stage_status in result.get("stage_statuses", {}).items():
        stage_run_dir = result["outputs"].get("stage_run_dirs", {}).get(stage_id)
        print(f"  {stage_id}: {stage_status} ({stage_run_dir})")
    outputs = result.get("outputs", {})
    if outputs.get("aligned_mcap"):
        print(f"  aligned_mcap: {outputs['aligned_mcap']}")
    if outputs.get("alignment_index"):
        print(f"  alignment_index: {outputs['alignment_index']}")
    if outputs.get("alignment_report"):
        print(f"  alignment_report: {outputs['alignment_report']}")
    print(f"  run_log: {result['run_log_path']}")

    if result.get("errors"):
        for error in result["errors"]:
            print(f"  error: {error.get('type')}: {error.get('message')}")

    return 0 if result["status"] == "success" else 1


SCENE3_CHECKS: list[tuple[str, str, MenuRunner]] = [
    ("scene3_mcap_a_input_check", "检查 MCAP_A 输入是否可消费", run_scene3_mcap_a_input_check_check),
    ("scene3_step_timeline_check", "检查 Step 时间轴生成", run_scene3_step_timeline_check_check),
    ("scene3_field_alignment_check", "检查多策略字段对齐", run_scene3_field_alignment_check_check),
    ("scene3_alignment_report_check", "检查对齐索引与报告生成", run_scene3_alignment_report_check_check),
    ("scene3_aligned_mcap_write_check", "检查 aligned MCAP 与 sidecar 写出", run_scene3_aligned_mcap_write_check_check),
    ("scene3_full_flow_check", "全流程验证：顺序运行场景三全部功能", run_scene3_full_flow_check_check),
]

SCENE_MENUS: list[tuple[str, str, list[tuple[str, str, MenuRunner]]]] = [
    ("scene1", "场景一：提取夹爪开合以及位姿转换", SCENE1_CHECKS),
    ("scene2", "场景二：硬件数据可靠性验证", SCENE2_CHECKS),
    ("scene3", "场景三：MCAP 多 topic 时间轴对齐", SCENE3_CHECKS),
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
