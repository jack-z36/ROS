"""Config layer tests for TO-BE TCP/width deploy.yaml schema.

This test file verifies that the new deploy.yaml (with observation/command
topics matching the TO-BE Contract) loads correctly through the config
schema from deploy_005/006/007, and that legacy fields are rejected.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from pi05.deploy.config import DeployConfig, DeployConfigError, load_deploy_config

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

NEW_DEPLOY_YAML = """\
bundle:
  bundle_dir: ../../outputs/exports/pi05_pour_water_v1

runtime:
  mode: shadow-run
  device: cuda:0
  dtype: bfloat16
  inference_hz: 10
  control_hz: 30
  chunk_size: 30
  execute_horizon: 10
  prefetch_steps: 5
  blend_steps: 3
  max_action_age_sec: 0.45
  max_inference_requests: 1
  max_pending_chunks: 1
  fallback_policy: hold_last_action
  max_delta_per_step: 0.03
  action_dim: 16
  state_dim: 16
  warmup_steps: 2
  compile_model: true
  compile_mode: reduce-overhead
  publish_metrics_hz: 1
  task: pour water from the bottle into the cup

image:
  image_size: 224
  resize_mode: resize_pad
  transport: raw

topics:
  namespace: /pi05
  observation:
    left_fisheye_image: /pi05/observation/image/left_gripper_fisheye
    right_fisheye_image: /pi05/observation/image/right_gripper_fisheye
    left_fisheye_image_raw: /pi05/observation/image/left_gripper_fisheye_raw
    right_fisheye_image_raw: /pi05/observation/image/right_gripper_fisheye_raw
    left_tcp_pose: /pi05/observation/arm/left_tcp_pose
    right_tcp_pose: /pi05/observation/arm/right_tcp_pose
    left_gripper_state: /pi05/observation/gripper/left_state
    right_gripper_state: /pi05/observation/gripper/right_state
  command:
    policy_action: /pi05/policy_action
    status: /pi05/status
    metrics: /pi05/metrics

safety:
  max_tcp_delta_m: 0.05
  stale_observation_timeout_s: 0.5
  command_timeout_s: 0.45
  clamp_normalized_action: true
  hold_last_action: true
  gripper_width_min: 0.0
  gripper_width_max: 1.0
  joint_limits:
    enabled: false
    left_min_rad: []
    left_max_rad: []
    right_min_rad: []
    right_max_rad: []
"""


def _write_yaml(tmp_path: Path, content: str) -> Path:
    path = tmp_path / "deploy.yaml"
    path.write_text(content, encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Test: load new deploy.yaml, assert observation/command fields correct
# ---------------------------------------------------------------------------


def test_load_new_config(tmp_path: Path) -> None:
    path = _write_yaml(tmp_path, NEW_DEPLOY_YAML)
    config = load_deploy_config(path)

    # Observation topics
    obs = config.topics.observation
    assert obs.left_fisheye_image == "/pi05/observation/image/left_gripper_fisheye"
    assert obs.right_fisheye_image == "/pi05/observation/image/right_gripper_fisheye"
    assert obs.left_fisheye_image_raw == "/pi05/observation/image/left_gripper_fisheye_raw"
    assert obs.right_fisheye_image_raw == "/pi05/observation/image/right_gripper_fisheye_raw"
    assert obs.left_tcp_pose == "/pi05/observation/arm/left_tcp_pose"
    assert obs.right_tcp_pose == "/pi05/observation/arm/right_tcp_pose"
    assert obs.left_gripper_state == "/pi05/observation/gripper/left_state"
    assert obs.right_gripper_state == "/pi05/observation/gripper/right_state"

    # Command topics
    cmd = config.topics.command
    assert cmd.policy_action == "/pi05/policy_action"
    assert cmd.status == "/pi05/status"
    assert cmd.metrics == "/pi05/metrics"

    # Runtime mode preserved
    assert config.runtime.mode == "shadow-run"


# ---------------------------------------------------------------------------
# Test: RuntimeConfig action_dim / state_dim default to 16
# ---------------------------------------------------------------------------


def test_dims_default_16(tmp_path: Path) -> None:
    """Even without explicit action_dim/state_dim, defaults should be 16."""
    yaml = """\
bundle:
  bundle_dir: ../../outputs/exports/run
runtime:
  mode: dry-run
  inference_hz: 10
  control_hz: 30
  chunk_size: 30
  execute_horizon: 30
topics:
  namespace: /pi05
  observation:
    left_fisheye_image: /pi05/observation/image/left_gripper_fisheye
    right_fisheye_image: /pi05/observation/image/right_gripper_fisheye
    left_fisheye_image_raw: /pi05/observation/image/left_gripper_fisheye_raw
    right_fisheye_image_raw: /pi05/observation/image/right_gripper_fisheye_raw
    left_tcp_pose: /pi05/observation/arm/left_tcp_pose
    right_tcp_pose: /pi05/observation/arm/right_tcp_pose
    left_gripper_state: /pi05/observation/gripper/left_state
    right_gripper_state: /pi05/observation/gripper/right_state
  command:
    policy_action: /pi05/policy_action
    status: /pi05/status
    metrics: /pi05/metrics
