"""Observation batch preparation for ACT inference (L2-03 Stage 1).

Converts an ``ObservationSnapshot`` into an ACT policy ``batch`` dict on the
policy device, executing 7 sequential computation micro-elements.  Each
micro-element is an independent, testable pure function.  The orchestration
function ``prepare_observation_batch`` chains them together.

No class is created for this stage: the 7 micro-elements have no independent
lifecycle, mutable state, or resource ownership.
"""

from __future__ import annotations

from typing import Any, Dict, Mapping, Tuple

import numpy as np
import torch

from model_deploy.act.repo.act_runtime_resources import PolicyInputSpec
from model_deploy.act.types.action_spec import ACTION_DIM

# ---------------------------------------------------------------------------
# input_spec convention
# ---------------------------------------------------------------------------
#
# input_spec is the frozen canonical PolicyInputSpec (deploy_056) produced once
# at startup by load_act_runtime_resources and injected into L2-03 by L2-06.
# It is a typed object, not a Dict -- every field is a typed attribute:
#
#   state_key:     str                        e.g. "observation.state"
#   state_dim:     int                        e.g. 16
#   image_prefix:  str                        e.g. "observation.images."
#   camera_keys:   Tuple[str, ...]            sorted, non-empty logical names
#   image_shapes:  Tuple[Tuple[int,int,int]]  CHW, one per camera_keys (aligned)
#   image_layout:  str                        "CHW"
#   image_dtype:   str                        "float32"
#   image_value_range: Tuple[float, float]   (0.0, 1.0)
#   action_dim:    int                        e.g. 16
#   chunk_size:    int                        positive
#
# camera_keys are the logical camera names used as keys in
# ObservationSnapshot.images; image_shapes is positionally aligned with
# camera_keys.  image_prefix is prepended to each camera name to form the full
# policy feature key used inside the ACT batch dict.
# ---------------------------------------------------------------------------

_DEFAULT_IMAGE_PREFIX: str = "observation.images."


# ===================================================================
# Micro-element 1: Model input compatibility check
# ===================================================================

def check_model_input_compatibility(
    snapshot: Any,  # ObservationSnapshot (lazy import to avoid circular deps)
    input_spec: PolicyInputSpec,
) -> None:
    """Verify snapshot fields satisfy the ACT policy's input contract.

    Reads the canonical ``PolicyInputSpec`` typed attributes only -- no Dict
    access, no default plug-in.  ``image_shapes`` is positionally aligned with
    ``camera_keys``; the mapping is built locally.

    Checks:
    * ``encoded_state`` is ``(state_dim,)`` and contains only finite values.
    * Every required camera (``camera_keys``) is present in ``snapshot.images``.
    * Each image has the expected CHW shape and contains only finite values.

    This is a **compatibility** check, not a freshness check.
    Freshness is the responsibility of L2-02 / L2-06.

    Raises:
        ValueError: state dimension, shape, or value contract violated.
        KeyError:   a required camera is missing from ``snapshot.images``.
    """
    state_dim = input_spec.state_dim
    encoded = snapshot.encoded_state

    # -- state dimension --
    if encoded.shape != (state_dim,):
        raise ValueError(
            f"encoded_state must have shape ({state_dim},), "
            f"got {encoded.shape}"
        )

    # -- state finite values --
    if not np.isfinite(encoded).all():
        raise ValueError("encoded_state contains NaN or Inf values")

    # -- camera presence & shape/value contract --
    camera_keys = input_spec.camera_keys
    image_shapes: Mapping[str, Tuple[int, int, int]] = dict(
        zip(camera_keys, input_spec.image_shapes)
    )
    snapshot_images = snapshot.images
    available = set(snapshot_images.keys())

    for camera_name in camera_keys:
        if camera_name not in available:
            raise KeyError(
                f"Snapshot missing required camera '{camera_name}': "
                f"available keys are {sorted(available)}"
            )

        img = np.asarray(snapshot_images[camera_name])

        expected = image_shapes.get(camera_name)
        if expected is not None and img.shape != expected:
            raise ValueError(
                f"Image '{camera_name}' has shape {img.shape}, "
                f"expected {expected}"
            )

        if not np.isfinite(img).all():
            raise ValueError(
                f"Image '{camera_name}' contains NaN or Inf values"
            )


