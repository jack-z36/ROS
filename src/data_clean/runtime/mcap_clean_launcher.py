"""Interactive launcher for the MCAP cleaning pipeline."""

from __future__ import annotations

import argparse
import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from mcap.reader import make_reader

from repo.config.mcap_process_config import AppConfig, calibration_missing_items, config_is_calibrated, load_app_config
from service.mcap_io import process_mcap_file
from service.validator import FileProcessingReport, build_topic_inventory, validate_input_inventory


DEFAULT_WORKERS = 6
WORKSPACE_DIR = Path("/home/hit/ROS")
SMOKE_CONFIG = WORKSPACE_DIR / "config/data_clean/data_clean_smoke_test.yaml"
CALIBRATED_CONFIG = WORKSPACE_DIR / "config/data_clean/data_clean_calibrated.yaml"


@dataclass(frozen=True)
class SelectedFile:
    input_path: Path
    output_path: Path
    existed_before: bool
    previous_size: int | None
    previous_mtime_ns: int | None


class CleaningInterrupted(KeyboardInterrupt):
    def __init__(self, reports: list[FileProcessingReport]):
        super().__init__()
        self.reports = reports


def _short_path(path: str | Path) -> str:
    try:
        return os.path.relpath(str(path), str(WORKSPACE_DIR))
    except ValueError:
        return str(path)


def _format_size(size: int) -> str:
    units = ("B", "KiB", "MiB", "GiB", "TiB")
    value = float(size)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            if unit == "B":
                return f"{int(value)} {unit}"
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{size} B"


def _iter_input_files(config: AppConfig) -> list[Path]:
    input_dir = Path(config.batch.input_dir)
    return sorted(
        (path for path in input_dir.glob(config.batch.file_glob) if path.is_file()),
        key=lambda path: path.name,
        reverse=True,
    )


def _print_no_input_files_message(config: AppConfig) -> None:
    input_dir = Path(config.batch.input_dir)
    output_dir = Path(config.batch.output_dir)
    print("没有找到需要处理的 MCAP 文件。")
    print(f"  输入目录: {_short_path(input_dir)}")
    print(f"  匹配规则: {config.batch.file_glob}")
    if not input_dir.exists():
        print("  原因判断: 输入目录不存在。")
    elif not input_dir.is_dir():
        print("  原因判断: 输入路径存在，但不是目录。")
    else:
        print("  原因判断: 输入目录存在，但没有匹配到文件。")
    print(f"  输出目录: {_short_path(output_dir)}")
    print("  建议: 请确认原始 MCAP 是否放在 /home/hit/ROS/mcap，或使用 --input-dir 指定真实目录。")


def _output_path(input_path: Path, config: AppConfig) -> Path:
    return Path(config.batch.output_dir) / input_path.name


def _select_latest(files: list[Path], count: int) -> list[Path]:
    if count < 1:
        raise ValueError("清洗数量必须 >= 1")
    return files[: min(count, len(files))]


def _build_selection(paths: Iterable[Path], config: AppConfig) -> list[SelectedFile]:
    selection: list[SelectedFile] = []
    for input_path in paths:
        output_path = _output_path(input_path, config)
        if output_path.exists():
            stat = output_path.stat()
            selection.append(
                SelectedFile(
                    input_path=input_path,
                    output_path=output_path,
                    existed_before=True,
                    previous_size=stat.st_size,
                    previous_mtime_ns=stat.st_mtime_ns,
                )
            )
        else:
            selection.append(
                SelectedFile(
                    input_path=input_path,
                    output_path=output_path,
                    existed_before=False,
                    previous_size=None,
                    previous_mtime_ns=None,
                )
            )
    return selection


def _resolve_workers(value: str | None, selected_count: int) -> int:
    if selected_count < 1:
        return 1
    if value is None or value == "auto":
        return max(1, min(DEFAULT_WORKERS, selected_count))
    try:
        workers = int(value)
    except ValueError as exc:
        raise ValueError("--workers 必须是 auto 或正整数") from exc
    if workers < 1:
        raise ValueError("--workers 必须 >= 1")
    return min(workers, selected_count)


