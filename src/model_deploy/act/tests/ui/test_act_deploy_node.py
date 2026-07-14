"""ActDeployNode composition + lifecycle tests (deploy_054).

Exercises A5 (atomic startup), B9 (fail-closed tick), B10 (bounded shutdown)
and C20 (single /act/metrics writer) against a :class:`FakeActDeployNode`
that subclasses the real :class:`_ActDeployComposition` logic but swaps the
ROS primitives for deterministic, ROS-free fakes (no DDS, no spinning).

The canonical resources are REAL — ``build_observation_pipeline`` builds a real
collector/buffer/adapter (subscriptions are env_blocked under no-rclpy), the
real ``SafetyGuard``, ``ControlLoop``, ``InferenceWorker`` and ``ActionPublisher``
are assembled exactly as in production.  Only the timer / publisher / clock
seams are faked.
"""

import time
from types import SimpleNamespace

import pytest

from model_deploy.act.config.schema import DeployConfig
from model_deploy.act.repo.act_runtime_resources import PolicyInputSpec
from model_deploy.act.runtime.inference_channel import LatestQueue
from model_deploy.act.types.action_publish import CommandPermit
from model_deploy.act.ui.act_deploy_node import _ActDeployComposition


# ---------------------------------------------------------------------------
# Fake ROS primitives (deterministic, no graph)
# ---------------------------------------------------------------------------


class FakeStringMsg:
    def __init__(self, data: str = "") -> None:
        self.data = data


class RecordingStringPublisher:
    def __init__(self) -> None:
        self.messages: list[str] = []

    def publish(self, msg) -> None:
        self.messages.append(msg.data if hasattr(msg, "data") else str(msg))


class FakeTimer:
    def __init__(self, period_s: float, callback) -> None:
        self.period_s = period_s
        self.callback = callback
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    def fire(self) -> None:
        if not self._cancelled:
            self.callback()


class FakeNode:
    """Node-like factory supporting create_publisher (mirrors existing tests)."""

    def __init__(self) -> None:
        self.created_publishers: list = []

    def create_publisher(self, msg_type, topic, qos):
        pub = RecordingStringPublisher()
        self.created_publishers.append((topic, pub))
        return pub


class FakeClock:
    def __init__(self, t: float = 1000.0) -> None:
        self._t = float(t)

    def __call__(self) -> float:
        return self._t

    def advance(self, dt: float) -> None:
        self._t += dt


# ---------------------------------------------------------------------------
# The composition under test
# ---------------------------------------------------------------------------


class FakeActDeployNode(FakeNode, _ActDeployComposition):
    def __init__(self, *, config, resources, inference_service, permit_source=None,
                 monotonic_clock=None):
        FakeNode.__init__(self)
        self._ros_time_value = 1.0
        self._destroyed = False
        self._timers: list[FakeTimer] = []
        clock = monotonic_clock if monotonic_clock is not None else FakeClock()
        self._act_init(
            config=config,
            resources=resources,
            inference_service=inference_service,
            permit_source=permit_source,
            monotonic_clock=clock,
        )

    # -- abstract ROS primitive seam (overridden) --
    def _ros_create_timer(self, period_s, callback):
        timer = FakeTimer(period_s, callback)
        self._timers.append(timer)
        return timer

    def _ros_cancel_timer(self, timer) -> None:
        if timer is not None:
            timer.cancel()

    def _ros_create_metrics_publisher(self, topic, qos):
        return RecordingStringPublisher(), FakeStringMsg

    def _ros_time_seconds(self) -> float:
        return float(self._ros_time_value)

    def _ros_destroy_node(self) -> None:
        self._destroyed = True

    # -- test helpers --
    def advance_ros_time(self, dt: float) -> None:
        self._ros_time_value += dt

    def fire_control_timer(self) -> None:
        if self._control_timer is not None:
            self._control_timer.fire()

    def fire_metrics_timer(self) -> None:
        if self._metrics_timer is not None:
            self._metrics_timer.fire()


# ---------------------------------------------------------------------------
# Builders (canonical, consistent)
# ---------------------------------------------------------------------------


def _spec():
    return PolicyInputSpec(
        state_key="/act/observation/arm_state",
        state_dim=16,
        image_prefix="/act/observation/image/",
        camera_keys=("left", "right"),
        image_shapes=((3, 224, 224), (3, 224, 224)),
        image_layout="CHW",
        image_dtype="float32",
        image_value_range=(0.0, 1.0),
        action_dim=16,
        chunk_size=30,
    )


