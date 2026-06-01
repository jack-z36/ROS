"""CLI developer entry for the temporary bimanual Forge bridge."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from service.forge_bridge import (
    ForgeBridgeConfig,
    ForgeBridgeError,
    write_forge_bridge,
)


def run_forge_bridge_check(
    *,
    aligned_mcap_path: str | Path,
    output_dir: str | Path,
    mode: str = "format-only",
    pose_source_profile: str | None = None,
    calibration_ready: bool = False,
    max_pose_abs_m: float = 10.0,
) -> dict:
    """Run the bridge and return a JSON-friendly developer-check result."""

    active_profile = pose_source_profile or mode
    try:
        result = write_forge_bridge(
            aligned_mcap_path=aligned_mcap_path,
            output_dir=output_dir,
            config=ForgeBridgeConfig(
                mode=mode,
                pose_source_profile=active_profile,
                calibration_ready=calibration_ready,
                max_pose_abs_m=max_pose_abs_m,
            ),
        )
        return {"status": "success", "outputs": asdict(result), "errors": []}
    except ForgeBridgeError as exc:
        return {
            "status": "failed",
            "outputs": {
                "forge_bridge_report": str(
                    Path(output_dir).expanduser().resolve()
                    / "forge_bridge_report.json"
                )
            },
            "errors": [{"type": type(exc).__name__, "message": str(exc)}],
        }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--aligned-mcap", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument(
        "--mode",
        choices=("format-only", "formal"),
        default="format-only",
    )
    parser.add_argument(
        "--pose-source-profile",
        choices=("format-only", "formal"),
    )
    parser.add_argument("--calibration-ready", action="store_true")
    parser.add_argument("--max-pose-abs-m", type=float, default=10.0)
    args = parser.parse_args()
    result = run_forge_bridge_check(
        aligned_mcap_path=args.aligned_mcap,
        output_dir=args.output_dir,
        mode=args.mode,
        pose_source_profile=args.pose_source_profile,
        calibration_ready=args.calibration_ready,
        max_pose_abs_m=args.max_pose_abs_m,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "success" else 1


if __name__ == "__main__":
    raise SystemExit(main())