def _prompt_file_selection(files: list[Path], config_path: str) -> list[Path]:
    print("请选择要清洗的 MCAP 文件：")
    print("  [回车] 最近 1 个")
    print("  n      最近 N 个")
    print("  a      全部")
    print("  c      配置/标定向导")
    print("  q      退出")
    choice = input("选择: ").strip().lower()

    if choice == "":
        return _select_latest(files, 1)
    if choice == "a":
        return files
    if choice == "q":
        print("已退出，未执行清洗。")
        raise SystemExit(0)
    if choice == "c":
        from ui.mcap_calibration_wizard import run_calibration_wizard

        raise SystemExit(run_calibration_wizard(config_path))
    if choice == "n":
        raw_count = input("请输入要清洗的最近文件数量 N: ").strip()
        try:
            return _select_latest(files, int(raw_count))
        except ValueError as exc:
            raise SystemExit(f"无效数量: {raw_count}") from exc

    raise SystemExit(f"未知选择: {choice}")


def _choose_files(args: argparse.Namespace, files: list[Path]) -> list[Path]:
    modes = sum(
        1
        for enabled in (
            args.latest is not None,
            args.all_files,
        )
        if enabled
    )
    if modes > 1:
        raise SystemExit("--latest 和 --all 只能选择一个")

    if args.all_files:
        return files
    if args.latest is not None:
        return _select_latest(files, args.latest)
    return _prompt_file_selection(files, args.config)


def _preview_selection(selection: list[SelectedFile], config: AppConfig, workers: int) -> None:
    input_dir = Path(config.batch.input_dir)
    output_dir = Path(config.batch.output_dir)
    print()
    print("清洗计划")
    print(f"  输入目录: {_short_path(input_dir)}")
    print(f"  输出目录: {_short_path(output_dir)}")
    print(f"  文件数量: {len(selection)}")
    print(f"  并行数量: {workers}")
    print(f"  覆盖策略: 直接覆盖同名输出")
    print()
    print("待清洗文件:")
    for index, item in enumerate(selection, start=1):
        size = _format_size(item.input_path.stat().st_size)
        print(f"  {index:>2}. {item.input_path.name}  {size}")
        print(f"      -> {_short_path(item.output_path)}")


def _print_calibration_warning(config: AppConfig) -> None:
    print()
    print("配置提醒")
    if config_is_calibrated(config):
        print("  当前配置标记为完整已标定：左右夹爪和左右 common frame 均已完成。")
    else:
        missing = "、".join(calibration_missing_items(config))
        print("  警告：当前配置未完整标定，可能仍有测试/占位参数。")
        if missing:
            print(f"  未完成分项: {missing}")
        print("  建议先在菜单中选择 c，或运行 ./start_data_clean.sh --calibrate 生成已标定配置。")
    print("  当前清洗会使用 YAML 中的 common frame transform 和 ArUco 夹爪标定参数。")
    for stream in config.pose_streams:
        transform = config.transform_for_pose_stream(stream)
        translation = transform.translation
        rotation = transform.rotation_xyzw
        print(
            "  common frame: "
            f"{stream.input_topic} -> {stream.output_topic}, "
            f"start_from_common.xyz=({translation.x}, {translation.y}, {translation.z}), "
            f"q=({rotation.qx}, {rotation.qy}, {rotation.qz}, {rotation.qw})"
        )
    for stream in config.gripper_streams:
        print(
            "  ArUco: "
            f"{stream.image_topic} -> {stream.output_topic}, "
            f"ids=({stream.marker_id_0}, {stream.marker_id_1}), "
            f"range=({stream.marker_min}, {stream.marker_max}), "
            f"gripper_max={stream.gripper_max}"
        )


def _confirm_or_exit() -> None:
    answer = input("确认开始清洗？[Y/n]: ").strip().lower()
    if answer not in ("", "y", "yes"):
        print("已取消，未执行清洗。")
        raise SystemExit(0)


def _validate_first_mcap(config: AppConfig, selection: list[SelectedFile], quiet: bool = False) -> None:
    if not selection:
        return
    first = selection[0].input_path
    if not quiet:
        print()
        print(f"检查首个 MCAP topic: {_short_path(first)}")
        sys.stdout.flush()
    with first.open("rb") as fh:
        summary = make_reader(fh).get_summary()
        inventory = build_topic_inventory(summary)
        validate_input_inventory(config, inventory)
    if not quiet:
        print("  topic 检查通过")


