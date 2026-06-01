"""Explicit Forge Python fallback for bridge MCAP -> LeRobot v3 conversion.

Forge CLI ``--config`` consumes a generic conversion config, while the MCAP
reader needs its own topic config. This entry keeps those concerns separate and
passes the bridge-generated topic config directly to ``MCAPReader``.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def convert_forge_bridge_to_lerobot(
    *,
    bridge_dir: str | Path,
    output_dir: str | Path,
    fps: float = 15.0,
) -> dict:
    """Convert a bridge directory into LeRobot v3 with explicit MCAP mapping."""

    from forge.core.models import DatasetInfo
    from forge.formats.lerobot_v3 import LeRobotV3Writer, LeRobotV3WriterConfig
    from forge.formats.mcap import MCAPReader, load_config

    bridge_path = Path(bridge_dir).expanduser().resolve()
    output_path = Path(output_dir).expanduser().resolve()
    mcap_path = bridge_path / "forge_ready.mcap"
    topic_config_path = bridge_path / "forge_topic_config.yaml"
    if not mcap_path.is_file():
        raise FileNotFoundError(f"forge_ready.mcap not found: {mcap_path}")
    if not topic_config_path.is_file():
        raise FileNotFoundError(
            f"forge_topic_config.yaml not found: {topic_config_path}"
        )
    if output_path.exists() and any(output_path.iterdir()):
        raise FileExistsError(f"output directory is not empty: {output_path}")

    topic_config = load_config(topic_config_path)
    episodes = list(MCAPReader().read_episodes(mcap_path, config=topic_config))
    if not episodes:
        raise ValueError("Forge MCAP reader produced no episodes")

    total_frames = sum(len(episode.load_frames()) for episode in episodes)
    cameras = {}
    for episode in episodes:
        cameras.update(episode.cameras)
    dataset_info = DatasetInfo(
        path=mcap_path,
        format="mcap",
        num_episodes=len(episodes),
        total_frames=total_frames,
        inferred_fps=fps,
        cameras=cameras,
    )
    writer = LeRobotV3Writer(LeRobotV3WriterConfig(fps=fps))
    writer.write_dataset(iter(episodes), output_path, dataset_info=dataset_info)
    return {
        "status": "success",
        "input_forge_ready_mcap": str(mcap_path),
        "input_topic_config": str(topic_config_path),
        "output_lerobot_v3": str(output_path),
        "episodes": len(episodes),
        "frames": total_frames,
        "cameras": sorted(cameras),
        "state_dim": episodes[0].state_dim,
        "action_dim": episodes[0].action_dim,
        "fps": fps,
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

