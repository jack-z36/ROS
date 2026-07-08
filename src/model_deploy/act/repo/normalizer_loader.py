"""Normalizer loader for ACT deployment bundles.

Reads ``normalizers.json`` and constructs ``ActionStateNormalizer`` objects.
Does NOT perform dimension business validation — that belongs to the config
layer's ``check_normalizer_contract``.
"""

from __future__ import annotations

import json
from pathlib import Path

from model_deploy.act.repo.normalization import ActionStateNormalizer

NORMALIZERS_NAME: str = "normalizers.json"


def load_bundle_normalizers(
    bundle_dir: str | Path,
) -> tuple[ActionStateNormalizer, ActionStateNormalizer]:
    """Read normalizers.json and construct state/action normalizer objects.

    Args:
        bundle_dir: Path to the bundle directory containing ``normalizers.json``.

    Returns:
        A ``(state_normalizer, action_normalizer)`` tuple.

    Raises:
        FileNotFoundError: If ``normalizers.json`` does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
        KeyError: If the payload is missing ``state`` or ``action`` keys.
    """
    bundle_dir = Path(bundle_dir).expanduser().resolve()
    normalizer_path = bundle_dir / NORMALIZERS_NAME
    with normalizer_path.open("r", encoding="utf-8") as fh:
        payload = json.load(fh)

    state_payload = payload["state"]
    action_payload = payload["action"]

    state_normalizer = ActionStateNormalizer(
        min_vals=state_payload["min"],
        max_vals=state_payload["max"],
        identity_indices=state_payload.get("identity_indices"),
    )
    action_normalizer = ActionStateNormalizer(
        min_vals=action_payload["min"],
        max_vals=action_payload["max"],
        identity_indices=action_payload.get("identity_indices"),
    )
    return state_normalizer, action_normalizer
