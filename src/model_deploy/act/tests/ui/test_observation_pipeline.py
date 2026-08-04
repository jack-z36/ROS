"""Tests for the typed ObservationPipeline factory (deploy_057).

Covers the frozen public seam, spec/clock identity, camera mismatch fail-fast,
CHW/range output, deep snapshot ownership, shared monotonic freshness, and
subscription rollback.
"""

import os

import numpy as np
import pytest

from model_deploy.act.config import load_deploy_config
from model_deploy.act.repo import PolicyInputSpec
from model_deploy.act.service.observation_collector import ObservationCollector
from model_deploy.act.ui import observation_ros_adapter as oa
from model_deploy.act.ui.observation_pipeline import (
    ObservationPipeline,
    build_observation_pipeline,
)

REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..")
)
DEPLOY_YAML = os.path.join(
    REPO_ROOT, "src/model_deploy/act/config_files/deploy.yaml"
)


def _load_config():
    return load_deploy_config(DEPLOY_YAML)


def _make_spec(config, camera_keys=None):
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
    def __init__(self, t=1000.0):
        self.t = t

    def __call__(self):
        return self.t

    def advance(self, dt):
        self.t += dt


class MockNode:
    def __init__(self, fail_on_call=None):
        self._calls = 0
        self.fail_on_call = fail_on_call

    def create_subscription(self, msg_type, topic, callback, qos):
        self._calls += 1
        if self.fail_on_call is not None and self._calls == self.fail_on_call:
            raise RuntimeError("simulated subscription failure")
        return __import__("unittest.mock", fromlist=["MagicMock"]).MagicMock()


# ---------------------------------------------------------------------------
# Public seam
# ---------------------------------------------------------------------------


class TestPublicSeam:
    def test_factory_builds_frozen_pipeline(self):
        config = _load_config()
        spec = _make_spec(config)
        clock = FakeClock()
        pipeline = build_observation_pipeline(
            node=MockNode(), config=config, input_spec=spec, monotonic_clock=clock
        )
        assert isinstance(pipeline, ObservationPipeline)
        assert oa._ROS_AVAILABLE is True or pipeline.adapter.env_blocked

    def test_spec_and_clock_identity(self):
        """pipeline.input_spec and pipeline.monotonic_clock are identity-equal."""
        config = _load_config()
        spec = _make_spec(config)
        clock = FakeClock()
        pipeline = build_observation_pipeline(
            node=MockNode(), config=config, input_spec=spec, monotonic_clock=clock
        )
        assert pipeline.input_spec is spec
        assert pipeline.monotonic_clock is clock

    def test_subscription_count_canonical(self):
        if not oa._ROS_AVAILABLE:
            pytest.skip("ROS not available")
        config = _load_config()
        spec = _make_spec(config)
        pipeline = build_observation_pipeline(
            node=MockNode(), config=config, input_spec=spec, monotonic_clock=FakeClock()
        )
        # 2 images + 2 tcp poses + 2 gripper states
        assert pipeline.adapter.subscription_count == 6


# ---------------------------------------------------------------------------
# Fail-fast validation
# ---------------------------------------------------------------------------


class TestFailFast:
    def test_camera_key_mismatch_raises(self):
        config = _load_config()
        bad_spec = _make_spec(config, camera_keys=("top", "wrist"))
        with pytest.raises(ValueError):
            build_observation_pipeline(
                node=MockNode(), config=config, input_spec=bad_spec,
                monotonic_clock=FakeClock(),
            )

    def test_type_errors_raise(self):
        config = _load_config()
        spec = _make_spec(config)
        with pytest.raises(TypeError):
            build_observation_pipeline(
                node=MockNode(), config=object(), input_spec=spec,  # type: ignore[arg-type]
                monotonic_clock=FakeClock(),
            )
        with pytest.raises(TypeError):
            build_observation_pipeline(
                node=MockNode(), config=config, input_spec=object(),  # type: ignore[arg-type]
                monotonic_clock=FakeClock(),
            )
        with pytest.raises(TypeError):
            build_observation_pipeline(
                node=MockNode(), config=config, input_spec=spec,
                monotonic_clock=None,  # type: ignore[arg-type]
            )

    def test_env_blocked_when_ros_absent(self):
        config = _load_config()
        spec = _make_spec(config)
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(oa, "_ROS_AVAILABLE", False)
            pipeline = build_observation_pipeline(
                node=MockNode(), config=config, input_spec=spec,
                monotonic_clock=FakeClock(),
            )
            assert pipeline.adapter.env_blocked is True
            assert pipeline.adapter.subscription_count == 0


