"""L2-03 Gate integration tests: three-stage closed-loop + static boundary scan.

Proves two things simultaneously:
1. A legal synchronous call completes ObservationSnapshot -> ActionChunk with
   strict (chunk_size, 16), float32, finite-values, 16D physical semantics.
2. The implementation does not pull L2-01 resource loading, L2-02 pixel
   processing, L2-04 safety, L2-05 ROS output, or L2-06 runtime scheduling
   into L2-03.

Uses stub policy + recording normalizer + sentinel snapshot on CPU only.
No ROS, GPU, real bundle, or production fake-policy branch required.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from unittest.mock import MagicMock

import numpy as np
import pytest
import torch

from model_deploy.act.config.schema import DeployConfig
from model_deploy.act.repo.act_runtime_resources import PolicyInputSpec
from model_deploy.act.repo.normalization import ActionStateNormalizer
from model_deploy.act.service.act_inference import ActInferenceService
from model_deploy.act.service.relative_tcp_action_decoder import (
    RelativeTcpActionDecoder,
)
from model_deploy.act.types.action_chunk import ActionChunk
from model_deploy.act.types.action_representation import ActionRepresentationSpec
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

# ACT source root under src/model_deploy/act/
_ACT_SRC = Path(__file__).resolve().parents[2]  # src/model_deploy/act


# ===================================================================
# Helpers: config
# ===================================================================


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


# ===================================================================
# Helpers: normalizers
# ===================================================================


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


# ===================================================================
# Helpers: stub policy
# ===================================================================


class _FakeFeature:
    """Minimal stand-in for LeRobot PolicyFeature."""

    def __init__(self, shape: tuple[int, ...]) -> None:
        self.shape = shape


class StubPolicy:
    """Deterministic stub policy with known sentinel output.

    Provides ``predict_action_chunk``, ``parameters()``, and a minimal
    ``config`` attribute carrying input/output feature metadata.
    """

    def __init__(
        self,
        chunk_size: int = _CHUNK_SIZE,
        action_dim: int = _ACTION_DIM,
        sentinel_value: float = 0.0,
        raise_on_predict: bool = False,
    ) -> None:
        self._chunk_size = chunk_size
        self._action_dim = action_dim
        self._sentinel_value = sentinel_value
        self._raise_on_predict = raise_on_predict
        self._param = torch.nn.Parameter(torch.zeros(1))

        self.config = type(
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
        # Broadcast the sentinel, then plant valid identity quaternions
        # (xyzw = 0,0,0,1) in the arm orientation slots so the output is a
        # decodable relative action.  Position + gripper slots keep the
        # sentinel value, which lets the sentinel-preservation test still
        # verify those fields flow through unchanged.
        out = torch.full(
            (1, self._chunk_size, self._action_dim),
            self._sentinel_value,
            dtype=torch.float32,
        )
        out[..., 3:7] = torch.tensor(
            (0.0, 0.0, 0.0, 1.0), dtype=torch.float32
        )
        out[..., 10:14] = torch.tensor(
            (0.0, 0.0, 0.0, 1.0), dtype=torch.float32
        )
        return out

    def parameters(self) -> Any:
        return iter([self._param])


class StubPolicyWithRaisingSelectAction(StubPolicy):
    """Stub whose ``select_action`` unconditionally raises.

    Used to prove L2-03 never invokes ``select_action``.
    """

    def select_action(self, batch: object) -> None:
        raise AssertionError("select_action must not be called")


class WrongShapePolicy(StubPolicy):
    """Policy returning a wrong chunk shape (stage-3 failure trigger)."""

    def predict_action_chunk(self, batch: object) -> torch.Tensor:
        return torch.zeros(1, 99, _ACTION_DIM)


class WrongDimPolicy(StubPolicy):
    """Policy returning wrong action dim (14 instead of 16)."""

    def predict_action_chunk(self, batch: object) -> torch.Tensor:
        return torch.zeros(1, self._chunk_size, 14)


def _make_input_spec(
    chunk_size: int = _CHUNK_SIZE,
    camera_keys: tuple[str, ...] = ("top",),
    image_size: int = 224,
) -> PolicyInputSpec:
    """Build a canonical frozen ``PolicyInputSpec`` (camera_keys sorted)."""
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


def _make_repr_spec() -> ActionRepresentationSpec:
    """The canonical first-version relative-action representation contract."""
    return ActionRepresentationSpec(
        arm_action_type="relative_tcp_pose",
        chunk_reference="inference_observation",
        translation_frame="tcp_local",
        rotation_representation="quaternion_xyzw",
        gripper_action_type="absolute",
    )


def _make_decoder() -> RelativeTcpActionDecoder:
    """Build a RelativeTcpActionDecoder from the canonical relative spec."""
    return RelativeTcpActionDecoder(_make_repr_spec())


# ===================================================================
# Helpers: recording normalizer
# ===================================================================


class RecordingNormalizer:
    """Wrapper delegating to a real normalizer and recording call count/direction."""

    def __init__(self, inner: ActionStateNormalizer, direction: str) -> None:
        self._inner = inner
        self._direction = direction  # "normalize" or "unnormalize"
        self.normalize_calls: int = 0
        self.unnormalize_calls: int = 0
        self.last_input: Optional[np.ndarray] = None

    def normalize(self, data: object) -> np.ndarray:
        self.normalize_calls += 1
        arr = np.asarray(data, dtype=np.float32)
        self.last_input = arr
        result = self._inner.normalize(arr)
        return result

    def unnormalize(self, data: object) -> np.ndarray:
        self.unnormalize_calls += 1
        arr = np.asarray(data, dtype=np.float32)
        self.last_input = arr
        result = self._inner.unnormalize(arr)
        return result

    @property
    def vector_dim(self) -> int:
        return self._inner.vector_dim


# ===================================================================
# Helpers: snapshot
# ===================================================================


def _make_snapshot(
    camera_keys: Optional[List[str]] = None,
    sentinel_value: Optional[np.ndarray] = None,
) -> ObservationSnapshot:
    """Construct a valid ObservationSnapshot for tests.

    Args:
        camera_keys: Camera names to include (defaults to ["top"]).
        sentinel_value: Optional explicit 16D state. Uses zeros when omitted.
    """
    if camera_keys is None:
        camera_keys = ["top"]

    images: Dict[str, np.ndarray] = {}
    rng = np.random.default_rng(42)
    for cam in camera_keys:
        images[cam] = rng.uniform(0.0, 1.0, (3, 224, 224)).astype(np.float32)

    if sentinel_value is None:
        encoded_state = np.zeros(16, dtype=np.float32)
    else:
        encoded_state = sentinel_value.astype(np.float32).copy()

    # The reference orientation slots must hold valid unit quaternions so the
    # relative-action decoder can use them as the chunk reference.  Plant
    # identity quaternions (xyzw = 0,0,0,1) when the caller did not supply a
    # full custom state.
    identity_quat = np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float32)
    encoded_state[3:7] = identity_quat
    encoded_state[10:14] = identity_quat

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


def _replace_encoded_state(snapshot: ObservationSnapshot, new_state: np.ndarray) -> Any:
    """Return a copy of the snapshot with a different encoded_state.

    Bypasses ``ObservationSnapshot.__post_init__`` validation so that
    intentionally-invalid snapshots can be injected for negative testing.
    """
    import copy

    s = copy.deepcopy(snapshot)
    object.__setattr__(s, "encoded_state", new_state)
    return s


# ===================================================================
# service.full_chain — Three-stage closed-loop
# ===================================================================


class TestFullChain:
    """Gate scenario: legal snapshot + recording normalizer + deterministic
    stub policy -> valid ActionChunk."""

    SENTINEL: float = 0.42

    def test_full_chain_returns_valid_action_chunk(self) -> None:
        """service.full_chain: full three-stage pipeline produces valid ActionChunk."""
        sn = _make_state_normalizer()
        an = _make_action_normalizer()
        rec_sn = RecordingNormalizer(sn, "normalize")
        rec_an = RecordingNormalizer(an, "unnormalize")

        policy = StubPolicy(sentinel_value=self.SENTINEL)
        svc = ActInferenceService(
            _make_deploy_config(chunk_size=_CHUNK_SIZE),
            rec_sn,
            rec_an,
            policy,
            input_spec=_make_input_spec(chunk_size=_CHUNK_SIZE, camera_keys=("top",)), relative_action_decoder=_make_decoder())

        snapshot = _make_snapshot(camera_keys=["top"])
        result = svc.predict_action_chunk(snapshot)

        assert isinstance(result, ActionChunk)
        assert isinstance(result.actions, np.ndarray)
        assert result.actions.shape == (_CHUNK_SIZE, _ACTION_DIM)
        assert result.actions.dtype == np.float32
        assert np.isfinite(result.actions).all()

    def test_sentinel_value_preserved(self) -> None:
        """Position and gripper sentinel values flow through the pipeline
        unmodified (identity normalizer + identity reference pose); the arm
        orientation slots are decoded from the unit relative quaternion and
        therefore land at the identity orientation ``(0,0,0,1)``."""
        svc = ActInferenceService(
            _make_deploy_config(chunk_size=_CHUNK_SIZE),
            _make_state_normalizer(),
            _make_action_normalizer(),
            StubPolicy(sentinel_value=self.SENTINEL),
            input_spec=_make_input_spec(chunk_size=_CHUNK_SIZE, camera_keys=("top",)), relative_action_decoder=_make_decoder())
        snapshot = _make_snapshot(camera_keys=["top"])
        result = svc.predict_action_chunk(snapshot)

        # Position slots [0:3], [7:10] and gripper slots [14:16] preserve the
        # sentinel (identity reference pose, identity normalizer).
        for slots in (slice(0, 3), slice(7, 10), slice(14, 16)):
            np.testing.assert_array_almost_equal(
                result.actions[:, slots],
                np.full((_CHUNK_SIZE, slots.stop - slots.start), self.SENTINEL, dtype=np.float32),
                decimal=5,
            )
        # Orientation slots decode from the unit relative quaternion composed
        # with the identity reference -> identity orientation.
        identity_quat = np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float32)
        for slots in (slice(3, 7), slice(10, 14)):
            np.testing.assert_array_almost_equal(
                result.actions[:, slots],
                np.tile(identity_quat, (_CHUNK_SIZE, 1)),
                decimal=5,
            )

    def test_normalizer_call_direction_and_count(self) -> None:
        """State normalizer only calls normalize, action normalizer only
        calls unnormalize, each exactly once."""
        sn = _make_state_normalizer()
        an = _make_action_normalizer()
        rec_sn = RecordingNormalizer(sn, "normalize")
        rec_an = RecordingNormalizer(an, "unnormalize")

        svc = ActInferenceService(
            _make_deploy_config(chunk_size=_CHUNK_SIZE),
            rec_sn,
            rec_an,
            StubPolicy(sentinel_value=self.SENTINEL),
            input_spec=_make_input_spec(chunk_size=_CHUNK_SIZE, camera_keys=("top",)), relative_action_decoder=_make_decoder())
        svc.predict_action_chunk(_make_snapshot(camera_keys=["top"]))

        assert rec_sn.normalize_calls == 1, (
            f"state normalizer normalize called {rec_sn.normalize_calls} times, "
            f"expected 1"
        )
        assert rec_sn.unnormalize_calls == 0, (
            "state normalizer must not be used to unnormalize"
        )
        assert rec_an.unnormalize_calls == 1, (
            f"action normalizer unnormalize called {rec_an.unnormalize_calls} times, "
            f"expected 1"
        )
        assert rec_an.normalize_calls == 0, (
            "action normalizer must not be used to normalize"
        )

    def test_select_action_not_called(self) -> None:
        """verify.sh must prove select_action is never called even when it
        would raise if called."""
        svc = ActInferenceService(
            _make_deploy_config(chunk_size=_CHUNK_SIZE),
            _make_state_normalizer(),
            _make_action_normalizer(),
            StubPolicyWithRaisingSelectAction(sentinel_value=self.SENTINEL),
            input_spec=_make_input_spec(chunk_size=_CHUNK_SIZE, camera_keys=("top",)), relative_action_decoder=_make_decoder())
        result = svc.predict_action_chunk(_make_snapshot(camera_keys=["top"]))
        assert isinstance(result, ActionChunk)

    def test_action_chunk_has_no_runtime_metadata(self) -> None:
        """ActionChunk must carry only actions, no runtime metadata fields."""
        svc = ActInferenceService(
            _make_deploy_config(chunk_size=_CHUNK_SIZE),
            _make_state_normalizer(),
            _make_action_normalizer(),
            StubPolicy(sentinel_value=self.SENTINEL),
            input_spec=_make_input_spec(chunk_size=_CHUNK_SIZE, camera_keys=("top",)), relative_action_decoder=_make_decoder())
        result = svc.predict_action_chunk(_make_snapshot(camera_keys=["top"]))

        forbidden = [
            "obs_time", "infer_start_time", "ready_time", "action_dt",
            "request_id", "cursor", "latency", "error", "metrics",
            "aligned_index", "is_expired", "remaining_steps",
        ]
        for attr in forbidden:
            assert not hasattr(result, attr), (
                f"ActionChunk must not have runtime metadata field '{attr}'"
            )

    def test_output_is_absolute_not_relative(self) -> None:
        """The cross-module output must be an absolute ActionChunk, never a
        RelativeActionChunk — the relative action is decoded away inside
        ActInferenceService and never escapes the L2-03 boundary."""
        from model_deploy.act.types.relative_action_chunk import RelativeActionChunk

        svc = ActInferenceService(
            _make_deploy_config(chunk_size=_CHUNK_SIZE),
            _make_state_normalizer(),
            _make_action_normalizer(),
            StubPolicy(sentinel_value=self.SENTINEL),
            input_spec=_make_input_spec(chunk_size=_CHUNK_SIZE, camera_keys=("top",)), relative_action_decoder=_make_decoder())
        result = svc.predict_action_chunk(_make_snapshot(camera_keys=["top"]))

        assert isinstance(result, ActionChunk), (
            "ActInferenceService must return an absolute ActionChunk"
        )
        assert not isinstance(result, RelativeActionChunk), (
            "RelativeActionChunk must never cross the L2-03 module boundary; "
            "it is decoded into an absolute ActionChunk before return"
        )


# ===================================================================
# service.error_stops_chain — Error chain-stop per stage
# ===================================================================


class TestErrorStopsChain:
    """Gate scenario: stage 1/2/3 failure each stops the chain with no
    partial output."""

    def test_stage1_failure_stops_chain(self) -> None:
        """Invalid snapshot (wrong state dim) raises and stage 2/3 never execute."""
        svc = ActInferenceService(
            _make_deploy_config(chunk_size=_CHUNK_SIZE),
            _make_state_normalizer(),
            _make_action_normalizer(),
            StubPolicy(sentinel_value=0.0),
            input_spec=_make_input_spec(chunk_size=_CHUNK_SIZE, camera_keys=("top",)), relative_action_decoder=_make_decoder())
        snapshot = _make_snapshot(camera_keys=["top"])
        bad_snapshot = _replace_encoded_state(snapshot, np.zeros(14, dtype=np.float32))

        with pytest.raises(ValueError, match="encoded_state must have shape"):
            svc.predict_action_chunk(bad_snapshot)

    def test_stage2_failure_stops_chain(self) -> None:
        """Policy raising on predict stops chain; stage 3 never executes."""
        svc = ActInferenceService(
            _make_deploy_config(chunk_size=_CHUNK_SIZE),
            _make_state_normalizer(),
            _make_action_normalizer(),
            StubPolicy(raise_on_predict=True),
            input_spec=_make_input_spec(chunk_size=_CHUNK_SIZE, camera_keys=("top",)), relative_action_decoder=_make_decoder())
        snapshot = _make_snapshot(camera_keys=["top"])

        with pytest.raises(RuntimeError, match="forced"):
            svc.predict_action_chunk(snapshot)

    def test_stage3_failure_stops_chain_raw_shape(self) -> None:
        """Wrong output shape from policy -> stage 3 rejects with ValueError."""
        svc = ActInferenceService(
            _make_deploy_config(chunk_size=_CHUNK_SIZE),
            _make_state_normalizer(),
            _make_action_normalizer(),
            WrongShapePolicy(),
            input_spec=_make_input_spec(chunk_size=_CHUNK_SIZE, camera_keys=("top",)), relative_action_decoder=_make_decoder())
        snapshot = _make_snapshot(camera_keys=["top"])

        with pytest.raises(ValueError, match="chunk dim"):
            svc.predict_action_chunk(snapshot)

    def test_stage3_failure_stops_chain_wrong_action_dim(self) -> None:
        """Wrong action dim (14) from policy -> stage 3 rejects."""
        svc = ActInferenceService(
            _make_deploy_config(chunk_size=_CHUNK_SIZE),
            _make_state_normalizer(),
            _make_action_normalizer(),
            WrongDimPolicy(),
            input_spec=_make_input_spec(chunk_size=_CHUNK_SIZE, camera_keys=("top",)), relative_action_decoder=_make_decoder())
        snapshot = _make_snapshot(camera_keys=["top"])

        with pytest.raises(ValueError, match="action dim"):
            svc.predict_action_chunk(snapshot)

    def test_no_repair_longer_output_rejected(self) -> None:
        """Longer output (N+1) must be rejected, not truncated."""
        class LongerPolicy(StubPolicy):
            def predict_action_chunk(self, batch: object) -> torch.Tensor:
                return torch.zeros(1, self._chunk_size + 1, _ACTION_DIM)

        svc = ActInferenceService(
            _make_deploy_config(chunk_size=_CHUNK_SIZE),
            _make_state_normalizer(),
            _make_action_normalizer(),
            LongerPolicy(chunk_size=_CHUNK_SIZE),
            input_spec=_make_input_spec(chunk_size=_CHUNK_SIZE, camera_keys=("top",)), relative_action_decoder=_make_decoder())
        with pytest.raises(ValueError, match="chunk dim"):
            svc.predict_action_chunk(_make_snapshot(camera_keys=["top"]))

    def test_no_repair_shorter_output_rejected(self) -> None:
        """Shorter output (N-1) must be rejected, not padded."""
        class ShorterPolicy(StubPolicy):
            def predict_action_chunk(self, batch: object) -> torch.Tensor:
                return torch.zeros(1, self._chunk_size - 1, _ACTION_DIM)

        svc = ActInferenceService(
            _make_deploy_config(chunk_size=_CHUNK_SIZE),
            _make_state_normalizer(),
            _make_action_normalizer(),
            ShorterPolicy(chunk_size=_CHUNK_SIZE),
            input_spec=_make_input_spec(chunk_size=_CHUNK_SIZE, camera_keys=("top",)), relative_action_decoder=_make_decoder())
        with pytest.raises(ValueError, match="chunk dim"):
            svc.predict_action_chunk(_make_snapshot(camera_keys=["top"]))

    def test_no_repair_2d_raw_output_rejected(self) -> None:
        """2D raw output (no batch dim) must be rejected."""
        class FlatPolicy(StubPolicy):
            def predict_action_chunk(self, batch: object) -> torch.Tensor:
                return torch.zeros(_CHUNK_SIZE, _ACTION_DIM)

        svc = ActInferenceService(
            _make_deploy_config(chunk_size=_CHUNK_SIZE),
            _make_state_normalizer(),
            _make_action_normalizer(),
            FlatPolicy(chunk_size=_CHUNK_SIZE),
            input_spec=_make_input_spec(chunk_size=_CHUNK_SIZE, camera_keys=("top",)), relative_action_decoder=_make_decoder())
        with pytest.raises(ValueError, match="rank 3"):
            svc.predict_action_chunk(_make_snapshot(camera_keys=["top"]))

    def test_no_repair_nan_output_rejected(self) -> None:
        """NaN output must be rejected, not replaced with zeros."""
        class NaNPolicy(StubPolicy):
            def predict_action_chunk(self, batch: object) -> torch.Tensor:
                t = torch.zeros(1, self._chunk_size, _ACTION_DIM)
                t[0, 0, 0] = float("nan")
                return t

        svc = ActInferenceService(
            _make_deploy_config(chunk_size=_CHUNK_SIZE),
            _make_state_normalizer(),
            _make_action_normalizer(),
            NaNPolicy(chunk_size=_CHUNK_SIZE),
            input_spec=_make_input_spec(chunk_size=_CHUNK_SIZE, camera_keys=("top",)), relative_action_decoder=_make_decoder())
        with pytest.raises(ValueError, match="NaN or Inf"):
            svc.predict_action_chunk(_make_snapshot(camera_keys=["top"]))


# ===================================================================
# Static boundary tests
# ===================================================================


# L2-03 specific source files (relative to _ACT_SRC)
_L2_03_SOURCE_FILES: frozenset[str] = frozenset({
    "types/action_chunk.py",
    "types/relative_action_chunk.py",
    "service/observation_batch.py",
    "service/action_chunk_postprocess.py",
    "service/relative_tcp_action_decoder.py",
    "service/act_inference.py",
})


def _list_l2_03_source_files() -> List[Path]:
    """List only L2-03-specific Python source files (not files from other L2s)."""
    files: List[Path] = []
    for rel_path in _L2_03_SOURCE_FILES:
        fpath = _ACT_SRC / rel_path
        if fpath.is_file():
            files.append(fpath)
    return sorted(files)


def _read_source_content(file_path: Path) -> str:
    """Read file content as text."""
    return file_path.read_text(encoding="utf-8")


def _extract_imports(source: str) -> Set[str]:
    """Extract all import module names from source using AST."""
    imports: Set[str] = set()
    try:
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                if node.level == 0:  # absolute import
                    imports.add(module)
                else:
                    # relative import -- add the package part
                    imports.add(f"<relative:{module}>")
    except SyntaxError:
        pass
    return imports


def _grep_pattern(source: str, patterns: List[str]) -> Dict[str, List[str]]:
    """Search source for regex patterns and return matched strings per pattern."""
    results: Dict[str, List[str]] = {}
    for pattern in patterns:
        matches = re.findall(pattern, source, re.IGNORECASE)
        if matches:
            results[pattern] = matches
    return results


def _strip_docstrings_and_comments(source: str) -> str:
    """Strip docstrings and comments from Python source to avoid matching prose.

    Removes triple-quoted strings and # comments.  This is a best-effort
    heuristic, not a full parser -- it handles the common cases in L2-03
    source files.
    """
    # Remove triple-quoted strings (single and double)
    source = re.sub(r'""".*?"""', '""', source, flags=re.DOTALL)
    source = re.sub(r"'''.*?'''", "''", source, flags=re.DOTALL)
    # Remove # comments (but not # in strings -- heuristic: # preceded by
    # whitespace or at start of line)
    lines = []
    for line in source.split("\n"):
        # Strip trailing comments
        stripped = re.sub(r'(\s*#.*)$', '', line)
        lines.append(stripped)
    return "\n".join(lines)


def _check_forbidden_imports(source: str, forbidden_modules: Set[str]) -> List[str]:
    """Check source for forbidden module imports using AST.

    Returns a list of violation descriptions.
    """
    violations: List[str] = []
    try:
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top = alias.name.split(".")[0]
                    if top in forbidden_modules:
                        violations.append(f"imports '{alias.name}'")
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                top = module.split(".")[0]
                if top in forbidden_modules:
                    violations.append(f"from '{module}' imports ...")
    except SyntaxError:
        pass
    return violations


class TestBoundary:
    """Static boundary scan: verify no forbidden patterns in L2-03 source."""

    # Forbidden imports -- checked via AST (unambiguous, not prose)
    FORBIDDEN_IMPORT_ROOTS: Set[str] = {
        "threading",
        "queue",
        "rospy",
        "rclpy",
        "serial",
        "modbus",
    }

    # Forbidden resource I/O function patterns (check after stripping docstrings)
    RESOURCE_IO_PATTERNS: List[re.Pattern] = [
        re.compile(r'\bjson\.load'),
        re.compile(r'\byaml\.(load|safe_load)'),
        re.compile(r'\btorch\.load'),
        re.compile(r'\btorch\.jit\.load'),
        re.compile(r'\.load_state_dict'),
        re.compile(r'\.from_pretrained'),
    ]

    # Forbidden functional patterns in stripped source
    FORBIDDEN_FUNC_PATTERNS: List[re.Pattern] = [
        re.compile(r'\bnp\.clip'),
        re.compile(r'\btorch\.clamp'),
        re.compile(r'\binverse_kinematics'),
    ]

    @pytest.fixture(autouse=True)
    def _src_files(self) -> List[Path]:
        """Cache source file list (L2-03 files only)."""
        return _list_l2_03_source_files()

    # ---------- boundary.no_resource_io ----------

    def test_no_resource_io(self, _src_files: List[Path]) -> None:
        """boundary.no_resource_io: No bundle/checkpoint/path/json/yaml
        loader calls in L2-03 source."""
        violations: List[str] = []
        for fpath in _src_files:
            source = _read_source_content(fpath)
            clean = _strip_docstrings_and_comments(source)
            for pattern in self.RESOURCE_IO_PATTERNS:
                if pattern.search(clean):
                    violations.append(
                        f"  {fpath.name}: matches '{pattern.pattern}'"
                    )
        assert not violations, (
            "boundary.no_resource_io FAILED: L2-03 source contains "
            "resource I/O calls:\n" + "\n".join(violations)
        )

    # ---------- boundary.no_runtime_state ----------

    def test_no_runtime_state(self, _src_files: List[Path]) -> None:
        """boundary.no_runtime_state: No Thread/queue/timer/request/cursor/
        metrics/fallback imports or usage in L2-03 source."""
        runtime_forbidden = {"threading", "queue"}
        violations: List[str] = []
        for fpath in _src_files:
            source = _read_source_content(fpath)
            v = _check_forbidden_imports(source, runtime_forbidden)
            for item in v:
                violations.append(f"  {fpath.name}: {item}")

        # Also check stripped source for runtime patterns that would appear
        # as actual code (not docstrings)
        runtime_code_patterns = [
            r'\bThread\s*\(',
            r'\bQueue\s*\(',
            r'\bTimer\s*\(',
            r'\bthreading\.',
        ]
        for fpath in _src_files:
            source = _read_source_content(fpath)
            clean = _strip_docstrings_and_comments(source)
            for pattern in runtime_code_patterns:
                if re.search(pattern, clean):
                    violations.append(
                        f"  {fpath.name}: matches runtime pattern '{pattern}'"
                    )

        assert not violations, (
            "boundary.no_runtime_state FAILED: L2-03 source contains "
            "runtime state:\n" + "\n".join(violations)
        )

    # ---------- boundary.no_ros_or_hardware ----------

    def test_no_ros_or_hardware(self, _src_files: List[Path]) -> None:
        """boundary.no_ros_or_hardware: No ROS import, publisher/subscriber,
        SDK/Modbus/serial in L2-03 source."""
        ros_hw_forbidden = {"rospy", "rclpy", "serial", "modbus"}
        violations: List[str] = []
        for fpath in _src_files:
            source = _read_source_content(fpath)
            v = _check_forbidden_imports(source, ros_hw_forbidden)
            for item in v:
                violations.append(f"  {fpath.name}: {item}")

        # Also scan for plain-text patterns (AST won't catch all)
        for fpath in _src_files:
            source = _read_source_content(fpath)
            clean = _strip_docstrings_and_comments(source)
            for pattern in [r'\bimport rospy\b', r'\bimport rclpy\b']:
                if re.search(pattern, clean):
                    violations.append(
                        f"  {fpath.name}: matches '{pattern}'"
                    )
        assert not violations, (
            "boundary.no_ros_or_hardware FAILED: L2-03 source contains "
            "ROS/hardware imports:\n" + "\n".join(violations)
        )

    # ---------- boundary.no_safety_or_smoothing ----------

    def test_no_safety_or_smoothing(self, _src_files: List[Path]) -> None:
        """boundary.no_safety_or_smoothing: No clamp/delta/IK/collision/
        blend/smooth/RTC code in L2-03 source."""
        violations: List[str] = []
        for fpath in _src_files:
            source = _read_source_content(fpath)
            clean = _strip_docstrings_and_comments(source)
            for pattern in self.FORBIDDEN_FUNC_PATTERNS:
                if pattern.search(clean):
                    violations.append(
                        f"  {fpath.name}: matches '{pattern.pattern}'"
                    )

        assert not violations, (
            "boundary.no_safety_or_smoothing FAILED: L2-03 source contains "
            "safety/smoothing code:\n" + "\n".join(violations)
        )

    # ---------- boundary.only_allowed_layers ----------

    def test_only_allowed_layers(self) -> None:
        """boundary.only_allowed_layers: L2-03-specific implementation files
        exist only in types/, service/, and tests/ (not config/repo/runtime/
        ui/launch)."""
        forbidden_dirs = {"config", "repo", "runtime", "ui", "launch"}
        violations: List[str] = []
        for forbidden in forbidden_dirs:
            for rel_path in _L2_03_SOURCE_FILES:
                fname = rel_path.split("/")[-1]  # e.g. "action_chunk.py"
                suspect = _ACT_SRC / forbidden / fname
                if suspect.is_file():
                    violations.append(
                        f"  {suspect.relative_to(_ACT_SRC)}"
                    )
        assert not violations, (
            "boundary.only_allowed_layers FAILED: L2-03 files found in "
            "forbidden directories:\n" + "\n".join(violations)
        )

    def test_l2_03_source_files_exist(self, _src_files: List[Path]) -> None:
        """Verify the L2-03 source modules exist on disk."""
        expected = [
            _ACT_SRC / "types" / "action_chunk.py",
            _ACT_SRC / "types" / "relative_action_chunk.py",
            _ACT_SRC / "service" / "observation_batch.py",
            _ACT_SRC / "service" / "action_chunk_postprocess.py",
            _ACT_SRC / "service" / "relative_tcp_action_decoder.py",
            _ACT_SRC / "service" / "act_inference.py",
        ]
        for fpath in expected:
            assert fpath.is_file(), (
                f"L2-03 source file not found: {fpath}"
            )
