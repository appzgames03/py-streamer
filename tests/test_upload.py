"""Unit tests for the file and directory upload blueprint in pyst.server.upload."""

import io
from pathlib import Path
import pytest
from pyst.server.app import create_app


@pytest.fixture
def upload_client(tmp_path: Path):
    """Fixture providing a test client configured with a temporary uploads directory."""
    uploads_dir = tmp_path / "uploads"
    uploads_dir.mkdir()

    app = create_app({
        "TESTING": True,
        "UPLOADS_DIR": uploads_dir,
    })
    client = app.test_client()
    return client, uploads_dir


def test_upload_page_renders(upload_client):
    """Test that the upload UI renders successfully."""
    client, _ = upload_client
    res = client.get("/upload")
    assert res.status_code == 200
    assert b"Upload Center" in res.data
    assert b"Drag and drop files here" in res.data


def test_upload_single_file(upload_client):
    """Test uploading an individual file."""
    client, uploads_dir = upload_client
    file_content = b"This is a test upload file."

    data = {
        "file": (io.BytesIO(file_content), "test_doc.txt"),
        "relpath": "test_doc.txt",
    }
    res = client.post("/upload", data=data, content_type="multipart/form-data")
    assert res.status_code == 200
    json_data = res.get_json()
    assert json_data["status"] == "ok"
    assert json_data["path"] == "test_doc.txt"

    saved_file = uploads_dir / "test_doc.txt"
    assert saved_file.exists()
    assert saved_file.read_bytes() == file_content


def test_upload_nested_directory(upload_client):
    """Test uploading a file with a relative folder path (webkitdirectory)."""
    client, uploads_dir = upload_client
    file_content = b"Nested video episode."

    data = {
        "file": (io.BytesIO(file_content), "ep01.mp4"),
        "relpath": "MyShow/Season1/ep01.mp4",
    }
    res = client.post("/upload", data=data, content_type="multipart/form-data")
    assert res.status_code == 200

    saved_file = uploads_dir / "MyShow" / "Season1" / "ep01.mp4"
    assert saved_file.exists()
    assert saved_file.read_bytes() == file_content


def test_upload_directory_traversal_blocked(upload_client):
    """Test that directory traversal attempts during upload are blocked with 403."""
    client, _ = upload_client
    data = {
        "file": (io.BytesIO(b"malicious payload"), "evil.sh"),
        "relpath": "../../evil.sh",
    }
    res = client.post("/upload", data=data, content_type="multipart/form-data")
    assert res.status_code == 403


def test_upload_missing_file(upload_client):
    """Test that requests with no file payload return 400 Bad Request."""
    client, _ = upload_client
    res = client.post("/upload", data={}, content_type="multipart/form-data")
    assert res.status_code == 400
