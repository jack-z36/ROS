"""Unit tests for act_inference.py: ActInferenceService + run_act_inference.

Covers:
- Construction with valid dependencies
- Contract validation (dimension mismatch, missing predict_action_chunk)
- End-to-end inference with stub policy
- select_action spy (prove never called)
- Stage failure propagation (stage 1, 2, 3)
- Normalizer direction and call count
"""

from __future__ import annotations

import inspect
from pathlib import Path
from typing import Any, Dict
from unittest.mock import MagicMock

import numpy as np
import pytest
import torch

from model_deploy.act.config.schema import DeployConfig
from model_deploy.act.repo.act_runtime_resources import PolicyInputSpec
from model_deploy.act.repo.normalization import ActionStateNormalizer
from model_deploy.act.service.act_inference import (
    ActInferenceService,
    run_act_inference,
)
from model_deploy.act.types.action_chunk import ActionChunk
from model_deploy.act.types.observation import (
    ObservationSnapshot,
    ObservationState,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_CHUNK_SIZE: int = 10
_STATE_DIM: int = 16
_ACTION_DIM: int = 16


# ---------------------------------------------------------------------------
# Helpers: config
# ---------------------------------------------------------------------------


def _make_raw_config(chunk_size: int = _CHUNK_SIZE) -> Dict[str, Any]:
    """Minimal raw mapping accepted by DeployConfig.from_mapping."""
    return {
        "bundle": {"bundle_dir": "/tmp/test"},
        "runtime": {
            "mode": "dry-run",
            "control_hz": 30.0,
            "inference_hz": 10.0,
            "chunk_size": chunk_size,
            "execute_horizon": chunk_size,
            "state_dim": _STATE_DIM,
            "action_dim": _ACTION_DIM,
            "fallback_policy": "hold_last_action",
        },
        "image": {"image_size": 224},
        "topics": {"namespace": "/act"},
        "safety": {},
    }


def _make_deploy_config(**overrides: Any) -> DeployConfig:
    raw = _make_raw_config()
    raw["runtime"].update(overrides)
    return DeployConfig.from_mapping(raw, base_dir=Path("/tmp"))


# ---------------------------------------------------------------------------
# Helpers: normalizers
# ---------------------------------------------------------------------------


def _make_state_normalizer(dim: int = _STATE_DIM) -> ActionStateNormalizer:
    """Identity-like state normalizer (min=-1, max=1 -> range=2)."""
    return ActionStateNormalizer(
        min_vals=np.full(dim, -1.0, dtype=np.float32),
        max_vals=np.full(dim, 1.0, dtype=np.float32),
    )


def _make_action_normalizer(dim: int = _ACTION_DIM) -> ActionStateNormalizer:
    """Identity-like action normalizer (min=-1, max=1 -> range=2)."""
    return ActionStateNormalizer(
        min_vals=np.full(dim, -1.0, dtype=np.float32),
        max_vals=np.full(dim, 1.0, dtype=np.float32),
    )


def _make_input_spec(
    chunk_size: int = _CHUNK_SIZE,
    camera_keys: tuple[str, ...] = ("top",),
    image_size: int = 224,
) -> PolicyInputSpec:
    """Build a canonical frozen ``PolicyInputSpec`` for tests.

    ``camera_keys`` are sorted (PolicyInputSpec invariant) and ``image_shapes``
    are aligned positionally.  All other fields use the fixed 16D ACT contract.
    """
    cams = tuple(sorted(camera_keys))
    image_shapes = tuple((3, image_size, image_size) for _ in cams)
    return PolicyInputSpec(
        state_key="observation.state",
        state_dim=_STATE_DIM,
        image_prefix="observation.images.",
        camera_keys=cams,
        image_shapes=image_shapes,
        image_layout="CHW",
        image_dtype="float32",
        image_value_range=(0.0, 1.0),
        action_dim=_ACTION_DIM,
        chunk_size=chunk_size,
    )


# ---------------------------------------------------------------------------
# Helpers: stub policy
# ---------------------------------------------------------------------------


class _FakeFeature:
    """Minimal stand-in for LeRobot PolicyFeature."""

    def __init__(self, shape: tuple[int, ...]) -> None:
        self.shape = shape


class StubPolicy:
    """Trainable-like policy stub for ActInferenceService tests.

    Provides ``predict_action_chunk``, ``parameters()``, and a minimal
    ``config`` attribute carrying input/output feature metadata for
    ``input_spec`` derivation.
    """

    def __init__(
        self,
        chunk_size: int = _CHUNK_SIZE,
        action_dim: int = _ACTION_DIM,
        raise_on_predict: bool = False,
    ) -> None:
        self._chunk_size = chunk_size
        self._action_dim = action_dim
        self._raise_on_predict = raise_on_predict
        # Tiny parameter so _resolve_device() finds a device
        self._param = torch.nn.Parameter(torch.zeros(1))

        # Minimal config for _derive_input_spec
        self.config = type(  # type: ignore[attr-defined]
            "_Config",
            (),
            {
                "chunk_size": chunk_size,
                "input_features": {
                    "observation.state": _FakeFeature((action_dim,)),
                    "observation.images.top": _FakeFeature((3, 224, 224)),
                },
                "output_features": {
                    "action": _FakeFeature((action_dim,)),
                },
            },
        )()

    def predict_action_chunk(self, batch: object) -> torch.Tensor:
        if self._raise_on_predict:
            raise RuntimeError("forced predict_action_chunk failure")
        output = torch.zeros(1, self._chunk_size, self._action_dim)
        output[..., 3] = 0.0
        output[..., 6] = 1.0
        output[..., 10] = 0.0
        output[..., 13] = 1.0
        return output

    def parameters(self) -> Any:
        return iter([self._param])


class StubPolicyWithRaisingSelectAction(StubPolicy):
    """Stub whose ``select_action`` unconditionally raises.

    Used to prove L2-03 never invokes ``select_action``.
    """

    def select_action(self, batch: object) -> None:
        raise AssertionError("select_action must not be called")


# ---------------------------------------------------------------------------
# Helpers: snapshot
# ---------------------------------------------------------------------------


def _make_snapshot(camera_keys: list[str] | None = None) -> ObservationSnapshot:
    """Construct a valid ObservationSnapshot for tests."""
    if camera_keys is None:
        camera_keys = ["top"]

    rng = np.random.default_rng(42)
    images: Dict[str, np.ndarray] = {}
    for cam in camera_keys:
        images[cam] = rng.uniform(0.0, 1.0, (3, 224, 224)).astype(np.float32)

    encoded_state = np.zeros(16, dtype=np.float32)
    encoded_state[0:3] = rng.uniform(0.3, 0.5, 3)
    encoded_state[3:7] = np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float32)
    encoded_state[7:10] = rng.uniform(-0.2, 0.2, 3)
    encoded_state[10:14] = np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float32)
    encoded_state[14] = 0.5
    encoded_state[15] = 0.8

    obs_state = ObservationState(
        left_tcp_position=encoded_state[0:3].copy(),
        left_tcp_orientation=encoded_state[3:7].copy(),
        left_gripper_width=float(encoded_state[14]),
        right_tcp_position=encoded_state[7:10].copy(),
        right_tcp_orientation=encoded_state[10:14].copy(),
        right_gripper_width=float(encoded_state[15]),
    )

    return ObservationSnapshot(
        images=images,
        state=obs_state,
        encoded_state=encoded_state,
        captured_at_s=1000.0,
    )


