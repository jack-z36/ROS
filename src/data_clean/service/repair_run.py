from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from schemas.reliability import MissingIntervalIssue, SampleReliabilityIssue, SignalSampleRef
from schemas.repair import (
    RepairDecisionStatus,
    RepairDisposition,
    RepairMethod,
    SignalIssueDisposition,
    SignalRepairRun,
)


@dataclass(frozen=True)
class SampleIssueGroup:
    sample_ref: SignalSampleRef
    issues: list[SampleReliabilityIssue]

    @property
    def issue_ids(self) -> list[str]:
        return [issue.issue_id for issue in self.issues]

    @property
    def field_paths(self) -> list[str]:
        return [issue.field_path for issue in self.issues]


@dataclass(frozen=True)
class LegalNeighbors:
    previous_ref: SignalSampleRef | None
    next_ref: SignalSampleRef | None
    reason: str = "success"


def aggregate_sample_issues(issues: Iterable[SampleReliabilityIssue]) -> list[SampleIssueGroup]:
    grouped: dict[tuple[str, str, int | float, int, str, str], list[SampleReliabilityIssue]] = {}
    for issue in issues:
        sample_ref = issue.sample_ref
        key = (
            sample_ref.topic,
            sample_ref.time_domain,
            sample_ref.timestamp,
            sample_ref.message_index,
            sample_ref.modality,
            issue.field_path,
        )
        grouped.setdefault(key, []).append(issue)

    return [SampleIssueGroup(issues=items, sample_ref=items[0].sample_ref) for items in grouped.values()]


def build_repair_runs(
    issue_groups: Iterable[SampleIssueGroup],
    missing_intervals: Iterable[MissingIntervalIssue] = (),
    dispositions: Iterable[SignalIssueDisposition] | None = None,
) -> list[SignalRepairRun]:
    disposition_by_issue = {
        disposition.issue_id: disposition
        for disposition in (dispositions if dispositions is not None else decide_issue_dispositions(issue_groups))
    }
    ordered_groups = sorted(
        issue_groups,
        key=lambda group: (
            group.sample_ref.topic,
            group.sample_ref.modality,
            _replacement_unit(group),
            group.sample_ref.timestamp,
            group.sample_ref.message_index,
        ),
    )
    runs: list[SignalRepairRun] = []
    current: list[SampleIssueGroup] = []

    for group in ordered_groups:
        if current and not _can_extend_run(current[-1], group, missing_intervals):
            runs.append(_make_repair_run(current, disposition_by_issue))
            current = []
        current.append(group)

    if current:
        runs.append(_make_repair_run(current, disposition_by_issue))

    return runs


def find_legal_neighbors(
    target_refs: Iterable[SignalSampleRef],
    samples: Iterable[SignalSampleRef],
    dirty_issue_groups: Iterable[SampleIssueGroup],
    missing_intervals: Iterable[MissingIntervalIssue] = (),
    repaired_refs: Iterable[SignalSampleRef] = (),
    replacement_unit: str | None = None,
) -> LegalNeighbors:
    targets = sorted(target_refs, key=lambda ref: (ref.timestamp, ref.message_index))
    if not targets:
        return LegalNeighbors(previous_ref=None, next_ref=None, reason="missing_target")

    first = targets[0]
    last = targets[-1]
    dirty_keys = {
        _sample_key(group.sample_ref)
        for group in dirty_issue_groups
        if replacement_unit is None or _replacement_unit(group) == replacement_unit
    }
    repaired_keys = {_sample_key(ref) for ref in repaired_refs}
    target_keys = {_sample_key(ref) for ref in targets}

    topic_samples = sorted(
        (
            sample
            for sample in samples
            if sample.topic == first.topic
            and sample.modality == first.modality
            and sample.time_domain == first.time_domain
        ),
        key=lambda ref: (ref.timestamp, ref.message_index),
    )

    previous_ref = next(
        (
            sample
            for sample in reversed(topic_samples)
            if (sample.timestamp, sample.message_index) < (first.timestamp, first.message_index)
            and _is_clean_neighbor(sample, dirty_keys, repaired_keys, target_keys)
            and not _crosses_missing_interval(sample, first, missing_intervals)
        ),
        None,
    )
    next_ref = next(
        (
            sample
            for sample in topic_samples
            if (sample.timestamp, sample.message_index) > (last.timestamp, last.message_index)
            and _is_clean_neighbor(sample, dirty_keys, repaired_keys, target_keys)
            and not _crosses_missing_interval(last, sample, missing_intervals)
        ),
        None,
    )

    if previous_ref is None and next_ref is None:
        return LegalNeighbors(previous_ref=None, next_ref=None, reason="missing_clean_neighbor")
    if previous_ref is None:
        return LegalNeighbors(previous_ref=None, next_ref=next_ref, reason="missing_previous_neighbor")
    if next_ref is None:
        return LegalNeighbors(previous_ref=previous_ref, next_ref=None, reason="missing_next_neighbor")
    return LegalNeighbors(previous_ref=previous_ref, next_ref=next_ref)


