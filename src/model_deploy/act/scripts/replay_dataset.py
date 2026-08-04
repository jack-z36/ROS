#!/usr/bin/env python3
"""Replay a LeRobot dataset episode on the real RM65 dual-arm robot.

Diagnostic tool that plays back the 16D ``action`` trajectory of one episode
from a LeRobot dataset so the cleaned data can be verified on real hardware.

Two modes:

* ``--dry-run`` (default): pure-RAM numeric validation. Loads the episode,
  reorders training→deploy action layout, checks grippers ∈ [0,1], quaternion
  unit-norm, per-step deltas vs safety limits, and prints a full report. Does
  NOT touch the robot (no ROS, no permit, no command topics). Use this to
  answer "is the cleaned dataset OK?".

* ``--real-run``: drives the real RM65 arms + grippers along the trajectory.
  Reuses the frozen ``SafetyGuard`` + ``ActionPublisher`` contracts and
  publishes the ``/act/command/permit`` heartbeat that the fail-closed
  hardware drivers require. Requires a sourced ROS 2 environment (rclpy).

Key contract (verified against ``lerobot_policy.py``): the dataset ``action``
is in the TRAINING interleaved order
``[L_tcp(0-6), L_grip(7), R_tcp(8-14), R_grip(15)]`` while the deploy
contract is the grouped order
``[L_tcp(0-6), R_tcp(7-13), L_grip(14), R_grip(15)]``. Every frame is
reordered via ``TRAIN_TO_DEPLOY_ACTION_INDEX`` before it reaches the safety
guard / publisher — getting this wrong would scramble the right arm TCP and
both grippers, which is physically dangerous.

Usage (dry-run, no ROS needed)::

    /home/hit/miniforge3/envs/lerobot/bin/python3 \\
        src/model_deploy/act/scripts/replay_dataset.py \\
        --episode 0

Usage (real-run, needs ``source /opt/ros/jazzy/setup.bash`` + workspace)::

    python3 src/model_deploy/act/scripts/replay_dataset.py \\
        --episode 0 --real-run --speed 0.25

This script is a standalone diagnostic — it does not modify the frozen deploy
pipeline (no new ``replay`` mode in the deploy node, no config changes).
"""

from __future__ import annotations

import argparse
import json
import math
import os
import signal
import sys
import time
from pathlib import Path
from typing import Any, Optional

import numpy as np

# ---------------------------------------------------------------------------
# Constants — must stay byte-for-byte identical to the deploy contract
# ---------------------------------------------------------------------------

DEFAULT_DATASET = (
    "/media/hit/BE84424B01016691/umi数据/数据2.0/lerobot/20260729_39_act"
)
DEFAULT_CONFIG = str(
    Path(__file__).resolve().parents[2] / "config_files" / "deploy.yaml"
)

# Training action order [L_tcp7, L_grip, R_tcp7, R_grip] -> deploy order
# [L_tcp7, R_tcp7, L_grip, R_grip].  Source of truth:
# src/model_deploy/act/service/lerobot_policy.py:66-68
TRAIN_TO_DEPLOY_ACTION_INDEX: tuple[int, ...] = (
    0, 1, 2, 3, 4, 5, 6, 8, 9, 10, 11, 12, 13, 14, 7, 15,
)

DEPLOY_DIM_LABELS = (
    "Lx", "Ly", "Lz", "Lqx", "Lqy", "Lqz", "Lqw",
    "Rx", "Ry", "Rz", "Rqx", "Rqy", "Rqz", "Rqw",
    "Lgrip", "Rgrip",
)

# Default deploy-side safety thresholds (from deploy.yaml).  Used by the
# dry-run report so the user can see how badly the per-step deltas exceed
# them.  The real-run path reads the live values from the loaded config.
DEFAULT_MAX_TRANSLATION_STEP_M = 0.008
DEFAULT_MAX_ROTATION_STEP_RAD = 0.04
DEFAULT_MAX_GRIPPER_STEP = 0.2


# ---------------------------------------------------------------------------
# Dataset loading (numpy/pyarrow only — works in the lerobot conda env)
# ---------------------------------------------------------------------------


