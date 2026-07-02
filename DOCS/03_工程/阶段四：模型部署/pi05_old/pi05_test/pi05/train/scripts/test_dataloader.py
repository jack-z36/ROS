#!/usr/bin/env python3
"""Sanity-check the Pi0.5 dataloader with one batch.

This script verifies:
- configured camera/tactile tensor layouts and value ranges
- normalized high-dimensional state range
- normalized 14D action chunk range
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
WORKSPACE_ROOT = PROJECT_ROOT.parents[1]
DEFAULT_DATASET_PATH = WORKSPACE_ROOT / "datasets" / "lerobot_data"
COMMON_SRC_ROOT = PROJECT_ROOT / "common" / "src"
TRAIN_SRC_ROOT = PROJECT_ROOT / "train" / "src"
LEROBOT_SRC = WORKSPACE_ROOT / "third_party" / "lerobot" / "src"

for path in (COMMON_SRC_ROOT, TRAIN_SRC_ROOT, LEROBOT_SRC):
    if path.exists() and str(path) not in sys.path:
        sys.path.insert(0, str(path))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect one batch from the Pi0.5 LeRobot dataloader.")
    parser.add_argument(
        "--dataset-path",
        type=Path,
        default=DEFAULT_DATASET_PATH,
        help="Path to a local LeRobot dataset directory.",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=30,
        help="Future action chunk length.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=4,
        help="Batch size for the smoke test.",
    )
    parser.add_argument(
        "--num-workers",
        type=int,
        default=2,
        help="Number of dataloader workers.",
    )
    parser.add_argument(
        "--disable-color-jitter",
        action="store_true",
        help="Disable online color jitter for deterministic inspection.",
    )
    parser.add_argument("--image-size", type=int, default=224, help="Model image size after Dataset transforms.")
    parser.add_argument("--state-dim", type=int, default=26, help="Expected observation.state dimension.")
    parser.add_argument("--action-dim", type=int, default=14, help="Expected action dimension.")
    parser.add_argument(
        "--cameras",
        nargs="+",
        default=["top", "left_wrist", "right_wrist"],
        help="Image camera keys to read, e.g. top left_wrist right_wrist left_tactile right_tactile.",
    )
    return parser.parse_args()


def describe_tensor(name: str, tensor: torch.Tensor) -> None:
    import torch

    print(f"{name}:")
    print(f"  shape = {tuple(tensor.shape)}")
    print(f"  dtype = {tensor.dtype}")
    print(f"  min   = {tensor.min().item():.6f}")
    print(f"  max   = {tensor.max().item():.6f}")


def main() -> None:
    args = parse_args()

    import torch
    from torch.utils.data import DataLoader

    from pi05.common.data.normalization import build_state_action_normalizers
    from pi05.train.data.dataset import Pi05LeRobotDataset

    dataset_path = args.dataset_path.expanduser().resolve()
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset path does not exist: {dataset_path}")

    bootstrap_dataset = Pi05LeRobotDataset(
        dataset_path=dataset_path,
        chunk_size=args.chunk_size,
        use_color_jitter=not args.disable_color_jitter,
        image_size=args.image_size,
        state_dim=args.state_dim,
        action_dim=args.action_dim,
        cameras=tuple(args.cameras),
    )
    state_normalizer, action_normalizer = build_state_action_normalizers(bootstrap_dataset.dataset)

    dataset = Pi05LeRobotDataset(
        dataset_path=dataset_path,
        chunk_size=args.chunk_size,
        use_color_jitter=not args.disable_color_jitter,
        image_size=args.image_size,
        state_dim=args.state_dim,
        action_dim=args.action_dim,
        cameras=tuple(args.cameras),
        state_normalizer=state_normalizer,
        action_normalizer=action_normalizer,
    )
    dataloader = DataLoader(
        dataset,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=args.num_workers,
        pin_memory=torch.cuda.is_available(),
    )

    for batch in dataloader:
        print(f"dataset_path = {dataset_path}")
        print(f"chunk_size   = {args.chunk_size}")
        print(f"batch_size   = {args.batch_size}")
        print(f"num_workers  = {args.num_workers}")
        print(f"cameras      = {args.cameras}")
        print("")
        for camera in args.cameras:
            describe_tensor(f"image_{camera}", batch[f"image_{camera}"])
        describe_tensor("state", batch["state"])
        describe_tensor("action_chunk", batch["action_chunk"])
        break


if __name__ == "__main__":
    main()
