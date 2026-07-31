# runtime package
#
# UI facade for L2-06 ControlLoop runtime objects. Only stable public symbols
# are re-exported here. The pre-existing ``observation_buffer`` submodule
# (L2-02) remains importable as ``model_deploy.act.runtime.observation_buffer``;
# it is intentionally NOT re-exported from this facade to avoid shadowing or
# pulling L2-02 internals into the L2-06 public surface.

from model_deploy.act.runtime.control_loop import (  # noqa: F401
    ControlLoop,
    ControlLoopConfig,
    FallbackReason,
    FallbackSelection,
    FALLBACK_MATRIX,
    CandidateSelection,
    build_inference_request,
    is_action_chunk_usable,
    select_candidate,
    select_fallback,
)
from model_deploy.act.runtime.inference_channel import (
    InferenceRequest,
    InferenceResult,
    LatestQueue,
)
from model_deploy.act.runtime.inference_worker import (  # noqa: F401
    InferenceWorker,
)
from model_deploy.act.runtime.runtime_metrics import (
    RuntimeMetrics,
    RuntimeMetricsSnapshot,
)
from model_deploy.act.runtime.action_response_verifier import (
    ActionResponseVerifier,
    ResponseCheck,
    ResponseState,
)

__all__ = [
    "ControlLoop",
    "ControlLoopConfig",
    "FallbackReason",
    "FallbackSelection",
    "FALLBACK_MATRIX",
    "CandidateSelection",
    "build_inference_request",
    "is_action_chunk_usable",
    "select_candidate",
    "select_fallback",
    "InferenceRequest",
    "InferenceResult",
    "LatestQueue",
    "RuntimeMetrics",
    "RuntimeMetricsSnapshot",
    "InferenceWorker",
    "ActionResponseVerifier",
    "ResponseCheck",
    "ResponseState",
]
from .command_permit_provider import (
    CommandPermitProvider,
    HardwareGateSample,
    PermitState,
)

__all__ = [
    "CommandPermitProvider",
    "HardwareGateSample",
    "PermitState",
]
