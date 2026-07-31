"""Fail-closed permit state-machine tests."""

from model_deploy.act.runtime.command_permit_provider import (
    CommandPermitProvider,
    PermitState,
)


class FakeClock:
    def __init__(self) -> None:
        self.now_s = 0.0

    def __call__(self) -> float:
        return self.now_s

    def advance(self, seconds: float) -> None:
        self.now_s += seconds


def _real_provider(clock: FakeClock) -> CommandPermitProvider:
    return CommandPermitProvider(
        mode="real-run",
        command_output_enabled=True,
        monotonic_clock=clock,
        health_timeout_s=0.5,
        warmup_allowed_heartbeats=2,
    )


def _make_healthy(provider: CommandPermitProvider) -> None:
    provider.update_topology(True, "TOPOLOGY_READY")
    provider.update_runtime_ready(True, "RUNTIME_READY")
    provider.update_rm65_health(True, "RM65_HEALTH_OK")
    provider.update_gripper_health(True, "GRIPPER_HEALTH_OK")


def test_dry_run_is_always_disabled() -> None:
    clock = FakeClock()
    provider = CommandPermitProvider(
        mode="dry-run",
        command_output_enabled=False,
        monotonic_clock=clock,
    )
    _make_healthy(provider)

    permit = provider.heartbeat_permit()

    assert permit.allowed is False
    assert permit.reason_code == "COMMAND_OUTPUT_DISABLED"
    assert provider.state is PermitState.DISABLED


def test_real_run_requires_two_published_allowed_heartbeats() -> None:
    clock = FakeClock()
    provider = _real_provider(clock)
    _make_healthy(provider)

    first = provider.heartbeat_permit()
    assert first.allowed is True
    provider.record_heartbeat_published(first)
    assert provider.command_permit().allowed is False
    assert provider.reason_code == "PERMIT_HEARTBEAT_WARMUP"

    second = provider.heartbeat_permit()
    assert second.allowed is True
    provider.record_heartbeat_published(second)

    assert provider.command_permit().allowed is True
    assert provider.state is PermitState.ALLOWED
    assert provider.has_been_allowed is True


def test_missing_topology_and_health_fail_closed() -> None:
    clock = FakeClock()
    provider = _real_provider(clock)

    assert provider.command_permit().reason_code == "TOPOLOGY_NOT_READY"

    provider.update_topology(True, "TOPOLOGY_READY")
    provider.update_runtime_ready(True, "RUNTIME_READY")
    assert provider.command_permit().reason_code == "RM65_HEALTH_MISSING"

    provider.update_rm65_health(True, "RM65_HEALTH_OK")
    assert provider.command_permit().reason_code == "GRIPPER_HEALTH_MISSING"


def test_dependency_status_excludes_runtime_and_heartbeat_warmup() -> None:
    clock = FakeClock()
    provider = _real_provider(clock)
    provider.update_topology(True, "TOPOLOGY_READY")
    provider.update_rm65_health(True, "RM65_HEALTH_OK")
    provider.update_gripper_health(True, "GRIPPER_HEALTH_OK")

    assert provider.dependency_status() == (
        True,
        "HARDWARE_DEPENDENCIES_READY",
    )
    assert provider.command_permit().reason_code == "RUNTIME_NOT_READY"


def test_health_fault_is_denied_and_stale_health_returns_to_waiting() -> None:
    clock = FakeClock()
    provider = _real_provider(clock)
    provider.update_topology(True, "TOPOLOGY_READY")
    provider.update_runtime_ready(True, "RUNTIME_READY")
    provider.update_rm65_health(False, "RM65_HEALTH_FAULT")
    provider.update_gripper_health(True, "GRIPPER_HEALTH_OK")

    permit = provider.command_permit()
    assert permit.allowed is False
    assert permit.reason_code == "RM65_HEALTH_FAULT"
    assert provider.state is PermitState.DENIED

    provider.update_rm65_health(True, "RM65_HEALTH_OK")
    clock.advance(0.51)
    permit = provider.command_permit()
    assert permit.allowed is False
    assert permit.reason_code == "RM65_HEALTH_STALE"
    assert provider.state is PermitState.WAITING_HEALTH


def test_runtime_not_ready_revokes_warmup() -> None:
    clock = FakeClock()
    provider = _real_provider(clock)
    _make_healthy(provider)
    heartbeat = provider.heartbeat_permit()
    provider.record_heartbeat_published(heartbeat)
    provider.update_runtime_ready(False, "OBSERVATION_STALE")

    assert provider.command_permit().reason_code == "OBSERVATION_STALE"
    assert provider.allowed_heartbeat_count == 0


def test_latched_fault_is_sticky() -> None:
    clock = FakeClock()
    provider = _real_provider(clock)
    _make_healthy(provider)
    provider.latch_denial("INFERENCE_WORKER_EXITED")

    for _ in range(2):
        assert provider.command_permit().reason_code == "INFERENCE_WORKER_EXITED"
        _make_healthy(provider)

    assert provider.state is PermitState.DENIED
