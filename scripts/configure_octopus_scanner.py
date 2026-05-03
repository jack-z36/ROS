#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


DEFAULT_TOPICS = [
    "/baton_mini_right/fast_odom",
    "/baton_mini_left/fast_odom",
    "/gopro_right/image_raw",
    "/gopro_left/image_raw",
    "/pressure/left_hand/gripper_1",
    "/pressure/left_hand/gripper_2",
    "/pressure/right_hand/gripper_1",
    "/pressure/right_hand/gripper_2",
]


def load_json(path):
    if not path.exists() or path.stat().st_size == 0:
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        default=str(Path.home() / ".config" / "scanner.json"),
        help="Octopus scanner.json path.",
    )
    parser.add_argument(
        "--recording-path",
        default="/home/hit/ROS/mcap",
        help="Directory where Octopus should write .mcap files.",
    )
    parser.add_argument(
        "--topic",
        action="append",
        dest="topics",
        help="Recording topic. Can be provided multiple times.",
    )
    args = parser.parse_args()

    config_path = Path(args.config).expanduser()
    recording_path = Path(args.recording_path).expanduser()
    topics = args.topics or DEFAULT_TOPICS

    config_path.parent.mkdir(parents=True, exist_ok=True)
    recording_path.mkdir(parents=True, exist_ok=True)

    config = load_json(config_path)
    config.setdefault("language", "zh_CN")
    config.setdefault("theme", "dark")
    config.setdefault("recording", {})
    config["recording"].setdefault("mcap", {})
    config["recording"]["mcap"]["path"] = str(recording_path)
    config["recording"]["mcap"]["compression"] = 2
    config["recording"]["mcap"]["topics"] = topics

    config_path.write_text(
        json.dumps(config, ensure_ascii=False, indent=4) + "\n",
        encoding="utf-8",
    )

    print(f"Octopus config: {config_path}")
    print(f"MCAP path: {recording_path}")
    print("Topics:")
    for topic in topics:
        print(f"  {topic}")


if __name__ == "__main__":
    main()