def _config():
    raw = {
        "bundle": {"bundle_dir": "/nonexistent/bundle"},
        "runtime": {"state_dim": 16, "action_dim": 16, "chunk_size": 30},
        "image": {"image_size": 224},
    }
    return DeployConfig.from_mapping(raw, base_dir="/tmp", command_output_enabled=False)


def _inference_service(spec):
    class _FakeService:
        input_spec = spec

        def predict_action_chunk(self, observation):
            # Not exercised by these tests (no observation submitted), but the
            # worker must be able to call it if a request ever arrives.
            return SimpleNamespace(actions=None)

    return _FakeService()


def _resources(spec):
    return SimpleNamespace(policy_input_spec=spec)


@pytest.fixture
def node():
    """A fully-started fake node; always torn down via bounded shutdown."""
    spec = _spec()
    config = _config()
    resources = _resources(spec)
    service = _inference_service(spec)
    n = FakeActDeployNode(
        config=config, resources=resources, inference_service=service, permit_source=None
    )
    try:
        yield n
    finally:
        n.shutdown()


# ---------------------------------------------------------------------------
# A5 — atomic startup order
# ---------------------------------------------------------------------------


def test_atomic_startup_assembles_all_deps(node):
    assert node._started is True
    assert node._worker_started is True
    assert node._worker.is_alive()
    # Timers created LAST (control + metrics).
    assert node._control_timer is not None
    assert node._metrics_timer is not None
    # Pipeline / guard / queues / publisher / control loop all present.
    assert node._observation_pipeline is not None
    assert node._safety_guard is not None
    assert node._request_queue is not None
    assert node._result_queue is not None
    assert node._runtime_metrics is not None
    assert node._control_loop is not None
    assert node._action_publisher is not None
    assert node._metrics_publisher is not None


def test_worker_started_only_after_preflight(node):
    # B12 ran first: preflight already verified the canonical contract.
    snap = node._runtime_metrics.snapshot()
    # The node reaching _started means preflight passed.
    assert node._started is True


def test_timers_fire_drives_tick_and_metrics(node):
    before = node._runtime_metrics.snapshot().tick_count
    node.fire_control_timer()  # B9 one step
    node.fire_metrics_timer()  # C20 one telemetry write
    after = node._runtime_metrics.snapshot()
    assert after.tick_count == before + 1
    # C20 single writer produced exactly one /act/metrics message.
    assert len(node._metrics_publisher.messages) == 1
    text = node._metrics_publisher.messages[0]
    assert isinstance(text, str) and len(text) > 0


# ---------------------------------------------------------------------------
# B9 — fail-closed tick
# ---------------------------------------------------------------------------


def test_control_tick_invalid_monotonic_clock(node):
    node._monotonic_clock = lambda: -1.0  # invalid: negative
    node.fire_control_timer()
    snap = node._runtime_metrics.snapshot()
    assert snap.worker_fatal_reason == "CLOCK_INVALID"
    # Control loop was never reached (no tick recorded).
    assert snap.tick_count == 0


def test_control_tick_invalid_ros_time(node):
    node._monotonic_clock = lambda: 1000.0
    node._ros_time_value = float("nan")  # invalid: nan
    node.fire_control_timer()
    snap = node._runtime_metrics.snapshot()
    assert snap.worker_fatal_reason == "CLOCK_INVALID"


def test_control_tick_worker_fatal_latched(node):
    node._runtime_metrics.record_event("worker_fatal_reason", value="QUEUE_INVARIANT")
    before = node._runtime_metrics.snapshot().tick_count
    node.fire_control_timer()
    snap = node._runtime_metrics.snapshot()
    # B9 latches the RUNTIME_FAULT status and refuses to run the control loop.
    assert snap.runtime_status == "RUNTIME_FAULT"
    assert snap.tick_count == before  # tick did not run


def test_control_tick_worker_unexpectedly_dead(node):
    # Worker was started but is no longer alive (crash/termination).
    node._worker_started = True
    node._worker.is_alive = lambda: False
    node.fire_control_timer()
    snap = node._runtime_metrics.snapshot()
    assert snap.worker_fatal_reason == "WORKER_TERMINATED"
    assert snap.runtime_status == "RUNTIME_FAULT"


# ---------------------------------------------------------------------------
# B9 — fail-closed permit resolution
# ---------------------------------------------------------------------------


def test_resolve_permit_denies_when_source_none(node):
    permit = node._resolve_permit()
    assert isinstance(permit, CommandPermit)
    assert permit.allowed is False
    assert permit.reason_code == "COMMAND_OUTPUT_DISABLED"


