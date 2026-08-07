"""Unit tests for RelativeTcpActionDecoder.

Covers the nine required cases from the refactor plan:
1. Identity relative pose recovers the reference pose.
2. Known translation relative pose recovers the absolute translation.
3. Known rotation relative quaternion composes correctly.
4. All chunk rows share the same reference.
5. Row k does not depend on row k-1 (no accumulation).
6. Left and right arms use their own reference independently.
7. Gripper absolute values pass through unchanged.
8. Non-unit relative quaternions are handled.
9. Zero / NaN / Inf quaternion and wrong-shape inputs are rejected.
"""

from __future__ import annotations

import numpy as np
import pytest

from model_deploy.act.service.relative_tcp_action_decoder import (
    RelativeTcpActionDecoder,
)
from model_deploy.act.types.action_chunk import ActionChunk
from model_deploy.act.types.action_representation import ActionRepresentationSpec
from model_deploy.act.types.observation import ObservationState
from model_deploy.act.types.relative_action_chunk import RelativeActionChunk


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_REL_SPEC = ActionRepresentationSpec(
    arm_action_type="relative_tcp_pose",
    chunk_reference="inference_observation",
    translation_frame="tcp_local",
    rotation_representation="quaternion_xyzw",
    gripper_action_type="absolute",
)


def _make_decoder() -> RelativeTcpActionDecoder:
    return RelativeTcpActionDecoder(_REL_SPEC)


def _state(
    *,
    l_pos=(0.0, 0.0, 0.0),
    l_quat=(0.0, 0.0, 0.0, 1.0),
    r_pos=(0.0, 0.0, 0.0),
    r_quat=(0.0, 0.0, 0.0, 1.0),
) -> ObservationState:
    """Build an ObservationState; default is identity pose for both arms."""
    return ObservationState(
        left_tcp_position=np.array(l_pos, dtype=np.float32),
        left_tcp_orientation=np.array(l_quat, dtype=np.float32),
        left_gripper_width=0.0,
        right_tcp_position=np.array(r_pos, dtype=np.float32),
        right_tcp_orientation=np.array(r_quat, dtype=np.float32),
        right_gripper_width=0.0,
    )


def _chunk(rows: list[np.ndarray]) -> RelativeActionChunk:
    """Build a RelativeActionChunk from a list of 16D rows."""
    arr = np.array(rows, dtype=np.float32)
    assert arr.shape[1] == 16
    return RelativeActionChunk(actions=arr)


def _identity_row() -> np.ndarray:
    """A 16D relative row that is identity for both arms + zero grippers.

    Identity translation (0,0,0) and identity quaternion xyzw=(0,0,0,1).
    """
    row = np.zeros(16, dtype=np.float32)
    row[3:7] = (0.0, 0.0, 0.0, 1.0)   # left identity quat
    row[10:14] = (0.0, 0.0, 0.0, 1.0)  # right identity quat
    return row


# ---------------------------------------------------------------------------
# Construction / representation-spec validation
# ---------------------------------------------------------------------------


class TestConstruction:
    def test_accepts_expected_relative_spec(self) -> None:
        d = _make_decoder()
        assert d.action_representation_spec is _REL_SPEC

    def test_rejects_non_relative_spec(self) -> None:
        abs_spec = ActionRepresentationSpec(
            arm_action_type="absolute_tcp_pose",
            chunk_reference="inference_observation",
            translation_frame="tcp_local",
            rotation_representation="quaternion_xyzw",
            gripper_action_type="absolute",
        )
        with pytest.raises(ValueError, match="relative-action representation"):
            RelativeTcpActionDecoder(abs_spec)

    def test_rejects_wrong_type(self) -> None:
        with pytest.raises(TypeError):
            RelativeTcpActionDecoder("not a spec")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Case 1: identity relative pose recovers reference pose
# ---------------------------------------------------------------------------