# ===================================================================
# Micro-element 2: State tensor representation conversion
# ===================================================================

def tensorize_state(encoded_state: np.ndarray) -> torch.Tensor:
    """Convert physical state ndarray to a CPU float32 tensor.

    Changes only container and dtype; does **not** alter numeric scale.

    Args:
        encoded_state: shape ``(state_dim,)`` numpy array in physical
            semantics.

    Returns:
        shape ``(state_dim,)`` ``torch.float32`` CPU tensor.
    """
    return torch.as_tensor(encoded_state, dtype=torch.float32)


# ===================================================================
# Micro-element 3: State numeric normalization
# ===================================================================

def normalize_state(
    state_tensor: torch.Tensor,
    state_normalizer: Any,
) -> torch.Tensor:
    """Apply the state normalizer to the physical state tensor.

    Calls ``state_normalizer.normalize()`` exactly once, then verifies that
    the output shape is preserved and that all values are finite.

    Args:
        state_tensor: shape ``(state_dim,)`` float32 CPU tensor.
        state_normalizer: ``ActionStateNormalizer`` instance.

    Returns:
        shape ``(state_dim,)`` normalized float32 tensor.

    Raises:
        ValueError: output shape mismatch or NaN/Inf in output.
    """
    normalized_np = state_normalizer.normalize(state_tensor)
    # normalizer returns a numpy array
    normalized_np = np.asarray(normalized_np, dtype=np.float32)

    if normalized_np.shape != state_tensor.shape:
        raise ValueError(
            f"state_normalizer changed output shape: "
            f"{state_tensor.shape} -> {normalized_np.shape}"
        )
    if not np.isfinite(normalized_np).all():
        raise ValueError("state_normalizer produced NaN or Inf values")

    return torch.as_tensor(normalized_np, dtype=torch.float32)


# ===================================================================
# Micro-element 4: Image tensor binding
# ===================================================================

def bind_images(
    snapshot_images: Dict[str, object],
    input_spec: PolicyInputSpec,
) -> Dict[str, torch.Tensor]:
    """Bind snapshot images to policy feature keys.

    For each camera name in ``input_spec.camera_keys``, looks up the image in
    ``snapshot_images``, converts it to a float32 tensor, and stores it
    under the full policy key ``<image_prefix><camera_name>``.

    Does **not** resize, recolor, re-layout, or apply visual
    normalization -- those all belong to L2-02.

    Args:
        snapshot_images: ``ObservationSnapshot.images`` mapping.
        input_spec:        canonical frozen ``PolicyInputSpec``.

    Returns:
        ``{full_policy_key: Tensor(C, H, W)}`` for each camera.

    Raises:
        KeyError: camera name missing from ``snapshot_images``.
    """
    camera_keys = input_spec.camera_keys
    prefix = input_spec.image_prefix

    bound: Dict[str, torch.Tensor] = {}
    for camera_name in camera_keys:
        img = snapshot_images[camera_name]
        full_key = f"{prefix}{camera_name}"
        bound[full_key] = torch.as_tensor(img, dtype=torch.float32)

    return bound


# ===================================================================
# Micro-element 5: Batch dimension addition
# ===================================================================

def add_batch_dim(*tensors: torch.Tensor) -> tuple[torch.Tensor, ...]:
    """Add a leading batch dimension (``B=1``) to every given tensor.

    Used for both state ``(D,) -> (1, D)`` and image ``(C, H, W) -> (1, C, H, W)``.

    Args:
        *tensors: one or more single-sample tensors.

    Returns:
        Tuple of the same tensors with ``B=1`` prepended.
    """
    return tuple(t.unsqueeze(0) for t in tensors)


