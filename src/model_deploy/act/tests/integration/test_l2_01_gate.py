"""L2 Gate integration tests for l2-01-external-contract — deploy_010.

End-to-end validation covering all 5 acceptance scenarios:
- S1: valid config loads successfully
- S2: invalid dimensions fail
- S3: missing bundle files fail
- S4: normalizer dimension mismatch fails
- S5: no smoothing config leakage
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from model_deploy.act.config.schema import (
    DeployConfig,
    DeployConfigError,
    load_deploy_config,
)
from model_deploy.act.types.action_spec import ACTION_DIM, ActionSpec, split_action
from model_deploy.act.types.contract_result import (
    BundleContractResult,
    NormalizerContractResult,
)
from model_deploy.act.types.state_spec import STATE_DIM, StateSpec, encode_state

# ---------------------------------------------------------------------------
# Forbidden smoothing fields (must NOT appear in source / config)
# ---------------------------------------------------------------------------

FORBIDDEN_FIELDS = (
    "blend_steps",
    "smoothstep",
    "cross_chunk",
    "rtc_alignment",
    "action_smoothing",
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_bundle(base: Path, *, state_dim: int = 16, action_dim: int = 16, missing: set[str] | None = None) -> Path:
    """Create a mock bundle directory."""
    bundle = base / "bundle"
    bundle.mkdir()
    missing = missing or set()

    if "adapter" not in missing:
        (bundle / "adapter").mkdir()

    if "checkpoint" not in missing:
        (bundle / "checkpoint.pt").write_text("dummy")

    if "manifest.json" not in missing:
        manifest = {
            "schema_version": 1,
            "model": {
                "pretrained_path": "checkpoint.pt",
                "state_dim": state_dim,
                "action_dim": action_dim,
                "chunk_size": 30,
            },
        }
        (bundle / "manifest.json").write_text(json.dumps(manifest))

    if "normalizers.json" not in missing:
        normalizers = {
            "state": {"min": [0.0] * state_dim, "max": [1.0] * state_dim, "identity_indices": []},
            "action": {"min": [-1.0] * action_dim, "max": [1.0] * action_dim, "identity_indices": []},
        }
        (bundle / "normalizers.json").write_text(json.dumps(normalizers))

    if "experiment_config.yaml" not in missing:
        exp = {"state_dim": state_dim, "action_dim": action_dim, "chunk_size": 30}
        (bundle / "experiment_config.yaml").write_text(yaml.safe_dump(exp))

    return bundle


def _write_deploy_yaml(path: Path, bundle_dir: str, **overrides) -> None:
    payload = {
        "bundle": {"bundle_dir": bundle_dir},
        "runtime": {
            "mode": "dry-run",
            "control_hz": 30.0,
            "inference_hz": 10.0,
            "chunk_size": 30,
            "execute_horizon": 10,
            "state_dim": 16,
            "action_dim": 16,
            "fallback_policy": "hold_last_action",
        },
        "image": {"image_size": 224},
        "topics": {"namespace": "/act"},
        "safety": {},
    }
    for section in ("runtime", "image", "topics", "safety"):
        if section in overrides:
            payload[section].update(overrides.pop(section))
    payload.update(overrides)
    path.write_text(yaml.safe_dump(payload))


# ---------------------------------------------------------------------------
# S1 — valid config loads successfully
# ---------------------------------------------------------------------------


def test_s1_legal_config_loads(tmp_path: Path) -> None:
    """S1: A complete legal deploy.yaml + mock bundle produces a valid DeployConfig."""
    bundle = _make_bundle(tmp_path)
    yaml_path = tmp_path / "deploy.yaml"
    _write_deploy_yaml(yaml_path, str(bundle))

    cfg = load_deploy_config(yaml_path)
    assert isinstance(cfg, DeployConfig)
    assert cfg.runtime.state_dim == 16
    assert cfg.runtime.action_dim == 16
    assert cfg.topics.namespace == "/act"
    assert cfg.safety.max_tcp_delta_per_step > 0

    # Verify types layer constants
    assert STATE_DIM == 16
    assert ACTION_DIM == 16

    # Verify StateSpec / ActionSpec work
    spec = StateSpec()
    assert spec.total_dim == 16
    action = split_action(list(range(16)))
    assert isinstance(action, ActionSpec)
    assert action.as_vector().shape == (16,)


# ---------------------------------------------------------------------------
# S2 — invalid dimensions fail
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("bad_dim", [15, 17, 14, 18])
def test_s2_invalid_dimension_fails(tmp_path: Path, bad_dim: int) -> None:
    """S2: Non-16 state_dim or action_dim causes contract failure."""
    bundle = _make_bundle(tmp_path, state_dim=bad_dim, action_dim=bad_dim)
    yaml_path = tmp_path / "deploy.yaml"
    _write_deploy_yaml(yaml_path, str(bundle))
    with pytest.raises(DeployConfigError):
        load_deploy_config(yaml_path)


# ---------------------------------------------------------------------------
# S3 — missing bundle files fail
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("missing_file", ["manifest.json", "normalizers.json", "checkpoint"])
def test_s3_bundle_missing_files_fails(tmp_path: Path, missing_file: str) -> None:
    """S3: Missing a required bundle file causes DeployConfigError."""
    bundle = _make_bundle(tmp_path, missing={missing_file})
    # Fix manifest so it doesn't reference a non-existent checkpoint
    if missing_file != "manifest.json":
        manifest = json.loads((bundle / "manifest.json").read_text())
        manifest["model"]["pretrained_path"] = "checkpoint.pt"
        (bundle / "manifest.json").write_text(json.dumps(manifest))

    yaml_path = tmp_path / "deploy.yaml"
    _write_deploy_yaml(yaml_path, str(bundle))
    with pytest.raises((DeployConfigError, FileNotFoundError)):
        load_deploy_config(yaml_path)


# ---------------------------------------------------------------------------
# S4 — normalizer dimension mismatch fails
# ---------------------------------------------------------------------------


def test_s4_normalizer_dim_mismatch_fails(tmp_path: Path) -> None:
    """S4: A normalizer with non-16 vector_dim causes contract failure."""
    bundle = _make_bundle(tmp_path, state_dim=14, action_dim=14)
    yaml_path = tmp_path / "deploy.yaml"
    _write_deploy_yaml(yaml_path, str(bundle))
    with pytest.raises(DeployConfigError) as exc_info:
        load_deploy_config(yaml_path)
    err_msg = str(exc_info.value)
    assert "14" in err_msg or "16" in err_msg


# ---------------------------------------------------------------------------
# S5 — no smoothing config leakage
# ---------------------------------------------------------------------------


def _scan_for_forbidden(root: Path, forbidden: tuple[str, ...]) -> list[str]:
    """Return list of 'file:line:match' strings where forbidden patterns appear."""
    hits: list[str] = []
    for fpath in sorted(root.rglob("*.py")):
        try:
            text = fpath.read_text()
        except Exception:
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            for pattern in forbidden:
                if pattern in line:
                    # Skip test files that intentionally reference the pattern
                    if "test_s5" in fpath.name or "FORBIDDEN_FIELDS" in line:
                        continue
                    hits.append(f"{fpath}:{lineno}:{pattern}")
    return hits


def test_s5_no_smoothing_config_leakage() -> None:
    """S5: No smoothing-related fields appear in ACT source or config files.

    Only scans source directories — tests and integration tests may
    intentionally reference forbidden patterns in assertions.
    """
    act_src_dirs = [
        Path("src/model_deploy/act/types"),
        Path("src/model_deploy/act/config"),
        Path("src/model_deploy/act/repo"),
        Path("src/model_deploy/act/service"),
        Path("src/model_deploy/act/runtime"),
        Path("src/model_deploy/act/ui"),
        Path("src/model_deploy/act/config_files"),
    ]

    hits: list[str] = []
    for src_dir in act_src_dirs:
        if src_dir.exists():
            hits.extend(_scan_for_forbidden(src_dir, FORBIDDEN_FIELDS))
    if hits:
        pytest.fail(
            "Forbidden smoothing fields found in ACT source/config:\n"
            + "\n".join(hits)
        )

    # Also check deploy.yaml
    deploy_yaml = Path("src/model_deploy/act/config_files/deploy.yaml")
    if deploy_yaml.exists():
        text = deploy_yaml.read_text()
        for pattern in FORBIDDEN_FIELDS:
            assert pattern not in text, f"Forbidden field '{pattern}' found in deploy.yaml"
