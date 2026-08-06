from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml
from mcap.reader import make_reader
from mcap.writer import CompressionType, Writer
from mcap_ros2.writer import serialize_dynamic

from repo.config.mcap_process_config import load_app_config
from repo.mcap_a_writer import MCAP_A_Writer
from repo.ros2_codec import Ros2DynamicCodec
from repo.scene2_mcap_reader import load_scene2_signal_samples
from runtime.scene2_mcap_a_writer import run_scene2_mcap_a_writer
from runtime.scene3_mcap_a_input_check import run_scene3_mcap_a_input_check
from schemas.alignment_config import Scene3AlignmentConfig
from schemas.mcap_a_writer import MCAP_A_MessageReplacement, MCAP_A_WritePlan, MCAP_A_WriterConfig
from schemas.pose_filter import PoseFilterConfig
from schemas.reliability import (
    AnomalySource,
    IssueSeverity,
    IssueType,
    MissingIntervalIssue,
    SampleReliabilityIssue,
    SignalSampleRef,
)
from schemas.repair import RepairDecisionStatus, RepairDisposition, RepairMethod, SignalRepairRun
from schemas.ros2_schemas import GEOMETRY_MSGS_POSE_STAMPED, SENSOR_MSGS_IMAGE, STD_MSGS_FLOAT32
from schemas.scene2_samples import GripperSample, PoseSample, TactilePressureFrame
from schemas.scene2_streams import Scene2StreamSpec
from schemas.tactile_filter import TactileFilterConfig
from service.detectors import (
    ReliabilityDetectionConfig,
    detect_gripper_reliability,
    detect_pose_reliability,
    detect_tactile_reliability,
)
from service.pose_filter import filter_pose_segments
from service.pose_segment import split_reliable_segments
from service.repair_compute import run_all_repairs
from service.repair_run import (
    aggregate_sample_issues,
    build_repair_runs,
    decide_issue_dispositions,
    find_legal_neighbors,
)
from service.tactile_filter import filter_tactile_segments
from service.tactile_segment import split_tactile_segments


CONFIG = Path("config/data_clean/data_clean_calibrated.yaml")


def test_detectors_never_compare_different_topics_or_time_domains() -> None:
    config = ReliabilityDetectionConfig(
        max_gap_duration_ns=20,
        pose_position_jump_threshold=5,
        gripper_jump_threshold=0.2,
        gripper_stuck_min_samples=99,
        tactile_spike_mean_delta_threshold=5,
        tactile_zero_ratio_threshold=2,
        tactile_saturation_ratio_threshold=2,
    )
    poses = [
        _pose("/left", 0, 0, 0),
        _pose("/right", 1, 0, 100),
        _pose("/left", 10, 1, 1),
        _pose("/right", 11, 1, 101),
    ]
    grippers = [
        GripperSample("/left_gripper", 0, 0, 0.0),
        GripperSample("/right_gripper", 1, 0, 0.9),
        GripperSample("/left_gripper", 10, 1, 0.1),
        GripperSample("/right_gripper", 11, 1, 1.0),
    ]
    tactile = [
        _tactile("/pressure/left", 0, 0, 1),
        _tactile("/pressure/right", 1, 0, 100),
        _tactile("/pressure/left", 10, 1, 2),
        _tactile("/pressure/right", 11, 1, 101),
    ]

    for result in (
        detect_pose_reliability(poses, config=config),
        detect_gripper_reliability(grippers, config=config),
        detect_tactile_reliability(tactile, config=config),
    ):
        assert result.sample_issues == []
        assert result.missing_interval_issues == []


