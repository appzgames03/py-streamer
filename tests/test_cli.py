"""Unit tests for the Click CLI interface using CliRunner."""

from pathlib import Path
from click.testing import CliRunner

from pyst import __version__
from pyst.cli import main


def test_cli_version():
    """Test pyst --version output."""
    runner = CliRunner()
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.output


def test_cli_help():
    """Test pyst --help output."""
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "pyst" in result.output
    assert "serve" in result.output
    assert "stream" in result.output
    assert "download" in result.output
    assert "torrent" in result.output
    assert "zip" in result.output


def test_cli_zip_command(tmp_path: Path):
    """Test running pyst zip via CLI."""
    sample_dir = tmp_path / "folder_to_zip"
    sample_dir.mkdir()
    (sample_dir / "file.txt").write_text("Hello from CLI test")

    out_zip = tmp_path / "result.zip"

    runner = CliRunner()
    result = runner.invoke(main, ["zip", str(sample_dir), "-o", str(out_zip)])
    assert result.exit_code == 0
    assert out_zip.exists()
