"""Runtime adapter for the independent official LeRobot exporter process."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

from schemas.lerobot_export import LeRobotExportRequest


DEFAULT_LEROBOT_PYTHON = Path(
    "/home/hit/ROS/src/data_clean/.conda-envs/lerobot-export/bin/python"
)
LEROBOT_PYTHON_ENV = "DATA_CLEAN_LEROBOT_PYTHON"


class OfficialLeRobotExporterError(RuntimeError):
    """Raised when preflight or the isolated exporter process fails."""


def lerobot_python_path() -> Path:
    return Path(os.environ.get(LEROBOT_PYTHON_ENV, str(DEFAULT_LEROBOT_PYTHON))).expanduser().resolve()


def preflight_official_exporter(*, report_dir: str | Path) -> dict[str, Any]:
    report_path = Path(report_dir).expanduser().resolve()
    report_path.mkdir(parents=True, exist_ok=True)
    response = report_path / "lerobot_exporter_preflight.json"
    python = lerobot_python_path()
    if not python.is_file() or not os.access(python, os.X_OK):
        raise OfficialLeRobotExporterError(
            f"official LeRobot exporter Python is missing or not executable: {python}"
        )
    request_placeholder = report_path / "lerobot_exporter_preflight_request.json"
    request_placeholder.write_text("{}", encoding="utf-8")
    process = subprocess.run(
        [
            str(python),
            "-m",
            "service.lerobot_official_exporter",
            "--request",
            str(request_placeholder),
            "--response",
            str(response),
            "--preflight",
        ],
        text=True,
        capture_output=True,
        check=False,
        env=_exporter_environment(),
    )
    data = _read_response(response, process)
    if process.returncode != 0 or data.get("status") != "success":
        raise OfficialLeRobotExporterError(
            f"official LeRobot exporter preflight failed: {_response_error(data, process)}"
        )
    return data


def run_official_exporter(
    request: LeRobotExportRequest,
    *,
    exchange_dir: str | Path,
) -> dict[str, Any]:
    exchange = Path(exchange_dir).expanduser().resolve()
    exchange.mkdir(parents=True, exist_ok=True)
    request_path = exchange / "lerobot_export_request.json"
    response_path = exchange / "lerobot_export_response.json"
    request_path.write_text(
        json.dumps(request.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    python = lerobot_python_path()
    process = subprocess.run(
        [
            str(python),
            "-m",
            "service.lerobot_official_exporter",
            "--request",
            str(request_path),
            "--response",
            str(response_path),
        ],
        text=True,
        capture_output=True,
        check=False,
        env=_exporter_environment(),
    )
    result = _read_response(response_path, process)
    result["process"] = {
        "returncode": process.returncode,
        "stdout": process.stdout[-8000:],
        "stderr": process.stderr[-8000:],
        "python": str(python),
    }
    if process.returncode != 0 or result.get("status") != "success":
        raise OfficialLeRobotExporterError(_response_error(result, process))
    return result


def _exporter_environment() -> dict[str, str]:
    data_clean_source = Path(__file__).resolve().parents[1]
    lerobot_source = (
        data_clean_source.parent / "model_deploy/third_party/lerobot/src"
    ).resolve()
    existing = os.environ.get("PYTHONPATH", "")
    return {
        **os.environ,
        "PYTHONPATH": os.pathsep.join(
            value
            for value in (str(data_clean_source), str(lerobot_source), existing)
            if value
        ),
        "HF_HUB_OFFLINE": os.environ.get("HF_HUB_OFFLINE", "1"),
    }


def _read_response(path: Path, process: subprocess.CompletedProcess[str]) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise OfficialLeRobotExporterError(
            f"exporter did not produce a valid JSON response: {exc}; stderr={process.stderr[-2000:]}"
        ) from exc
    if not isinstance(value, dict):
        raise OfficialLeRobotExporterError("exporter response must be a JSON object")
    return value


def _response_error(
    data: dict[str, Any],
    process: subprocess.CompletedProcess[str],
) -> str:
    error = data.get("error")
    if isinstance(error, dict):
        detail = f"{error.get('type', 'Error')}: {error.get('message', '')}"
    else:
        detail = str(error or "unknown exporter failure")
    stderr = process.stderr.strip()
    return f"{detail}" + (f"; stderr={stderr[-2000:]}" if stderr else "")
