from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any
import hashlib
import json

import yaml

from schemas.runtime_config_types import ConfigSnapshot, EffectiveRuntimeConfig
from schemas.runtime_context import RunContext
from schemas.lerobot_features import compile_lerobot_feature_contract


class ConfigSnapshotError(RuntimeError):
    ...


def read_config_snapshot_metadata(path: str | Path) -> dict[str, Any]:
    """Read v2 snapshot provenance while accepting legacy snapshots."""

    value = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    if not isinstance(value, dict):
        raise ConfigSnapshotError("config snapshot must be a mapping")
    return {
        "contract_fingerprint": value.get("contract_fingerprint"),
        "processing_config_fingerprint": value.get("processing_config_fingerprint"),
        "compiled_feature_contract": value.get("compiled_feature_contract"),
        "effective_config": value.get("effective_config", {}),
    }


def write_config_snapshot(
    effective_config: EffectiveRuntimeConfig,
    run_dir: Path,
    snapshot_path: Path | None = None,
) -> ConfigSnapshot:
    run_dir = run_dir.resolve()

    if snapshot_path is None:
        snapshot_path = run_dir / "config_snapshot.yaml"
    else:
        snapshot_path = snapshot_path.resolve()
        try:
            snapshot_path.relative_to(run_dir)
        except ValueError:
            raise ConfigSnapshotError(
                f"snapshot path {snapshot_path} must be inside run_dir {run_dir}"
            )

    if snapshot_path.exists():
        raise ConfigSnapshotError(
            f"config snapshot already exists: {snapshot_path}"
        )

    snapshot_path.parent.mkdir(parents=True, exist_ok=True)

    web_pipeline = effective_config.config_data.get("web_pipeline", {})
    features = web_pipeline.get("lerobot_features") if isinstance(web_pipeline, dict) else None
    contract = compile_lerobot_feature_contract(features)
    processing_config = deepcopy(effective_config.config_data)
    processing_pipeline = processing_config.get("web_pipeline")
    if isinstance(processing_pipeline, dict):
        processing_pipeline.pop("lerobot_features", None)
    processing_payload = json.dumps(
        processing_config, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str
    ).encode("utf-8")
    processing_fingerprint = hashlib.sha256(processing_payload).hexdigest()
    payload: dict[str, Any] = {
        "original_config": deepcopy(effective_config.config_data),
        "effective_config": deepcopy(effective_config.config_data),
        "compiled_feature_contract": contract.to_dict(),
        "contract_fingerprint": contract.fingerprint,
        "processing_config_fingerprint": processing_fingerprint,
        "runtime_config_source": {
            "source_kind": effective_config.config_source.source_kind.value,
            "config_path": str(effective_config.config_source.config_path),
            "exists_at_load_time": effective_config.config_source.exists_at_load_time,
            "declared_by": effective_config.config_source.declared_by,
        },
        "config_override_set": {
            "overrides": deepcopy(effective_config.override_set.overrides),
            "source_detail": effective_config.override_set.source_detail,
            "empty_is_valid": effective_config.override_set.empty_is_valid,
        },
        "written_at": datetime.now().isoformat(),
    }
    snapshot_path.write_text(
        yaml.safe_dump(payload, default_flow_style=False, allow_unicode=True),
        encoding="utf-8",
    )

    return ConfigSnapshot(
        snapshot_path=snapshot_path,
        effective_config=effective_config,
        written_at=datetime.now(),
        contract_fingerprint=contract.fingerprint,
        processing_config_fingerprint=processing_fingerprint,
    )


def attach_config_snapshot_to_context(
    context: RunContext,
    snapshot: ConfigSnapshot,
) -> RunContext:
    import copy
    updated = copy.copy(context)
    updated.config_snapshot_path = snapshot.snapshot_path
    return updated