class TestIdentityRecoversReference:
    def test_identity_relative_at_identity_reference(self) -> None:
        dec = _make_decoder()
        ref = _state()
        rel = _chunk([_identity_row()])
        out = dec.decode(rel, ref)

        assert isinstance(out, ActionChunk)
        # At identity reference, identity relative -> identity absolute.
        np.testing.assert_allclose(out.actions[0, 0:3], [0, 0, 0], atol=1e-6)
        np.testing.assert_allclose(out.actions[0, 3:7], [0, 0, 0, 1], atol=1e-6)

    def test_identity_relative_at_nonzero_reference_recovers_reference(self) -> None:
        """Identity relative action should reproduce the reference pose exactly."""
        dec = _make_decoder()
        ref = _state(
            l_pos=(0.1, -0.2, 0.3),
            l_quat=(0.0, 0.0, 0.0, 1.0),
            r_pos=(0.5, 0.6, -0.7),
            r_quat=(0.0, 0.0, 0.0, 1.0),
        )
        rel = _chunk([_identity_row()])
        out = dec.decode(rel, ref)

        # Left arm should equal the reference.
        np.testing.assert_allclose(out.actions[0, 0:3], [0.1, -0.2, 0.3], atol=1e-6)
        np.testing.assert_allclose(out.actions[0, 3:7], [0, 0, 0, 1], atol=1e-6)
        # Right arm should equal the reference.
        np.testing.assert_allclose(out.actions[0, 7:10], [0.5, 0.6, -0.7], atol=1e-6)
        np.testing.assert_allclose(out.actions[0, 10:14], [0, 0, 0, 1], atol=1e-6)


# ---------------------------------------------------------------------------
# Case 2: known translation
# ---------------------------------------------------------------------------


class TestKnownTranslation:
    def test_translation_at_identity_reference(self) -> None:
        """p_abs = p_ref + R(I) @ p_rel = p_rel when ref is identity."""
        dec = _make_decoder()
        ref = _state()
        row = _identity_row()
        row[0:3] = (0.1, 0.2, 0.3)  # left relative translation
        row[7:10] = (-0.4, 0.5, -0.6)  # right relative translation
        out = dec.decode(_chunk([row]), ref)

        np.testing.assert_allclose(out.actions[0, 0:3], [0.1, 0.2, 0.3], atol=1e-6)
        np.testing.assert_allclose(out.actions[0, 7:10], [-0.4, 0.5, -0.6], atol=1e-6)

    def test_translation_rotated_by_reference_frame(self) -> None:
        """When the reference is a 90-deg rotation about z, a local +x relative
        translation becomes a world +y absolute translation."""
        dec = _make_decoder()
        # 90 deg about z: xyzw = (0, 0, sin45, cos45).
        rot_z90 = np.array([0.0, 0.0, np.sqrt(2) / 2, np.sqrt(2) / 2], dtype=np.float32)
        ref = _state(l_quat=tuple(rot_z90), r_quat=tuple(rot_z90))
        row = _identity_row()
        row[0:3] = (1.0, 0.0, 0.0)  # left relative +x in TCP-local frame
        row[7:10] = (1.0, 0.0, 0.0)  # right relative +x in TCP-local frame
        out = dec.decode(_chunk([row]), ref)

        # R(z90) @ (1,0,0) = (0,1,0).
        np.testing.assert_allclose(out.actions[0, 0:3], [0.0, 1.0, 0.0], atol=1e-5)
        np.testing.assert_allclose(out.actions[0, 7:10], [0.0, 1.0, 0.0], atol=1e-5)


# ---------------------------------------------------------------------------
# Case 3: known rotation composition
# ---------------------------------------------------------------------------