def _safe_delete_output(item: SelectedFile) -> None:
    path = item.output_path
    if not path.exists():
        return
    if item.existed_before:
        stat = path.stat()
        unchanged = stat.st_size == item.previous_size and stat.st_mtime_ns == item.previous_mtime_ns
        if unchanged:
            return
    path.unlink()


def _report_to_json(report: FileProcessingReport) -> str:
    return json.dumps(report.to_dict(), ensure_ascii=False)


def _print_report_summary(index: int, report: FileProcessingReport) -> None:
    input_file = _short_path(report.input_file)
    output_file = _short_path(report.output_file)
    if report.status == "success":
        print(f"[{index}] 成功: {input_file}")
        print(f"    输出: {output_file}")
        print(f"    topic: 输入 {report.input_topic_count} 个 -> 输出 {report.output_topic_count} 个")
        if report.pose_topics:
            print("    位姿:")
            for pose in report.pose_topics:
                print(f"      - {pose.topic}: {pose.input_count} -> {pose.output_count} 条")
        if report.gripper_topics:
            print("    夹爪宽度:")
            for gripper in report.gripper_topics:
                print(
                    f"      - {gripper.output_topic}: {gripper.gripper_count} 条 "
                    f"(图像帧 {gripper.frame_count}, 插值 {gripper.interpolated_frames})"
                )
    elif report.status == "skipped":
        print(f"[{index}] 跳过: {input_file}")
        print(f"    已存在输出: {output_file}")
    else:
        print(f"[{index}] 失败: {input_file}")
        print(f"    目标输出: {output_file}")
        print(f"    原因: {report.failure_reason or '未提供失败原因'}")
    print()


def _print_progress(done: int, total: int, success: int, failed: int, current: str) -> None:
    message = f"进度 {done}/{total} | 成功 {success} | 失败 {failed} | 当前 {current}"
    print("\r" + message.ljust(100), end="", flush=True)


def _process_one(args: tuple[str, str, AppConfig]) -> FileProcessingReport:
    input_file, output_file, config = args
    try:
        return process_mcap_file(input_file, output_file, config)
    except Exception as exc:  # noqa: BLE001 - convert worker crashes into per-file failures.
        return FileProcessingReport(
            input_file=input_file,
            output_file=output_file,
            status="failed",
            input_topic_count=0,
            output_topic_count=0,
            pose_topics=tuple(),
            gripper_topics=tuple(),
            failure_reason=f"unexpected error: {exc}",
        )


def _run_cleaning(config: AppConfig, selection: list[SelectedFile], workers: int, raw_json: bool) -> list[FileProcessingReport]:
    reports: list[FileProcessingReport] = []
    item_by_input = {str(item.input_path): item for item in selection}
    total = len(selection)
    success = 0
    failed = 0

    if workers == 1:
        try:
            for index, item in enumerate(selection, start=1):
                if not raw_json:
                    _print_progress(index - 1, total, success, failed, item.input_path.name)
                report = _process_one((str(item.input_path), str(item.output_path), config))
                reports.append(report)
                if report.status == "success":
                    success += 1
                elif report.status == "failed":
                    failed += 1
                    _safe_delete_output(item)
                if raw_json:
                    print(_report_to_json(report), flush=True)
                else:
                    _print_progress(index, total, success, failed, item.input_path.name)
                    print()
                    _print_report_summary(index, report)
        except KeyboardInterrupt as exc:
            completed_inputs = {report.input_file for report in reports if report.status == "success"}
            for item in selection:
                if str(item.input_path) not in completed_inputs:
                    _safe_delete_output(item)
            raise CleaningInterrupted(reports) from exc
        return reports

    work_items = [(str(item.input_path), str(item.output_path), config) for item in selection]
    with ProcessPoolExecutor(max_workers=workers) as executor:
        future_map = {executor.submit(_process_one, work_item): work_item for work_item in work_items}
        try:
            for done_count, future in enumerate(as_completed(future_map), start=1):
                input_file, _output_file, _config = future_map[future]
                report = future.result()
                reports.append(report)
                if report.status == "success":
                    success += 1
                elif report.status == "failed":
                    failed += 1
                    item = item_by_input.get(input_file)
                    if item is not None:
                        _safe_delete_output(item)
                if raw_json:
                    print(_report_to_json(report), flush=True)
                else:
                    _print_progress(done_count, total, success, failed, Path(input_file).name)
                    print()
                    _print_report_summary(done_count, report)
        except KeyboardInterrupt as exc:
            executor.shutdown(cancel_futures=True)
            completed_inputs = {report.input_file for report in reports if report.status == "success"}
            for item in selection:
                if str(item.input_path) not in completed_inputs:
                    _safe_delete_output(item)
            raise CleaningInterrupted(reports) from exc

    return sorted(reports, key=lambda report: report.input_file)


