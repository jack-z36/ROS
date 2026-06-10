from pathlib import Path
import socket
import subprocess

import yaml
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction, IncludeLaunchDescription, LogInfo, OpaqueFunction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def _as_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("1", "true", "yes", "on")
    return bool(value)


def _stringify(value):
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _require(mapping, key, context):
    if key not in mapping:
        raise RuntimeError(f"Missing '{key}' in {context}")
    return mapping[key]


def _topic_setting(topics, key, default_name, default_enabled=True):
    value = (topics or {}).get(key)
    if isinstance(value, dict):
        return (
            value.get("name", value.get("topic", default_name)),
            _as_bool(value.get("enabled", default_enabled)),
        )
    if value is None:
        return default_name, _as_bool(default_enabled)
    return value, _as_bool(default_enabled)


def _detect_local_ip(server_ip):
    proc = subprocess.run(
        ["ip", "route", "get", str(server_ip)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"Failed to detect local IP for server {server_ip}: {proc.stderr.strip()}"
        )

    parts = proc.stdout.split()
    if "src" in parts:
        src_index = parts.index("src") + 1
        if src_index < len(parts):
            return parts[src_index]

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.connect((str(server_ip), 9))
        return sock.getsockname()[0]


def _resolve_local_ip(cfg, side):
    server_ip = _require(cfg, "server_ip", f"baton_mini.{side}")
    local_ip = cfg.get("local_ip", "auto")
    if str(local_ip).lower() == "auto":
        return _detect_local_ip(server_ip)
    return local_ip


def _baton_include(side, cfg, launch_file):
    topics = cfg.get("topics") or {}
    local_ip = _resolve_local_ip(cfg, side)
    imu_topic, publish_imu = _topic_setting(topics, "imu", f"/baton_mini_{side}/imu", True)
    odom_topic, publish_odometry = _topic_setting(
        topics, "odometry", f"/baton_mini_{side}/odometry", True
    )
    fast_odom_topic, publish_fast_odom = _topic_setting(
        topics, "fast_odom", f"/baton_mini_{side}/fast_odom", True
    )
    image_left_topic, publish_image_left = _topic_setting(
        topics, "image_left", f"/baton_mini_{side}/image_left", True
    )
    image_right_topic, publish_image_right = _topic_setting(
        topics, "image_right", f"/baton_mini_{side}/image_right", True
    )
    return IncludeLaunchDescription(
        PythonLaunchDescriptionSource(launch_file),
        launch_arguments={
            "server_ip": _stringify(_require(cfg, "server_ip", f"baton_mini.{side}")),
            "local_ip": _stringify(local_ip),
            "node_name": _stringify(cfg.get("node_name", f"baton_mini_{side}")),
            "imu_topic": _stringify(imu_topic),
            "odom_topic": _stringify(odom_topic),
            "fast_odom_topic": _stringify(fast_odom_topic),
            "image_left_topic": _stringify(image_left_topic),
            "image_right_topic": _stringify(image_right_topic),
            "publish_imu": _stringify(publish_imu),
            "publish_odometry": _stringify(publish_odometry),
            "publish_fast_odom": _stringify(publish_fast_odom),
            "publish_image_left": _stringify(publish_image_left),
            "publish_image_right": _stringify(publish_image_right),
        }.items(),
    )


def _gopro_include(side, cfg, launch_file):
    topics = cfg.get("topics") or {}
    image_raw_topic, _publish_image_raw = _topic_setting(topics, "image_raw", "image_raw", True)
    camera_info_default = cfg.get("publish_camera_info", False if topics else True)
    camera_info_topic, publish_camera_info = _topic_setting(
        topics, "camera_info", "camera_info", camera_info_default
    )
    return GroupAction(
        scoped=True,
        forwarding=False,
        actions=[
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(launch_file),
                launch_arguments={
                    "video_device": _stringify(_require(cfg, "video_device", f"gopro.{side}")),
                    "publish_camera_info": _stringify(publish_camera_info),
                    "camera_namespace": _stringify(cfg.get("namespace", f"gopro_{side}")),
                    "node_name": _stringify(cfg.get("node_name", f"gopro_{side}_camera")),
                    "camera_name": _stringify(cfg.get("camera_name", f"gopro_{side}")),
                    "frame_id": _stringify(cfg.get("frame_id", f"gopro_{side}_optical_frame")),
                    "frame_rate": _stringify(cfg.get("frame_rate", 30)),
                    "pixel_format": _stringify(cfg.get("pixel_format", "YUYV")),
                    "output_encoding": _stringify(cfg.get("output_encoding", "rgb8")),
                    "image_raw_topic": _stringify(image_raw_topic),
                    "camera_info_topic": _stringify(camera_info_topic),
                }.items(),
            )
        ],
    )


