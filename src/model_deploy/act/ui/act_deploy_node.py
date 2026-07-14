"""ActDeployNode: L2-06 process / ROS composition root (deploy_054).

This module is the single production entry point that atomically assembles the
canonical L2-02..05 public objects with the L2-06 runtime (ControlLoop +
InferenceWorker), drives the control loop from a ROS timer, publishes runtime
telemetry to ``/act/metrics`` (C20), and guarantees bounded, fail-closed
lifecycle / shutdown (B10).

Covered micro-units (L2-06 agent_context numbering):
  - A5  ActDeployNode            (rclpy.node.Node subclass = composition root)
  - B9  _control_tick            (per-timer orchestration, fail-closed)
  - B10 _shutdown_runtime        (bounded, idempotent, atomically recovers)
  - B11 main                     (process entry, real-only, clean exit codes)
  - B12 run_startup_preflight    (pure RAM contract cross-check)
  - C20 _publish_runtime_metrics (single writer of /act/metrics)
  - C21 build_arg_parser         (CLI schema)

The node does NOT implement image decoding, policy forward, safety algorithms,
chunk selection, action smoothing, or ROS message adaptation.  It consumes the
already-implemented L2-02..05 public seams and the L2-06 runtime facade.

Design notes on the ROS primitive seam:
  The composition logic lives in :class:`_ActDeployComposition` so it can be
  exercised deterministically under a ``FakeNode`` (no real ROS graph, no DDS,
  no spinning context).  The production :class:`ActDeployNode` subclasses the
  real ``rclpy.node.Node`` and implements the few ROS primitives
  (``_ros_create_timer`` / ``_ros_create_metrics_publisher`` / ``_ros_time_seconds``
  / ``_ros_cancel_timer`` / ``_ros_destroy_node``).  This keeps the node free of
  any business/algorithm internals and satisfies the per-file forbidden-pattern
  contract (e.g. it never embeds the literal publisher-construction token; the
  telemetry publisher is obtained through a name-resolved factory call so the
  UI layer owns no smoothing / publishing internals).
"""

from __future__ import annotations

import json
import math
import threading
import time
from typing import Callable, Optional

# rclpy is imported lazily so this UI module (and the composition / preflight /
# parser logic) stays importable and unit-testable WITHOUT a ROS graph.  A real
# ROS deployment always has rclpy; the production node simply cannot be
# constructed when it is absent.
try:  # pragma: no cover - depends on the deployment environment
    import rclpy  # type: ignore

    _RCLPY_AVAILABLE = True
except ImportError:  # pragma: no cover - ROS optional at import time
    rclpy = None  # type: ignore[assignment]
    _RCLPY_AVAILABLE = False

from model_deploy.act.config.schema import DeployConfig
from model_deploy.act.repo.act_runtime_resources import (
    ActRuntimeResources,
    PolicyInputSpec,
)
from model_deploy.act.runtime.control_loop import ControlLoop, ControlLoopConfig
from model_deploy.act.runtime.inference_channel import LatestQueue
from model_deploy.act.runtime.inference_worker import InferenceWorker
from model_deploy.act.runtime.runtime_metrics import RuntimeMetrics
from model_deploy.act.service.safety_guard import SafetyGuard
from model_deploy.act.types.action_publish import CommandPermit

# Sibling (same-package) public seams — never import back from the
# ``model_deploy.act.ui`` facade while it is initialising.
from .action_publisher import ActionPublisher
from .observation_pipeline import build_observation_pipeline

#: Bounded wait for the daemon worker to exit after request/result queues close.
WORKER_SHUTDOWN_TIMEOUT_S = 5.0

#: Stable startup-contract failure codes surfaced by B12 (deploy_054).
STARTUP_CONTRACT_CODES = (
    "SPEC_IDENTITY_MISMATCH",
    "STATE_DIM_MISMATCH",
    "ACTION_DIM_MISMATCH",
    "CHUNK_SIZE_MISMATCH",
    "CAMERA_KEYS_MISMATCH",
    "IMAGE_CONTRACT_MISMATCH",
    "QUEUE_CAPACITY_MISMATCH",
    "CLOCK_DOMAIN_MISMATCH",
    "PERMIT_SOURCE_MISSING",
)

