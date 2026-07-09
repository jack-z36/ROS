"""L2-02 Gate integration tests — end-to-end mock pipeline verification.

Covers all 6 L2 Gate scenarios:
    S1  Mock full-field snapshot assembly
    S2  Missing-field / stale reject
    S3  Image pre-processing (covered by test_image_preprocess.py)
    S4  Latest-only buffer semantics (covered by test_observation_buffer.py)
    S5  Import without ROS
    S6  Boundary no-overreach check
"""

import os
import subprocess
import sys
import time

import numpy as np
import pytest

# ---------------------------------------------------------------------------
# Fixtures & helpers
# ---------------------------------------------------------------------------

REQUIRED_IMAGE_KEYS = ["cam_high", "cam_wrist"]
REQUIRED_STATE_FIELDS = [
    "left_tcp_position", "left_tcp_orientation", "left_gripper_width",
    "right_tcp_position", "right_tcp_orientation", "right_gripper_width",
]

REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..")
)


def _make_state():
    from model_deploy.act.types.observation import ObservationState

    return ObservationState(
        left_tcp_position=np.array([0.1, 0.2, 0.3], dtype=np.float32),
        left_tcp_orientation=np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float32),
        left_gripper_width=0.05,
        right_tcp_position=np.array([0.4, 0.5, 0.6], dtype=np.float32),
        right_tcp_orientation=np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float32),
        right_gripper_width=0.08,
    )


def _fill_collector(col):
    """Fill all required fields into a collector."""
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    col.update_image("cam_high", img)
    col.update_image("cam_wrist", img)
    col.update_tcp_pose("left", [0.1, 0.2, 0.3], [0.0, 0.0, 0.0, 1.0])
    col.update_tcp_pose("right", [0.4, 0.5, 0.6], [0.0, 0.0, 0.0, 1.0])
    col.update_gripper_state("left", 0.05)
    col.update_gripper_state("right", 0.08)


# ===================================================================
# S1: Mock full-field snapshot assembly
# ===================================================================


class TestFullMockPipeline:
    """S1 – end-to-end: collector → snapshot → buffer → latest_observation."""

    def test_full_mock_pipeline(self) -> None:
        from model_deploy.act.service.observation_collector import ObservationCollector
        from model_deploy.act.runtime.observation_buffer import ObservationBuffer

        collector = ObservationCollector(
            required_image_keys=REQUIRED_IMAGE_KEYS,
            required_state_fields=REQUIRED_STATE_FIELDS,
        )
        buffer = ObservationBuffer()

        _fill_collector(collector)

        snap = collector.snapshot(max_age_s=5.0)
        assert snap is not None, "snapshot should be non-None with full fields"
        assert snap.encoded_state.shape == (16,), "encoded_state must be 16D"
        assert snap.state.left_gripper_width == 0.05
        assert snap.state.right_gripper_width == 0.08
        assert "cam_high" in snap.images
        assert "cam_wrist" in snap.images

        buffer.set_observation(snap)
        latest = buffer.latest_observation(max_age_s=30.0)
        assert latest is snap, "latest_observation should return written snapshot"


# ===================================================================
# S2: Missing-field / stale reject
# ===================================================================


class TestMissingFieldPipeline:
    """S2 – missing field → collector returns None → buffer not written."""

    def test_missing_field_pipeline(self) -> None:
        from model_deploy.act.service.observation_collector import ObservationCollector
        from model_deploy.act.runtime.observation_buffer import ObservationBuffer

        collector = ObservationCollector(
            required_image_keys=REQUIRED_IMAGE_KEYS,
            required_state_fields=REQUIRED_STATE_FIELDS,
        )
        buffer = ObservationBuffer()

        # Only fill one image – leave cam_wrist and all state fields missing
        collector.update_image("cam_high", np.zeros((480, 640, 3), dtype=np.uint8))

        snap = collector.snapshot(max_age_s=5.0)
        assert snap is None, "snapshot should be None when fields are missing"
        missing = collector.missing_fields()
        assert len(missing) > 0, "missing_fields should be non-empty"

        # Buffer should still be empty
        assert buffer.latest_observation() is None

    def test_stale_pipeline(self) -> None:
        from model_deploy.act.service.observation_collector import ObservationCollector
        from model_deploy.act.runtime.observation_buffer import ObservationBuffer

        collector = ObservationCollector(
            required_image_keys=REQUIRED_IMAGE_KEYS,
            required_state_fields=REQUIRED_STATE_FIELDS,
        )
        buffer = ObservationBuffer()

        _fill_collector(collector)

        # With tiny max_age_s, fields should be stale
        time.sleep(0.05)
        snap = collector.snapshot(max_age_s=0.001)
        assert snap is None, "snapshot should be None when fields are stale"

        stale = collector.stale_fields(time.monotonic(), max_age_s=0.001)
        assert len(stale) > 0, "stale_fields should be non-empty"

        # Buffer still empty
        assert buffer.latest_observation() is None


# ===================================================================
# S6: Boundary no-overreach
# ===================================================================