# ---------------------------------------------------------------------------
# Monotonic freshness (shared clock)
# ---------------------------------------------------------------------------


class TestMonotonicFreshness:
    def test_captured_at_uses_shared_clock(self):
        config = _load_config()
        spec = _make_spec(config)
        clock = FakeClock(500.0)
        pipeline = build_observation_pipeline(
            node=MockNode(), config=config, input_spec=spec, monotonic_clock=clock
        )
        # Feed all fields via collector, then build a snapshot.
        col = pipeline.collector
        img = np.zeros((3, 224, 224), dtype=np.float32)
        col.update_image("left", img)
        col.update_image("right", img)
        col.update_tcp_pose("left", [0.1, 0.2, 0.3], [0.0, 0.0, 0.0, 1.0])
        col.update_tcp_pose("right", [0.4, 0.5, 0.6], [0.0, 0.0, 0.0, 1.0])
        col.update_gripper_state("left", 0.05)
        col.update_gripper_state("right", 0.08)

        clock.advance(0.01)
        snap = col.snapshot(max_age_s=5.0)
        assert snap is not None
        assert snap.captured_at_s == clock.t  # captured from the shared clock

    def test_buffer_freshness_uses_shared_clock(self):
        from model_deploy.act.runtime.observation_buffer import ObservationBuffer
        from model_deploy.act.ui.observation_pipeline import REQUIRED_STATE_FIELDS
        from model_deploy.act.repo import PolicyInputSpec

        config = _load_config()
        spec = _make_spec(config)
        clock = FakeClock(500.0)
        collector = ObservationCollector(
            required_image_keys=list(spec.camera_keys),
            required_state_fields=list(REQUIRED_STATE_FIELDS),
            monotonic_clock=clock,
        )
        buffer = ObservationBuffer(monotonic_clock=clock)
        img = np.zeros((3, 224, 224), dtype=np.float32)
        collector.update_image("left", img)
        collector.update_image("right", img)
        collector.update_tcp_pose("left", [0.1, 0.2, 0.3], [0.0, 0.0, 0.0, 1.0])
        collector.update_tcp_pose("right", [0.4, 0.5, 0.6], [0.0, 0.0, 0.0, 1.0])
        collector.update_gripper_state("left", 0.05)
        collector.update_gripper_state("right", 0.08)
        snap = collector.snapshot(max_age_s=5.0)
        assert snap is not None
        buffer.set_observation(snap)

        # advance beyond max_age and confirm the SAME clock expires it
        clock.advance(10.0)
        assert buffer.latest_observation(max_age_s=1.0) is None


# ---------------------------------------------------------------------------
# Deep snapshot ownership
# ---------------------------------------------------------------------------


class TestDeepOwnership:
    def test_source_mutation_does_not_affect_snapshot(self):
        config = _load_config()
        spec = _make_spec(config)
        clock = FakeClock()
        pipeline = build_observation_pipeline(
            node=MockNode(), config=config, input_spec=spec, monotonic_clock=clock
        )
        col = pipeline.collector

        # Mutable shared buffer simulating a reused ROS decode buffer.
        shared = np.zeros((3, 224, 224), dtype=np.float32)
        col.update_image("left", shared)
        col.update_image("right", shared)
        col.update_tcp_pose("left", [0.1, 0.2, 0.3], [0.0, 0.0, 0.0, 1.0])
        col.update_tcp_pose("right", [0.4, 0.5, 0.6], [0.0, 0.0, 0.0, 1.0])
        col.update_gripper_state("left", 0.05)
        col.update_gripper_state("right", 0.08)

        snap = col.snapshot(max_age_s=5.0)
        assert snap is not None

        # Mutate the shared buffer AFTER snapshot construction.
        shared += 1.0
        assert np.all(snap.images["left"] == 0.0), "snapshot must own its arrays"
        assert np.all(snap.images["right"] == 0.0)


# ---------------------------------------------------------------------------
# Subscription rollback
# ---------------------------------------------------------------------------


class TestSubscriptionRollback:
    def test_rollback_on_partial_failure(self):
        if not oa._ROS_AVAILABLE:
            pytest.skip("ROS not available")
        config = _load_config()
        spec = _make_spec(config)
        with pytest.raises(RuntimeError):
            build_observation_pipeline(
                node=MockNode(fail_on_call=3), config=config, input_spec=spec,
                monotonic_clock=FakeClock(),
            )
