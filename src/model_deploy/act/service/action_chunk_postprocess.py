"""ActionChunk post-processing: raw normalized tensor → physical action chunk.

Implements L2-03 primary stage three: six ordered computation micro-functions
that transform a raw policy output tensor into an action chunk carrying
only physical actions.  Two orchestration entry points share the same six
micro-functions:

- ``postprocess_action_chunk`` → absolute ``ActionChunk`` (cross-module output).
- ``postprocess_relative_action_chunk`` → ``RelativeActionChunk`` (L2-03-internal,
  decoded into absolute by ``RelativeTcpActionDecoder``).

No clamping, cropping, padding, reordering, quaternion or gripper correction
is applied at any step. Unnormalized-action fallback is prohibited.
"""

from __future__ import annotations

import numpy as np
import torch

from model_deploy.act.repo.normalization import ActionStateNormalizer
from model_deploy.act.types.action_chunk import ActionChunk
from model_deploy.act.types.relative_action_chunk import RelativeActionChunk
from model_deploy.act.types.action_spec import ACTION_DIM


# ---------------------------------------------------------------------------
# Micro ①: Raw output structure check
# ---------------------------------------------------------------------------


def check_raw_output_structure(
    raw_output: object,
    expected_chunk_size: int,
) -> torch.Tensor:
    """Validate the raw policy output tensor structure.

    Accepts **only** a finite ``torch.Tensor`` of shape ``(1, N, 16)``
    where ``N == expected_chunk_size``.  No repair is attempted -- any
    deviation is raised immediately.

    Args:
        raw_output:   Value returned by the policy forward pass.
        expected_chunk_size:  Required chunk-length ``N``.

    Returns:
        The validated tensor (same object).

    Raises:
        TypeError:  ``raw_output`` is not a ``torch.Tensor``.
        ValueError: rank != 3, B != 1, N != expected_chunk_size,
                    D != 16, or any element is non-finite.
    """
    if not isinstance(raw_output, torch.Tensor):
        raise TypeError(
            f"Raw output must be a torch.Tensor, got {type(raw_output).__name__}"
        )

    if raw_output.ndim != 3:
        raise ValueError(
            f"Raw output must be rank 3, got ndim={raw_output.ndim}"
        )

    b, n, d = raw_output.shape
    if b != 1:
        raise ValueError(f"Raw output batch dim must be 1, got B={b}")
    if n != expected_chunk_size:
        raise ValueError(
            f"Raw output chunk dim must be {expected_chunk_size}, got N={n}"
        )
    if d != ACTION_DIM:
        raise ValueError(f"Raw output action dim must be {ACTION_DIM}, got D={d}")

    if not torch.isfinite(raw_output).all():
        raise ValueError("Raw output contains NaN or Inf values")

    return raw_output


# ---------------------------------------------------------------------------
# Micro ②: Batch dimension removal
# ---------------------------------------------------------------------------


def remove_batch_dim(tensor_1_N_16: torch.Tensor) -> torch.Tensor:
    """Remove the already-validated batch dimension.

    Only removes the ``B=1`` leading dimension that has been verified by
    ``check_raw_output_structure``.  No squeeze on arbitrary axes.

    Args:
        tensor_1_N_16:  Tensor of shape ``(1, N, 16)``.

    Returns:
        Tensor of shape ``(N, 16)``.
    """
    return tensor_1_N_16[0]


# ---------------------------------------------------------------------------
# Micro ③: Action unnormalization
# ---------------------------------------------------------------------------


def unnormalize_actions(
    normalized: torch.Tensor,
    action_normalizer: ActionStateNormalizer,
) -> np.ndarray:
    """Restore actions to physical scale via the action normalizer.

    Calls ``action_normalizer.unnormalize()`` **exactly once**.  No clamp,
    crop, pad, or reorder is applied.

    Args:
        normalized:        Normalized tensor of shape ``(N, 16)``.
        action_normalizer: Configured ``ActionStateNormalizer`` instance.

    Returns:
        Physical ``np.ndarray`` float32 of shape ``(N, 16)``.
    """
    normalized_np = normalized.detach().cpu().numpy().astype(np.float32, copy=False)
    return action_normalizer.unnormalize(normalized_np)


# ---------------------------------------------------------------------------
# Micro ④: CPU float32 array conversion
# ---------------------------------------------------------------------------


def to_cpu_float32_array(
    tensor_or_array: torch.Tensor | np.ndarray,
) -> np.ndarray:
    """Convert a tensor or array to contiguous C-order CPU ``float32``.

    This is the final representation boundary: every downstream consumer
    receives ``np.ndarray`` of ``dtype=float32``.

    Args:
        tensor_or_array:  A ``torch.Tensor`` or ``np.ndarray``.

    Returns:
        Contiguous C-order numpy ``float32`` array.  When the input is
        already contiguous C-order float32, the returned array may share
        memory with the input.
    """
    if isinstance(tensor_or_array, torch.Tensor):
        arr = tensor_or_array.detach().cpu().numpy().astype(np.float32, copy=False)
    else:
        arr = np.asarray(tensor_or_array, dtype=np.float32)
    # Ensure C-contiguous; ascontiguousarray is a no-op when already contiguous.
    return np.ascontiguousarray(arr, dtype=np.float32)


