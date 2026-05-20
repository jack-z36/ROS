from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from schemas.runtime_context import RunContext
from schemas.runtime_enums import SceneName
from schemas.runtime_config_types import ConfigSnapshot, EffectiveRuntimeConfig
from schemas.runtime_precheck_types import (
    ConfigPrecheckIssue,
    ConfigPrecheckResult,
    ConfigPrecheckRule,
    PRECHECK_RULES,
    SceneConfigRequirement,
)

FULL_PIPELINE_ORDER: list[SceneName] = [
    SceneName.SCENE1,
    SceneName.SCENE2,
    SceneName.SCENE3,
    SceneName.SCENE4,
    SceneName.SCENE5,
]


def _check_effective_config_exists(
    effective_config: EffectiveRuntimeConfig | None,
) -> list[ConfigPrecheckIssue]:
    issues: list[ConfigPrecheckIssue] = []
    if effective_config is None:
        issues.append(
            ConfigPrecheckIssue(
                issue_code="effective_config_missing",
                severity="error",
                message="EffectiveRuntimeConfig is None",
            )
        )
        return issues
    if not isinstance(effective_config.config_data, dict):
        issues.append(
            ConfigPrecheckIssue(
                issue_code="effective_config_not_mapping",
                severity="error",
                message=f"EffectiveRuntimeConfig.config_data is not a mapping, got {type(effective_config.config_data).__name__}",
            )
        )
    return issues


def _check_config_source_traceable(
    effective_config: EffectiveRuntimeConfig,
) -> list[ConfigPrecheckIssue]:
    issues: list[ConfigPrecheckIssue] = []
    source = effective_config.config_source
    if source is None:
        issues.append(
            ConfigPrecheckIssue(
                issue_code="config_source_untraceable",
                severity="error",
                message="RuntimeConfigSource is None",
            )
        )
    elif not source.config_path:
        issues.append(
            ConfigPrecheckIssue(
                issue_code="config_source_untraceable",
                severity="error",
                message="RuntimeConfigSource.config_path is empty",
                config_path=str(source.config_path),
            )
        )
    return issues


def _check_override_set_recorded(
    effective_config: EffectiveRuntimeConfig,
) -> list[ConfigPrecheckIssue]:
    issues: list[ConfigPrecheckIssue] = []
    override_set = effective_config.override_set
    if override_set is None:
        issues.append(
            ConfigPrecheckIssue(
                issue_code="override_set_missing",
                severity="error",
                message="ConfigOverrideSet is None",
            )
        )
    return issues


def _check_snapshot_traceable(
    config_snapshot: ConfigSnapshot | None,
    run_dir: str,
) -> list[ConfigPrecheckIssue]:
    issues: list[ConfigPrecheckIssue] = []
    if config_snapshot is None:
        issues.append(
            ConfigPrecheckIssue(
                issue_code="snapshot_untraceable",
                severity="error",
                message="ConfigSnapshot is None",
            )
        )
        return issues
    snapshot_path = config_snapshot.snapshot_path
    if not snapshot_path:
        issues.append(
            ConfigPrecheckIssue(
                issue_code="snapshot_untraceable",
                severity="error",
                message="ConfigSnapshot.snapshot_path is empty",
            )
        )
        return issues
    if not run_dir:
        issues.append(
            ConfigPrecheckIssue(
                issue_code="snapshot_untraceable",
                severity="error",
                message="RunContext.run_dir is empty, cannot verify snapshot containment",
            )
        )
        return issues
    try:
        snapshot_resolved = Path(str(snapshot_path)).resolve()
        run_dir_resolved = Path(run_dir).resolve()
        snapshot_resolved.relative_to(run_dir_resolved)
    except (ValueError, OSError):
        issues.append(
            ConfigPrecheckIssue(
                issue_code="snapshot_untraceable",
                severity="error",
                message=f"ConfigSnapshot path {snapshot_path} is not inside run_dir {run_dir}",
                config_path=str(snapshot_path),
                details={"run_dir": run_dir, "snapshot_path": str(snapshot_path)},
            )
        )
    return issues


def _check_scene_names_controlled(
    target_scenes: list[SceneName],
) -> list[ConfigPrecheckIssue]:
    issues: list[ConfigPrecheckIssue] = []
    controlled_values = {m.value for m in SceneName}
    for scene in target_scenes:
        scene_val = scene.value if hasattr(scene, "value") else scene
        if scene_val not in controlled_values:
            issues.append(
                ConfigPrecheckIssue(
                    issue_code="unknown_scene_name",
                    severity="error",
                    message=f"Target scene {scene_val!r} is not a controlled SceneName",
                )
            )
    return issues


def _check_scene_sequence(
    target_scenes: list[SceneName],
) -> list[ConfigPrecheckIssue]:
    issues: list[ConfigPrecheckIssue] = []
    if len(target_scenes) > 1:
        expected = [m.value for m in FULL_PIPELINE_ORDER[:len(target_scenes)]]
        actual = [s.value if hasattr(s, "value") else s for s in target_scenes]
        if actual != expected:
            issues.append(
                ConfigPrecheckIssue(
                    issue_code="invalid_scene_sequence",
                    severity="error",
                    message=(
                        f"Invalid scene sequence: got {actual}, "
                        f"expected {expected}"
                    ),
                    details={
                        "actual": actual,
                        "expected": expected,
                    },
                )
            )
    return issues


