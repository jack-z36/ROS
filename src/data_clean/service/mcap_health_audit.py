"""Raw MCAP health audit and rejected-file movement for Web jobs."""

from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from mcap.reader import make_reader

from repo.config.mcap_process_config import AppConfig, GripperStreamConfig, PoseStreamConfig
from schemas.lerobot_features import enabled_state_segments
from schemas.mcap_health_audit import (
    HealthAuditResult,
    HealthAuditSummary,
    HealthStatus,
    MoveInputFileResult,
    MoveRejectedResult,
    RejectGroup,
    RejectReason,
)
from service.baton_pose_audit import (
    CLASS_INVALID_POSE,
    CLASS_MISSING_TOPIC,
    CLASS_NORMAL,
    CLASS_UNIT_MISMATCH,
    audit_mcap_file,
)
from service.validator import TopicInventory, build_topic_inventory


TACTILE_SOURCE_TOPICS = {
    "tactile_left_gripper_1": "/pressure/left_hand/gripper_1",
    "tactile_left_gripper_2": "/pressure/left_hand/gripper_2",
    "tactile_right_gripper_1": "/pressure/right_hand/gripper_1",
    "tactile_right_gripper_2": "/pressure/right_hand/gripper_2",
}
TACTILE_SCHEMA_NAME = "hwk_pressure_interfaces/msg/PressureFrame"


def audit_mcap_health_file(
    mcap_path: str | Path,
    *,
    config: AppConfig,
    lerobot_features: dict[str, Any] | None = None,
    include_pose_audit: bool = True,
) -> HealthAuditResult:
    """Audit whether a raw MCAP can enter the normal Web cleaning pipeline."""

    path = Path(mcap_path).expanduser().resolve()
    stat = path.stat() if path.exists() else None
    size = stat.st_size if stat is not None else 0
    try:
        with path.open("rb") as handle:
            summary = make_reader(handle).get_summary()
        inventory = build_topic_inventory(summary)
    except Exception as exc:  # noqa: BLE001 - file-local health report must capture all read failures.
        return _result(
            path,
            size=size,
            status=HealthStatus.REJECTED,
            group=RejectGroup.UNREADABLE,
            reason=RejectReason.MCAP_UNREADABLE,
            read_error=f"{type(exc).__name__}: {exc}",
        )

    topic_counts = {topic: item.message_count for topic, item in sorted(inventory.items())}

    camera_failure = _camera_failure(config.gripper_streams, inventory)
    if camera_failure is not None:
        group, reason, parts = camera_failure
        return _result(
            path,
            size=size,
            status=HealthStatus.REJECTED,
            group=group,
            reason=reason,
            dir_parts=parts,
            topic_counts=topic_counts,
        )

    pose_failure = _pose_contract_failure(config.pose_streams, inventory)
    pose_audit_payload: dict[str, Any] | None = None
    if pose_failure is None and include_pose_audit:
        left_pose, right_pose = _left_right_pose_streams(config.pose_streams)
        pose_audit = audit_mcap_file(path, left_topic=left_pose.input_topic, right_topic=right_pose.input_topic)
        pose_audit_payload = pose_audit.to_dict()
        pose_failure = _pose_audit_failure(pose_audit_payload)
    if pose_failure is not None:
        group, reason, parts = pose_failure
        return _result(
            path,
            size=size,
            status=HealthStatus.REJECTED,
            group=group,
            reason=reason,
            dir_parts=parts,
            topic_counts=topic_counts,
            pose_audit=pose_audit_payload,
        )

    tactile_failure = _tactile_failure(_required_tactile_topics(lerobot_features), inventory)
    if tactile_failure is not None:
        group, reason, parts = tactile_failure
        return _result(
            path,
            size=size,
            status=HealthStatus.REJECTED,
            group=group,
            reason=reason,
            dir_parts=parts,
            topic_counts=topic_counts,
            pose_audit=pose_audit_payload,
        )

    return _result(
        path,
        size=size,
        status=HealthStatus.ELIGIBLE,
        topic_counts=topic_counts,
        pose_audit=pose_audit_payload,
    )


