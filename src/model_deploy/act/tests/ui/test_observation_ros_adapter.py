"""Tests for ObservationRosAdapter — typed DeployConfig + PolicyInputSpec contract.

Covers: mock callbacks (image/tcp/gripper), decode, CHW float32 [0,1] output,
camera-key validation, consistent gripper decoder, and env-blocked behavior.
"""

import os
import time
from typing import Any
from unittest.mock import MagicMock

import numpy as np
import pytest

from model_deploy.act.config import load_deploy_config
from model_deploy.act.repo import PolicyInputSpec
from model_deploy.act.runtime.observation_buffer import ObservationBuffer
from model_deploy.act.service.observation_collector import ObservationCollector
from model_deploy.act.ui import observation_ros_adapter as oa
from model_deploy.act.ui.observation_ros_adapter import (
    ObservationRosAdapter,
    decode_gripper_width,
)

REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..")
)
DEPLOY_YAML = os.path.join(
    REPO_ROOT, "src/model_deploy/act/config_files/deploy.yaml"
)


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _load_config() -> Any:
    return load_deploy_config(DEPLOY_YAML)


def _make_spec(config: Any, camera_keys: tuple[str, ...] | None = None) -> PolicyInputSpec:
    camera_keys = tuple(camera_keys) if camera_keys is not None else config.topics.observation.camera_keys
    image_size = config.image.image_size
    return PolicyInputSpec(
        state_key=config.topics.observation.arm_state,
        state_dim=16,
        image_prefix=config.topics.namespace + "/observation/image/",
        camera_keys=camera_keys,
        image_shapes=tuple((3, image_size, image_size) for _ in camera_keys),
        image_layout="CHW",
        image_dtype="float32",
        image_value_range=(0.0, 1.0),
        action_dim=16,
        chunk_size=config.runtime.chunk_size,
    )


class FakeClock:
    def __init__(self, t: float = 1000.0) -> None:
        self.t = t

    def __call__(self) -> float:
        return self.t

    def advance(self, dt: float) -> None:
        self.t += dt


def _new_adapter(config: Any | None = None, spec: PolicyInputSpec | None = None,
                 clock: FakeClock | None = None) -> ObservationRosAdapter:
    config = config or _load_config()
    spec = spec or _make_spec(config)
    clock = clock or FakeClock()
    collector = ObservationCollector(
        required_image_keys=list(spec.camera_keys),
        required_state_fields=[
            "left_tcp_position", "left_tcp_orientation", "left_gripper_width",
            "right_tcp_position", "right_tcp_orientation", "right_gripper_width",
        ],
        monotonic_clock=clock,
    )
    buffer = ObservationBuffer(monotonic_clock=clock)
    return ObservationRosAdapter(
        collector=collector,
        buffer=buffer,
        config=config,
        input_spec=spec,
        max_age_s=config.runtime.max_observation_age_sec,
        monotonic_clock=clock,
    )


# ---- Mock message helpers ----


class MockImageMsg:
    """Mock a sensor_msgs.msg.Image with raw byte data."""

    def __init__(self, h: int = 224, w: int = 224, encoding: str = "rgb8") -> None:
        self.height = h
        self.width = w
        self.encoding = encoding
        if encoding in ("rgb8", "bgr8", "mono8"):
            self.data = np.random.randint(0, 256, (h, w, 3), dtype=np.uint8).tobytes()
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
        self.data = b"\xff\xd8\xff\xe0\x00\x10JFIF"  # minimal truncated jpeg
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


class MockGripperMsgWidth:
    """Mock a gripper state message carrying a scalar `width`."""

    def __init__(self, width: float = 0.05) -> None:
        self.width = width
        self.__class__.__name__ = "GripperState"


class MockGripperMsgPose:
    """Mock a gripper state message shaped like Pose (position.x = width)."""

    def __init__(self, width: float = 0.05) -> None:
        self.position = MagicMock()
        self.position.x = width
        self.__class__.__name__ = "Pose"


class MockNode:
    """Minimal mock ROS node."""

    def __init__(self, fail_on_call: int | None = None) -> None:
        self._calls = 0
        self.fail_on_call = fail_on_call

    def create_subscription(self, msg_type: type, topic: str,
                            callback: Any, qos: int) -> MagicMock:
        self._calls += 1
        if self.fail_on_call is not None and self._calls == self.fail_on_call:
            raise RuntimeError("simulated subscription failure")
        sub = MagicMock()
        return sub