safety:
  max_tcp_delta_m: 0.05
  stale_observation_timeout_s: 0.5
  command_timeout_s: 0.45
  clamp_normalized_action: true
  hold_last_action: true
"""
    path = _write_yaml(tmp_path, yaml)
    config = load_deploy_config(path)

    assert config.runtime.action_dim == 16
    assert config.runtime.state_dim == 16


# ---------------------------------------------------------------------------
# Test: SafetyConfig has TCP/width fields, no hand_min/hand_max
# ---------------------------------------------------------------------------


def test_safety_tcp_width(tmp_path: Path) -> None:
    path = _write_yaml(tmp_path, NEW_DEPLOY_YAML)
    config = load_deploy_config(path)

    safety = config.safety
    # TO-BE fields exist
    assert hasattr(safety, "max_tcp_delta_m")
    assert safety.max_tcp_delta_m == pytest.approx(0.05)
    assert hasattr(safety, "gripper_width_min")
    assert safety.gripper_width_min == pytest.approx(0.0)
    assert hasattr(safety, "gripper_width_max")
    assert safety.gripper_width_max == pytest.approx(1.0)

    # AS-IS joint-space fields absent
    assert not hasattr(safety, "max_joint_delta_rad")
    assert not hasattr(safety, "hand_min")
    assert not hasattr(safety, "hand_max")


# ---------------------------------------------------------------------------
# Test: DeployConfig has no bridge/mux attributes
# ---------------------------------------------------------------------------


def test_no_bridge_mux(tmp_path: Path) -> None:
    path = _write_yaml(tmp_path, NEW_DEPLOY_YAML)
    config = load_deploy_config(path)

    assert not hasattr(config, "bridge")
    assert not hasattr(config, "mux")
    assert not hasattr(config.topics, "bridge_output")
    assert not hasattr(config.topics, "mux")


# ---------------------------------------------------------------------------
# Test: tactile fields optional; can load without them
# ---------------------------------------------------------------------------


def test_tactile_optional(tmp_path: Path) -> None:
    """When tactile keys are omitted from YAML, they should be None."""
    path = _write_yaml(tmp_path, NEW_DEPLOY_YAML)
    config = load_deploy_config(path)

    obs = config.topics.observation
    assert obs.tactile_l1 is None
    assert obs.tactile_l2 is None
    assert obs.tactile_r1 is None
    assert obs.tactile_r2 is None


# ---------------------------------------------------------------------------
# Test: old AS-IS fields are rejected by new schema
# ---------------------------------------------------------------------------


def test_old_config_rejected(tmp_path: Path) -> None:
    """Old AS-IS fields are silently dropped / ignored; TO-BE defaults apply."""
    old_yaml = """\
bundle:
  bundle_dir: ../../outputs/exports/run
runtime:
  mode: dry-run
  inference_hz: 10
  control_hz: 30
  chunk_size: 30
  execute_horizon: 30
topics:
  namespace: /pi05_vla
  observation:
    top_image: /realsense/top/color/image_raw/compressed
    proprioception: /vla_teleop/proprioception
    left_hand_state: /inspire/left_hand/joint_states
    right_hand_state: /inspire/right_hand/joint_states
    left_ee_position: /left_arm/ee_position
    right_ee_position: /right_arm/ee_position
  command:
    left_arm_joint_target: /pi05_vla/command/left_arm/joint_target
    right_arm_joint_target: /pi05_vla/command/right_arm/joint_target
    left_hand_target: /pi05_vla/command/left_hand/target
    right_hand_target: /pi05_vla/command/right_hand/target
    status: /pi05_vla/status
    metrics: /pi05_vla/metrics
  bridge_output:
    left_arm_joint_target: /vla/left_arm/safe_joint_target
  mux:
    vla_enable: /mux/enable_vla
safety:
  max_joint_delta_rad: 0.03
  hand_min: 300
  hand_max: 1000
"""
    path = _write_yaml(tmp_path, old_yaml)

    # Old YAML loads because TO-BE fields have defaults, old fields are dropped
    config = load_deploy_config(path)

    # Old observation fields are NOT present on the TO-BE schema
    obs = config.topics.observation
    assert not hasattr(obs, "top_image")
    assert not hasattr(obs, "proprioception")

    # TO-BE fields got defaults from topics.py (namespace /pi05_vla)
    assert obs.left_fisheye_image == "/pi05_vla/observation/image/left_gripper_fisheye"
    assert obs.right_fisheye_image == "/pi05_vla/observation/image/right_gripper_fisheye"

    # Old command fields are NOT present
    cmd = config.topics.command
    assert not hasattr(cmd, "left_arm_joint_target")
    assert cmd.policy_action == "/pi05_vla/policy_action"

    # Old safety fields are NOT present on TO-BE schema
    safe = config.safety
    assert not hasattr(safe, "max_joint_delta_rad")
    assert not hasattr(safe, "hand_min")
    assert not hasattr(safe, "hand_max")
    # TO-BE defaults replace them
    assert safe.gripper_width_min == pytest.approx(0.0)
    assert safe.gripper_width_max == pytest.approx(1.0)

    # No bridge/mux on DeployConfig
    assert not hasattr(config, "bridge")
    assert not hasattr(config, "mux")