def audit_mcap_health_files(
    mcap_paths: list[str | Path],
    *,
    config: AppConfig,
    lerobot_features: dict[str, Any] | None = None,
    include_pose_audit: bool = True,
) -> list[HealthAuditResult]:
    return [
        audit_mcap_health_file(
            path,
            config=config,
            lerobot_features=lerobot_features,
            include_pose_audit=include_pose_audit,
        )
        for path in mcap_paths
    ]


def summarize_health_results(results: list[HealthAuditResult] | list[dict[str, Any]]) -> HealthAuditSummary:
    total = len(results)
    eligible_count = 0
    rejected_count = 0
    raw_total_size = 0
    eligible_raw_size = 0
    rejected_raw_size = 0
    reject_counts: dict[str, int] = {}
    for item in results:
        data = item.to_dict() if isinstance(item, HealthAuditResult) else item
        size = int(data.get("size") or 0)
        raw_total_size += size
        if data.get("precheck_status") == HealthStatus.ELIGIBLE.value:
            eligible_count += 1
            eligible_raw_size += size
        else:
            rejected_count += 1
            rejected_raw_size += size
            group = str(data.get("reject_group") or RejectGroup.OTHER.value)
            reject_counts[group] = reject_counts.get(group, 0) + 1
    return HealthAuditSummary(
        total=total,
        eligible_count=eligible_count,
        rejected_count=rejected_count,
        raw_total_size=raw_total_size,
        eligible_raw_size=eligible_raw_size,
        rejected_raw_size=rejected_raw_size,
        reject_counts=reject_counts,
    )


def move_rejected_files(
    results: list[HealthAuditResult] | list[dict[str, Any]],
    rejected_root: str | Path,
) -> list[MoveRejectedResult]:
    """Move rejected MCAP files into Chinese reason directories without overwriting."""

    root = Path(rejected_root).expanduser().resolve()
    moves: list[MoveRejectedResult] = []
    for item in results:
        data = item.to_dict() if isinstance(item, HealthAuditResult) else item
        if data.get("precheck_status") != HealthStatus.REJECTED.value:
            continue
        source = Path(str(data.get("input_path") or "")).expanduser().resolve()
        parts = data.get("reject_dir_parts") or [RejectGroup.OTHER.value]
        target_dir = root.joinpath(*(str(part) for part in parts if str(part)))
        target = _non_overwriting_target(target_dir / source.name)
        if not source.exists():
            moves.append(
                MoveRejectedResult(
                    source_path=str(source),
                    target_path=str(target),
                    precheck_status=HealthStatus.REJECTED.value,
                    reject_group=data.get("reject_group"),
                    reject_reason=data.get("reject_reason"),
                    moved=False,
                    reason="source_missing",
                )
            )
            continue
        try:
            target_dir.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source), str(target))
            moves.append(
                MoveRejectedResult(
                    source_path=str(source),
                    target_path=str(target),
                    precheck_status=HealthStatus.REJECTED.value,
                    reject_group=data.get("reject_group"),
                    reject_reason=data.get("reject_reason"),
                    moved=True,
                    reason="moved",
                )
            )
        except Exception as exc:  # noqa: BLE001 - report per-file move failures.
            moves.append(
                MoveRejectedResult(
                    source_path=str(source),
                    target_path=str(target),
                    precheck_status=HealthStatus.REJECTED.value,
                    reject_group=data.get("reject_group"),
                    reject_reason=data.get("reject_reason"),
                    moved=False,
                    reason=f"{type(exc).__name__}: {exc}",
                )
            )
    return moves


