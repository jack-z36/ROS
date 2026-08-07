"""Cross-process contract for the official LeRobot v3 exporter."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from schemas.lerobot_features import MACHINE_NAME_PATTERN, compile_lerobot_feature_contract


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
    state_names: tuple[str, ...] = ()
    action_names: tuple[str, ...] = ()
    feature_contract: dict[str, Any] | None = None
    contract_fingerprint: str | None = None

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
        if self.state_dim <= 0 or self.action_dim <= 0:
            raise LeRobotExportContractError("state_dim and action_dim must be positive")
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
        state_names = self.state_names or tuple(f"state_{index}" for index in range(self.state_dim))
        action_names = self.action_names or tuple(f"action_{index}" for index in range(self.action_dim))
        _validate_names("state_names", state_names, self.state_dim)
        _validate_names("action_names", action_names, self.action_dim)
        object.__setattr__(self, "state_names", state_names)
        object.__setattr__(self, "action_names", action_names)
        if self.feature_contract is not None and hasattr(self.feature_contract, "to_dict"):
            object.__setattr__(self, "feature_contract", self.feature_contract.to_dict())
        if self.feature_contract is not None:
            if not isinstance(self.feature_contract, dict):
                raise LeRobotExportContractError("feature_contract must be a mapping")
            contract_fp = self.feature_contract.get("contract_fingerprint") or self.feature_contract.get("fingerprint")
            if self.contract_fingerprint and contract_fp and self.contract_fingerprint != contract_fp:
                raise LeRobotExportContractError("contract_fingerprint does not match feature_contract")
            if contract_fp and not self.contract_fingerprint:
                object.__setattr__(self, "contract_fingerprint", str(contract_fp))
            for key, expected_dim, expected_names in (
                ("observation.state", self.state_dim, self.state_names),
                ("action", self.action_dim, self.action_names),
            ):
                layout = self.feature_contract.get(key)
                if not isinstance(layout, dict):
                    layout = self.feature_contract.get("state" if key == "observation.state" else "action")
                if isinstance(layout, dict):
                    if list(layout.get("shape", [])) != [expected_dim]:
                        raise LeRobotExportContractError(
                            f"feature_contract {key} shape does not match request"
                        )
                    if list(layout.get("names", [])) != list(expected_names):
                        raise LeRobotExportContractError(
                            f"feature_contract {key} names do not match request"
                        )
            if isinstance(self.feature_contract.get("config"), dict):
                compiled = compile_lerobot_feature_contract(self.feature_contract["config"])
                if compiled.fingerprint != self.contract_fingerprint:
                    raise LeRobotExportContractError(
                        "feature_contract fingerprint does not match its config"
                    )

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
            "state_names": list(self.state_names),
            "action_names": list(self.action_names),
            "feature_contract": self.feature_contract,
            "contract_fingerprint": self.contract_fingerprint,
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
            state_names=tuple(str(item) for item in raw.get("state_names", [])),
            action_names=tuple(str(item) for item in raw.get("action_names", [])),
            feature_contract=raw.get("feature_contract") if isinstance(raw.get("feature_contract"), dict) else None,
            contract_fingerprint=str(raw["contract_fingerprint"]) if raw.get("contract_fingerprint") else None,
        )


def official_lerobot_features(request: LeRobotExportRequest) -> dict[str, dict[str, Any]]:
    """Return the single production feature contract consumed by LeRobot."""

    state_names = list(request.state_names)
    action_names = list(request.action_names)
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


def _validate_names(path: str, names: tuple[str, ...], expected_dim: int) -> None:
    if len(names) != expected_dim:
        raise LeRobotExportContractError(
            f"{path} must contain {expected_dim} names, got {len(names)}"
        )
    if any(not name or not MACHINE_NAME_PATTERN.fullmatch(name) for name in names):
        raise LeRobotExportContractError(
            f"{path} must use ASCII letters, numbers, _, ., or -"
        )
    duplicates = sorted({name for name in names if names.count(name) > 1})
    if duplicates:
        raise LeRobotExportContractError(f"{path} contains duplicate names: {duplicates}")
