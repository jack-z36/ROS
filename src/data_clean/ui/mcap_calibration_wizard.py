"""Live GoPro calibration center for the MCAP cleaning pipeline."""

from __future__ import annotations

import argparse
import copy
import json
import os
import select
import shutil
import signal
import socket
import subprocess
import sys
import threading
import time
import webbrowser
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import cv2
import numpy as np
import yaml
from repo.config.mcap_process_config import (
    AppConfig,
    GripperStreamConfig,
    PoseStreamConfig,
    QuaternionConfig,
    TransformConfig,
    Vector3Config,
    calibration_item_status,
    config_is_calibrated,
    load_app_config,
)
from repo.ros2_codec import extract_pose_fields


WORKSPACE_DIR = Path("/home/hit/ROS")
DEFAULT_OUTPUT_CONFIG = WORKSPACE_DIR / "config/data_clean/data_clean_calibrated.yaml"
GOPRO_ONLY_SCRIPT = WORKSPACE_DIR / "start_gopro_only.sh"
GOPRO_LOG_DIR = WORKSPACE_DIR / "log"
GOPRO_TOPICS = {
    "left": "/gopro_left/image_raw",
    "right": "/gopro_right/image_raw",
}
HAND_LABELS = {
    "left": "左手",
    "right": "右手",
}
ARUCO_CANDIDATES = (
    "DICT_4X4_50",
    "DICT_4X4_100",
    "DICT_4X4_250",
    "DICT_4X4_1000",
    "DICT_5X5_50",
    "DICT_5X5_100",
    "DICT_5X5_250",
    "DICT_5X5_1000",
    "DICT_6X6_50",
    "DICT_6X6_100",
    "DICT_6X6_250",
    "DICT_6X6_1000",
)
SAMPLE_SECONDS = 2.0
MIN_SAMPLE_FRAMES = 30
MIN_PAIR_DETECTION_RATE = 0.90
MAX_DISTANCE_STD_PX = 3.0
FRESH_IMAGE_MAX_AGE_SEC = 2.0
LOST_IMAGE_TIMEOUT_SEC = 5.0


@dataclass(frozen=True)
class DetectionFrame:
    aruco_dict: str | None
    ids: list[int]
    centers: dict[int, np.ndarray]
    corners: list[np.ndarray]
    distance_px: float | None


@dataclass(frozen=True)
class LiveSampleStats:
    sampled_frames: int
    detections: dict[str, list[dict[int, np.ndarray]]]
    id_counts: dict[str, Counter[int]]


@dataclass(frozen=True)
class GripperSideCalibration:
    hand: str
    image_topic: str
    output_topic: str
    aruco_dict: str
    marker_id_0: int
    marker_id_1: int
    marker_min: float
    marker_max: float
    closed_rate: float
    open_rate: float
    closed_std: float
    open_std: float
    closed_frames: int
    open_frames: int


@dataclass(frozen=True)
class CommonFrameSideCalibration:
    hand: str
    input_topic: str
    output_topic: str
    start_from_common: TransformConfig
    sample_frames: int
    position_std: float


@dataclass(frozen=True)
class CommonFrameRightCalibration:
    """Right-hand common frame calibration with raw pose and inverse extrinsic."""

    input_topic: str
    output_topic: str
    sample_frames: int
    position_std: float
    t_right_start_common: TransformConfig
    common_from_right_start: TransformConfig


ASSET_BASE = WORKSPACE_DIR / "asset/阶段二：数据清洗"
DEV_RUNS_BASE = ASSET_BASE / "dev_runs/scene1"


@dataclass(frozen=True)
class Scene1DevRun:
    run_id: str
    check_id: str
    run_dir: Path
    artifact_dir: Path
    log_dir: Path
    config_dir: Path
    effective_config: Path
    status: str


def create_scene1_dev_run(check_id: str) -> Scene1DevRun:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_id = f"{timestamp}_{check_id}"
    run_dir = DEV_RUNS_BASE / run_id
    artifact_dir = run_dir / "artifacts"
    log_dir = run_dir / "logs"
    config_dir = run_dir / "config"
    effective_config = config_dir / "effective_config.yaml"

    artifact_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)
    config_dir.mkdir(parents=True, exist_ok=True)

    run_log = {
        "run_id": run_id,
        "check_id": check_id,
        "run_dir": str(run_dir),
        "artifact_dir": str(artifact_dir),
        "log_dir": str(log_dir),
        "effective_config": str(effective_config),
        "status": "ready",
        "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
    }
    with (log_dir / "run_log.json").open("w", encoding="utf-8") as fh:
        json.dump(run_log, fh, ensure_ascii=False, indent=2)

    with effective_config.open("w", encoding="utf-8") as fh:
        yaml.safe_dump({"#": "effective config snapshot"}, fh, allow_unicode=True)

    return Scene1DevRun(
        run_id=run_id,
        check_id=check_id,
        run_dir=run_dir,
        artifact_dir=artifact_dir,
        log_dir=log_dir,
        config_dir=config_dir,
        effective_config=effective_config,
        status="ready",
    )


def write_gripper_calibration_artifacts(
    dev_run: Scene1DevRun,
    results: list[GripperSideCalibration],
) -> Scene1DevRun:
    config_path = dev_run.artifact_dir / "gripper_calibration_config.yaml"
    summary_path = dev_run.artifact_dir / "gripper_calibration_summary.json"
    run_log_path = dev_run.log_dir / "run_log.json"

    config_data = {
        "gripper_calibration": {
            "generated_by": "scene1_gripper_calibration_config",
            "calibrated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "sides": {},
        }
    }
    summary = {}

    for item in results:
        side_config = {
            "hand": item.hand,
            "image_topic": item.image_topic,
            "output_topic": item.output_topic,
            "aruco_dict": item.aruco_dict,
            "marker_id_0": item.marker_id_0,
            "marker_id_1": item.marker_id_1,
            "marker_min": round(item.marker_min, 3),
            "marker_max": round(item.marker_max, 3),
            "gripper_max": 100.0,
            "calibration_source": "browser_gopro_calibration",
        }
        config_data["gripper_calibration"]["sides"][item.hand] = side_config

        summary[item.hand] = {
            "marker_id_0": item.marker_id_0,
            "marker_id_1": item.marker_id_1,
            "marker_min": round(item.marker_min, 3),
            "marker_max": round(item.marker_max, 3),
            "gripper_max": 100.0,
            "closed_rate": round(item.closed_rate, 4),
            "open_rate": round(item.open_rate, 4),
            "closed_std": round(item.closed_std, 3),
            "open_std": round(item.open_std, 3),
            "closed_frames": item.closed_frames,
            "open_frames": item.open_frames,
        }

    with config_path.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(config_data, fh, allow_unicode=True, sort_keys=False)

    with summary_path.open("w", encoding="utf-8") as fh:
        json.dump(summary, fh, ensure_ascii=False, indent=2)

    with run_log_path.open("r", encoding="utf-8") as fh:
        run_log = json.load(fh)

    run_log["status"] = "success"
    run_log["artifacts"] = {
        "gripper_calibration_config.yaml": str(config_path),
        "gripper_calibration_summary.json": str(summary_path),
    }
    run_log["completed_at"] = datetime.now().astimezone().isoformat(timespec="seconds")

    with run_log_path.open("w", encoding="utf-8") as fh:
        json.dump(run_log, fh, ensure_ascii=False, indent=2)

    return Scene1DevRun(
        run_id=dev_run.run_id,
        check_id=dev_run.check_id,
        run_dir=dev_run.run_dir,
        artifact_dir=dev_run.artifact_dir,
        log_dir=dev_run.log_dir,
        config_dir=dev_run.config_dir,
        effective_config=dev_run.effective_config,
        status="success",
    )


def save_gripper_calibration_to_production(
    output_path: Path,
    results: list[GripperSideCalibration],
) -> AppConfig:
    config = load_app_config(output_path)
    return _save_gripper(config, output_path, results)


def _short_path(path: str | Path) -> str:
    try:
        return os.path.relpath(str(path), str(WORKSPACE_DIR))
    except ValueError:
        return str(path)


def _detector_parameters():
    if hasattr(cv2.aruco, "DetectorParameters"):
        return cv2.aruco.DetectorParameters()
    return cv2.aruco.DetectorParameters_create()


def _aruco_dictionaries() -> dict[str, Any]:
    return {
        name: cv2.aruco.getPredefinedDictionary(getattr(cv2.aruco, name))
        for name in ARUCO_CANDIDATES
        if hasattr(cv2.aruco, name)
    }


def _to_mapping(transform: TransformConfig) -> dict[str, Any]:
    return {
        "start_from_common": {
            "translation": {
                "x": transform.translation.x,
                "y": transform.translation.y,
                "z": transform.translation.z,
            },
            "rotation_xyzw": {
                "qx": transform.rotation_xyzw.qx,
                "qy": transform.rotation_xyzw.qy,
                "qz": transform.rotation_xyzw.qz,
                "qw": transform.rotation_xyzw.qw,
            },
        }
    }


