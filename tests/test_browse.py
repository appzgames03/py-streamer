"""Unit tests for the file browser blueprint and dashboard in pyst.server.browse."""

from pathlib import Path
import pytest
from pyst.server.app import create_app
import pyst.config as config


@pytest.fixture
def app_and_client(tmp_path: Path, monkeypatch):
    """Fixture that configures temporary directories and returns a test client."""
    downloads_dir = tmp_path / "downloads"
    completed_dir = tmp_path / "completed"
    downloads_dir.mkdir()
    completed_dir.mkdir()

    monkeypatch.setattr(config, "DOWNLOADS_DIR", downloads_dir)
    monkeypatch.setattr(config, "COMPLETED_DIR", completed_dir)

    app = create_app({
        "TESTING": True,
        "DOWNLOADS_DIR": downloads_dir,
        "COMPLETED_DIR": completed_dir,
    })
    client = app.test_client()
    return client, downloads_dir, completed_dir


def test_dashboard_route(app_and_client):
    """Test that the dashboard loads with HTTP 200 and expected markup."""
    client, downloads_dir, _ = app_and_client
    res = client.get("/")
    assert res.status_code == 200
    assert b"pyst Media Server" in res.data
    assert b"File Browser" in res.data


def test_browse_empty_directory(app_and_client):
    """Test browsing an empty directory."""
    client, downloads_dir, _ = app_and_client
    res = client.get("/browse")
    assert res.status_code == 200
    assert b"This directory is empty." in res.data


def test_browse_files_and_subdirectories(app_and_client):
    """Test directory listing with files, subdirectories, and completed markers."""
    client, downloads_dir, completed_dir = app_and_client

    # Create dummy files and subdirs
    (downloads_dir / "Movies").mkdir()
    sample_video = downloads_dir / "Movies" / "test_video.mp4"
    sample_video.write_bytes(b"dummy video data")

    # Mark as completed
    (completed_dir / "Movies" / "test_video.mp4.completed").parent.mkdir(parents=True, exist_ok=True)
    (completed_dir / "Movies" / "test_video.mp4.completed").touch()

    # Browse root
    res = client.get("/browse")
    assert res.status_code == 200
    assert b"Movies" in res.data

    # Browse subdirectory
    res = client.get("/browse?path=Movies")
    assert res.status_code == 200
    assert b"test_video.mp4" in res.data
    assert b"Stream" in res.data
    assert b"Download" in res.data


def test_browse_path_traversal_blocked(app_and_client):
    """Test that accessing paths outside downloads returns 403."""
    client, _, _ = app_and_client
    res = client.get("/browse?path=../../etc")
    assert res.status_code == 403


def test_download_file(app_and_client):
    """Test downloading an existing file."""
    client, downloads_dir, _ = app_and_client
    file_to_download = downloads_dir / "document.txt"
    file_to_download.write_text("Hello pyst!")

    res = client.get("/download?path=document.txt")
    assert res.status_code == 200
    assert b"Hello pyst!" in res.data
    assert "attachment" in res.headers.get("Content-Disposition", "")


def test_download_missing_or_invalid_file(app_and_client):
    """Test download errors for missing or traversing paths."""
    client, _, _ = app_and_client

    # Missing path param
    res = client.get("/download")
    assert res.status_code == 400

    # Non-existent file
    res = client.get("/download?path=does_not_exist.mp4")
    assert res.status_code == 404

    # Traversal attempt
    res = client.get("/download?path=../../test.txt")
    assert res.status_code == 403
