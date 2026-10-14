"""Unit tests for shared utility functions in pyst.utils."""

from pathlib import Path
import pytest
from werkzeug.exceptions import Forbidden

from pyst.utils import get_size, mark_completed, safe_path


def test_safe_path_valid(tmp_path: Path):
    """Test that safe relative paths resolve correctly within base directory."""
    subfile = tmp_path / "video.mp4"
    subfile.touch()

    resolved = safe_path(tmp_path, "video.mp4")
    assert resolved == subfile.resolve()


def test_safe_path_traversal_blocked(tmp_path: Path):
    """Test that directory traversal attempts raise 403 Forbidden."""
    with pytest.raises(Forbidden):
        safe_path(tmp_path, "../../etc/passwd")


def test_get_size_file(tmp_path: Path):
    """Test human readable size for a single file."""
    test_file = tmp_path / "sample.bin"
    test_file.write_bytes(b"A" * 2048)  # 2 KB

    size_str = get_size(test_file)
    assert "KB" in size_str


def test_get_size_directory(tmp_path: Path):
    """Test human readable size calculation for a directory."""
    (tmp_path / "file1.txt").write_bytes(b"A" * 1024)
    (tmp_path / "file2.txt").write_bytes(b"B" * 1024)

    size_str = get_size(tmp_path)
    assert "KB" in size_str


def test_mark_completed(tmp_path: Path):
    """Test creation of completion marker file."""
    marker = mark_completed("my_movie.mkv", tmp_path)
    assert marker.exists()
    assert marker.name == "my_movie.mkv.completed"
