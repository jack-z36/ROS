"""Tests for ObservationRosAdapter — mock callbacks, decode, import."""

import threading
import time
from typing import Any
from unittest.mock import MagicMock

import numpy as np
import pytest

from model_deploy.act.ui.observation_ros_adapter import (
    ObservationRosAdapter,
    _ROS_AVAILABLE,
)
from model_deploy.act.runtime.observation_buffer import ObservationBuffer
from model_deploy.act.service.observation_collector import ObservationCollector


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


REQUIRED_IMAGE_KEYS = ["cam_high", "cam_wrist"]
REQUIRED_STATE_FIELDS = [
    "left_tcp_position", "left_tcp_orientation", "left_gripper_width",
    "right_tcp_position", "right_tcp_orientation", "right_gripper_width",
]


def _new_collector() -> ObservationCollector:
    return ObservationCollector(
        required_image_keys=REQUIRED_IMAGE_KEYS,
        required_state_fields=REQUIRED_STATE_FIELDS,
    )


def _new_buffer() -> ObservationBuffer:
    return ObservationBuffer()


def _new_adapter() -> ObservationRosAdapter:
    return ObservationRosAdapter(
        collector=_new_collector(),
        buffer=_new_buffer(),
        config={},
        max_age_s=5.0,
    )


# ---- Mock message helpers ----


class MockImageMsg:
    """Mock a sensor_msgs.msg.Image with raw byte data."""

    def __init__(self, h: int = 480, w: int = 640, encoding: str = "rgb8") -> None:
        self.height = h
        self.width = w
        self.encoding = encoding
        if encoding == "rgb8":
            self.data = np.random.randint(0, 256, (h, w, 3), dtype=np.uint8).tobytes()
        elif encoding == "bgr8":
            self.data = np.random.randint(0, 256, (h, w, 3), dtype=np.uint8).tobytes()
        elif encoding == "mono8":
            self.data = np.random.randint(0, 256, (h, w, 1), dtype=np.uint8).tobytes()
        else:
            self.data = b""
        self.header = MagicMock()
        self._is_bigendian = 0
        self.step = w * 3
        self.__class__.__name__ = "Image"


class MockCompressedImageMsg:
    """Mock a sensor_msgs.msg.CompressedImage."""

    def __init__(self, format_str: str = "jpeg") -> None:
        self.format = format_str
        # Minimal JPEG header
        self.data = (
            b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
            b"\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t"
            b"\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a"
            b"\x1f\x1e\x1d\x1a\x1c\x1c $.' \",#\x1c\x1c(7),01444\x1f'9=82<.342"
            b"\xff\xc0\x00\x11\x08\x00\x01\x00\x01\x03\x01\"\x00\x02\x11\x01"
            b"\x03\x11\x01\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01"
            b"\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05"
            b"\x06\x07\x08\t\n\x0b\xff\xc4\x00\xb5\x10\x00\x02\x01\x03\x03"
            b"\x02\x04\x03\x05\x05\x04\x04\x00\x00\x01}\x01\x02\x03\x00\x04"
            b"\x11\x05\x12!1A\x06\x13Qa\x07\"q\x142\x81\x91\xa1\x08#B\xb1"
            b"\xc1\x15R\xd1\xf0$3br\x82\x90\n\x16\x17\x18\x19\x1a%&'()*456789"
            b":CDEFGHIJSTUVWXYZcdefghijstuvwxyz\x83\x84\x85\x86\x87\x88\x89"
            b"\x8a\x92\x93\x94\x95\x96\x97\x98\x99\x9a\xa2\xa3\xa4\xa5\xa6"
            b"\xa7\xa8\xa9\xaa\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xc2\xc3"
            b"\xc4\xc5\xc6\xc7\xc8\xc9\xca\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9"
            b"\xda\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xf1\xf2\xf3\xf4"
            b"\xf5\xf6\xf7\xf8\xf9\xfa\xff\xd9"
        )
        self.__class__.__name__ = "CompressedImage"


class MockPoseMsg:
    """Mock a geometry_msgs.msg.Pose."""

    def __init__(self, x: float = 0.1, y: float = 0.2, z: float = 0.3,
                 ox: float = 0.0, oy: float = 0.0, oz: float = 0.0, ow: float = 1.0) -> None:
        self.position = MagicMock()
        self.position.x = x
        self.position.y = y
        self.position.z = z
        self.orientation = MagicMock()
        self.orientation.x = ox
        self.orientation.y = oy
        self.orientation.z = oz
        self.orientation.w = ow
        self.__class__.__name__ = "Pose"


class MockGripperMsg:
    """Mock a gripper state message with width attribute."""

    def __init__(self, width: float = 0.05) -> None:
        self.width = width
        self.__class__.__name__ = "GripperState"


