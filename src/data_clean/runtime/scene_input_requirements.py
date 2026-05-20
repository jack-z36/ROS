"""Scene input requirements resolver — maps SceneName to InputArtifactRequirement list."""

from __future__ import annotations

from schemas.input_artifact_types import InputArtifactRequirement
from schemas.runtime_enums import RunMode, SceneName

UNKNOWN_SCENE_MSG = "unknown_scene_input_requirement"

_SCENE_REQUIREMENTS: dict[SceneName, list[InputArtifactRequirement]] = {}


def _build_all() -> dict[SceneName, list[InputArtifactRequirement]]:
    all_modes = list(RunMode)

    return {
        SceneName.SCENE1: [
            InputArtifactRequirement(
                scene_name=SceneName.SCENE1,
                artifact_role="raw_mcap",
                path_config_key="scene1.input_path",
                required_kind="file",
                required_for_modes=all_modes,
                allow_manual_override=True,
                description="Raw MCAP input for scene 1 cleaning.",
            ),
        ],
        SceneName.SCENE2: [
            InputArtifactRequirement(
                scene_name=SceneName.SCENE2,
                artifact_role="cleaned_mcap",
                path_config_key="scene2.input_path",
                required_kind="file",
                required_for_modes=all_modes,
                allow_manual_override=True,
                description="Cleaned MCAP input for scene 2 validation.",
            ),
        ],
        SceneName.SCENE3: [
            InputArtifactRequirement(
                scene_name=SceneName.SCENE3,
                artifact_role="validated_mcap",
                path_config_key="scene3.input_path",
                required_kind="file",
                required_for_modes=all_modes,
                allow_manual_override=True,
                description="Validated MCAP input for scene 3 alignment.",
            ),
        ],
        SceneName.SCENE4: [
            InputArtifactRequirement(
                scene_name=SceneName.SCENE4,
                artifact_role="aligned_mcap",
                path_config_key="scene4.input_path",
                required_kind="file",
                required_for_modes=all_modes,
                allow_manual_override=True,
                description="Aligned MCAP input for scene 4 canonical dataset construction.",
            ),
        ],
        SceneName.SCENE5: [
            InputArtifactRequirement(
                scene_name=SceneName.SCENE5,
                artifact_role="canonical_dataset",
                path_config_key="scene5.input_path",
                required_kind="directory",
                required_for_modes=all_modes,
                allow_manual_override=True,
                description="Canonical dataset directory for scene 5 export.",
            ),
        ],
    }


def get_scene_input_requirements(
    scene_name: SceneName,
    run_mode: RunMode | None = None,
) -> list[InputArtifactRequirement]:
    """Return the list of input artifact requirements for a given scene.

    Args:
        scene_name: The target scene to resolve requirements for.
        run_mode: Optional run mode (first version returns same requirements
                  regardless of mode).

    Returns:
        List of InputArtifactRequirement for the given scene.

    Raises:
        ValueError: If scene_name is not a recognized SceneName.
    """
    if not _SCENE_REQUIREMENTS:
        _SCENE_REQUIREMENTS.update(_build_all())

    try:
        scene = SceneName(scene_name)
    except (ValueError, AttributeError):
        raise ValueError(
            f"{UNKNOWN_SCENE_MSG}: unrecognized scene {scene_name!r}"
        )

    if scene not in _SCENE_REQUIREMENTS:
        raise ValueError(
            f"{UNKNOWN_SCENE_MSG}: no requirements defined for {scene.value!r}"
        )

    return list(_SCENE_REQUIREMENTS[scene])
