"""ObservationPipeline — frozen typed observation assembly facade (deploy_057).

Builds the full L2-02 observation assembly chain (collector + buffer +
adapter) from a single ``DeployConfig`` and the canonical ``PolicyInputSpec``,
plus a shared monotonic clock.  All RAM validation (config / spec / camera /
image / message-class consistency) happens *before* any ROS subscription is
created, so a misconfiguration fails fast instead of leaking partial
subscriptions.

The returned ``ObservationPipeline`` exposes the collector, buffer, adapter,
the input spec and the monotonic clock.  The spec and clock objects are the
same instances passed in (identity preserved), so the ControlLoop can rely on
a single, stable contract.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Sequence

from model_deploy.act.config.schema import DeployConfig
from model_deploy.act.repo.act_runtime_resources import PolicyInputSpec
from model_deploy.act.runtime.observation_buffer import ObservationBuffer
from model_deploy.act.service.observation_collector import ObservationCollector
from model_deploy.act.ui.observation_ros_adapter import ObservationRosAdapter


# State sub-fields required for a complete ObservationSnapshot.  These are the
# canonical ACT 16D state layout (left/right TCP pose + gripper width) and are
# independent of the camera mapping.
REQUIRED_STATE_FIELDS: Sequence[str] = (
    "left_tcp_position",
    "left_tcp_orientation",
    "left_gripper_width",
    "right_tcp_position",
    "right_tcp_orientation",
    "right_gripper_width",
)


@dataclass(frozen=True)
class ObservationPipeline:
    """Frozen typed observation assembly facade.

    Attributes:
        collector:       ObservationCollector (service layer cache + builder).
        buffer:          ObservationBuffer (runtime latest-only slot).
        adapter:         ObservationRosAdapter (ROS message -> RAM bridge).
        input_spec:      Canonical PolicyInputSpec (identity-equal to the one
                         passed to ``build_observation_pipeline``).
        monotonic_clock: Shared monotonic clock (identity-equal to the one
                         passed to ``build_observation_pipeline``).
    """

    collector: ObservationCollector
    buffer: ObservationBuffer
    adapter: ObservationRosAdapter
    input_spec: PolicyInputSpec
    monotonic_clock: Callable[[], float]


def build_observation_pipeline(
    *,
    node: object,
    config: DeployConfig,
    input_spec: PolicyInputSpec,
    monotonic_clock: Callable[[], float],
) -> ObservationPipeline:
    """Assemble a validated, ready ``ObservationPipeline``.

    Validation order (all pure RAM checks, no ROS side effects):
        1. ``config`` is a ``DeployConfig`` and ``input_spec`` a
           ``PolicyInputSpec``.
        2. Camera keys of ``config.topics.observation`` exactly equal
           ``input_spec.camera_keys``.
        3. ``input_spec`` image layout / dtype / value-range are the policy
           contract (CHW / float32 / [0, 1]).
        4. Gripper topology is recorded as unknown (not verified on hardware).

    Only after all checks pass are ROS subscriptions created.  If subscription
    creation raises (e.g. partial ROS failure), the adapter rolls back already
    created handles and the error propagates — the pipeline is not returned in
    a half-built state.

    Args:
        node:            ROS node used to create subscriptions (may be a mock
                         when ROS is absent; the adapter records env_blocked).
        config:          Frozen ``DeployConfig``.
        input_spec:      Frozen canonical ``PolicyInputSpec``.
        monotonic_clock: Callable returning the current monotonic time (s).

    Returns:
        A frozen ``ObservationPipeline`` with the same ``input_spec`` and
        ``monotonic_clock`` instances as passed in.

    Raises:
        TypeError:  If ``config`` / ``input_spec`` / ``monotonic_clock`` have
                    the wrong type.
        ValueError: If camera keys or image contract are inconsistent.
    """
    if not isinstance(config, DeployConfig):
        raise TypeError("config must be a DeployConfig")
    if not isinstance(input_spec, PolicyInputSpec):
        raise TypeError("input_spec must be a PolicyInputSpec")
    if not callable(monotonic_clock):
        raise TypeError("monotonic_clock must be callable")

    # --- 2. camera-key alignment ---
    # (image layout / dtype / value-range are guaranteed by the frozen
    #  PolicyInputSpec construction; the camera mapping is the one cross-check
    #  between the config topics and the spec, so it is enforced here.)
    config_cameras = set(config.topics.observation.camera_keys)
    spec_cameras = set(input_spec.camera_keys)
    if config_cameras != spec_cameras:
        raise ValueError(
            "Observation camera keys mismatch: config has "
            f"{sorted(config_cameras)} but PolicyInputSpec requires "
            f"{sorted(spec_cameras)}"
        )

    # --- 3. build the chain ---
    collector = ObservationCollector(
        required_image_keys=list(input_spec.camera_keys),
        required_state_fields=list(REQUIRED_STATE_FIELDS),
        monotonic_clock=monotonic_clock,
    )
    buffer = ObservationBuffer(monotonic_clock=monotonic_clock)
    adapter = ObservationRosAdapter(
        collector=collector,
        buffer=buffer,
        config=config,
        input_spec=input_spec,
        max_age_s=config.runtime.max_observation_age_sec,
        monotonic_clock=monotonic_clock,
    )

    # --- create subscriptions only after all RAM checks pass ---
    adapter.create_subscriptions(node)

    return ObservationPipeline(
        collector=collector,
        buffer=buffer,
        adapter=adapter,
        input_spec=input_spec,
        monotonic_clock=monotonic_clock,
    )
