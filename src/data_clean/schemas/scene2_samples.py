"""RAM sample objects decoded from the Scene 2 MCAP whitelist."""

from __future__ import annotations

from dataclasses import dataclass, field

from .scene2_streams import Scene2StreamInventory


@dataclass(frozen=True)
class PoseSample:
    topic: str
    timestamp_ns: int
    message_index: int
    position: tuple[float, float, float]
    orientation_xyzw: tuple[float, float, float, float]
    time_domain: str = "log_time"
    log_time_ns: int | None = None
    publish_time_ns: int | None = None
    sequence: int | None = None
    source_channel_id: int | None = None


@dataclass(frozen=True)
class GripperSample:
    topic: str
    timestamp_ns: int
    message_index: int
    value: float
    time_domain: str = "log_time"
    log_time_ns: int | None = None
    publish_time_ns: int | None = None
    sequence: int | None = None
    source_channel_id: int | None = None


@dataclass(frozen=True)
class TactilePressureFrame:
    topic: str
    timestamp_ns: int
    message_index: int
    hand: str
    gripper: str
    rows: int
    cols: int
    data: list[int]
    time_domain: str = "log_time"
    log_time_ns: int | None = None
    publish_time_ns: int | None = None
    sequence: int | None = None
    source_channel_id: int | None = None


@dataclass(frozen=True)
class Scene2SignalSamples:
    pose: list[PoseSample]
    gripper: list[GripperSample]
    tactile: list[TactilePressureFrame]
    inventory: Scene2StreamInventory | None = None