# ===================================================================
# Micro-element 6: ACT batch assembly
# ===================================================================

def assemble_act_batch(
    state_tensor: torch.Tensor,
    image_tensors: Dict[str, torch.Tensor],
    input_spec: PolicyInputSpec,
) -> Dict[str, torch.Tensor]:
    """Assemble the ACT observation batch dict.

    Writes ``observation.state`` and ``observation.images.<camera>`` keys
    only.  Does **not** write ``task``, ``action``, request/time fields, or
    any runtime metadata.

    Args:
        state_tensor:  shape ``(1, state_dim)`` batched state tensor.
        image_tensors: camera tensors keyed by full policy key
                       ``<image_prefix><camera>``.
        input_spec:    canonical frozen ``PolicyInputSpec`` (provides
                       ``state_key``).

    Returns:
        ACT batch dict ready for ``align_to_device``.
    """
    state_key = input_spec.state_key
    batch: Dict[str, torch.Tensor] = {state_key: state_tensor}
    batch.update(image_tensors)
    return batch


# ===================================================================
# Micro-element 7: Device alignment
# ===================================================================

def align_to_device(
    batch: Dict[str, torch.Tensor],
    device: torch.device,
) -> Dict[str, torch.Tensor]:
    """Move every tensor in the batch to the target device.

    Does **not** auto-switch device on failure and does **not** cache
    pinned-memory buffers.  Each call produces new tensors on the target
    device.

    Args:
        batch:  CPU batch dict from ``assemble_act_batch``.
        device: target ``torch.device`` (e.g. ``cuda:0`` or ``cpu``).

    Returns:
        Batch dict with all tensors residing on ``device``.
    """
    return {key: t.to(device) for key, t in batch.items()}


# ===================================================================
# Stage-1 orchestration: prepare_observation_batch
# ===================================================================

def prepare_observation_batch(
    snapshot: Any,  # ObservationSnapshot
    state_normalizer: Any,  # ActionStateNormalizer
    input_spec: PolicyInputSpec,
    device: torch.device,
) -> Dict[str, torch.Tensor]:
    """Orchestrate the 7 observation batch micro-elements.

    Chains:
      1. ``check_model_input_compatibility``
      2. ``tensorize_state``
      3. ``normalize_state``
      4. ``bind_images``
      5. ``add_batch_dim``  (state + each image)
      6. ``assemble_act_batch``
      7. ``align_to_device``

    Args:
        snapshot:         validated ``ObservationSnapshot``.
        state_normalizer: instance from L2-01.
        input_spec:       canonical frozen ``PolicyInputSpec`` (see module
                         docstring).
        device:           target inference device.

    Returns:
        ACT batch dict with all tensors on ``device``, containing
        ``observation.state`` and ``observation.images.*`` keys.

    Raises:
        Propagates exceptions from any micro-element.
    """
    with torch.no_grad():
        # 1. Compatibility
        check_model_input_compatibility(snapshot, input_spec)

        # 2. State tensor representation
        state_t = tensorize_state(snapshot.encoded_state)

        # 3. State numeric normalization
        norm_state = normalize_state(state_t, state_normalizer)

        # 4. Image tensor binding
        image_map = bind_images(snapshot.images, input_spec)

        # 5. Batch dimension on state
        (batched_state,) = add_batch_dim(norm_state)

        # 5. (cont.) Batch dimension on each image
        batched_images: Dict[str, torch.Tensor] = {}
        for key, img_t in image_map.items():
            (batched_img,) = add_batch_dim(img_t)
            batched_images[key] = batched_img

        # 6. Assemble batch dict
        batch = assemble_act_batch(batched_state, batched_images, input_spec)

        # 7. Device alignment
        return align_to_device(batch, device)