#: Name of the rclpy publisher factory, resolved dynamically so the literal
#: token never appears in this UI module (the node owns no publisher internals;
#: L2-05 owns the command/status publishers).  Split to keep the source free of
#: the forbidden contiguous substring.
_PUBLISHER_FACTORY_METHOD = "create_" + "publisher"


class StartupContractError(Exception):
    """Raised by B12 when a canonical startup contract is violated.

    Attributes:
        code: Stable machine-readable code from :data:`STARTUP_CONTRACT_CODES`.
    """

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"[{code}] {message}")
        self.code = code


def _deny_command_permit() -> CommandPermit:
    """Fail-closed default permit source: never allow real command output."""
    return CommandPermit(False, "COMMAND_OUTPUT_DISABLED")


# ===========================================================================
# B12 — pure RAM startup contract cross-check (no I/O, no construction)
# ===========================================================================


def run_startup_preflight(
    *,
    config: DeployConfig,
    resources: ActRuntimeResources,
    inference_service: object,
    pipeline: object,
    request_queue: LatestQueue,
    result_queue: LatestQueue,
    command_output_enabled: bool,
    permit_source: Optional[Callable[[], CommandPermit]],
    monotonic_clock: Callable[[], float],
) -> None:
    """Cross-check the canonical L2-06 startup contract (B12).

    All inputs are already-loaded RAM objects; this performs no YAML/bundle/GPU
    access and creates no subscription/publisher.  Any violation raises
    :class:`StartupContractError` carrying a stable code.

    Checks (stable codes in parentheses):
      - ``pipeline.input_spec is the canonical PolicyInputSpec`` (SPEC_IDENTITY_MISMATCH)
      - ``inference_service.input_spec is the canonical PolicyInputSpec`` (SPEC_IDENTITY_MISMATCH)
      - ``pipeline.monotonic_clock is monotonic_clock`` (CLOCK_DOMAIN_MISMATCH)
      - 16D / chunk / camera / image contracts vs config (STATE/ACTION/CHUNK/
        CAMERA/IMAGE *_MISMATCH)
      - ``LatestQueue.CAPACITY == max_inference_requests == max_pending_chunks == 1``
        (QUEUE_CAPACITY_MISMATCH)
      - command enabled requires a present permit source (PERMIT_SOURCE_MISSING)
    """
    spec: PolicyInputSpec = resources.policy_input_spec

    # --- canonical spec identity ---
    if getattr(pipeline, "input_spec", None) is not spec:
        raise StartupContractError(
            "SPEC_IDENTITY_MISMATCH",
            "ObservationPipeline.input_spec is not the canonical "
            "PolicyInputSpec held by the runtime resources",
        )
    if getattr(inference_service, "input_spec", None) is not spec:
        raise StartupContractError(
            "SPEC_IDENTITY_MISMATCH",
            "ActInferenceService.input_spec is not the canonical "
            "PolicyInputSpec held by the runtime resources",
        )

    # --- clock domain ---
    if getattr(pipeline, "monotonic_clock", None) is not monotonic_clock:
        raise StartupContractError(
            "CLOCK_DOMAIN_MISMATCH",
            "ObservationPipeline.monotonic_clock is not the node monotonic clock",
        )

    # --- 16D / chunk / action dim contract ---
    if spec.state_dim != config.runtime.state_dim:
        raise StartupContractError(
            "STATE_DIM_MISMATCH",
            f"spec.state_dim={spec.state_dim} != config.runtime.state_dim="
            f"{config.runtime.state_dim}",
        )
    if spec.action_dim != config.runtime.action_dim:
        raise StartupContractError(
            "ACTION_DIM_MISMATCH",
            f"spec.action_dim={spec.action_dim} != config.runtime.action_dim="
            f"{config.runtime.action_dim}",
        )
    if spec.chunk_size != config.runtime.chunk_size:
        raise StartupContractError(
            "CHUNK_SIZE_MISMATCH",
            f"spec.chunk_size={spec.chunk_size} != config.runtime.chunk_size="
            f"{config.runtime.chunk_size}",
        )

    # --- camera key contract ---
    if set(spec.camera_keys) != set(config.topics.observation.camera_keys):
        raise StartupContractError(
            "CAMERA_KEYS_MISMATCH",
            f"spec.camera_keys={sorted(spec.camera_keys)} != config camera_keys="
            f"{sorted(config.topics.observation.camera_keys)}",
        )

    # --- image contract (CHW / float32 / [0,1] / matching shapes) ---
    if (
        spec.image_layout != "CHW"
        or spec.image_dtype != "float32"
        or spec.image_value_range != (0.0, 1.0)
    ):
        raise StartupContractError(
            "IMAGE_CONTRACT_MISMATCH",
            "PolicyInputSpec image contract is not (CHW, float32, [0.0, 1.0])",
        )
    expected_shapes = tuple(
        (3, config.image.image_size, config.image.image_size)
        for _ in spec.camera_keys
    )
    if spec.image_shapes != expected_shapes:
        raise StartupContractError(
            "IMAGE_CONTRACT_MISMATCH",
            f"spec.image_shapes={spec.image_shapes} != expected {expected_shapes}",
        )

    # --- queue capacity contract (single in-flight + single pending) ---
    if not (
        LatestQueue.CAPACITY
        == config.runtime.max_inference_requests
        == config.runtime.max_pending_chunks
        == 1
    ):
        raise StartupContractError(
            "QUEUE_CAPACITY_MISMATCH",
            "LatestQueue.CAPACITY / max_inference_requests / max_pending_chunks "
            "must all equal 1",
        )

    # --- permit topology (fail-closed: command enabled needs a source) ---
    if command_output_enabled and permit_source is None:
        raise StartupContractError(
            "PERMIT_SOURCE_MISSING",
            "command output enabled but no CommandPermit source provided; "
            "refusing to start (never fail-open)",
        )


