from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
from types import SimpleNamespace

import numpy as np
from mcap.writer import CompressionType, Writer
from mcap_ros2.writer import serialize_dynamic

from repo.bridge_mcap_reader import iter_bridge_frames
from runtime.official_lerobot_export import run_official_exporter
from schemas.lerobot_export import LeRobotExportRequest
from schemas.ros2_schemas import SENSOR_MSGS_IMAGE, SENSOR_MSGS_JOINT_STATE
from service.forge_bridge import FORGE_TOPICS


def _header() -> SimpleNamespace:
    return SimpleNamespace(
        stamp=SimpleNamespace(sec=0, nanosec=0),
        frame_id="fixture",
    )


def _write_bridge(path: Path, *, frame_count: int, seed: int) -> None:
    path.mkdir(parents=True)
    joint_encoder = serialize_dynamic(
        "sensor_msgs/msg/JointState",
        SENSOR_MSGS_JOINT_STATE,
    )["sensor_msgs/msg/JointState"]
    image_encoder = serialize_dynamic(
        "sensor_msgs/msg/Image",
        SENSOR_MSGS_IMAGE,
    )["sensor_msgs/msg/Image"]
    with (path / "forge_ready.mcap").open("wb") as stream:
        writer = Writer(stream, compression=CompressionType.NONE)
        writer.start()
        joint_schema = writer.register_schema(
            "sensor_msgs/msg/JointState",
            "ros2msg",
            SENSOR_MSGS_JOINT_STATE.encode(),
        )
        image_schema = writer.register_schema(
            "sensor_msgs/msg/Image",
            "ros2msg",
            SENSOR_MSGS_IMAGE.encode(),
        )
        channels = {
            "state": writer.register_channel(FORGE_TOPICS["state"], "cdr", joint_schema),
            "action": writer.register_channel(FORGE_TOPICS["action"], "cdr", joint_schema),
            "left": writer.register_channel(FORGE_TOPICS["image_left"], "cdr", image_schema),
            "right": writer.register_channel(FORGE_TOPICS["image_right"], "cdr", image_schema),
        }
        for frame_index in range(frame_count):
            timestamp_ns = int(frame_index * 1_000_000_000 / 15)
            state = (np.arange(16, dtype=np.float32) + seed + frame_index / 10).tolist()
            action = (np.arange(16, dtype=np.float32) + seed + frame_index / 5).tolist()
            for field, values in (("state", state), ("action", action)):
                writer.add_message(
                    channel_id=channels[field],
                    log_time=timestamp_ns,
                    publish_time=timestamp_ns,
                    sequence=frame_index,
                    data=joint_encoder(
                        SimpleNamespace(
                            header=_header(),
                            name=[f"dim_{index}" for index in range(16)],
                            position=values,
                            velocity=[],
                            effort=[],
                        )
                    ),
                )
            for camera_index, field in enumerate(("left", "right")):
                image = np.zeros((480, 640, 3), dtype=np.uint8)
                image[..., 0] = (seed + frame_index * 3 + camera_index * 40) % 255
                image[..., 1] = np.arange(640, dtype=np.uint8)[None, :]
                image[..., 2] = np.arange(480, dtype=np.uint8)[:, None]
                writer.add_message(
                    channel_id=channels[field],
                    log_time=timestamp_ns,
                    publish_time=timestamp_ns,
                    sequence=frame_index,
                    data=image_encoder(
                        SimpleNamespace(
                            header=_header(),
                            height=480,
                            width=640,
                            encoding="rgb8",
                            is_bigendian=0,
                            step=640 * 3,
                            data=image.tobytes(),
                        )
                    ),
                )
        writer.finish()
    (path / "forge_bridge_report.json").write_text(
        json.dumps({"status": "completed", "output_step_count": frame_count}),
        encoding="utf-8",
    )


def test_streaming_bridge_reader_keeps_contract(tmp_path: Path) -> None:
    bridge = tmp_path / "bridge"
    _write_bridge(bridge, frame_count=3, seed=5)
    frames = list(
        iter_bridge_frames(
            bridge,
            state_dim=16,
            action_dim=16,
            image_height=480,
            image_width=640,
        )
    )
    assert len(frames) == 3
    assert frames[0].state.dtype == np.float32
    assert frames[0].action.shape == (16,)
    assert frames[0].image_left.shape == (480, 640, 3)
    assert frames[0].image_left.dtype == np.uint8