def _print_final_summary(reports: list[FileProcessingReport], interrupted: bool = False) -> None:
    total = len(reports)
    success = sum(1 for report in reports if report.status == "success")
    skipped = sum(1 for report in reports if report.status == "skipped")
    failed = sum(1 for report in reports if report.status == "failed")
    if interrupted:
        print("清洗已中断")
    else:
        print("清洗完成")
    print(f"  总计: {total}")
    print(f"  成功: {success}")
    print(f"  跳过: {skipped}")
    print(f"  失败: {failed}")
    if failed:
        print()
        print("失败文件:")
        for report in reports:
            if report.status == "failed":
                print(f"  - {_short_path(report.input_file)}: {report.failure_reason or '未提供失败原因'}")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="交互式 MCAP 数据清洗启动器。")
    default_config = CALIBRATED_CONFIG if CALIBRATED_CONFIG.exists() else SMOKE_CONFIG
    parser.add_argument("--config", default=str(default_config), help="YAML 配置文件。")
    parser.add_argument("--calibrate", action="store_true", help="进入配置/标定向导，生成已标定配置。")
    parser.add_argument("--input-dir", help="覆盖配置中的 batch.input_dir。")
    parser.add_argument("--output-dir", help="覆盖配置中的 batch.output_dir。")
    parser.add_argument("--latest", type=int, help="清洗最近 N 个 MCAP。")
    parser.add_argument("--all", dest="all_files", action="store_true", help="清洗全部匹配的 MCAP。")
    parser.add_argument("--dry-run", action="store_true", help="只预览计划，不执行清洗。")
    parser.add_argument("--workers", default=None, help="并行数量：auto 或正整数。默认 auto，最高 6。")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    raw_json = os.environ.get("DATA_CLEAN_RAW_JSON") == "1"

    config = load_app_config(
        args.config,
        input_dir_override=args.input_dir,
        output_dir_override=args.output_dir,
    )
    if args.calibrate:
        from ui.mcap_calibration_wizard import run_calibration_wizard

        return run_calibration_wizard(args.config)

    files = _iter_input_files(config)
    if not files:
        _print_no_input_files_message(config)
        return 0

    if not raw_json:
        print("数据清洗启动器")
        print(f"  配置文件: {_short_path(args.config)}")
        print(f"  配置状态: {'已标定' if config_is_calibrated(config) else '未完整标定/测试配置'}")
        print(f"  输入目录: {_short_path(config.batch.input_dir)}")
        print(f"  输出目录: {_short_path(config.batch.output_dir)}")
        print(f"  可清洗文件: {len(files)}")
        print("  默认选择: 最近 1 个")
        print()

    selected_paths = _choose_files(args, files)
    selection = _build_selection(selected_paths, config)
    workers = _resolve_workers(args.workers, len(selection))

    if not raw_json:
        _preview_selection(selection, config, workers)
        sys.stdout.flush()
    try:
        _validate_first_mcap(config, selection, quiet=raw_json)
    except Exception as exc:  # noqa: BLE001 - user-facing validation failure.
        print(f"配置检查失败: {exc}", file=sys.stderr)
        return 1
    if not raw_json:
        _print_calibration_warning(config)

    if args.dry_run:
        if not raw_json:
            print()
            print("dry-run 模式：只预览，不执行清洗。")
        return 0

    if args.latest is None and not args.all_files:
        print()
        _confirm_or_exit()

    if not raw_json:
        print()
        print("开始清洗")
    try:
        reports = _run_cleaning(config, selection, workers, raw_json)
    except CleaningInterrupted as exc:
        if not raw_json:
            print()
            _print_final_summary(exc.reports, interrupted=True)
        return 130

    if not raw_json:
        _print_final_summary(reports)
    return 1 if any(report.status == "failed" for report in reports) else 0


if __name__ == "__main__":
    raise SystemExit(main())