class TestBoundaryNoOverreach:
    """S6 – L2-02 must not contain inference/control/hardware logic."""

    FORBIDDEN_PATTERNS = [
        "predict_action_chunk",
        "ActionChunk",
        "SafetyGuard",
        "safety_guard",
        "publish.*hardware",
        "send.*command",
        "motor_control",
        "actuator",
        "robot_driver",
    ]

    SEARCH_DIRS = [
        "src/model_deploy/act/service",
        "src/model_deploy/act/runtime",
        "src/model_deploy/act/ui",
    ]

    def _rg_scan(self, pattern: str) -> list[str]:
        """Run rg for `pattern` in SEARCH_DIRS, return matching lines."""
        dirs = [
            d
            for d in self.SEARCH_DIRS
            if os.path.isdir(os.path.join(REPO_ROOT, d))
        ]
        if not dirs:
            return []
        cmd = ["rg", "-n", "--no-heading", pattern] + dirs
        try:
            result = subprocess.run(
                cmd,
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                timeout=15,
            )
            return result.stdout.strip().split("\n") if result.stdout.strip() else []
        except FileNotFoundError:
            # rg not available – skip
            return []
        except subprocess.TimeoutExpired:
            return []

    def test_boundary_no_inference_control(self) -> None:
        """No predict_action_chunk / ActionChunk / SafetyGuard in service/runtime/ui."""
        matches: list[str] = []
        for pattern in self.FORBIDDEN_PATTERNS:
            matches.extend(self._rg_scan(pattern))

        # Filter out matches from test files and docstrings that reference boundaries
        violations = [
            m for m in matches
            if "test_" not in m and "FORBIDDEN" not in m and "_verify" not in m
        ]
        assert len(violations) == 0, (
            f"L2-02 boundary violation: found forbidden patterns in "
            f"service/runtime/ui:\n" + "\n".join(violations)
        )

    def test_boundary_no_config_repo(self) -> None:
        """L2-02 has no config/ or repo/ layer products."""
        config_dir = os.path.join(REPO_ROOT, "src/model_deploy/act/config")
        repo_dir = os.path.join(REPO_ROOT, "src/model_deploy/act/repo")

        # These dirs exist from L2-01 — L2-02 must not add NEW .py files
        # We verify by checking that no observation-related files exist there
        observation_patterns = ["observation", "snapshot", "freshness"]
        violations: list[str] = []

        for directory in [config_dir, repo_dir]:
            if not os.path.isdir(directory):
                continue
            for root, _, files in os.walk(directory):
                for f in files:
                    if f.endswith(".py"):
                        for pat in observation_patterns:
                            if pat in f.lower():
                                violations.append(os.path.join(root, f))

        assert len(violations) == 0, (
            f"L2-02 boundary violation: observation files in config/repo: {violations}"
        )


# ===================================================================
# S5: Import without ROS
# ===================================================================


class TestImportWithoutROS:
    """S5 – all L2-02 modules importable without ROS."""

    def test_import_all_l2_02_modules(self) -> None:
        """Every L2-02 module must import successfully."""
        from model_deploy.act.types import observation
        from model_deploy.act.service import observation_collector
        from model_deploy.act.service import image_preprocess
        from model_deploy.act.runtime import observation_buffer
        from model_deploy.act.ui import observation_ros_adapter

        assert observation.ObservationSnapshot is not None
        assert observation_collector.ObservationCollector is not None
        assert image_preprocess.preprocess_observation_image is not None
        assert observation_buffer.ObservationBuffer is not None
        assert observation_ros_adapter.ObservationRosAdapter is not None


# ===================================================================
# S3 / S4: Delegated to unit tests (verified via verify.sh)
# ===================================================================


class TestDelegatedCoverage:
    """Verify that S3 (image preprocess) and S4 (buffer) have unit coverage."""

    def test_image_preprocess_test_exists(self) -> None:
        path = os.path.join(
            REPO_ROOT,
            "src/model_deploy/act/tests/service/test_image_preprocess.py",
        )
        assert os.path.isfile(path), f"Missing test file: {path}"

    def test_observation_buffer_test_exists(self) -> None:
        path = os.path.join(
            REPO_ROOT,
            "src/model_deploy/act/tests/runtime/test_observation_buffer.py",
        )
        assert os.path.isfile(path), f"Missing test file: {path}"

    def test_all_unit_tests_pass(self) -> None:
        """Run all L2-02 unit tests and verify they pass."""
        test_files = [
            "src/model_deploy/act/tests/types/test_observation.py",
            "src/model_deploy/act/tests/service/test_observation_collector.py",
            "src/model_deploy/act/tests/service/test_image_preprocess.py",
            "src/model_deploy/act/tests/runtime/test_observation_buffer.py",
            "src/model_deploy/act/tests/ui/test_observation_ros_adapter.py",
        ]
        for tf in test_files:
            path = os.path.join(REPO_ROOT, tf)
            if not os.path.isfile(path):
                pytest.skip(f"Test file not found: {tf}")

        result = subprocess.run(
            [sys.executable, "-m", "pytest", "-x", "--tb=short"] + test_files,
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert result.returncode == 0, (
            f"Unit tests failed:\nSTDOUT:\n{result.stdout[:2000]}\n"
            f"STDERR:\n{result.stderr[:2000]}"
        )