class MockNode:
    """Minimal mock ROS node."""

    def create_subscription(self, msg_type: type, topic: str,
                            callback: Any, qos: int) -> MagicMock:
        return MagicMock()


# ---------------------------------------------------------------------------
# Import without ROS
# ---------------------------------------------------------------------------


class TestImportWithoutROS:
    def test_import_without_ros(self) -> None:
        """Module must import without ROS packages (no ImportError)."""
        from model_deploy.act.ui import observation_ros_adapter as oa

        assert oa.ObservationRosAdapter is ObservationRosAdapter

    def test_env_blocked_when_no_ros(self) -> None:
        """create_subscriptions sets env_blocked when ROS is absent."""
        adapter = _new_adapter()
        adapter.create_subscriptions(MagicMock())
        if not _ROS_AVAILABLE:
            assert adapter.env_blocked is True


# ---------------------------------------------------------------------------
# decode_image_message
# ---------------------------------------------------------------------------


class TestDecodeImageMessage:
    def test_decode_image_rgb8(self) -> None:
        msg = MockImageMsg(480, 640, "rgb8")
        result = ObservationRosAdapter.decode_image_message(msg)
        assert result.shape == (480, 640, 3)
        assert result.dtype == np.uint8

    def test_decode_image_bgr8(self) -> None:
        msg = MockImageMsg(480, 640, "bgr8")
        result = ObservationRosAdapter.decode_image_message(msg)
        assert result.shape == (480, 640, 3)
        assert result.dtype == np.uint8

    def test_decode_image_mono8(self) -> None:
        msg = MockImageMsg(480, 640, "mono8")
        result = ObservationRosAdapter.decode_image_message(msg)
        assert result.shape == (480, 640, 3)
        assert result.dtype == np.uint8

    def test_decode_compressed_jpeg(self) -> None:
        """Compressed JPEG decode requires cv2 — should raise if invalid or succeed."""
        msg = MockCompressedImageMsg("jpeg")
        try:
            result = ObservationRosAdapter.decode_image_message(msg)
            assert isinstance(result, np.ndarray)
            assert result.ndim == 3
        except ValueError as e:
            assert "Unsupported" in str(e) or "Cannot decode" in str(e)

    def test_decode_unknown_type_raises(self) -> None:
        """Unknown message type raises ValueError."""
        msg = MagicMock()
        msg.__class__ = MagicMock()
        msg.__class__.__name__ = "UnknownType"
        del msg.height  # Remove any chance of it looking like Image
        with pytest.raises(ValueError):
            ObservationRosAdapter.decode_image_message(msg)

    def test_decode_unsupported_encoding_raises(self) -> None:
        msg = MockImageMsg(480, 640, "32FC1")
        with pytest.raises(ValueError, match="Unsupported image encoding"):
            ObservationRosAdapter.decode_image_message(msg)


# ---------------------------------------------------------------------------
# handle_image (mock callback)
# ---------------------------------------------------------------------------


class TestHandleImage:
    def test_handle_image_mock(self) -> None:
        """handle_image decodes, preprocesses, and updates collector."""
        adapter = _new_adapter()
        msg = MockImageMsg(480, 640, "rgb8")
        adapter.handle_image("cam_high", msg)
        # After one image, snapshot should still return None (missing other fields)
        assert "cam_high" not in adapter._collector.missing_fields()

    def test_handle_image_decode_failure_does_not_crash(self) -> None:
        """Decode failure records error in buffer, does not raise."""
        adapter = _new_adapter()
        msg = MagicMock()
        msg.__class__.__name__ = "UnknownType"
        # Remove attributes that make it look like Image
        del msg.height
        adapter.handle_image("cam_high", msg)
        # Buffer should have recorded an error
        metrics = adapter._buffer.metrics_snapshot()
        assert metrics["last_error"] is not None


# ---------------------------------------------------------------------------
# handle_tcp_pose (mock callback)
# ---------------------------------------------------------------------------


class TestHandleTCPPose:
    def test_handle_tcp_pose_mock(self) -> None:
        adapter = _new_adapter()
        adapter.handle_tcp_pose("left", MockPoseMsg(0.1, 0.2, 0.3))
        # After one pose, snapshot still returns None (missing other fields)
        missing = adapter._collector.missing_fields()
        assert "left_tcp_position" not in missing
        assert "left_tcp_orientation" not in missing

    def test_handle_tcp_pose_parse_failure(self) -> None:
        """Parse failure records error, does not raise."""
        adapter = _new_adapter()
        msg = MagicMock()
        del msg.position  # Remove position to trigger parse error
        adapter.handle_tcp_pose("left", msg)
        metrics = adapter._buffer.metrics_snapshot()
        assert metrics["last_error"] is not None


# ---------------------------------------------------------------------------
# handle_gripper_state (mock callback)
# ---------------------------------------------------------------------------


