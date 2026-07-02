"""Data contracts for raw MCAP health audit before Web cleaning jobs."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any


class HealthStatus(StrEnum):
    ELIGIBLE = "eligible"
    REJECTED = "rejected"


class RejectGroup(StrEnum):
    UNREADABLE = "MCAP结构不可读"
    CAMERA_IMAGE_MISSING = "相机图像缺失"
    POSE_ABNORMAL = "位姿数据异常"
    TACTILE_MISSING = "触觉数据缺失"
    OTHER = "其他缺陷"


class RejectReason(StrEnum):
    NONE = ""
    MCAP_UNREADABLE = "MCAP summary 不可读"
    LEFT_CAMERA_MISSING = "左相机图像缺失"
    RIGHT_CAMERA_MISSING = "右相机图像缺失"
    BOTH_CAMERAS_MISSING = "双相机图像缺失"
    IMAGE_SCHEMA_MISMATCH = "相机图像 schema 类型不匹配"
    POSE_TOPIC_MISSING = "位姿 topic 缺失"
    POSE_SCHEMA_MISMATCH = "位姿 schema 类型不匹配"
    POSE_UNIT_MISMATCH = "位姿单位疑似不一致"
    POSE_VALUE_ABNORMAL = "位姿数值异常"
    TACTILE_TOPIC_MISSING = "触觉 topic 缺失"
    TACTILE_SCHEMA_MISMATCH = "触觉 schema 类型不匹配"
    OTHER_PRECHECK_FAILED = "其他预检失败"


@dataclass(frozen=True)
class HealthAuditResult:
    input_path: str
    name: str
    size: int
    precheck_status: HealthStatus
    reject_group: str | None = None
    reject_reason: str | None = None
    reject_dir_parts: tuple[str, ...] = ()
    topic_counts: dict[str, int] = field(default_factory=dict)
    read_error: str | None = None
    pose_audit: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["precheck_status"] = self.precheck_status.value
        return data


@dataclass(frozen=True)
class HealthAuditSummary:
    total: int
    eligible_count: int
    rejected_count: int
    raw_total_size: int
    eligible_raw_size: int
    rejected_raw_size: int
    reject_counts: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MoveRejectedResult:
    source_path: str
    target_path: str | None
    precheck_status: str
    reject_group: str | None
    reject_reason: str | None
    moved: bool
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MoveInputFileResult:
    source_path: str
    target_path: str | None
    group: str
    moved: bool
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
