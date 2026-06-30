from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from schemas.reliability import MissingIntervalIssue, SampleReliabilityIssue, SignalSampleRef
from schemas.repair import RepairDecisionStatus, RepairMethod, SignalRepairRun


REPAIRABLE_ACTIONS = {"repairable_interpolate", "repairable_hold"}


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
    grouped: dict[tuple[str, str, int | float, int, str], list[SampleReliabilityIssue]] = {}
    for issue in issues:
        sample_ref = issue.sample_ref
        key = (
            sample_ref.topic,
            sample_ref.time_domain,
            sample_ref.timestamp,
            sample_ref.message_index,
            sample_ref.modality,
        )
        grouped.setdefault(key, []).append(issue)

    return [SampleIssueGroup(issues=items, sample_ref=items[0].sample_ref) for items in grouped.values()]


def build_repair_runs(
    issue_groups: Iterable[SampleIssueGroup],
    missing_intervals: Iterable[MissingIntervalIssue] = (),
) -> list[SignalRepairRun]:
    ordered_groups = sorted(
        issue_groups,
        key=lambda group: (
            group.sample_ref.topic,
            group.sample_ref.modality,
            _replacement_unit(group),
            group.sample_ref.message_index,
            group.sample_ref.timestamp,
        ),
    )
    runs: list[SignalRepairRun] = []
    current: list[SampleIssueGroup] = []

    for group in ordered_groups:
        if current and not _can_extend_run(current[-1], group, missing_intervals):
            runs.append(_make_repair_run(current, len(runs)))
            current = []
        current.append(group)

    if current:
        runs.append(_make_repair_run(current, len(runs)))

    return runs


def find_legal_neighbors(
    target_refs: Iterable[SignalSampleRef],
    samples: Iterable[SignalSampleRef],
    dirty_issue_groups: Iterable[SampleIssueGroup],
    missing_intervals: Iterable[MissingIntervalIssue] = (),
    repaired_refs: Iterable[SignalSampleRef] = (),
) -> LegalNeighbors:
    targets = sorted(target_refs, key=lambda ref: (ref.message_index, ref.timestamp))
    if not targets:
        return LegalNeighbors(previous_ref=None, next_ref=None, reason="missing_target")

    first = targets[0]
    last = targets[-1]
    dirty_keys = {_sample_key(group.sample_ref) for group in dirty_issue_groups}
    repaired_keys = {_sample_key(ref) for ref in repaired_refs}
    target_keys = {_sample_key(ref) for ref in targets}

    topic_samples = sorted(
        (sample for sample in samples if sample.topic == first.topic and sample.modality == first.modality),
        key=lambda ref: (ref.message_index, ref.timestamp),
    )

    previous_ref = next(
        (
            sample
            for sample in reversed(topic_samples)
            if sample.message_index < first.message_index
            and _is_clean_neighbor(sample, dirty_keys, repaired_keys, target_keys)
            and not _crosses_missing_interval(sample, first, missing_intervals)
        ),
        None,
    )
    next_ref = next(
        (
            sample
            for sample in topic_samples
            if sample.message_index > last.message_index
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


def _make_repair_run(groups: list[SampleIssueGroup], run_index: int) -> SignalRepairRun:
    first = groups[0]
    repairable = all(_is_group_repairable(group) for group in groups)
    return SignalRepairRun(
        repair_run_id=f"repair-run-{run_index + 1:04d}",
        source_topic=first.sample_ref.topic,
        modality=first.sample_ref.modality,
        replacement_unit=_replacement_unit(first),
        input_window_refs=[group.sample_ref for group in groups],
        sample_issue_ids=[issue_id for group in groups for issue_id in group.issue_ids],
        status=RepairDecisionStatus.REPAIRED if repairable else RepairDecisionStatus.UNREPAIRABLE,
        applied_method=_repair_method(first) if repairable else None,
        reason="repairable_run_candidate" if repairable else "mixed_repairability_in_run",
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
        and _actions_compatible(previous, current)
        and current_ref.message_index == previous_ref.message_index + 1
        and not _crosses_missing_interval(previous_ref, current_ref, missing_intervals)
    )


def _is_group_repairable(group: SampleIssueGroup) -> bool:
    return all(issue.suggested_action in REPAIRABLE_ACTIONS for issue in group.issues)


def _actions_compatible(previous: SampleIssueGroup, current: SampleIssueGroup) -> bool:
    if _is_group_repairable(previous) and _is_group_repairable(current):
        return _repair_method(previous) == _repair_method(current)
    return True


def _repair_method(group: SampleIssueGroup) -> RepairMethod | None:
    actions = {issue.suggested_action for issue in group.issues}
    if actions == {"repairable_interpolate"}:
        return RepairMethod.INTERPOLATE_LINEAR
    if actions == {"repairable_hold"}:
        return RepairMethod.FORWARD_FILL
    return None


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
