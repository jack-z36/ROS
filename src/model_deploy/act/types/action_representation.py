"""Explicit ACT action representation contract."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ActionRepresentationSpec:
    """The semantic contract of one ACT action bundle."""

    arm_action_type: str
    chunk_reference: str
    translation_frame: str
    rotation_representation: str
    gripper_action_type: str

    def __post_init__(self) -> None:
        expected = {
            "arm_action_type": "relative_tcp_pose",
            "chunk_reference": "inference_observation",
            "translation_frame": "tcp_local",
            "rotation_representation": "quaternion_xyzw",
            "gripper_action_type": "absolute",
        }
        for field_name, expected_value in expected.items():
            actual = getattr(self, field_name)
            if actual != expected_value:
                raise ValueError(
                    f"unsupported action representation {field_name}={actual!r}; "
                    f"expected {expected_value!r}"
                )

    @classmethod
    def relative_tcp_v1(cls) -> "ActionRepresentationSpec":
        return cls(
            arm_action_type="relative_tcp_pose",
            chunk_reference="inference_observation",
            translation_frame="tcp_local",
            rotation_representation="quaternion_xyzw",
            gripper_action_type="absolute",
        )

    def as_mapping(self) -> dict[str, str]:
        return {
            "arm_action_type": self.arm_action_type,
            "chunk_reference": self.chunk_reference,
            "translation_frame": self.translation_frame,
            "rotation_representation": self.rotation_representation,
            "gripper_action_type": self.gripper_action_type,
        }
