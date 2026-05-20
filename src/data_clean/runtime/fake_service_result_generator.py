"""Fake service result generator for Runtime MVP."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

from data_clean.schemas.fake_service_types import FakeServicePlan, FakeServiceResult
from data_clean.schemas.runtime_enums import FakeServiceBehavior, RunStatus
from data_clean.schemas.runtime_results import RuntimeErrorRef
from data_clean.schemas.run_directory_types import RunDirectory


@dataclass
class FakeServiceExecutionError(Exception):
    """Error raised when fake service execution fails."""

    error_code: str
    message: str
    scene_name: str | None = None

    def __str__(self) -> str:
        return f"{self.error_code}: {self.message}"


def generate_fake_service_result(
    plan: FakeServicePlan,
    run_dir: RunDirectory,
) -> FakeServiceResult:
    """Generate a FakeServiceResult based on the FakeServicePlan.

    Args:
        plan: The fake service execution plan.
        run_dir: The run directory for output path validation.

    Returns:
        A FakeServiceResult representing the fake service execution.

    Raises:
        FakeServiceExecutionError: If the execution fails due to invalid inputs
            or boundary conditions.
    """
    # Validate service mode
    if plan.service_mode.value != "fake":
        raise FakeServiceExecutionError(
            error_code="fake_service_mode_mismatch",
            message=f"service_mode must be 'fake', got '{plan.service_mode.value}'",
            scene_name=plan.scene_name.value,
        )

    # Validate output paths don't escape run directory
    _validate_output_paths(plan.declared_outputs, run_dir)

    # Record start time
    started_at = datetime.now()

    # Determine result based on behavior
    behavior = plan.behavior

    if behavior == FakeServiceBehavior.SUCCESS:
        status = RunStatus.SUCCEEDED
        error = None
    elif behavior == FakeServiceBehavior.CONTROLLED_FAILURE:
        status = RunStatus.FAILED
        error = RuntimeErrorRef(
            error_code="fake_service_controlled_failure",
            step_name="fake_service",
            message="Fake service controlled failure for testing error summary chain",
            scene_name=plan.scene_name,
            details={"behavior": behavior.value},
        )
    elif behavior == FakeServiceBehavior.SKIPPED:
        # Skipped is not an error, but not success either
        # We'll mark it as failed since it didn't execute
        status = RunStatus.FAILED
        error = RuntimeErrorRef(
            error_code="fake_service_skipped",
            step_name="fake_service",
            message="Fake service was skipped",
            scene_name=plan.scene_name,
            details={"behavior": behavior.value},
        )
    else:
        # Unexpected behavior
        raise FakeServiceExecutionError(
            error_code="fake_service_invalid_behavior",
            message=f"Invalid behavior: {behavior}",
            scene_name=plan.scene_name.value,
        )

    # Record end time and calculate duration
    finished_at = datetime.now()
    duration_ms = int((finished_at - started_at).total_seconds() * 1000)

    # If duration is 0 (too fast), add minimum 1ms
    if duration_ms == 0:
        duration_ms = 1

    return FakeServiceResult(
        scene_name=plan.scene_name,
        behavior=behavior,
        status=status,
        output_paths=plan.declared_outputs,
        started_at=started_at,
        finished_at=finished_at,
        duration_ms=duration_ms,
        input_summary=plan.input_summary,
        error=error,
    )


def _validate_output_paths(
    declared_outputs: dict[str, str],
    run_dir: RunDirectory,
) -> None:
    """Validate that output paths don't escape the run directory.

    Args:
        declared_outputs: The declared output paths.
        run_dir: The run directory to validate against.

    Raises:
        FakeServiceExecutionError: If any output path escapes the run directory.
    """
    run_dir_path = run_dir.run_dir.resolve()

    for name, path_str in declared_outputs.items():
        if not path_str:
            continue

        # Convert to Path and resolve
        output_path = Path(path_str)

        # If it's an absolute path, check if it's within run directory
        if output_path.is_absolute():
            try:
                output_path.resolve().relative_to(run_dir_path)
            except ValueError:
                raise FakeServiceExecutionError(
                    error_code="fake_output_path_escape",
                    message=f"Output path '{path_str}' escapes run directory '{run_dir_path}'",
                    scene_name=None,
                )
        # For relative paths, we assume they're relative to the run directory
        # This is acceptable since they stay within the run directory structure
