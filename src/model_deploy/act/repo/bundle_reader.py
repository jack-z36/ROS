"""Bundle directory reader for ACT deployment.

Checks bundle directory structural integrity (file existence) and resolves
the checkpoint path.  Does NOT load model weights, parse manifest content,
or do dimension business validation.
"""

from __future__ import annotations

import json
from pathlib import Path

BUNDLE_SCHEMA_VERSION: int = 1

BUNDLE_REQUIRED_FILES: tuple[str, ...] = (
    "manifest.json",
    "normalizers.json",
    "experiment_config.yaml",
    "adapter",
)


class BundleStructureError(ValueError):
    """Raised when the bundle directory structure is incomplete or invalid.

    Covers:
    - Bundle directory does not exist.
    - Required files or directories are missing.
    - Checkpoint path cannot be resolved.
    """


def resolve_bundle_adapter_dir(bundle_dir: str | Path) -> Path:
    """Return the adapter sub-directory inside the bundle.

    Args:
        bundle_dir: Path to the bundle root directory.

    Returns:
        ``bundle_dir / "adapter"``.

    Raises:
        FileNotFoundError: If the adapter directory does not exist.
    """
    bundle_dir = Path(bundle_dir).expanduser().resolve()
    adapter_dir = bundle_dir / "adapter"
    if not adapter_dir.is_dir():
        raise FileNotFoundError(
            f"Bundle adapter directory does not exist: {adapter_dir}"
        )
    return adapter_dir


def check_bundle_files(bundle_dir: str | Path) -> list[str]:
    """Check that all required bundle files and directories exist.

    Args:
        bundle_dir: Path to the bundle root directory.

    Returns:
        A list of relative paths for missing items.  An empty list means
        the bundle structure is complete.

    Raises:
        BundleStructureError: If *bundle_dir* itself does not exist.
    """
    bundle_dir = Path(bundle_dir).expanduser().resolve()
    if not bundle_dir.is_dir():
        raise BundleStructureError(f"Bundle directory does not exist: {bundle_dir}")

    missing: list[str] = []
    for name in BUNDLE_REQUIRED_FILES:
        candidate = bundle_dir / name
        if name == "adapter":
            if not candidate.is_dir():
                missing.append(name)
        else:
            if not candidate.is_file():
                missing.append(name)
    return missing


def resolve_checkpoint_path(bundle_dir: str | Path) -> Path:
    """Resolve the checkpoint path from the bundle.

    Strategy:
    1. Read ``manifest.json`` and extract the checkpoint path from
       ``model.pretrained_path``.
    2. If the manifest is unavailable or the field is missing, scan the
       bundle directory for common checkpoint files (``.pt``, ``.safetensors``,
       or a ``checkpoint`` directory).

    Args:
        bundle_dir: Path to the bundle root directory.

    Returns:
        The resolved checkpoint path.

    Raises:
        BundleStructureError: If the checkpoint cannot be resolved by either
            strategy.
    """
    bundle_dir = Path(bundle_dir).expanduser().resolve()

    # Strategy 1: read from manifest.json
    manifest_path = bundle_dir / "manifest.json"
    if manifest_path.is_file():
        try:
            with manifest_path.open("r", encoding="utf-8") as fh:
                manifest = json.load(fh)
            pretrained = manifest.get("model", {}).get("pretrained_path")
            if pretrained:
                candidate = Path(pretrained)
                if not candidate.is_absolute():
                    candidate = bundle_dir / candidate
                if candidate.exists():
                    return candidate.resolve()
        except (json.JSONDecodeError, KeyError, TypeError):
            pass  # fall through to directory scan

    # Strategy 2: directory scan
    for entry in sorted(bundle_dir.rglob("*")):
        if entry.is_file() and entry.suffix in (".pt", ".safetensors"):
            return entry.resolve()
        if entry.is_dir() and entry.name == "checkpoint":
            # A checkpoint directory should contain weight files
            return entry.resolve()

    raise BundleStructureError(
        f"Cannot resolve checkpoint path in bundle: {bundle_dir}"
    )
