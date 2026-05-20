from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable

from schemas.runtime_precheck_types import (
    ConfigPrecheckResult,
    ConfigPrecheckRule,
    SceneConfigRequirement,
)
from schemas.runtime_config_types import ConfigSnapshot, EffectiveRuntimeConfig
from schemas.runtime_context import RunContext
from schemas.runtime_enums import RunStatus, SceneName
from schemas.runtime_results import PipelineResult

from .config_prechecker import ConfigPrechecker


class RuntimeInitError(Exception):
    """Raised when Runtime initialization fails."""


class RuntimeInitStep(str, Enum):
    CONFIG_LOAD = "config_load"
    CONFIG_PRECHECK = "config_precheck"
    INPUT_PRECHECK = "input_precheck"
    SERVICE_DISPATCH = "service_dispatch"


InputPrecheckHook = Callable[
    [RunContext, EffectiveRuntimeConfig | None], Any
]


class ConfigPrecheckGate:
    """Orchestration gate that runs config precheck and controls downstream flow.

    The gate decides whether the pipeline should proceed to input precheck
    and Service dispatch based on the ConfigPrecheckResult.
    """

    def __init__(
        self,
        scene_requirements: dict[SceneName, SceneConfigRequirement] | None = None,
        input_precheck_hook: InputPrecheckHook | None = None,
    ) -> None:
        self.scene_requirements = scene_requirements or {}
        self.input_precheck_hook = input_precheck_hook

    def run_precheck(
        self,
        context: RunContext,
        effective_config: EffectiveRuntimeConfig | None,
        config_snapshot: ConfigSnapshot | None,
    ) -> ConfigPrecheckResult:
        checker = ConfigPrechecker(
            scene_requirements=self.scene_requirements,
        )
        return checker.check(context, effective_config, config_snapshot)

    def should_proceed(self, result: ConfigPrecheckResult) -> bool:
        return result.passed


def init_runtime(
    context: RunContext,
    effective_config: EffectiveRuntimeConfig | None,
    config_snapshot: ConfigSnapshot | None,
    gate: ConfigPrecheckGate | None = None,
) -> PipelineResult:
    """Initialize the Runtime pipeline with config precheck as the gating step.

    Args:
        context: The RunContext for this execution.
        effective_config: The effective runtime config from config loading.
        config_snapshot: The config snapshot reference.
        gate: Optional ConfigPrecheckGate with scene requirements and hooks.

    Returns:
        PipelineResult with status SUCCEEDED if precheck passed, FAILED otherwise.
    """
    if gate is None:
        gate = ConfigPrecheckGate()

    precheck_result = gate.run_precheck(
        context, effective_config, config_snapshot
    )

    if gate.should_proceed(precheck_result):
        if gate.input_precheck_hook is not None:
            gate.input_precheck_hook(context, effective_config)

        return PipelineResult(
            run_id=context.run_id,
            status=RunStatus.SUCCEEDED,
            run_dir=context.run_dir,
            scene_results=[],
        )

    return PipelineResult(
        run_id=context.run_id,
        status=RunStatus.FAILED,
        run_dir=context.run_dir,
        scene_results=[],
    )