# ===================================================================
# run_act_inference (standalone)
# ===================================================================


class TestRunActInference:
    """Primary stage 2: standalone function tests."""

    def test_returns_raw_tensor(self) -> None:
        policy = StubPolicy(chunk_size=10)
        batch: Dict[str, torch.Tensor] = {"observation.state": torch.zeros(1, 16)}
        result = run_act_inference(policy, batch)
        assert isinstance(result, torch.Tensor)
        assert result.shape == (1, 10, 16)

    def test_propagates_policy_error(self) -> None:
        policy = StubPolicy(raise_on_predict=True)
        batch = {"observation.state": torch.zeros(1, 16)}
        with pytest.raises(RuntimeError, match="forced"):
            run_act_inference(policy, batch)


# ===================================================================
# Construction
# ===================================================================


class TestConstruction:
    """ActInferenceService construction tests."""

    def test_creates_with_valid_dependencies(self) -> None:
        cfg = _make_deploy_config()
        svc = ActInferenceService(
            cfg,
            _make_state_normalizer(),
            _make_action_normalizer(),
            StubPolicy(),
            input_spec=_make_input_spec(),
        )
        assert svc is not None

    def test_input_spec_is_injected_by_identity(self) -> None:
        """L2-03 consumes the canonical spec by identity, no re-derivation."""
        cfg = _make_deploy_config(chunk_size=10)
        injected = _make_input_spec(chunk_size=10, camera_keys=("top",))

        svc = ActInferenceService(
            cfg,
            _make_state_normalizer(),
            _make_action_normalizer(),
            StubPolicy(chunk_size=10, action_dim=16),
            input_spec=injected,
        )

        # Public read-only property returns the identical object.
        assert svc.input_spec is injected
        # No Dict / copy / re-derived mapping.
        assert isinstance(svc.input_spec, PolicyInputSpec)
        assert svc.input_spec.state_dim == 16
        assert svc.input_spec.action_dim == 16
        assert svc.input_spec.chunk_size == 10
        assert svc.input_spec.state_key == "observation.state"
        assert svc.input_spec.camera_keys == ("top",)
        assert svc.input_spec.image_prefix == "observation.images."
        assert svc.input_spec.image_shapes == ((3, 224, 224),)

    def test_uses_injected_spec_even_without_policy_metadata(self) -> None:
        """No policy-metadata fallback: an explicit spec is required and used.

        A bare policy with no ``config`` attribute works as long as the
        canonical ``input_spec`` is injected.  This proves L2-03 no longer
        reads policy RAM metadata to derive the spec.
        """
        cfg = _make_deploy_config(chunk_size=30)

        class BarePolicy:
            def predict_action_chunk(self, batch: object) -> torch.Tensor:
                return torch.zeros(1, 30, 16)

            def parameters(self) -> Any:
                return iter([torch.nn.Parameter(torch.zeros(1))])

        injected = _make_input_spec(chunk_size=30, camera_keys=("top",))
        svc = ActInferenceService(
            cfg,
            _make_state_normalizer(),
            _make_action_normalizer(),
            BarePolicy(),
            input_spec=injected,
        )
        assert svc.input_spec is injected
        assert svc.input_spec.chunk_size == 30
        assert svc.input_spec.state_dim == 16
        assert svc.input_spec.action_dim == 16

    def test_requires_input_spec_argument(self) -> None:
        """input_spec is a required constructor argument (no silent default)."""
        cfg = _make_deploy_config()
        with pytest.raises(TypeError):
            ActInferenceService(
                cfg,
                _make_state_normalizer(),
                _make_action_normalizer(),
                StubPolicy(),
            )