def test_non_auto_repair_run_never_enters_numeric_dispatch(monkeypatch: pytest.MonkeyPatch) -> None:
    ref = SignalSampleRef("/left", 1, 0, "pose")
    run = SignalRepairRun(
        repair_run_id="manual",
        source_topic="/left",
        modality="pose",
        replacement_unit="pose.position",
        input_window_refs=[ref],
        sample_issue_ids=["issue"],
        status=RepairDecisionStatus.SKIPPED,
        applied_method=None,
        reason="manual",
        disposition=RepairDisposition.MANUAL_REVIEW,
        planned_method=RepairMethod.LINEAR_INTERPOLATE,
    )

    monkeypatch.setattr("service.repair_compute._dispatch_repair", lambda *_: pytest.fail("numeric repair called"))
    result = run_all_repairs([run], {"manual": {"previous": None, "next": None}})[0]
    assert result.repair_runs[0].status is RepairDecisionStatus.SKIPPED
    assert result.repair_runs[0].disposition is RepairDisposition.MANUAL_REVIEW


def test_pose_fields_form_independent_auto_repair_runs() -> None:
    ref = SignalSampleRef("/pose", 10, 1, "pose")
    issues = [
        SampleReliabilityIssue(
            issue_id=f"issue-{field}",
            sample_ref=ref,
            issue_type=issue_type,
            severity=IssueSeverity.ERROR,
            source=AnomalySource.POSE,
            field_path=field,
            message="bad",
        )
        for field, issue_type in (
            ("pose.position", IssueType.POSE_JUMP),
            ("pose.orientation", IssueType.INVALID_ORIENTATION),
        )
    ]
    groups = aggregate_sample_issues(issues)
    dispositions = decide_issue_dispositions(groups)
    runs = build_repair_runs(groups, dispositions=dispositions)
    assert {run.replacement_unit for run in runs} == {"pose.position", "pose.orientation"}
    assert all(run.disposition is RepairDisposition.AUTO_REPAIR for run in runs)
    assert {run.planned_method for run in runs} == {
        RepairMethod.LINEAR_INTERPOLATE,
        RepairMethod.SLERP_INTERPOLATE,
    }


@pytest.mark.parametrize(
    ("unit", "previous", "following", "contract", "expected"),
    [
        ("pose.position", [0.0, 0.0, 0.0], [2.0, 2.0, 2.0], {}, [1.0, 1.0, 1.0]),
        ("pose.orientation", [0.0, 0.0, 0.0, 1.0], [0.0, 0.0, 1.0, 0.0], {}, None),
        ("gripper.value", 0.0, 2.0, {}, 1.0),
        ("tactile.frame", [[0.0, 2.0]], [[2.0, 4.0]], {"rows": 1, "cols": 2}, [[1.0, 3.0]]),
    ],
)
def test_all_replacement_units_require_two_legal_neighbors(unit, previous, following, contract, expected) -> None:
    modality = unit.split(".")[0]
    target = SignalSampleRef(f"/{modality}", 10, 1, modality)
    run = SignalRepairRun(
        repair_run_id=unit,
        source_topic=target.topic,
        modality=modality,
        replacement_unit=unit,
        input_window_refs=[target],
        sample_issue_ids=["issue"],
        status=RepairDecisionStatus.PENDING,
        applied_method=None,
        reason="approved",
        disposition=RepairDisposition.AUTO_REPAIR,
        planned_method=(
            RepairMethod.SLERP_INTERPOLATE if unit == "pose.orientation" else RepairMethod.LINEAR_INTERPOLATE
        ),
        replacement_contract=contract,
    )
    neighbors = {
        unit: {
            "previous": {"sample_ref": SignalSampleRef(target.topic, 0, 0, modality), "value": previous},
            "next": {"sample_ref": SignalSampleRef(target.topic, 20, 2, modality), "value": following},
        }
    }
    repaired = run_all_repairs([run], neighbors)[0].repair_runs[0]
    assert repaired.status is RepairDecisionStatus.REPAIRED
    value = repaired.sample_records[0].value_summary["value"]
    if expected is not None:
        assert value == pytest.approx(expected) if unit != "tactile.frame" else value == expected
    else:
        assert sum(component * component for component in value) == pytest.approx(1.0)

    failed = run_all_repairs([run], {unit: {"previous": None, "next": neighbors[unit]["next"]}})[0].repair_runs[0]
    assert failed.status is RepairDecisionStatus.UNREPAIRABLE


