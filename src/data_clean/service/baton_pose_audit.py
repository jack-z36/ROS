"""Baton Mini pose topic audit helpers for raw MCAP files."""

from __future__ import annotations

import hashlib
import math
import shutil
import statistics
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from mcap.reader import make_reader

from repo.ros2_codec import Ros2DynamicCodec, extract_pose_fields


DEFAULT_LEFT_TOPIC = "/baton_mini_left/fast_odom"
DEFAULT_RIGHT_TOPIC = "/baton_mini_right/fast_odom"
DEFAULT_MAX_SAMPLES = 1000
DEFAULT_SHOW_SAMPLES = 3
UNIT_MISMATCH_RATIO_THRESHOLD = 100.0
QUATERNION_NORM_TOLERANCE = 0.05

SUPPORTED_POSE_TYPES = {
    "nav_msgs/msg/Odometry",
    "geometry_msgs/msg/PoseStamped",
}

CLASS_NORMAL = "unit_consistent_likely"
CLASS_UNIT_MISMATCH = "unit_mismatch_suspected"
CLASS_MISSING_TOPIC = "missing_pose_topic"
CLASS_INVALID_POSE = "pose_value_invalid_suspected"
CLASS_DECODE_FAILED = "decode_failed"

MOVE_GROUPS = {
    CLASS_NORMAL: "normal",
    CLASS_UNIT_MISMATCH: "unit_mismatch",
    CLASS_MISSING_TOPIC: "other_issue",
    CLASS_INVALID_POSE: "other_issue",
    CLASS_DECODE_FAILED: "other_issue",
}

UNIT_NOTE = (
    "ROS nav_msgs/msg/Odometry and geometry_msgs/msg/PoseStamped position fields "
    "are interpreted as meters by convention. Quaternions are unitless and should "
    "have norm close to 1. This audit infers unit consistency from value scale; "
    "it does not rewrite MCAP data or prove the hardware's true unit."
)


@dataclass(frozen=True)
class PoseSideStats:
    topic: str
    schema_name: str | None
    message_count: int
    sample_count: int
    xyz_min: list[float] | None = None
    xyz_max: list[float] | None = None
    xyz_mean: list[float] | None = None
    median_abs_xyz: float | None = None
    p95_abs_xyz: float | None = None
    quaternion_norm_min: float | None = None
    quaternion_norm_max: float | None = None
    samples: list[list[float]] = field(default_factory=list)


@dataclass(frozen=True)
class BatonPoseAuditResult:
    input_path: str
    name: str
    status: str
    move_group: str
    reason: str
    unit_note: str
    left: PoseSideStats
    right: PoseSideStats
    median_scale_ratio: float | None = None
    p95_scale_ratio: float | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MoveResult:
    source_path: str
    target_path: str
    status: str
    move_group: str
    moved: bool
    reason: str


def audit_mcap_file(
    mcap_path: str | Path,
    *,
    left_topic: str = DEFAULT_LEFT_TOPIC,
    right_topic: str = DEFAULT_RIGHT_TOPIC,
    max_samples: int = DEFAULT_MAX_SAMPLES,
    show_samples: int = DEFAULT_SHOW_SAMPLES,
    ratio_threshold: float = UNIT_MISMATCH_RATIO_THRESHOLD,
) -> BatonPoseAuditResult:
    """Audit left/right Baton Mini pose values from a single MCAP file."""

    path = Path(mcap_path).expanduser().resolve()
    left_topic = left_topic or DEFAULT_LEFT_TOPIC
    right_topic = right_topic or DEFAULT_RIGHT_TOPIC
    max_samples = max(1, int(max_samples))
    show_samples = max(0, int(show_samples))

    try:
        raw = _collect_pose_samples(
            path,
            left_topic=left_topic,
            right_topic=right_topic,
            max_samples=max_samples,
        )
        left = _build_side_stats(left_topic, raw[left_topic], show_samples)
        right = _build_side_stats(right_topic, raw[right_topic], show_samples)
        status, reason, median_ratio, p95_ratio = classify_pose_stats(
            left,
            right,
            ratio_threshold=ratio_threshold,
        )
        return BatonPoseAuditResult(
            input_path=str(path),
            name=path.name,
            status=status,
            move_group=MOVE_GROUPS[status],
            reason=reason,
            unit_note=UNIT_NOTE,
            left=left,
            right=right,
            median_scale_ratio=median_ratio,
            p95_scale_ratio=p95_ratio,
        )
    except Exception as exc:  # noqa: BLE001 - report file-local decode failures.
        empty_left = PoseSideStats(topic=left_topic, schema_name=None, message_count=0, sample_count=0)
        empty_right = PoseSideStats(topic=right_topic, schema_name=None, message_count=0, sample_count=0)
        return BatonPoseAuditResult(
            input_path=str(path),
            name=path.name,
            status=CLASS_DECODE_FAILED,
            move_group=MOVE_GROUPS[CLASS_DECODE_FAILED],
            reason=f"{type(exc).__name__}: {exc}",
            unit_note=UNIT_NOTE,
            left=empty_left,
            right=empty_right,
            error=f"{type(exc).__name__}: {exc}",
        )


