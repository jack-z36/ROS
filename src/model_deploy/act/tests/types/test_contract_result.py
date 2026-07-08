"""Tests for BundleContractResult and NormalizerContractResult."""

import pytest
from dataclasses import FrozenInstanceError

from model_deploy.act.types.contract_result import (
    BundleContractResult,
    NormalizerContractResult,
)


class TestBundleContractResult:
    """Tests for BundleContractResult frozen dataclass."""

    def test_construct_pass(self) -> None:
        result = BundleContractResult(
            passed=True,
            reason="all files present",
            missing_files=(),
            schema_version=1,
        )
        assert result.passed is True
        assert result.is_pass is True
        assert result.reason == "all files present"
        assert result.missing_files == ()
        assert result.schema_version == 1

    def test_construct_fail(self) -> None:
        result = BundleContractResult(
            passed=False,
            reason="missing manifest.json",
            missing_files=("manifest.json", "normalizers.json"),
            schema_version=None,
        )
        assert result.passed is False
        assert result.is_pass is False
        assert result.missing_files == ("manifest.json", "normalizers.json")
        assert result.schema_version is None

    def test_is_pass_property(self) -> None:
        assert BundleContractResult(passed=True, reason="ok").is_pass is True
        assert BundleContractResult(passed=False, reason="fail").is_pass is False

    def test_frozen_immutable(self) -> None:
        result = BundleContractResult(passed=True, reason="ok")
        with pytest.raises(FrozenInstanceError):
            result.passed = False  # type: ignore[misc]

    def test_default_fields(self) -> None:
        result = BundleContractResult(passed=True, reason="ok")
        assert result.missing_files == ()
        assert result.schema_version is None


class TestNormalizerContractResult:
    """Tests for NormalizerContractResult frozen dataclass."""

    def test_construct_pass(self) -> None:
        result = NormalizerContractResult(
            passed=True,
            reason="dimension matches",
            expected_dim=16,
            actual_dim=16,
        )
        assert result.passed is True
        assert result.is_pass is True
        assert result.reason == "dimension matches"
        assert result.expected_dim == 16
        assert result.actual_dim == 16

    def test_construct_fail(self) -> None:
        result = NormalizerContractResult(
            passed=False,
            reason="dimension mismatch: expected 16, got 14",
            expected_dim=16,
            actual_dim=14,
        )
        assert result.passed is False
        assert result.is_pass is False
        assert result.expected_dim == 16
        assert result.actual_dim == 14

    def test_is_pass_property(self) -> None:
        assert NormalizerContractResult(
            passed=True, reason="ok", expected_dim=16, actual_dim=16
        ).is_pass is True
        assert NormalizerContractResult(
            passed=False, reason="fail", expected_dim=16, actual_dim=14
        ).is_pass is False

    def test_frozen_immutable(self) -> None:
        result = NormalizerContractResult(
            passed=True, reason="ok", expected_dim=16, actual_dim=16
        )
        with pytest.raises(FrozenInstanceError):
            result.passed = False  # type: ignore[misc]
