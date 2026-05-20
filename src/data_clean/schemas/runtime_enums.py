"""Runtime status, mode, and scene enums for the data cleaning pipeline."""

from __future__ import annotations

from enum import Enum


class RunStatus(str, Enum):
    """Lifecycle status of a Runtime run, scene result, or step record."""

    CREATED = "created"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RunMode(str, Enum):
    """Runtime execution mode: dev vs prod, single scene vs full pipeline."""

    DEV_SINGLE_SCENE = "dev_single_scene"
    DEV_FULL_PIPELINE = "dev_full_pipeline"
    PROD_SINGLE_SCENE = "prod_single_scene"
    PROD_FULL_PIPELINE = "prod_full_pipeline"


class ServiceMode(str, Enum):
    """Whether the Runtime calls fake or real services."""

    FAKE = "fake"
    REAL = "real"


class SceneName(str, Enum):
    """Controlled names for the five stage-two business scenes."""

    SCENE1 = "scene1"
    SCENE2 = "scene2"
    SCENE3 = "scene3"
    SCENE4 = "scene4"
    SCENE5 = "scene5"


class FakeServiceBehavior(str, Enum):
    """Controlled fake-service behavior: success, controlled failure, or skip."""

    SUCCESS = "success"
    CONTROLLED_FAILURE = "controlled_failure"
    SKIPPED = "skipped"
