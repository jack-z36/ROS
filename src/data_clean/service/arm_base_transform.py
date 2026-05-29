"""Arm-base TCP pose transform via RealMan SDK official API.

This module provides the official RealMan SDK adapter for converting
TCP-in-camera poses to TCP-in-arm-base poses.  It encapsulates the two
SDK calls that form the second stage of the two-stage transform pipeline:

    Stage 1 (tcp_transform.py):  camera pose → TCP in camera frame
    Stage 2 (this module):       TCP in camera frame → TCP in arm base

The official API chain is:
    Algo.rm_algo_pos2matrix(work_frame_euler_pose)       → work frame 4×4 matrix
    Algo.rm_algo_quaternion2euler(tcp_quat_sdk)           → tcp Euler angles
    Algo.rm_algo_workframe2base(matrix, tcp_pose_in_work) → tcp pose in base
    Algo.rm_algo_euler2quaternion(result_euler)           → result quaternion

Experimental SDK semantics (verified by identity + round-trip tests):

    ``rm_algo_pos2matrix([x,y,z,rx,ry,rz])`` creates a 4×4 matrix *M*
    that maps from base to work:  ``p_work = M · p_base``.

    ``rm_algo_workframe2base(M, p_work)`` computes
    ``p_base = M⁻¹ · p_work``, i.e. the tool-end (TCP) pose expressed
    in the arm base coordinate frame.

    ``rm_algo_base2workframe(M, p_base)`` returns the **base-frame
    origin** expressed in work-frame coordinates, *not* the tool-end
    pose in work frame.  Therefore a naive round-trip via base2workframe
    is not valid for tool poses (see test_round_trip_semantics).
"""

from __future__ import annotations

from schemas.arm_base_pose import (
    ArmBaseTcpPose,
    FrameIdType,
    HandType,
    WorkFrameInArmBasePose,
)


def compute_arm_base_tcp_pose(
    tcp_x: float,
    tcp_y: float,
    tcp_z: float,
    tcp_qx: float,
    tcp_qy: float,
    tcp_qz: float,
    tcp_qw: float,
    work_frame: WorkFrameInArmBasePose,
    algo: object,
) -> ArmBaseTcpPose:
    """Convert TCP-in-camera pose to TCP-in-arm-base pose via RealMan SDK.

    This is the second stage of the two-stage pipeline.  The TCP-in-camera
    pose (typically from ``compute_tcp_in_camera``) is treated as the
    tool-end pose **in the work frame** (the camera frame serves as the
    "work frame" for this conversion).

    Args:
        tcp_x/y/z: TCP position in metres (camera / work frame).
        tcp_qx/y/z/w: TCP orientation as ROS-ordered quaternion
            (x, y, z, w).  This is the format used by ``compute_tcp_in_camera``.
        work_frame: User-defined work frame expressed in the corresponding
            arm base coordinate frame.
        algo: An initialised ``Algo`` instance (RealMan SDK).
            Must be created with the correct arm model and force type,
            e.g. ``Algo(RM_MODEL_RM_65_E, RM_MODEL_RM_B_E)``.

    Returns:
        :class:`ArmBaseTcpPose` with the TCP pose expressed in the
        corresponding arm base coordinate frame (``left_arm_base``
        or ``right_arm_base``).

    Raises:
        ValueError: If the ``work_frame`` has an invalid hand value
            (propagated from ``WorkFrameInArmBasePose`` validation).

    Notes:
        Unstable / non-deterministic quaternion ↔ Euler conversion at
        gimbal-lock orientations (±90° pitch) is a known limitation of
        the Euler-angle representation.  The SDK's internal conversion
        is used, so any such behaviour is inherited.
    """
    # ====================================================================
    # 1. WorkFrameInArmBasePose → SDK euler pose list [x,y,z,rx,ry,rz]
    #    The orientation is stored as ROS quaternion (xyzw).  Convert to
    #    SDK wxyz order, then to euler via the SDK.
    # ====================================================================
    wf_px = work_frame.position_m["x"]
    wf_py = work_frame.position_m["y"]
    wf_pz = work_frame.position_m["z"]

    wf_qx = work_frame.orientation["x"]
    wf_qy = work_frame.orientation["y"]
    wf_qz = work_frame.orientation["z"]
    wf_qw = work_frame.orientation["w"]

    # ROS (xyzw) → SDK (wxyz)
    wf_euler: list[float] = algo.rm_algo_quaternion2euler(
        [wf_qw, wf_qx, wf_qy, wf_qz]
    )

    work_frame_pose: list[float] = [wf_px, wf_py, wf_pz, wf_euler[0], wf_euler[1], wf_euler[2]]
    work_matrix = algo.rm_algo_pos2matrix(work_frame_pose)

    # ====================================================================
    # 2. TCP quaternion (ROS xyzw) → SDK euler for rm_pose_t
    # ====================================================================
    tcp_euler: list[float] = algo.rm_algo_quaternion2euler(
        [tcp_qw, tcp_qx, tcp_qy, tcp_qz]
    )

    # ====================================================================
    # 3. Build rm_pose_t for the TCP in work frame
    # ====================================================================
    # Import here to avoid forcing SDK import on module load
    from Robotic_Arm.rm_ctypes_wrap import rm_euler_t, rm_pose_t, rm_position_t

    pose_in_work = rm_pose_t()
    pose_in_work.position = rm_position_t(tcp_x, tcp_y, tcp_z)
    pose_in_work.euler = rm_euler_t(tcp_euler[0], tcp_euler[1], tcp_euler[2])

    # ====================================================================
    # 4. Call workframe2base → TCP in arm base (Euler angles)
    # ====================================================================
    result_pose: list[float] = algo.rm_algo_workframe2base(work_matrix, pose_in_work, flag=1)

    base_x, base_y, base_z = result_pose[0], result_pose[1], result_pose[2]
    base_rx, base_ry, base_rz = result_pose[3], result_pose[4], result_pose[5]

    # ====================================================================
    # 5. Convert result Euler → SDK quaternion (wxyz) → ROS quaternion (xyzw)
    # ====================================================================
    base_quat_sdk: list[float] = algo.rm_algo_euler2quaternion([base_rx, base_ry, base_rz])
    # SDK returns [w, x, y, z]; ROS convention is [x, y, z, w]
    base_qw, base_qx, base_qy, base_qz = base_quat_sdk

    # ====================================================================
    # 6. Determine frame_id from work_frame hand
    # ====================================================================
    hand_value = work_frame.hand if isinstance(work_frame.hand, str) else work_frame.hand.value
    if hand_value == HandType.LEFT.value:
        frame_id = FrameIdType.LEFT_ARM_BASE
    else:
        frame_id = FrameIdType.RIGHT_ARM_BASE

    return ArmBaseTcpPose(
        hand=work_frame.hand,
        frame_id=frame_id,
        position_m={"x": float(base_x), "y": float(base_y), "z": float(base_z)},
        orientation={
            "x": float(base_qx),
            "y": float(base_qy),
            "z": float(base_qz),
            "w": float(base_qw),
        },
        official_api="Algo.rm_algo_workframe2base",
    )