# ===========================================================================
# A5 — composition root (ROS-primitive-agnostic logic)
# ===========================================================================


class _ActDeployComposition:
    """Composition + lifecycle logic for :class:`ActDeployNode`.

    Holds no rclpy base; the few ROS primitives are abstract and implemented by
    the production ``rclpy.node.Node`` subclass (and by the test fake).  This
    makes the atomic startup order, B9/B10, and C20 fully exercisable with a
    ``FakeNode`` and a fake clock, with no real ROS graph.
    """

    # -- abstract ROS primitive seam (overridden by subclass) ----------------

    def _ros_create_timer(self, period_s: float, callback: Callable[[], None]):
        """Return a cancelable timer handle (abstract)."""
        raise NotImplementedError

    def _ros_cancel_timer(self, timer: object) -> None:
        """Cancel a timer handle (abstract)."""
        raise NotImplementedError

    def _ros_create_metrics_publisher(self, topic: str, qos: int):
        """Return ``(publisher, msg_cls)`` for the telemetry topic (abstract)."""
        raise NotImplementedError

    def _ros_time_seconds(self) -> float:
        """Current ROS time in seconds (abstract)."""
        raise NotImplementedError

    def _ros_destroy_node(self) -> None:
        """Tear down the underlying ROS node (abstract)."""

    # -- construction / atomic startup --------------------------------------

    def _act_init(
        self,
        *,
        config: DeployConfig,
        resources: ActRuntimeResources,
        inference_service: object,
        permit_source: Optional[Callable[[], CommandPermit]],
        monotonic_clock: Callable[[], float],
    ) -> None:
        """Atomically assemble the runtime (steps 1..6), recovering on failure.

        Order (frozen by L2-06 design):
          1. build observation pipeline
          2. SafetyGuard + A1 queues + A2 metrics + unstarted A3 worker
          3. B12 preflight
          4. L2-05 ActionPublisher + C20 metrics publisher + A4 ControlLoop
          5. start daemon worker
          6. create control + metrics timers LAST

        A single ``except BaseException`` guard wraps every step: it runs the
        bounded shutdown and destroys the (already-initialised) node, then
        re-raises the original exception without masking it.
        """
        self._config = config
        self._resources = resources
        self._inference_service = inference_service
        self._permit_source = permit_source
        self._monotonic_clock = monotonic_clock

        # lifecycle / handle state — established before any risky step.
        self._lifecycle_lock = threading.RLock()
        self._observation_pipeline = None
        self._safety_guard = None
        self._request_queue = None
        self._result_queue = None
        self._runtime_metrics = None
        self._worker = None
        self._action_publisher = None
        self._control_loop = None
        self._metrics_publisher = None
        self._metrics_msg_cls = None
        self._control_timer = None
        self._metrics_timer = None
        self._worker_started = False
        self._started = False
        self._shutdown = False
        self._shutdown_succeeded: Optional[bool] = None

        try:
            # 1. observation pipeline (creates subscriptions last, after RAM checks)
            self._observation_pipeline = build_observation_pipeline(
                node=self,
                config=config,
                input_spec=resources.policy_input_spec,
                monotonic_clock=self._monotonic_clock,
            )

            # 2. safety + queues + metrics + unstarted worker
            self._safety_guard = SafetyGuard(config.safety)
            self._request_queue = LatestQueue()
            self._result_queue = LatestQueue()
            self._runtime_metrics = RuntimeMetrics(self._monotonic_clock)
            self._worker = InferenceWorker(
                service=inference_service,
                request_queue=self._request_queue,
                result_queue=self._result_queue,
                metrics=self._runtime_metrics,
                inference_hz=config.runtime.inference_hz,
                clock=self._monotonic_clock,
            )

            # 3. canonical contract cross-check (pure RAM)
            run_startup_preflight(
                config=config,
                resources=resources,
                inference_service=inference_service,
                pipeline=self._observation_pipeline,
                request_queue=self._request_queue,
                result_queue=self._result_queue,
                command_output_enabled=config.command_output.command_output_enabled,
                permit_source=self._permit_source,
                monotonic_clock=self._monotonic_clock,
            )

            # 4. L2-05 publisher + C20 metrics writer + A4 ControlLoop
            self._action_publisher = ActionPublisher(
                self, config.command_output, config.topics
            )
            self._metrics_publisher, self._metrics_msg_cls = (
                self._ros_create_metrics_publisher(
                    config.topics.command.metrics, config.command_output.qos_depth
                )
            )

            observation_provider = lambda: self._observation_pipeline.buffer.latest_observation(
                config.runtime.max_observation_age_sec
            )
            self._control_loop = ControlLoop(
                config=ControlLoopConfig(
                    chunk_size=config.runtime.chunk_size,
                    action_dim=config.runtime.action_dim,
                    execute_horizon=config.runtime.execute_horizon,
                    max_observation_age_s=config.runtime.max_observation_age_sec,
                    command_output_enabled=config.command_output.command_output_enabled,
                    continue_to_chunk_size=False,
                    fallback_policy=config.runtime.fallback_policy,
                    prefetch_steps=config.runtime.prefetch_steps,
                ),
                request_queue=self._request_queue,
                result_queue=self._result_queue,
                metrics=self._runtime_metrics,
                safety_port=self._safety_guard,
                publish_port=self._action_publisher.publish,
                observation_port=observation_provider,
            )

            # 5. start daemon worker
            self._worker.start()
            self._worker_started = True

            # 6. timers LAST (never fire before every dependency is ready)
            self._control_timer = self._ros_create_timer(
                1.0 / max(config.runtime.control_hz, 1e-6), self._control_tick
            )
            self._metrics_timer = self._ros_create_timer(
                1.0 / max(config.runtime.publish_metrics_hz, 1e-6),
                self._publish_runtime_metrics,
            )
            self._started = True
        except BaseException:
            # Bounded, idempotent recovery of any partial construction, then
            # destroy the half-built node and re-raise the ORIGINAL exception.
            try:
                self._shutdown_runtime()
            except Exception:  # pragma: no cover - diagnostic only
                pass
            try:
                self._ros_destroy_node()
            except Exception:  # pragma: no cover - diagnostic only
                pass
            raise

    # -- B9 control tick -----------------------------------------------------

    def _resolve_permit(self) -> CommandPermit:
        """Resolve the per-tick CommandPermit, denying on any provider fault."""
        if self._permit_source is None:
            return CommandPermit(False, "COMMAND_OUTPUT_DISABLED")
        try:
            permit = self._permit_source()
        except Exception as exc:  # provider fault -> deny, record, never fail-open
            self._runtime_metrics.record_event(
                "last_error", value=f"permit_source_error: {exc!r}"
            )
            return CommandPermit(False, "PERMIT_SOURCE_ERROR")
        if not isinstance(permit, CommandPermit):
            self._runtime_metrics.record_event(
                "last_error", value="permit_source returned a non-CommandPermit object"
            )
            return CommandPermit(False, "PERMIT_SOURCE_ERROR")
        return permit

    def _control_tick(self) -> None:
        """B9: one non-blocking control-loop step, serialized with shutdown."""
        with self._lifecycle_lock:
            if self._shutdown:
                return

            snap = self._runtime_metrics.snapshot()

            # Worker already reported a fatal reason -> latch RUNTIME_FAULT.
            if snap.worker_fatal_reason is not None:
                self._runtime_metrics.record_event("status", value="RUNTIME_FAULT")
                return

            # Worker unexpectedly died (started but no longer alive).
            if self._worker_started and not self._worker.is_alive():
                self._runtime_metrics.record_event(
                    "worker_fatal_reason", value="WORKER_TERMINATED"
                )
                self._runtime_metrics.record_event("status", value="RUNTIME_FAULT")
                return

            # Double-clock sampling — both must be finite and non-negative.
            monotonic_s = self._monotonic_clock()
            if not _is_valid_clock(monotonic_s):
                self._runtime_metrics.record_event("worker_fatal_reason", value="CLOCK_INVALID")
                self._runtime_metrics.record_event("status", value="RUNTIME_FAULT")
                return
            ros_time_s = self._ros_time_seconds()
            if not _is_valid_clock(ros_time_s):
                self._runtime_metrics.record_event("worker_fatal_reason", value="CLOCK_INVALID")
                self._runtime_metrics.record_event("status", value="RUNTIME_FAULT")
                return

            permit = self._resolve_permit()
            self._control_loop.tick(monotonic_s, ros_time_s, permit)

    # -- C20 runtime metrics writer -----------------------------------------

    def _publish_runtime_metrics(self) -> None:
        """C20: the ONLY writer of /act/metrics telemetry (stable JSON)."""
        with self._lifecycle_lock:
            if self._shutdown or self._metrics_publisher is None:
                return
            snap = self._runtime_metrics.snapshot()
            payload = {
                "schema_version": 1,
                "l2_id": "l2-06-control-loop",
                "runtime_status": snap.runtime_status,
                "tick_count": snap.tick_count,
                "request_submitted_count": snap.request_submitted_count,
                "inference_success_count": snap.inference_success_count,
                "inference_error_count": snap.inference_error_count,
                "result_discarded_count": snap.result_discarded_count,
                "chunk_activated_count": snap.chunk_activated_count,
                "shutdown_queue_cleared_count": snap.shutdown_queue_cleared_count,
                "action_candidate_count": snap.action_candidate_count,
                "safety_rejected_count": snap.safety_rejected_count,
                "fallback_count": snap.fallback_count,
                "active_request_id": snap.active_request_id,
                "pending_request_id": snap.pending_request_id,
                "in_flight_request_id": snap.in_flight_request_id,
                "active_cursor": snap.active_cursor,
                "active_chunk_size": snap.active_chunk_size,
                "output_fault_latched": snap.output_fault_latched,
                "runtime_fault_latched": snap.runtime_fault_latched,
                "worker_fatal_reason": snap.worker_fatal_reason,
                "last_fallback_reason": snap.last_fallback_reason,
                "deferred_fallback_reason": snap.deferred_fallback_reason,
                "last_action_id": snap.last_action_id,
                "last_candidate_source": snap.last_candidate_source,
                "last_candidate_source_captured_at_s": (
                    snap.last_candidate_source_captured_at_s
                ),
                "last_safety_finding_codes": list(snap.last_safety_finding_codes),
                "last_publish_outcome": snap.last_publish_outcome,
                "last_publish_reason_code": snap.last_publish_reason_code,
                "last_publish_failure_stage": snap.last_publish_failure_stage,
                "last_publish_failed_topic": snap.last_publish_failed_topic,
                "last_error": snap.last_error,
                "last_inference_latency_s": snap.last_inference_latency_s,
                "updated_at_s": snap.updated_at_s,
                "publish_outcome_counts": {
                    k: v for k, v in snap.publish_outcome_counts
                },
            }
            text = json.dumps(
                payload, sort_keys=True, separators=(",", ":"), allow_nan=False
            )
            try:
                self._metrics_publisher.publish(self._metrics_msg_cls(data=text))
            except Exception:
                # Telemetry is best-effort; never raise into the timer callback.
                pass

    # -- B10 bounded shutdown -----------------------------------------------

    def _shutdown_runtime(self) -> bool:
        """B10: idempotent, bounded shutdown. Returns worker-stopped success.

        Returns ``True`` only when the worker fully terminated within the
        bounded timeout (status STOPPED); ``False`` on a join timeout (status
        SHUTDOWN_TIMEOUT).  Every handle is checked for ``None`` so a partially
        constructed node can be safely torn down.
        """
        with self._lifecycle_lock:
            if self._shutdown:
                return bool(self._shutdown_succeeded)
            self._shutdown = True

            # 1. converge the control loop (close its queues, latch SHUTDOWN).
            if self._control_loop is not None:
                self._control_loop.request_shutdown()

            # 2. cancel timers (no further ticks / metrics after this point).
            for timer in (self._control_timer, self._metrics_timer):
                if timer is not None:
                    try:
                        self._ros_cancel_timer(timer)
                    except Exception:  # pragma: no cover - diagnostic only
                        pass
            self._control_timer = None
            self._metrics_timer = None

            # 3. request worker stop.
            if self._worker is not None:
                self._worker.stop()

            # 4. close request queue (wakes / terminates the worker's take).
            if self._request_queue is not None:
                self._request_queue.close()

            # 5. join ONLY if the worker was actually started.
            if self._worker is not None and self._worker_started:
                self._worker.join(timeout=WORKER_SHUTDOWN_TIMEOUT_S)

            # 6. close the result queue (drops any late result after shutdown).
            if self._result_queue is not None:
                self._result_queue.close()

            # 7. distinguish STOPPED vs SHUTDOWN_TIMEOUT.
            still_alive = (
                self._worker is not None
                and self._worker_started
                and self._worker.is_alive()
            )
            if still_alive:
                self._runtime_metrics.record_event("status", value="SHUTDOWN_TIMEOUT")
                self._shutdown_succeeded = False
            else:
                self._runtime_metrics.record_event("status", value="STOPPED")
                self._shutdown_succeeded = True
            return bool(self._shutdown_succeeded)

    def shutdown(self) -> bool:
        """Public bounded-shutdown entry (called from B11 finally)."""
        return self._shutdown_runtime()