def move_audited_files(
    results: list[HealthAuditResult] | list[dict[str, Any]],
    *,
    health_audited_root: str | Path,
    rejected_root: str | Path,
) -> list[MoveInputFileResult]:
    """Move eligible files to the health-audited root and rejected files to defect groups."""

    healthy_root = Path(health_audited_root).expanduser().resolve()
    rejected_base = Path(rejected_root).expanduser().resolve()
    moves: list[MoveInputFileResult] = []
    for item in results:
        data = item.to_dict() if isinstance(item, HealthAuditResult) else item
        source = Path(str(data.get("input_path") or "")).expanduser().resolve()
        status = str(data.get("precheck_status") or "")
        if status == HealthStatus.ELIGIBLE.value:
            group = "health_audited"
            target_dir = healthy_root
        elif status == HealthStatus.REJECTED.value:
            parts = data.get("reject_dir_parts") or [RejectGroup.OTHER.value]
            group = str(data.get("reject_group") or RejectGroup.OTHER.value)
            target_dir = rejected_base.joinpath(*(str(part) for part in parts if str(part)))
        else:
            continue
        target = _non_overwriting_target(target_dir / source.name)
        if not source.exists():
            moves.append(
                MoveInputFileResult(
                    source_path=str(source),
                    target_path=str(target),
                    group=group,
                    moved=False,
                    reason="source_missing",
                )
            )
            continue
        try:
            target_dir.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source), str(target))
            moves.append(
                MoveInputFileResult(
                    source_path=str(source),
                    target_path=str(target),
                    group=group,
                    moved=True,
                    reason="moved",
                )
            )
        except Exception as exc:  # noqa: BLE001 - report per-file move failures.
            moves.append(
                MoveInputFileResult(
                    source_path=str(source),
                    target_path=str(target),
                    group=group,
                    moved=False,
                    reason=f"{type(exc).__name__}: {exc}",
                )
            )
    return moves


def _result(
    path: Path,
    *,
    size: int,
    status: HealthStatus,
    group: RejectGroup | None = None,
    reason: RejectReason | None = None,
    dir_parts: tuple[str, ...] | None = None,
    topic_counts: dict[str, int] | None = None,
    read_error: str | None = None,
    pose_audit: dict[str, Any] | None = None,
) -> HealthAuditResult:
    if status == HealthStatus.REJECTED and dir_parts is None:
        dir_parts = (group.value if group is not None else RejectGroup.OTHER.value,)
    return HealthAuditResult(
        input_path=str(path),
        name=path.name,
        size=size,
        precheck_status=status,
        mtime_ns=path.stat().st_mtime_ns if path.exists() else 0,
        modified_at=(
            datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds")
            if path.exists()
            else None
        ),
        reject_group=group.value if group is not None else None,
        reject_reason=reason.value if reason is not None else None,
        reject_dir_parts=dir_parts or (),
        topic_counts=topic_counts or {},
        read_error=read_error,
        pose_audit=pose_audit,
    )


def _camera_failure(
    streams: tuple[GripperStreamConfig, ...],
    inventory: dict[str, TopicInventory],
) -> tuple[RejectGroup, RejectReason, tuple[str, ...]] | None:
    left_missing = False
    right_missing = False
    schema_mismatch = False
    for side, stream in _side_streams(streams, "image_topic").items():
        topic = inventory.get(stream.image_topic)
        if topic is None or topic.message_count <= 0:
            if side == "left":
                left_missing = True
            elif side == "right":
                right_missing = True
        elif topic.schema_name != stream.image_msg_type:
            schema_mismatch = True
    if left_missing and right_missing:
        return (
            RejectGroup.CAMERA_IMAGE_MISSING,
            RejectReason.BOTH_CAMERAS_MISSING,
            (RejectGroup.CAMERA_IMAGE_MISSING.value, "双相机缺失"),
        )
    if left_missing:
        return (
            RejectGroup.CAMERA_IMAGE_MISSING,
            RejectReason.LEFT_CAMERA_MISSING,
            (RejectGroup.CAMERA_IMAGE_MISSING.value, "左相机缺失"),
        )
    if right_missing:
        return (
            RejectGroup.CAMERA_IMAGE_MISSING,
            RejectReason.RIGHT_CAMERA_MISSING,
            (RejectGroup.CAMERA_IMAGE_MISSING.value, "右相机缺失"),
        )
    if schema_mismatch:
        return (RejectGroup.OTHER, RejectReason.IMAGE_SCHEMA_MISMATCH, (RejectGroup.OTHER.value,))
    return None