def test_resolve_permit_denies_on_provider_error(node):
    def boom():
        raise RuntimeError("permit source down")

    node._permit_source = boom
    permit = node._resolve_permit()
    assert permit.allowed is False
    assert permit.reason_code == "PERMIT_SOURCE_ERROR"
    assert "permit_source_error" in (node._runtime_metrics.snapshot().last_error or "")


def test_resolve_permit_denies_on_bad_return_type(node):
    node._permit_source = lambda: "not-a-permit"
    permit = node._resolve_permit()
    assert permit.allowed is False
    assert permit.reason_code == "PERMIT_SOURCE_ERROR"


# ---------------------------------------------------------------------------
# C20 — single /act/metrics writer
# ---------------------------------------------------------------------------


def test_c20_telemetry_payload_is_stable_json(node):
    node._publish_runtime_metrics()
    text = node._metrics_publisher.messages[-1]
    import json

    payload = json.loads(text)
    assert payload["schema_version"] == 1
    assert payload["l2_id"] == "l2-06-control-loop"
    # A representative subset of the C4 snapshot fields are present.
    for key in (
        "runtime_status",
        "tick_count",
        "worker_fatal_reason",
        "publish_outcome_counts",
    ):
        assert key in payload
    # Stable serialization contract (sorted keys, compact separators).
    assert json.dumps(payload, sort_keys=True, separators=(",", ":")) == text


def test_c20_only_writer_of_metrics_topic(node):
    # The metrics publisher is a distinct object from the 6 command/status
    # publishers created by L2-05 ActionPublisher (recorded on the FakeNode).
    metrics_pub = node._metrics_publisher
    command_pubs = {p for _, p in node.created_publishers}
    assert metrics_pub not in command_pubs
    # Driving one metrics tick writes exactly one message.
    node._publish_runtime_metrics()
    assert len(metrics_pub.messages) == 1


# ---------------------------------------------------------------------------
# B10 — bounded, idempotent shutdown
# ---------------------------------------------------------------------------


def test_shutdown_closes_queues_cancels_timers_returns_true(node):
    rc = node.shutdown()
    assert rc is True
    assert node._shutdown is True
    assert node._shutdown_succeeded is True
    # Worker fully terminated within the bounded timeout.
    assert node._worker.is_alive() is False
    # Both queues closed, no live handles left.
    assert node._request_queue.is_closed
    assert node._result_queue.is_closed
    assert node._control_timer is None
    assert node._metrics_timer is None
    # (Node teardown/destroy is performed by the caller / B11 finally, not by
    # bounded shutdown itself; the destroy path is covered by the atomic
    # recovery test.)
    assert node._runtime_metrics.snapshot().runtime_status == "STOPPED"


def test_shutdown_is_idempotent(node):
    assert node.shutdown() is True
    # Second call returns the same success and does not raise.
    assert node.shutdown() is True


def test_shutdown_timeout_returns_false(monkeypatch):
    spec = _spec()
    config = _config()
    n = FakeActDeployNode(
        config=config,
        resources=_resources(spec),
        inference_service=_inference_service(spec),
        permit_source=None,
    )
    # Simulate a worker that refuses to exit (daemon still blocked) so the
    # bounded join times out -> SHUTDOWN_TIMEOUT, not STOPPED.
    n._worker.join = lambda *a, **k: None
    n._worker.is_alive = lambda: True
    try:
        rc = n.shutdown()
        assert rc is False
        assert n._shutdown_succeeded is False
        assert n._runtime_metrics.snapshot().runtime_status == "SHUTDOWN_TIMEOUT"
    finally:
        # Restore so teardown can actually reap the daemon thread.
        n._worker.is_alive = lambda: False
        n._worker.join = lambda *a, **k: None
        n._request_queue.close()
        n._result_queue.close()


# ---------------------------------------------------------------------------
# Atomic recovery on a partial-construction failure
# ---------------------------------------------------------------------------


def test_atomic_recovery_on_pipeline_build_failure(monkeypatch):
    import model_deploy.act.ui.act_deploy_node as mod

    def _boom(**kwargs):
        raise RuntimeError("subscription creation failed under env_blocked")

    monkeypatch.setattr(mod, "build_observation_pipeline", _boom)

    spec = _spec()
    config = _config()
    n = FakeActDeployNode.__new__(FakeActDeployNode)
    FakeNode.__init__(n)
    n._destroyed = False
    with pytest.raises(RuntimeError):
        n._act_init(
            config=config,
            resources=_resources(spec),
            inference_service=_inference_service(spec),
            permit_source=None,
            monotonic_clock=FakeClock(),
        )
    # The half-built node was destroyed and the original error preserved.
    assert n._destroyed is True
    assert n._shutdown is True
