"""Bundle and normalizer contract check result objects.

These are frozen dataclasses that carry structured pass/fail results
for contract validation functions in the config layer.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class BundleContractResult:
    """Result of checking an ACT bundle for required files and metadata.

    Attributes:
        passed: Whether the bundle contract check passed.
        reason: Human-readable explanation of the result.
        missing_files: Files expected in the bundle but not found.
        schema_version: The manifest schema_version found in the bundle, if any.
    """

    passed: bool
    reason: str
    missing_files: tuple[str, ...] = ()
    schema_version: Optional[int] = None

    @property
    def is_pass(self) -> bool:
        """Convenience accessor for the pass/fail status."""
        return self.passed


@dataclass(frozen=True)
class NormalizerContractResult:
    """Result of checking normalizer dimensions against the 16D contract.

    Attributes:
        passed: Whether the normalizer dimension check passed.
        reason: Human-readable explanation of the result.
        expected_dim: The expected dimension (16 for ACT).
        actual_dim: The actual dimension found in the normalizer.
    """

    passed: bool
    reason: str
    expected_dim: int
    actual_dim: int

    @property
    def is_pass(self) -> bool:
        """Convenience accessor for the pass/fail status."""
        return self.passed