def _to_mapping_from_transform(transform: TransformConfig) -> dict[str, Any]:
    return {
        "start_from_common": {
            "translation": {
                "x": transform.translation.x,
                "y": transform.translation.y,
                "z": transform.translation.z,
            },
            "rotation_xyzw": {
                "qx": transform.rotation_xyzw.qx,
                "qy": transform.rotation_xyzw.qy,
                "qz": transform.rotation_xyzw.qz,
                "qw": transform.rotation_xyzw.qw,
            },
        }
    }


def _batch_to_mapping(config: AppConfig) -> dict[str, Any]:
    return {
        "input_dir": config.batch.input_dir,
        "output_dir": config.batch.output_dir,
        "file_glob": config.batch.file_glob,
        "workers": config.batch.workers,
        "overwrite": config.batch.overwrite,
        "fail_fast": config.batch.fail_fast,
    }


def _pose_stream_to_mapping(stream: PoseStreamConfig, fallback_transform: TransformConfig) -> dict[str, Any]:
    mapping = {
        "input_topic": stream.input_topic,
        "msg_type": stream.msg_type,
        "output_topic": stream.output_topic,
    }
    if stream.transform_file:
        mapping["transform_file"] = stream.transform_file
    else:
        transform = stream.transform or fallback_transform
        mapping["transform"] = _to_mapping(transform)
    return mapping


def _gripper_stream_to_mapping(stream: GripperStreamConfig) -> dict[str, Any]:
    return {
        "image_topic": stream.image_topic,
        "image_msg_type": stream.image_msg_type,
        "output_topic": stream.output_topic,
        "output_msg_type": stream.output_msg_type,
        "aruco_dict": stream.aruco_dict,
        "marker_id_0": stream.marker_id_0,
        "marker_id_1": stream.marker_id_1,
        "marker_min": stream.marker_min,
        "marker_max": stream.marker_max,
        "gripper_max": stream.gripper_max,
    }


def _hand_from_text(*values: str) -> str | None:
    joined = " ".join(values).lower()
    if "left" in joined or "左" in joined:
        return "left"
    if "right" in joined or "右" in joined:
        return "right"
    return None


def _stream_for_hand(streams: tuple[GripperStreamConfig, ...], hand: str) -> GripperStreamConfig:
    for stream in streams:
        if _hand_from_text(stream.image_topic, stream.output_topic) == hand:
            return stream
    raise RuntimeError(f"配置中找不到 {HAND_LABELS[hand]} GoPro 夹爪 stream。")


def _pose_for_hand(streams: tuple[PoseStreamConfig, ...], hand: str) -> PoseStreamConfig:
    for stream in streams:
        if _hand_from_text(stream.input_topic, stream.output_topic) == hand:
            return stream
    raise RuntimeError(f"配置中找不到 {HAND_LABELS[hand]} 位姿 stream。")


def _ros_image_to_bgr(msg: Any) -> np.ndarray:
    height = int(msg.height)
    width = int(msg.width)
    step = int(msg.step)
    encoding = str(msg.encoding).lower()
    raw = np.frombuffer(bytes(msg.data), dtype=np.uint8)

    if encoding in {"rgb8", "bgr8"}:
        rows = raw.reshape(height, step)[:, : width * 3]
        image = rows.reshape(height, width, 3)
        if encoding == "rgb8":
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        return np.ascontiguousarray(image)
    if encoding == "mono8":
        rows = raw.reshape(height, step)[:, :width]
        return cv2.cvtColor(np.ascontiguousarray(rows), cv2.COLOR_GRAY2BGR)
    if encoding in {"rgba8", "bgra8"}:
        rows = raw.reshape(height, step)[:, : width * 4]
        image = rows.reshape(height, width, 4)
        code = cv2.COLOR_RGBA2BGR if encoding == "rgba8" else cv2.COLOR_BGRA2BGR
        return cv2.cvtColor(image, code)
    if encoding in {"yuyv", "yuyv422", "yuv422_yuy2"}:
        rows = raw.reshape(height, step)[:, : width * 2]
        image = rows.reshape(height, width, 2)
        return cv2.cvtColor(image, cv2.COLOR_YUV2BGR_YUY2)
    raise RuntimeError(f"暂不支持实时图像编码: {msg.encoding}")


class LiveImageSubscriber:
    def __init__(self, topics: dict[str, str], pose_streams: tuple[PoseStreamConfig, ...]) -> None:
        import rclpy
        from rclpy.qos import qos_profile_sensor_data
        from geometry_msgs.msg import PoseStamped
        from nav_msgs.msg import Odometry
        from sensor_msgs.msg import Image

        self._rclpy = rclpy
        if not rclpy.ok():
            rclpy.init(args=None)
        self.node = rclpy.create_node("data_clean_calibration_wizard")
        self._lock = threading.Lock()
        self._latest: dict[str, tuple[np.ndarray, float, int]] = {}
        self._seq_by_hand: dict[str, int] = {}
        self._latest_pose: dict[str, tuple[tuple[float, float, float, float, float, float, float], float, int]] = {}
        self._pose_seq_by_topic: dict[str, int] = {}
        pose_msg_types = {
            "nav_msgs/msg/Odometry": Odometry,
            "geometry_msgs/msg/PoseStamped": PoseStamped,
        }
        self._subscriptions = [
            self.node.create_subscription(
                Image,
                topic,
                self._make_callback(hand),
                qos_profile_sensor_data,
            )
            for hand, topic in topics.items()
        ]
        for stream in pose_streams:
            msg_type = pose_msg_types.get(stream.msg_type)
            if msg_type is None:
                raise RuntimeError(f"实时标定暂不支持位姿类型: {stream.msg_type}")
            self._subscriptions.append(
                self.node.create_subscription(
                    msg_type,
                    stream.input_topic,
                    self._make_pose_callback(stream),
                    qos_profile_sensor_data,
                )
            )

    def _make_callback(self, hand: str):
        def callback(msg: Any) -> None:
            try:
                image = _ros_image_to_bgr(msg)
            except Exception as exc:  # noqa: BLE001 - keep subscriber alive.
                print(f"\n{HAND_LABELS[hand]} 图像转换失败: {exc}", file=sys.stderr)
                return
            with self._lock:
                seq = self._seq_by_hand.get(hand, 0) + 1
                self._seq_by_hand[hand] = seq
                self._latest[hand] = (image, time.monotonic(), seq)

        return callback

    def _make_pose_callback(self, stream: PoseStreamConfig):
        def callback(msg: Any) -> None:
            try:
                pose = extract_pose_fields(msg, stream.msg_type)
            except Exception as exc:  # noqa: BLE001 - keep subscriber alive.
                print(f"\n{stream.input_topic} 位姿解析失败: {exc}", file=sys.stderr)
                return
            with self._lock:
                seq = self._pose_seq_by_topic.get(stream.input_topic, 0) + 1
                self._pose_seq_by_topic[stream.input_topic] = seq
                self._latest_pose[stream.input_topic] = (pose, time.monotonic(), seq)

        return callback

    def spin_once(self, timeout_sec: float = 0.05) -> None:
        self._rclpy.spin_once(self.node, timeout_sec=timeout_sec)

    def latest_image(self, hand: str, max_age_sec: float | None = None) -> np.ndarray | None:
        with self._lock:
            item = self._latest.get(hand)
            if item is None:
                return None
            if max_age_sec is not None and time.monotonic() - item[1] > max_age_sec:
                return None
            return item[0].copy()

    def latest_frame(self, hand: str, max_age_sec: float | None = None) -> tuple[np.ndarray, float, int] | None:
        with self._lock:
            item = self._latest.get(hand)
            if item is None:
                return None
            if max_age_sec is not None and time.monotonic() - item[1] > max_age_sec:
                return None
            return item[0].copy(), item[1], item[2]

    def wait_for_images(self, hands: tuple[str, ...] = ("left", "right"), timeout_sec: float = 5.0) -> bool:
        deadline = time.monotonic() + timeout_sec
        while time.monotonic() < deadline:
            self.spin_once(0.1)
            with self._lock:
                now = time.monotonic()
                if all(
                    hand in self._latest and now - self._latest[hand][1] <= FRESH_IMAGE_MAX_AGE_SEC
                    for hand in hands
                ):
                    return True
        return False

    def missing_hands(self, hands: tuple[str, ...] = ("left", "right")) -> list[str]:
        with self._lock:
            now = time.monotonic()
            return [
                hand
                for hand in hands
                if hand not in self._latest or now - self._latest[hand][1] > FRESH_IMAGE_MAX_AGE_SEC
            ]

    def latest_pose(
        self,
        topic: str,
        max_age_sec: float | None = None,
    ) -> tuple[tuple[float, float, float, float, float, float, float], float, int] | None:
        with self._lock:
            item = self._latest_pose.get(topic)
            if item is None:
                return None
            if max_age_sec is not None and time.monotonic() - item[1] > max_age_sec:
                return None
            return item

    def close(self) -> None:
        self.node.destroy_node()