def audit_mcap_files(
    mcap_paths: list[str | Path],
    *,
    left_topic: str = DEFAULT_LEFT_TOPIC,
    right_topic: str = DEFAULT_RIGHT_TOPIC,
    max_samples: int = DEFAULT_MAX_SAMPLES,
    show_samples: int = DEFAULT_SHOW_SAMPLES,
) -> list[BatonPoseAuditResult]:
    return [
        audit_mcap_file(
            path,
            left_topic=left_topic,
            right_topic=right_topic,
            max_samples=max_samples,
            show_samples=show_samples,
        )
        for path in mcap_paths
    ]


def classify_pose_stats(
    left: PoseSideStats,
    right: PoseSideStats,
    *,
    ratio_threshold: float = UNIT_MISMATCH_RATIO_THRESHOLD,
    quaternion_norm_tolerance: float = QUATERNION_NORM_TOLERANCE,
) -> tuple[str, str, float | None, float | None]:
    """Return fine-grained class, reason, median ratio, and p95 ratio."""

    if left.sample_count == 0 or right.sample_count == 0:
        missing = []
        if left.sample_count == 0:
            missing.append("left")
        if right.sample_count == 0:
            missing.append("right")
        return CLASS_MISSING_TOPIC, f"missing_or_empty_pose_topic: {', '.join(missing)}", None, None

    invalid_quaternion_sides = []
    for side_name, stats in (("left", left), ("right", right)):
        values = [stats.quaternion_norm_min, stats.quaternion_norm_max]
        if any(value is not None and abs(value - 1.0) > quaternion_norm_tolerance for value in values):
            invalid_quaternion_sides.append(side_name)
    if invalid_quaternion_sides:
        return (
            CLASS_INVALID_POSE,
            f"quaternion_norm_out_of_range: {', '.join(invalid_quaternion_sides)}",
            _scale_ratio(left.median_abs_xyz, right.median_abs_xyz),
            _scale_ratio(left.p95_abs_xyz, right.p95_abs_xyz),
        )

    median_ratio = _scale_ratio(left.median_abs_xyz, right.median_abs_xyz)
    p95_ratio = _scale_ratio(left.p95_abs_xyz, right.p95_abs_xyz)
    if (median_ratio is not None and median_ratio >= ratio_threshold) or (
        p95_ratio is not None and p95_ratio >= ratio_threshold
    ):
        return (
            CLASS_UNIT_MISMATCH,
            f"left/right xyz scale ratio exceeds {ratio_threshold:g}",
            median_ratio,
            p95_ratio,
        )

    return CLASS_NORMAL, "left/right xyz scale appears consistent", median_ratio, p95_ratio


def move_audit_results(
    results: list[dict[str, Any]] | list[BatonPoseAuditResult],
    classified_dir: str | Path,
) -> list[MoveResult]:
    """Move audited MCAP files into simplified classification directories."""

    root = Path(classified_dir).expanduser().resolve()
    move_results: list[MoveResult] = []
    for item in results:
        data = item.to_dict() if isinstance(item, BatonPoseAuditResult) else item
        source = Path(str(data["input_path"])).expanduser().resolve()
        status = str(data.get("status") or CLASS_DECODE_FAILED)
        move_group = str(data.get("move_group") or MOVE_GROUPS.get(status, "other_issue"))
        target_dir = root / move_group
        target_dir.mkdir(parents=True, exist_ok=True)
        target = _non_overwriting_target(target_dir / source.name, source)
        if not source.exists():
            move_results.append(
                MoveResult(
                    source_path=str(source),
                    target_path=str(target),
                    status=status,
                    move_group=move_group,
                    moved=False,
                    reason="source_missing",
                )
            )
            continue
        shutil.move(str(source), str(target))
        move_results.append(
            MoveResult(
                source_path=str(source),
                target_path=str(target),
                status=status,
                move_group=move_group,
                moved=True,
                reason=str(data.get("reason") or ""),
            )
        )
    return move_results


