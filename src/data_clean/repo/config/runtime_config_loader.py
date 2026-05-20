from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml

from schemas.runtime_config_types import (
    ConfigOverrideSet,
    EffectiveRuntimeConfig,
    RuntimeConfigSource,
    RuntimeConfigSourceKind,
)


class RuntimeConfigError(ValueError):
    ...


def resolve_runtime_config_source(
    explicit_path: Path | str | None,
    *,
    default_config_path: Path | str | None = None,
) -> RuntimeConfigSource:
    if explicit_path is not None:
        path = Path(explicit_path).resolve()
        kind = RuntimeConfigSourceKind.EXPLICIT
    elif default_config_path is not None:
        path = Path(default_config_path).resolve()
        kind = RuntimeConfigSourceKind.DEFAULT
    else:
        raise RuntimeConfigError("either explicit_path or default_config_path must be provided")
    return RuntimeConfigSource(
        config_path=path,
        source_kind=kind,
        exists_at_load_time=path.is_file(),
    )


def load_effective_runtime_config(
    source: RuntimeConfigSource,
    override_set: ConfigOverrideSet | None = None,
) -> EffectiveRuntimeConfig:
    config_path = source.config_path
    if not config_path.is_file():
        raise RuntimeConfigError(f"config path does not exist: {config_path}")

    with config_path.open("r", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh) or {}
    if not isinstance(raw, dict):
        raise RuntimeConfigError(f"config file must be a YAML mapping: {config_path}")

    if override_set is None:
        override_set = ConfigOverrideSet()

    config_data = _apply_overrides(raw, override_set.overrides)

    return EffectiveRuntimeConfig(
        config_source=source,
        override_set=override_set,
        config_data=config_data,
    )


def _apply_overrides(base: dict[str, Any], overrides: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(base)
    for dot_path, value in overrides.items():
        parts = dot_path.split(".")
        _set_nested(result, parts, value)
    return result


def _set_nested(target: dict, parts: list[str], value: Any) -> None:
    for i, part in enumerate(parts[:-1]):
        if not isinstance(target.get(part), dict):
            raise RuntimeConfigError(
                f"override path conflict: '{'.'.join(parts)}' — "
                f"'{part}' is not a mapping"
            )
        target = target[part]
    target[parts[-1]] = value
