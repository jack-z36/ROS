"""Input artifact prechecker — checks existence, readability, and kind of artifact paths."""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from schemas.runtime_config_types import EffectiveRuntimeConfig

from schemas.input_artifact_types import (
    InputArtifactCheckResult,
    InputArtifactPrecheckSummary,
    InputArtifactRequirement,
)
from schemas.runtime_enums import RunStatus
from schemas.runtime_results import RuntimeErrorRef

INPUT_PRECHECK_STEP = "input_artifact_precheck"


def _lookup_path(config_data: dict, path_config_key: str) -> str | None:
    val = config_data.get(path_config_key)
    if isinstance(val, str) and val:
        return val
    if "." in path_config_key:
        parts = path_config_key.split(".", 1)
        nested = config_data.get(parts[0])
        if isinstance(nested, dict):
            val = nested.get(parts[1])
            if isinstance(val, str) and val:
                return val
    return None


def _check_single_artifact(
    requirement: InputArtifactRequirement,
    effective_config: EffectiveRuntimeConfig,
) -> InputArtifactCheckResult:
    candidate_path = _lookup_path(
        effective_config.config_data, requirement.path_config_key
    )
    if candidate_path is None:
        return InputArtifactCheckResult(
            requirement=requirement,
            status=RunStatus.FAILED,
            exists=False,
            readable=False,
            kind_matches=False,
            error=RuntimeErrorRef(
                error_code="input_path_missing_in_config",
                step_name=INPUT_PRECHECK_STEP,
                message=(
                    f"Config key {requirement.path_config_key!r} missing or empty "
                    f"for {requirement.artifact_role!r}"
                ),
                scene_name=requirement.scene_name,
            ),
        )

    path = Path(candidate_path)
    if not path.exists():
        return InputArtifactCheckResult(
            requirement=requirement,
            status=RunStatus.FAILED,
            exists=False,
            readable=False,
            kind_matches=False,
            candidate_path=candidate_path,
            error=RuntimeErrorRef(
                error_code="input_artifact_not_found",
                step_name=INPUT_PRECHECK_STEP,
                message=f"Input artifact not found: {candidate_path}",
                scene_name=requirement.scene_name,
            ),
        )

    if not os.access(path, os.R_OK):
        return InputArtifactCheckResult(
            requirement=requirement,
            status=RunStatus.FAILED,
            exists=True,
            readable=False,
            kind_matches=False,
            candidate_path=candidate_path,
            error=RuntimeErrorRef(
                error_code="input_artifact_not_readable",
                step_name=INPUT_PRECHECK_STEP,
                message=f"Input artifact not readable: {candidate_path}",
                scene_name=requirement.scene_name,
            ),
        )

    is_file = path.is_file()
    is_dir = path.is_dir()
    expected_kind = requirement.required_kind
    kind_matches = (expected_kind == "file" and is_file) or (
        expected_kind == "directory" and is_dir
    )

    if not kind_matches:
        actual = "file" if is_file else "directory" if is_dir else "unknown"
        return InputArtifactCheckResult(
            requirement=requirement,
            status=RunStatus.FAILED,
            exists=True,
            readable=True,
            kind_matches=False,
            candidate_path=candidate_path,
            error=RuntimeErrorRef(
                error_code="input_artifact_kind_mismatch",
                step_name=INPUT_PRECHECK_STEP,
                message=(
                    f"Expected {expected_kind} but got {actual}: {candidate_path}"
                ),
                scene_name=requirement.scene_name,
            ),
        )

    return InputArtifactCheckResult(
        requirement=requirement,
        status=RunStatus.SUCCEEDED,
        exists=True,
        readable=True,
        kind_matches=True,
        candidate_path=candidate_path,
    )


def precheck_input_artifacts(
    requirements: list[InputArtifactRequirement],
    effective_config: EffectiveRuntimeConfig,
) -> InputArtifactPrecheckSummary:
    """Check all input artifact requirements and return a structured summary.

    Args:
        requirements: List of input artifact requirements to check.
        effective_config: The effective runtime config containing path data.

    Returns:
        InputArtifactPrecheckSummary with per-requirement results.

    Raises:
        ValueError: If requirements list is empty.
    """
    if not requirements:
        raise ValueError("requirements must be non-empty")

    results = [_check_single_artifact(req, effective_config) for req in requirements]

    scene_name = results[0].requirement.scene_name
    all_succeeded = all(r.status == RunStatus.SUCCEEDED for r in results)
    blocking_errors = [r.error for r in results if r.error is not None]

    return InputArtifactPrecheckSummary(
        scene_name=scene_name,
        results=results,
        status=RunStatus.SUCCEEDED if all_succeeded else RunStatus.FAILED,
        blocking_errors=blocking_errors,
    )
