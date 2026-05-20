"""Runtime smoke test types for MVP acceptance testing."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .fake_service_types import FakeServiceBehavior, FakeServicePlan
from .run_directory_types import RunArtifactPath, RunDirectory
from .runtime_context import RunContext, RunMode, SceneName, ServiceMode
from .runtime_dispatch_types import SceneDispatchPlan
from .runtime_enums import FakeServiceBehavior as FakeServiceBehaviorEnum
from .runtime_enums import RunStatus
from .runtime_results import PipelineResult, RuntimeErrorRef


class RuntimeSmokeCaseKind(str, Enum):
    """Controlled smoke test case categories."""

    SINGLE_SCENE_SUCCESS = "single_scene_success"
    PIPELINE_SUCCESS = "pipeline_success"
    MISSING_CONFIG = "missing_config"
    MISSING_INPUT = "missing_input"
    CONTROLLED_FAILURE = "controlled_failure"


@dataclass
class RuntimeSmokeAssertion:
    """A single assertion comparing expected vs actual in a smoke test."""

    assertion_name: str
    expected_summary: str
    actual_summary: str
    passed: bool
    details: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.assertion_name:
            raise ValueError("assertion_name must be non-empty")
        if not self.expected_summary:
            raise ValueError("expected_summary must be non-empty")
        if not self.actual_summary:
            raise ValueError("actual_summary must be non-empty")


@dataclass
class RuntimeSmokeTestCase:
    """A single smoke test case definition for Runtime MVP."""

    case_id: str
    title: str
    case_kind: RuntimeSmokeCaseKind
    target_scenes: list[SceneName] = field(default_factory=list)
    run_mode: RunMode = RunMode.DEV_SINGLE_SCENE
    service_mode: ServiceMode = ServiceMode.FAKE
    fake_behavior: FakeServiceBehavior = FakeServiceBehaviorEnum.SUCCESS
    expected_status: RunStatus = RunStatus.SUCCEEDED
    expected_error_code: str = ""
    expected_artifacts: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.case_id:
            raise ValueError("case_id must be non-empty")
        if not self.title:
            raise ValueError("title must be non-empty")
        if self.service_mode == ServiceMode.REAL:
            raise ValueError(
                "service_mode must be FAKE for Runtime MVP smoke tests"
            )
        if self.case_kind in (
            RuntimeSmokeCaseKind.CONTROLLED_FAILURE,
            RuntimeSmokeCaseKind.MISSING_CONFIG,
            RuntimeSmokeCaseKind.MISSING_INPUT,
        ):
            if not self.expected_error_code:
                raise ValueError(
                    f"expected_error_code must be non-empty for {self.case_kind.value} case"
                )
            if self.expected_status == RunStatus.SUCCEEDED:
                raise ValueError(
                    f"failure case {self.case_kind.value} must not expect SUCCEEDED status"
                )
        if self.case_kind in (
            RuntimeSmokeCaseKind.SINGLE_SCENE_SUCCESS,
            RuntimeSmokeCaseKind.PIPELINE_SUCCESS,
        ):
            if not self.target_scenes:
                raise ValueError(
                    f"target_scenes must be non-empty for {self.case_kind.value} case"
                )


@dataclass
class RuntimeSmokeTestSuite:
    """A collection of Runtime smoke test cases for MVP acceptance."""

    suite_id: str
    title: str
    cases: list[RuntimeSmokeTestCase]
    required_cases: list[str] = field(default_factory=list)
    allowed_service_mode: ServiceMode = ServiceMode.FAKE

    def __post_init__(self) -> None:
        if not self.suite_id:
            raise ValueError("suite_id must be non-empty")
        if not self.title:
            raise ValueError("title must be non-empty")
        if not self.cases:
            raise ValueError("cases must be non-empty")
        case_ids = {c.case_id for c in self.cases}
        for req_id in self.required_cases:
            if req_id not in case_ids:
                raise ValueError(
                    f"required_case {req_id!r} not found in cases"
                )
        if self.allowed_service_mode != ServiceMode.FAKE:
            raise ValueError(
                "allowed_service_mode must be FAKE for Runtime MVP"
            )
        for case in self.cases:
            if case.service_mode != ServiceMode.FAKE:
                raise ValueError(
                    f"case {case.case_id!r} uses non-fake service_mode"
                )


@dataclass
class RuntimeSmokeTestResult:
    """Structured result of a single smoke test case execution."""

    case_id: str
    status: RunStatus
    pipeline_result: PipelineResult | None = None
    run_directory: RunDirectory | None = None
    observed_artifacts: dict[str, RunArtifactPath] = field(default_factory=dict)
    observed_error: RuntimeErrorRef | None = None
    assertions: list[RuntimeSmokeAssertion] = field(default_factory=list)
    duration_ms: int | None = None

    def __post_init__(self) -> None:
        if not self.case_id:
            raise ValueError("case_id must be non-empty")
        if self.status == RunStatus.FAILED and self.observed_error is None:
            raise ValueError(
                "observed_error must be provided when status is FAILED"
            )
        if self.status == RunStatus.SUCCEEDED and self.pipeline_result is None:
            raise ValueError(
                "pipeline_result should be provided when status is SUCCEEDED"
            )
