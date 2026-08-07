"""Action representation contract for ACT model deployment.

Defines how the ACT model expresses its arm / gripper action, so the bundle is
self-describing and the loader can reject an old absolute-action checkpoint
instead of misinterpreting it as relative action.

Two layers share these enum-style constants:

- ``ActionRepresentationSpec`` (types layer, frozen dataclass): the single
  representation contract read from the bundle ``manifest.json`` and carried
  inside the runtime resources and the decoder.
- ``ActionRepresentationConfig`` lives in ``config/schema.py`` as the
  deploy-side *expected* representation declared in ``deploy.yaml``.  The
  startup preflight cross-validates the two field-by-field.

The supported (and only) first-version representation is:

    arm_action_type         = relative_tcp_pose
    chunk_reference         = inference_observation
    translation_frame       = tcp_local
    rotation_representation = quaternion_xyzw
    gripper_action_type     = absolute

Semantics of each field:

- ``arm_action_type``: the arm part of each action row is a *relative* TCP
  pose (translation + quaternion) with respect to the inference-moment
  reference, not an absolute base-frame target.
- ``chunk_reference``: every row in one chunk is relative to the *same*
  reference — the TCP captured in the ObservationSnapshot that produced this
  inference.  No step-wise accumulation.
- ``translation_frame``: the relative translation is expressed in the
  reference TCP local frame, so the absolute translation is
  ``p_abs = p_ref + R_ref @ p_rel``.
- ``rotation_representation``: the relative orientation is an ``xyzw``
  quaternion composed as ``q_abs = q_ref ⊗ q_rel``.
- ``gripper_action_type``: the gripper fields stay *absolute* targets and are
  copied through unchanged.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


# ---------------------------------------------------------------------------
# Enum-style representation tokens
# ---------------------------------------------------------------------------


class ArmActionType(str, Enum):
    """How the arm TCP action is expressed by the model."""

    RELATIVE_TCP_POSE = "relative_tcp_pose"
    ABSOLUTE_TCP_POSE = "absolute_tcp_pose"


class ChunkReference(str, Enum):
    """Which state the relative chunk is referenced against."""

    INFERENCE_OBSERVATION = "inference_observation"


class TranslationFrame(str, Enum):
    """Coordinate frame of the relative translation component."""

    TCP_LOCAL = "tcp_local"


class RotationRepresentation(str, Enum):
    """Rotation encoding and component order of the relative orientation."""

    QUATERNION_XYZW = "quaternion_xyzw"


class GripperActionType(str, Enum):
    """How the gripper action is expressed by the model."""

    ABSOLUTE = "absolute"


# ---------------------------------------------------------------------------
# Canonical expected representation (first-version ACT relative-action bundle)
# ---------------------------------------------------------------------------

#: The only representation supported by the first-version ACT deployment. The
#: deploy config defaults to this, and the runtime-resource loader reads it
#: from the bundle manifest and cross-validates field-by-field at startup.
EXPECTED_ARM_ACTION_TYPE = ArmActionType.RELATIVE_TCP_POSE.value
EXPECTED_CHUNK_REFERENCE = ChunkReference.INFERENCE_OBSERVATION.value
EXPECTED_TRANSLATION_FRAME = TranslationFrame.TCP_LOCAL.value
EXPECTED_ROTATION_REPRESENTATION = RotationRepresentation.QUATERNION_XYZW.value
EXPECTED_GRIPPER_ACTION_TYPE = GripperActionType.ABSOLUTE.value


# ---------------------------------------------------------------------------
# ActionRepresentationSpec
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ActionRepresentationSpec:
    """Frozen representation contract read from the bundle manifest.

    Carries the five self-describing representation tokens of a checkpoint.
    The runtime-resource loader constructs this once from
    ``manifest.json`` ``action_representation`` and the deploy config holds the
    matching expectation; the startup preflight asserts they are identical.

    Attributes:
        arm_action_type:         ``relative_tcp_pose`` or ``absolute_tcp_pose``.
        chunk_reference:         ``inference_observation`` for the first version.
        translation_frame:       ``tcp_local`` for the first version.
        rotation_representation: ``quaternion_xyzw`` for the first version.
        gripper_action_type:     ``absolute`` for the first version.
    """

    arm_action_type: str
    chunk_reference: str
    translation_frame: str
    rotation_representation: str
    gripper_action_type: str

    def __post_init__(self) -> None:
        for name, value in (
            ("arm_action_type", self.arm_action_type),
            ("chunk_reference", self.chunk_reference),
            ("translation_frame", self.translation_frame),
            ("rotation_representation", self.rotation_representation),
            ("gripper_action_type", self.gripper_action_type),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(
                    f"ActionRepresentationSpec.{name} must be a non-empty string"
                )

    def as_mapping(self) -> dict[str, str]:
        """Return the five tokens as a plain ``dict`` for cross-validation."""
        return {
            "arm_action_type": self.arm_action_type,
            "chunk_reference": self.chunk_reference,
            "translation_frame": self.translation_frame,
            "rotation_representation": self.rotation_representation,
            "gripper_action_type": self.gripper_action_type,
        }


def is_expected_relative_spec(spec: ActionRepresentationSpec) -> bool:
    """True when *spec* matches the first-version relative-action contract."""
    return spec.as_mapping() == {
        "arm_action_type": EXPECTED_ARM_ACTION_TYPE,
        "chunk_reference": EXPECTED_CHUNK_REFERENCE,
        "translation_frame": EXPECTED_TRANSLATION_FRAME,
        "rotation_representation": EXPECTED_ROTATION_REPRESENTATION,
        "gripper_action_type": EXPECTED_GRIPPER_ACTION_TYPE,
    }
