"""Native LeRobot ACT checkpoint source and metadata tests."""

import json
from pathlib import Path

import pytest

from model_deploy.act.config import DeployConfig
from model_deploy.act.repo import (
    ModelSourceError,
    load_checkpoint_metadata,
    load_act_runtime_resources,
    resolve_model_source,
)


def _make_checkpoint(tmp_path: Path) -> Path:
    checkpoint = tmp_path / "checkpoints" / "100000"
    pretrained = checkpoint / "pretrained_model"
    pretrained.mkdir(parents=True)
    (pretrained / "model.safetensors").write_bytes(b"test")

    config = {
        "input_features": {
            "observation.state": {"shape": [16]},
            "observation.images.left": {"shape": [3, 480, 640]},
            "observation.images.right": {"shape": [3, 480, 640]},
        },
        "output_features": {"action": {"shape": [16]}},
        "chunk_size": 100,
    }
    (pretrained / "config.json").write_text(json.dumps(config), encoding="utf-8")
    (pretrained / "policy_preprocessor.json").write_text(
        json.dumps(
            {
                "steps": [
                    {
                        "registry_name": "normalizer_processor",
                        "state_file": "input.safetensors",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    (pretrained / "policy_postprocessor.json").write_text(
        json.dumps(
            {
                "steps": [
                    {
                        "registry_name": "unnormalizer_processor",
                        "state_file": "output.safetensors",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    (pretrained / "input.safetensors").write_bytes(b"test")
    (pretrained / "output.safetensors").write_bytes(b"test")
    return checkpoint


def test_checkpoint_root_resolves_to_pretrained_model(tmp_path: Path) -> None:
    checkpoint = _make_checkpoint(tmp_path)

    source = resolve_model_source(checkpoint)

    assert source.is_checkpoint
    assert source.pretrained_dir == checkpoint / "pretrained_model"


def test_pretrained_model_directory_is_accepted(tmp_path: Path) -> None:
    checkpoint = _make_checkpoint(tmp_path)

    source = resolve_model_source(checkpoint / "pretrained_model")

    assert source.requested_path == checkpoint / "pretrained_model"
    assert source.pretrained_dir == checkpoint / "pretrained_model"


def test_checkpoint_metadata_reads_native_contract(tmp_path: Path) -> None:
    checkpoint = _make_checkpoint(tmp_path)

    metadata = load_checkpoint_metadata(resolve_model_source(checkpoint))

    assert metadata.state_dim == 16
    assert metadata.action_dim == 16
    assert metadata.chunk_size == 100
    assert metadata.camera_keys == ("left", "right")
    assert metadata.image_shapes == ((3, 480, 640), (3, 480, 640))
    assert metadata.input_stats_path.name == "input.safetensors"
    assert metadata.output_stats_path.name == "output.safetensors"


def test_native_checkpoint_aggregates_identity_deployment_normalizers(
    tmp_path: Path,
) -> None:
    checkpoint = _make_checkpoint(tmp_path)
    config = DeployConfig.from_mapping(
        {
            "model": {"checkpoint_dir": str(checkpoint)},
            "runtime": {
                "device": "cpu",
                "chunk_size": 100,
                "state_dim": 16,
                "action_dim": 16,
            },
            "image": {"image_size": 640, "image_shape": [480, 640]},
            "topics": {"namespace": "/act"},
            "safety": {},
        },
        base_dir=tmp_path,
    )

    resources = load_act_runtime_resources(
        config, load_policy=lambda source: ("fake", source)
    )

    assert resources.model_source_kind == "checkpoint"
    assert resources.checkpoint_dir == checkpoint
    assert resources.state_normalizer.normalize([2.0] * 16)[0] == 2.0
    assert resources.action_normalizer.unnormalize([-3.0] * 16)[0] == -3.0


def test_checkpoint_missing_model_file_fails_fast(tmp_path: Path) -> None:
    checkpoint = _make_checkpoint(tmp_path)
    (checkpoint / "pretrained_model" / "model.safetensors").unlink()

    with pytest.raises(ModelSourceError, match="model.safetensors"):
        resolve_model_source(checkpoint)


def test_unknown_model_source_fails_fast(tmp_path: Path) -> None:
    empty = tmp_path / "empty"
    empty.mkdir()

    with pytest.raises(ModelSourceError, match="neither"):
        resolve_model_source(empty)