class ManagedGoProProcess:
    def __init__(self, process: subprocess.Popen[str] | None, log_path: Path | None = None) -> None:
        self.process = process
        self.log_path = log_path

    @property
    def started_by_wizard(self) -> bool:
        return self.process is not None

    def stop(self) -> None:
        if self.process is None or self.process.poll() is not None:
            return
        try:
            os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
            self.process.wait(timeout=8)
        except subprocess.TimeoutExpired:
            os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
            self.process.wait(timeout=3)


def _start_gopro_only(sides: list[str]) -> ManagedGoProProcess:
    if not GOPRO_ONLY_SCRIPT.exists():
        raise RuntimeError(f"找不到 GoPro-only 启动脚本: {GOPRO_ONLY_SCRIPT}")
    GOPRO_LOG_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = GOPRO_LOG_DIR / f"data_clean_gopro_only_{stamp}.log"
    log_fh = log_path.open("a", encoding="utf-8")
    process = subprocess.Popen(
        [str(GOPRO_ONLY_SCRIPT), "--sides", *sides],
        cwd=str(WORKSPACE_DIR),
        text=True,
        stdout=log_fh,
        stderr=subprocess.STDOUT,
        preexec_fn=os.setsid,
    )
    log_fh.close()
    return ManagedGoProProcess(process, log_path)


def _ensure_gopro_topics(subscriber: LiveImageSubscriber) -> ManagedGoProProcess:
    print("检查左右 GoPro 实时图像 topic ...")
    if subscriber.wait_for_images(timeout_sec=3.0):
        print("  已收到 /gopro_left/image_raw 和 /gopro_right/image_raw。")
        return ManagedGoProProcess(None)

    missing = subscriber.missing_hands()
    missing_label = "、".join(HAND_LABELS[hand] for hand in missing)
    print(f"  当前缺少 {missing_label} GoPro 图像，自动启动缺失侧 GoPro-only 节点。")
    process = _start_gopro_only(missing)
    if process.log_path is not None:
        print(f"  GoPro 启动日志: {_short_path(process.log_path)}")
    if subscriber.wait_for_images(timeout_sec=20.0):
        print("  GoPro 图像已就绪。")
        return process

    process.stop()
    if process.log_path is not None:
        print(f"  详细日志: {_short_path(process.log_path)}")
    raise RuntimeError("启动 GoPro 后仍未收到左右图像，请检查采集卡、电源、HDMI 输入和设备映射。")


def _detect_markers(
    image: np.ndarray,
    dictionaries: dict[str, Any],
    parameters: Any,
    preferred_dict: str | None = None,
    marker_pair: tuple[int, int] | None = None,
) -> DetectionFrame:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image
    names = [preferred_dict] if preferred_dict else list(dictionaries)
    best: DetectionFrame | None = None
    for name in names:
        if name is None or name not in dictionaries:
            continue
        corners, ids, _ = cv2.aruco.detectMarkers(gray, dictionaries[name], parameters=parameters)
        if ids is None:
            candidate = DetectionFrame(name, [], {}, [], None)
        else:
            centers: dict[int, np.ndarray] = {}
            id_list: list[int] = []
            for index, marker_id in enumerate(ids.flatten()):
                marker_id = int(marker_id)
                id_list.append(marker_id)
                centers[marker_id] = np.mean(corners[index][0], axis=0)
            distance: float | None = None
            if marker_pair and marker_pair[0] in centers and marker_pair[1] in centers:
                distance = float(np.linalg.norm(centers[marker_pair[0]] - centers[marker_pair[1]]))
            elif len(id_list) >= 2:
                distance = float(np.linalg.norm(centers[id_list[0]] - centers[id_list[1]]))
            candidate = DetectionFrame(name, id_list, centers, list(corners), distance)
        if marker_pair and candidate.distance_px is not None:
            return candidate
        if best is None or len(candidate.ids) > len(best.ids):
            best = candidate
        if not marker_pair and len(candidate.ids) >= 2:
            return candidate
    return best or DetectionFrame(None, [], {}, [], None)


def _draw_detection_overlay(image: np.ndarray, detection: DetectionFrame, title: str) -> np.ndarray:
    canvas = image.copy()
    if detection.corners and detection.ids:
        ids = np.asarray(detection.ids, dtype=np.int32).reshape(-1, 1)
        cv2.aruco.drawDetectedMarkers(canvas, detection.corners, ids)
    color = (0, 220, 0) if detection.distance_px is not None else (0, 0, 255)
    lines = [
        title,
        f"dict: {detection.aruco_dict or '-'}  ids: {detection.ids or '-'}",
        f"distance: {detection.distance_px:.1f}px" if detection.distance_px is not None else "distance: waiting",
    ]
    y = 28
    for line in lines:
        cv2.putText(canvas, line, (12, y), cv2.FONT_HERSHEY_SIMPLEX, 0.75, color, 2, cv2.LINE_AA)
        y += 32
    return canvas


def _distances_for_pair(stats: LiveSampleStats, aruco_dict: str, marker_id_0: int, marker_id_1: int) -> list[float]:
    distances: list[float] = []
    for centers in stats.detections.get(aruco_dict, []):
        if marker_id_0 in centers and marker_id_1 in centers:
            distances.append(float(np.linalg.norm(centers[marker_id_0] - centers[marker_id_1])))
    return distances


def _select_dictionary_and_ids(
    closed_stats: LiveSampleStats,
    open_stats: LiveSampleStats,
) -> tuple[str, int, int]:
    best_name = ""
    best_score = -1
    for name in ARUCO_CANDIDATES:
        combined = closed_stats.id_counts.get(name, Counter()) + open_stats.id_counts.get(name, Counter())
        if len(combined) < 2:
            continue
        score = sum(combined.values())
        if score > best_score:
            best_name = name
            best_score = score
    if not best_name:
        raise RuntimeError("没有稳定识别到两个 ArUco marker。")
    top_ids = [
        marker_id
        for marker_id, _count in (
            closed_stats.id_counts[best_name] + open_stats.id_counts[best_name]
        ).most_common(2)
    ]
    return best_name, int(top_ids[0]), int(top_ids[1])


def _quality_check(
    label: str,
    stats: LiveSampleStats,
    distances: list[float],
) -> tuple[float, float]:
    if stats.sampled_frames < MIN_SAMPLE_FRAMES:
        raise RuntimeError(f"{label} 采样帧数不足：{stats.sampled_frames} < {MIN_SAMPLE_FRAMES}")
    rate = len(distances) / max(1, stats.sampled_frames)
    if rate < MIN_PAIR_DETECTION_RATE:
        raise RuntimeError(f"{label} 成对 marker 检测率不足：{rate:.1%} < {MIN_PAIR_DETECTION_RATE:.0%}")
    std = float(np.std(np.asarray(distances, dtype=np.float64)))
    if std > MAX_DISTANCE_STD_PX:
        raise RuntimeError(f"{label} 距离波动过大：{std:.2f}px > {MAX_DISTANCE_STD_PX:.1f}px")
    return rate, std


def _capture_latest_frame(subscriber: LiveImageSubscriber, hand: str, timeout_sec: float = 5.0) -> np.ndarray:
    deadline = time.monotonic() + timeout_sec
    while time.monotonic() < deadline:
        subscriber.spin_once(0.05)
        image = subscriber.latest_image(hand)
        if image is not None:
            return image
    raise RuntimeError(f"没有收到 {HAND_LABELS[hand]} GoPro 图像。")


def _base_config_mapping(config: AppConfig) -> dict[str, Any]:
    return {
        "calibration": dict(config.calibration),
        "batch": _batch_to_mapping(config),
        "transform": _to_mapping(config.transform),
        "pose_streams": [
            _pose_stream_to_mapping(stream, config.transform)
            for stream in config.pose_streams
        ],
        "gripper_streams": [
            _gripper_stream_to_mapping(stream)
            for stream in config.gripper_streams
        ],
    }


def _ensure_nested_status(calibration: dict[str, Any]) -> dict[str, Any]:
    calibration = dict(calibration or {})
    calibration.setdefault("generated_by", "core.mcap_calibration_wizard")
    calibration["updated_at"] = datetime.now().astimezone().isoformat(timespec="seconds")
    calibration.setdefault("gripper", {})
    calibration.setdefault("common_frame", {})
    calibration.pop("tcp", None)
    for section in ("gripper", "common_frame"):
        if not isinstance(calibration[section], dict):
            calibration[section] = {}
        for hand in ("left", "right"):
            current = calibration[section].get(hand)
            if not isinstance(current, dict):
                current = {"calibrated": False}
            current.setdefault("calibrated", False)
            calibration[section][hand] = current
    return calibration


def _mark_overall_status(calibration: dict[str, Any]) -> None:
    complete = all(
        bool(calibration.get(section, {}).get(hand, {}).get("calibrated"))
        for section in ("gripper", "common_frame")
        for hand in ("left", "right")
    )
    calibration["calibrated"] = complete
    calibration["complete"] = complete