def decide_issue_dispositions(
    issue_groups: Iterable[SampleIssueGroup],
) -> list[SignalIssueDisposition]:
    dispositions: list[SignalIssueDisposition] = []
    method_by_field = {
        "pose.position": RepairMethod.LINEAR_INTERPOLATE,
        "pose.orientation": RepairMethod.SLERP_INTERPOLATE,
        "gripper.value": RepairMethod.LINEAR_INTERPOLATE,
        "tactile.frame": RepairMethod.LINEAR_INTERPOLATE,
    }
    for group in issue_groups:
        method = method_by_field.get(_replacement_unit(group))
        for issue in group.issues:
            action = RepairDisposition.AUTO_REPAIR if method is not None else RepairDisposition.MANUAL_REVIEW
            dispositions.append(
                SignalIssueDisposition(
                    issue_id=issue.issue_id,
                    action=action,
                    field_path=issue.field_path,
                    reason="scene2_auto_repair_policy" if method is not None else "unsupported_replacement_unit",
                    sample_ref=issue.sample_ref,
                    planned_method=method,
                )
            )
    return dispositions


def _make_repair_run(
    groups: list[SampleIssueGroup],
    disposition_by_issue: dict[str, SignalIssueDisposition],
) -> SignalRepairRun:
    first = groups[0]
    issue_dispositions = [disposition_by_issue[issue_id] for group in groups for issue_id in group.issue_ids]
    auto_repair = bool(issue_dispositions) and all(
        disposition.action is RepairDisposition.AUTO_REPAIR for disposition in issue_dispositions
    )
    planned_methods = {disposition.planned_method for disposition in issue_dispositions}
    planned_method = next(iter(planned_methods)) if len(planned_methods) == 1 else None
    first_ref = first.sample_ref
    replacement_unit = _replacement_unit(first)
    return SignalRepairRun(
        repair_run_id=(
            f"repair-{first_ref.topic.strip('/').replace('/', '_')}-"
            f"{replacement_unit.replace('.', '_')}-{first_ref.message_index}"
        ),
        source_topic=first.sample_ref.topic,
        modality=first.sample_ref.modality,
        replacement_unit=_replacement_unit(first),
        input_window_refs=[group.sample_ref for group in groups],
        sample_issue_ids=[issue_id for group in groups for issue_id in group.issue_ids],
        status=RepairDecisionStatus.PENDING if auto_repair else RepairDecisionStatus.SKIPPED,
        applied_method=None,
        reason="auto_repair_approved" if auto_repair else "not_approved_for_auto_repair",
        disposition=RepairDisposition.AUTO_REPAIR if auto_repair else issue_dispositions[0].action,
        planned_method=planned_method,
        replacement_contract=_replacement_contract(first),
        sample_records=[],
    )


def _can_extend_run(
    previous: SampleIssueGroup,
    current: SampleIssueGroup,
    missing_intervals: Iterable[MissingIntervalIssue],
) -> bool:
    previous_ref = previous.sample_ref
    current_ref = current.sample_ref
    return (
        previous_ref.topic == current_ref.topic
        and previous_ref.modality == current_ref.modality
        and _replacement_unit(previous) == _replacement_unit(current)
        and previous_ref.time_domain == current_ref.time_domain
        and current_ref.message_index == previous_ref.message_index + 1
        and not _crosses_missing_interval(previous_ref, current_ref, missing_intervals)
    )


def _replacement_unit(group: SampleIssueGroup) -> str:
    return group.issues[0].field_path


def _sample_key(sample_ref: SignalSampleRef) -> tuple[str, str, int | float, int, str]:
    return (
        sample_ref.topic,
        sample_ref.time_domain,
        sample_ref.timestamp,
        sample_ref.message_index,
        sample_ref.modality,
    )


def _replacement_contract(group: SampleIssueGroup) -> dict[str, object]:
    if _replacement_unit(group) != "tactile.frame":
        return {}
    for issue in group.issues:
        for evidence in issue.evidence:
            if "rows" in evidence and "cols" in evidence:
                return {"rows": int(evidence["rows"]), "cols": int(evidence["cols"])}
    return {}


def _is_clean_neighbor(
    sample_ref: SignalSampleRef,
    dirty_keys: set[tuple[str, str, int | float, int, str]],
    repaired_keys: set[tuple[str, str, int | float, int, str]],
    target_keys: set[tuple[str, str, int | float, int, str]],
) -> bool:
    key = _sample_key(sample_ref)
    return key not in dirty_keys and key not in repaired_keys and key not in target_keys


def _crosses_missing_interval(
    left: SignalSampleRef,
    right: SignalSampleRef,
    missing_intervals: Iterable[MissingIntervalIssue],
) -> bool:
    start = min(left.timestamp, right.timestamp)
    end = max(left.timestamp, right.timestamp)
    return any(
        interval.topic == left.topic
        and interval.modality == left.modality
        and interval.time_domain == left.time_domain
        and start < interval.end_time
        and interval.start_time < end
        for interval in missing_intervals
    )