# ===================================================================
# Contract validation
# ===================================================================


class TestContractValidation:
    """Constructor contract validation tests."""

    def test_raises_when_policy_missing_predict_action_chunk(self) -> None:
        class BadPolicy:
            def parameters(self) -> Any:
                return iter([torch.nn.Parameter(torch.zeros(1))])

        with pytest.raises(AttributeError, match="predict_action_chunk"):
            ActInferenceService(
                _make_deploy_config(),
                _make_state_normalizer(),
                _make_action_normalizer(),
                BadPolicy(),
                input_spec=_make_input_spec(),
            )

    def test_raises_on_state_normalizer_dimension_mismatch(self) -> None:
        with pytest.raises(ValueError, match="state_normalizer"):
            ActInferenceService(
                _make_deploy_config(),
                _make_state_normalizer(dim=8),  # policy expects 16
                _make_action_normalizer(),
                StubPolicy(),
                input_spec=_make_input_spec(),
            )

    def test_raises_on_action_normalizer_dimension_mismatch(self) -> None:
        with pytest.raises(ValueError, match="action_normalizer"):
            ActInferenceService(
                _make_deploy_config(),
                _make_state_normalizer(),
                _make_action_normalizer(dim=8),  # policy expects 16
                StubPolicy(),
                input_spec=_make_input_spec(),
            )


