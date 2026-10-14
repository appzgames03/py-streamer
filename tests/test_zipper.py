"""Unit tests for the zipper utility in pyst.zipper."""

from pathlib import Path
import zipfile
import pytest

from pyst.zipper import zip_folder


def test_zip_folder_creates_valid_archive(tmp_path: Path):
    """Test compressing a directory and verifying zip archive contents."""
    source_dir = tmp_path / "my_media"
    source_dir.mkdir()

    (source_dir / "ep1.txt").write_text("Episode 1 content")
    (source_dir / "Season2").mkdir()
    (source_dir / "Season2" / "ep2.txt").write_text("Episode 2 content")

    out_zip = tmp_path / "my_media.zip"
    result_path = zip_folder(source_dir, out_zip)

    assert result_path == out_zip
    assert out_zip.is_file()

    # Unpack and verify structure
    with zipfile.ZipFile(out_zip, "r") as z:
        namelist = z.namelist()
        assert "my_media/ep1.txt" in namelist
        assert "my_media/Season2/ep2.txt" in namelist
        assert z.read("my_media/ep1.txt") == b"Episode 1 content"


def test_zip_nonexistent_directory(tmp_path: Path):
    """Test that zipping a non-existent path raises ValueError."""
    fake_path = tmp_path / "does_not_exist"
    with pytest.raises(ValueError):
        zip_folder(fake_path)
