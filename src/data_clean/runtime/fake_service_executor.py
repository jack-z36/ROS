"""Fake service executor for generating controlled results.

This module provides the FakeServiceExecutor class which generates
FakeServiceResult from FakeServicePlan based on controlled behavior.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from data_clean.schemas.fake_service_types import FakeServicePlan, FakeServiceResult
from data_clean.schemas.runtime_enums import (
    FakeServiceBehavior,
    RunStatus,
    ServiceMode,
)
from data_clean.schemas.runtime_results import RuntimeErrorRef


def _now() -> datetime:
    return datetime.now(tz=timezone.utc)


class FakeServiceExecutorError(Exception):
    """Raised when fake service execution fails."""

    def __init__(self, error_code: str, message: str) -> None:
        self.error_code = error_code
        self.message = message
        super().__init__(f"{error_code}: {message}")


class FakeServiceExecutor:
    """Executor that generates FakeServiceResult from FakeServicePlan.

    This executor provides controlled fake service behavior for Runtime MVP
    testing, supporting success, controlled failure, and skipped scenarios.
    """

    def execute(
        self,
        plan: FakeServicePlan,
        run_dir: Path | None = None,
    ) -> FakeServiceResult:
        """Execute a fake service based on the plan.

        Args:
            plan: The fake service execution plan.
            run_dir: Optional run directory for output path validation.

        Returns:
            FakeServiceResult based on plan's behavior.

        Raises:
            FakeServiceExecutorError: If validation fails.
        """
        # Validate service mode - this is also done at plan creation,
        # but we check here for explicit error handling
        if plan.service_mode != ServiceMode.FAKE:
            raise FakeServiceExecutorError(
                error_code="fake_service_mode_mismatch",
                message=f"service_mode must be FAKE, got {plan.service_mode.value!r}",
            )

        # Validate scene_name exists
        if plan.scene_name is None:
            raise FakeServiceExecutorError(
                error_code="fake_service_scene_missing",
                message="scene_name is required",
            )

        # Validate output paths don't escape run_dir
        if run_dir is not None and plan.declared_outputs:
            run_dir_resolved = run_dir.resolve()
            for name, path_str in plan.declared_outputs.items():
                path = Path(path_str).resolve()
                try:
                    path.relative_to(run_dir_resolved)
                except ValueError:
                    raise FakeServiceExecutorError(
                        error_code="fake_output_path_escape",
                        message=f"output path escapes run_dir: {path_str}",
                    )

        started_at = _now()

        # Generate result based on behavior
        if plan.behavior == FakeServiceBehavior.SUCCESS:
            return self._create_success_result(plan, started_at)
        elif plan.behavior == FakeServiceBehavior.CONTROLLED_FAILURE:
            return self._create_failure_result(plan, started_at)
        elif plan.behavior == FakeServiceBehavior.SKIPPED:
            return self._create_skipped_result(plan, started_at)
        else:
            raise FakeServiceExecutorError(
                error_code="fake_service_unknown_behavior",
                message=f"Unknown behavior: {plan.behavior}",
            )

    def _create_success_result(
        self,
        plan: FakeServicePlan,
        started_at: datetime,
    ) -> FakeServiceResult:
        """Create a success result."""
        finished_at = _now()
        duration_ms = int((finished_at - started_at).total_seconds() * 1000)
        # Ensure minimum duration for realistic timing
        if duration_ms < 1:
            duration_ms = 100

        return FakeServiceResult(
            scene_name=plan.scene_name,
            behavior=plan.behavior,
            status=RunStatus.SUCCEEDED,
            output_paths=plan.declared_outputs,
            started_at=started_at,
            finished_at=finished_at,
            duration_ms=duration_ms,
            input_summary=plan.input_summary,
            error=None,
        )

    def _create_failure_result(
        self,
        plan: FakeServicePlan,
        started_at: datetime,
    ) -> FakeServiceResult:
        """Create a controlled failure result."""
        finished_at = _now()
        duration_ms = int((finished_at - started_at).total_seconds() * 1000)
        if duration_ms < 1:
            duration_ms = 50

        error = RuntimeErrorRef(
            error_code="fake_service_controlled_failure",
            step_name="fake_service",
            message=plan.message or "Simulated controlled failure",
            scene_name=plan.scene_name,
        )

        return FakeServiceResult(
            scene_name=plan.scene_name,
            behavior=plan.behavior,
            status=RunStatus.FAILED,
            output_paths={},
            started_at=started_at,
            finished_at=finished_at,
            duration_ms=duration_ms,
            input_summary=plan.input_summary,
            error=error,
        )

    def _create_skipped_result(
        self,
        plan: FakeServicePlan,
        started_at: datetime,
    ) -> FakeServiceResult:
        """Create a skipped result."""
        finished_at = _now()

        return FakeServiceResult(
            scene_name=plan.scene_name,
            behavior=plan.behavior,
            status=RunStatus.CANCELLED,
            output_paths={},
            started_at=started_at,
            finished_at=finished_at,
            duration_ms=0,
            input_summary=plan.input_summary,
            error=None,
        )


# Convenience function for simple usage
def execute_fake_service(
    plan: FakeServicePlan,
    run_dir: Path | None = None,
) -> FakeServiceResult:
    """Execute a fake service and return the result.

    Args:
        plan: The fake service execution plan.
        run_dir: Optional run directory for output path validation.

    Returns:
        FakeServiceResult based on plan's behavior.
    """
    executor = FakeServiceExecutor()
    return executor.execute(plan, run_dir)
