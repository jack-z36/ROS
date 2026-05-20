"""Service registry — build a ServiceRegistry and query ServiceBinding by SceneName."""

from __future__ import annotations

from schemas.runtime_dispatch_types import ServiceBinding, ServiceRegistry
from schemas.runtime_enums import SceneName, ServiceMode

SERVICE_NOT_REGISTERED = "service_not_registered"
SERVICE_MODE_MISMATCH = "service_mode_mismatch"


def build_service_registry(
    bindings: list[ServiceBinding],
    service_mode: ServiceMode,
) -> ServiceRegistry:
    """Build a ServiceRegistry from a list of ServiceBindings.

    Validates that:
    - No duplicate bindings for the same scene.
    - Each binding's service_mode matches the registry mode.

    Returns:
        A populated ServiceRegistry.

    Raises:
        ValueError: On duplicate binding or service_mode mismatch.
    """
    binding_map: dict[SceneName, ServiceBinding] = {}
    seen: set[SceneName] = set()

    for b in bindings:
        if b.scene_name in seen:
            raise ValueError(
                f"duplicate binding for scene {b.scene_name.value}"
            )
        if b.service_mode != service_mode:
            raise ValueError(
                f"{SERVICE_MODE_MISMATCH}: binding for {b.scene_name.value} "
                f"has mode {b.service_mode.value}, expected {service_mode.value}"
            )
        binding_map[b.scene_name] = b
        seen.add(b.scene_name)

    return ServiceRegistry(
        bindings=binding_map,
        service_mode=service_mode,
        registered_scenes=list(binding_map.keys()),
    )


def lookup_service_binding(
    registry: ServiceRegistry,
    scene_name: SceneName,
) -> ServiceBinding:
    """Look up a ServiceBinding for the given scene.

    Args:
        registry: The ServiceRegistry to query.
        scene_name: Target scene to find a binding for.

    Returns:
        The ServiceBinding for the given scene.

    Raises:
        KeyError: If the scene is not registered.
    """
    if scene_name not in registry.bindings:
        raise KeyError(
            f"{SERVICE_NOT_REGISTERED}: scene {scene_name.value} "
            f"is not registered in this service registry"
        )
    return registry.bindings[scene_name]