def _apply_gripper_results(data: dict[str, Any], results: list[GripperSideCalibration]) -> None:
    calibration = _ensure_nested_status(data.get("calibration", {}))
    by_hand = {item.hand: item for item in results}
    for stream in data.get("gripper_streams", []):
        hand = _hand_from_text(str(stream.get("image_topic", "")), str(stream.get("output_topic", "")))
        if hand not in by_hand:
            continue
        item = by_hand[hand]
        stream["aruco_dict"] = item.aruco_dict
        stream["marker_id_0"] = item.marker_id_0
        stream["marker_id_1"] = item.marker_id_1
        stream["marker_min"] = round(item.marker_min, 3)
        stream["marker_max"] = round(item.marker_max, 3)
        stream["gripper_max"] = 100.0
        calibration["gripper"][hand] = {
            "calibrated": True,
            "method": "live_gopro_aruco",
            "image_topic": item.image_topic,
            "output_topic": item.output_topic,
            "aruco_dict": item.aruco_dict,
            "marker_ids": [item.marker_id_0, item.marker_id_1],
            "marker_min": round(item.marker_min, 3),
            "marker_max": round(item.marker_max, 3),
            "closed_detection_rate": round(item.closed_rate, 4),
            "open_detection_rate": round(item.open_rate, 4),
            "closed_std_px": round(item.closed_std, 3),
            "open_std_px": round(item.open_std, 3),
            "closed_frames": item.closed_frames,
            "open_frames": item.open_frames,
            "updated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        }
    _mark_overall_status(calibration)
    data["calibration"] = calibration


def _resolve_transform_file_for_write(path_raw: str, base_dir: Path) -> Path:
    path = Path(os.path.expandvars(path_raw)).expanduser()
    if path.is_absolute():
        return path
    return base_dir / path


def _load_transform_mapping_for_write(path: Path, fallback: dict[str, Any]) -> dict[str, Any]:
    if not path.exists():
        return copy.deepcopy(fallback)
    with path.open("r", encoding="utf-8") as fh:
        raw_data = yaml.safe_load(fh) or {}
    if not isinstance(raw_data, dict):
        return copy.deepcopy(fallback)
    transform_data = raw_data.get("transform", raw_data)
    if not isinstance(transform_data, dict):
        return copy.deepcopy(fallback)
    return copy.deepcopy(transform_data)


def _apply_common_frame_results(data: dict[str, Any], results: list[CommonFrameSideCalibration], base_dir: Path) -> None:
    calibration = _ensure_nested_status(data.get("calibration", {}))
    by_hand = {item.hand: item for item in results}
    for stream in data.get("pose_streams", []):
        hand = _hand_from_text(str(stream.get("input_topic", "")), str(stream.get("output_topic", "")))
        if hand not in by_hand:
            continue
        item = by_hand[hand]
        transform_file = str(stream.get("transform_file", "")).strip()
        if transform_file:
            transform_path = _resolve_transform_file_for_write(transform_file, base_dir)
            transform = _to_mapping(item.start_from_common)
        else:
            transform = _to_mapping(item.start_from_common)
            stream["transform"] = transform
        if transform_file:
            _write_yaml_with_backup(transform_path, transform)
        calibration["common_frame"][hand] = {
            "calibrated": True,
            "method": "live_baton_pose_window",
            "input_topic": item.input_topic,
            "output_topic": item.output_topic,
            "start_from_common": _to_mapping(item.start_from_common)["start_from_common"],
            "sample_frames": item.sample_frames,
            "position_std": round(item.position_std, 9),
            "updated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        }
    _mark_overall_status(calibration)
    data["calibration"] = calibration


def _backup_existing(path: Path) -> Path | None:
    if not path.exists():
        return None
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = path.with_name(f"{path.name}.{stamp}.bak")
    shutil.copy2(path, backup)
    return backup


def _write_yaml_with_backup(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    backup = _backup_existing(path)
    with path.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(data, fh, allow_unicode=True, sort_keys=False)
    if backup is not None:
        print(f"  已备份旧配置: {_short_path(backup)}")
    print(f"  已写入配置: {_short_path(path)}")


def _print_status(config: AppConfig) -> None:
    status = calibration_item_status(config)
    print()
    print("当前标定状态（common_frame 仅作历史兼容参考，不再作为主路线必需项）")
    for key, label in (
        ("gripper_left", "左手夹爪"),
        ("gripper_right", "右手夹爪"),
    ):
        print(f"  {label}: {'已完成' if status[key] else '未完成'}")
    print("  [注] 左右 common frame 标定已废弃，不再作为主路线必需项。")
    has_common = status.get("common_frame_left", False) or status.get("common_frame_right", False)
    if has_common:
        print("  [注] 旧 common frame 配置仍保留，但不会被主路线使用。")
    print(f"  总体: {'基本标定完成（gripper 就绪）' if config_is_calibrated(config) else '未完整标定（需完成夹爪标定）'}")


def _reload_config(output_path: Path, fallback_path: Path) -> AppConfig:
    return load_app_config(output_path if output_path.exists() else fallback_path)


def _save_gripper(config: AppConfig, output_path: Path, results: list[GripperSideCalibration]) -> AppConfig:
    data = _base_config_mapping(config)
    _apply_gripper_results(data, results)
    _write_yaml_with_backup(output_path, data)
    return load_app_config(output_path)


def _save_common_frame(config: AppConfig, output_path: Path, results: list[CommonFrameSideCalibration]) -> AppConfig:
    data = _base_config_mapping(config)
    _apply_common_frame_results(data, results, output_path.parent)
    _write_yaml_with_backup(output_path, data)
    return load_app_config(output_path)


def _save_frame_alignment_from_right(
    config: AppConfig,
    output_path: Path,
    result: CommonFrameRightCalibration,
) -> AppConfig:
    data = _base_config_mapping(config)
    _apply_frame_alignment_from_right(data, result)
    _write_yaml_with_backup(output_path, data)
    return load_app_config(output_path)


def _apply_frame_alignment_from_right(data: dict[str, Any], result: CommonFrameRightCalibration) -> None:
    calibration = _ensure_nested_status(data.get("calibration", {}))
    calibration["common_frame"]["right"] = {
        "calibrated": True,
        "method": "live_baton_pose_window_frame_alignment",
        "input_topic": result.input_topic,
        "output_topic": result.output_topic,
        "t_right_start_common": _to_mapping_from_transform(result.t_right_start_common)["start_from_common"],
        "common_from_right_start": _to_mapping_from_transform(result.common_from_right_start)["start_from_common"],
        "sample_frames": result.sample_frames,
        "position_std": round(result.position_std, 9),
        "updated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
    }
    _mark_overall_status(calibration)
    data["calibration"] = calibration


def _find_open_port(start_port: int = 8765, host: str = "127.0.0.1") -> int:
    for port in range(start_port, start_port + 100):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind((host, port))
            except OSError:
                continue
            return port
    raise RuntimeError(f"无法在 {host}:{start_port}-{start_port + 99} 找到可用端口。")


def _sample_stats_to_summary(stats: LiveSampleStats, aruco_dict: str, marker_id_0: int, marker_id_1: int) -> dict[str, Any]:
    distances = _distances_for_pair(stats, aruco_dict, marker_id_0, marker_id_1)
    rate, std = _quality_check("当前步骤", stats, distances)
    return {
        "aruco_dict": aruco_dict,
        "marker_id_0": marker_id_0,
        "marker_id_1": marker_id_1,
        "median": float(np.median(np.asarray(distances, dtype=np.float64))),
        "rate": rate,
        "std": std,
        "frames": stats.sampled_frames,
    }


def _select_dictionary_and_ids_single(stats: LiveSampleStats) -> tuple[str, int, int]:
    best_name = ""
    best_score = -1
    for name in ARUCO_CANDIDATES:
        counts = stats.id_counts.get(name, Counter())
        if len(counts) < 2:
            continue
        score = sum(counts.values())
        if score > best_score:
            best_score = score
            best_name = name
    if not best_name:
        raise RuntimeError("当前步骤没有稳定识别到两个 ArUco marker。")
    top_ids = [marker_id for marker_id, _count in stats.id_counts[best_name].most_common(2)]
    return best_name, int(top_ids[0]), int(top_ids[1])


def _encode_jpeg(image: np.ndarray, quality: int = 82) -> bytes:
    ok, encoded = cv2.imencode(".jpg", image, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
    if not ok:
        raise RuntimeError("JPEG 编码失败。")
    return encoded.tobytes()


GRIPPER_STEPS = (
    ("left", "closed"),
    ("left", "open"),
    ("right", "closed"),
    ("right", "open"),
)
PHASE_LABELS = {
    "closed": "完全闭合",
    "open": "完全张开",
}


def _average_quaternion_xyzw(quaternions: list[tuple[float, float, float, float]]) -> tuple[float, float, float, float]:
    if not quaternions:
        raise RuntimeError("没有可用于平均的四元数样本。")
    aligned: list[np.ndarray] = []
    reference = np.asarray(quaternions[0], dtype=np.float64)
    for quat in quaternions:
        values = np.asarray(quat, dtype=np.float64)
        norm = float(np.linalg.norm(values))
        if norm == 0.0:
            raise RuntimeError("收到零四元数位姿样本。")
        values = values / norm
        if float(np.dot(values, reference)) < 0:
            values = -values
        aligned.append(values)
    accumulator = np.zeros((4, 4), dtype=np.float64)
    for values in aligned:
        accumulator += np.outer(values, values)
    eigenvalues, eigenvectors = np.linalg.eigh(accumulator)
    average = eigenvectors[:, int(np.argmax(eigenvalues))]
    if average[3] < 0:
        average = -average
    average = average / np.linalg.norm(average)
    return tuple(float(value) for value in average)


def _se3_inverse_xyzw(
    translation: tuple[float, float, float],
    rotation_xyzw: tuple[float, float, float, float],
) -> tuple[tuple[float, float, float], tuple[float, float, float, float]]:
    """Compute SE(3) inverse of (translation, quaternion_xyzw).

    For T = (t, R), T^(-1) = (-R^T * t, R^(-1)).
    Quaternion conjugate gives R^(-1) for unit quaternions.
    """
    qx, qy, qz, qw = rotation_xyzw
    tx, ty, tz = translation

    inv_qx, inv_qy, inv_qz, inv_qw = -qx, -qy, -qz, qw

    inv_tx = -(tx * (1 - 2 * (qy * qy + qz * qz)) + ty * 2 * (qx * qy + qz * qw) + tz * 2 * (qx * qz - qy * qw))
    inv_ty = -(tx * 2 * (qx * qy - qz * qw) + ty * (1 - 2 * (qx * qx + qz * qz)) + tz * 2 * (qy * qz + qx * qw))
    inv_tz = -(tx * 2 * (qx * qz + qy * qw) + ty * 2 * (qy * qz - qx * qw) + tz * (1 - 2 * (qx * qx + qy * qy)))

    return (inv_tx, inv_ty, inv_tz), (inv_qx, inv_qy, inv_qz, inv_qw)


class BrowserCalibrationSession:
    def __init__(
        self,
        config_path: Path,
        output_path: Path,
        config: AppConfig,
        subscriber: LiveImageSubscriber,
        process: ManagedGoProProcess,
    ) -> None:
        self.config_path = config_path
        self.output_path = output_path
        self.config = config
        self.subscriber = subscriber
        self.process = process
        self.dictionaries = _aruco_dictionaries()
        self.parameters = _detector_parameters()
        self.lock = threading.RLock()
        self.stop_event = threading.Event()
        self.mode = "home"
        self.gripper_index = 0
        self.step_status = "ready"
        self.error = ""
        self.message = ""
        self.current_detection: dict[str, Any] = {}
        self.sample_summaries: dict[str, dict[str, Any]] = {}
        self.common_hand = "left"
        self.common_status = "ready"
        self.last_heartbeat: float | None = None
        self.saw_browser = False
        self.force_stop_gopro = True
        self._spin_stop = threading.Event()
        self._spin_thread = threading.Thread(target=self._spin_loop, daemon=True)
        self._monitor_thread = threading.Thread(target=self._monitor_browser, daemon=True)
        self._sample_thread: threading.Thread | None = None

    def start_background_threads(self) -> None:
        self._spin_thread.start()
        self._monitor_thread.start()

    def close(self) -> None:
        self._spin_stop.set()
        if self._spin_thread.is_alive():
            self._spin_thread.join(timeout=2)

    def _spin_loop(self) -> None:
        while not self._spin_stop.is_set():
            try:
                self.subscriber.spin_once(0.03)
            except Exception as exc:  # noqa: BLE001 - keep browser service alive enough to show error.
                with self.lock:
                    self.error = f"ROS 图像订阅异常: {exc}"
                time.sleep(0.5)

    def _monitor_browser(self) -> None:
        while not self.stop_event.is_set():
            time.sleep(2)
            with self.lock:
                if self.saw_browser and self.last_heartbeat is not None:
                    stale = time.monotonic() - self.last_heartbeat > 30
                else:
                    stale = False
            if stale:
                with self.lock:
                    self.message = "浏览器页面已关闭，标定中心自动退出。"
                self.stop_event.set()
                return

    def heartbeat(self) -> None:
        with self.lock:
            self.saw_browser = True
            self.last_heartbeat = time.monotonic()

    def current_gripper_step(self) -> tuple[str, str]:
        index = min(self.gripper_index, len(GRIPPER_STEPS) - 1)
        return GRIPPER_STEPS[index]

    def state(self) -> dict[str, Any]:
        with self.lock:
            status = calibration_item_status(self.config)
            hand, phase = self.current_gripper_step()
            return {
                "mode": self.mode,
                "status": status,
                "is_calibrated": config_is_calibrated(self.config),
                "gripper": {
                    "index": self.gripper_index,
                    "total": len(GRIPPER_STEPS),
                    "hand": hand,
                    "hand_label": HAND_LABELS[hand],
                    "phase": phase,
                    "phase_label": PHASE_LABELS[phase],
                    "step_status": self.step_status,
                    "done": self.gripper_index >= len(GRIPPER_STEPS),
                },
                "common_frame": {
                    "hand": self.common_hand,
                    "hand_label": HAND_LABELS[self.common_hand],
                    "step_status": self.common_status,
                },
                "detection": self.current_detection,
                "message": self.message,
                "error": self.error,
                "topics": GOPRO_TOPICS,
                "log_path": _short_path(self.process.log_path) if self.process.log_path else "",
            }

    def set_mode(self, mode: str, hand: str | None = None) -> dict[str, Any]:
        with self.lock:
            self.error = ""
            self.message = ""
            if mode == "gripper":
                self.mode = "gripper"
                if self.gripper_index >= len(GRIPPER_STEPS):
                    self.gripper_index = 0
                self.step_status = "ready"
            elif mode == "common":
                if hand not in {"left", "right"}:
                    raise RuntimeError("common frame 标定必须指定 left 或 right。")
                self.mode = "common"
                self.common_hand = hand
                self.common_status = "ready"
                stream = _pose_for_hand(self.config.pose_streams, hand)
                self.message = (
                    f"【已废弃】common frame 标定已不再作为主路线必需项。\n"
                    f"请将 {HAND_LABELS[hand]} Baton Mini 放到 common frame 原点/标准姿态，\n"
                    f"然后点击开始采样。位姿 topic: {stream.input_topic}"
                )
            elif mode == "home":
                self.mode = "home"
            else:
                raise RuntimeError(f"未知模式: {mode}")
        return self.state()

    def retry_current_gripper_step(self) -> dict[str, Any]:
        with self.lock:
            hand, phase = self.current_gripper_step()
            self.sample_summaries.pop(f"{hand}:{phase}", None)
            self.step_status = "ready"
            self.error = ""
            self.message = "已重置当前步骤，可重新采样。"
        return self.state()

    def confirm_next_gripper_step(self) -> dict[str, Any]:
        with self.lock:
            if self.step_status != "sampled":
                raise RuntimeError("当前步骤还没有合格采样，不能进入下一步。")
            if self.gripper_index < len(GRIPPER_STEPS):
                self.gripper_index += 1
            self.step_status = "ready"
            self.error = ""
            if self.gripper_index >= len(GRIPPER_STEPS):
                self.message = "夹爪宽度标定已完成。"
                self.mode = "home"
            else:
                hand, phase = self.current_gripper_step()
                self.message = f"进入下一步：{HAND_LABELS[hand]}{PHASE_LABELS[phase]}。"
        return self.state()

    def start_gripper_sample(self) -> dict[str, Any]:
        with self.lock:
            if self.step_status == "sampling":
                raise RuntimeError("当前正在采样，请稍等。")
            if self.gripper_index >= len(GRIPPER_STEPS):
                raise RuntimeError("夹爪标定已经完成。")
            self.step_status = "sampling"
            self.error = ""
            self.message = "正在采样 2 秒，请保持夹爪姿态稳定。"
            self._sample_thread = threading.Thread(target=self._sample_current_gripper_step, daemon=True)
            self._sample_thread.start()
        return self.state()

    def _sample_current_gripper_step(self) -> None:
        hand, phase = self.current_gripper_step()
        try:
            stats = self._sample_stats(hand)
            aruco_dict, marker_id_0, marker_id_1 = _select_dictionary_and_ids_single(stats)
            summary = _sample_stats_to_summary(stats, aruco_dict, marker_id_0, marker_id_1)
            key = f"{hand}:{phase}"
            with self.lock:
                self.sample_summaries[key] = summary

            if phase == "open":
                self._save_completed_gripper_hand(hand)

            with self.lock:
                self.step_status = "sampled"
                self.error = ""
                self.message = (
                    f"{HAND_LABELS[hand]}{PHASE_LABELS[phase]}采样合格："
                    f"{summary['frames']} 帧，检测率 {summary['rate']:.0%}，波动 {summary['std']:.2f}px。"
                )
        except Exception as exc:  # noqa: BLE001 - report to browser.
            with self.lock:
                self.step_status = "failed"
                self.error = str(exc)
                self.message = "当前步骤采样不合格，请调整画面后重采。"

    def _sample_stats(self, hand: str) -> LiveSampleStats:
        deadline = time.monotonic() + SAMPLE_SECONDS
        detections: dict[str, list[dict[int, np.ndarray]]] = {name: [] for name in self.dictionaries}
        id_counts: dict[str, Counter[int]] = {name: Counter() for name in self.dictionaries}
        sampled_frames = 0
        last_seq: int | None = None
        last_fresh_image_time = time.monotonic()

        while time.monotonic() < deadline:
            frame = self.subscriber.latest_frame(hand, max_age_sec=FRESH_IMAGE_MAX_AGE_SEC)
            if frame is None:
                if time.monotonic() - last_fresh_image_time > LOST_IMAGE_TIMEOUT_SEC:
                    raise RuntimeError(f"{HAND_LABELS[hand]} GoPro 超过 {LOST_IMAGE_TIMEOUT_SEC:.0f} 秒没有新图像。")
                time.sleep(0.01)
                continue
            image, _stamp, seq = frame
            if last_seq == seq:
                time.sleep(0.005)
                continue
            last_seq = seq
            last_fresh_image_time = time.monotonic()
            sampled_frames += 1
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            for name, dictionary in self.dictionaries.items():
                corners, ids, _ = cv2.aruco.detectMarkers(gray, dictionary, parameters=self.parameters)
                if ids is None:
                    detections[name].append({})
                    continue
                centers: dict[int, np.ndarray] = {}
                for index, marker_id in enumerate(ids.flatten()):
                    marker_id = int(marker_id)
                    centers[marker_id] = np.mean(corners[index][0], axis=0)
                    id_counts[name][marker_id] += 1
                detections[name].append(centers)
        return LiveSampleStats(sampled_frames=sampled_frames, detections=detections, id_counts=id_counts)

    def _save_completed_gripper_hand(self, hand: str) -> None:
        closed = self.sample_summaries.get(f"{hand}:closed")
        opened = self.sample_summaries.get(f"{hand}:open")
        if closed is None or opened is None:
            raise RuntimeError("缺少闭合或张开采样结果，不能保存夹爪标定。")
        if (
            closed["aruco_dict"] != opened["aruco_dict"]
            or closed["marker_id_0"] != opened["marker_id_0"]
            or closed["marker_id_1"] != opened["marker_id_1"]
        ):
            raise RuntimeError("闭合和张开识别到的 ArUco 字典或 marker ID 不一致，请重采当前手。")
        if opened["median"] <= closed["median"]:
            raise RuntimeError("张开距离不大于闭合距离，请确认动作顺序和 marker 安装。")

        stream = _stream_for_hand(self.config.gripper_streams, hand)
        result = GripperSideCalibration(
            hand=hand,
            image_topic=stream.image_topic,
            output_topic=stream.output_topic,
            aruco_dict=str(closed["aruco_dict"]),
            marker_id_0=int(closed["marker_id_0"]),
            marker_id_1=int(closed["marker_id_1"]),
            marker_min=float(closed["median"]),
            marker_max=float(opened["median"]),
            closed_rate=float(closed["rate"]),
            open_rate=float(opened["rate"]),
            closed_std=float(closed["std"]),
            open_std=float(opened["std"]),
            closed_frames=int(closed["frames"]),
            open_frames=int(opened["frames"]),
        )
        with self.lock:
            self.config = _save_gripper(self.config, self.output_path, [result])

    def _capture_frame_locked(self, hand: str) -> np.ndarray:
        frame = self.subscriber.latest_frame(hand, max_age_sec=FRESH_IMAGE_MAX_AGE_SEC)
        if frame is None:
            raise RuntimeError(f"没有收到 {HAND_LABELS[hand]} GoPro 新图像。")
        return frame[0]

    def frame_jpeg(self) -> bytes:
        with self.lock:
            hand = self.common_hand if self.mode == "common" else self.current_gripper_step()[0]
            title = f"{HAND_LABELS[hand]} 实时画面"
        frame = self.subscriber.latest_frame(hand, max_age_sec=FRESH_IMAGE_MAX_AGE_SEC)
        if frame is None:
            image = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(image, "Waiting for fresh GoPro frame", (28, 240), cv2.FONT_HERSHEY_SIMPLEX, 0.85, (0, 0, 255), 2)
            return _encode_jpeg(image)
        image = frame[0]
        detection = _detect_markers(image, self.dictionaries, self.parameters)
        with self.lock:
            self.current_detection = {
                "aruco_dict": detection.aruco_dict,
                "ids": detection.ids,
                "distance_px": detection.distance_px,
            }
        return _encode_jpeg(_draw_detection_overlay(image, detection, title))

    def start_common_frame_sample(self) -> dict[str, Any]:
        with self.lock:
            if self.common_status == "sampling":
                raise RuntimeError("当前正在采样，请稍等。")
            self.common_status = "sampling"
            self.error = ""
            self.message = f"正在采样 {HAND_LABELS[self.common_hand]} Baton Mini 位姿 2 秒，请保持设备静止。"
            self._sample_thread = threading.Thread(target=self._sample_current_common_frame, daemon=True)
            self._sample_thread.start()
        return self.state()

    def _sample_current_common_frame(self) -> None:
        hand = self.common_hand
        stream = _pose_for_hand(self.config.pose_streams, hand)
        try:
            if hand == "right":
                result = self._sample_right_common_frame_pose(stream)
                with self.lock:
                    self.config = _save_frame_alignment_from_right(
                        self.config, self.output_path, result
                    )
                    self.common_status = "sampled"
                    self.error = ""
                    self.message = (
                        f"【已废弃】{HAND_LABELS[hand]} common frame 外参已生成："
                        f"{result.sample_frames} 帧，位置标准差 {result.position_std:.6g}。"
                        f"common_from_right_start 由 inverse(T_right_start_common) 计算。\n"
                        f"注意：此配置不再作为主路线必需项。"
                    )
            else:
                result = self._sample_common_frame_pose(hand, stream)
                with self.lock:
                    self.config = _save_common_frame(self.config, self.output_path, [result])
                    self.common_status = "sampled"
                    self.error = ""
                    self.message = (
                        f"{HAND_LABELS[hand]} common frame 已保存："
                        f"{result.sample_frames} 帧，位置标准差 {result.position_std:.6g}。"
                    )
        except Exception as exc:  # noqa: BLE001 - report to browser.
            with self.lock:
                self.common_status = "failed"
                self.error = str(exc)
                self.message = "common frame 采样失败，请确认 Baton Mini 位姿 topic 正在发布且设备保持静止。"

    def _sample_common_frame_pose(self, hand: str, stream: PoseStreamConfig) -> CommonFrameSideCalibration:
        deadline = time.monotonic() + SAMPLE_SECONDS
        positions: list[tuple[float, float, float]] = []
        quaternions: list[tuple[float, float, float, float]] = []
        last_seq: int | None = None
        last_fresh_pose_time = time.monotonic()

        while time.monotonic() < deadline:
            sample = self.subscriber.latest_pose(stream.input_topic, max_age_sec=FRESH_IMAGE_MAX_AGE_SEC)
            if sample is None:
                if time.monotonic() - last_fresh_pose_time > LOST_IMAGE_TIMEOUT_SEC:
                    raise RuntimeError(f"{stream.input_topic} 超过 {LOST_IMAGE_TIMEOUT_SEC:.0f} 秒没有新位姿。")
                time.sleep(0.01)
                continue
            pose, _stamp, seq = sample
            if last_seq == seq:
                time.sleep(0.005)
                continue
            last_seq = seq
            last_fresh_pose_time = time.monotonic()
            x, y, z, qx, qy, qz, qw = pose
            positions.append((x, y, z))
            quaternions.append((qx, qy, qz, qw))

        if len(positions) < MIN_SAMPLE_FRAMES:
            raise RuntimeError(f"{HAND_LABELS[hand]} 位姿采样帧数不足：{len(positions)} < {MIN_SAMPLE_FRAMES}")

        position_array = np.asarray(positions, dtype=np.float64)
        median_position = np.median(position_array, axis=0)
        position_std = float(np.mean(np.std(position_array, axis=0)))
        qx, qy, qz, qw = _average_quaternion_xyzw(quaternions)
        transform = TransformConfig(
            translation=Vector3Config(
                x=float(median_position[0]),
                y=float(median_position[1]),
                z=float(median_position[2]),
            ),
            rotation_xyzw=QuaternionConfig(qx=qx, qy=qy, qz=qz, qw=qw),
        )
        return CommonFrameSideCalibration(
            hand=hand,
            input_topic=stream.input_topic,
            output_topic=stream.output_topic,
            start_from_common=transform,
            sample_frames=len(positions),
            position_std=position_std,
        )

    def _sample_right_common_frame_pose(self, stream: PoseStreamConfig) -> CommonFrameRightCalibration:
        deadline = time.monotonic() + SAMPLE_SECONDS
        positions: list[tuple[float, float, float]] = []
        quaternions: list[tuple[float, float, float, float]] = []
        last_seq: int | None = None
        last_fresh_pose_time = time.monotonic()

        while time.monotonic() < deadline:
            sample = self.subscriber.latest_pose(stream.input_topic, max_age_sec=FRESH_IMAGE_MAX_AGE_SEC)
            if sample is None:
                if time.monotonic() - last_fresh_pose_time > LOST_IMAGE_TIMEOUT_SEC:
                    raise RuntimeError(f"{stream.input_topic} 超过 {LOST_IMAGE_TIMEOUT_SEC:.0f} 秒没有新位姿。")
                time.sleep(0.01)
                continue
            pose, _stamp, seq = sample
            if last_seq == seq:
                time.sleep(0.005)
                continue
            last_seq = seq
            last_fresh_pose_time = time.monotonic()
            x, y, z, qx, qy, qz, qw = pose
            positions.append((x, y, z))
            quaternions.append((qx, qy, qz, qw))

        if len(positions) < MIN_SAMPLE_FRAMES:
            raise RuntimeError(f"右手位姿采样帧数不足：{len(positions)} < {MIN_SAMPLE_FRAMES}")

        position_array = np.asarray(positions, dtype=np.float64)
        median_position = np.median(position_array, axis=0)
        position_std = float(np.mean(np.std(position_array, axis=0)))
        qx, qy, qz, qw = _average_quaternion_xyzw(quaternions)

        t_right_start_common = TransformConfig(
            translation=Vector3Config(
                x=float(median_position[0]),
                y=float(median_position[1]),
                z=float(median_position[2]),
            ),
            rotation_xyzw=QuaternionConfig(qx=qx, qy=qy, qz=qz, qw=qw),
        )

        inv_translation, inv_rotation = _se3_inverse_xyzw(
            (float(median_position[0]), float(median_position[1]), float(median_position[2])),
            (qx, qy, qz, qw),
        )
        common_from_right_start = TransformConfig(
            translation=Vector3Config(
                x=inv_translation[0],
                y=inv_translation[1],
                z=inv_translation[2],
            ),
            rotation_xyzw=QuaternionConfig(
                qx=inv_rotation[0],
                qy=inv_rotation[1],
                qz=inv_rotation[2],
                qw=inv_rotation[3],
            ),
        )

        return CommonFrameRightCalibration(
            input_topic=stream.input_topic,
            output_topic=stream.output_topic,
            sample_frames=len(positions),
            position_std=position_std,
            t_right_start_common=t_right_start_common,
            common_from_right_start=common_from_right_start,
        )

    def exit(self) -> dict[str, Any]:
        with self.lock:
            self.message = "正在退出标定中心。"
        self.stop_event.set()
        return self.state()


def _html_page() -> str:
    return r"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>数据清洗实时标定中心</title>
  <style>
    body { margin: 0; font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color: #18202a; background: #f5f7fa; }
    header { padding: 14px 20px; background: #18324a; color: white; display: flex; align-items: center; justify-content: space-between; }
    main { max-width: 1120px; margin: 0 auto; padding: 18px; }
    .grid { display: grid; grid-template-columns: 1.5fr 1fr; gap: 16px; align-items: start; }
    .panel { background: white; border: 1px solid #d8dee7; border-radius: 8px; padding: 14px; }
    .video { width: 100%; background: #111; border-radius: 6px; display: block; }
    button { border: 1px solid #b9c4d2; background: #fff; color: #1e2b38; border-radius: 6px; padding: 9px 12px; margin: 4px 4px 4px 0; cursor: pointer; font-size: 14px; }
    button.primary { background: #1264a3; border-color: #1264a3; color: white; }
    button.danger { background: #b42318; border-color: #b42318; color: white; }
    button:disabled { opacity: .45; cursor: not-allowed; }
    .status { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; margin: 10px 0; }
    .badge { padding: 8px; border-radius: 6px; background: #eef2f7; }
    .done { background: #e7f6ed; color: #176239; }
    .todo { background: #fff4e5; color: #8a4b00; }
    .message { white-space: pre-wrap; background: #eef6ff; border: 1px solid #cce4ff; border-radius: 6px; padding: 10px; margin: 10px 0; }
    .error { white-space: pre-wrap; background: #fff1f0; border: 1px solid #ffccc7; color: #a8071a; border-radius: 6px; padding: 10px; margin: 10px 0; }
    .muted { color: #64748b; font-size: 13px; }
    .hidden { display: none; }
    @media (max-width: 900px) { .grid { grid-template-columns: 1fr; } }
  </style>
</head>
<body>
<header>
  <strong>数据清洗实时标定中心</strong>
  <span id="overall">加载中</span>
</header>
<main>
  <div class="grid">
    <section class="panel">
      <img id="live" class="video" src="/frame.jpg" alt="GoPro 实时画面">
    </section>
    <section class="panel">
      <h3>标定状态</h3>
      <div class="status" id="status"></div>
      <div id="message" class="message hidden"></div>
      <div id="error" class="error hidden"></div>
      <h3>操作</h3>
      <div id="homeControls">
        <button class="primary" onclick="setMode('gripper')">夹爪宽度实时标定</button>
        <button onclick="setMode('common','left')">左手 common frame 标定（已废弃）</button>
        <button onclick="setMode('common','right')">右手 common frame 标定（已废弃）</button>
        <button onclick="setMode('home')">查看状态</button>
        <button class="danger" onclick="exitWizard()">退出标定中心</button>
      </div>
      <div id="gripperControls" class="hidden">
        <h4 id="gripperTitle"></h4>
        <p class="muted" id="gripperHint"></p>
        <button class="primary" id="sampleBtn" onclick="sampleGripper()">开始采样</button>
        <button onclick="retryGripper()">重采当前步</button>
        <button id="nextBtn" onclick="nextGripper()">确认并进入下一步</button>
        <button onclick="setMode('home')">返回中心</button>
      </div>
      <div id="commonControls" class="hidden">
        <h4 id="commonTitle"></h4>
        <p class="muted">【已废弃】common frame 标定不再作为主路线必需项。新路线改为用户直接输入 work_frame_in_arm_base_pose。此功能保留仅用于历史兼容。</p>
        <button class="primary" id="commonSampleBtn" onclick="sampleCommon()">开始采样并保存</button>
        <button onclick="setMode('home')">返回中心</button>
      </div>
      <h3>检测信息</h3>
      <pre id="detect" class="muted"></pre>
      <p class="muted">页面仅连接本机 127.0.0.1；关闭页面后服务会自动退出。</p>
    </section>
  </div>
</main>
<script>
let state = null;

async function api(path, body = {}) {
  const res = await fetch(path, {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body)});
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || '请求失败');
  state = data;
  render();
  return data;
}
async function poll() {
  try {
    const res = await fetch('/state');
    state = await res.json();
    render();
  } catch (e) {}
}
async function heartbeat() { try { await fetch('/api/heartbeat', {method: 'POST'}); } catch (e) {} }
function refreshImages() {
  if (!state) return;
  document.getElementById('live').src = '/frame.jpg?t=' + Date.now();
}
function render() {
  if (!state) return;
  document.getElementById('overall').textContent = state.is_calibrated ? '夹爪已标定' : '未完整标定';
  const labels = {gripper_left:'左手夹爪', gripper_right:'右手夹爪', common_frame_left:'左手 common frame（已废弃）', common_frame_right:'右手 common frame（已废弃）'};
  document.getElementById('status').innerHTML = Object.keys(labels).map(k => `<div class="badge ${state.status[k] ? 'done' : 'todo'}">${labels[k]}：${state.status[k] ? '已完成' : '未完成'}</div>`).join('');
  const msg = document.getElementById('message');
  msg.textContent = state.message || '';
  msg.classList.toggle('hidden', !state.message);
  const err = document.getElementById('error');
  err.textContent = state.error || '';
  err.classList.toggle('hidden', !state.error);
  document.getElementById('detect').textContent = JSON.stringify(state.detection || {}, null, 2);
  document.getElementById('homeControls').classList.toggle('hidden', state.mode !== 'home');
  document.getElementById('gripperControls').classList.toggle('hidden', state.mode !== 'gripper');
  document.getElementById('commonControls').classList.toggle('hidden', state.mode !== 'common');
  if (state.mode === 'gripper') {
    document.getElementById('gripperTitle').textContent = `${state.gripper.hand_label}${state.gripper.phase_label} (${Math.min(state.gripper.index + 1, state.gripper.total)}/${state.gripper.total})`;
    document.getElementById('gripperHint').textContent = state.gripper.done ? '夹爪标定已完成。' : '摆好动作后点击“开始采样”，采样 2 秒内请保持稳定。';
    document.getElementById('sampleBtn').disabled = state.gripper.step_status === 'sampling' || state.gripper.done;
    document.getElementById('nextBtn').disabled = state.gripper.step_status !== 'sampled';
  }
  if (state.mode === 'common') {
    document.getElementById('commonTitle').textContent = `${state.common_frame.hand_label} common frame 标定`;
    document.getElementById('commonSampleBtn').disabled = state.common_frame.step_status === 'sampling';
  }
}
async function setMode(mode, hand=null) {
  await api('/api/mode', {mode, hand});
}
async function sampleGripper() { await api('/api/gripper/sample'); }
async function retryGripper() { await api('/api/gripper/retry'); }
async function nextGripper() { await api('/api/gripper/next'); }
async function sampleCommon() { await api('/api/common/sample'); }
async function exitWizard() { await api('/api/exit'); document.body.innerHTML = '<main><h2>标定中心已退出</h2></main>'; }
setInterval(poll, 500);
setInterval(refreshImages, 250);
setInterval(heartbeat, 2000);
poll();
heartbeat();
</script>
</body>
</html>"""


class CalibrationHttpServer(ThreadingHTTPServer):
    def __init__(self, server_address: tuple[str, int], handler_class: type[BaseHTTPRequestHandler], session: BrowserCalibrationSession):
        super().__init__(server_address, handler_class)
        self.session = session


class CalibrationRequestHandler(BaseHTTPRequestHandler):
    server: CalibrationHttpServer

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002 - stdlib signature.
        return

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        try:
            if parsed.path == "/":
                self._send_bytes(_html_page().encode("utf-8"), "text/html; charset=utf-8")
            elif parsed.path == "/state":
                self._send_json(self.server.session.state())
            elif parsed.path == "/frame.jpg":
                self._send_bytes(self.server.session.frame_jpeg(), "image/jpeg")
            else:
                self.send_error(HTTPStatus.NOT_FOUND, "not found")
        except Exception as exc:  # noqa: BLE001 - return browser-readable errors.
            self._send_json({"error": str(exc)}, status=500)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        try:
            body = self._read_json()
            if parsed.path == "/api/heartbeat":
                self.server.session.heartbeat()
                self._send_json({"ok": True})
            elif parsed.path == "/api/mode":
                self._send_json(self.server.session.set_mode(str(body.get("mode", "home")), body.get("hand")))
            elif parsed.path == "/api/gripper/sample":
                self._send_json(self.server.session.start_gripper_sample())
            elif parsed.path == "/api/gripper/retry":
                self._send_json(self.server.session.retry_current_gripper_step())
            elif parsed.path == "/api/gripper/next":
                self._send_json(self.server.session.confirm_next_gripper_step())
            elif parsed.path == "/api/common/sample":
                self._send_json(self.server.session.start_common_frame_sample())
            elif parsed.path == "/api/exit":
                self._send_json(self.server.session.exit())
            else:
                self.send_error(HTTPStatus.NOT_FOUND, "not found")
        except Exception as exc:  # noqa: BLE001 - return browser-readable errors.
            self._send_json({"error": str(exc)}, status=400)

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            return {}
        data = self.rfile.read(length)
        return json.loads(data.decode("utf-8"))

    def _send_json(self, data: dict[str, Any], status: int = 200) -> None:
        payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self._send_bytes(payload, "application/json; charset=utf-8", status=status)

    def _send_bytes(self, payload: bytes, content_type: str, status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(payload)


def _open_browser(url: str) -> None:
    try:
        webbrowser.open(url, new=2)
    except Exception:
        pass


def _wait_until_not_sampling(session: BrowserCalibrationSession) -> None:
    while True:
        state = session.state()
        if state["gripper"]["step_status"] != "sampling":
            return
        time.sleep(0.1)


def _terminal_gripper_fallback(session: BrowserCalibrationSession) -> None:
    print()
    print("进入夹爪宽度终端兜底流程。common frame 标定仍需浏览器页面。")
    session.set_mode("gripper")
    while True:
        state = session.state()
        gripper = state["gripper"]
        if gripper["done"]:
            print("夹爪宽度标定已完成。")
            return
        print()
        print(f"{gripper['hand_label']}{gripper['phase_label']} ({gripper['index'] + 1}/{gripper['total']})")
        print("请摆好夹爪动作并保证两个 ArUco marker 在画面内。")
        answer = input("按 Enter 开始采样，输入 q 返回浏览器服务等待: ").strip().lower()
        if answer == "q":
            return
        session.start_gripper_sample()
        _wait_until_not_sampling(session)
        state = session.state()
        if state["error"]:
            print(f"采样不合格: {state['error']}")
            session.retry_current_gripper_step()
            continue
        print(state["message"])
        input("按 Enter 确认并进入下一步: ")
        session.confirm_next_gripper_step()



def _calibration_center_menu() -> str:
    print()
    print("标定中心")
    print("  1  夹爪宽度实时标定")
    print("  2  [已废弃] common frame 位姿标定")
    print("  3  查看当前标定状态")
    print("  q  返回/退出")
    return input("选择: ").strip().lower()


def _finish_gopro_process(process: ManagedGoProProcess, *, force_stop: bool = False) -> None:
    if not process.started_by_wizard:
        return
    if force_stop:
        print()
        print("正在停止本向导启动的 GoPro 节点 ...")
        process.stop()
        print("  已停止 GoPro 节点。")
        return
    print()
    answer = input("GoPro 节点是本向导自动启动的，是否保留继续运行？[Y/n]: ").strip().lower()
    if answer in {"n", "no"}:
        process.stop()
        print("  已停止本向导启动的 GoPro 节点。")
    else:
        print("  已保留 GoPro 节点。后续可按 Ctrl+C 停止启动该节点的终端，或运行 cleanup_ros_residue.sh 清理。")


def run_calibration_wizard(
    config_path: str | Path,
    *,
    output_path: str | Path = DEFAULT_OUTPUT_CONFIG,
) -> int:
    config_path = Path(config_path)
    output_path = Path(output_path)
    config = _reload_config(output_path, config_path)

    print("数据清洗实时标定中心")
    print(f"  当前基础配置: {_short_path(config_path)}")
    print(f"  标定配置输出: {_short_path(output_path)}")
    print("  夹爪标定订阅: /gopro_left/image_raw, /gopro_right/image_raw")
    print("  common frame 标定订阅: pose_streams 中的左右 Baton Mini odometry topic")
    print("  [注] common frame 标定已废弃，新路线使用 work_frame_in_arm_base_pose")
    print("  交互方式: 浏览器向导，OpenCV 仅做后台 ArUco 检测。")

    process = ManagedGoProProcess(None)
    subscriber: LiveImageSubscriber | None = None
    session: BrowserCalibrationSession | None = None
    server: CalibrationHttpServer | None = None
    server_thread: threading.Thread | None = None
    force_stop_gopro = False
    try:
        subscriber = LiveImageSubscriber(GOPRO_TOPICS, config.pose_streams)
        try:
            process = _ensure_gopro_topics(subscriber)
        except Exception as exc:  # noqa: BLE001 - common-frame calibration can still run.
            print(f"  GoPro 图像未就绪：{exc}")
            print("  可继续使用 common frame 标定；夹爪宽度标定需要 GoPro 图像。")
            process = ManagedGoProProcess(None)
        session = BrowserCalibrationSession(config_path, output_path, config, subscriber, process)
        session.start_background_threads()
        port = _find_open_port()
        server = CalibrationHttpServer(("127.0.0.1", port), CalibrationRequestHandler, session)
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()
        url = f"http://127.0.0.1:{port}"
        print()
        print("浏览器标定页面已启动")
        print(f"  {url}")
        print("  如果浏览器没有自动打开，请复制上面的地址到浏览器。")
        print("  浏览器不可用时，可在本终端输入 g 回车，进入夹爪标定终端兜底流程。")
        print("  退出页面或按 Ctrl+C 会停止本向导启动的 GoPro 节点。")
        _open_browser(url)
        while not session.stop_event.is_set():
            if sys.stdin.isatty():
                readable, _writable, _error = select.select([sys.stdin], [], [], 0)
                if readable:
                    command = sys.stdin.readline().strip().lower()
                    if command == "g":
                        _terminal_gripper_fallback(session)
            time.sleep(0.2)
        if session.message:
            print(session.message)
        return 0
    except KeyboardInterrupt:
        print()
        print("标定已中断，已完成并写入的配置会保留。")
        force_stop_gopro = True
        return 130
    except Exception as exc:  # noqa: BLE001 - wizard stays user-facing.
        print()
        print(f"标定失败：{exc}")
        force_stop_gopro = True
        return 1
    finally:
        if server is not None:
            server.shutdown()
            server.server_close()
        if server_thread is not None and server_thread.is_alive():
            server_thread.join(timeout=2)
        if session is not None:
            session.close()
        if subscriber is not None:
            subscriber.close()
        _finish_gopro_process(process, force_stop=True if process.started_by_wizard else force_stop_gopro)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="实时 GoPro 数据清洗标定中心。")
    parser.add_argument("--config", default=str(WORKSPACE_DIR / "config/data_clean/data_clean_smoke_test.yaml"))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT_CONFIG))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    return run_calibration_wizard(args.config, output_path=args.output)


if __name__ == "__main__":
    raise SystemExit(main())