def load_episode_actions(dataset_dir: str, episode: int) -> tuple[np.ndarray, int]:
    """Load one episode's action trajectory in DEPLOY order.

    Args:
        dataset_dir: LeRobot dataset root (contains ``data/`` and ``meta/``).
        episode: Episode index (0-based; one episode per chunk in this set).

    Returns:
        ``(actions_deploy, fps)`` where ``actions_deploy`` is a
        ``(N, 16)`` float32 array in deploy order
        ``[L_tcp7, R_tcp7, L_grip, R_grip]`` and ``fps`` is the dataset fps.
    """
    import pyarrow.parquet as pq

    dataset_path = Path(dataset_dir).expanduser().resolve()
    parquet_path = dataset_path / "data" / f"chunk-{episode:03d}" / "file-000.parquet"
    if not parquet_path.exists():
        raise FileNotFoundError(
            f"Episode parquet not found: {parquet_path}. "
            f"Check --dataset and --episode (this dataset has one episode per chunk)."
        )

    table = pq.read_table(parquet_path, columns=["action"])
    raw = np.asarray(table["action"].to_pylist(), dtype=np.float32)  # (N,16) TRAIN order
    if raw.ndim != 2 or raw.shape[1] != 16:
        raise ValueError(
            f"Expected action shape (N,16), got {raw.shape} in {parquet_path}"
        )

    # Reorder training -> deploy.
    actions_deploy = raw[:, TRAIN_TO_DEPLOY_ACTION_INDEX].astype(np.float32, copy=True)

    # Read fps from meta/info.json.
    fps = 15
    info_path = dataset_path / "meta" / "info.json"
    if info_path.exists():
        with info_path.open("r", encoding="utf-8") as fh:
            fps = int(json.load(fh).get("fps", fps))

    return actions_deploy, fps


def normalize_quaternions_inplace(actions: np.ndarray) -> np.ndarray:
    """Normalize each arm's xyzw quaternion to unit length (deploy order).

    Operates on a copy.  Mirrors
    ``lerobot_policy.normalize_deploy_action_quaternions``.  Left quaternion
    is indices [3:7], right is [10:14].
    """
    out = actions.astype(np.float32, copy=True)
    for start in (3, 10):
        q = out[:, start:start + 4]
        norm = np.linalg.norm(q, axis=1, keepdims=True)
        norm = np.maximum(norm, 1e-12)
        out[:, start:start + 4] = q / norm
    return out


# ---------------------------------------------------------------------------
# Dry-run numeric report (no ROS) — answers "is the dataset OK?"
# ---------------------------------------------------------------------------