def summarize_results(results: list[BatonPoseAuditResult] | list[dict[str, Any]]) -> dict[str, Any]:
    counts: dict[str, int] = {}
    move_counts: dict[str, int] = {}
    for item in results:
        data = item.to_dict() if isinstance(item, BatonPoseAuditResult) else item
        status = str(data.get("status") or CLASS_DECODE_FAILED)
        move_group = str(data.get("move_group") or MOVE_GROUPS.get(status, "other_issue"))
        counts[status] = counts.get(status, 0) + 1
        move_counts[move_group] = move_counts.get(move_group, 0) + 1
    return {
        "total": len(results),
        "status_counts": counts,
        "move_group_counts": move_counts,
        "has_unit_mismatch": counts.get(CLASS_UNIT_MISMATCH, 0) > 0,
        "unit_note": UNIT_NOTE,
    }


def _collect_pose_samples(path: Path, *, left_topic: str, right_topic: str, max_samples: int) -> dict[str, dict[str, Any]]:
    targets = {left_topic, right_topic}
    result: dict[str, dict[str, Any]] = {
        left_topic: {"schema_name": None, "message_count": 0, "samples": []},
        right_topic: {"schema_name": None, "message_count": 0, "samples": []},
    }
    codec = Ros2DynamicCodec()
    with path.open("rb") as fh:
        reader = make_reader(fh)
        for schema, channel, message in reader.iter_messages(log_time_order=False):
            if channel.topic not in targets:
                continue
            side = result[channel.topic]
            side["message_count"] += 1
            side["schema_name"] = schema.name if schema is not None else None
            if len(side["samples"]) >= max_samples:
                continue
            if schema is None:
                continue
            if schema.name not in SUPPORTED_POSE_TYPES:
                continue
            decoded = codec.decode(schema, message)
            side["samples"].append(list(extract_pose_fields(decoded, schema.name)))
    return result


def _build_side_stats(topic: str, raw: dict[str, Any], show_samples: int) -> PoseSideStats:
    samples = [[float(value) for value in row] for row in raw.get("samples", [])]
    if not samples:
        return PoseSideStats(
            topic=topic,
            schema_name=raw.get("schema_name"),
            message_count=int(raw.get("message_count", 0)),
            sample_count=0,
            samples=[],
        )

    xyz_columns = list(zip(*[row[:3] for row in samples]))
    xyz_abs = [abs(value) for row in samples for value in row[:3]]
    qnorms = [_quaternion_norm(row[3:7]) for row in samples]
    return PoseSideStats(
        topic=topic,
        schema_name=raw.get("schema_name"),
        message_count=int(raw.get("message_count", 0)),
        sample_count=len(samples),
        xyz_min=[min(axis) for axis in xyz_columns],
        xyz_max=[max(axis) for axis in xyz_columns],
        xyz_mean=[statistics.fmean(axis) for axis in xyz_columns],
        median_abs_xyz=statistics.median(xyz_abs),
        p95_abs_xyz=_percentile(xyz_abs, 95.0),
        quaternion_norm_min=min(qnorms),
        quaternion_norm_max=max(qnorms),
        samples=samples[:show_samples],
    )


def _percentile(values: list[float], percentile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * percentile / 100.0
    low = math.floor(position)
    high = math.ceil(position)
    if low == high:
        return float(ordered[low])
    return float(ordered[low] * (high - position) + ordered[high] * (position - low))


def _scale_ratio(left_value: float | None, right_value: float | None) -> float | None:
    if left_value is None or right_value is None:
        return None
    small = max(min(abs(left_value), abs(right_value)), 1e-12)
    return max(abs(left_value), abs(right_value)) / small


def _quaternion_norm(values: list[float]) -> float:
    qx, qy, qz, qw = values
    return math.sqrt(qx * qx + qy * qy + qz * qz + qw * qw)


def _non_overwriting_target(candidate: Path, source: Path) -> Path:
    if not candidate.exists():
        return candidate
    digest = hashlib.sha1(str(source).encode("utf-8")).hexdigest()[:8]
    stem = candidate.stem
    suffix = candidate.suffix
    for index in range(1, 10_000):
        target = candidate.with_name(f"{stem}_{digest}_{index:03d}{suffix}")
        if not target.exists():
            return target
    raise RuntimeError(f"unable to allocate non-overwriting target for {candidate}")
