"""ObservationRosAdapter — ROS observation message → RAM value bridge (deploy_057).

Converts incoming ROS Image / CompressedImage / Pose / gripper-state messages
into RAM values consumable by the service layer (``ObservationCollector``),
triggers snapshot assembly, and writes ready snapshots into ``ObservationBuffer``.

Typed contract (no raw Dict config):
- Consumes a frozen ``DeployConfig`` and the canonical ``PolicyInputSpec``.
- Produces owned ``float32`` CHW images in ``[0, 1]`` exactly matching the
  spec's ``image_shapes``.
- Camera keys are validated against the spec (fail-fast on mismatch).
- Gripper message type and scalar decoder are kept consistent; the real
  gripper ROS topology is unknown and recorded (not masked as a local success).

Lazy ROS import: the module is importable without rclpy installed.  When rclpy
is absent, ``create_subscriptions`` records ``env_blocked``.  All other errors
(config / decoder) propagate — they are never downgraded to ``env_blocked``.
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Mapping, Optional, Tuple

import numpy as np

from model_deploy.act.config.schema import DeployConfig
from model_deploy.act.repo.act_runtime_resources import PolicyInputSpec
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
    from geometry_msgs.msg import Pose  # noqa: F401
    from rclpy.qos import qos_profile_sensor_data  # noqa: F401
    from sensor_msgs.msg import CompressedImage, Image  # noqa: F401

    _ROS_AVAILABLE = True
except ImportError:  # pragma: no cover
    Pose = None  # type: ignore[assignment]
    qos_profile_sensor_data = None  # type: ignore[assignment]
    Image = None  # type: ignore[assignment]
    CompressedImage = None  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# Gripper scalar decoder (consistent with the subscribed message type)
# ---------------------------------------------------------------------------


def decode_gripper_width(msg: Any) -> float:
    """Decode a scalar gripper width from a gripper-state message.

    The subscribed message type for gripper topics is ``geometry_msgs/Pose``
    (a placeholder; the real hardware topology is unknown — see
    ``gripper_topology_unknown``).  This decoder reads the scalar width from a
    consistent source:

    - ``msg.width`` (a scalar width attribute, if present),
    - otherwise ``msg.position.x`` (Pose layout),
    - otherwise ``msg.data`` (numeric scalar).

    Raises:
        ValueError: If no scalar width can be extracted (the local FAIL is
            recorded, never masked).
    """
    if hasattr(msg, "width") and msg.width is not None:
        return float(msg.width)
    if hasattr(msg, "position") and msg.position is not None:
        return float(msg.position.x)
    if hasattr(msg, "data") and msg.data is not None:
        return float(msg.data)
    raise ValueError(f"Cannot extract gripper width from {type(msg).__name__}")


# ---------------------------------------------------------------------------
# Adapter
# ---------------------------------------------------------------------------


class ObservationRosAdapter:
    """ROS callback → service/runtime bridge for observation topics.

    Typed construction (deploy_057)::

        adapter = ObservationRosAdapter(
            collector=collector,
            buffer=buffer,
            config=deploy_config,
            input_spec=policy_input_spec,
            max_age_s=deploy_config.runtime.max_observation_age_sec,
            monotonic_clock=monotonic_clock,
        )
        adapter.create_subscriptions(node)

    Parameters:
        collector:         ObservationCollector instance (service layer).
        buffer:            ObservationBuffer instance (runtime layer).
        config:            Frozen ``DeployConfig`` (topics + image settings).
        input_spec:        Frozen canonical ``PolicyInputSpec`` (camera keys,
                           image shapes / layout / dtype / range).
        max_age_s:         Default freshness timeout for snapshots (seconds).
        monotonic_clock:   Shared monotonic clock (same domain as collector /
                           buffer; deploy_057 / P0-07).
    """

    # pylint: disable=too-many-instance-attributes

    def __init__(
        self,
        *,
        collector: ObservationCollector,
        buffer: ObservationBuffer,
        config: DeployConfig,
        input_spec: PolicyInputSpec,
        max_age_s: float = 5.0,
        monotonic_clock: Callable[[], float] | None = None,
    ) -> None:
        if not isinstance(collector, ObservationCollector):
            raise TypeError("collector must be an ObservationCollector")
        if not isinstance(buffer, ObservationBuffer):
            raise TypeError("buffer must be an ObservationBuffer")
        if not isinstance(config, DeployConfig):
            raise TypeError("config must be a DeployConfig")
        if not isinstance(input_spec, PolicyInputSpec):
            raise TypeError("input_spec must be a PolicyInputSpec")

        self._collector = collector
        self._buffer = buffer
        self._config = config
        self._input_spec = input_spec
        self._max_age_s = float(max_age_s)
        if monotonic_clock is None:
            import time

            self._monotonic_clock: Callable[[], float] = time.monotonic
        else:
            self._monotonic_clock = monotonic_clock

        self._env_blocked: bool = False
        self._subscriptions: list = []

        # Pre-resolved, spec-aligned lookups (fail-fast if inconsistent).
        self._image_topics: Mapping[str, str] = dict(config.topics.observation.image_topics)
        self._tcp_pose_topics: Mapping[str, str] = {
            "left": config.topics.observation.left_tcp_pose,
            "right": config.topics.observation.right_tcp_pose,
        }
        self._gripper_topics: Mapping[str, str] = {
            "left": config.topics.observation.left_gripper_state,
            "right": config.topics.observation.right_gripper_state,
        }

        # Per-camera expected CHW shape + HWC preprocess target (from spec).
        self._image_expected_shapes: Mapping[str, Tuple[int, int, int]] = {}
        self._image_target_shapes: Mapping[str, Tuple[int, int, int]] = {}
        for cam, shape in zip(input_spec.camera_keys, input_spec.image_shapes):
            self._image_expected_shapes[cam] = tuple(shape)  # (3, H, W) CHW
            self._image_target_shapes[cam] = (shape[1], shape[2], shape[0])  # (H, W, 3)

        # Gripper topology is not verified against real hardware.
        self.gripper_topology_unknown: bool = True

        # Validate camera-key alignment at construction (config error).
        config_cameras = set(self._image_topics.keys())
        spec_cameras = set(input_spec.camera_keys)
        if config_cameras != spec_cameras:
            raise ValueError(
                f"Observation camera keys mismatch: config has {sorted(config_cameras)} "
                f"but PolicyInputSpec requires {sorted(spec_cameras)}"
            )
        if len(input_spec.image_shapes) != len(input_spec.camera_keys):
            raise ValueError(
                "PolicyInputSpec.image_shapes length must match camera_keys"
            )

    # ------------------------------------------------------------------
    # ROS subscription setup
    # ------------------------------------------------------------------

    def create_subscriptions(self, node: Any) -> None:
        """Create ROS subscriptions after all RAM validation has passed.

        Callers (``build_observation_pipeline``) must have validated config /
        spec consistency before invoking this.  If rclpy is unavailable the
        method records ``env_blocked`` and returns.  Any other failure during
        creation rolls back already-created handles and re-raises — it is
        never downgraded to ``env_blocked``.
        """
        if not _ROS_AVAILABLE:
            self._env_blocked = True
            _logger.warning(
                "ObservationRosAdapter: ROS not available, skipping subscriptions."
            )
            return

        created: list = []
        try:
            # Image topics (raw or compressed, per config.image.transport).
            # 相机发布端（v4l2_camera 用 use_sensor_data_qos=true）是 BEST_EFFORT。
            # 若订阅侧用 RELIABLE（裸整数 10 的默认），DDS request-offer 不兼容，
            # 会建立连接但静默丢弃每一帧 → observation 永远缺数据。故图像订阅必须
            # 用 sensor_data（BEST_EFFORT, KEEP_LAST 5）匹配发布端（与
            # camera_health_node 的做法一致）。位姿/夹爪发布端是 RELIABLE，保持 10。
            msg_type = (
                CompressedImage if getattr(self._config.image, "transport", "raw") == "compressed"
                else Image
            )
            for cam_key, topic in self._image_topics.items():
                sub = node.create_subscription(
                    msg_type,
                    topic,
                    lambda msg, key=cam_key: self.handle_image(key, msg),
                    qos_profile_sensor_data,
                )
                created.append(sub)

            # TCP pose topics (Pose).
            for side, topic in self._tcp_pose_topics.items():
                if not topic:
                    continue
                sub = node.create_subscription(
                    Pose,
                    topic,
                    lambda msg, s=side: self.handle_tcp_pose(s, msg),
                    10,
                )
                created.append(sub)

            # Gripper state topics (Pose placeholder; topology unknown).
            for side, topic in self._gripper_topics.items():
                if not topic:
                    continue
                sub = node.create_subscription(
                    Pose,
                    topic,
                    lambda msg, s=side: self.handle_gripper_state(s, msg),
                    10,
                )
                created.append(sub)

            self._subscriptions = created
        except Exception:
            # Roll back any partial subscription handles, then propagate.
            self._rollback_subscriptions(created)
            self._subscriptions = []
            _logger.exception("ObservationRosAdapter: subscription creation failed.")
            raise

    def _rollback_subscriptions(self, created: list) -> None:
        """Best-effort destroy of partially-created subscription handles."""
        for sub in created:
            destroy = getattr(sub, "destroy", None)
            if callable(destroy):
                try:
                    destroy()
                except Exception:  # pragma: no cover - defensive
                    _logger.debug("Subscription destroy failed; ignoring.")

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
        """Decode *msg*, pre-process to CHW float32 [0,1], feed collector."""
        expected = self._image_expected_shapes.get(name)
        if expected is None:
            _logger.warning("ObservationRosAdapter: unknown camera '%s'", name)
            self._buffer.record_error(f"unknown camera {name}")
            return

        try:
            image = self.decode_image_message(msg)
        except Exception as exc:
            _logger.warning("ObservationRosAdapter: decode %s failed: %s", name, exc)
            self._buffer.record_error(f"decode {name}: {exc}")
            return

        target = self._image_target_shapes[name]
        image_config = ImageConfig(target_shape=target, dtype=np.float32)
        try:
            processed = preprocess_observation_image(image, image_config)
        except Exception as exc:
            _logger.warning("ObservationRosAdapter: preprocess %s failed: %s", name, exc)
            self._buffer.record_error(f"preprocess {name}: {exc}")
            return

        # Convert HWC -> CHW to match the policy input contract.
        processed_chw = np.ascontiguousarray(processed.transpose(2, 0, 1))

        # Boundary validation against the spec (fail-fast, not downstream).
        if processed_chw.shape != expected:
            _logger.warning(
                "ObservationRosAdapter: %s shape %s != spec %s",
                name, processed_chw.shape, expected,
            )
            self._buffer.record_error(
                f"image {name} shape {processed_chw.shape} != spec {expected}"
            )
            return
        if not np.isfinite(processed_chw).all() or processed_chw.min() < 0.0 or processed_chw.max() > 1.0:
            _logger.warning("ObservationRosAdapter: %s out of [0,1] range", name)
            self._buffer.record_error(f"image {name} out of [0,1] range")
            return

        self._collector.update_image(name, processed_chw)
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
        """Parse a gripper-state message and update collector.

        The gripper message type / decoder are kept consistent (Pose ->
        ``decode_gripper_width``).  The real topology is unknown and recorded
        via ``gripper_topology_unknown``; a decode failure is recorded as a
        local error and never masked as success.
        """
        try:
            width = decode_gripper_width(msg)
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
