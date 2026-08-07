"""Bundle / checkpoint directory reader for ACT deployment.

Checks bundle directory structural integrity (file existence) and resolves
the checkpoint path.  Does NOT load model weights, parse manifest content,
or do dimension business validation.

Two source layouts are recognised (auto-detected by file existence):

1. **bundle** — a packaged ``deploy_bundle/`` carrying ``manifest.json``,
   ``normalizers.json``, ``experiment_config.yaml`` and an ``adapter/``
   directory that mirrors the trained ``pretrained_model/``.
2. **checkpoint** — a raw training checkpoint directory such as
   ``.../checkpoints/100000/`` (or its inner ``pretrained_model/``).  It
   carries ``pretrained_model/config.json`` + ``model.safetensors`` and the
   exported preprocessor safetensors; no manifest / sidecar files are
   required.
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

#: The lerobot ACT ``pretrained_model`` directory name inside a checkpoint.
CHECKPOINT_PRETRAINED_SUBDIR: str = "pretrained_model"

#: The policy hyperparameter file that lives inside ``pretrained_model/``.
CHECKPOINT_CONFIG_NAME: str = "config.json"


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


# ---------------------------------------------------------------------------
# Source-layout detection (bundle vs raw checkpoint)
# ---------------------------------------------------------------------------


def is_bundle_dir(path: str | Path) -> bool:
    """Return ``True`` if *path* looks like a packaged deploy bundle.

    A bundle is identified by the presence of ``manifest.json`` at the top
    level.  The remaining required files (``normalizers.json`` etc.) are
    verified separately by :func:`check_bundle_files`.
    """
    return (Path(path).expanduser().resolve() / "manifest.json").is_file()


def is_checkpoint_dir(path: str | Path) -> bool:
    """Return ``True`` if *path* is a raw training checkpoint directory.

    Two shapes are accepted:

    - ``<checkpoint>/pretrained_model/config.json`` (e.g.
      ``.../checkpoints/100000/``), or
    - ``<pretrained_model>/config.json`` (when the caller points directly at
      the inner ``pretrained_model/`` directory).
    """
    root = Path(path).expanduser().resolve()
    if (root / CHECKPOINT_PRETRAINED_SUBDIR / CHECKPOINT_CONFIG_NAME).is_file():
        return True
    if (root / CHECKPOINT_CONFIG_NAME).is_file():
        return True
    return False


def resolve_pretrained_dir(source_dir: str | Path) -> Path:
    """Resolve the ``pretrained_model`` directory from a bundle or checkpoint.

    Accepts either source layout and always returns the directory that
    contains ``config.json`` + ``model.safetensors`` — the single entry point
    the policy loader and the statistics loader consume.

    Args:
        source_dir: A bundle root, a checkpoint root
            (``.../checkpoints/100000``), or an inner ``pretrained_model``
            directory.

    Returns:
        The resolved ``pretrained_model`` directory.

    Raises:
        BundleStructureError: If the pretrained directory cannot be located.
    """
    root = Path(source_dir).expanduser().resolve()

    # Strategy 1: packaged bundle — delegate to the manifest-aware resolver.
    if (root / "manifest.json").is_file():
        checkpoint = resolve_checkpoint_path(root)
        return checkpoint if checkpoint.is_dir() else checkpoint.parent

    # Strategy 2: checkpoint root with an inner pretrained_model/.
    inner = root / CHECKPOINT_PRETRAINED_SUBDIR
    if (inner / CHECKPOINT_CONFIG_NAME).is_file():
        return inner

    # Strategy 3: the caller already pointed at pretrained_model/ itself.
    if (root / CHECKPOINT_CONFIG_NAME).is_file():
        return root

    raise BundleStructureError(
        f"Cannot resolve a pretrained_model directory from {root}: expected a "
        f"bundle (manifest.json), a checkpoint (pretrained_model/config.json), "
        f"or a pretrained_model directory (config.json)."
    )