# ---------------------------------------------------------------------------
# Import without ROS
# ---------------------------------------------------------------------------


class TestImportWithoutROS:
    def test_import_without_ros(self) -> None:
        """Module must import without ROS packages (no ImportError)."""
        assert oa.ObservationRosAdapter is ObservationRosAdapter

    def test_env_blocked_when_no_ros(self) -> None:
        """create_subscriptions sets env_blocked when ROS is absent."""
        adapter = _new_adapter()
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(oa, "_ROS_AVAILABLE", False)
            adapter.create_subscriptions(MagicMock())
            assert adapter.env_blocked is True
            assert adapter.subscription_count == 0


# ---------------------------------------------------------------------------
# decode_image_message
# ---------------------------------------------------------------------------


class TestDecodeImageMessage:
    def test_decode_image_rgb8(self) -> None:
        msg = MockImageMsg(224, 224, "rgb8")
        result = ObservationRosAdapter.decode_image_message(msg)
        assert result.shape == (224, 224, 3)
        assert result.dtype == np.uint8

    def test_decode_image_bgr8(self) -> None:
        msg = MockImageMsg(224, 224, "bgr8")
        result = ObservationRosAdapter.decode_image_message(msg)
        assert result.shape == (224, 224, 3)
        assert result.dtype == np.uint8

    def test_decode_unknown_type_raises(self) -> None:
        msg = MagicMock()
        msg.__class__ = MagicMock()
        msg.__class__.__name__ = "UnknownType"
        del msg.height
        with pytest.raises(ValueError):
            ObservationRosAdapter.decode_image_message(msg)


# ---------------------------------------------------------------------------
# Gripper decoder consistency
# ---------------------------------------------------------------------------


class TestGripperDecoder:
    def test_decode_width(self) -> None:
        assert decode_gripper_width(MockGripperMsgWidth(0.07)) == 0.07

    def test_decode_pose_position_x(self) -> None:
        assert decode_gripper_width(MockGripperMsgPose(0.09)) == 0.09

    def test_decode_missing_raises(self) -> None:
        msg = MagicMock()
        del msg.width
        del msg.position
        del msg.data
        with pytest.raises(ValueError):
            decode_gripper_width(msg)


# ---------------------------------------------------------------------------
# handle_image -> CHW float32 [0,1]
# ---------------------------------------------------------------------------


class TestHandleImage:
    def test_handle_image_produces_chw(self) -> None:
        """handle_image normalizes to CHW float32 in [0,1] matching the spec."""
        config = _load_config()
        spec = _make_spec(config)
        adapter = _new_adapter(config, spec)
        adapter.handle_image("left", MockImageMsg(224, 224, "rgb8"))

        img = adapter._collector._images["left"]
        # 尺寸跟随配置的 image_size（真实部署为 640），不硬编码
        size = config.image.image_size
        assert img.shape == (3, size, size)  # CHW
        assert img.dtype == np.float32
        assert img.min() >= 0.0
        assert img.max() <= 1.0

    def test_handle_image_decode_failure_does_not_crash(self) -> None:
        adapter = _new_adapter()
        msg = MagicMock()
        msg.__class__.__name__ = "UnknownType"
        del msg.height
        adapter.handle_image("left", msg)
        metrics = adapter._buffer.metrics_snapshot()
        assert metrics["last_error"] is not None


# ---------------------------------------------------------------------------
# handle_tcp_pose / handle_gripper_state
# ---------------------------------------------------------------------------


class TestHandleTCPPose:
    def test_handle_tcp_pose_mock(self) -> None:
        adapter = _new_adapter()
        adapter.handle_tcp_pose("left", MockPoseMsg(0.1, 0.2, 0.3))
        missing = adapter._collector.missing_fields()
        assert "left_tcp_position" not in missing
        assert "left_tcp_orientation" not in missing

    def test_handle_tcp_pose_parse_failure(self) -> None:
        adapter = _new_adapter()
        msg = MagicMock()
        del msg.position
        adapter.handle_tcp_pose("left", msg)
        assert adapter._buffer.metrics_snapshot()["last_error"] is not None


