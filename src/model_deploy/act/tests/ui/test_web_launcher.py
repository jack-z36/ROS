"""Regression tests for the ACT Web 控制中心 outer-process UI."""

import asyncio
import time
import yaml
from pathlib import Path

from model_deploy.act.ui import web_launcher


_STATIC_DIR = Path(web_launcher.__file__).parent / "static"


class _QuietLogManager:
    """A manager whose log long-poll deliberately blocks for a short time."""

    def wait_for_new_logs(self, after_seq: int, timeout: float = 15.0) -> list[dict]:
        del after_seq, timeout
        time.sleep(0.08)
        return []


def test_log_long_poll_does_not_block_asyncio_event_loop(monkeypatch):
    """A quiet /ws/logs connection must not freeze unrelated HTTP requests."""
    manager = _QuietLogManager()

    async def scenario():
        monkeypatch.setattr(web_launcher, "_process_manager", manager)
        task = asyncio.create_task(web_launcher._wait_for_new_logs(manager, 0))

        # This timer can only run before the log wait finishes when the wait is
        # offloaded from the ASGI event loop.
        await asyncio.sleep(0.01)
        assert not task.done()
        assert await task == []

    asyncio.run(scenario())


def test_outer_web_shutdown_stops_its_launch_group(monkeypatch):
    class _Manager:
        def __init__(self) -> None:
            self.stop_called = False

        def stop(self) -> dict:
            self.stop_called = True
            return {"ok": True}

    manager = _Manager()
    monkeypatch.setattr(web_launcher, "_process_manager", manager)

    asyncio.run(web_launcher._on_shutdown())

    assert manager.stop_called is True


def test_dashboard_vendors_browser_dependencies_locally():
    html = (_STATIC_DIR / "dashboard.html").read_text(encoding="utf-8")

    assert "https://unpkg.com/vue" not in html
    assert "https://cdn.tailwindcss.com" not in html
    assert "https://cdn.jsdelivr.net/npm/echarts" not in html
    for filename in ("vue.global.prod.js", "tailwindcss.js", "echarts.min.js"):
        assert (_STATIC_DIR / "vendor" / filename).stat().st_size > 0


def test_dashboard_reconnects_image_streams_after_inner_startup():
    html = (_STATIC_DIR / "dashboard.html").read_text(encoding="utf-8")

    assert "@error=\"scheduleImageRetry\"" in html
    assert "imageStreamVersion" in html
    assert "refreshImageStreams" in html


def test_web_launcher_materializes_checkpoint_config_without_bundle(tmp_path):
    config_path = tmp_path / "deploy.yaml"
    config_path.write_text(
        yaml.safe_dump(
            {
                "bundle": {"bundle_dir": "/old/deploy_bundle"},
                "runtime": {"mode": "dry-run"},
            }
        ),
        encoding="utf-8",
    )
    manager = web_launcher.ActProcessManager(
        str(config_path),
        default_checkpoint_dir="/models/checkpoints/100000",
    )

    materialized = Path(manager._materialize_config())
    payload = yaml.safe_load(materialized.read_text(encoding="utf-8"))

    assert payload["model"]["checkpoint_dir"] == "/models/checkpoints/100000"
    assert payload["bundle"]["bundle_dir"] is None
    manager._cleanup_temp_configs()