def _check_scene_config_blocks(
    effective_config: EffectiveRuntimeConfig,
    target_scenes: list[SceneName],
    scene_requirements: dict[SceneName, SceneConfigRequirement] | None,
) -> list[ConfigPrecheckIssue]:
    issues: list[ConfigPrecheckIssue] = []
    config_data = effective_config.config_data or {}

    req_by_key: dict[str, SceneConfigRequirement] = {}
    if scene_requirements:
        for s, r in scene_requirements.items():
            key = s.value if hasattr(s, "value") else s
            req_by_key[key] = r

    for scene in target_scenes:
        scene_key = scene.value if hasattr(scene, "value") else scene
        has_scene_block = scene_key in config_data

        if not has_scene_block:
            issues.append(
                ConfigPrecheckIssue(
                    issue_code="missing_scene_config",
                    severity="error",
                    message=f"Missing runtime-level config block for scene {scene_key!r}",
                    scene_name=scene if hasattr(scene, "value") else None,
                    config_path=scene_key,
                )
            )
            continue

        if scene_key in req_by_key:
            req = req_by_key[scene_key]
            for section in req.required_sections:
                if section not in config_data.get(scene_key, {}):
                    issues.append(
                        ConfigPrecheckIssue(
                            issue_code="missing_scene_config",
                            severity="error",
                            message=(
                                f"Scene {scene_key!r} missing required section "
                                f"{section!r}"
                            ),
                            scene_name=scene,
                            config_path=f"{scene_key}.{section}",
                        )
                    )
            for field in req.required_fields:
                parts = field.split(".")
                current = config_data.get(scene_key, {})
                found = True
                for part in parts:
                    if isinstance(current, dict) and part in current:
                        current = current[part]
                    else:
                        found = False
                        break
                if not found:
                    issues.append(
                        ConfigPrecheckIssue(
                            issue_code="missing_scene_config",
                            severity="error",
                            message=(
                                f"Scene {scene_key!r} missing required field "
                                f"{field!r}"
                            ),
                            scene_name=scene,
                            config_path=f"{scene_key}.{field}",
                        )
                    )

    return issues


def _add_service_not_checked_warning(
    target_scenes: list[SceneName],
) -> list[ConfigPrecheckIssue]:
    if target_scenes:
        return [
            ConfigPrecheckIssue(
                issue_code="service_business_config_not_checked",
                severity="warning",
                message="Runtime-level precheck does not verify Service business parameters",
            )
        ]
    return []


def _check_global_runtime_config(
    effective_config: EffectiveRuntimeConfig,
) -> list[ConfigPrecheckIssue]:
    issues: list[ConfigPrecheckIssue] = []
    config_data = effective_config.config_data or {}
    if not isinstance(config_data, dict):
        return issues
    global_keys = {"batch", "pose_streams", "gripper_streams"}
    for key in global_keys:
        if key not in config_data:
            issues.append(
                ConfigPrecheckIssue(
                    issue_code="missing_global_runtime_config",
                    severity="error",
                    message=f"Missing global runtime config key: {key!r}",
                    config_path=key,
                )
            )
    return issues


class ConfigPrechecker:
    def __init__(
        self,
        scene_requirements: dict[SceneName, SceneConfigRequirement] | None = None,
    ) -> None:
        self._scene_requirements = scene_requirements or {}

    def check(
        self,
        context: RunContext,
        effective_config: EffectiveRuntimeConfig | None,
        config_snapshot: ConfigSnapshot | None,
    ) -> ConfigPrecheckResult:
        all_issues: list[ConfigPrecheckIssue] = []
        checked_rules: list[str] = [r.rule_id for r in PRECHECK_RULES]

        target_scenes: list[SceneName] = list(context.target_scenes or [])

        all_issues.extend(
            _check_effective_config_exists(effective_config)
        )

        if effective_config is not None:
            all_issues.extend(
                _check_config_source_traceable(effective_config)
            )
            all_issues.extend(
                _check_override_set_recorded(effective_config)
            )
            all_issues.extend(
                _check_global_runtime_config(effective_config)
            )
            all_issues.extend(
                _check_scene_config_blocks(
                    effective_config, target_scenes, self._scene_requirements
                )
            )

        all_issues.extend(
            _check_snapshot_traceable(config_snapshot, context.run_dir)
        )
        all_issues.extend(
            _check_scene_names_controlled(target_scenes)
        )
        all_issues.extend(
            _check_scene_sequence(target_scenes)
        )

        warning_issues = _add_service_not_checked_warning(target_scenes)
        all_issues.extend(warning_issues)

        has_blocking = any(
            iss.severity == "error"
            for iss in all_issues
        )

        return ConfigPrecheckResult(
            passed=not has_blocking,
            checked_scenes=target_scenes,
            issues=all_issues,
            checked_rules=checked_rules,
            effective_config_ref=effective_config,
            config_snapshot_ref=config_snapshot,
            created_at=datetime.now(),
        )
