"""Experiment config loader for ACT deployment bundles.

Reads ``experiment_config.yaml`` and returns the raw mapping.
Preserves all fields (including ``state_dim``/``action_dim``) as-is.
Does NOT perform dimension business validation — that belongs to the config
layer's cross-validation.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

EXPERIMENT_CONFIG_NAME: str = "experiment_config.yaml"


class ExperimentConfigLoadError(ValueError):
    """Raised when ``experiment_config.yaml`` cannot be loaded.

    Covers three failure modes:
    - File does not exist.
    - File is not valid YAML.
    - Root node is not a mapping (dict).
    """


def load_experiment_config(path: str | Path) -> dict[str, Any]:
    """Load experiment_config.yaml and return the raw mapping.

    Args:
        path: Path to the ``experiment_config.yaml`` file.

    Returns:
        The parsed contents as a dict.  All fields are preserved as-is;
        no defaults are injected and no dimension values are overridden.

    Raises:
        ExperimentConfigLoadError: If the file is missing, unparseable,
            or the root node is not a mapping.
    """
    path = Path(path).expanduser().resolve()

    if not path.is_file():
        raise ExperimentConfigLoadError(
            f"experiment_config file not found: {path}"
        )

    try:
        with path.open("r", encoding="utf-8") as fh:
            raw = yaml.safe_load(fh)
    except yaml.YAMLError as exc:
        raise ExperimentConfigLoadError(
            f"Failed to parse experiment_config YAML: {path}"
        ) from exc

    if not isinstance(raw, dict):
        raise ExperimentConfigLoadError(
            f"experiment_config root must be a mapping, got {type(raw).__name__}: {path}"
        )

    return raw
