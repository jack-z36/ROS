"""ROS adapter tests for real-run permit heartbeat and emergency stop."""

from pathlib import Path
from types import SimpleNamespace

import pytest

from model_deploy.act.config.schema import DeployConfig
from model_deploy.act.ui.command_permit_provider import (
    GRIPPER_ESTOP_SERVICE,
    PERMIT_TOPIC,
    RM65_ESTOP_SERVICE,
    RosCommandPermitProvider,
)


class FakeClock:
    def __init__(self) -> None:
        self.now_s = 0.0

    def __call__(self) -> float:
        return self.now_s

    def advance(self, seconds: float) -> None:
        self.now_s += seconds


class FakePublisher:
    def __init__(self, subscription_count: int = 2) -> None:
        self.subscription_count = subscription_count
        self.messages = []

    def get_subscription_count(self) -> int:
        return self.subscription_count

    def publish(self, msg) -> None:
        self.messages.append(msg)


class FakeClient:
    def __init__(self, ready: bool = True) -> None:
        self.ready = ready
        self.requests = []

    def service_is_ready(self) -> bool:
        return self.ready

    def call_async(self, request) -> None:
        self.requests.append(request)


class FakeTimer:
    def __init__(self) -> None:
        self.cancelled = False

    def cancel(self) -> None:
        self.cancelled = True


class FakeNode:
    def __init__(self) -> None:
        self.permit_publisher = FakePublisher()
        self.command_subscriber_count = 1
        self.clients = {
            RM65_ESTOP_SERVICE: FakeClient(),
            GRIPPER_ESTOP_SERVICE: FakeClient(),
        }
        self.timer = FakeTimer()

    def create_publisher(self, msg_type, topic, qos):
        assert topic == PERMIT_TOPIC
        return self.permit_publisher

    def create_subscription(self, msg_type, topic, callback, qos):
        return SimpleNamespace(topic=topic, callback=callback)

    def create_client(self, srv_type, service):
        return self.clients[service]

    def create_timer(self, period_s, callback):
        self.timer.callback = callback
        return self.timer

    def count_subscribers(self, topic) -> int:
        return self.command_subscriber_count

    def get_clock(self):
        from builtin_interfaces.msg import Time

        return SimpleNamespace(
            now=lambda: SimpleNamespace(to_msg=lambda: Time())
        )


def _config() -> DeployConfig:
    raw = {
        "bundle": {"bundle_dir": "/tmp/bundle"},
        "runtime": {"mode": "real-run"},
        "safety": {},
    }
    return DeployConfig.from_mapping(
        raw,
        base_dir=Path("/tmp"),
        command_output_enabled=True,
    )


def _rm65_health(*, healthy: bool = True):
    return SimpleNamespace(
        left_connected=healthy,
        right_connected=healthy,
        left_estop_active=False,
        right_estop_active=False,
        left_sdk_code=0,
        right_sdk_code=0,
        left_controller_err=0,
        right_controller_err=0,
    )


def _gripper_health(*, healthy: bool = True):
    return SimpleNamespace(
        left_connected=healthy,
        right_connected=healthy,
        estop_active=False,
        status=0 if healthy else 2,
    )


def _healthy_provider():
    node = FakeNode()
    clock = FakeClock()
    provider = RosCommandPermitProvider(
        node=node, config=_config(), monotonic_clock=clock
    )
    provider._on_rm65_health(_rm65_health())
    provider._on_gripper_health(_gripper_health())
    return provider, node, clock


def test_real_run_preflight_and_two_heartbeat_warmup() -> None:
    provider, node, _ = _healthy_provider()

    provider.run_startup_preflight(timeout_s=0.1)
    provider.update_runtime_ready(True, "RUNTIME_READY")
    provider._publish_heartbeat()
    assert provider.resolve().allowed is False
    provider._publish_heartbeat()

    assert provider.resolve().allowed is True
    assert len(node.permit_publisher.messages) == 2
    assert all(msg.allowed for msg in node.permit_publisher.messages)


def test_health_fault_after_allow_revokes_and_requests_both_estops() -> None:
    provider, node, _ = _healthy_provider()
    provider.update_runtime_ready(True, "RUNTIME_READY")
    provider._publish_heartbeat()
    provider._publish_heartbeat()
    assert provider.resolve().allowed is True

    provider._on_rm65_health(_rm65_health(healthy=False))

    assert provider.resolve().allowed is False
    assert provider.reason_code == "RM65_HEALTH_FAULT"
    assert len(node.clients[RM65_ESTOP_SERVICE].requests) == 1
    assert len(node.clients[GRIPPER_ESTOP_SERVICE].requests) == 1
    assert node.permit_publisher.messages[-1].allowed is False


def test_missing_command_subscriber_fails_startup_preflight(
    monkeypatch,
) -> None:
    provider, node, clock = _healthy_provider()
    node.command_subscriber_count = 0

    import rclpy

    monkeypatch.setattr(
        rclpy,
        "spin_once",
        lambda _node, timeout_sec: clock.advance(max(timeout_sec, 0.01)),
    )
    with pytest.raises(RuntimeError, match="TOPOLOGY_NOT_READY"):
        provider.run_startup_preflight(timeout_s=0.1)

    assert node.permit_publisher.messages[-1].allowed is False
    assert provider.reason_code == "STARTUP_DEPENDENCY_TIMEOUT"
