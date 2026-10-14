"""Video downloader utility powered by yt-dlp.

Downloads video media from hundreds of supported websites into the downloads
directory and creates a .completed marker when finished.
"""

from pathlib import Path
import click
import yt_dlp

from pyst import config
from pyst.utils import mark_completed


def download_video(
    url: str,
    output_dir: Path | str = config.DOWNLOADS_DIR,
    completed_dir: Path | str = config.COMPLETED_DIR,
) -> Path:
    """Download video content from a given URL using yt-dlp.

    Args:
        url: The web URL of the video to download.
        output_dir: Destination directory for downloaded media.
        completed_dir: Directory where .completed markers are recorded.

    Returns:
        Path to the downloaded media file.
    """
    out_dir = Path(output_dir)
    comp_dir = Path(completed_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    comp_dir.mkdir(parents=True, exist_ok=True)

    template = str(out_dir / "%(title)s.%(ext)s")
    ydl_opts = {
        "outtmpl": template,
        "quiet": False,
        "no_warnings": True,
    }

    click.echo(f"  {click.style('⏳', fg='yellow')} Querying video metadata...")
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        if not info:
            raise RuntimeError("Failed to extract video information")
        target_filename = ydl.prepare_filename(info)

    file_path = Path(target_filename)
    marker = mark_completed(file_path.name, comp_dir)

    click.echo(f"  {click.style('✅', fg='green')} Download complete: {click.style(str(file_path), bold=True)}")
    click.echo(f"  {click.style('📋', fg='cyan')} Marked completed: {marker.name}")
    return file_path
