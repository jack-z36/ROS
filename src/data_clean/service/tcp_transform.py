"""Common-frame pose transformation helpers for Baton Mini odometry."""

from __future__ import annotations

from functools import lru_cache

import numpy as np
from scipy.spatial.transform import Rotation as R

from repo.config.mcap_process_config import TransformConfig


def _pose_to_matrix(
    x: float,
    y: float,
    z: float,
    qx: float,
    qy: float,
    qz: float,
    qw: float,
) -> np.ndarray:
    transform = np.eye(4, dtype=np.float64)
    transform[:3, :3] = R.from_quat([qx, qy, qz, qw]).as_matrix()
    transform[:3, 3] = [x, y, z]
    return transform


@lru_cache(maxsize=32)
def _cached_start_from_common(
    x: float,
    y: float,
    z: float,
    qx: float,
    qy: float,
    qz: float,
    qw: float,
) -> tuple[tuple[float, ...], ...]:
    transform = _pose_to_matrix(x, y, z, qx, qy, qz, qw)
    return tuple(tuple(float(value) for value in row) for row in transform)


def build_start_from_common_transform(config: TransformConfig) -> np.ndarray:
    """Return the configured transform from common frame to Baton Mini start frame."""

    translation = config.translation
    rotation = config.rotation_xyzw
    return np.asarray(
        _cached_start_from_common(
            translation.x,
            translation.y,
            translation.z,
            rotation.qx,
            rotation.qy,
            rotation.qz,
            rotation.qw,
        ),
        dtype=np.float64,
    )


def transform_pose_to_common_camera(
    x: float,
    y: float,
    z: float,
    qx: float,
    qy: float,
    qz: float,
    qw: float,
    config: TransformConfig,
) -> tuple[float, float, float, float, float, float, float]:
    """Transform one Baton Mini camera pose from start frame into common frame."""

    start_from_common = build_start_from_common_transform(config)
    common_from_start = np.linalg.inv(start_from_common)
    start_from_camera = _pose_to_matrix(x, y, z, qx, qy, qz, qw)
    common_from_camera = common_from_start @ start_from_camera

    tx, ty, tz = common_from_camera[:3, 3].tolist()
    qx_common, qy_common, qz_common, qw_common = R.from_matrix(common_from_camera[:3, :3]).as_quat()
    return tx, ty, tz, qx_common, qy_common, qz_common, qw_common
