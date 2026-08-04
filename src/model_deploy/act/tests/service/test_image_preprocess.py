"""Tests for preprocess_observation_image and ImageConfig."""

import numpy as np
import pytest

from model_deploy.act.service.image_preprocess import (
    ImageConfig,
    preprocess_observation_image,
)


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _make_image(h: int = 480, w: int = 640, c: int = 3) -> np.ndarray:
    """Return a dummy RGB image."""
    return np.random.randint(0, 256, (h, w, c), dtype=np.uint8)


def _make_config(
    h: int = 480, w: int = 640, c: int = 3, dtype: type = np.float32,
) -> ImageConfig:
    return ImageConfig(target_shape=(h, w, c), dtype=dtype)


# ---------------------------------------------------------------------------
# ImageConfig
# ---------------------------------------------------------------------------


class TestImageConfig:
    def test_valid_config(self) -> None:
        cfg = ImageConfig(target_shape=(480, 640, 3))
        assert cfg.target_shape == (480, 640, 3)
        assert cfg.dtype == np.float32

    def test_invalid_target_shape_raises(self) -> None:
        with pytest.raises(ValueError):
            ImageConfig(target_shape=(480, 640))  # 2-tuple, not 3-tuple


# ---------------------------------------------------------------------------
# preprocess_observation_image – valid inputs
# ---------------------------------------------------------------------------


class TestPreprocessValid:
    def test_preprocess_valid_rgb(self) -> None:
        image = _make_image(480, 640, 3)
        cfg = _make_config(480, 640, 3)
        result = preprocess_observation_image(image, cfg)
        assert result.shape == (480, 640, 3)
        assert result.dtype == np.float32

    def test_preprocess_same_shape_preserves_dtype(self) -> None:
        image = _make_image(480, 640, 3)
        cfg = ImageConfig(target_shape=(480, 640, 3), dtype=np.float32)
        result = preprocess_observation_image(image, cfg)
        assert result.dtype == np.float32

    def test_preprocess_uint8_normalized_to_unit_float32(self) -> None:
        """uint8 input is scaled to [0, 1] float32 (deploy_057 image range)."""
        image = _make_image(480, 640, 3).astype(np.uint8)
        cfg = ImageConfig(target_shape=(480, 640, 3), dtype=np.float32)
        result = preprocess_observation_image(image, cfg)
        assert result.dtype == np.float32
        assert result.min() >= 0.0
        assert result.max() <= 1.0

    def test_preprocess_grayscale(self) -> None:
        """Single-channel images should be accepted."""
        image = np.random.randint(0, 256, (480, 640, 1), dtype=np.uint8)
        cfg = ImageConfig(target_shape=(480, 640, 1))
        result = preprocess_observation_image(image, cfg)
        assert result.shape == (480, 640, 1)

    def test_preprocess_float32_input(self) -> None:
        """float32 input with matching config should pass through."""
        image = np.random.rand(480, 640, 3).astype(np.float32)
        cfg = ImageConfig(target_shape=(480, 640, 3), dtype=np.float32)
        result = preprocess_observation_image(image, cfg)
        assert result.shape == (480, 640, 3)
        assert result.dtype == np.float32


# ---------------------------------------------------------------------------
# preprocess_observation_image – invalid inputs
# ---------------------------------------------------------------------------


class TestPreprocessInvalid:
    def test_preprocess_resize_with_cv2(self) -> None:
        """When cv2 is available, image is resized to target_shape."""
        image = _make_image(100, 100, 3)
        cfg = _make_config(480, 640, 3)
        result = preprocess_observation_image(image, cfg)
        assert result.shape == (480, 640, 3)
        assert result.dtype == np.float32

    def test_preprocess_invalid_shape_raises(self) -> None:
        """Non-3D image raises ValueError."""
        image = np.zeros((480, 640), dtype=np.uint8)  # 2D grayscale without channels
        with pytest.raises(ValueError, match="must be 3-dim"):
            preprocess_observation_image(image, _make_config())

    def test_preprocess_non_ndarray_raises(self) -> None:
        with pytest.raises(ValueError, match="must be np.ndarray"):
            preprocess_observation_image([1, 2, 3], _make_config())  # type: ignore[arg-type]

    def test_preprocess_unsupported_channels_raises(self) -> None:
        image = np.zeros((480, 640, 4), dtype=np.uint8)  # RGBA
        with pytest.raises(ValueError, match="Unsupported channel count"):
            preprocess_observation_image(image, _make_config(480, 640, 3))


# ---------------------------------------------------------------------------
# Import without ROS
# ---------------------------------------------------------------------------


class TestImportWithoutROS:
    def test_import_without_ros(self) -> None:
        """Module must be importable without ROS packages."""
        from model_deploy.act.service import image_preprocess as ip

        assert ip.preprocess_observation_image is preprocess_observation_image
        assert ip.ImageConfig is ImageConfig
