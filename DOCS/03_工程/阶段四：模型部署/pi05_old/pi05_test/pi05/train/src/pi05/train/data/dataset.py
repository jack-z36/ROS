"""Dataset wrapper for Pi0.5-style LeRobot offline training."""

from pathlib import Path
from typing import Any, Callable
import warnings

import numpy as np
import torch
from lerobot.datasets.lerobot_dataset import LeRobotDataset
from torch.utils.data import Dataset
from torchvision.transforms import ColorJitter, InterpolationMode
from torchvision.transforms import functional as TF


DEFAULT_CAMERAS = ("top", "left_wrist", "right_wrist")
TACTILE_CAMERAS = frozenset({"left_tactile", "right_tactile"})
DEFAULT_IMAGE_SIZE = 224
# PI0.5 模型内部会把 [0, 1] 图像再映射到 [-1, 1]；这里保留 Normalize 步骤但使用 identity，
# 避免提前做 ImageNet 标准化导致模型侧二次归一化错误。
IMAGE_NORMALIZE_MEAN = (0.0, 0.0, 0.0)
IMAGE_NORMALIZE_STD = (1.0, 1.0, 1.0)


class Pi05LeRobotDataset(Dataset):
    """LeRobot-backed dataset with action chunking and optional online image jitter."""

    DEFAULT_TASK = "bimanual manipulation"

    def __init__(
        self,
        dataset_path: str | Path,
        chunk_size: int = 30,
        use_color_jitter: bool = True,
        image_size: int = DEFAULT_IMAGE_SIZE,
        state_dim: int | None = None,
        action_dim: int | None = None,
        cameras: tuple[str, ...] | list[str] = DEFAULT_CAMERAS,
        state_normalizer: Callable[[torch.Tensor], torch.Tensor] | Any | None = None,
        action_normalizer: Callable[[torch.Tensor], torch.Tensor] | Any | None = None,
    ) -> None:
        self.dataset_path = Path(dataset_path).expanduser().resolve()
        if not self.dataset_path.exists():
            raise FileNotFoundError(f"Dataset path does not exist: {self.dataset_path}")
        if chunk_size <= 0:
            raise ValueError(f"chunk_size must be positive, got {chunk_size}")

        self.chunk_size = chunk_size
        self.image_size = int(image_size)
        self.cameras = self._normalize_cameras(cameras)
        self.lerobot_dataset = LeRobotDataset(repo_id=self.dataset_path.name, root=self.dataset_path)
        self.dataset = self.lerobot_dataset
        features = self.lerobot_dataset.features
        self.state_dim = self._feature_dim(features, "observation.state")
        self.action_dim = self._feature_dim(features, "action")
        self._warn_if_stale_expected_dim("observation.state", state_dim, self.state_dim)
        self._warn_if_stale_expected_dim("action", action_dim, self.action_dim)
        self.image_keys = self._resolve_image_keys()
        self._validate_vector_features()
        self.color_jitter = (
            ColorJitter(brightness=0.08, contrast=0.08, saturation=0.08, hue=0.03)
            if use_color_jitter
            else None
        )
        self.state_normalizer = state_normalizer
        self.action_normalizer = action_normalizer
        self.episode_ranges = self._build_episode_ranges()

    def __len__(self) -> int:
        return len(self.dataset)

    def __getitem__(self, idx: int) -> dict[str, torch.Tensor | str]:
        item = self.dataset[idx]
        images = {}
        for output_key, dataset_key in self.image_keys.items():
            camera_name = self._camera_from_output_key(output_key)
            images[output_key] = self._prepare_image(item[dataset_key], camera_name=camera_name)
        state = torch.as_tensor(item["observation.state"], dtype=torch.float32)
        state = self._apply_normalizer(state, self.state_normalizer)

        episode_index = self._to_int(item["episode_index"])
        action_chunk = self._get_action_chunk(idx, episode_index)
        action_chunk = self._apply_normalizer(action_chunk, self.action_normalizer)
        task = self._resolve_task(item)

        return {
            **images,
            "state": state,
            "action_chunk": action_chunk,
            "task": task,
        }

    def _resolve_image_keys(self) -> dict[str, str]:
        camera_keys = list(self.dataset.meta.camera_keys)
        if not camera_keys:
            raise ValueError("No image keys found in LeRobot dataset metadata.")

        image_key_map = {
            self._output_image_key(camera): self._dataset_image_key(camera)
            for camera in self.cameras
        }
        missing = [dataset_key for dataset_key in image_key_map.values() if dataset_key not in camera_keys]
        if missing:
            raise ValueError(
                "Dataset is missing required Pi0.5 image keys: "
                f"{missing}. Available keys: {camera_keys}"
            )
        return image_key_map

    def _validate_vector_features(self) -> None:
        features = self.lerobot_dataset.features
        for key, expected_dim in (("observation.state", self.state_dim), ("action", self.action_dim)):
            actual_dim = self._feature_dim(features, key)
            if actual_dim != expected_dim:
                raise ValueError(f"Dataset {key} shape changed while loading: got {actual_dim}, expected {expected_dim}.")

    def _build_episode_ranges(self) -> dict[int, tuple[int, int]]:
        ranges: dict[int, tuple[int, int]] = {}
        for episode_index in range(self.dataset.meta.total_episodes):
            episode = self.dataset.meta.episodes[episode_index]
            start = self._to_int(episode["dataset_from_index"])
            end = self._to_int(episode["dataset_to_index"])
            ranges[episode_index] = (start, end)
        return ranges

    def _get_action_chunk(self, idx: int, episode_index: int) -> torch.Tensor:
        _, episode_end = self.episode_ranges[episode_index]
        last_valid_idx = episode_end - 1

        actions = []
        for step in range(self.chunk_size):
            query_idx = min(idx + step, last_valid_idx)
            action = self.dataset.hf_dataset[query_idx]["action"]
            action_tensor = torch.as_tensor(action, dtype=torch.float32).flatten()
            if action_tensor.numel() != self.action_dim:
                raise ValueError(
                    f"Action at dataset index {query_idx} has dim {action_tensor.numel()}, expected {self.action_dim}."
                )
            actions.append(action_tensor)

        return torch.stack(actions, dim=0)

    def _prepare_image(self, image: Any, *, camera_name: str) -> torch.Tensor:
        image_tensor = self._to_image_tensor(image)
        is_tactile = camera_name in TACTILE_CAMERAS
        interpolation = InterpolationMode.NEAREST if is_tactile else InterpolationMode.BILINEAR
        if tuple(image_tensor.shape[-2:]) != (self.image_size, self.image_size):
            image_tensor = TF.resize(
                image_tensor,
                [self.image_size, self.image_size],
                interpolation=interpolation,
                antialias=not is_tactile,
            )
        image_tensor = TF.center_crop(image_tensor, [self.image_size, self.image_size])
        if self.color_jitter is not None and not is_tactile:
            image_tensor = self.color_jitter(image_tensor)
        image_tensor = TF.normalize(
            image_tensor,
            mean=IMAGE_NORMALIZE_MEAN,
            std=IMAGE_NORMALIZE_STD,
        )
        return image_tensor

    @staticmethod
    def _normalize_cameras(cameras: tuple[str, ...] | list[str]) -> tuple[str, ...]:
        normalized = tuple(str(camera).strip() for camera in cameras if str(camera).strip())
        if not normalized:
            raise ValueError("At least one image camera/key must be configured.")
        duplicates = sorted({camera for camera in normalized if normalized.count(camera) > 1})
        if duplicates:
            raise ValueError(f"Duplicate camera names are not allowed: {duplicates}")
        return normalized

    @staticmethod
    def _dataset_image_key(camera: str) -> str:
        return f"observation.images.{camera}"

    @staticmethod
    def _output_image_key(camera: str) -> str:
        return f"image_{camera}"

    @staticmethod
    def _camera_from_output_key(output_key: str) -> str:
        if not output_key.startswith("image_"):
            raise ValueError(f"Invalid dataset image output key: {output_key}")
        return output_key.removeprefix("image_")

    def _resolve_task(self, item: dict[str, Any]) -> str:
        task = item.get("task")
        if task is None and "task_index" in item:
            task = self._task_from_index(item["task_index"])
        if isinstance(task, str) and task.strip():
            return task.strip()
        return self.DEFAULT_TASK

    def _task_from_index(self, task_index: Any) -> str | None:
        task_idx = self._to_int(task_index)
        tasks = getattr(self.lerobot_dataset.meta, "tasks", None)
        if tasks is None:
            return None
        try:
            if hasattr(tasks, "iloc"):
                row = tasks.iloc[task_idx]
                for key in ("task", "tasks", "description"):
                    if key in row and isinstance(row[key], str):
                        return row[key]
            if isinstance(tasks, dict):
                value = tasks.get(task_idx, tasks.get(str(task_idx)))
                if isinstance(value, str):
                    return value
                if isinstance(value, dict):
                    return value.get("task")
        except (IndexError, KeyError, TypeError, ValueError):
            return None
        return None

    def _to_image_tensor(self, image: Any) -> torch.Tensor:
        if isinstance(image, torch.Tensor):
            image_tensor = image.detach().clone()
            if image_tensor.ndim != 3:
                raise ValueError(f"Expected 3D image tensor, got shape {tuple(image_tensor.shape)}")
            if image_tensor.shape[0] != 3 and image_tensor.shape[-1] == 3:
                image_tensor = image_tensor.permute(2, 0, 1)
            image_tensor = image_tensor.to(dtype=torch.float32)
            if image_tensor.max() > 1.0:
                image_tensor = image_tensor / 255.0
            return image_tensor

        if isinstance(image, np.ndarray):
            if image.ndim != 3 or image.shape[-1] != 3:
                raise ValueError(f"Expected image shape (H, W, 3), got {image.shape}")
            return TF.to_tensor(image)

        return TF.to_tensor(image)

    @staticmethod
    def _to_int(value: Any) -> int:
        if isinstance(value, torch.Tensor):
            return int(value.item())
        if isinstance(value, np.ndarray):
            return int(value.item())
        return int(value)

    @staticmethod
    def _apply_normalizer(
        tensor: torch.Tensor,
        normalizer: Callable[[torch.Tensor], torch.Tensor] | Any | None,
    ) -> torch.Tensor:
        if normalizer is None:
            return tensor
        if hasattr(normalizer, "normalize"):
            return normalizer.normalize(tensor)
        return normalizer(tensor)

    @staticmethod
    def _feature_dim(features: dict[str, dict], key: str) -> int:
        if key not in features:
            raise ValueError(f"Dataset is missing required feature '{key}'.")
        shape = tuple(features[key].get("shape", ()))
        if not shape:
            raise ValueError(f"Dataset feature '{key}' must have a non-empty shape.")
        return int(np.prod(shape))

    @staticmethod
    def _warn_if_stale_expected_dim(key: str, expected_dim: int | None, actual_dim: int) -> None:
        if expected_dim is None or int(expected_dim) == actual_dim:
            return
        warnings.warn(
            f"Ignoring configured {key} dim {expected_dim}; dataset metadata reports {actual_dim}.",
            RuntimeWarning,
            stacklevel=3,
        )
