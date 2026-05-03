#!/usr/bin/env python3
import argparse
import copy
import os
import shutil
import socket
import subprocess
import sys
from glob import glob
from pathlib import Path

import yaml


WORKSPACE_DIR = Path(__file__).resolve().parents[1]
HARDWARE_IDENTITY_SCRIPT = WORKSPACE_DIR / "scripts" / "hardware_identity_scan.py"


def run(cmd, timeout=3):
    try:
        return subprocess.run(
            cmd,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return subprocess.CompletedProcess(cmd, 124, exc.stdout or "", exc.stderr or "timeout")


def load_config(path):
    config_path = Path(path).expanduser()
    if not config_path.is_absolute():
        config_path = Path.cwd() / config_path
    with config_path.open("r", encoding="utf-8") as stream:
        return yaml.safe_load(stream) or {}, config_path


def resolve_path(path, base=None):
    resolved = Path(str(path)).expanduser()
    if not resolved.is_absolute():
        resolved = (base or Path.cwd()) / resolved
    return resolved


def as_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("1", "true", "yes", "on")
    return bool(value)


def enabled_items(config, section):
    for side, sensor_config in (config.get(section) or {}).items():
        if as_bool(sensor_config.get("enabled", True)):
            yield side, sensor_config


def topic_setting(topics, key, default_name, default_enabled=True):
    value = (topics or {}).get(key)
    if isinstance(value, dict):
        return (
            value.get("name", value.get("topic", default_name)),
            as_bool(value.get("enabled", default_enabled)),
        )
    if value is None:
        return default_name, as_bool(default_enabled)
    return value, as_bool(default_enabled)


def normalize_topic(name, namespace=""):
    topic = str(name).strip()
    if topic.startswith("/"):
        return topic
    namespace = str(namespace).strip("/")
    if namespace:
        return f"/{namespace}/{topic.strip('/')}"
    return f"/{topic.strip('/')}"


def load_identity_resolved(path):
    if not path:
        return {}
    resolved_path = Path(path).expanduser()
    if not resolved_path.is_absolute():
        resolved_path = Path.cwd() / resolved_path
    if not resolved_path.exists():
        return {}
    with resolved_path.open("r", encoding="utf-8") as stream:
        return yaml.safe_load(stream) or {}


def apply_identity_resolved(config, resolved):
    if not resolved:
        return config
    updated = copy.deepcopy(config)
    for side, resolved_cfg in (resolved.get("gopro") or {}).items():
        device = resolved_cfg.get("device")
        if device and side in (updated.get("gopro") or {}):
            updated["gopro"][side]["video_device"] = device
    return updated


def identity_map_from_config(config, config_base):
    identity_cfg = config.get("hardware_identity") or {}
    if not as_bool(identity_cfg.get("enabled", True)):
        return None
    map_file = identity_cfg.get("map_file")
    if not map_file:
        default_map = config_base / "hardware_identity_map.yaml"
        if default_map.exists():
            return str(default_map)
        workspace_map = WORKSPACE_DIR / "config" / "hardware_identity_map.yaml"
        return str(workspace_map) if workspace_map.exists() else None
    return str(resolve_path(map_file, config_base))


def validate_hardware_identity(identity_map, write_resolved=None):
    if not identity_map:
        return 0
    cmd = [
        sys.executable,
        str(HARDWARE_IDENTITY_SCRIPT),
        "validate",
        "--map",
        str(identity_map),
    ]
    if write_resolved:
        cmd.extend(["--write-resolved", str(write_resolved)])

    print_header("硬件身份映射校验")
    proc = run(cmd, timeout=30)
    if proc.stdout:
        print(proc.stdout.rstrip())
    if proc.stderr:
        print(proc.stderr.rstrip(), file=sys.stderr)
    if proc.returncode != 0:
        print("FAIL 硬件身份映射校验失败，停止启动。")
    return proc.returncode


def configured_pressure_topics(cfg, config_base):
    topics = []
    topics_cfg = cfg.get("topics") or {}
    for key, value in topics_cfg.items():
        default_name = f"/pressure/left_hand/{key}"
        topic_name, publish_topic = topic_setting(topics_cfg, key, default_name, True)
        if publish_topic and topic_name:
            topics.append(normalize_topic(topic_name))

    if topics:
        return topics

    pressure_config_file = cfg.get("config_file")
    if not pressure_config_file:
        return topics

    pressure_config_path = resolve_path(pressure_config_file, config_base)
    try:
        with pressure_config_path.open("r", encoding="utf-8") as stream:
            pressure_config = yaml.safe_load(stream) or {}
    except OSError:
        return topics

    params = (
        pressure_config.get("pressure_driver_node", {})
        .get("ros__parameters", {})
    )
    for port_cfg in params.get("serial_ports") or []:
        for sensor_cfg in port_cfg.get("sensors") or []:
            topic = sensor_cfg.get("topic")
            if topic:
                topics.append(normalize_topic(topic))

    return topics


def expected_sensors(config, config_base=None, identity_resolved=None):
    config_base = config_base or Path.cwd()
    config = apply_identity_resolved(config, identity_resolved)
    sensors = []
    for side, cfg in enabled_items(config, "baton_mini"):
        topics = cfg.get("topics") or {}
        node_name = cfg.get("node_name", f"baton_mini_{side}")
        expected_topics = []
        for key, default_name in (
            ("imu", f"/{node_name}/imu"),
            ("odometry", f"/{node_name}/odometry"),
            ("fast_odom", f"/{node_name}/fast_odom"),
            ("image_left", f"/{node_name}/image_left"),
            ("image_right", f"/{node_name}/image_right"),
        ):
            topic_name, publish_topic = topic_setting(topics, key, default_name, True)
            if publish_topic:
                expected_topics.append(normalize_topic(topic_name))
        sensors.append(
            {
                "id": f"baton_mini.{side}",
                "label": f"Baton Mini {side}",
                "node": f"/{node_name}",
                "topics": expected_topics,
                "preflight": {
                    "local_ip": cfg.get("local_ip"),
                    "server_ip": cfg.get("server_ip"),
                },
            }
        )

    for side, cfg in enabled_items(config, "gopro"):
        namespace = str(cfg.get("namespace", f"gopro_{side}")).strip("/")
        topics_cfg = cfg.get("topics") or {}
        image_raw_topic, publish_image_raw = topic_setting(
            topics_cfg, "image_raw", "image_raw", True
        )
        if not publish_image_raw:
            continue
        camera_info_default = cfg.get("publish_camera_info", False if topics_cfg else True)
        camera_info_topic, publish_camera_info = topic_setting(
            topics_cfg, "camera_info", "camera_info", camera_info_default
        )
        topics = [normalize_topic(image_raw_topic, namespace)]
        if publish_camera_info:
            topics.append(normalize_topic(camera_info_topic, namespace))
        sensors.append(
            {
                "id": f"gopro.{side}",
                "label": f"GoPro {side}",
                "node": f"/{namespace}/{cfg.get('node_name', f'gopro_{side}_camera')}",
                "topics": topics,
                "preflight": {
                    "video_device": cfg.get("video_device"),
                },
            }
        )

    pressure_cfg = config.get("pressure") or {}
    if as_bool(pressure_cfg.get("enabled", False)):
        pressure_config_file = pressure_cfg.get(
            "config_file", "src/hwk_pressure_driver/config/pressure_sensors.yaml"
        )
        sensors.append(
            {
                "id": "pressure",
                "label": "HWK pressure",
                "node": f"/{pressure_cfg.get('node_name', 'pressure_driver_node')}",
                "topics": configured_pressure_topics(pressure_cfg, config_base),
                "preflight": {
                    "pressure_config_file": str(resolve_path(pressure_config_file, config_base)),
                },
            }
        )

    return sensors


def print_header(title):
    print(f"\n=== {title} ===")


def ip_output():
    proc = run(["ip", "-br", "addr"], timeout=2)
    return proc.stdout


def detect_local_ip(server_ip):
    proc = run(["ip", "route", "get", str(server_ip)], timeout=2)
    if proc.returncode == 0:
        parts = proc.stdout.split()
        if "src" in parts:
            src_index = parts.index("src") + 1
            if src_index < len(parts):
                return parts[src_index]

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect((str(server_ip), 9))
            return sock.getsockname()[0]
    except OSError:
        return None


def resolve_local_ip(local_ip, server_ip):
    if str(local_ip).lower() == "auto":
        return detect_local_ip(server_ip)
    return local_ip


def has_local_ip(output, local_ip):
    return bool(local_ip and local_ip in output)


def ping_server(server_ip):
    if not server_ip or not shutil.which("ping"):
        return None
    proc = run(["ping", "-c", "1", "-W", "1", str(server_ip)], timeout=2)
    return proc.returncode == 0


def tcp_port_open(host, port, timeout=1.0):
    if not host:
        return False
    try:
        with socket.create_connection((str(host), int(port)), timeout=timeout):
            return True
    except OSError:
        return False


def fuser_output(device):
    if not device or not shutil.which("fuser"):
        return ""
    proc = run(["fuser", "-v", str(device)], timeout=2)
    return (proc.stdout + proc.stderr).strip()


def is_video_capture_device(device):
    if not device or not shutil.which("v4l2-ctl"):
        return None
    proc = run(["v4l2-ctl", f"--device={device}", "--all"], timeout=3)
    output = proc.stdout + proc.stderr
    if proc.returncode != 0:
        return False
    return "Format Video Capture:" in output or "\n\t\tVideo Capture\n" in output


def preflight(config, config_path, identity_map=None, write_identity_resolved=None, identity_resolved=None):
    identity_map = identity_map or identity_map_from_config(config, config_path.parent)
    if identity_map:
        status = validate_hardware_identity(identity_map, write_identity_resolved)
        if status != 0:
            return status
        if write_identity_resolved:
            identity_resolved = load_identity_resolved(write_identity_resolved)

    sensors = expected_sensors(config, config_path.parent, identity_resolved)
    ip_info = ip_output()
    hard_failures = 0

    print_header("启动前检查")
    for sensor in sensors:
        checks = sensor["preflight"]
        if sensor["id"].startswith("baton_mini."):
            local_ip = checks.get("local_ip")
            server_ip = checks.get("server_ip")
            resolved_local_ip = resolve_local_ip(local_ip, server_ip)
            local_ok = has_local_ip(ip_info, resolved_local_ip)
            ping_ok = ping_server(server_ip)
            required_ports = sensor.get("preflight", {}).get(
                "tcp_ports", [8000, 9994, 9996, 9997, 9998]
            )
            if not local_ok:
                hard_failures += 1
                print(
                    f"FAIL {sensor['label']}: 本机未绑定 local_ip={resolved_local_ip} "
                    f"(config={local_ip})"
                )
            else:
                suffix = f" (auto)" if str(local_ip).lower() == "auto" else ""
                print(f"OK   {sensor['label']}: 已绑定 local_ip={resolved_local_ip}{suffix}")

            if ping_ok is True:
                print(f"OK   {sensor['label']}: 设备 IP 可 ping 通 server_ip={server_ip}")
            elif ping_ok is False:
                print(f"WARN {sensor['label']}: ping 不通 server_ip={server_ip}，如果设备禁 ICMP 可忽略")
            else:
                print(f"WARN {sensor['label']}: 未执行 ping 检查")

            closed_ports = [port for port in required_ports if not tcp_port_open(server_ip, port)]
            if closed_ports:
                hard_failures += 1
                closed_text = ", ".join(str(port) for port in closed_ports)
                print(f"FAIL {sensor['label']}: 设备 TCP 端口未打开 server_ip={server_ip}, ports={closed_text}")
                if ping_ok is True:
                    print(
                        f"     说明: {server_ip} 网络可达，但 Baton Mini 设备侧 SDK 服务未开放。"
                    )
                    print(
                        "     建议: 先重启或重新插拔该 Baton Mini，等待 10-20 秒后重新运行脚本。"
                    )
            else:
                open_text = ", ".join(str(port) for port in required_ports)
                print(f"OK   {sensor['label']}: 设备 TCP 端口已打开 ports={open_text}")
        elif sensor["id"].startswith("gopro."):
            device = checks.get("video_device")
            if not device or not Path(device).exists():
                hard_failures += 1
                print(f"FAIL {sensor['label']}: 视频设备不存在 video_device={device}")
                continue
            if not shutil.which("v4l2-ctl"):
                hard_failures += 1
                print(f"FAIL {sensor['label']}: 未安装 v4l2-ctl，无法在启动前设置采集卡帧率")
                continue
            access = os.access(device, os.R_OK | os.W_OK)
            video_capture = is_video_capture_device(device)
            busy = fuser_output(device)
            if access:
                print(f"OK   {sensor['label']}: 视频设备存在且当前用户可访问 {device}")
            else:
                hard_failures += 1
                print(f"FAIL {sensor['label']}: 当前用户不可读写视频设备 {device}")
            if video_capture is True:
                print(f"OK   {sensor['label']}: {device} 是 Video Capture 设备")
            elif video_capture is False:
                hard_failures += 1
                print(f"FAIL {sensor['label']}: {device} 不是 Video Capture 设备，可能是 metadata 节点")
            if busy:
                print(f"WARN {sensor['label']}: 设备可能被占用: {busy}")
        elif sensor["id"] == "pressure":
            config_file = checks.get("pressure_config_file")
            if not config_file or not Path(config_file).exists():
                hard_failures += 1
                print(f"FAIL {sensor['label']}: 触觉配置文件不存在 config_file={config_file}")
                continue

            print(f"OK   {sensor['label']}: 触觉配置文件存在 {config_file}")
            try:
                with Path(config_file).open("r", encoding="utf-8") as stream:
                    pressure_config = yaml.safe_load(stream) or {}
            except OSError as exc:
                hard_failures += 1
                print(f"FAIL {sensor['label']}: 读取触觉配置失败: {exc}")
                continue

            params = (
                pressure_config.get("pressure_driver_node", {})
                .get("ros__parameters", {})
            )
            serial_ports = params.get("serial_ports") or []
            serial_candidates = []
            for pattern in params.get("serial_port_globs") or params.get("candidate_serial_ports") or []:
                serial_candidates.extend(glob(os.path.expanduser(os.path.expandvars(str(pattern)))))

            seen_realpaths = set()
            serial_checks = []
            for port_cfg in serial_ports:
                name = port_cfg.get("name", "unnamed")
                port = port_cfg.get("port")
                if port:
                    realpath = str(Path(port).resolve()) if Path(port).exists() else str(port)
                    seen_realpaths.add(realpath)
                serial_checks.append((name, port))
            for index, port in enumerate(sorted(set(serial_candidates))):
                realpath = str(Path(port).resolve()) if Path(port).exists() else str(port)
                if realpath in seen_realpaths:
                    continue
                seen_realpaths.add(realpath)
                serial_checks.append((f"discovered_{index}", port))

            if not serial_checks:
                hard_failures += 1
                print(f"FAIL {sensor['label']}: 触觉配置中没有可用 serial_ports 或 serial_port_globs")
                continue

            for name, port in serial_checks:
                if not port or not Path(port).exists():
                    hard_failures += 1
                    print(f"FAIL {sensor['label']}: 串口不存在 {name} port={port}")
                    continue
                access = os.access(port, os.R_OK | os.W_OK)
                busy = fuser_output(port)
                if access:
                    print(f"OK   {sensor['label']}: 串口存在且当前用户可访问 {name} port={port}")
                else:
                    hard_failures += 1
                    print(f"FAIL {sensor['label']}: 当前用户不可读写串口 {name} port={port}")
                if busy:
                    print(f"WARN {sensor['label']}: 串口可能被占用: {busy}")

    if hard_failures:
        print(f"\n启动前检查失败：{hard_failures} 个硬错误。已停止启动，先修硬件/设备状态。")
        return 1

    print("\n启动前检查通过。")
    return 0


def ros_list(args):
    proc = run(args, timeout=8)
    values = []
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line or line.startswith("["):
            continue
        values.append(line)
    return set(values), proc


def postlaunch(config, config_path, identity_resolved=None):
    sensors = expected_sensors(config, config_path.parent, identity_resolved)
    spin_time = os.environ.get("ROS_GRAPH_SPIN_TIME", "5")
    nodes, node_proc = ros_list(["ros2", "node", "list", "--no-daemon", "--spin-time", spin_time])
    topics, topic_proc = ros_list(["ros2", "topic", "list", "--no-daemon", "--spin-time", spin_time])
    failures = 0
    warnings = 0

    print_header("启动结果")
    if node_proc.returncode != 0:
        print(f"WARN ros2 node list 返回异常: {node_proc.stderr.strip()}")
    if topic_proc.returncode != 0:
        print(f"WARN ros2 topic list 返回异常: {topic_proc.stderr.strip()}")

    for sensor in sensors:
        expected_topics = [topic for topic in sensor["topics"] if topic]
        found_topics = [topic for topic in expected_topics if topic in topics]
        node_ok = sensor["node"] in nodes
        topics_ok = len(found_topics) == len(expected_topics)
        if node_ok and topics_ok:
            print(
                f"OK   {sensor['label']}: node={sensor['node']} "
                f"topics={len(found_topics)}/{len(expected_topics)}"
            )
        elif node_ok:
            warnings += 1
            print(
                f"WARN {sensor['label']}: node={sensor['node']} 已启动; "
                f"topics={len(found_topics)}/{len(expected_topics)}"
            )
            missing = [topic for topic in expected_topics if topic not in topics]
            if missing:
                print(f"     缺失 topic: {', '.join(missing)}")
        else:
            failures += 1
            print(
                f"FAIL {sensor['label']}: node={sensor['node']} "
                f"未发现; topics={len(found_topics)}/{len(expected_topics)}"
            )
            missing = [topic for topic in expected_topics if topic not in topics]
            if missing:
                print(f"     缺失 topic: {', '.join(missing)}")

    if failures:
        ok_count = len(sensors) - failures - warnings
        print(
            f"\n启动结果：{ok_count}/{len(sensors)} 个节点完全通过，"
            f"{warnings} 个已启动但 topic 不完整，{failures} 个未启动。"
        )
        return 2

    if warnings:
        ok_count = len(sensors) - warnings
        print(
            f"\n启动结果：{ok_count}/{len(sensors)} 个节点完全通过，"
            f"{warnings} 个已启动但 topic 不完整。"
        )
        return 1

    print(f"\n启动结果：{len(sensors)}/{len(sensors)} 个节点全部通过检查。")
    return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("preflight", "postlaunch"))
    parser.add_argument("--config", required=True)
    parser.add_argument("--identity-map", help="hardware identity map YAML to validate before launch")
    parser.add_argument(
        "--write-identity-resolved",
        help="write resolved hardware paths after successful preflight identity validation",
    )
    parser.add_argument(
        "--identity-resolved",
        help="resolved hardware identity YAML used to override runtime device paths",
    )
    args = parser.parse_args()

    config, config_path = load_config(args.config)
    print(f"配置文件: {config_path}")

    identity_resolved = load_identity_resolved(args.identity_resolved)
    if args.mode == "preflight":
        return preflight(
            config,
            config_path,
            identity_map=args.identity_map,
            write_identity_resolved=args.write_identity_resolved,
            identity_resolved=identity_resolved,
        )
    return postlaunch(config, config_path, identity_resolved=identity_resolved)


if __name__ == "__main__":
    sys.exit(main())