def test_repair_rejects_invalid_field_contracts_and_missing_interval_neighbors() -> None:
    orientation_ref = SignalSampleRef("/pose", 10, 1, "pose")
    orientation_run = _repair_run(
        orientation_ref,
        "pose.orientation",
        RepairMethod.SLERP_INTERPOLATE,
    )
    invalid_orientation = run_all_repairs(
        [orientation_run],
        {
            orientation_run.repair_run_id: {
                "previous": {"sample_ref": SignalSampleRef("/pose", 0, 0, "pose"), "value": [0, 0, 1]},
                "next": {"sample_ref": SignalSampleRef("/pose", 20, 2, "pose"), "value": [0, 0, 1]},
            }
        },
    )[0].repair_runs[0]
    assert invalid_orientation.status is RepairDecisionStatus.UNREPAIRABLE
    assert invalid_orientation.reason == "invalid_quaternion_neighbor"

    tactile_ref = SignalSampleRef("/pressure", 10, 1, "tactile")
    tactile_run = _repair_run(
        tactile_ref,
        "tactile.frame",
        RepairMethod.LINEAR_INTERPOLATE,
        contract={"rows": 1, "cols": 2},
    )
    invalid_tactile = run_all_repairs(
        [tactile_run],
        {
            tactile_run.repair_run_id: {
                "previous": {"sample_ref": SignalSampleRef("/pressure", 0, 0, "tactile"), "value": [[1, 2, 3]]},
                "next": {"sample_ref": SignalSampleRef("/pressure", 20, 2, "tactile"), "value": [[4, 5, 6]]},
            }
        },
    )[0].repair_runs[0]
    assert invalid_tactile.status is RepairDecisionStatus.UNREPAIRABLE
    assert invalid_tactile.reason == "tactile_shape_mismatch"

    issue = SampleReliabilityIssue(
        issue_id="gap-target",
        sample_ref=orientation_ref,
        issue_type=IssueType.INVALID_ORIENTATION,
        severity=IssueSeverity.ERROR,
        source=AnomalySource.POSE,
        field_path="pose.orientation",
        message="bad",
    )
    groups = aggregate_sample_issues([issue])
    gap = MissingIntervalIssue(
        issue_id="gap",
        topic="/pose",
        modality="pose",
        start_time=0,
        end_time=10,
        expected_count=1,
        actual_count=0,
        severity=IssueSeverity.WARNING,
        suggested_action="mark_unhandled_gap",
    )
    neighbors = find_legal_neighbors(
        [orientation_ref],
        [SignalSampleRef("/pose", 0, 0, "pose"), orientation_ref, SignalSampleRef("/pose", 20, 2, "pose")],
        groups,
        [gap],
        replacement_unit="pose.orientation",
    )
    assert neighbors.previous_ref is None
    assert neighbors.reason == "missing_previous_neighbor"


def test_pose_segment_uses_caller_config_and_exact_membership() -> None:
    samples = [
        {
            "sample_ref": SignalSampleRef("/pose", index * 100_000_000, index, "pose", "publish_time"),
            "position": {"x": float(index * index), "y": 0.0, "z": 0.0},
            "orientation": {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0},
        }
        for index in range(7)
    ]
    config = PoseFilterConfig(
        window_duration_ms=500,
        polyorder=3,
        position_guard_max_delta_m=100,
        orientation_guard_max_delta_deg=10,
    )
    segments = split_reliable_segments(samples, [], [], config)
    result = filter_pose_segments(samples, segments, config)

    assert len(segments) == 1
    assert segments[0].actual_window_size_samples == 5
    assert segments[0].polyorder == 3
    assert segments[0].configured_window_duration_ms == 500
    assert segments[0].sample_refs == [sample["sample_ref"] for sample in samples]
    assert result.pose_filter_config_ref is config
    assert {record.segment_id for record in result.sample_records} == {segments[0].segment_id}