def test_official_exporter_writes_two_ordered_episodes(
    tmp_path: Path,
    monkeypatch,
) -> None:
    bridges = [tmp_path / "bridge_0", tmp_path / "bridge_1"]
    _write_bridge(bridges[0], frame_count=4, seed=10)
    _write_bridge(bridges[1], frame_count=5, seed=20)
    monkeypatch.setenv(
        "DATA_CLEAN_LEROBOT_PYTHON",
        "/home/hit/.conda-envs/lerobot-export/bin/python",
    )
    request = LeRobotExportRequest(
        job_id="fixture-job",
        dataset_name="fixture-dataset",
        bridge_dirs=tuple(str(path) for path in bridges),
        output_dir=str(tmp_path / "dataset"),
    )
    result = run_official_exporter(request, exchange_dir=tmp_path / "exchange")
    assert result["status"] == "success"
    assert result["episodes"] == 2
    assert result["frames"] == 9
    assert [item["bridge_dir"] for item in result["bridges"]] == [
        str(path) for path in bridges
    ]
    assert result["official_compatibility"]["status"] == "passed"
    assert result["official_compatibility"]["act_batch"]["action"] == [2, 100, 16]

    act_report_path = tmp_path / "act_acceptance.json"
    act_process = subprocess.run(
        [
            "/home/hit/.conda-envs/lerobot-export/bin/python",
            "-m",
            "service.lerobot_act_acceptance",
            "--root",
            str(tmp_path / "dataset"),
            "--repo-id",
            "local/fixture-dataset",
            "--output",
            str(act_report_path),
        ],
        cwd=Path(__file__).resolve().parents[2],
        env={
            **os.environ,
            "PYTHONPATH": os.pathsep.join(
                [
                    str(Path(__file__).resolve().parents[2] / "src/data_clean"),
                    str(
                        Path(__file__).resolve().parents[2]
                        / "src/model_deploy/third_party/lerobot/src"
                    ),
                    os.environ.get("PYTHONPATH", ""),
                ]
            ),
        },
        text=True,
        capture_output=True,
        check=False,
    )
    assert act_process.returncode == 0, act_process.stderr
    act_report = json.loads(act_report_path.read_text(encoding="utf-8"))
    assert act_report["status"] == "passed"
    assert act_report["batch"]["action"] == [1, 100, 16]
    assert act_report["gradient_tensors"] > 0

    stats_path = tmp_path / "dataset/meta/stats.json"
    broken_stats = json.loads(stats_path.read_text(encoding="utf-8"))
    broken_stats.pop("observation.images.right")
    stats_path.write_text(json.dumps(broken_stats), encoding="utf-8")
    negative_gate = subprocess.run(
        [
            "/home/hit/.conda-envs/lerobot-export/bin/python",
            "-c",
            (
                "import json,sys;"
                "from schemas.lerobot_export import LeRobotExportRequest;"
                "from service.lerobot_official_validator import "
                "validate_official_lerobot_dataset;"
                "request=LeRobotExportRequest.from_dict("
                "json.load(open(sys.argv[1], encoding='utf-8')));"
                "validate_official_lerobot_dataset(request)"
            ),
            str(tmp_path / "exchange/lerobot_export_request.json"),
        ],
        cwd=Path(__file__).resolve().parents[2],
        env={
            **os.environ,
            "PYTHONPATH": os.pathsep.join(
                [
                    str(Path(__file__).resolve().parents[2] / "src/data_clean"),
                    str(
                        Path(__file__).resolve().parents[2]
                        / "src/model_deploy/third_party/lerobot/src"
                    ),
                    os.environ.get("PYTHONPATH", ""),
                ]
            ),
        },
        text=True,
        capture_output=True,
        check=False,
    )
    assert negative_gate.returncode != 0
    assert "stats missing: observation.images.right" in negative_gate.stderr
