"""Version-acceptance check: official dataset -> processor -> ACT backward."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any


def run_act_acceptance(
    *,
    root: str | Path,
    repo_id: str,
) -> dict[str, Any]:
    """Run a deliberately small ACT model against one real loader batch.

    This is a CI/version acceptance check, not a per-production-job gate.
    """

    import torch
    from torch.utils.data import DataLoader

    from lerobot.configs.types import FeatureType, PolicyFeature
    from lerobot.datasets.lerobot_dataset import LeRobotDataset
    from lerobot.policies.act.configuration_act import ACTConfig
    from lerobot.policies.act.modeling_act import ACTPolicy
    from lerobot.policies.act.processor_act import make_act_pre_post_processors

    torch.manual_seed(0)
    dataset = LeRobotDataset(
        repo_id,
        root=Path(root).expanduser().resolve(),
        delta_timestamps={"action": [index / 15 for index in range(100)]},
        video_backend="torchcodec",
    )
    raw_batch = next(
        iter(DataLoader(dataset, batch_size=1, shuffle=False, num_workers=0))
    )
    input_features = {
        "observation.state": PolicyFeature(FeatureType.STATE, (16,)),
        "observation.images.left": PolicyFeature(
            FeatureType.VISUAL,
            (3, 480, 640),
        ),
        "observation.images.right": PolicyFeature(
            FeatureType.VISUAL,
            (3, 480, 640),
        ),
    }
    output_features = {
        "action": PolicyFeature(FeatureType.ACTION, (16,)),
    }
    config = ACTConfig(
        input_features=input_features,
        output_features=output_features,
        device="cpu",
        pretrained_backbone_weights=None,
        dim_model=64,
        n_heads=4,
        dim_feedforward=128,
        n_encoder_layers=1,
        n_decoder_layers=1,
        n_vae_encoder_layers=1,
        latent_dim=8,
    )
    preprocessor, _postprocessor = make_act_pre_post_processors(
        config,
        dataset_stats=dataset.meta.stats,
    )
    batch = preprocessor(raw_batch)
    policy = ACTPolicy(config)
    loss, loss_details = policy.forward(batch)
    if not torch.isfinite(loss):
        raise RuntimeError("ACT acceptance loss is not finite")
    loss.backward()
    gradients = [
        parameter.grad
        for parameter in policy.parameters()
        if parameter.grad is not None
    ]
    if not gradients or not all(torch.isfinite(value).all() for value in gradients):
        raise RuntimeError("ACT acceptance backward produced invalid gradients")
    return {
        "status": "passed",
        "repo_id": repo_id,
        "batch": {
            key: list(value.shape)
            for key, value in batch.items()
            if isinstance(value, torch.Tensor)
            and key
            in {
                "observation.state",
                "observation.images.left",
                "observation.images.right",
                "action",
                "action_is_pad",
            }
        },
        "loss": float(loss.detach()),
        "loss_details": loss_details,
        "gradient_tensors": len(gradients),
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--repo-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        report = run_act_acceptance(root=args.root, repo_id=args.repo_id)
        return_code = 0
    except Exception as exc:  # noqa: BLE001 - serialize the acceptance boundary.
        report = {
            "status": "failed",
            "error": {"type": type(exc).__name__, "message": str(exc)},
        }
        return_code = 1
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_name(
        f".{args.output.name}.{os.getpid()}.tmp"
    )
    temporary.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    os.replace(temporary, args.output)
    return return_code


if __name__ == "__main__":
    raise SystemExit(main())