def test_tactile_segments_reset_filter_state_per_topic_and_contact_boundary() -> None:
    config = TactileFilterConfig(median_window=3, ema_alpha=0.5, contact_reset_threshold=20)
    frames = [
        _tactile_dict("/pressure/left", index, index, value)
        for index, value in enumerate((0, 0, 0, 100, 100, 100))
    ] + [
        _tactile_dict("/pressure/right", index, index, 7)
        for index in range(3)
    ]
    segments = split_tactile_segments(frames, [], config)
    records = filter_tactile_segments(frames, segments, config)

    left_segments = [segment for segment in segments if segment.source_topic == "/pressure/left"]
    assert len(left_segments) == 2
    first_records = [next(record for record in records if record.segment_id == segment.segment_id) for segment in segments]
    assert all(record.filter_state_reset for record in first_records)
    second_left_first = next(record for record in records if record.segment_id == left_segments[1].segment_id)
    assert second_left_first.filtered_matrix == [[100.0, 100.0, 100.0]]


def test_invalid_tactile_shape_is_preserved_as_an_isolated_boundary() -> None:
    config = TactileFilterConfig(median_window=3, ema_alpha=0.5)
    frames = [
        _tactile_dict("/pressure/left", 0, 0, 1),
        {
            "sample_ref": SignalSampleRef("/pressure/left", 1, 1, "tactile", "header_stamp"),
            "topic": "/pressure/left",
            "timestamp_ns": 1,
            "message_index": 1,
            "rows": 0,
            "cols": 0,
            "data": [99],
            "status": "unrepairable",
        },
        _tactile_dict("/pressure/left", 2, 2, 2),
    ]
    segments = split_tactile_segments(frames, [], config)
    records = filter_tactile_segments(frames, segments, config)
    invalid = next(record for record in records if record.sample_ref.message_index == 1)
    assert invalid.filtered_matrix is None
    assert invalid.status.value in {"invalid_shape", "skipped_boundary"}
    assert all(
        [ref.message_index for ref in segment.sample_refs] != [0, 1, 2]
        for segment in segments
    )


def test_physical_message_identity_targets_only_one_duplicate_time_message(tmp_path: Path) -> None:
    source = tmp_path / "source.mcap"
    _write_required_scene2_mcap(source)
    config = load_app_config(CONFIG)
    samples = load_scene2_signal_samples(source, config)
    left = [sample for sample in samples.gripper if sample.topic == "/gopro_left/gripper_width"]
    assert [sample.message_index for sample in left] == [0, 1, 2, 3]
    assert [sample.log_time_ns for sample in left] == [300, 100, 200, 400]

    target = left[1]
    replacement = MCAP_A_MessageReplacement(_ref(target, "gripper"), "gripper.value", 0.75)
    output = tmp_path / "output.mcap"
    plan = MCAP_A_WritePlan(
        source_mcap=str(source),
        output_mcap=str(output),
        operations=[{"operation": "replace", "topic": target.topic, "sequence_ref": "stable"}],
        output_sequence_refs={
            "signal_repair_result_ref": "repair",
            "pose_filter_result_ref": "pose",
            "tactile_filter_result_ref": "tactile",
        },
        run_id="writer-test",
    )
    writer = MCAP_A_Writer(MCAP_A_WriterConfig(output_path=str(output), compression="none"), plan)
    result = writer.execute_write_plan(plan, replacements=[replacement])
    assert result.success, result.error_log

    source_payloads = _topic_payloads(source, target.topic)
    output_payloads = _topic_payloads(output, target.topic)
    assert len(source_payloads) == len(output_payloads) == 4
    assert [payload for index, payload in enumerate(output_payloads) if index != 1] == [
        payload for index, payload in enumerate(source_payloads) if index != 1
    ]
    assert _float_values(output, target.topic) == pytest.approx([0.0, 0.75, 0.2, 0.3])