def _pressure_include(cfg, launch_file):
    config_file = Path(cfg.get("config_file", "")).expanduser()
    if not config_file.is_absolute():
        config_file = Path.cwd() / config_file
    if not config_file.exists():
        raise RuntimeError(f"Pressure config file does not exist: {config_file}")

    return IncludeLaunchDescription(
        PythonLaunchDescriptionSource(launch_file),
        launch_arguments={
            "config_file": str(config_file),
        }.items(),
    )


def _load_identity_resolved(path):
    if not path:
        return {}
    resolved_path = Path(path).expanduser()
    if not resolved_path.is_absolute():
        resolved_path = Path.cwd() / resolved_path
    if not resolved_path.exists():
        return {}
    with resolved_path.open("r", encoding="utf-8") as stream:
        return yaml.safe_load(stream) or {}


def _apply_identity_resolved(config, resolved):
    for side, resolved_cfg in (resolved.get("gopro") or {}).items():
        device = resolved_cfg.get("device")
        if device and side in (config.get("gopro") or {}):
            config["gopro"][side]["video_device"] = device


def _load_nodes(context):
    config_file = Path(LaunchConfiguration("config_file").perform(context)).expanduser()
    if not config_file.is_absolute():
        config_file = Path.cwd() / config_file
    if not config_file.exists():
        raise RuntimeError(f"Sensor config file does not exist: {config_file}")

    with config_file.open("r", encoding="utf-8") as stream:
        config = yaml.safe_load(stream) or {}
    identity_resolved_file = LaunchConfiguration("identity_resolved_file").perform(context)
    identity_resolved = _load_identity_resolved(identity_resolved_file)
    _apply_identity_resolved(config, identity_resolved)

    baton_launch = PathJoinSubstitution(
        [FindPackageShare("baton_mini"), "launch", "baton_mini.launch.py"]
    )
    gopro_launch = PathJoinSubstitution(
        [FindPackageShare("gopro_camera_launch"), "launch", "gopro_pose_record.launch.py"]
    )
    pressure_launch = PathJoinSubstitution(
        [FindPackageShare("hwk_pressure_driver"), "launch", "pressure_driver.launch.py"]
    )

    actions = [LogInfo(msg=f"Loading all sensor config: {config_file}")]
    if identity_resolved:
        actions.append(LogInfo(msg=f"Using resolved hardware identity file: {identity_resolved_file}"))

    for side, cfg in (config.get("baton_mini") or {}).items():
        if _as_bool(cfg.get("enabled", True)):
            actions.append(LogInfo(msg=f"Starting Baton Mini {side}"))
            actions.append(_baton_include(side, cfg, baton_launch))

    for side, cfg in (config.get("gopro") or {}).items():
        topics = cfg.get("topics") or {}
        _image_raw_topic, publish_image_raw = _topic_setting(topics, "image_raw", "image_raw", True)
        if _as_bool(cfg.get("enabled", True)) and publish_image_raw:
            actions.append(LogInfo(msg=f"Starting GoPro {side}"))
            actions.append(_gopro_include(side, cfg, gopro_launch))

    pressure_cfg = config.get("pressure") or {}
    if _as_bool(pressure_cfg.get("enabled", False)):
        actions.append(LogInfo(msg="Starting HWK pressure driver"))
        actions.append(_pressure_include(pressure_cfg, pressure_launch))

    return actions


def generate_launch_description():
    default_config = "/home/hit/ROS/config/all_sensor_nodes.yaml"
    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "config_file",
                default_value=default_config,
                description="YAML file that defines enabled sensors, devices, namespaces, and topics.",
            ),
            DeclareLaunchArgument(
                "identity_resolved_file",
                default_value="",
                description="Resolved hardware identity YAML generated before launch.",
            ),
            OpaqueFunction(function=_load_nodes),
        ]
    )