def run_dry_run(actions: np.ndarray, fps: int, episode: int) -> int:
    """Print a full numeric validation report. Returns process exit code."""
    n = actions.shape[0]
    labels = DEPLOY_DIM_LABELS

    print("=" * 72)
    print(f"  DRY-RUN  episode {episode}  |  {n} frames  |  {fps} fps  "
          f"({n / fps:.1f}s)")
    print("=" * 72)

    # 1. finiteness
    finite = bool(np.isfinite(actions).all())
    print(f"\n[1] finiteness:              {'OK (no NaN/Inf)' if finite else 'FAIL (NaN/Inf present)'}")

    # 2. gripper domain [0,1]
    lg = actions[:, 14]
    rg = actions[:, 15]
    lg_ok = (lg.min() >= 0.0) and (lg.max() <= 1.0)
    rg_ok = (rg.min() >= 0.0) and (rg.max() <= 1.0)
    print(f"[2] gripper domain [0,1]:    L [{lg.min():.4f}, {lg.max():.4f}] "
          f"{'OK' if lg_ok else 'FAIL'}  |  R [{rg.min():.4f}, {rg.max():.4f}] "
          f"{'OK' if rg_ok else 'FAIL'}")

    # 3. quaternion unit-norm
    lq_norm = np.linalg.norm(actions[:, 3:7], axis=1)
    rq_norm = np.linalg.norm(actions[:, 10:14], axis=1)
    lq_ok = bool(np.all(np.abs(lq_norm - 1.0) < 1e-3))
    rq_ok = bool(np.all(np.abs(rq_norm - 1.0) < 1e-3))
    print(f"[3] quaternion unit-norm:    L [{lq_norm.min():.5f}, {lq_norm.max():.5f}] "
          f"{'OK' if lq_ok else 'FAIL'}  |  R [{rq_norm.min():.5f}, {rq_norm.max():.5f}] "
          f"{'OK' if rq_ok else 'FAIL'}")

    # 4. per-dim min/max/range table
    print("\n[4] per-dimension min / max / range (DEPLOY order):")
    print(f"    {'dim':<7}{'min':>11}{'max':>11}{'range':>11}")
    for i in range(16):
        lo, hi = float(actions[:, i].min()), float(actions[:, i].max())
        print(f"    {labels[i]:<7}{lo:>11.4f}{hi:>11.4f}{hi - lo:>11.4f}")

    # 5. workspace sanity — TCP z is expected to be negative here. The dataset
    #    TCP pose is produced by the official RealMan SDK
    #    ``rm_algo_workframe2base`` (arm_base_transform.py) using a calibrated
    #    work frame whose origin sits at base-z ≈ +0.19 m, and the TCP reaches
    #    below the arm base toward the table. The deployment driver publishes
    #    and consumes commands in the SAME RealMan base frame with no flip, so
    #    negative z is the correct, recorded pose — NOT a frame mismatch.
    print("\n[5] workspace note:")
    print(f"    L_tcp xyz: x[{actions[:,0].min():.3f},{actions[:,0].max():.3f}] "
          f"y[{actions[:,1].min():.3f},{actions[:,1].max():.3f}] "
          f"z[{actions[:,2].min():.3f},{actions[:,2].max():.3f}]")
    print(f"    R_tcp xyz: x[{actions[:,7].min():.3f},{actions[:,7].max():.3f}] "
          f"y[{actions[:,8].min():.3f},{actions[:,8].max():.3f}] "
          f"z[{actions[:,9].min():.3f},{actions[:,9].max():.3f}]")
    lz_neg = float(actions[:, 2].min()) < 0.0
    rz_neg = float(actions[:, 9].min()) < 0.0
    if lz_neg or rz_neg:
        print("    i  TCP z is negative. This is EXPECTED for this dataset: the TCP")
        print("       pose is in the RM65 arm-base frame (RealMan SDK), where the work")
        print("       frame is calibrated at base-z ~ +0.19 m and the TCP reaches below")
        print("       the arm base toward the table. Verified consistent between the data")
        print("       pipeline (rm_algo_workframe2base) and the deploy driver (no flip).")

    # 6. per-step deltas vs safety limits
    deltas = np.abs(np.diff(actions, axis=0))
    lt = np.linalg.norm(np.diff(actions[:, 0:3], axis=0), axis=1)
    rt = np.linalg.norm(np.diff(actions[:, 7:10], axis=0), axis=1)
    lg_step = np.abs(np.diff(actions[:, 14]))
    rg_step = np.abs(np.diff(actions[:, 15]))
    print("\n[6] per-step deltas vs deploy safety limits:")
    print(f"    L_tcp translation: mean={lt.mean():.5f} m  max={lt.max():.5f} m  "
          f"(limit {DEFAULT_MAX_TRANSLATION_STEP_M})  "
          f"{'OK' if lt.max() <= DEFAULT_MAX_TRANSLATION_STEP_M else 'EXCEEDS (will be clamped)'}")
    print(f"    R_tcp translation: mean={rt.mean():.5f} m  max={rt.max():.5f} m  "
          f"(limit {DEFAULT_MAX_TRANSLATION_STEP_M})  "
          f"{'OK' if rt.max() <= DEFAULT_MAX_TRANSLATION_STEP_M else 'EXCEEDS (will be clamped)'}")
    print(f"    L_gripper step:    max={lg_step.max():.4f}   "
          f"(limit {DEFAULT_MAX_GRIPPER_STEP})  "
          f"{'OK' if lg_step.max() <= DEFAULT_MAX_GRIPPER_STEP else 'EXCEEDS (will be clamped)'}")
    print(f"    R_gripper step:    max={rg_step.max():.4f}   "
          f"(limit {DEFAULT_MAX_GRIPPER_STEP})  "
          f"{'OK' if rg_step.max() <= DEFAULT_MAX_GRIPPER_STEP else 'EXCEEDS (will be clamped)'}")

    # 7. start pose
    print("\n[7] episode start pose (frame 0, DEPLOY order):")
    print(f"    L_tcp: xyz={np.array2string(actions[0,0:3], precision=4)}  "
          f"q(xyzw)={np.array2string(actions[0,3:7], precision=4)}  grip={actions[0,14]:.3f}")
    print(f"    R_tcp: xyz={np.array2string(actions[0,7:10], precision=4)}  "
          f"q(xyzw)={np.array2string(actions[0,10:14], precision=4)}  grip={actions[0,15]:.3f}")
    if args_start_pose_note():
        print("    ℹ  For a faithful real-run, manually move the arms to the above")
        print("       start pose first (the safety guard clamps from the live pose).")

    # summary verdict
    print("\n" + "=" * 72)
    critical_fail = not (finite and lg_ok and rg_ok and lq_ok and rq_ok)
    exceeds = ((lt.max() > DEFAULT_MAX_TRANSLATION_STEP_M)
               or (rt.max() > DEFAULT_MAX_TRANSLATION_STEP_M))
    if critical_fail:
        print("  VERDICT: CRITICAL data problem detected — do NOT real-run until fixed.")
    elif exceeds:
        print("  VERDICT: Data is clean & consistent, but some per-step deltas exceed the")
        print("           safety step limit (see [6]). The SafetyGuard will clamp those on a")
        print("           real-run, distorting the trajectory. Consider --speed < 1 to inspect.")
    else:
        print("  VERDICT: Data looks clean and within safety limits.")
    print("=" * 72)
    print("\nTo drive the real arms (after sourcing ROS 2):")
    print("  python3 " + str(Path(__file__).resolve()) +
          f" --episode {episode} --real-run --speed 0.25")
    return 1 if critical_fail else 0


