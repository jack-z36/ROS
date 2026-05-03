"""Pose transformation helpers derived from FastUMI's TCP processing logic."""

from __future__ import annotations

from functools import lru_cache

import numpy as np
from scipy.spatial.transform import Rotation as R

from core.mcap_process_config import TransformConfig


@lru_cache(maxsize=32)
def _cached_base_transform(
    base_x: float,
    base_y: float,
    base_z: float,
    base_roll_deg: float,
    base_pitch_deg: float,
    base_yaw_deg: float,
) -> tuple[tuple[float, ...], ...]:
    base_roll, base_pitch, base_yaw = np.deg2rad([base_roll_deg, base_pitch_deg, base_yaw_deg])
    rotation_base_to_local = R.from_euler("xyz", [base_roll, base_pitch, base_yaw]).as_matrix()
    transform = np.eye(4)
    transform[:3, :3] = rotation_base_to_local
    transform[:3, 3] = [base_x, base_y, base_z]
    return tuple(tuple(float(value) for value in row) for row in transform)


def build_base_to_local_transform(config: TransformConfig) -> np.ndarray:
    """Return the cached homogeneous transform from base to local(camera) frame."""

    return np.asarray(
        _cached_base_transform(
            config.base_position.x,
            config.base_position.y,
            config.base_position.z,
            config.base_orientation_deg.roll,
            config.base_orientation_deg.pitch,
            config.base_orientation_deg.yaw,
        ),
        dtype=np.float64,
    )


def transform_to_base_quat(
    x: float,
    y: float,
    z: float,
    qx: float,
    qy: float,
    qz: float,
    qw: float,
    base_to_local_transform: np.ndarray,
) -> tuple[float, float, float, float, float, float, float]:
    """Mirror the original FastUMI frame transform from local camera coordinates into base frame."""

    rotation_local = R.from_quat([qx, qy, qz, qw]).as_matrix()
    local_transform = np.eye(4)
    local_transform[:3, :3] = rotation_local
    local_transform[:3, 3] = [x, y, z]

    base_rotation = np.dot(local_transform[:3, :3], base_to_local_transform[:3, :3])
    base_position = base_to_local_transform[:3, 3] + local_transform[:3, 3]
    qx_base, qy_base, qz_base, qw_base = R.from_matrix(base_rotation).as_quat()
    x_base, y_base, z_base = base_position
    return x_base, y_base, z_base, qx_base, qy_base, qz_base, qw_base


def transform_pose_to_tcp(
    x: float,
    y: float,
    z: float,
    qx: float,
    qy: float,
    qz: float,
    qw: float,
    config: TransformConfig,
) -> tuple[float, float, float, float, float, float, float]:
    """Apply the documented FastUMI TCP transform to a single pose sample."""

    transform = build_base_to_local_transform(config)
    offset = config.tcp_offset

    x_local = x - offset.x
    y_local = y
    z_local = z + offset.z

    x_base, y_base, z_base, qx_base, qy_base, qz_base, qw_base = transform_to_base_quat(
        x_local,
        y_local,
        z_local,
        qx,
        qy,
        qz,
        qw,
        transform,
    )

    orientation_matrix = R.from_quat([qx_base, qy_base, qz_base, qw_base]).as_matrix()
    position = np.array([x_base, y_base, z_base], dtype=np.float64)
    position += offset.x * orientation_matrix[:, 2]
    position -= offset.z * orientation_matrix[:, 0]
    x_tcp, y_tcp, z_tcp = position.tolist()
    return x_tcp, y_tcp, z_tcp, qx_base, qy_base, qz_base, qw_base