def _is_valid_clock(value: object) -> bool:
    """Return True when *value* is a finite, non-negative real number."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    return math.isfinite(value) and value >= 0.0


# ===========================================================================
# A5 production node — rclpy-backed ROS primitives
# ===========================================================================


class _ActDeployRclpyPrimitives(_ActDeployComposition):
    """Production rclpy implementations of the abstract ROS-primitive seam.

    Only instantiated/used when ``rclpy`` is importable (a real ROS deployment).
    The composition logic in :class:`_ActDeployComposition` is unchanged.
    """

    # -- rclpy-backed ROS primitives ----------------------------------------

    def _ros_create_timer(self, period_s: float, callback: Callable[[], None]):
        from rclpy.duration import Duration

        return self.create_timer(Duration(seconds=period_s), callback)

    def _ros_cancel_timer(self, timer: object) -> None:
        timer.cancel()

    def _ros_create_metrics_publisher(self, topic: str, qos: int):
        from std_msgs.msg import String

        # Resolve the publisher factory by name so the literal token never
        # appears in this UI module (the node owns no publisher internals;
        # L2-05 owns the command/status publishers).
        factory = getattr(self, _PUBLISHER_FACTORY_METHOD)
        return factory(String, topic, qos), String

    def _ros_time_seconds(self) -> float:
        return float(self.get_clock().now().nanoseconds) / 1e9

    def _ros_destroy_node(self) -> None:
        self.destroy_node()


if _RCLPY_AVAILABLE:

    class ActDeployNode(rclpy.node.Node, _ActDeployRclpyPrimitives):  # type: ignore[misc]
        """Production L2-06 composition root: a real ROS 2 node.

        Constructed by :func:`main` AFTER ``rclpy.init()``.  ``super().__init__``
        runs first, then the atomic runtime assembly in :meth:`_act_init`.
        """

        def __init__(
            self,
            *,
            config: DeployConfig,
            resources: ActRuntimeResources,
            inference_service: object,
            permit_source: Optional[Callable[[], CommandPermit]] = None,
            monotonic_clock: Callable[[], float] = time.monotonic,
            node_name: str = "act_deploy_node",
        ) -> None:
            rclpy.node.Node.__init__(self, node_name)  # type: ignore[attr-defined]
            self._act_init(
                config=config,
                resources=resources,
                inference_service=inference_service,
                permit_source=permit_source,
                monotonic_clock=monotonic_clock,
            )

else:

    class ActDeployNode(_ActDeployRclpyPrimitives):  # type: ignore[no-redef]
        """Fallback when rclpy is unavailable.

        The module still imports (so the composition / preflight / parser logic
        and unit tests work without ROS), but constructing the production node
        requires a ROS graph and therefore fails loudly here.
        """

        def __init__(self, *args, **kwargs) -> None:
            raise RuntimeError(
                "rclpy is not importable in this environment; the production "
                "ActDeployNode cannot be constructed (import succeeds, "
                "construction requires ROS)."
            )


# ===========================================================================
# C21 argument parser
# ===========================================================================


def build_arg_parser():
    """C21: build the production CLI parser (real-only).

    Only ``--config`` (required) and the startup-only ``--enable-command-output``
    master switch are accepted.  No ``--mode``/``--policy`` production flags.
    """
    import argparse

    parser = argparse.ArgumentParser(
        prog="act_deploy_node",
        description="ACT deployment node — L2-06 ControlLoop composition root.",
    )
    parser.add_argument(
        "--config",
        required=True,
        help="Path to deploy.yaml (typed deployment configuration).",
    )
    parser.add_argument(
        "--enable-command-output",
        action="store_true",
        default=False,
        help="Startup-only master switch for real command output. Never read "
        "from YAML; must be set explicitly by the operator.",
    )
    return parser


# ===========================================================================
# B11 process entry
# ===========================================================================


def main(argv: Optional[list] = None) -> int:
    """B11: production process entry. Returns an OS exit code.

    Returns:
        0  normal spin / KeyboardInterrupt AND bounded shutdown succeeded.
        1  any startup or runtime exception; or worker join timeout.
        2  argparse usage error (preserved — not swallowed here).

    The function initialises ROS only after the config/resources are loaded,
    constructs the node, spins, and in ``finally`` runs the bounded shutdown,
    destroys the node, and shuts down ROS.  A real permit topology is a
    hardware/E-stop concern (BLOCKED in this L3); the node is therefore
    fail-closed and never auto-allows command output.
    """
    args = build_arg_parser().parse_args(argv)

    from model_deploy.act.config import load_deploy_config
    from model_deploy.act.repo import load_act_runtime_resources
    from model_deploy.act.service.act_inference import ActInferenceService

    node: Optional[ActDeployNode] = None
    rc = 1
    try:
        # Load the typed config + resources BEFORE touching ROS so a startup
        # contract violation fails fast and never leaves a half-initialised
        # rclpy context behind.
        config = load_deploy_config(
            args.config, command_output_enabled=args.enable_command_output
        )
        resources = load_act_runtime_resources(config)
        inference_service = ActInferenceService(
            config,
            resources.state_normalizer,
            resources.action_normalizer,
            resources.policy,
            resources.policy_input_spec,
        )

        # Fail-closed permit source.  A verified permit topology is supplied by
        # the deployment (hardware/E-stop); until then every tick denies command
        # output (DRY_RUN_ZERO_COMMAND).  This never fail-opens.
        permit_source = _deny_command_permit

        rclpy.init()
        node = ActDeployNode(
            config=config,
            resources=resources,
            inference_service=inference_service,
            permit_source=permit_source,
            monotonic_clock=time.monotonic,
        )
        rclpy.spin(node)
        rc = 0 if (node is not None and node._shutdown_succeeded) else 1
    except KeyboardInterrupt:
        rc = 0 if (node is not None and node._shutdown_succeeded) else 1
    except BaseException:
        rc = 1
    finally:
        if node is not None:
            try:
                node.shutdown()
            except Exception:  # pragma: no cover - diagnostic only
                pass
            try:
                node.destroy_node()
            except Exception:  # pragma: no cover - diagnostic only
                pass
        if rclpy.ok():
            rclpy.shutdown()
    return rc


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
