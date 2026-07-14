"""B12 startup-contract cross-check tests (deploy_054).

Pure-RAM: no ROS graph, no bundle, no policy weights.  Verifies
:func:`run_startup_preflight` accepts a canonical, internally-consistent
resource set and raises :class:`StartupContractError` with the exact stable
code for every violated invariant.
"""

from types import SimpleNamespace

import pytest

from model_deploy.act.config.schema import DeployConfig
from model_deploy.act.repo.act_runtime_resources import PolicyInputSpec
from model_deploy.act.runtime.inference_channel import LatestQueue
from model_deploy.act.ui.act_deploy_node import (
    STARTUP_CONTRACT_CODES,
    StartupContractError,
    run_startup_preflight,
)


# ---------------------------------------------------------------------------
# Builders (kept local — test-only harness)
# ---------------------------------------------------------------------------


def _spec(
    *,
    camera_keys=("left", "right"),
    state_dim=16,
    action_dim=16,
    chunk_size=30,
    image_layout="CHW",
    image_dtype="float32",
    image_value_range=(0.0, 1.0),
    image_size=224,
):
    shapes = tuple((3, image_size, image_size) for _ in camera_keys)
    return PolicyInputSpec(
        state_key="/act/observation/arm_state",
        state_dim=state_dim,
        image_prefix="/act/observation/image/",
        camera_keys=tuple(camera_keys),
        image_shapes=shapes,
        image_layout=image_layout,
        image_dtype=image_dtype,
        image_value_range=image_value_range,
        action_dim=action_dim,
        chunk_size=chunk_size,
    )


def _config(*, state_dim=16, action_dim=16, chunk_size=30, command_output_enabled=False):
    raw = {
        "bundle": {"bundle_dir": "/nonexistent/bundle"},
        "runtime": {
            "state_dim": state_dim,
            "action_dim": action_dim,
            "chunk_size": chunk_size,
        },
        "image": {"image_size": 224},
    }
    return DeployConfig.from_mapping(raw, base_dir="/tmp", command_output_enabled=command_output_enabled)


def _loose_spec(
    *,
    camera_keys=("left", "right"),
    state_dim=16,
    action_dim=16,
    chunk_size=30,
    image_layout="CHW",
    image_dtype="float32",
    image_value_range=(0.0, 1.0),
    image_size=224,
):
    """A spec-like object B12 can inspect without PolicyInputSpec's own
    post-init enforcement (lets us exercise the negative contract codes)."""
    return SimpleNamespace(
        state_key="/act/observation/arm_state",
        state_dim=state_dim,
        image_prefix="/act/observation/image/",
        camera_keys=tuple(camera_keys),
        image_shapes=tuple((3, image_size, image_size) for _ in camera_keys),
        image_layout=image_layout,
        image_dtype=image_dtype,
        image_value_range=image_value_range,
        action_dim=action_dim,
        chunk_size=chunk_size,
    )


def _inference_service(spec):
    return SimpleNamespace(input_spec=spec)


def _pipeline(spec, clock):
    return SimpleNamespace(input_spec=spec, monotonic_clock=clock)


def _resources(spec):
    return SimpleNamespace(policy_input_spec=spec)


def _preflight_ok(*, spec, config, clock, command_output_enabled=False, permit_source=None):
    """Run preflight with a fully-canonical, consistent set; assert it passes."""
    run_startup_preflight(
        config=config,
        resources=_resources(spec),
        inference_service=_inference_service(spec),
        pipeline=_pipeline(spec, clock),
        request_queue=LatestQueue(),
        result_queue=LatestQueue(),
        command_output_enabled=command_output_enabled,
        permit_source=permit_source,
        monotonic_clock=clock,
    )


# ---------------------------------------------------------------------------
# Stable-code surface
# ---------------------------------------------------------------------------


def test_startup_contract_codes_are_stable():
    assert STARTUP_CONTRACT_CODES == (
        "SPEC_IDENTITY_MISMATCH",
        "STATE_DIM_MISMATCH",
        "ACTION_DIM_MISMATCH",
        "CHUNK_SIZE_MISMATCH",
        "CAMERA_KEYS_MISMATCH",
        "IMAGE_CONTRACT_MISMATCH",
        "QUEUE_CAPACITY_MISMATCH",
        "CLOCK_DOMAIN_MISMATCH",
        "PERMIT_SOURCE_MISSING",
    )


# ---------------------------------------------------------------------------
# Happy path — canonical, internally consistent
# ---------------------------------------------------------------------------


def test_preflight_passes_canonical_set():
    clock = lambda: 1000.0
    spec = _spec()
    config = _config()
    # No exception expected.
    _preflight_ok(spec=spec, config=config, clock=clock)


# ---------------------------------------------------------------------------
# Each violated invariant raises with the exact stable code
# ---------------------------------------------------------------------------


def test_spec_identity_mismatch_inference_service():
    clock = lambda: 1000.0
    spec = _spec()
    other_spec = _loose_spec(image_layout="HWC")  # distinct object
    config = _config()
    with pytest.raises(StartupContractError) as exc:
        run_startup_preflight(
            config=config,
            resources=_resources(spec),
            inference_service=_inference_service(other_spec),
            pipeline=_pipeline(spec, clock),
            request_queue=LatestQueue(),
            result_queue=LatestQueue(),
            command_output_enabled=False,
            permit_source=None,
            monotonic_clock=clock,
        )
    assert exc.value.code == "SPEC_IDENTITY_MISMATCH"


