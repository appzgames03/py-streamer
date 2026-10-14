"""Unit tests for the synchronized playback blueprint in pyst.server.sync."""

from pathlib import Path
import pytest
from pyst.server.app import create_app


@pytest.fixture
def sync_client(tmp_path: Path):
    """Fixture providing a test client with a test video file."""
    downloads_dir = tmp_path / "downloads"
    downloads_dir.mkdir()

    test_video = downloads_dir / "party.mp4"
    test_video.write_bytes(b"dummy sync video stream")

    app = create_app({
        "TESTING": True,
        "DOWNLOADS_DIR": downloads_dir,
    })
    client = app.test_client()
    return client, downloads_dir, test_video


def test_sync_index_redirect(sync_client):
    """Test /sync/ redirects to /sync/watch."""
    client, _, _ = sync_client
    res = client.get("/sync/")
    assert res.status_code == 302
    assert "/sync/watch" in res.headers.get("Location", "")


def test_sync_host_and_watch_pages(sync_client):
    """Test host and client HTML page rendering."""
    client, _, _ = sync_client

    # Host page
    res_host = client.get("/sync/host")
    assert res_host.status_code == 200
    assert b"Host" in res_host.data
    assert b"party.mp4" in res_host.data

    # Watch (client) page
    res_watch = client.get("/sync/watch")
    assert res_watch.status_code == 200
    assert b"Client" in res_watch.data


def test_sync_control_flow(sync_client):
    """Test control commands: select video, pause, and seek."""
    client, _, _ = sync_client

    # 1. Select video
    res = client.post("/sync/api/control", json={"action": "select", "file": "party.mp4"})
    assert res.status_code == 200
    data = res.get_json()
    assert data["file"] == "party.mp4"
    assert data["playing"] is True
    assert abs(data["position"]) < 0.5

    # 2. Pause
    res = client.post("/sync/api/control", json={"action": "pause", "position": 25.5})
    assert res.status_code == 200
    data = res.get_json()
    assert data["playing"] is False
    assert abs(data["position"] - 25.5) < 0.1

    # 3. Read state
    res_state = client.get("/sync/api/state")
    assert res_state.status_code == 200
    state = res_state.get_json()
    assert state["file"] == "party.mp4"
    assert state["playing"] is False

    # 4. Invalid action
    res_bad = client.post("/sync/api/control", json={"action": "jump_to_hyperspace"})
    assert res_bad.status_code == 400


def test_sync_video_serving(sync_client):
    """Test /sync/video endpoint serving video content."""
    client, _, test_video = sync_client
    res = client.get("/sync/video?path=party.mp4")
    assert res.status_code == 200
    assert res.data == test_video.read_bytes()

    # Traversal test
    res_traversal = client.get("/sync/video?path=../../test.txt")
    assert res_traversal.status_code == 403


def test_root_sync_endpoints_compatibility(sync_client):
    """Test that original endpoints (/host, /watch, /client, /api/state) also resolve cleanly."""
    client, _, _ = sync_client

    assert client.get("/host").status_code == 200
    assert client.get("/watch").status_code == 200
    assert client.get("/client").status_code == 200
    assert client.get("/api/state").status_code == 200
    assert client.get("/video?path=party.mp4").status_code == 200
