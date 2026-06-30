#!/usr/bin/env python3
"""Start only the left/right GoPro ROS nodes for live calibration."""

from __future__ import annotations

import argparse
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import yaml


WORKSPACE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = WORKSPACE_DIR / "config/all_sensor_nodes.yaml"
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))


def _as_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("1", "true", "yes", "on")
    return bool(value)


def _require(mapping: dict[str, Any], key: str, label: str) -> Any:
    if key not in mapping:
        raise RuntimeError(f"{label} 缺少 {key}")
    return mapping[key]


def _topic_setting(topics: dict[str, Any], key: str, default_name: str, default_enabled: bool) -> tuple[str, bool]:
    raw = topics.get(key, {})
    if isinstance(raw, dict):
        return str(raw.get("name", default_name)), bool(raw.get("enabled", default_enabled))
    return default_name, default_enabled


def _identity_ref_parts(value: Any) -> tuple[str, str] | None:
    text = str(value or "")
    if not text.startswith("identity:"):
        return None
    ref = text.split(":", 1)[1]
    parts = ref.split(".", 1)
    if len(parts) != 2 or not parts[0] or not parts[1]:
        raise RuntimeError(f"非法硬件身份引用: {text}")
    return parts[0], parts[1]


def _resolve_path(path: Any, base: Path) -> Path:
    resolved = Path(str(path)).expanduser()
    if not resolved.is_absolute():
        resolved = base / resolved
    return resolved


def _load_identity_map(data: dict[str, Any], config_path: Path) -> dict[str, Any]:
    identity_cfg = data.get("hardware_identity") or {}
    if not _as_bool(identity_cfg.get("enabled"), True):
        return {}
    map_file = identity_cfg.get("map_file") or (WORKSPACE_DIR / "config/hardware_identity_map.yaml")
    map_path = _resolve_path(map_file, config_path.parent)
    if not map_path.exists():
        raise RuntimeError(f"硬件身份映射文件不存在: {map_path}")
    with map_path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def _resolve_gopro_identity(value: Any, identity_map: dict[str, Any]) -> str:
    parts = _identity_ref_parts(value)
    if parts is None:
        return str(value)
    group, logical_name = parts
    if group != "gopro":
        raise RuntimeError(f"GoPro video_device 只能引用 gopro 身份，当前为 {value}")

    from hardware_identity_scan import collect_devices, device_matches, preferred_path

    entry = (identity_map.get("gopro") or {}).get(logical_name)
    if not isinstance(entry, dict):
        raise RuntimeError(f"hardware_identity_map.yaml 缺少 gopro.{logical_name}")
    match = entry.get("match") or {}
    if not match:
        raise RuntimeError(f"hardware_identity_map.yaml 中 gopro.{logical_name} 缺少 match")

    candidates = []
    for device in collect_devices().get("video", []):
        if _as_bool(entry.get("require_video_capture"), True) and device.get("video_capture") is False:
            continue
        if device_matches(device, match):
            candidates.append(device)
    if not candidates:
        raise RuntimeError(f"{value} 未解析到当前 GoPro 视频设备")
    if len(candidates) > 1:
        paths = ", ".join(device["path"] for device in candidates)
        raise RuntimeError(f"{value} 匹配到多个视频设备: {paths}")
    return preferred_path(candidates[0], match)


def _load_gopro_config(path: Path, sides: list[str]) -> dict[str, dict[str, Any]]:
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    if not isinstance(data, dict):
        raise RuntimeError("all_sensor_nodes.yaml 顶层必须是 mapping")
    identity_map = _load_identity_map(data, path)
    gopro = data.get("gopro", {})
    if not isinstance(gopro, dict):
        raise RuntimeError("all_sensor_nodes.yaml 缺少 gopro 配置")
    result: dict[str, dict[str, Any]] = {}
    for side in sides:
        cfg = gopro.get(side, {})
        if isinstance(cfg, dict) and bool(cfg.get("enabled", True)):
            cfg = dict(cfg)
            cfg["video_device"] = _resolve_gopro_identity(
                _require(cfg, "video_device", f"gopro.{side}"),
                identity_map,
            )
            result[side] = cfg
    if not result:
        raise RuntimeError("没有启用的 GoPro 配置")
    return result


def _build_command(side: str, cfg: dict[str, Any]) -> list[str]:
    topics = cfg.get("topics") or {}
    image_raw_topic, publish_image_raw = _topic_setting(topics, "image_raw", "image_raw", True)
    if not publish_image_raw:
        raise RuntimeError(f"gopro.{side}.topics.image_raw 未启用")
    camera_info_topic, publish_camera_info = _topic_setting(topics, "camera_info", "camera_info", False)
    return [
        "ros2",
        "launch",
        "gopro_camera_launch",
        "gopro_pose_record.launch.py",
        f"video_device:={_require(cfg, 'video_device', f'gopro.{side}')}",
        f"publish_camera_info:={str(publish_camera_info).lower()}",
        f"camera_namespace:={cfg.get('namespace', f'gopro_{side}')}",
        f"node_name:={cfg.get('node_name', f'gopro_{side}_camera')}",
        f"camera_name:={cfg.get('camera_name', f'gopro_{side}')}",
        f"frame_id:={cfg.get('frame_id', f'gopro_{side}_optical_frame')}",
        f"frame_rate:={cfg.get('frame_rate', 30)}",
        f"pixel_format:={cfg.get('pixel_format', 'YUYV')}",
        f"output_encoding:={cfg.get('output_encoding', 'rgb8')}",
        f"image_raw_topic:={image_raw_topic}",
        f"camera_info_topic:={camera_info_topic}",
    ]


def _terminate(processes: list[subprocess.Popen[str]]) -> None:
    for process in processes:
        if process.poll() is None:
            process.terminate()
    deadline = time.monotonic() + 8
    while time.monotonic() < deadline and any(process.poll() is None for process in processes):
        time.sleep(0.2)
    for process in processes:
        if process.poll() is None:
            process.kill()
    for process in processes:
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            pass


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="只启动左右 GoPro ROS 节点。")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG), help="all_sensor_nodes.yaml 路径。")
    parser.add_argument(
        "--sides",
        nargs="+",
        choices=("left", "right"),
        default=["right", "left"],
        help="要启动的 GoPro 侧别，默认 right left。",
    )
    args = parser.parse_args(argv)

    config_path = Path(args.config).expanduser()
    gopro_config = _load_gopro_config(config_path, args.sides)
    processes: list[subprocess.Popen[str]] = []

    def handle_signal(_signum: int, _frame: Any) -> None:
        _terminate(processes)
        raise SystemExit(130)

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    try:
        for side, cfg in gopro_config.items():
            command = _build_command(side, cfg)
            print(f"启动 GoPro {side}: {' '.join(command)}", flush=True)
            processes.append(subprocess.Popen(command, text=True))
        print("GoPro-only 节点已启动。按 Ctrl+C 停止。", flush=True)
        while True:
            for process in processes:
                code = process.poll()
                if code is not None:
                    _terminate(processes)
                    print(f"GoPro 子进程退出，返回码 {code}", file=sys.stderr)
                    return code or 1
            time.sleep(1)
    except KeyboardInterrupt:
        _terminate(processes)
        return 130
    except Exception as exc:  # noqa: BLE001 - user-facing startup script.
        _terminate(processes)
        print(f"启动 GoPro-only 失败: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