def _pose_contract_failure(
    streams: tuple[PoseStreamConfig, ...],
    inventory: dict[str, TopicInventory],
) -> tuple[RejectGroup, RejectReason, tuple[str, ...]] | None:
    missing = False
    schema_mismatch = False
    for stream in streams:
        topic = inventory.get(stream.input_topic)
        if topic is None or topic.message_count <= 0:
            missing = True
        elif topic.schema_name != stream.msg_type:
            schema_mismatch = True
    if missing:
        return (
            RejectGroup.POSE_ABNORMAL,
            RejectReason.POSE_TOPIC_MISSING,
            (RejectGroup.POSE_ABNORMAL.value, "位姿topic缺失"),
        )
    if schema_mismatch:
        return (RejectGroup.POSE_ABNORMAL, RejectReason.POSE_SCHEMA_MISMATCH, (RejectGroup.POSE_ABNORMAL.value,))
    return None


def _pose_audit_failure(data: dict[str, Any]) -> tuple[RejectGroup, RejectReason, tuple[str, ...]] | None:
    status = str(data.get("status") or "")
    if status == CLASS_NORMAL:
        return None
    if status == CLASS_MISSING_TOPIC:
        return (
            RejectGroup.POSE_ABNORMAL,
            RejectReason.POSE_TOPIC_MISSING,
            (RejectGroup.POSE_ABNORMAL.value, "位姿topic缺失"),
        )
    if status == CLASS_UNIT_MISMATCH:
        return (
            RejectGroup.POSE_ABNORMAL,
            RejectReason.POSE_UNIT_MISMATCH,
            (RejectGroup.POSE_ABNORMAL.value, "位姿单位疑似不一致"),
        )
    if status == CLASS_INVALID_POSE:
        return (
            RejectGroup.POSE_ABNORMAL,
            RejectReason.POSE_VALUE_ABNORMAL,
            (RejectGroup.POSE_ABNORMAL.value, "位姿数值异常"),
        )
    return (RejectGroup.POSE_ABNORMAL, RejectReason.POSE_VALUE_ABNORMAL, (RejectGroup.POSE_ABNORMAL.value,))


def _tactile_failure(
    topics: list[str],
    inventory: dict[str, TopicInventory],
) -> tuple[RejectGroup, RejectReason, tuple[str, ...]] | None:
    missing = [topic for topic in topics if topic not in inventory or inventory[topic].message_count <= 0]
    if missing:
        return (RejectGroup.TACTILE_MISSING, RejectReason.TACTILE_TOPIC_MISSING, (RejectGroup.TACTILE_MISSING.value,))
    mismatch = [
        topic
        for topic in topics
        if inventory[topic].schema_name is not None and inventory[topic].schema_name != TACTILE_SCHEMA_NAME
    ]
    if mismatch:
        return (RejectGroup.OTHER, RejectReason.TACTILE_SCHEMA_MISMATCH, (RejectGroup.OTHER.value,))
    return None


def _required_tactile_topics(lerobot_features: dict[str, Any] | None) -> list[str]:
    topics: list[str] = []
    for segment in enabled_state_segments(lerobot_features):
        if segment.source_field.startswith("tactile_"):
            topic = TACTILE_SOURCE_TOPICS.get(segment.source_field)
            if topic is not None:
                topics.append(topic)
    return topics


def _left_right_pose_streams(streams: tuple[PoseStreamConfig, ...]) -> tuple[PoseStreamConfig, PoseStreamConfig]:
    sided = _side_streams(streams, "input_topic")
    left = sided.get("left") or streams[0]
    right = sided.get("right") or streams[min(1, len(streams) - 1)]
    return left, right


def _side_streams(streams: tuple[Any, ...], topic_attr: str) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for index, stream in enumerate(streams):
        topic = str(getattr(stream, topic_attr, ""))
        text = topic.lower()
        side = "left" if "left" in text else "right" if "right" in text else None
        if side is None:
            side = "left" if index == 0 else "right" if index == 1 else None
        if side is not None and side not in result:
            result[side] = stream
    return result


def _non_overwriting_target(target: Path) -> Path:
    if not target.exists():
        return target
    stem = target.stem
    suffix = target.suffix
    for index in range(1, 10000):
        candidate = target.with_name(f"{stem}_{index:03d}{suffix}")
        if not candidate.exists():
            return candidate
    return target.with_name(f"{stem}_{Path(target).stat().st_mtime_ns}{suffix}")
