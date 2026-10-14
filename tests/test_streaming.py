"""Unit tests for video streaming and HTTP Range request handling in pyst.server.streaming."""

from pathlib import Path
import pytest
from pyst.server.app import create_app


@pytest.fixture
def streaming_client(tmp_path: Path):
    """Fixture providing a test client and sample video file."""
    downloads_dir = tmp_path / "downloads"
    downloads_dir.mkdir()

    sample_video = downloads_dir / "sample.mp4"
    # Create 1000 bytes of dummy video content
    sample_video.write_bytes(bytes([i % 256 for i in range(1000)]))

    app = create_app({
        "TESTING": True,
        "DOWNLOADS_DIR": downloads_dir,
    })
    client = app.test_client()
    return client, downloads_dir, sample_video


def test_stream_page_renders(streaming_client):
    """Test that the /stream page renders HTML with player and metadata."""
    client, _, _ = streaming_client
    res = client.get("/stream?path=sample.mp4")
    assert res.status_code == 200
    assert b"sample.mp4" in res.data
    assert b"<video" in res.data
    assert b"/play?path=sample.mp4" in res.data


def test_stream_page_missing_or_invalid(streaming_client):
    """Test /stream errors when path is missing or file does not exist."""
    client, _, _ = streaming_client

    # Missing path
    res = client.get("/stream")
    assert res.status_code == 400

    # Non-existent file
    res = client.get("/stream?path=nonexistent.mp4")
    assert res.status_code == 404


def test_play_full_file(streaming_client):
    """Test /play streaming full content when no Range header is sent."""
    client, _, sample_video = streaming_client
    res = client.get("/play?path=sample.mp4")
    assert res.status_code == 200
    assert len(res.data) == 1000
    assert res.data == sample_video.read_bytes()


def test_play_range_header_seeking(streaming_client):
    """Test /play returns 206 Partial Content when Range header is provided."""
    client, _, sample_video = streaming_client

    # Request first 100 bytes (0-99)
    res = client.get("/play?path=sample.mp4", headers={"Range": "bytes=0-99"})
    assert res.status_code == 206
    assert res.headers.get("Content-Range") == "bytes 0-99/1000"
    assert res.headers.get("Accept-Ranges") == "bytes"
    assert res.headers.get("Content-Length") == "100"
    assert len(res.data) == 100
    assert res.data == sample_video.read_bytes()[:100]

    # Request middle range (500-599)
    res = client.get("/play?path=sample.mp4", headers={"Range": "bytes=500-599"})
    assert res.status_code == 206
    assert res.headers.get("Content-Range") == "bytes 500-599/1000"
    assert res.headers.get("Content-Length") == "100"
    assert len(res.data) == 100
    assert res.data == sample_video.read_bytes()[500:600]


def test_movie_endpoint_with_single_video_config(tmp_path: Path):
    """Test /movie endpoint when VIDEO_PATH is configured on the app."""
    video_file = tmp_path / "standalone.mp4"
    video_file.write_bytes(b"A" * 500)

    app = create_app({
        "TESTING": True,
        "VIDEO_PATH": str(video_file),
    })
    client = app.test_client()

    res = client.get("/movie", headers={"Range": "bytes=0-49"})
    assert res.status_code == 206
    assert res.headers.get("Content-Range") == "bytes 0-49/500"
    assert len(res.data) == 50


def test_streaming_traversal_blocked(streaming_client):
    """Test that traversal attempts on /play return 403."""
    client, _, _ = streaming_client
    res = client.get("/play?path=../../etc/passwd")
    assert res.status_code == 403
