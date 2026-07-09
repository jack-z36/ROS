"""Image pre-processing for observation images.

Pure-function pipeline that converts a decode-d RGB RAM image into the
format expected by the ACT model.  No ROS dependency — the ui layer
handles ROS message decoding before calling this function.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

import numpy as np

try:
    import cv2  # type: ignore[import-untyped]
except ImportError:  # pragma: no cover
    cv2 = None  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# ImageConfig — minimal interface (aligned with L2-01 DeployConfig.image)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ImageConfig:
    """Minimal image pre-processing configuration.

    Fields:
        target_shape:  Desired output (height, width, channels).
        dtype:         Target numpy dtype (e.g. ``np.float32``).
        resize_width:  Target width for resize (optional if matches input).
        resize_height: Target height for resize (optional if matches input).
    """

    target_shape: Tuple[int, int, int]
    dtype: type = np.float32
    resize_width: Optional[int] = None
    resize_height: Optional[int] = None

    def __post_init__(self) -> None:
        if len(self.target_shape) != 3:
            raise ValueError(
                f"target_shape must be (H, W, C), got {self.target_shape}"
            )


# ---------------------------------------------------------------------------
# preprocess_observation_image
# ---------------------------------------------------------------------------


def preprocess_observation_image(
    image: np.ndarray,
    image_config: ImageConfig,
) -> np.ndarray:
    """Pre-process a decoded RGB image for ACT model consumption.

    Args:
        image:        RGB image as ``np.ndarray`` of shape (H, W, 3).
        image_config: Target shape, dtype, and optional resize parameters.

    Returns:
        Pre-processed image array matching ``image_config.target_shape``
        and ``image_config.dtype``.

    Raises:
        ValueError: If input shape, dtype, or channel count is unsupported.
    """
    # --- validate input ---
    if not isinstance(image, np.ndarray):
        raise ValueError(f"image must be np.ndarray, got {type(image).__name__}")

    if image.ndim != 3:
        raise ValueError(f"image must be 3-dim (H, W, C), got shape {image.shape}")

    h, w, c = image.shape
    if c not in (1, 3):
        raise ValueError(f"Unsupported channel count {c}, expected 1 or 3")

    # --- resize if needed ---
    target_h, target_w, target_c = image_config.target_shape

    if image_config.resize_width is not None and image_config.resize_height is not None:
        resize_w = image_config.resize_width
        resize_h = image_config.resize_height
    else:
        resize_w = target_w
        resize_h = target_h

    if (h != resize_h or w != resize_w) and cv2 is not None:
        image = cv2.resize(image, (resize_w, resize_h))
    elif (h != resize_h or w != resize_w) and cv2 is None:
        # Fallback: use numpy slicing/padding for simple resize without cv2
        # For test purposes, we resize by simple cropping or padding
        # In production, cv2 is expected
        pass  # let the shape check below catch mismatches

    # --- convert dtype ---
    if image.dtype != image_config.dtype:
        image = image.astype(image_config.dtype)

    # --- validate output ---
    if image.shape != image_config.target_shape:
        raise ValueError(
            f"Pre-processed image shape {image.shape} does not match "
            f"target_shape {image_config.target_shape}"
        )

    return image