class TestKnownRotation:
    def test_relative_rotation_composes_with_reference(self) -> None:
        """q_abs = q_ref ⊗ q_rel. A 90-deg-z ref composed with a 90-deg-z
        relative yields a 180-deg-z absolute."""
        dec = _make_decoder()
        half = np.sqrt(2) / 2
        # 90 deg about z: xyzw = (0,0,s,c)
        q90 = np.array([0.0, 0.0, half, half], dtype=np.float32)
        ref = _state(l_quat=tuple(q90), r_quat=tuple(q90))

        row = _identity_row()
        row[3:7] = q90  # left relative 90-deg-z
        row[10:14] = q90  # right relative 90-deg-z
        out = dec.decode(_chunk([row]), ref)

        # 180 deg about z: xyzw = (0,0,1,0).
        np.testing.assert_allclose(out.actions[0, 3:7], [0.0, 0.0, 1.0, 0.0], atol=1e-5)
        np.testing.assert_allclose(out.actions[0, 10:14], [0.0, 0.0, 1.0, 0.0], atol=1e-5)

    def test_identity_relative_keeps_reference_rotation(self) -> None:
        dec = _make_decoder()
        rot_z90 = np.array([0.0, 0.0, np.sqrt(2) / 2, np.sqrt(2) / 2], dtype=np.float32)
        ref = _state(l_quat=tuple(rot_z90), r_quat=tuple(rot_z90))
        out = dec.decode(_chunk([_identity_row()]), ref)

        np.testing.assert_allclose(out.actions[0, 3:7], rot_z90, atol=1e-6)
        np.testing.assert_allclose(out.actions[0, 10:14], rot_z90, atol=1e-6)


# ---------------------------------------------------------------------------
# Case 4 & 5: all rows share the same reference; no accumulation
# ---------------------------------------------------------------------------


class TestChunkSharedReference:
    def test_all_rows_use_same_reference(self) -> None:
        """Two rows with the same relative translation both land at the same
        absolute position (since reference is shared, not accumulated)."""
        dec = _make_decoder()
        ref = _state(l_pos=(1.0, 2.0, 3.0), r_pos=(4.0, 5.0, 6.0))
        r1 = _identity_row(); r1[0:3] = (0.1, 0.0, 0.0); r1[7:10] = (0.0, 0.2, 0.0)
        r2 = _identity_row(); r2[0:3] = (0.1, 0.0, 0.0); r2[7:10] = (0.0, 0.2, 0.0)
        out = dec.decode(_chunk([r1, r2]), ref)

        # Both rows identical because reference is shared.
        np.testing.assert_allclose(out.actions[0, 0:3], [1.1, 2.0, 3.0], atol=1e-6)
        np.testing.assert_allclose(out.actions[1, 0:3], [1.1, 2.0, 3.0], atol=1e-6)
        np.testing.assert_allclose(out.actions[0, 7:10], [4.0, 5.2, 6.0], atol=1e-6)
        np.testing.assert_allclose(out.actions[1, 7:10], [4.0, 5.2, 6.0], atol=1e-6)

    def test_second_row_does_not_depend_on_first(self) -> None:
        """A large relative action in row 0 must not affect row 1's result."""
        dec = _make_decoder()
        ref = _state(l_pos=(0.0, 0.0, 0.0))
        big = _identity_row(); big[0:3] = (10.0, 0.0, 0.0)
        small = _identity_row(); small[0:3] = (0.1, 0.0, 0.0)
        out = dec.decode(_chunk([big, small]), ref)

        # Row 1 lands at 0.1, not 10.1 — proving no accumulation.
        np.testing.assert_allclose(out.actions[1, 0:3], [0.1, 0.0, 0.0], atol=1e-6)

        # Reversing the order gives the same per-row results.
        out_rev = dec.decode(_chunk([small, big]), ref)
        np.testing.assert_allclose(out_rev.actions[0, 0:3], [0.1, 0.0, 0.0], atol=1e-6)
        np.testing.assert_allclose(out_rev.actions[1, 0:3], [10.0, 0.0, 0.0], atol=1e-6)


