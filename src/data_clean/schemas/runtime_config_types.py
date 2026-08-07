from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any


class RuntimeConfigSourceKind(str, Enum):
    DEFAULT = "default"
    EXPLICIT = "explicit"
    ENVIRONMENT = "environment"
    DEFAULT_CALIBRATED = "default_calibrated"
    DEFAULT_SMOKE_TEST = "default_smoke_test"


@dataclass
class RuntimeConfigSource:
    config_path: Path
    source_kind: RuntimeConfigSourceKind
    exists_at_load_time: bool = True
    declared_by: str = ""


@dataclass
class ConfigOverrideSet:
    overrides: dict[str, Any] = field(default_factory=dict)
    source_detail: str = ""
    empty_is_valid: bool = True

    @property
    def is_empty(self) -> bool:
        return len(self.overrides) == 0


@dataclass
class EffectiveRuntimeConfig:
    config_source: RuntimeConfigSource
    override_set: ConfigOverrideSet
    config_data: dict[str, Any]
    config_format: str = "yaml"


@dataclass
class ConfigSnapshot:
    snapshot_path: Path
    effective_config: EffectiveRuntimeConfig
    written_at: datetime | None = None
    snapshot_format: str = "yaml"
    is_required: bool = True
    contract_fingerprint: str | None = None
    processing_config_fingerprint: str | None = None