# ===================================================================
# Instance field audit
# ===================================================================


class TestInstanceFields:
    """Verify ActInferenceService has no forbidden fields."""

    def test_only_allowed_private_fields(self) -> None:
        svc = ActInferenceService(
            _make_deploy_config(),
            _make_state_normalizer(),
            _make_action_normalizer(),
            StubPolicy(),
            input_spec=_make_input_spec(),
        )

        allowed = {
            "_config",
            "_state_normalizer",
            "_action_normalizer",
            "_policy",
            "_input_spec",
            "_device",
            "_relative_tcp_action_decoder",
        }
        actual = set(vars(svc).keys())
        assert actual == allowed, (
            f"Unexpected attributes: {actual - allowed}\n"
            f"Missing attributes: {allowed - actual}"
        )

    def test_no_forbidden_field_names(self) -> None:
        svc = ActInferenceService(
            _make_deploy_config(),
            _make_state_normalizer(),
            _make_action_normalizer(),
            StubPolicy(),
            input_spec=_make_input_spec(),
        )

        forbidden = {
            "snapshot", "batch", "raw_chunk", "request_id",
            "thread", "event", "queue", "lock",
            "cursor", "history", "latency", "error",
            "metrics", "retry", "fallback",
        }
        names_lower = {k.lower() for k in vars(svc).keys()}
        for f in forbidden:
            assert f not in names_lower, f"Forbidden field name '{f}' detected"


# ===================================================================
# End-to-end
# ===================================================================


class TestEndToEnd:
    """Full-chain inference tests with stub policy."""

    def test_full_chain_returns_action_chunk(self) -> None:
        svc = ActInferenceService(
            _make_deploy_config(chunk_size=10),
            _make_state_normalizer(),
            _make_action_normalizer(),
            StubPolicy(chunk_size=10),
            input_spec=_make_input_spec(chunk_size=10, camera_keys=("top",)),
        )
        snapshot = _make_snapshot(camera_keys=["top"])
        result = svc.predict_action_chunk(snapshot)

        assert isinstance(result, ActionChunk)
        assert isinstance(result.actions, np.ndarray)
        assert result.actions.shape == (10, 16)
        assert result.actions.dtype == np.float32
        assert np.isfinite(result.actions).all()

    def test_select_action_never_called(self) -> None:
        """Prove select_action is not invoked even when it would raise."""
        svc = ActInferenceService(
            _make_deploy_config(chunk_size=10),
            _make_state_normalizer(),
            _make_action_normalizer(),
            StubPolicyWithRaisingSelectAction(chunk_size=10),
            input_spec=_make_input_spec(chunk_size=10, camera_keys=("top",)),
        )
        snapshot = _make_snapshot(camera_keys=["top"])
        # Must succeed — select_action is never called
        result = svc.predict_action_chunk(snapshot)
        assert isinstance(result, ActionChunk)


# ===================================================================
# Failure propagation
# ===================================================================


