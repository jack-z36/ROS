"""Runtime precheck types: config precheck and input artifact precheck types."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .runtime_config_types import ConfigSnapshot, EffectiveRuntimeConfig
    from .runtime_results import RuntimeErrorRef

from .runtime_enums import RunMode, RunStatus, SceneName


class PrecheckRuleId(str, Enum):
    """Stable identifiers for the fixed set of Runtime precheck rules."""

    EFFECTIVE_CONFIG_EXISTS = "effective_config_exists"
    CONFIG_SOURCE_TRACEABLE = "config_source_traceable"
    OVERRIDE_SET_RECORDED = "override_set_recorded"
    SNAPSHOT_IS_TRACEABLE = "snapshot_is_traceable"
    TARGET_SCENE_CONFIG_EXISTS = "target_scene_config_exists"
    SCENE_SEQUENCE_VALID = "scene_sequence_valid"
    GLOBAL_RUNTIME_CONFIG_EXISTS = "global_runtime_config_exists"


@dataclass
class ConfigPrecheckRule:
    """A single Runtime-level precheck rule targeting global or per-scene config."""

    rule_id: str
    scope: str
    required: bool
    description: str
    failure_issue_code: str

    def __post_init__(self) -> None:
        if not self.rule_id:
            raise ValueError("rule_id must be non-empty")
        if not self.scope:
            raise ValueError("scope must be non-empty")
        if not self.description:
            raise ValueError("description must be non-empty")
        if not self.failure_issue_code:
            raise ValueError("failure_issue_code must be non-empty")


PRECHECK_RULES: list[ConfigPrecheckRule] = [
    ConfigPrecheckRule(
        rule_id=PrecheckRuleId.EFFECTIVE_CONFIG_EXISTS,
        scope="global",
        required=True,
        description="Effective config must exist and be a consumable mapping.",
        failure_issue_code="effective_config_missing",
    ),
    ConfigPrecheckRule(
        rule_id=PrecheckRuleId.CONFIG_SOURCE_TRACEABLE,
        scope="global",
        required=True,
        description="Config source must be locatable with source type and path.",
        failure_issue_code="config_source_untraceable",
    ),
    ConfigPrecheckRule(
        rule_id=PrecheckRuleId.OVERRIDE_SET_RECORDED,
        scope="global",
        required=True,
        description="Override set must be explicitly recorded (empty is valid).",
        failure_issue_code="override_set_missing",
    ),
    ConfigPrecheckRule(
        rule_id=PrecheckRuleId.SNAPSHOT_IS_TRACEABLE,
        scope="global",
        required=True,
        description="Config snapshot path must reside inside the run directory.",
        failure_issue_code="snapshot_untraceable",
    ),
    ConfigPrecheckRule(
        rule_id=PrecheckRuleId.TARGET_SCENE_CONFIG_EXISTS,
        scope="scene",
        required=True,
        description="Each target scene must have a config block in effective config.",
        failure_issue_code="missing_scene_config",
    ),
    ConfigPrecheckRule(
        rule_id=PrecheckRuleId.SCENE_SEQUENCE_VALID,
        scope="global",
        required=True,
        description="Full-pipeline target scene order must match SceneName order.",
        failure_issue_code="invalid_scene_sequence",
    ),
    ConfigPrecheckRule(
        rule_id=PrecheckRuleId.GLOBAL_RUNTIME_CONFIG_EXISTS,
        scope="global",
        required=True,
        description="Required global runtime config fields must be present.",
        failure_issue_code="missing_global_runtime_config",
    ),
]


@dataclass
class ConfigPrecheckIssue:
    """A single issue found during config prechecking."""

    issue_code: str
    severity: str
    message: str
    config_path: str | None = None
    scene_name: SceneName | None = None
    details: dict[str, Any] = field(default_factory=dict)
    runtime_error_ref: RuntimeErrorRef | None = None

    def __post_init__(self) -> None:
        if not self.issue_code:
            raise ValueError("issue_code must be non-empty")
        if not self.severity:
            raise ValueError("severity must be non-empty")
        if not self.message:
            raise ValueError("message must be non-empty")


@dataclass
class SceneConfigRequirement:
    """Runtime-level minimum config requirements for a single scene."""

    scene_name: SceneName | None
    required_sections: list[str] = field(default_factory=list)
    required_fields: list[str] = field(default_factory=list)
    required_semantics: list[str] = field(default_factory=list)
    notes: str = ""

    def __post_init__(self) -> None:
        if self.scene_name is None:
            raise ValueError("scene_name must be provided")


@dataclass
class ConfigPrecheckResult:
    """Result of a Runtime config precheck execution."""

    passed: bool
    checked_scenes: list[SceneName]
    issues: list[ConfigPrecheckIssue]
    effective_config_ref: EffectiveRuntimeConfig
    checked_rules: list[str] = field(default_factory=list)
    config_snapshot_ref: ConfigSnapshot | None = None
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.checked_scenes:
            raise ValueError("checked_scenes must be non-empty")
        if self.passed:
            for issue in self.issues:
                if issue.severity == "error":
                    raise ValueError(
                        "passed=true but contains error-severity issue"
                    )


# =============================================================================
# Input Artifact Precheck Types
# =============================================================================


@dataclass
class InputArtifactRequirement:
    """A single input artifact requirement for a target scene."""

    scene_name: SceneName | None
    artifact_role: str
    path_config_key: str
    required_kind: str
    required_for_modes: list[RunMode]
    allow_manual_override: bool
    description: str = ""

    def __post_init__(self) -> None:
        if self.scene_name is None:
            raise ValueError("scene_name must be provided")
        if not self.artifact_role:
            raise ValueError("artifact_role must be non-empty")
        if not self.path_config_key:
            raise ValueError("path_config_key must be non-empty")
        if not self.required_kind:
            raise ValueError("required_kind must be non-empty")
        if not self.required_for_modes:
            raise ValueError("required_for_modes must be non-empty")


@dataclass
class InputArtifactCheckResult:
    """Result of checking a single input artifact requirement."""

    requirement: InputArtifactRequirement
    candidate_path: str | None = None
    status: RunStatus = RunStatus.FAILED
    exists: bool = False
    readable: bool = False
    kind_matches: bool = False
    error: RuntimeErrorRef | None = None

    def __post_init__(self) -> None:
        if self.status == RunStatus.SUCCEEDED and not self.candidate_path:
            raise ValueError(
                "candidate_path must be non-empty when status is succeeded"
            )
        if self.status == RunStatus.FAILED and self.error is None:
            raise ValueError("error must be provided when status is failed")


@dataclass
class InputArtifactPrecheckSummary:
    """Summary of all input artifact precheck results for a target scene."""

    scene_name: SceneName
    results: list[InputArtifactCheckResult]
    status: RunStatus
    blocking_errors: list[RuntimeErrorRef]
    checked_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.results:
            raise ValueError("results must be non-empty")
        if self.status == RunStatus.SUCCEEDED and self.blocking_errors:
            raise ValueError(
                "status succeeded but blocking_errors is non-empty"
            )