def args_start_pose_note() -> bool:
    """Placeholder kept simple — always True."""
    return True


# ---------------------------------------------------------------------------
# Real-run: drive the real RM65 via the frozen SafetyGuard + ActionPublisher
# ---------------------------------------------------------------------------


def run_real_run(
    actions: np.ndarray,
    fps: int,
    episode: int,
    speed: float,
    config_path: str,
) -> int:
    """Drive the real arms along ``actions`` at ``fps * speed``.

    Reuses the deploy contracts (SafetyGuard, ActionPublisher, CommandPermit,
    ActionPublishRequest). Publishes the /act/command/permit heartbeat that
    the fail-closed RM65 + gripper drivers require, and wires the RM65 /
    gripper emergency-stop services on shutdown / safety REJECT.
    """
    try:
        import rclpy
        from rclpy.node import Node
        from rclpy.qos import QoSProfile, ReliabilityPolicy
        from geometry_msgs.msg import Pose
        from std_msgs.msg import Float32MultiArray, Float64, String
        from std_srvs.srv import SetBool
    except ImportError as exc:
        print(
            "ERROR: real-run requires rclpy (source your ROS 2 setup). "
            f"Detail: {exc}",
            file=sys.stderr,
        )
        return 2

    # Deploy contract imports (need the model_deploy package on sys.path).
    repo_src = Path(__file__).resolve().parents[3]  # .../src
    if str(repo_src) not in sys.path:
        sys.path.insert(0, str(repo_src))

    from model_deploy.act.config.schema import (
        CommandOutputConfig,
        SafetyConfig,
        TopicsConfig,
        load_deploy_config,
    )
    from model_deploy.act.types.action_publish import (
        ActionPublishRequest,
        CommandPermit,
    )
    from model_deploy.act.types.observation import (
        ObservationSnapshot,
        ObservationState,
    )
    from model_deploy.act.service.safety_guard import SafetyGuard
    from model_deploy.act.ui.action_publisher import ActionPublisher

    n = actions.shape[0]
    cfg = load_deploy_config(config_path, command_output_enabled=True)
    topics = cfg.topics
    safety_cfg = cfg.safety
    guard = SafetyGuard(safety_cfg)
    PERMIT_TOPIC = "/act/command/permit"
    PERMIT_HZ = 20.0
    print(f"[real-run] episode {episode} | {n} frames | {fps} fps | "
          f"speed {speed} | step_dt {1.0 / (fps * speed):.3f}s")
    print("[real-run] SafetyGuard limits: "
          f"trans {safety_cfg.max_translation_step_m} m  "
          f"rot {safety_cfg.max_rotation_step_rad} rad  "
          f"grip {safety_cfg.max_gripper_step}")
    print("[real-run] Waiting for first TCP observation before moving...")

    rclpy.init()
    node = Node("act_replay_dataset")

    # --- live observation state (thread-safe-ish: single-threaded executor) ---
    obs_state: dict[str, Any] = {
        "left_tcp": None, "right_tcp": None,
        "left_grip": None, "right_grip": None,
    }

    def _on_left_tcp(msg: Pose) -> None:
        obs_state["left_tcp"] = msg
    def _on_right_tcp(msg: Pose) -> None:
        obs_state["right_tcp"] = msg
    def _on_left_grip(msg: Any) -> None:
        try:
            obs_state["left_grip"] = float(getattr(msg, "data",
                                       getattr(msg.position, "x", msg)))
        except Exception:
            pass
    def _on_right_grip(msg: Any) -> None:
        try:
            obs_state["right_grip"] = float(getattr(msg, "data",
                                        getattr(msg.position, "x", msg)))
        except Exception:
            pass

    node.create_subscription(Pose, topics.observation.left_tcp_pose, _on_left_tcp, 10)
    node.create_subscription(Pose, topics.observation.right_tcp_pose, _on_right_tcp, 10)
    node.create_subscription(Pose, topics.observation.left_gripper_state, _on_left_grip, 10)
    node.create_subscription(Pose, topics.observation.right_gripper_state, _on_right_grip, 10)

    # --- command publisher (reuses frozen ActionPublisher) ---
    command_output = CommandOutputConfig(command_output_enabled=True)
    publisher = ActionPublisher(node, command_output, topics)

    # --- permit heartbeat publisher (REQUIRED for fail-closed drivers) ---
    try:
        from act_interfaces.msg import CommandPermit as PermitMsg
    except ImportError:
        print("ERROR: act_interfaces.msg.CommandPermit not found. "
              "Build the act_interfaces package first.", file=sys.stderr)
        rclpy.shutdown()
        return 3
    permit_pub = node.create_publisher(PermitMsg, PERMIT_TOPIC, 10)
    permit_allowed = {"value": True}

    def _publish_permit() -> None:
        msg = PermitMsg()
        msg.header.stamp = node.get_clock().now().to_msg()
        msg.allowed = bool(permit_allowed["value"])
        msg.reason_code = "" if msg.allowed else "replay_shutdown"
        permit_pub.publish(msg)
    permit_timer = node.create_timer(1.0 / PERMIT_HZ, _publish_permit)

    # --- emergency-stop clients ---
    rm65_estop = node.create_client(SetBool, "/hardware/rm65/emergency_stop")
    grip_estop = node.create_client(SetBool, "/hardware/gripper/emergency_stop")

    def _emergency_stop() -> None:
        permit_allowed["value"] = False
        for client in (rm65_estop, grip_estop):
            if client.service_is_ready():
                try:
                    client.call_async(SetBool.Request(data=True))
                except Exception:
                    pass
        print("[real-run] EMERGENCY STOP issued (RM65 + gripper).")

    # --- graceful shutdown on SIGINT / SIGTERM ---
    shutdown_flag = {"done": False}
    def _signal_handler(signum, frame):
        if not shutdown_flag["done"]:
            print(f"\n[real-run] signal {signum} received, stopping...")
            shutdown_flag["done"] = True
    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    # wait for first TCP observation on both arms
    wait_start = time.monotonic()
    while (obs_state["left_tcp"] is None or obs_state["right_tcp"] is None):
        rclpy.spin_once(node, timeout_sec=0.05)
        _publish_permit()
        if time.monotonic() - wait_start > 10.0:
            print("ERROR: timed out waiting for TCP observation. "
                  "Are the rm65 + observation nodes running?", file=sys.stderr)
            _emergency_stop()
            rclpy.shutdown()
            return 4
        if shutdown_flag["done"]:
            _emergency_stop()
            rclpy.shutdown()
            return 0
    print("[real-run] Observation ready. Beginning replay in 3s (Ctrl-C to abort)...")
    for countdown in (3, 2, 1):
        print(f"  {countdown}...")
        end = time.monotonic() + 1.0
        while time.monotonic() < end:
            rclpy.spin_once(node, timeout_sec=0.05)
            _publish_permit()

    def _build_snapshot() -> Optional[ObservationSnapshot]:
        lt = obs_state["left_tcp"]; rt = obs_state["right_tcp"]
        if lt is None or rt is None:
            return None
        lpos = np.array([lt.position.x, lt.position.y, lt.position.z], dtype=np.float32)
        lquat = np.array([lt.orientation.x, lt.orientation.y, lt.orientation.z, lt.orientation.w], dtype=np.float32)
        rpos = np.array([rt.position.x, rt.position.y, rt.position.z], dtype=np.float32)
        rquat = np.array([rt.orientation.x, rt.orientation.y, rt.orientation.z, rt.orientation.w], dtype=np.float32)
        lg = float(obs_state.get("left_grip") or 0.0)
        rg = float(obs_state.get("right_grip") or 0.0)
        state = ObservationState(
            left_tcp_position=lpos, left_tcp_orientation=lquat,
            left_gripper_width=lg,
            right_tcp_position=rpos, right_tcp_orientation=rquat,
            right_gripper_width=rg,
        )
        encoded = np.concatenate([lpos, lquat, [lg], rpos, rquat, [rg]]).astype(np.float32)
        return ObservationSnapshot(
            images={}, state=state, encoded_state=encoded,
            captured_at_s=time.monotonic(),
        )

    # main replay loop
    previous_safe = None
    step_dt = 1.0 / (fps * speed)
    rejected_count = 0
    last_i = -1
    for i in range(n):
        if shutdown_flag["done"]:
            break
        next_deadline = time.monotonic() + step_dt
        # pump ROS callbacks + permit until the frame deadline
        while time.monotonic() < next_deadline and not shutdown_flag["done"]:
            rclpy.spin_once(node, timeout_sec=min(0.02, max(0.0, next_deadline - time.monotonic())))
        if shutdown_flag["done"]:
            break
        _publish_permit()

        candidate = actions[i]
        snapshot = _build_snapshot()
        result = guard.filter_action(
            candidate,
            previous_safe_action=previous_safe,
            latest_observation=snapshot,
        )
        if result.status.value == "REJECTED" or result.action is None:
            rejected_count += 1
            codes = ",".join(f.code.value for f in result.findings)
            print(f"  [{i+1}/{n}] REJECTED ({codes}) — issuing E-stop.")
            _emergency_stop()
            break
        previous_safe = result.action
        permit = CommandPermit(allowed=True)
        now_mono = time.monotonic()
        now_ros = node.get_clock().now().nanoseconds * 1e-9
        req = ActionPublishRequest(
            action_id=f"replay-ep{episode}-{i+1}",
            safety_result=result,
            command_permit=permit,
            ros_time_s=float(now_ros),
            monotonic_s=float(now_mono),
        )
        pub_result = publisher.publish(req)
        if i % 20 == 0 or i == n - 1:
            print(f"  [{i+1}/{n}] safety={result.status.value} "
                  f"outcome={pub_result.outcome.value} "
                  f"cmds={pub_result.command_publish_count}")
        last_i = i

    frames_sent = last_i + 1
    print(f"[real-run] done. frames sent={frames_sent} rejected={rejected_count}")
    # park: stop the permit so the drivers go fail-closed, then e-stop.
    permit_allowed["value"] = False
    _publish_permit()
    _emergency_stop()
    time.sleep(0.3)
    rclpy.spin_once(node, timeout_sec=0.1)
    rclpy.shutdown()
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="replay_dataset.py",
        description="Replay a LeRobot dataset episode on the real RM65 dual-arm "
                    "robot (dry-run validates data; real-run drives the arms).",
    )
    p.add_argument("--dataset", default=DEFAULT_DATASET,
                   help=f"LeRobot dataset root (default: {DEFAULT_DATASET})")
    p.add_argument("--episode", type=int, default=0,
                   help="Episode index (default 0; one episode per chunk)")
    mode = p.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", default=True,
                      help="Numeric validation only, no robot motion (default).")
    mode.add_argument("--real-run", dest="real_run", action="store_true",
                      help="Drive the real arms (requires ROS 2 / rclpy).")
    p.add_argument("--speed", type=float, default=1.0,
                   help="Playback speed multiplier (default 1.0; try 0.25 for "
                        "a cautious first real-run).")
    p.add_argument("--fps", type=int, default=0,
                   help="Override dataset fps (default: read from meta/info.json).")
    p.add_argument("--config", default=DEFAULT_CONFIG,
                   help=f"deploy.yaml path (default: {DEFAULT_CONFIG})")
    return p


def main(argv: Optional[list[str]] = None) -> int:
    args = build_arg_parser().parse_args(argv)
    actions, fps = load_episode_actions(args.dataset, args.episode)
    if args.fps > 0:
        fps = args.fps
    # Always normalize quaternions before either path (mirrors deploy wrapper).
    actions = normalize_quaternions_inplace(actions)

    if args.real_run:
        return run_real_run(actions, fps, args.episode, args.speed, args.config)
    return run_dry_run(actions, fps, args.episode)


if __name__ == "__main__":
    raise SystemExit(main())