class TestFailurePropagation:
    """Each stage failure must propagate immediately."""

    def test_stage1_failure_propagates(self) -> None:
        # Spec requires two cameras, but the snapshot only carries "top".
        svc = ActInferenceService(
            _make_deploy_config(chunk_size=10),
            _make_state_normalizer(),
            _make_action_normalizer(),
            StubPolicy(chunk_size=10),
            input_spec=_make_input_spec(
                chunk_size=10, camera_keys=("left_wrist", "top")
            ),
        )
        snapshot = _make_snapshot(camera_keys=["top"])

        with pytest.raises(KeyError, match="missing required camera"):
            svc.predict_action_chunk(snapshot)

    def test_stage2_failure_propagates(self) -> None:
        svc = ActInferenceService(
            _make_deploy_config(chunk_size=10),
            _make_state_normalizer(),
            _make_action_normalizer(),
            StubPolicy(chunk_size=10, raise_on_predict=True),
            input_spec=_make_input_spec(chunk_size=10, camera_keys=("top",)),
        )
        snapshot = _make_snapshot(camera_keys=["top"])

        with pytest.raises(RuntimeError, match="forced"):
            svc.predict_action_chunk(snapshot)

    def test_stage3_failure_propagates(self) -> None:
        """Stage 3 rejects wrong output shape from policy."""

        class WrongShapePolicy(StubPolicy):
            def predict_action_chunk(self, batch: object) -> torch.Tensor:
                return torch.zeros(1, 99, 16)  # chunk_size is 10, not 99

        svc = ActInferenceService(
            _make_deploy_config(chunk_size=10),
            _make_state_normalizer(),
            _make_action_normalizer(),
            WrongShapePolicy(chunk_size=10),
            input_spec=_make_input_spec(chunk_size=10, camera_keys=("top",)),
        )
        snapshot = _make_snapshot(camera_keys=["top"])

        with pytest.raises(ValueError, match="chunk dim"):
            svc.predict_action_chunk(snapshot)


# ===================================================================
# No swallow / no fallback
# ===================================================================


class TestNoSwallowNoFallback:
    """Verify no try/except: return None / zeros / last_chunk patterns."""

    def test_predict_action_chunk_has_no_try_except(self) -> None:
        src = inspect.getsource(ActInferenceService.predict_action_chunk)
        assert "try:" not in src, (
            "predict_action_chunk must not swallow exceptions via try/except"
        )

    def test_no_return_none_pattern(self) -> None:
        src = inspect.getsource(ActInferenceService.predict_action_chunk)
        assert "return None" not in src
        assert "return  None" not in src

    def test_no_return_zeros_pattern(self) -> None:
        src = inspect.getsource(ActInferenceService.predict_action_chunk)
        assert "zeros" not in src, (
            "predict_action_chunk must not return zero tensors on failure"
        )


# ===================================================================
# Normalizer direction and call count
# ===================================================================


class TestNormalizerDirectionAndCount:
    """Verify state normalizer only calls normalize, action normalizer
    only calls unnormalize, each exactly once."""

    def test_state_normalizer_only_calls_normalize(self) -> None:
        sn = _make_state_normalizer()
        sn_mock = MagicMock(wraps=sn)
        # MagicMock(wraps=...) does not always forward data attributes;
        # manually forward the integer value so _validate_contract passes.
        sn_mock.vector_dim = sn.vector_dim

        svc = ActInferenceService(
            _make_deploy_config(chunk_size=10),
            sn_mock,
            _make_action_normalizer(),
            StubPolicy(chunk_size=10),
            input_spec=_make_input_spec(chunk_size=10, camera_keys=("top",)),
        )
        svc.predict_action_chunk(_make_snapshot(camera_keys=["top"]))

        sn_mock.normalize.assert_called_once()
        sn_mock.unnormalize.assert_not_called()

    def test_action_normalizer_only_calls_unnormalize(self) -> None:
        an = _make_action_normalizer()
        an_mock = MagicMock(wraps=an)
        an_mock.vector_dim = an.vector_dim

        svc = ActInferenceService(
            _make_deploy_config(chunk_size=10),
            _make_state_normalizer(),
            an_mock,
            StubPolicy(chunk_size=10),
            input_spec=_make_input_spec(chunk_size=10, camera_keys=("top",)),
        )
        svc.predict_action_chunk(_make_snapshot(camera_keys=["top"]))

        an_mock.unnormalize.assert_called_once()
        an_mock.normalize.assert_not_called()
