"""Batch runner for FastUMI-style MCAP cleaning jobs."""

from __future__ import annotations

import argparse
import json
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Iterable

from repo.config.mcap_process_config import AppConfig, load_app_config
from service.validator import FileProcessingReport


def _iter_input_files(config: AppConfig) -> list[Path]:
    input_dir = Path(config.batch.input_dir)
    return sorted(path for path in input_dir.glob(config.batch.file_glob) if path.is_file())


def _build_output_path(input_path: Path, config: AppConfig) -> Path:
    return Path(config.batch.output_dir) / input_path.name


def _process_single_file(args: tuple[str, str, AppConfig]) -> FileProcessingReport:
    from service.mcap_io import process_mcap_file

    input_file, output_file, config = args
    return process_mcap_file(input_file, output_file, config)


def _should_skip_output(output_path: Path, config: AppConfig) -> bool:
    return output_path.exists() and not config.batch.overwrite


def run_batch(config: AppConfig) -> list[FileProcessingReport]:
    reports: list[FileProcessingReport] = []
    input_files = _iter_input_files(config)
    if not input_files:
        return reports

    work_items: list[tuple[str, str, AppConfig]] = []
    for input_path in input_files:
        output_path = _build_output_path(input_path, config)
        if _should_skip_output(output_path, config):
            reports.append(
                FileProcessingReport(
                    input_file=str(input_path),
                    output_file=str(output_path),
                    status="skipped",
                    input_topic_count=0,
                    output_topic_count=0,
                    pose_topics=tuple(),
                    gripper_topics=tuple(),
                    failure_reason=None,
                )
            )
            continue
        work_items.append((str(input_path), str(output_path), config))

    if not work_items:
        return reports

    if config.batch.workers == 1:
        for item in work_items:
            report = _process_single_file(item)
            reports.append(report)
            if report.status == "failed" and config.batch.fail_fast:
                break
        return reports

    with ProcessPoolExecutor(max_workers=config.batch.workers) as executor:
        future_map = {executor.submit(_process_single_file, item): item for item in work_items}
        for future in as_completed(future_map):
            report = future.result()
            reports.append(report)
            if report.status == "failed" and config.batch.fail_fast:
                executor.shutdown(cancel_futures=True)
                break
    return sorted(reports, key=lambda report: report.input_file)


def _print_reports(reports: Iterable[FileProcessingReport]) -> None:
    for report in reports:
        print(json.dumps(report.to_dict(), ensure_ascii=False))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Batch-clean ROS2 MCAP files into common-frame camera/gripper format.")
    parser.add_argument("--config", required=True, help="Path to the YAML configuration file.")
    parser.add_argument("--input-dir", help="Override batch.input_dir from the config.")
    parser.add_argument("--output-dir", help="Override batch.output_dir from the config.")
    parser.add_argument("--workers", type=int, help="Override batch.workers from the config.")
    args = parser.parse_args(argv)

    config = load_app_config(
        args.config,
        input_dir_override=args.input_dir,
        output_dir_override=args.output_dir,
        workers_override=args.workers,
    )
    reports = run_batch(config)
    _print_reports(reports)

    failed = [report for report in reports if report.status == "failed"]
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
