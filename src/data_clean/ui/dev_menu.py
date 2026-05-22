"""Developer interactive menu for data clean pipeline."""

from __future__ import annotations

import sys
from pathlib import Path

DATA_CLEAN_SOURCE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(DATA_CLEAN_SOURCE))

from ui.scene1_dev_checks import (  # noqa: E402
    run_scene1_frame_alignment_config,
    save_frame_alignment_to_production,
)

SCENE1_CHECKS = [
    ("scene1_frame_alignment_config", "位姿转换 frame_alignment 配置生成"),
]


def _scene1_menu() -> None:
    print()
    print("场景一：提取夹爪开合以及位姿转换")
    print("  功能检验项:")
    for idx, (check_id, label) in enumerate(SCENE1_CHECKS, 1):
        print(f"    {idx}  {label} ({check_id})")
    print("    q  返回")
    print()

    while True:
        choice = input("选择检验项: ").strip().lower()
        if choice in {"q", "quit", "exit"}:
            return
        if choice == "1":
            _run_frame_alignment_check()
            return
        print("无效选择，请重试。")


def _run_frame_alignment_check() -> None:
    print()
    print("运行 scene1_frame_alignment_config ...")
    print()
    print("提示: 此检验项生成 frame_alignment 配置模板。")
    print("如需从右手 Baton Mini 标定采样生成 common_from_right_start，")
    print("请使用实时标定中心: ./start_data_clean.sh --calibrate")
    print()

    answer = input("继续生成默认配置？[Y/n]: ").strip().lower()
    if answer in {"n", "no"}:
        print("已取消。")
        return

    try:
        dev_run = run_scene1_frame_alignment_config()
    except Exception as exc:
        print(f"配置生成失败: {exc}")
        return

    print()
    save_answer = input("是否保存到正式配置？[y/N]: ").strip().lower()
    if save_answer in {"y", "yes"}:
        try:
            save_frame_alignment_to_production(dev_run)
        except Exception as exc:
            print(f"保存失败: {exc}")
    else:
        print("保留临时配置，未写入正式配置。")


def main() -> None:
    print("数据清洗开发者功能检验菜单")
    print()
    print("  1  场景一：提取夹爪开合以及位姿转换")
    print("  q  退出")
    print()

    while True:
        choice = input("选择场景: ").strip().lower()
        if choice in {"q", "quit", "exit"}:
            print("已退出。")
            return
        if choice == "1":
            _scene1_menu()
            print()
        else:
            print("无效选择，请重试。")
        print()
        print("  1  场景一：提取夹爪开合以及位姿转换")
        print("  q  退出")
        print()


if __name__ == "__main__":
    main()
