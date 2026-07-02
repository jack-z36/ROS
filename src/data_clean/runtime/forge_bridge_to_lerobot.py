"""Explicit Forge Python fallback for bridge MCAP -> LeRobot v3 conversion.

Forge CLI ``--config`` consumes a generic conversion config, while the MCAP
reader needs its own topic config. This entry keeps those concerns separate and
passes the bridge-generated topic config directly to ``MCAPReader``.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
from typing import Iterable


def _ensure_forge_runtime_paths() -> None:
    """Expose Forge fallback dependencies without shadowing data-clean packages."""

    forge_source = Path(os.environ.get("DATA_CLEAN_FORGE_SOURCE", "/home/hit/forge"))
    if (forge_source / "forge").is_dir() and str(forge_source) not in sys.path:
        sys.path.insert(0, str(forge_source))

    forge_venv = Path(os.environ.get("DATA_CLEAN_FORGE_VENV", str(forge_source / ".venv")))
    candidates: list[Path] = []
    for pattern in (
        "lib/python*/site-packages",
        "local/lib/python*/dist-packages",
        "lib/python*/dist-packages",
        "lib/python3/dist-packages",
    ):
        candidates.extend(sorted(forge_venv.glob(pattern)))
    for path in candidates:
        value = str(path)
        if path.is_dir() and value not in sys.path:
            sys.path.append(value)


def convert_forge_bridge_to_lerobot(
    *,
    bridge_dir: str | Path,
    output_dir: str | Path,
    fps: float = 15.0,
) -> dict:
    """Convert a bridge directory into LeRobot v3 with explicit MCAP mapping."""

    result = convert_forge_bridges_to_lerobot(
        bridge_dirs=[bridge_dir],
        output_dir=output_dir,
        fps=fps,
    )
    first_bridge = result["bridges"][0]
    return {
        "status": result["status"],
        "input_forge_ready_mcap": first_bridge["input_forge_ready_mcap"],
        "input_topic_config": first_bridge["input_topic_config"],
        "output_lerobot_v3": result["output_lerobot_v3"],
        "episodes": result["episodes"],
        "frames": result["frames"],
        "cameras": result["cameras"],
        "state_dim": result["state_dim"],
        "action_dim": result["action_dim"],
        "fps": result["fps"],
    }


def convert_forge_bridges_to_lerobot(
    *,
    bridge_dirs: Iterable[str | Path],
    output_dir: str | Path,
    fps: float = 15.0,
) -> dict:
    """Convert multiple bridge directories into one LeRobot v3 dataset."""

    _ensure_forge_runtime_paths()

    from forge.core.models import DatasetInfo
    from forge.formats.lerobot_v3 import LeRobotV3Writer, LeRobotV3WriterConfig
    from forge.formats.mcap import MCAPReader, load_config

    bridge_paths = [Path(path).expanduser().resolve() for path in bridge_dirs]
    if not bridge_paths:
        raise ValueError("bridge_dirs must not be empty")

    output_path = Path(output_dir).expanduser().resolve()
    if output_path.exists() and any(output_path.iterdir()):
        raise FileExistsError(f"output directory is not empty: {output_path}")

    all_episodes = []
    cameras = {}
    total_frames = 0
    bridge_summaries = []
    first_mcap_path: Path | None = None

    for bridge_path in bridge_paths:
        mcap_path = bridge_path / "forge_ready.mcap"
        topic_config_path = bridge_path / "forge_topic_config.yaml"
        if not mcap_path.is_file():
            raise FileNotFoundError(f"forge_ready.mcap not found: {mcap_path}")
        if not topic_config_path.is_file():
            raise FileNotFoundError(
                f"forge_topic_config.yaml not found: {topic_config_path}"
            )
        first_mcap_path = first_mcap_path or mcap_path
        topic_config = load_config(topic_config_path)
        episodes = list(MCAPReader().read_episodes(mcap_path, config=topic_config))
        if not episodes:
            raise ValueError(f"Forge MCAP reader produced no episodes: {bridge_path}")

        bridge_frames = 0
        for episode in episodes:
            frame_count = len(episode.load_frames())
            bridge_frames += frame_count
            total_frames += frame_count
            cameras.update(episode.cameras)
        all_episodes.extend(episodes)
        bridge_summaries.append(
            {
                "bridge_dir": str(bridge_path),
                "input_forge_ready_mcap": str(mcap_path),
                "input_topic_config": str(topic_config_path),
                "episodes": len(episodes),
                "frames": bridge_frames,
            }
        )

    if not all_episodes:
        raise ValueError("Forge MCAP reader produced no episodes")

    dataset_info = DatasetInfo(
        path=first_mcap_path,
        format="mcap",
        num_episodes=len(all_episodes),
        total_frames=total_frames,
        inferred_fps=fps,
        cameras=cameras,
    )
    writer = LeRobotV3Writer(LeRobotV3WriterConfig(fps=fps))
    writer.write_dataset(iter(all_episodes), output_path, dataset_info=dataset_info)

    # 相对时间戳后处理：Forge writer 写入的是 MCAP 绝对 Unix 时间戳（log_time/1e9），
    # LeRobot v3 训练要求每个 episode 第一帧 timestamp = 0.0。这里按 episode 减去
    # 本 episode 第一帧时间戳，原地重写 data/chunk-*/file-*.parquet（不改 forge 源码）。
    from service.lerobot_timestamp_rebase import rebase_lerobot_timestamps

    rebase_lerobot_timestamps(output_path)

    # 图像 stats 补全：Forge writer 的 _STAT_FEATURES 只统计 state/action，跳过了
    # video feature。LeRobot 训练要求 info.json 里每个 feature 都有 stats，否则
    # 报 KeyError。这里在 writer 完成后解码视频，补全 observation.images.* 的每通道
    # 统计（÷255 归一化），不改 forge 源码。
    from service.lerobot_image_stats import augment_image_stats

    augment_image_stats(output_path)

    return {
        "status": "success",
        "output_lerobot_v3": str(output_path),
        "bridge_count": len(bridge_summaries),
        "episodes": len(all_episodes),
        "frames": total_frames,
        "cameras": sorted(cameras),
        "state_dim": all_episodes[0].state_dim,
        "action_dim": all_episodes[0].action_dim,
        "fps": fps,
        "bridges": bridge_summaries,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bridge-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--fps", type=float, default=15.0)
    args = parser.parse_args()
    result = convert_forge_bridge_to_lerobot(
        bridge_dir=args.bridge_dir,
        output_dir=args.output_dir,
        fps=args.fps,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
