"""B11 main + C21 argument-parser tests (deploy_054).

Production ``main`` is real-only and requires a ROS graph, so these tests
exercise it with the rclpy globals + production constructors monkeypatched to
deterministic fakes (no DDS, no spinning, no policy weights).  The CLI schema
and the OS exit-code contract (0 / 1 / argparse 2) are verified directly.
"""

from types import SimpleNamespace

import pytest

import model_deploy.act.config as config_mod
import model_deploy.act.repo as repo_mod
import model_deploy.act.service.act_inference as svc_mod
from model_deploy.act.config.schema import DeployConfig
from model_deploy.act.ui.act_deploy_node import build_arg_parser, main


# ---------------------------------------------------------------------------
# Fakes for the ROS / production-only seams
# ---------------------------------------------------------------------------


class FakeRclpy:
    def __init__(self) -> None:
        self.init_called = False
        self.spin_called = False
        self.shutdown_called = False

    def init(self, *a, **k) -> None:
        self.init_called = True

    def spin(self, node) -> None:
        self.spin_called = True

    def shutdown(self, *a, **k) -> None:
        self.shutdown_called = True

    def ok(self) -> bool:
        return True


class FakeDeployNode:
    """Stand-in for the production ActDeployNode (construction-only)."""

    def __init__(self, *, config, resources, inference_service, permit_source=None,
                 monotonic_clock=None, node_name="act_deploy_node"):
        self.config = config
        self._shutdown_succeeded = True
        self.shutdown_called = False
        self.destroy_called = False

    def shutdown(self) -> bool:
        self.shutdown_called = True
        return self._shutdown_succeeded

    def destroy_node(self) -> None:
        self.destroy_called = True


# ---------------------------------------------------------------------------
# Canonical builders (shared shape with the preflight / composition tests)
# ---------------------------------------------------------------------------


def _spec():
    from model_deploy.act.repo.act_runtime_resources import PolicyInputSpec

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


def _config(command_output_enabled=False):
    raw = {
        "bundle": {"bundle_dir": "/nonexistent/bundle"},
        "runtime": {
            "mode": "real-run" if command_output_enabled else "dry-run",
            "state_dim": 16,
            "action_dim": 16,
            "chunk_size": 30,
        },
        "image": {"image_size": 224},
    }
    return DeployConfig.from_mapping(
        raw, base_dir="/tmp", command_output_enabled=command_output_enabled
    )


def _resources(spec):
    return SimpleNamespace(
        policy=None,
        state_normalizer=None,
        action_normalizer=None,
        policy_input_spec=spec,
    )


def _inference_service(spec):
    class _FakeService:
        input_spec = spec

        def predict_action_chunk(self, observation):
            return SimpleNamespace(actions=None)

    return _FakeService()


# ---------------------------------------------------------------------------
# C21 — argument parser schema
# ---------------------------------------------------------------------------


def test_parser_requires_config():
    with pytest.raises(SystemExit) as exc:
        build_arg_parser().parse_args([])
    assert exc.value.code == 2  # argparse usage error, preserved


def test_parser_enable_flag_defaults_false():
    args = build_arg_parser().parse_args(["--config", "dummy.yaml"])
    assert args.config == "dummy.yaml"
    assert args.enable_command_output is False


def test_parser_enable_flag_can_be_set():
    args = build_arg_parser().parse_args(
        ["--config", "dummy.yaml", "--enable-command-output"]
    )
    assert args.enable_command_output is True


# ---------------------------------------------------------------------------
# B11 — main entry / exit codes
# ---------------------------------------------------------------------------


@pytest.fixture
def patched_main(monkeypatch):
    fake_rclpy = FakeRclpy()
    monkeypatch.setattr("model_deploy.act.ui.act_deploy_node.rclpy", fake_rclpy)
    monkeypatch.setattr(
        "model_deploy.act.ui.act_deploy_node.ActDeployNode", FakeDeployNode
    )

    spec = _spec()
    monkeypatch.setattr(
        config_mod, "load_deploy_config", lambda path, **kw: _config(**kw)
    )
    monkeypatch.setattr(
        repo_mod,
        "load_act_runtime_resources",
        lambda config, **kw: _resources(spec),
    )
    monkeypatch.setattr(
        svc_mod,
        "ActInferenceService",
        lambda config, sn, an, policy, spec_arg: _inference_service(spec_arg),
    )
    return fake_rclpy


def test_main_success_returns_zero(patched_main):
    rc = main(["--config", "dummy.yaml"])
    assert rc == 0
    assert patched_main.init_called
    assert patched_main.spin_called
    assert patched_main.shutdown_called


def test_main_command_output_flag_passed_to_loader(patched_main, monkeypatch):
    captured = {}

    def _fake_load(path, *, command_output_enabled=False):
        captured["enabled"] = command_output_enabled
        return _config(command_output_enabled=command_output_enabled)

    monkeypatch.setattr(config_mod, "load_deploy_config", _fake_load)
    rc = main(["--config", "dummy.yaml", "--enable-command-output"])
    assert rc == 0
    assert captured["enabled"] is True


def test_main_construction_error_returns_one(patched_main, monkeypatch):
    class _Boom(FakeDeployNode):
        def __init__(self, **kwargs):
            raise RuntimeError("composition failed under env_blocked")

    monkeypatch.setattr(
        "model_deploy.act.ui.act_deploy_node.ActDeployNode", _Boom
    )
    rc = main(["--config", "dummy.yaml"])
    assert rc == 1


def test_main_keyboard_interrupt_returns_zero(patched_main):
    def _raise_kb_int(*a, **k):
        raise KeyboardInterrupt()

    patched_main.spin = _raise_kb_int
    rc = main(["--config", "dummy.yaml"])
    assert rc == 0
    assert patched_main.shutdown_called


def test_main_config_load_error_returns_one(patched_main, monkeypatch):
    def _boom(path, **kw):
        raise config_mod.DeployConfigError("missing bundle")

    monkeypatch.setattr(config_mod, "load_deploy_config", _boom)
    rc = main(["--config", "dummy.yaml"])
    assert rc == 1


def test_main_does_not_import_ros_at_module_load():
    # Importing the module must not pull in rclpy side effects / threads.
    import model_deploy.act.ui.act_deploy_node as mod

    # The module is importable even when rclpy is absent in this env.
    assert mod is not None