class TestHandleGripperState:
    def test_handle_gripper_state_mock(self) -> None:
        adapter = _new_adapter()
        adapter.handle_gripper_state("left", MockGripperMsg(0.05))
        missing = adapter._collector.missing_fields()
        assert "left_gripper_width" not in missing

    def test_handle_gripper_parse_failure(self) -> None:
        """Gripper message without width/position/data raises and records error."""
        adapter = _new_adapter()
        msg = MagicMock()
        del msg.width
        del msg.position
        del msg.data
        adapter.handle_gripper_state("left", msg)
        metrics = adapter._buffer.metrics_snapshot()
        assert metrics["last_error"] is not None


# ---------------------------------------------------------------------------
# try_publish_observation
# ---------------------------------------------------------------------------


class TestTryPublishObservation:
    def test_try_publish_ready(self) -> None:
        """When all fields are present, snapshot goes to buffer."""
        adapter = _new_adapter()
        # Fill all fields via handle_* calls
        adapter.handle_image("cam_high", MockImageMsg(100, 100, "rgb8"))
        adapter.handle_image("cam_wrist", MockImageMsg(100, 100, "rgb8"))
        adapter.handle_tcp_pose("left", MockPoseMsg(0.1, 0.2, 0.3))
        adapter.handle_tcp_pose("right", MockPoseMsg(0.4, 0.5, 0.6))
        adapter.handle_gripper_state("left", MockGripperMsg(0.05))
        adapter.handle_gripper_state("right", MockGripperMsg(0.08))

        # Now snapshot should be ready
        snap = adapter._buffer.latest_observation(max_age_s=30.0)
        assert snap is not None
        assert snap.encoded_state.shape == (16,)

    def test_try_publish_missing(self) -> None:
        """When fields are missing, buffer records missing_fields."""
        adapter = _new_adapter()
        # Only fill one image, leave everything else missing
        adapter.handle_image("cam_high", MockImageMsg(100, 100, "rgb8"))

        # Buffer should have recorded missing fields
        metrics = adapter._buffer.metrics_snapshot()
        assert isinstance(metrics["last_missing_fields"], list)

    def test_try_publish_with_ros_config(self) -> None:
        """Adapter with full topic/image config works correctly."""
        config = {
            "image": {
                "target_height": 100,
                "target_width": 100,
                "target_channels": 3,
            },
            "topics": {
                "observation": {
                    "images": {"cam_high": "/cam_high/image_raw"},
                    "left_tcp_pose": "/left/tcp_pose",
                    "right_tcp_pose": "/right/tcp_pose",
                    "left_gripper_state": "/left/gripper/state",
                    "right_gripper_state": "/right/gripper/state",
                }
            },
        }
        adapter = ObservationRosAdapter(
            collector=_new_collector(),
            buffer=_new_buffer(),
            config=config,
            max_age_s=5.0,
        )
        adapter.handle_image("cam_high", MockImageMsg(100, 100, "rgb8"))
        adapter.handle_image("cam_wrist", MockImageMsg(100, 100, "rgb8"))
        adapter.handle_tcp_pose("left", MockPoseMsg())
        adapter.handle_tcp_pose("right", MockPoseMsg())
        adapter.handle_gripper_state("left", MockGripperMsg())
        adapter.handle_gripper_state("right", MockGripperMsg())

        snap = adapter._buffer.latest_observation(max_age_s=30.0)
        assert snap is not None


# ---------------------------------------------------------------------------
# create_subscriptions env-blocked
# ---------------------------------------------------------------------------


class TestCreateSubscriptions:
    def test_no_ros_subscription_blocked(self) -> None:
        """Without ROS, create_subscriptions sets env_blocked."""
        adapter = _new_adapter()
        adapter.create_subscriptions(MagicMock())
        if not _ROS_AVAILABLE:
            assert adapter.env_blocked is True
            assert adapter.subscription_count == 0

    def test_with_ros_mock_node(self) -> None:
        """With a mock node, subscriptions are created if ROS is available."""
        if not _ROS_AVAILABLE:
            pytest.skip("ROS not available — env_blocked path tested above")

        config = {
            "topics": {
                "observation": {
                    "images": {"cam_high": "/cam_high/image_raw"},
                    "left_tcp_pose": "/left/tcp_pose",
                    "right_tcp_pose": "/right/tcp_pose",
                    "left_gripper_state": "/left/gripper/state",
                    "right_gripper_state": "/right/gripper/state",
                }
            },
        }
        adapter = ObservationRosAdapter(
            collector=_new_collector(),
            buffer=_new_buffer(),
            config=config,
        )
        adapter.create_subscriptions(MockNode())
        assert adapter.subscription_count == 5  # 1 image + 2 pose + 2 gripper
        assert adapter.env_blocked is False
