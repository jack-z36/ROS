"""Cross-process contract for the official LeRobot v3 exporter."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


OFFICIAL_LEROBOT_VERSION = "0.5.2"
OFFICIAL_CODEBASE_VERSION = "v3.0"
DEFAULT_EXPORT_TASK = "bimanual manipulation"
DEFAULT_EXPORT_FPS = 15
DEFAULT_STATE_DIM = 16
DEFAULT_ACTION_DIM = 16
DEFAULT_IMAGE_HEIGHT = 480
DEFAULT_IMAGE_WIDTH = 640
IMAGE_FEATURES = (
    "observation.images.left",
    "observation.images.right",
)


class LeRobotExportContractError(ValueError):
    """Raised when an exporter request violates the production contract."""


@dataclass(frozen=True)
class LeRobotExportRequest:
    job_id: str
    dataset_name: str
    bridge_dirs: tuple[str, ...]
    output_dir: str
    task: str = DEFAULT_EXPORT_TASK
    fps: int = DEFAULT_EXPORT_FPS
    state_dim: int = DEFAULT_STATE_DIM
    action_dim: int = DEFAULT_ACTION_DIM
    image_height: int = DEFAULT_IMAGE_HEIGHT
    image_width: int = DEFAULT_IMAGE_WIDTH
    robot_type: str = "umi_bimanual"
    repo_id: str | None = None

    def __post_init__(self) -> None:
        if not self.job_id.strip():
            raise LeRobotExportContractError("job_id must not be empty")
        if not self.dataset_name.strip():
            raise LeRobotExportContractError("dataset_name must not be empty")
        if not self.bridge_dirs:
            raise LeRobotExportContractError("bridge_dirs must not be empty")
        if self.fps != DEFAULT_EXPORT_FPS:
            raise LeRobotExportContractError(
                f"production fps must be {DEFAULT_EXPORT_FPS}, got {self.fps}"
            )
        if self.state_dim != DEFAULT_STATE_DIM:
            raise LeRobotExportContractError(
                f"observation.state must be float32[{DEFAULT_STATE_DIM}], got {self.state_dim}"
            )
        if self.action_dim != DEFAULT_ACTION_DIM:
            raise LeRobotExportContractError(
                f"action must be float32[{DEFAULT_ACTION_DIM}], got {self.action_dim}"
            )
        if (self.image_height, self.image_width) != (
            DEFAULT_IMAGE_HEIGHT,
            DEFAULT_IMAGE_WIDTH,
        ):
            raise LeRobotExportContractError(
                "production images must be uint8[480,640,3]"
            )
        if self.robot_type != "umi_bimanual":
            raise LeRobotExportContractError("robot_type must be umi_bimanual")
        if not self.task.strip():
            raise LeRobotExportContractError("task must not be empty")

    @property
    def effective_repo_id(self) -> str:
        return self.repo_id or f"local/{self.dataset_name}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "dataset_name": self.dataset_name,
            "bridge_dirs": list(self.bridge_dirs),
            "output_dir": self.output_dir,
            "task": self.task,
            "fps": self.fps,
            "state_dim": self.state_dim,
            "action_dim": self.action_dim,
            "image_height": self.image_height,
            "image_width": self.image_width,
            "robot_type": self.robot_type,
            "repo_id": self.effective_repo_id,
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "LeRobotExportRequest":
        if not isinstance(raw, dict):
            raise LeRobotExportContractError("request must be a JSON object")
        bridge_dirs = raw.get("bridge_dirs")
        if not isinstance(bridge_dirs, list):
            raise LeRobotExportContractError("bridge_dirs must be a list")
        output_dir = str(raw.get("output_dir", "")).strip()
        if not output_dir:
            raise LeRobotExportContractError("output_dir must not be empty")
        return cls(
            job_id=str(raw.get("job_id", "")),
            dataset_name=str(raw.get("dataset_name", "")),
            bridge_dirs=tuple(str(Path(item).expanduser().resolve()) for item in bridge_dirs),
            output_dir=str(Path(output_dir).expanduser().resolve()),
            task=str(raw.get("task") or DEFAULT_EXPORT_TASK),
            fps=int(raw.get("fps", DEFAULT_EXPORT_FPS)),
            state_dim=int(raw.get("state_dim", DEFAULT_STATE_DIM)),
            action_dim=int(raw.get("action_dim", DEFAULT_ACTION_DIM)),
            image_height=int(raw.get("image_height", DEFAULT_IMAGE_HEIGHT)),
            image_width=int(raw.get("image_width", DEFAULT_IMAGE_WIDTH)),
            robot_type=str(raw.get("robot_type") or "umi_bimanual"),
            repo_id=str(raw["repo_id"]) if raw.get("repo_id") else None,
        )


def official_lerobot_features(request: LeRobotExportRequest) -> dict[str, dict[str, Any]]:
    """Return the single production feature contract consumed by LeRobot."""

    state_names = [f"state_{index}" for index in range(request.state_dim)]
    action_names = [f"action_{index}" for index in range(request.action_dim)]
    return {
        "observation.state": {
            "dtype": "float32",
            "shape": (request.state_dim,),
            "names": state_names,
        },
        "action": {
            "dtype": "float32",
            "shape": (request.action_dim,),
            "names": action_names,
        },
        IMAGE_FEATURES[0]: {
            "dtype": "video",
            "shape": (request.image_height, request.image_width, 3),
            "names": ["height", "width", "channels"],
        },
        IMAGE_FEATURES[1]: {
            "dtype": "video",
            "shape": (request.image_height, request.image_width, 3),
            "names": ["height", "width", "channels"],
        },
    }
