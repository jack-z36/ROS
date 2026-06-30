#!/usr/bin/env python3
"""
自动扫描当前视频设备并更新 config/all_sensor_nodes.yaml 中的 GoPro 摄像头路径。

当 USB 拓扑变化、系统重启或摄像头重连后 GoPro 的 by-path 链接可能改变，
运行此脚本可自动检测并更新配置。

用法:
  python3 scripts/update_sensor_paths.py          # 仅扫描并打印建议
  python3 scripts/update_sensor_paths.py --write  # 扫描并直接写入 config 文件

也可配合硬件身份扫描使用:
  python3 scripts/hardware_identity_scan.py scan  # 查看所有硬件信息
"""

import argparse
import os
import re
import subprocess
import sys
from glob import glob
from pathlib import Path

import yaml

WORKSPACE_DIR = Path(__file__).resolve().parents[1]
CONFIG_FILE = WORKSPACE_DIR / "config" / "all_sensor_nodes.yaml"


def run(cmd, timeout=5):
    try:
        proc = subprocess.run(
            cmd,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
        return proc.stdout.strip() + proc.stderr.strip()
    except subprocess.TimeoutExpired:
        return ""


def get_v4l_by_path_devices():
    """Scan /dev/v4l/by-path/ and return list of (link_name, real_dev)."""
    by_path_dir = Path("/dev/v4l/by-path")
    if not by_path_dir.is_dir():
        return []
    devices = []
    for entry in sorted(by_path_dir.iterdir()):
        if entry.is_symlink():
            real_path = entry.resolve()
            devices.append({
                "link": str(entry),
                "link_name": entry.name,
                "dev": str(real_path),
            })
    return devices


def get_device_info(dev):
    """Get udev properties for a video device."""
    proc = subprocess.run(
        ["udevadm", "info", "-q", "property", "-n", dev],
        text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=3, check=False,
    )
    props = {}
    for line in proc.stdout.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            props[key] = value
    return props


def is_capture_device(dev):
    """Check if device is a Video Capture device."""
    props = get_device_info(dev)
    capabilities = props.get("ID_V4L_CAPABILITIES", "")
    if ":capture:" in capabilities:
        return True
    # fallback: try v4l2-ctl
    output = run(["v4l2-ctl", "-d", dev, "--all"])
    if "Format Video Capture:" in output or "Video Capture" in output:
        return True
    return False


def get_card_type(dev):
    """Get card type name from v4l2-ctl --info."""
    output = run(["v4l2-ctl", "-d", dev, "--info"])
    for line in output.splitlines():
        if "Card type" in line:
            return line.split(":", 1)[1].strip()
    return ""


def scan_gopro_cameras():
    """Scan and identify all GoPro (VID 0bda) capture cameras."""
    cameras = []
    for dev_info in get_v4l_by_path_devices():
        props = get_device_info(dev_info["dev"])
        vid = props.get("ID_VENDOR_ID", "")
        if vid != "0bda":  # GoPro USB Camera VID
            continue
        if not is_capture_device(dev_info["dev"]):
            continue
        card_type = get_card_type(dev_info["dev"])
        camera = {
            "by_path": dev_info["link"],
            "dev": dev_info["dev"],
            "card_type": card_type,
            "serial": props.get("ID_SERIAL_SHORT", ""),
        }
        # Prefer the -index0 (capture) link, skip -index1 (metadata)
        if dev_info["link_name"].endswith("-index0"):
            cameras.append(camera)
    return cameras


def load_config(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def write_config(path, config):
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(config, f, sort_keys=False, allow_unicode=True)
    print(f"已写入: {path}")


def main():
    parser = argparse.ArgumentParser(
        description="自动更新传感器设备路径 (GoPro 摄像头)"
    )
    parser.add_argument("--write", action="store_true",
                        help="将检测到的路径写入 config 文件")
    parser.add_argument("--config", default=str(CONFIG_FILE),
                        help=f"config 文件路径 (默认: {CONFIG_FILE})")
    args = parser.parse_args()

    print("=" * 60)
    print("扫描 GoPro 摄像头设备...")
    print("=" * 60)

    cameras = scan_gopro_cameras()
    if not cameras:
        print("未检测到 GoPro 摄像头 (VID=0bda)")
        sys.exit(1)

    print(f"\n发现 {len(cameras)} 个 GoPro 摄像头:\n")
    for i, cam in enumerate(cameras):
        print(f"  [{i}] {cam['by_path']}")
        print(f"       -> {cam['dev']}")
        print(f"       Card: {cam['card_type']}")

    if len(cameras) < 2:
        print("\n⚠ 只发现 1 个 GoPro，预期是 2 个。请检查摄像头连接。")
        # Still continue if --write, might be partial

    # Load current config
    config = load_config(args.config)
    gopro_config = config.get("gopro", {})

    print("\n" + "=" * 60)
    print("当前配置 vs 实际设备")
    print("=" * 60)

    # Match cameras to right/left by Card type or by user selection
    suggestions = {}
    for side in ("right", "left"):
        current_path = gopro_config.get(side, {}).get("video_device", "")
        print(f"\nGoPro {side}:")
        print(f"  当前配置: {current_path}")
        if current_path and Path(current_path).exists():
            print(f"  状态: ✅ 存在")
            suggestions[side] = current_path
        else:
            print(f"  状态: ❌ 不存在")

    need_update = False
    for side in ("right", "left"):
        current_path = gopro_config.get(side, {}).get("video_device", "")
        if not current_path or not Path(current_path).exists():
            need_update = True
            break

    if not need_update:
        print("\n✅ 所有 GoPro 路径当前都有效，无需更新。")
        return

    # If both old paths are dead, try to match by USB topology naming
    print("\n需要更新设备路径。尝试自动匹配...")

    # Strategy: try to match right to Camera3 and left to Camera2
    # based on the USB controller (0d.0 is right, 14.0 is left)
    for cam in cameras:
        cam["assigned_side"] = "unknown"
        link = cam["by_path"]
        if "00:0d.0" in link:
            cam["assigned_side"] = "right"
        elif "00:14.0" in link:
            cam["assigned_side"] = "left"

    right_cams = [c for c in cameras if c["assigned_side"] == "right"]
    left_cams = [c for c in cameras if c["assigned_side"] == "left"]

    print()
    for side, side_cams in [("right", right_cams), ("left", left_cams)]:
        if side_cams:
            print(f"  GoPro {side} -> {side_cams[0]['by_path']}")
        else:
            print(f"  GoPro {side} -> 未找到匹配")

    if not right_cams or not left_cams:
        print("\n⚠ 无法自动匹配左右。用户需手动判断：")
        for i, cam in enumerate(cameras):
            print(f"  [{i}] {cam['by_path']} ({cam['card_type']})")
        print()

        # Try by-id if it helps
        by_id_dir = Path("/dev/v4l/by-id")
        if by_id_dir.is_dir():
            print("/dev/v4l/by-id/ 中的 GoPro 设备:")
            for entry in sorted(by_id_dir.iterdir()):
                if "Camera2" in entry.name or "Camera3" in entry.name:
                    real = entry.resolve()
                    for cam in cameras:
                        if cam["dev"] == str(real):
                            print(f"  {entry.name} -> {cam['by_path']} ({cam['card_type']})")

        print("\n使用 --write 前请先手动修正。")
        return

    if args.write:
        for side in ("right", "left"):
            side_cams = right_cams if side == "right" else left_cams
            if side_cams:
                old = config["gopro"][side]["video_device"]
                new = side_cams[0]["by_path"]
                config["gopro"][side]["video_device"] = new
                print(f"  GoPro {side}: {old} -> {new}")

        write_config(args.config, config)
        print("\n✅ 配置已更新。运行以下命令验证:")
        print(f"  python3 scripts/all_sensor_status.py preflight --config {args.config} --identity-map config/hardware_identity_map.yaml")
    else:
        print("\n预览修改 (添加 --write 以生效):")
        for side in ("right", "left"):
            side_cams = right_cams if side == "right" else left_cams
            if side_cams:
                old = config["gopro"][side]["video_device"]
                new = side_cams[0]["by_path"]
                print(f"  GoPro {side}:")
                print(f"    {old}")
                print(f"    -> {new}")
        print(f"\n运行: python3 {__file__} --write  来写入配置")


if __name__ == "__main__":
    main()
