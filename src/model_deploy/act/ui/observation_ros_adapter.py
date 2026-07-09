"""ObservationRosAdapter — ROS observation message → RAM value bridge.

Converts incoming ROS Image, Pose, and gripper-state messages into RAM
values consumable by the service layer (ObservationCollector), triggers
snapshot assembly, and writes ready snapshots into ObservationBuffer.

Lazy ROS import: the module is importable without rclpy installed.
Real subscription creation is marked BLOCKED_ENV when ROS is absent.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import numpy as np

from model_deploy.act.runtime.observation_buffer import ObservationBuffer
from model_deploy.act.service.image_preprocess import (
    ImageConfig,
    preprocess_observation_image,
)
from model_deploy.act.service.observation_collector import ObservationCollector

_logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Lazy ROS import
# ---------------------------------------------------------------------------

_ROS_AVAILABLE: bool = False
try:
    import rclpy  # noqa: F401
    from sensor_msgs.msg import CompressedImage, Image  # noqa: F401
    from geometry_msgs.msg import Pose  # noqa: F401

    _ROS_AVAILABLE = True
except ImportError:  # pragma: no cover
    pass


# ---------------------------------------------------------------------------
# Adapter
# ---------------------------------------------------------------------------


class ObservationRosAdapter:
    """ROS callback → service/runtime bridge for observation topics.

    Typical construction::

        adapter = ObservationRosAdapter(collector, buffer, config)
        # Later, when the ROS node is ready:
        adapter.create_subscriptions(node)

    Parameters:
        collector:         ObservationCollector instance (service layer).
        buffer:            ObservationBuffer instance (runtime layer).
        config:            Dict-like with ``topics.observation`` and
                           ``image`` config sections.
        max_age_s:         Default freshness timeout for snapshots (seconds).
    """

    # pylint: disable=too-many-instance-attributes

    def __init__(
        self,
        collector: ObservationCollector,
        buffer: ObservationBuffer,
        config: Dict[str, Any] | None = None,
        max_age_s: float = 5.0,
    ) -> None:
        self._collector = collector
        self._buffer = buffer
        self._config: Dict[str, Any] = config or {}
        self._max_age_s = max_age_s
        self._env_blocked: bool = False
        self._subscriptions: list = []

    # ------------------------------------------------------------------
    # ROS subscription setup
    # ------------------------------------------------------------------

    def create_subscriptions(self, node: Any) -> None:
        """Create ROS subscriptions from config.

        If ROS packages are unavailable, records ``env_blocked`` and logs
        a warning instead of raising.
        """
        if not _ROS_AVAILABLE:
            self._env_blocked = True
            _logger.warning(
                "ObservationRosAdapter: ROS not available, skipping subscriptions."
            )
            return

        try:
            obs_topics = self._config.get("topics", {}).get("observation", {})

            # Image topics
            for cam_key, topic_name in obs_topics.get("images", {}).items():
                msg_type_name = obs_topics.get("image_msg_type", "Image")
                msg_type = CompressedImage if msg_type_name == "CompressedImage" else Image
                sub = node.create_subscription(
                    msg_type,
                    topic_name,
                    lambda msg, key=cam_key: self.handle_image(key, msg),
                    10,
                )
                self._subscriptions.append(sub)

            # TCP pose topics
            for side in ("left", "right"):
                topic_name = obs_topics.get(f"{side}_tcp_pose")
                if topic_name:
                    sub = node.create_subscription(
                        Pose,
                        topic_name,
                        lambda msg, s=side: self.handle_tcp_pose(s, msg),
                        10,
                    )
                    self._subscriptions.append(sub)

            # Gripper state topics
            for side in ("left", "right"):
                topic_name = obs_topics.get(f"{side}_gripper_state")
                if topic_name:
                    sub = node.create_subscription(
                        Pose,  # Use Pose as common message type
                        topic_name,
                        lambda msg, s=side: self.handle_gripper_state(s, msg),
                        10,
                    )
                    self._subscriptions.append(sub)

        except Exception:  # pragma: no cover
            self._env_blocked = True
            _logger.exception("ObservationRosAdapter: subscription creation failed.")

    # ------------------------------------------------------------------
    # Message decode
    # ------------------------------------------------------------------

    @staticmethod
    def decode_image_message(msg: Any) -> np.ndarray:
        """Decode a ROS Image or CompressedImage message into an RGB array.

        Args:
            msg: A ``sensor_msgs.msg.Image`` or ``.CompressedImage``.

        Returns:
            RGB ``np.ndarray`` of shape (H, W, 3) dtype uint8.

        Raises:
            ValueError: If the message encoding is unsupported.
        """
        # Try real ROS decode first
        msg_class = getattr(msg, "__class__", None)
        if msg_class is not None:
            cls_name = msg_class.__name__ if hasattr(msg_class, "__name__") else str(msg_class)
        else:
            cls_name = ""

        # Handle ROS Image: convert raw data to numpy array
        if hasattr(msg, "height") and hasattr(msg, "width") and hasattr(msg, "encoding"):
            h, w = msg.height, msg.width
            data: np.ndarray = np.frombuffer(msg.data, dtype=np.uint8)
            encoding: str = str(msg.encoding)

            if encoding in ("rgb8", "bgr8"):
                data = data.reshape((h, w, 3))
                if encoding == "bgr8":
                    data = data[..., ::-1].copy()  # BGR → RGB
            elif encoding == "mono8":
                data = data.reshape((h, w, 1))
                data = np.dstack([data, data, data])  # expand to 3 channels
            elif encoding == "16UC1":
                data = data.view(np.uint16).reshape((h, w, 1))
                # Normalize and expand
                data = (data.astype(np.float32) / data.max()).astype(np.uint8) * 255
                data = np.dstack([data, data, data])
                data = data.astype(np.uint8)
            else:
                raise ValueError(f"Unsupported image encoding: {encoding}")
            return data

        # Handle CompressedImage
        if hasattr(msg, "format") and hasattr(msg, "data"):
            fmt: str = str(getattr(msg, "format", ""))
            raw: bytes = bytes(msg.data)
            np_arr = np.frombuffer(raw, dtype=np.uint8)
            if fmt == "jpeg" or fmt == "png":
                try:
                    import cv2

                    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
                    if img is not None:
                        return img[..., ::-1].copy()  # BGR → RGB
                except ImportError:  # pragma: no cover
                    pass
            raise ValueError(f"Unsupported compressed format: {fmt}")

        raise ValueError(f"Cannot decode message of type {cls_name}")

    # ------------------------------------------------------------------
    # Callback handlers
    # ------------------------------------------------------------------

    def handle_image(self, name: str, msg: Any) -> None:
        """Decode *msg*, pre-process, and feed to collector."""
        try:
            image = self.decode_image_message(msg)
        except Exception as exc:
            _logger.warning("ObservationRosAdapter: decode %s failed: %s", name, exc)
            self._buffer.record_error(f"decode {name}: {exc}")
            return

        image_config_dict = self._config.get("image", {})
        image_config = ImageConfig(
            target_shape=(
                image_config_dict.get("target_height", image.shape[0]),
                image_config_dict.get("target_width", image.shape[1]),
                image_config_dict.get("target_channels", image.shape[2]),
            ),
            dtype=np.float32,
            resize_width=image_config_dict.get("resize_width"),
            resize_height=image_config_dict.get("resize_height"),
        )
        processed = preprocess_observation_image(image, image_config)
        self._collector.update_image(name, processed)
        self._try_publish_observation()

    def handle_tcp_pose(self, side: str, msg: Any) -> None:
        """Parse a ROS Pose message and update collector."""
        try:
            position = [
                float(msg.position.x),
                float(msg.position.y),
                float(msg.position.z),
            ]
            orientation = [
                float(msg.orientation.x),
                float(msg.orientation.y),
                float(msg.orientation.z),
                float(msg.orientation.w),
            ]
        except Exception as exc:
            _logger.warning("ObservationRosAdapter: pose parse %s failed: %s", side, exc)
            self._buffer.record_error(f"pose parse {side}: {exc}")
            return

        self._collector.update_tcp_pose(side, position, orientation)
        self._try_publish_observation()

    def handle_gripper_state(self, side: str, msg: Any) -> None:
        """Parse a gripper-state message and update collector."""
        try:
            # Try common attributes for gripper width
            width: float = 0.0
            if hasattr(msg, "width"):
                width = float(msg.width)
            elif hasattr(msg, "position"):
                width = float(msg.position)
            elif hasattr(msg, "data"):
                width = float(msg.data)
            else:
                raise ValueError(f"Cannot extract gripper width from {msg}")
        except Exception as exc:
            _logger.warning(
                "ObservationRosAdapter: gripper parse %s failed: %s", side, exc
            )
            self._buffer.record_error(f"gripper parse {side}: {exc}")
            return

        self._collector.update_gripper_state(side, width)
        self._try_publish_observation()

    # ------------------------------------------------------------------
    # Snapshot gate
    # ------------------------------------------------------------------

    def _try_publish_observation(self) -> bool:
        """Try to assemble a snapshot and write it to the buffer.

        Returns:
            ``True`` if a ready snapshot was written to the buffer.
        """
        snap = self._collector.snapshot(max_age_s=self._max_age_s)
        if snap is not None:
            self._buffer.set_observation(snap)
            return True

        missing = self._collector.missing_fields()
        if missing:
            self._buffer.record_missing_fields(missing)
        return False

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    @property
    def env_blocked(self) -> bool:
        """True when ROS was unavailable and subscriptions were skipped."""
        return self._env_blocked

    @property
    def subscription_count(self) -> int:
        """Number of active ROS subscriptions."""
        return len(self._subscriptions)