def test_spec_identity_mismatch_pipeline():
    clock = lambda: 1000.0
    spec = _spec()
    other_spec = _loose_spec(image_layout="HWC")
    config = _config()
    with pytest.raises(StartupContractError) as exc:
        run_startup_preflight(
            config=config,
            resources=_resources(spec),
            inference_service=_inference_service(spec),
            pipeline=_pipeline(other_spec, clock),
            request_queue=LatestQueue(),
            result_queue=LatestQueue(),
            command_output_enabled=False,
            permit_source=None,
            monotonic_clock=clock,
        )
    assert exc.value.code == "SPEC_IDENTITY_MISMATCH"


def test_state_dim_mismatch():
    clock = lambda: 1000.0
    spec = _spec(state_dim=16)
    config = _config(state_dim=15)  # allowed by schema, differs from spec
    with pytest.raises(StartupContractError) as exc:
        _preflight_ok(spec=spec, config=config, clock=clock)
    assert exc.value.code == "STATE_DIM_MISMATCH"


def test_action_dim_mismatch():
    clock = lambda: 1000.0
    spec = _spec(action_dim=16)
    config = _config(action_dim=15)
    with pytest.raises(StartupContractError) as exc:
        _preflight_ok(spec=spec, config=config, clock=clock)
    assert exc.value.code == "ACTION_DIM_MISMATCH"


def test_chunk_size_mismatch():
    clock = lambda: 1000.0
    spec = _spec(chunk_size=30)
    config = _config(chunk_size=29)
    with pytest.raises(StartupContractError) as exc:
        _preflight_ok(spec=spec, config=config, clock=clock)
    assert exc.value.code == "CHUNK_SIZE_MISMATCH"


def test_camera_keys_mismatch():
    clock = lambda: 1000.0
    spec = _loose_spec(camera_keys=("cam1", "cam2"))
    config = _config()  # default left/right
    with pytest.raises(StartupContractError) as exc:
        _preflight_ok(spec=spec, config=config, clock=clock)
    assert exc.value.code == "CAMERA_KEYS_MISMATCH"


def test_image_contract_mismatch_layout():
    clock = lambda: 1000.0
    spec = _loose_spec(image_layout="HWC")
    config = _config()
    with pytest.raises(StartupContractError) as exc:
        _preflight_ok(spec=spec, config=config, clock=clock)
    assert exc.value.code == "IMAGE_CONTRACT_MISMATCH"


def test_image_contract_mismatch_dtype():
    clock = lambda: 1000.0
    spec = _loose_spec(image_dtype="uint8")
    config = _config()
    with pytest.raises(StartupContractError) as exc:
        _preflight_ok(spec=spec, config=config, clock=clock)
    assert exc.value.code == "IMAGE_CONTRACT_MISMATCH"


def test_image_contract_mismatch_value_range():
    clock = lambda: 1000.0
    spec = _loose_spec(image_value_range=(0.0, 255.0))
    config = _config()
    with pytest.raises(StartupContractError) as exc:
        _preflight_ok(spec=spec, config=config, clock=clock)
    assert exc.value.code == "IMAGE_CONTRACT_MISMATCH"


def test_image_contract_mismatch_shapes():
    clock = lambda: 1000.0
    spec = _loose_spec(image_size=112)  # (3,112,112) != config (3,224,224)
    config = _config()
    with pytest.raises(StartupContractError) as exc:
        _preflight_ok(spec=spec, config=config, clock=clock)
    assert exc.value.code == "IMAGE_CONTRACT_MISMATCH"


def test_clock_domain_mismatch():
    clock = lambda: 1000.0
    other_clock = lambda: 2000.0
    spec = _spec()
    config = _config()
    with pytest.raises(StartupContractError) as exc:
        run_startup_preflight(
            config=config,
            resources=_resources(spec),
            inference_service=_inference_service(spec),
            pipeline=_pipeline(spec, other_clock),
            request_queue=LatestQueue(),
            result_queue=LatestQueue(),
            command_output_enabled=False,
            permit_source=None,
            monotonic_clock=clock,
        )
    assert exc.value.code == "CLOCK_DOMAIN_MISMATCH"


def test_queue_capacity_mismatch(monkeypatch):
    clock = lambda: 1000.0
    spec = _spec()
    config = _config()
    # Force the queue CAPACITY invariant off (schema guarantees ==1, but the
    # contract check must still catch a divergence).
    monkeypatch.setattr(LatestQueue, "CAPACITY", 2)
    with pytest.raises(StartupContractError) as exc:
        _preflight_ok(spec=spec, config=config, clock=clock)
    assert exc.value.code == "QUEUE_CAPACITY_MISMATCH"


def test_permit_source_missing_when_command_enabled():
    clock = lambda: 1000.0
    spec = _spec()
    config = _config(command_output_enabled=True)
    with pytest.raises(StartupContractError) as exc:
        _preflight_ok(
            spec=spec, config=config, clock=clock, command_output_enabled=True,
            permit_source=None,
        )
    assert exc.value.code == "PERMIT_SOURCE_MISSING"


def test_permit_source_present_when_command_enabled_passes():
    clock = lambda: 1000.0
    spec = _spec()
    config = _config(command_output_enabled=True)
    # A real permit source is supplied -> fail-closed gate opens cleanly.
    _preflight_ok(
        spec=spec, config=config, clock=clock, command_output_enabled=True,
        permit_source=lambda: None,
    )
