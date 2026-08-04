"""Streaming reader for the standard Scene 4 bridge MCAP boundary."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

import numpy as np
from mcap.reader import make_reader

from repo.ros2_codec import Ros2DynamicCodec
from service.forge_bridge import FORGE_TOPICS


class BridgeMcapError(RuntimeError):
    """Raised when a bridge MCAP frame is incomplete or violates its schema."""


@dataclass(frozen=True)
class BridgeFrame:
    timestamp_ns: int
    state: np.ndarray
    action: np.ndarray
    image_left: np.ndarray
    image_right: np.ndarray


_TOPIC_TO_FIELD = {
    FORGE_TOPICS["state"]: "state",
    FORGE_TOPICS["action"]: "action",
    FORGE_TOPICS["image_left"]: "image_left",
    FORGE_TOPICS["image_right"]: "image_right",
}
_REQUIRED_FIELDS = frozenset(_TOPIC_TO_FIELD.values())


def iter_bridge_frames(
    bridge_dir: str | Path,
    *,
    state_dim: int,
    action_dim: int,
    image_height: int,
    image_width: int,
) -> Iterator[BridgeFrame]:
    """Yield one decoded frame at a time without retaining an episode in RAM."""

    bridge_path = Path(bridge_dir).expanduser().resolve()
    mcap_path = bridge_path / "forge_ready.mcap"
    if not mcap_path.is_file():
        raise BridgeMcapError(f"forge_ready.mcap not found: {mcap_path}")

    codec = Ros2DynamicCodec()
    current_timestamp: int | None = None
    current: dict[str, np.ndarray] = {}
    yielded = 0

    with mcap_path.open("rb") as stream:
        reader = make_reader(stream)
        for schema, channel, message in reader.iter_messages(log_time_order=True):
            field = _TOPIC_TO_FIELD.get(channel.topic)
            if field is None:
                continue
            timestamp_ns = int(message.log_time)
            if current_timestamp is None:
                current_timestamp = timestamp_ns
            elif timestamp_ns != current_timestamp:
                yield _build_frame(
                    mcap_path=mcap_path,
                    timestamp_ns=current_timestamp,
                    values=current,
                    state_dim=state_dim,
                    action_dim=action_dim,
                    image_height=image_height,
                    image_width=image_width,
                )
                yielded += 1
                current_timestamp = timestamp_ns
                current = {}

            if field in current:
                raise BridgeMcapError(
                    f"duplicate bridge field: topic={channel.topic} timestamp_ns={timestamp_ns}"
                )
            if schema is None:
                raise BridgeMcapError(
                    f"bridge schema missing: topic={channel.topic} timestamp_ns={timestamp_ns}"
                )
            decoded = codec.decode(schema, message)
            if field in {"state", "action"}:
                current[field] = np.asarray(decoded.position, dtype=np.float32)
            else:
                current[field] = _decode_image(decoded, schema.name)

    if current_timestamp is not None:
        yield _build_frame(
            mcap_path=mcap_path,
            timestamp_ns=current_timestamp,
            values=current,
            state_dim=state_dim,
            action_dim=action_dim,
            image_height=image_height,
            image_width=image_width,
        )
        yielded += 1
    if yielded == 0:
        raise BridgeMcapError(f"bridge contains no complete frames: {mcap_path}")


def _decode_image(message: object, schema_name: str) -> np.ndarray:
    if schema_name != "sensor_msgs/msg/Image":
        raise BridgeMcapError(f"unsupported bridge image schema: {schema_name}")
    height = int(getattr(message, "height"))
    width = int(getattr(message, "width"))
    step = int(getattr(message, "step"))
    encoding = str(getattr(message, "encoding")).lower()
    raw = bytes(getattr(message, "data"))
    if encoding in {"rgb8", "bgr8"}:
        row_width = width * 3
        if step < row_width or len(raw) < height * step:
            raise BridgeMcapError("bridge image payload is shorter than height/step")
        image = np.frombuffer(raw, dtype=np.uint8).reshape(height, step)[:, :row_width]
        image = image.reshape(height, width, 3)
        if encoding == "bgr8":
            image = image[:, :, ::-1]
    elif encoding == "mono8":
        if step < width or len(raw) < height * step:
            raise BridgeMcapError("bridge mono image payload is shorter than height/step")
        mono = np.frombuffer(raw, dtype=np.uint8).reshape(height, step)[:, :width]
        image = np.repeat(mono[:, :, None], 3, axis=2)
    else:
        raise BridgeMcapError(f"unsupported bridge image encoding: {encoding}")
    return np.ascontiguousarray(image, dtype=np.uint8)


def _build_frame(
    *,
    mcap_path: Path,
    timestamp_ns: int,
    values: dict[str, np.ndarray],
    state_dim: int,
    action_dim: int,
    image_height: int,
    image_width: int,
) -> BridgeFrame:
    missing = sorted(_REQUIRED_FIELDS - values.keys())
    if missing:
        raise BridgeMcapError(
            f"incomplete bridge frame: file={mcap_path} timestamp_ns={timestamp_ns} missing={missing}"
        )
    state = values["state"]
    action = values["action"]
    if state.shape != (state_dim,) or state.dtype != np.float32:
        raise BridgeMcapError(
            f"observation.state contract mismatch: expected=float32[{state_dim}] "
            f"actual={state.dtype}{list(state.shape)}"
        )
    if action.shape != (action_dim,) or action.dtype != np.float32:
        raise BridgeMcapError(
            f"action contract mismatch: expected=float32[{action_dim}] "
            f"actual={action.dtype}{list(action.shape)}"
        )
    if not np.isfinite(state).all() or not np.isfinite(action).all():
        raise BridgeMcapError("state/action contains a non-finite value")
    expected_image_shape = (image_height, image_width, 3)
    for key in ("image_left", "image_right"):
        image = values[key]
        if image.shape != expected_image_shape or image.dtype != np.uint8:
            raise BridgeMcapError(
                f"{key} contract mismatch: expected=uint8{list(expected_image_shape)} "
                f"actual={image.dtype}{list(image.shape)}"
            )
    return BridgeFrame(
        timestamp_ns=timestamp_ns,
        state=state,
        action=action,
        image_left=values["image_left"],
        image_right=values["image_right"],
    )
