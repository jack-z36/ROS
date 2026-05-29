"""Alignment index Parquet and report JSON sidecar writer for Scene 3.

Provides:
- write_alignment_index:  list[AlignmentIndexRecord] → alignment_index.parquet
- write_alignment_report:  AlignmentReport draft + AlignmentReportFinalization
                           → alignment_report.json

Per L3 service_s3_020 — pure data read/write; no re-computation.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq

from schemas.step_timeline import AlignmentIndexRecord, AlignmentIndexSchema
from schemas.aligned_mcap_report import AlignmentReport, AlignmentReportFinalization


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ensure_parent(output_path: str) -> None:
    """Create parent directory of output_path if it does not exist."""
    parent = os.path.dirname(os.path.abspath(output_path))
    if parent and not os.path.exists(parent):
        os.makedirs(parent, exist_ok=True)


# ---------------------------------------------------------------------------
# JSON report sidecar write
# ---------------------------------------------------------------------------


def write_alignment_report(
    draft: AlignmentReport,
    finalization: AlignmentReportFinalization,
    output_path: str,
) -> str:
    """Write a finalized AlignmentReport to JSON.

    Applies finalization fields (output_aligned_mcap, alignment_index, run_id,
    status, failure_reason) over the draft report, then serializes to JSON.

    Args:
        draft:        AlignmentReport draft (must not be None).
        finalization: AlignmentReportFinalization containing final fields
                      (must not be None).
        output_path:  Path for the output ``alignment_report.json``.

    Returns:
        ``output_path`` on success.

    Raises:
        ValueError: If *draft* or *finalization* is ``None``.
        OSError:    If the output path cannot be written.
    """
    if draft is None:
        raise ValueError("draft must not be None")
    if finalization is None:
        raise ValueError("finalization must not be None")

    # Convert draft to plain dict (recursively converts nested dataclasses)
    report_dict: dict[str, Any] = asdict(draft)

    # Override with finalization fields
    report_dict["output_aligned_mcap"] = finalization.output_aligned_mcap
    report_dict["alignment_index"] = finalization.alignment_index
    report_dict["run_id"] = finalization.run_id
    report_dict["status"] = finalization.status
    report_dict["failure_reason"] = finalization.failure_reason

    _ensure_parent(output_path)

    try:
        with open(output_path, "w") as f:
            json.dump(report_dict, f, indent=2, ensure_ascii=False)
    except OSError as e:
        raise OSError(
            f"Cannot write alignment report to {output_path}: {e}"
        ) from e

    return output_path


# ---------------------------------------------------------------------------
# Parquet index sidecar write
# ---------------------------------------------------------------------------


def _record_to_columns(records: list[AlignmentIndexRecord]) -> dict[str, list[Any]]:
    """Convert a list of AlignmentIndexRecord to column-oriented dict.

    Each column name matches ``AlignmentIndexSchema`` keys.
    Enum values are converted to their string representation.
    """
    cols: dict[str, list[Any]] = {
        "step_index": [],
        "step_time_ns": [],
        "field_name": [],
        "source_topic": [],
        "output_topic": [],
        "source_time_ns": [],
        "alignment_method": [],
        "status": [],
        "dt_ms": [],
        "neighbor_before_time_ns": [],
        "neighbor_after_time_ns": [],
        "window_start_time_ns": [],
        "window_end_time_ns": [],
        "sample_count": [],
        "coverage_ratio": [],
        "fallback_reason": [],
        "message_ref": [],
    }

    for rec in records:
        cols["step_index"].append(rec.step_index)
        cols["step_time_ns"].append(rec.step_time_ns)
        cols["field_name"].append(rec.field_name)
        cols["source_topic"].append(rec.source_topic)
        cols["output_topic"].append(rec.output_topic)
        cols["source_time_ns"].append(rec.source_time_ns)
        cols["alignment_method"].append(rec.alignment_method)
        cols["status"].append(
            rec.status.value if hasattr(rec.status, "value") else rec.status
        )
        cols["dt_ms"].append(rec.dt_ms)
        cols["neighbor_before_time_ns"].append(rec.neighbor_before_time_ns)
        cols["neighbor_after_time_ns"].append(rec.neighbor_after_time_ns)
        cols["window_start_time_ns"].append(rec.window_start_time_ns)
        cols["window_end_time_ns"].append(rec.window_end_time_ns)
        cols["sample_count"].append(rec.sample_count)
        cols["coverage_ratio"].append(rec.coverage_ratio)
        cols["fallback_reason"].append(rec.fallback_reason)
        cols["message_ref"].append(rec.message_ref)

    return cols


def write_alignment_index(
    records: list[AlignmentIndexRecord] | None,
    output_path: str,
) -> str:
    """Write AlignmentIndex records to a Parquet file.

    Each record becomes one row in ``alignment_index.parquet``.
    Schema columns follow ``AlignmentIndexSchema``.

    Args:
        records:    List of AlignmentIndexRecord (must not be None or empty).
        output_path: Path for the output ``alignment_index.parquet``.

    Returns:
        ``output_path`` on success.

    Raises:
        ValueError: If *records* is ``None`` or empty.
        OSError:    If the output path cannot be written.
    """
    if records is None:
        raise ValueError("records must not be None")
    if len(records) == 0:
        raise ValueError("records must not be empty")

    cols = _record_to_columns(records)
    names = list(AlignmentIndexSchema.keys())

    # Build pyarrow arrays from columns — use inferred types that match
    # the AlignmentIndexSchema expectations.
    arrays: list[pa.Array] = []
    for name in names:
        data = cols[name]
        schema_type = AlignmentIndexSchema.get(name, "")
        if schema_type == "int64":
            arrays.append(pa.array(data, type=pa.int64()))
        elif schema_type == "float64":
            arrays.append(pa.array(data, type=pa.float64()))
        else:
            arrays.append(pa.array(data, type=pa.string()))

    table = pa.Table.from_arrays(arrays, names=names)

    _ensure_parent(output_path)

    try:
        pq.write_table(table, output_path)
    except (OSError, pa.ArrowException) as e:
        raise OSError(
            f"Cannot write alignment index to {output_path}: {e}"
        ) from e

    return output_path
