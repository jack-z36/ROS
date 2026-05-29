"""Common-frame pose transformation helpers for Baton Mini odometry."""

from __future__ import annotations

from functools import lru_cache

import numpy as np
from scipy.spatial.transform import Rotation as R

from repo.config.mcap_process_config import FrameAlignmentConfig, TransformConfig


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


def _extrinsic_to_matrix(
    translation_m: tuple[float, float, float],
    rotation_quat_xyzw: tuple[float, float, float, float],
) -> np.ndarray:
    tx, ty, tz = translation_m
    qx, qy, qz, qw = rotation_quat_xyzw
    return _pose_to_matrix(tx, ty, tz, qx, qy, qz, qw)


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


def transform_pose_to_common_camera_frame(
    x: float,
    y: float,
    z: float,
    qx: float,
    qy: float,
    qz: float,
    qw: float,
    frame_alignment: FrameAlignmentConfig,
    hand: str,
) -> tuple[float, float, float, float, float, float, float]:
    """Transform raw pose to common frame camera pose using FrameAlignmentConfig.

    When common_anchor is 'left':
      - left: T_common_camera = T_raw (common_from_left_start is identity)
      - right: T_common_camera = T_common_right_start @ T_raw
    """
    start_from_camera = _pose_to_matrix(x, y, z, qx, qy, qz, qw)

    if hand == "left":
        common_from_start = _extrinsic_to_matrix(
            frame_alignment.common_from_left_start.translation_m,
            frame_alignment.common_from_left_start.rotation_quat_xyzw,
        )
    elif hand == "right":
        common_from_start = _extrinsic_to_matrix(
            frame_alignment.common_from_right_start.translation_m,
            frame_alignment.common_from_right_start.rotation_quat_xyzw,
        )
    else:
        raise ValueError(f'unknown hand "{hand}", expected "left" or "right"')

    common_from_camera = common_from_start @ start_from_camera

    tx, ty, tz = common_from_camera[:3, 3].tolist()
    qx_out, qy_out, qz_out, qw_out = R.from_matrix(common_from_camera[:3, :3]).as_quat()
    return tx, ty, tz, qx_out, qy_out, qz_out, qw_out


def transform_camera_to_common_tcp(
    camera_x: float,
    camera_y: float,
    camera_z: float,
    camera_qx: float,
    camera_qy: float,
    camera_qz: float,
    camera_qw: float,
    frame_alignment: FrameAlignmentConfig,
    hand: str,
) -> tuple[float, float, float, float, float, float, float]:
    """Transform common frame camera pose to common frame TCP pose.

    T_common_tcp = T_common_camera @ T_camera_tcp
    """
    common_from_camera = _pose_to_matrix(camera_x, camera_y, camera_z, camera_qx, camera_qy, camera_qz, camera_qw)

    if hand == "left":
        camera_from_tcp = _extrinsic_to_matrix(
            frame_alignment.camera_from_left_tcp.translation_m,
            frame_alignment.camera_from_left_tcp.rotation_quat_xyzw,
        )
    elif hand == "right":
        camera_from_tcp = _extrinsic_to_matrix(
            frame_alignment.camera_from_right_tcp.translation_m,
            frame_alignment.camera_from_right_tcp.rotation_quat_xyzw,
        )
    else:
        raise ValueError(f'unknown hand "{hand}", expected "left" or "right"')

    common_from_tcp = common_from_camera @ camera_from_tcp

    tx, ty, tz = common_from_tcp[:3, 3].tolist()
    qx_out, qy_out, qz_out, qw_out = R.from_matrix(common_from_tcp[:3, :3]).as_quat()
    return tx, ty, tz, qx_out, qy_out, qz_out, qw_out


def compute_tcp_in_camera(
    camera_x: float,
    camera_y: float,
    camera_z: float,
    camera_qx: float,
    camera_qy: float,
    camera_qz: float,
    camera_qw: float,
    translation_m: tuple[float, float, float],
    rotation_quat_xyzw: tuple[float, float, float, float],
) -> tuple[float, float, float, float, float, float, float]:
    """Compute TCP pose in camera frame from camera pose and fixed extrinsic.

    The TCP-in-camera pose represents the end-effector (TCP) position and
    orientation relative to the Baton Mini camera coordinate frame.  When
    the TCP is rigidly attached to the camera, this is the constant
    extrinsic T_camera_tcp.

    The output can be used as ``pose_in_work`` input to
    ``Algo.rm_algo_workframe2base()``, where the work frame is the
    camera frame.

    The camera pose parameters are accepted for pipeline continuity but
    do *not* affect the result — TCP-in-camera depends only on the
    fixed extrinsic.

    Args:
        camera_x/y/z: Camera position in the source reference frame.
        camera_qx/y/z/w: Camera orientation quaternion (xyzw order).
        translation_m: Extrinsic translation (tx, ty, tz) in metres.
        rotation_quat_xyzw: Extrinsic rotation quaternion (xyzw order).

    Returns:
        Tuple of (x, y, z, qx, qy, qz, qw) representing the TCP pose
        expressed in the camera coordinate frame.

    Raises:
        ValueError: If the extrinsic rotation quaternion is not a unit
            quaternion (norm² deviates from 1 by more than 1e-6).
    """
    qx, qy, qz, qw = rotation_quat_xyzw
    norm_sq = qx * qx + qy * qy + qz * qz + qw * qw
    if abs(norm_sq - 1.0) > 1e-6:
        raise ValueError(
            f"invalid_quaternion: extrinsic rotation is not a unit quaternion "
            f"(norm^2={norm_sq:.10f})"
        )

    tx, ty, tz = translation_m
    return (tx, ty, tz, qx, qy, qz, qw)
