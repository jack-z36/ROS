"""ROS topic naming helpers for the Pi0.5 deployment stack."""

from __future__ import annotations

from dataclasses import dataclass


DEFAULT_NAMESPACE = "/pi05"


def join_topic(namespace: str, *parts: str) -> str:
    """Join ROS topic fragments while keeping a single leading slash."""
    cleaned = [str(namespace).strip("/")]
    cleaned.extend(str(part).strip("/") for part in parts if str(part).strip("/"))
    return "/" + "/".join(part for part in cleaned if part)


@dataclass(frozen=True)
class Pi05CommandTopics:
    """Topic set produced by the Pi0.5 deployment command loop.

    TO-BE: single policy_action topic instead of four joint/hand targets.
    """

    policy_action: str
    status: str
    metrics: str

    @classmethod
    def with_namespace(cls, namespace: str = DEFAULT_NAMESPACE) -> "Pi05CommandTopics":
        return cls(
            policy_action=join_topic(namespace, "policy_action"),
            status=join_topic(namespace, "status"),
            metrics=join_topic(namespace, "metrics"),
        )


@dataclass(frozen=True)
class Pi05ObservationTopics:
    """Default topic set consumed by the Pi0.5 observation collector.

    TO-BE fields: fisheye stereo images, left/right TCP pose, left/right gripper state.
    """

    left_fisheye_image: str
    right_fisheye_image: str
    left_tcp_pose: str
    right_tcp_pose: str
    left_gripper_state: str
    right_gripper_state: str

    @classmethod
    def with_namespace(cls, namespace: str = DEFAULT_NAMESPACE) -> "Pi05ObservationTopics":
        return cls(
            left_fisheye_image=join_topic(namespace, "observation", "image", "left_gripper_fisheye"),
            right_fisheye_image=join_topic(namespace, "observation", "image", "right_gripper_fisheye"),
            left_tcp_pose=join_topic(namespace, "observation", "arm", "left_tcp_pose"),
            right_tcp_pose=join_topic(namespace, "observation", "arm", "right_tcp_pose"),
            left_gripper_state=join_topic(namespace, "observation", "gripper", "left_state"),
            right_gripper_state=join_topic(namespace, "observation", "gripper", "right_state"),
        )
