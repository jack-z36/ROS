from __future__ import annotations

import json
from pathlib import Path
import threading
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from ui.web_launcher import (
    DataCleanRequestHandler,
    INDEX_HTML,
    TRAJECTORY_VIDEO_SCHEMA_VERSION,
    _build_trajectory_video_metadata,
    _hydrate_trajectory_video_urls,
    _trajectory_video_relative_path,
)


class _FakeCell:
    def __init__(self, value):
        self.value = value

    def as_py(self):
        return self.value


class _FakeColumn:
    def __init__(self, values):
        self.values = values

    def __getitem__(self, index):
        return _FakeCell(self.values[index])


class _FakeTable:
    def __init__(self, columns):
        self._columns = columns
        self.column_names = list(columns)
        self.num_rows = len(next(iter(columns.values())))

    def __getitem__(self, name):
        return _FakeColumn(self._columns[name])


class _FakeParquet:
    table = _FakeTable(
        {
            "episode_index": [0, 1],
            "videos/observation.images.left/chunk_index": [0, 0],
            "videos/observation.images.left/file_index": [0, 0],
            "videos/observation.images.left/from_timestamp": [0.0, 18.2],
            "videos/observation.images.left/to_timestamp": [18.2, 41.133333],
            "videos/observation.images.right/chunk_index": [0, 0],
            "videos/observation.images.right/file_index": [0, 0],
            "videos/observation.images.right/from_timestamp": [0.0, 18.2],
            "videos/observation.images.right/to_timestamp": [18.2, 41.133333],
        }
    )

    @classmethod
    def read_table(cls, _path):
        return cls.table


def _dataset_tree(tmp_path: Path) -> Path:
    dataset = tmp_path / "dataset"
    (dataset / "meta/episodes/chunk-000").mkdir(parents=True)
    (dataset / "videos/observation.images.left/chunk-000").mkdir(parents=True)
    (dataset / "videos/observation.images.right/chunk-000").mkdir(parents=True)
    (dataset / "meta/info.json").write_text(
        json.dumps(
            {
                "fps": 15,
                "video_path": "videos/{video_key}/chunk-{chunk_index:03d}/file-{file_index:03d}.mp4",
                "features": {
                    "observation.images.left": {"dtype": "video", "info": {"video.fps": 15}},
                    "observation.images.right": {"dtype": "video", "info": {"video.fps": 15}},
                },
            }
        ),
        encoding="utf-8",
    )
    (dataset / "meta/episodes/chunk-000/file-000.parquet").write_bytes(b"placeholder")
    for side in ("left", "right"):
        (dataset / f"videos/observation.images.{side}/chunk-000/file-000.mp4").write_bytes(b"mp4")
    return dataset


def test_trajectory_video_metadata_contains_episode_ranges_and_urls(tmp_path: Path) -> None:
    dataset = _dataset_tree(tmp_path)
    media = _build_trajectory_video_metadata(dataset, _FakeParquet)

    assert media["schema_version"] == TRAJECTORY_VIDEO_SCHEMA_VERSION
    assert {stream["stream_id"] for stream in media["streams"]} == {"left", "right"}
    left = next(stream for stream in media["streams"] if stream["stream_id"] == "left")
    assert left["episodes"]["1"]["from_timestamp"] == pytest.approx(18.2)
    assert left["episodes"]["1"]["available"] is True

    hydrated = _hydrate_trajectory_video_urls(
        {"video_media": media},
        "job with spaces",
    )
    url = hydrated["video_media"]["streams"][0]["episodes"]["0"]["url"]
    assert url.endswith("/trajectory-video/observation.images.left/0/0") or url.endswith(
        "/trajectory-video/observation.images.right/0/0"
    )
    assert "job%20with%20spaces" in url


def test_trajectory_video_path_rejects_escape(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="escapes dataset"):
        _trajectory_video_relative_path(
            tmp_path,
            "../outside/{video_key}.mp4",
            "observation.images.left",
            0,
            0,
        )


def test_quality_details_are_marked_for_refresh_state_and_poll_is_guarded() -> None:
    assert "captureQualityDetails" in INDEX_HTML
    assert "restoreQualityDetails" in INDEX_HTML
    assert "data-detail-key=\"v2-forge\"" in INDEX_HTML
    assert "state.jobPollInFlight" in INDEX_HTML


def test_programmatic_video_seek_does_not_stop_trajectory_playback() -> None:
    assert "_trajectoryProgrammaticSeekUntil" in INDEX_HTML
    assert "video._trajectoryProgrammaticSeekUntil > performance.now()" in INDEX_HTML
    assert "_trajectoryProgrammaticPlayUntil" in INDEX_HTML
    assert "_trajectoryProgrammaticPauseUntil" in INDEX_HTML
    assert "|| !video.paused" in INDEX_HTML


def test_trajectory_video_route_supports_http_range(tmp_path: Path) -> None:
    video = tmp_path / "video.mp4"
    video.write_bytes(b"0123456789")

    class _AppState:
        @staticmethod
        def trajectory_video(_job_id, _feature, _chunk_index, _file_index):
            return video

    from http.server import ThreadingHTTPServer

    DataCleanRequestHandler.app_state = _AppState()
    server = ThreadingHTTPServer(("127.0.0.1", 0), DataCleanRequestHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        request = Request(
            f"http://127.0.0.1:{server.server_port}/api/jobs/job/trajectory-video/observation.images.left/0/0",
            headers={"Range": "bytes=2-5"},
        )
        with urlopen(request) as response:
            assert response.status == 206
            assert response.headers["Content-Range"] == "bytes 2-5/10"
            assert response.read() == b"2345"
        bad_request = Request(
            f"http://127.0.0.1:{server.server_port}/api/jobs/job/trajectory-video/observation.images.left/0/0",
            headers={"Range": "bytes=bad"},
        )
        with pytest.raises(HTTPError) as error:
            urlopen(bad_request)
        assert error.value.code == 416
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