# ---------------------------------------------------------------------------
# Micro ⑤: Final output contract check
# ---------------------------------------------------------------------------


def check_final_output_contract(
    array: np.ndarray,
    expected_chunk_size: int,
) -> None:
    """Validate the final physical action array before constructing ActionChunk.

    Strictly enforces shape ``(chunk_size, 16)``, ``dtype=float32``, and
    that every element is finite.  This is an output-contract gate -- it
    does **not** apply L2-04 safety range checks.

    Args:
        array:               Physical action array to validate.
        expected_chunk_size: Required number of rows.

    Raises:
        ValueError:  Shape mismatch or non-finite values.
        TypeError:   ``dtype`` is not ``float32``.
    """
    if array.ndim != 2:
        raise ValueError(
            f"Final output must be 2D, got ndim={array.ndim}"
        )
    if array.shape[0] != expected_chunk_size:
        raise ValueError(
            f"Final output must have {expected_chunk_size} rows, "
            f"got {array.shape[0]}"
        )
    if array.shape[1] != ACTION_DIM:
        raise ValueError(
            f"Final output last dim must be {ACTION_DIM}, "
            f"got {array.shape[1]}"
        )
    if array.dtype != np.float32:
        raise TypeError(
            f"Final output dtype must be float32, got {array.dtype}"
        )
    if not np.isfinite(array).all():
        raise ValueError("Final output contains NaN or Inf values")


# ---------------------------------------------------------------------------
# Micro ⑥ + Primary stage three orchestration
# ---------------------------------------------------------------------------


def postprocess_action_chunk(
    raw_chunk: torch.Tensor,
    action_normalizer: ActionStateNormalizer,
    expected_chunk_size: int,
) -> ActionChunk:
    """Primary stage three: raw normalized tensor → physical ActionChunk.

    Executes six ordered micro-functions inside a single synchronous call:

    1. ``check_raw_output_structure``  -- validate rank/shape/finiteness
    2. ``remove_batch_dim``            -- strip verified B=1 dimension
    3. ``unnormalize_actions``         -- restore physical scale
    4. ``to_cpu_float32_array``        -- convert to contiguous numpy float32
    5. ``check_final_output_contract`` -- strict output shape/dtype/finite gate
    6. ``ActionChunk`` construction    -- wrap validated array

    Any step failure propagates immediately; no partial ``ActionChunk``
    is ever returned.

    Args:
        raw_chunk:          Raw normalized tensor from policy, shape ``(1, N, 16)``.
        action_normalizer:  ``ActionStateNormalizer`` for unnormalization.
        expected_chunk_size: Required chunk size ``N``.

    Returns:
        ``ActionChunk(actions=…)`` carrying only the physical action array.

    Raises:
        TypeError / ValueError:  Propagated from any failing micro-function.
    """
    # ① Raw output structure check
    validated = check_raw_output_structure(raw_chunk, expected_chunk_size)

    # ② Batch dimension removal
    unbatch = remove_batch_dim(validated)

    # ③ Action unnormalization
    physical = unnormalize_actions(unbatch, action_normalizer)

    # ④ CPU float32 array conversion
    arr = to_cpu_float32_array(physical)

    # ⑤ Final output contract check
    check_final_output_contract(arr, expected_chunk_size)

    # ⑥ ActionChunk construction
    return ActionChunk(actions=arr)


def postprocess_relative_action_chunk(
    raw_chunk: torch.Tensor,
    action_normalizer: ActionStateNormalizer,
    expected_chunk_size: int,
) -> RelativeActionChunk:
    """Primary stage three variant: raw normalized tensor → RelativeActionChunk.

    Executes the same six ordered micro-functions as
    ``postprocess_action_chunk`` (check → remove batch → unnormalize → to
    float32 → final contract check → wrap), differing only in the wrapper
    type.  The wrapped array is the physical *relative* TCP arm action +
    absolute gripper targets produced by the ACT model; it is an
    L2-03-internal value and never crosses into the control loop.

    This module cannot perform the relative → absolute conversion because it
    does not have the inference-moment ``ObservationState``; that is the job
    of ``RelativeTcpActionDecoder`` inside ``ActInferenceService``.

    Any step failure propagates immediately; no partial
    ``RelativeActionChunk`` is ever returned.

    Args:
        raw_chunk:          Raw normalized tensor from policy, shape ``(1, N, 16)``.
        action_normalizer:  ``ActionStateNormalizer`` for unnormalization.
        expected_chunk_size: Required chunk size ``N``.

    Returns:
        ``RelativeActionChunk(actions=…)`` carrying only the physical relative
        action array.

    Raises:
        TypeError / ValueError:  Propagated from any failing micro-function.
    """
    # ① Raw output structure check
    validated = check_raw_output_structure(raw_chunk, expected_chunk_size)

    # ② Batch dimension removal
    unbatch = remove_batch_dim(validated)

    # ③ Action unnormalization
    physical = unnormalize_actions(unbatch, action_normalizer)

    # ④ CPU float32 array conversion
    arr = to_cpu_float32_array(physical)

    # ⑤ Final output contract check
    check_final_output_contract(arr, expected_chunk_size)

    # ⑥ RelativeActionChunk construction
    return RelativeActionChunk(actions=arr)
