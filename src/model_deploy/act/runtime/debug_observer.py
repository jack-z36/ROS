"""Debug Observer — 旁路采集 observation 数据，供 Web UI 展示。

设计原则：
- 不阻塞主推理流程
- 线程安全
- 故障不影响推理
"""

from __future__ import annotations

import threading
import time
from collections import deque
from typing import Optional

import numpy as np


class DebugObserver:
    """从 ObservationBuffer 旁路采集数据，缓存最新帧和数值。

    所有公开方法均有 try/except，绝不向调用方抛出异常。
    """

    def __init__(self, max_history: int = 300) -> None:
        """
        Args:
            max_history: 数值历史记录条数（约 30 秒 @ 10Hz）
        """
        self._lock = threading.Lock()
        self._latest_jpeg_left: Optional[bytes] = None
        self._latest_jpeg_right: Optional[bytes] = None
        self._latest_state: Optional[dict] = None
        self._state_history: deque = deque(maxlen=max_history)
        self._frame_count: int = 0
        self._last_capture_time: float = 0.0
        self._min_capture_interval: float = 0.1  # 10 FPS max

    # ------------------------------------------------------------------
    # Callback entry point
    # ------------------------------------------------------------------

    def on_observation(self, snapshot) -> None:
        """回调：当新的 observation 写入 ObservationBuffer 时调用。

        从 ObservationSnapshot 中提取：
          - images: Mapping[str, np.ndarray]  CHW float32 [0,1]
          - state:  ObservationState (left/right tcp pose + gripper width)

        图像会被转换为 HWC uint8 然后编码为 JPEG 缓存。
        任何异常均被静默吞掉，绝不影响主推理流程。
        """
        now = time.time()
        if now - self._last_capture_time < self._min_capture_interval:
            return  # 限频
        self._last_capture_time = now

        try:
            self._do_capture(snapshot, now)
        except Exception:
            pass  # Debug observer 不能影响主流程

    def _do_capture(self, snapshot, now: float) -> None:
        """内部提取逻辑（可能抛出，由调用方兜底）。"""
        import cv2

        # --- 提取图像 ---
        images = getattr(snapshot, "images", None)
        if images:
            for key, attr in [("left", "_latest_jpeg_left"), ("right", "_latest_jpeg_right")]:
                img = images.get(key)
                if img is not None and isinstance(img, np.ndarray):
                    jpeg_bytes = self._encode_chw_to_jpeg(img, cv2)
                    if jpeg_bytes is not None:
                        with self._lock:
                            setattr(self, attr, jpeg_bytes)

        # --- 提取状态数值 ---
        state_obj = getattr(snapshot, "state", None)
        if state_obj is not None:
            state = self._extract_state(state_obj, now)
            if state:
                with self._lock:
                    self._latest_state = state
                    self._state_history.append(dict(state))
                    self._frame_count += 1

    @staticmethod
    def _encode_chw_to_jpeg(img: np.ndarray, cv2) -> Optional[bytes]:
        """将 CHW float32 [0,1] 图像编码为 JPEG bytes。"""
        try:
            if img.ndim == 3 and img.shape[0] in (1, 3):
                # CHW → HWC
                hwc = np.ascontiguousarray(img.transpose(1, 2, 0))
            elif img.ndim == 3:
                hwc = img
            else:
                return None

            # float32 [0,1] → uint8 [0,255]
            if hwc.dtype == np.float32 or hwc.dtype == np.float64:
                hwc = np.clip(hwc * 255.0, 0, 255).astype(np.uint8)

            # 单通道 → 三通道
            if hwc.ndim == 3 and hwc.shape[2] == 1:
                hwc = np.concatenate([hwc, hwc, hwc], axis=2)

            # RGB → BGR (OpenCV 期望 BGR)
            if hwc.ndim == 3 and hwc.shape[2] == 3:
                hwc = hwc[:, :, ::-1]

            ok, buf = cv2.imencode(".jpg", hwc, [cv2.IMWRITE_JPEG_QUALITY, 70])
            if ok:
                return buf.tobytes()
        except Exception:
            pass
        return None

    @staticmethod
    def _extract_state(state_obj, now: float) -> Optional[dict]:
        """从 ObservationState 提取可读的状态 dict。"""
        try:
            left_pos = getattr(state_obj, "left_tcp_position", None)
            left_ori = getattr(state_obj, "left_tcp_orientation", None)
            right_pos = getattr(state_obj, "right_tcp_position", None)
            right_ori = getattr(state_obj, "right_tcp_orientation", None)
            left_grip = getattr(state_obj, "left_gripper_width", 0.0)
            right_grip = getattr(state_obj, "right_gripper_width", 0.0)

            def _to_list(arr):
                if arr is None:
                    return []
                if isinstance(arr, np.ndarray):
                    return arr.tolist()
                return list(arr)

            return {
                "left_tcp_position": _to_list(left_pos),
                "left_tcp_orientation": _to_list(left_ori),
                "left_gripper": float(left_grip),
                "right_tcp_position": _to_list(right_pos),
                "right_tcp_orientation": _to_list(right_ori),
                "right_gripper": float(right_grip),
                "timestamp": now,
            }
        except Exception:
            return None

    # ------------------------------------------------------------------
    # Public read API (all thread-safe, never raise)
    # ------------------------------------------------------------------

    def get_latest_jpeg(self, side: str) -> Optional[bytes]:
        """获取最新的 JPEG 图像帧。side: 'left' 或 'right'"""
        try:
            with self._lock:
                if side == "left":
                    return self._latest_jpeg_left
                elif side == "right":
                    return self._latest_jpeg_right
        except Exception:
            pass
        return None

    def get_latest_state(self) -> Optional[dict]:
        """获取最新的状态数值。"""
        try:
            with self._lock:
                return dict(self._latest_state) if self._latest_state else None
        except Exception:
            return None

    def get_state_history(self, n: int = 50) -> list:
        """获取最近 n 条状态历史。"""
        try:
            with self._lock:
                return list(self._state_history)[-n:]
        except Exception:
            return []

    def get_stats(self) -> dict:
        """获取 observer 统计信息。"""
        try:
            with self._lock:
                return {
                    "frame_count": self._frame_count,
                    "history_size": len(self._state_history),
                }
        except Exception:
            return {"frame_count": 0, "history_size": 0}