class TestHandleGripperState:
    def test_handle_gripper_width(self) -> None:
        adapter = _new_adapter()
        adapter.handle_gripper_state("left", MockGripperMsgWidth(0.05))
        assert "left_gripper_width" not in adapter._collector.missing_fields()

    def test_handle_gripper_pose_consistent(self) -> None:
        """Decoder matches the declared Pose message type."""
        adapter = _new_adapter()
        adapter.handle_gripper_state("left", MockGripperMsgPose(0.06))
        assert "left_gripper_width" not in adapter._collector.missing_fields()

    def test_handle_gripper_parse_failure(self) -> None:
        adapter = _new_adapter()
        msg = MagicMock()
        del msg.width
        del msg.position
        del msg.data
        adapter.handle_gripper_state("left", msg)
        assert adapter._buffer.metrics_snapshot()["last_error"] is not None


# ---------------------------------------------------------------------------
# Full publish (all fields present)
# ---------------------------------------------------------------------------


class TestTryPublishObservation:
    def test_try_publish_ready(self) -> None:
        config = _load_config()
        spec = _make_spec(config)
        adapter = _new_adapter(config, spec)
        adapter.handle_image("left", MockImageMsg(224, 224, "rgb8"))
        adapter.handle_image("right", MockImageMsg(224, 224, "rgb8"))
        adapter.handle_tcp_pose("left", MockPoseMsg(0.1, 0.2, 0.3))
        adapter.handle_tcp_pose("right", MockPoseMsg(0.4, 0.5, 0.6))
        adapter.handle_gripper_state("left", MockGripperMsgWidth(0.05))
        adapter.handle_gripper_state("right", MockGripperMsgWidth(0.08))

        snap = adapter._buffer.latest_observation(max_age_s=30.0)
        assert snap is not None
        assert snap.encoded_state.shape == (16,)
        # CHW images in the snapshot（尺寸跟随配置的 image_size）
        size = config.image.image_size
        assert snap.images["left"].shape == (3, size, size)
        assert snap.images["right"].shape == (3, size, size)

    def test_try_publish_missing_records(self) -> None:
        adapter = _new_adapter()
        adapter.handle_image("left", MockImageMsg(224, 224, "rgb8"))
        metrics = adapter._buffer.metrics_snapshot()
        assert isinstance(metrics["last_missing_fields"], list)


# ---------------------------------------------------------------------------
# create_subscriptions + camera-key validation
# ---------------------------------------------------------------------------


class TestCreateSubscriptions:
    def test_with_ros_mock_node(self) -> None:
        """Canonical mapping (left,right) -> 2 images + 2 pose + 2 gripper = 6."""
        if not oa._ROS_AVAILABLE:
            pytest.skip("ROS not available — env_blocked path tested above")
        adapter = _new_adapter()
        adapter.create_subscriptions(MockNode())
        assert adapter.subscription_count == 6
        assert adapter.env_blocked is False

    def test_camera_key_mismatch_raises(self) -> None:
        """Camera-key mismatch is a config error (fail-fast at construction)."""
        config = _load_config()
        bad_spec = _make_spec(config, camera_keys=("top", "wrist"))
        collector = ObservationCollector(
            required_image_keys=["top", "wrist"],
            required_state_fields=[
                "left_tcp_position", "left_tcp_orientation", "left_gripper_width",
                "right_tcp_position", "right_tcp_orientation", "right_gripper_width",
            ],
        )
        buffer = ObservationBuffer()
        with pytest.raises(ValueError):
            ObservationRosAdapter(
                collector=collector,
                buffer=buffer,
                config=config,
                input_spec=bad_spec,
                max_age_s=config.runtime.max_observation_age_sec,
            )

    def test_subscription_rollback_on_failure(self) -> None:
        """Partial subscription failure rolls back created handles."""
        if not oa._ROS_AVAILABLE:
            pytest.skip("ROS not available")
        adapter = _new_adapter()
        node = MockNode(fail_on_call=3)  # fail on the 3rd create_subscription
        with pytest.raises(RuntimeError):
            adapter.create_subscriptions(node)
        # No leaked subscriptions remain accessible.
        assert adapter.subscription_count == 0
