from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from schemas.runtime_config_types import ConfigSnapshot, EffectiveRuntimeConfig
from schemas.runtime_context import RunContext


class ConfigSnapshotError(RuntimeError):
    ...


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

    payload: dict[str, Any] = {
        "effective_config": deepcopy(effective_config.config_data),
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
    )


def attach_config_snapshot_to_context(
    context: RunContext,
    snapshot: ConfigSnapshot,
) -> RunContext:
    import copy
    updated = copy.copy(context)
    updated.config_snapshot_path = snapshot.snapshot_path
    return updated
