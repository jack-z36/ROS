"""Manifest parser for ACT deployment bundles.

Reads ``manifest.json`` and returns its contents as a dict.
Does NOT perform schema-version validation, field-completeness checks,
or dimension business validation — those belong to the config layer.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

MANIFEST_NAME: str = "manifest.json"


def load_bundle_manifest(bundle_dir: str | Path) -> dict[str, Any]:
    """Read and parse the bundle manifest file.

    Args:
        bundle_dir: Path to the bundle directory containing ``manifest.json``.

    Returns:
        The manifest contents as a dict.

    Raises:
        FileNotFoundError: If ``manifest.json`` does not exist under *bundle_dir*.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    bundle_dir = Path(bundle_dir).expanduser().resolve()
    manifest_path = bundle_dir / MANIFEST_NAME
    with manifest_path.open("r", encoding="utf-8") as fh:
        return json.load(fh)