def test_scene2_inventory_is_fail_closed_and_rejects_duplicate_config(tmp_path: Path) -> None:
    missing_source = tmp_path / "missing_required.mcap"
    _write_required_scene2_mcap(missing_source, omitted_topics={"/gopro_right/gripper_width"})
    config = load_app_config(CONFIG)
    with pytest.raises(ValueError, match="missing_required_scene2_topics"):
        load_scene2_signal_samples(missing_source, config)

    source = tmp_path / "unsupported_schema.mcap"
    _write_required_scene2_mcap(source)
    wrong_modality = replace(
        config,
        scene2_streams=tuple(
            Scene2StreamSpec(stream.topic, "pose", stream.required)
            if stream.topic == "/gopro_left/gripper_width"
            else stream
            for stream in config.scene2_streams
        ),
    )
    with pytest.raises(ValueError, match="unsupported_scene2_schema"):
        load_scene2_signal_samples(source, wrong_modality)

    raw = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    raw["web_pipeline"]["scene2"]["streams"].append(
        dict(raw["web_pipeline"]["scene2"]["streams"][0])
    )
    duplicate_config = tmp_path / "duplicate.yaml"
    duplicate_config.write_text(yaml.safe_dump(raw, allow_unicode=True, sort_keys=False), encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate scene2 stream topics"):
        load_app_config(duplicate_config)


def test_unlisted_topics_are_not_analyzed_and_are_copied_byte_for_byte(tmp_path: Path) -> None:
    source = tmp_path / "unlisted_topics.mcap"
    _write_required_scene2_mcap(source, include_unlisted=True)
    samples = load_scene2_signal_samples(source, load_app_config(CONFIG))
    analyzed_topics = {
        *(sample.topic for sample in samples.pose),
        *(sample.topic for sample in samples.gripper),
        *(sample.topic for sample in samples.tactile),
    }
    assert "/left_arm_base_tcp_pose" not in analyzed_topics
    assert "/pressure/unlisted" not in analyzed_topics

    result = run_scene2_mcap_a_writer(
        cleaned_mcap_path=source,
        config_path=CONFIG,
        run_root=tmp_path / "runs",
    )
    assert result["status"] == "success", result["errors"]
    output = Path(result["outputs"]["mcap_a"])
    for topic in ("/left_arm_base_tcp_pose", "/pressure/unlisted"):
        assert _topic_payloads(output, topic) == _topic_payloads(source, topic)


def test_main_writer_loads_and_analyzes_once_with_shared_run_id(tmp_path: Path) -> None:
    source = tmp_path / "source.mcap"
    _write_required_scene2_mcap(source)
    calls = 0

    def spy(path: Path, config):
        nonlocal calls
        calls += 1
        return load_scene2_signal_samples(path, config)

    result = run_scene2_mcap_a_writer(
        cleaned_mcap_path=source,
        config_path=CONFIG,
        run_root=tmp_path / "runs",
        sample_loader=spy,
    )
    assert result["status"] == "success", result["errors"]
    assert calls == 1
    run_ids = {
        json.loads(Path(result["outputs"][key]).read_text(encoding="utf-8"))["run_id"]
        for key in (
            "signal_reliability_detection_result_json",
            "signal_repair_result_json",
            "pose_filter_result_json",
            "tactile_filter_result_json",
        )
    }
    summary = json.loads(Path(result["outputs"]["mcap_a_write_summary_json"]).read_text(encoding="utf-8"))
    run_ids.add(summary["run_id"])
    assert run_ids == {result["run_id"]}
    detection = json.loads(
        Path(result["outputs"]["signal_reliability_detection_result_json"]).read_text(encoding="utf-8")
    )
    assert summary["config_snapshot"] == detection["run_context"]["config_snapshot"]
    assert result["stream_inventory"]["missing_optional_topics"]


def test_successful_gripper_repair_is_written_back(tmp_path: Path) -> None:
    source = tmp_path / "gripper_anomaly.mcap"
    _write_required_scene2_mcap(source, gripper_values=(0.0, 2.0, 0.2, 0.3))
    result = run_scene2_mcap_a_writer(
        cleaned_mcap_path=source,
        config_path=CONFIG,
        run_root=tmp_path / "runs",
    )
    assert result["status"] == "success", result["errors"]
    output = Path(result["outputs"]["mcap_a"])
    assert _float_values(output, "/gopro_left/gripper_width") == pytest.approx([0.0, 0.2, 0.2, 0.3])
    summary = json.loads(Path(result["outputs"]["mcap_a_write_summary_json"]).read_text(encoding="utf-8"))
    assert summary["replaced_modality_stats"]["gripper"] == 2

    scene3 = run_scene3_mcap_a_input_check(
        mcap_a_path=output,
        summary_path=result["outputs"]["mcap_a_write_summary_json"],
        config=Scene3AlignmentConfig(),
        run_root=tmp_path / "scene3_runs",
    )
    assert scene3["status"] == "success", scene3["errors"]


def _pose(topic: str, timestamp: int, index: int, x: float) -> PoseSample:
    return PoseSample(topic, timestamp, index, (x, 0.0, 0.0), (0.0, 0.0, 0.0, 1.0))


def _repair_run(
    ref: SignalSampleRef,
    unit: str,
    method: RepairMethod,
    *,
    contract: dict | None = None,
) -> SignalRepairRun:
    return SignalRepairRun(
        repair_run_id=f"test-{unit}",
        source_topic=ref.topic,
        modality=ref.modality,
        replacement_unit=unit,
        input_window_refs=[ref],
        sample_issue_ids=["issue"],
        status=RepairDecisionStatus.PENDING,
        applied_method=None,
        reason="approved",
        disposition=RepairDisposition.AUTO_REPAIR,
        planned_method=method,
        replacement_contract=contract or {},
    )


def _tactile(topic: str, timestamp: int, index: int, value: int) -> TactilePressureFrame:
    return TactilePressureFrame(topic, timestamp, index, "hand", "gripper", 1, 3, [value] * 3)


def _tactile_dict(topic: str, timestamp: int, index: int, value: int) -> dict:
    return {
        "sample_ref": SignalSampleRef(topic, timestamp, index, "tactile", "header_stamp"),
        "topic": topic,
        "timestamp_ns": timestamp,
        "message_index": index,
        "rows": 1,
        "cols": 3,
        "data": [value] * 3,
        "status": "kept_original",
    }


def _ref(sample, modality: str) -> SignalSampleRef:
    return SignalSampleRef(
        sample.topic,
        sample.timestamp_ns,
        sample.message_index,
        modality,
        sample.time_domain,
        sample.log_time_ns,
        sample.publish_time_ns,
        sample.sequence,
        sample.source_channel_id,
    )


def _stamp(timestamp_ns: int) -> SimpleNamespace:
    return SimpleNamespace(sec=timestamp_ns // 1_000_000_000, nanosec=timestamp_ns % 1_000_000_000)


def _pose_message(timestamp_ns: int, x: float) -> SimpleNamespace:
    return SimpleNamespace(
        header=SimpleNamespace(stamp=_stamp(timestamp_ns), frame_id="source"),
        pose=SimpleNamespace(
            position=SimpleNamespace(x=x, y=0.0, z=0.0),
            orientation=SimpleNamespace(x=0.0, y=0.0, z=0.0, w=1.0),
        ),
    )


def _write_required_scene2_mcap(
    path: Path,
    *,
    gripper_values: tuple[float, float, float, float] = (0.0, 0.1, 0.2, 0.3),
    omitted_topics: set[str] | None = None,
    include_unlisted: bool = False,
) -> None:
    omitted_topics = omitted_topics or set()
    pose_encoder = serialize_dynamic("geometry_msgs/msg/PoseStamped", GEOMETRY_MSGS_POSE_STAMPED)[
        "geometry_msgs/msg/PoseStamped"
    ]
    gripper_encoder = serialize_dynamic("std_msgs/msg/Float32", STD_MSGS_FLOAT32)["std_msgs/msg/Float32"]
    image_encoder = serialize_dynamic("sensor_msgs/msg/Image", SENSOR_MSGS_IMAGE)["sensor_msgs/msg/Image"]
    with path.open("wb") as fh:
        writer = Writer(fh, chunk_size=128, compression=CompressionType.NONE)
        writer.start()
        pose_schema = writer.register_schema(
            "geometry_msgs/msg/PoseStamped", "ros2msg", GEOMETRY_MSGS_POSE_STAMPED.encode()
        )
        gripper_schema = writer.register_schema("std_msgs/msg/Float32", "ros2msg", STD_MSGS_FLOAT32.encode())
        image_schema = writer.register_schema("sensor_msgs/msg/Image", "ros2msg", SENSOR_MSGS_IMAGE.encode())
        channels = {
            topic: writer.register_channel(topic, "cdr", pose_schema)
            for topic in ("/baton_mini_left/tcp_pose", "/baton_mini_right/tcp_pose")
            if topic not in omitted_topics
        }
        channels.update(
            {
                topic: writer.register_channel(topic, "cdr", gripper_schema)
                for topic in ("/gopro_left/gripper_width", "/gopro_right/gripper_width")
                if topic not in omitted_topics
            }
        )
        channels.update(
            {
                topic: writer.register_channel(topic, "cdr", image_schema)
                for topic in ("/gopro_left/image_raw", "/gopro_right/image_raw")
            }
        )
        if include_unlisted:
            channels["/left_arm_base_tcp_pose"] = writer.register_channel(
                "/left_arm_base_tcp_pose", "cdr", pose_schema
            )
            channels["/pressure/unlisted"] = writer.register_channel(
                "/pressure/unlisted", "cdr", gripper_schema
            )
        for index, log_time in enumerate((300, 100, 200, 400)):
            publish_time = 100_000_000 if index in (1, 2) else (50_000_000 if index == 0 else 300_000_000)
            sequence = 7 if index in (1, 2) else index
            for topic in ("/gopro_left/image_raw", "/gopro_right/image_raw"):
                writer.add_message(
                    channel_id=channels[topic],
                    log_time=log_time,
                    publish_time=publish_time,
                    sequence=sequence,
                    data=image_encoder(
                        SimpleNamespace(
                            header=SimpleNamespace(stamp=_stamp(publish_time), frame_id="camera"),
                            height=1,
                            width=1,
                            encoding="mono8",
                            is_bigendian=0,
                            step=1,
                            data=bytes([index]),
                        )
                    ),
                )
            for topic in ("/baton_mini_left/tcp_pose", "/baton_mini_right/tcp_pose"):
                if topic in omitted_topics:
                    continue
                writer.add_message(
                    channel_id=channels[topic],
                    log_time=log_time,
                    publish_time=publish_time,
                    sequence=sequence,
                    data=pose_encoder(_pose_message(publish_time, float(index * index))),
                )
            for topic in ("/gopro_left/gripper_width", "/gopro_right/gripper_width"):
                if topic in omitted_topics:
                    continue
                writer.add_message(
                    channel_id=channels[topic],
                    log_time=log_time,
                    publish_time=publish_time,
                    sequence=sequence,
                    data=gripper_encoder(SimpleNamespace(data=gripper_values[index])),
                )
            if include_unlisted:
                writer.add_message(
                    channel_id=channels["/left_arm_base_tcp_pose"],
                    log_time=log_time,
                    publish_time=publish_time,
                    sequence=sequence,
                    data=pose_encoder(_pose_message(publish_time, 1_000.0 + index)),
                )
                writer.add_message(
                    channel_id=channels["/pressure/unlisted"],
                    log_time=log_time,
                    publish_time=publish_time,
                    sequence=sequence,
                    data=gripper_encoder(SimpleNamespace(data=9.0 + index)),
                )
        writer.finish()


def _topic_payloads(path: Path, topic: str) -> list[bytes]:
    with path.open("rb") as fh:
        return [message.data for _, channel, message in make_reader(fh).iter_messages(log_time_order=False) if channel.topic == topic]


def _float_values(path: Path, topic: str) -> list[float]:
    codec = Ros2DynamicCodec()
    values = []
    with path.open("rb") as fh:
        for schema, channel, message in make_reader(fh).iter_messages(log_time_order=False):
            if channel.topic == topic:
                values.append(float(codec.decode(schema, message).data))
    return values