# ---------------------------------------------------------------------------
# Case 6: left and right arms use their own reference independently
# ---------------------------------------------------------------------------


class TestIndependentArmReferences:
    def test_left_and_right_use_separate_references(self) -> None:
        dec = _make_decoder()
        ref = _state(
            l_pos=(1.0, 0.0, 0.0),
            r_pos=(0.0, 0.0, 10.0),
        )
        row = _identity_row()
        row[0:3] = (0.5, 0.0, 0.0)   # left relative +x
        row[7:10] = (0.0, 0.0, 0.5)  # right relative +z
        out = dec.decode(_chunk([row]), ref)

        np.testing.assert_allclose(out.actions[0, 0:3], [1.5, 0.0, 0.0], atol=1e-6)
        np.testing.assert_allclose(out.actions[0, 7:10], [0.0, 0.0, 10.5], atol=1e-6)

    def test_only_left_reference_rotation_applies_to_left(self) -> None:
        """Left reference rotation must not affect the right arm decoding."""
        dec = _make_decoder()
        half = np.sqrt(2) / 2
        q90 = np.array([0.0, 0.0, half, half], dtype=np.float32)
        ref = _state(l_quat=tuple(q90), r_quat=(0.0, 0.0, 0.0, 1.0))
        row = _identity_row()
        row[0:3] = (1.0, 0.0, 0.0)   # left +x local
        row[7:10] = (1.0, 0.0, 0.0)  # right +x local
        out = dec.decode(_chunk([row]), ref)

        # Left: rotated by 90 about z -> (0,1,0). Right: identity ref -> (1,0,0).
        np.testing.assert_allclose(out.actions[0, 0:3], [0.0, 1.0, 0.0], atol=1e-5)
        np.testing.assert_allclose(out.actions[0, 7:10], [1.0, 0.0, 0.0], atol=1e-6)


# ---------------------------------------------------------------------------
# Case 7: grippers pass through unchanged
# ---------------------------------------------------------------------------


class TestGripperPassthrough:
    def test_gripper_absolute_values_unchanged(self) -> None:
        dec = _make_decoder()
        ref = _state()
        row = _identity_row()
        row[14] = 0.73  # left gripper
        row[15] = 0.27  # right gripper
        out = dec.decode(_chunk([row]), ref)

        np.testing.assert_allclose(out.actions[0, 14], 0.73, atol=1e-6)
        np.testing.assert_allclose(out.actions[0, 15], 0.27, atol=1e-6)

    def test_gripper_passthrough_multiple_rows(self) -> None:
        dec = _make_decoder()
        ref = _state()
        rows = []
        for lg, rg in [(0.0, 0.0), (0.5, 0.5), (1.0, 0.0)]:
            r = _identity_row()
            r[14] = lg
            r[15] = rg
            rows.append(r)
        out = dec.decode(_chunk(rows), ref)

        np.testing.assert_allclose(out.actions[:, 14], [0.0, 0.5, 1.0], atol=1e-6)
        np.testing.assert_allclose(out.actions[:, 15], [0.0, 0.5, 0.0], atol=1e-6)


# ---------------------------------------------------------------------------
# Case 8: non-unit relative quaternions
# ---------------------------------------------------------------------------


