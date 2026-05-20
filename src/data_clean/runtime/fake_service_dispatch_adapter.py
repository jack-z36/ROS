"""Fake service dispatch adapter for Runtime MVP.

This module provides the FakeServiceDispatchAdapter which acts as a binding
between the service dispatch layer and the fake service executor.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from data_clean.schemas.fake_service_types import FakeServicePlan, FakeServiceResult
from data_clean.schemas.runtime_dispatch_types import ServiceBinding
from data_clean.schemas.runtime_enums import (
    FakeServiceBehavior,
    RunStatus,
    ServiceMode,
)
from data_clean.schemas.runtime_results import RuntimeErrorRef, SceneResult


def _now() -> datetime:
    return datetime.now(tz=timezone.utc)


class FakeServiceDispatchAdapter:
    """Adapter that wraps fake service execution for dispatch layer integration.

    This adapter acts as a callable that can be bound to a ServiceBinding
    and produces SceneResult from FakeServicePlan.
    """

    def invoke(
        self,
        plan: FakeServicePlan,
    ) -> SceneResult:
        """Invoke fake service and convert result to SceneResult.

        Args:
            plan: The fake service execution plan.

        Returns:
            SceneResult derived from the fake service execution.
        """
        started_at = _now()

        # Execute based on behavior
        if plan.behavior == FakeServiceBehavior.SUCCESS:
            finished_at = _now()
            duration_ms = max(
                int((finished_at - started_at).total_seconds() * 1000), 100
            )

            return SceneResult(
                scene_name=plan.scene_name,
                status=RunStatus.SUCCEEDED,
                input_paths={},
                output_paths=plan.declared_outputs,
                started_at=started_at,
                finished_at=finished_at,
                duration_ms=duration_ms,
                error=None,
            )

        elif plan.behavior == FakeServiceBehavior.CONTROLLED_FAILURE:
            finished_at = _now()
            duration_ms = max(
                int((finished_at - started_at).total_seconds() * 1000), 50
            )

            error = RuntimeErrorRef(
                error_code="fake_service_controlled_failure",
                step_name="fake_service",
                message=plan.message or "Simulated controlled failure",
                scene_name=plan.scene_name,
            )

            return SceneResult(
                scene_name=plan.scene_name,
                status=RunStatus.FAILED,
                input_paths={},
                output_paths={},
                started_at=started_at,
                finished_at=finished_at,
                duration_ms=duration_ms,
                error=error,
            )

        elif plan.behavior == FakeServiceBehavior.SKIPPED:
            finished_at = _now()

            return SceneResult(
                scene_name=plan.scene_name,
                status=RunStatus.CANCELLED,
                input_paths={},
                output_paths={},
                started_at=started_at,
                finished_at=finished_at,
                duration_ms=0,
                error=None,
            )

        else:
            # Unknown behavior - treat as failure
            error = RuntimeErrorRef(
                error_code="fake_service_unknown_behavior",
                step_name="fake_service",
                message=f"Unknown behavior: {plan.behavior}",
                scene_name=plan.scene_name,
            )

            finished_at = _now()
            return SceneResult(
                scene_name=plan.scene_name,
                status=RunStatus.FAILED,
                input_paths={},
                output_paths={},
                started_at=started_at,
                finished_at=finished_at,
                duration_ms=0,
                error=error,
            )

    def __call__(self, plan: FakeServicePlan) -> SceneResult:
        """Make adapter callable for ServiceBinding integration."""
        return self.invoke(plan)


# Convenience function for simple usage
def dispatch_fake_service(
    plan: FakeServicePlan,
) -> SceneResult:
    """Dispatch a fake service and return SceneResult.

    Args:
        plan: The fake service execution plan.

    Returns:
        SceneResult from the fake service execution.
    """
    adapter = FakeServiceDispatchAdapter()
    return adapter.invoke(plan)