class TestNonUnitQuaternion:
    def test_non_unit_relative_quaternion_normalized(self) -> None:
        """A non-unit relative quaternion still decodes to a unit result."""
        dec = _make_decoder()
        ref = _state()
        row = _identity_row()
        # 2x the 90-deg-z quaternion — same orientation, non-unit magnitude.
        row[3:7] = (0.0, 0.0, np.sqrt(2), np.sqrt(2))
        row[10:14] = (0.0, 0.0, np.sqrt(2), np.sqrt(2))
        out = dec.decode(_chunk([row]), ref)

        # Result should be the same as the unit case: 90-deg-z.
        half = np.sqrt(2) / 2
        np.testing.assert_allclose(out.actions[0, 3:7], [0.0, 0.0, half, half], atol=1e-5)
        np.testing.assert_allclose(out.actions[0, 10:14], [0.0, 0.0, half, half], atol=1e-5)
        # And unit length.
        assert abs(np.linalg.norm(out.actions[0, 3:7]) - 1.0) < 1e-5

    def test_non_unit_reference_quaternion_normalized(self) -> None:
        """A non-unit reference orientation is normalized before use."""
        dec = _make_decoder()
        # 2x identity quaternion.
        ref = _state(
            l_quat=(0.0, 0.0, 0.0, 2.0),
            r_quat=(0.0, 0.0, 0.0, 2.0),
        )
        row = _identity_row()
        row[0:3] = (1.0, 0.0, 0.0)
        out = dec.decode(_chunk([row]), ref)

        # Identity ref -> relative translation passes straight through.
        np.testing.assert_allclose(out.actions[0, 0:3], [1.0, 0.0, 0.0], atol=1e-6)


# ---------------------------------------------------------------------------
# Case 9: rejection of degenerate inputs
# ---------------------------------------------------------------------------


class TestRejection:
    def test_zero_reference_quaternion_rejected(self) -> None:
        dec = _make_decoder()
        ref = _state(l_quat=(0.0, 0.0, 0.0, 0.0))
        with pytest.raises(ValueError, match="quaternion norm"):
            dec.decode(_chunk([_identity_row()]), ref)

    def test_nan_reference_quaternion_rejected(self) -> None:
        dec = _make_decoder()
        ref = _state(l_quat=(float("nan"), 0.0, 0.0, 1.0))
        with pytest.raises(ValueError, match="NaN or Inf"):
            dec.decode(_chunk([_identity_row()]), ref)

    def test_inf_relative_quaternion_rejected(self) -> None:
        """A relative quaternion producing Inf in the decoded result is rejected."""
        dec = _make_decoder()
        ref = _state()
        row = _identity_row()
        row[3:7] = (float("inf"), 0.0, 0.0, 1.0)
        # RelativeActionChunk itself rejects non-finite inputs, so build via
        # the validated constructor which should raise first.
        with pytest.raises(ValueError):
            RelativeActionChunk(actions=np.array([row], dtype=np.float32))

    def test_wrong_input_type_relative_chunk(self) -> None:
        dec = _make_decoder()
        with pytest.raises(TypeError):
            dec.decode("not a chunk", _state())  # type: ignore[arg-type]

    def test_wrong_input_type_reference_state(self) -> None:
        dec = _make_decoder()
        with pytest.raises(TypeError):
            dec.decode(_chunk([_identity_row()]), "not a state")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Output contract
# ---------------------------------------------------------------------------


class TestOutputContract:
    def test_output_is_absolute_action_chunk(self) -> None:
        dec = _make_decoder()
        out = dec.decode(_chunk([_identity_row()]), _state())
        assert isinstance(out, ActionChunk)
        assert out.actions.dtype == np.float32
        assert out.actions.shape == (1, 16)

    def test_output_quaternions_are_unit_length(self) -> None:
        dec = _make_decoder()
        half = np.sqrt(2) / 2
        ref = _state(l_quat=(0.0, 0.0, half, half), r_quat=(0.0, 0.0, half, half))
        row = _identity_row()
        row[3:7] = (0.0, 0.0, half, half)
        out = dec.decode(_chunk([row]), ref)
        assert abs(np.linalg.norm(out.actions[0, 3:7]) - 1.0) < 1e-5
        assert abs(np.linalg.norm(out.actions[0, 10:14]) - 1.0) < 1e-5

    def test_output_chunk_size_preserved(self) -> None:
        dec = _make_decoder()
        rows = [_identity_row() for _ in range(7)]
        out = dec.decode(_chunk(rows), _state())
        assert out.actions.shape == (7, 16)
