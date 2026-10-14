"""CLI entry point — defines all pyst commands.

This module is the "main menu" of the application. When you run
`pyst` in your terminal, Python calls the `main()` function here.

Click turns decorated Python functions into CLI commands automatically:
  - @click.group()    → creates the top-level `pyst` command
  - @main.command()   → adds a subcommand like `pyst serve`
  - @click.option()   → adds a --flag to a command
  - @click.argument() → adds a positional argument to a command

For now each command just prints a placeholder. Subsequent phases
will replace each placeholder with the real implementation.
"""

import socket
import sys

# Ensure UTF-8 output across all subcommands and help texts on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import click

from pyst import __version__
from pyst.config import DEFAULT_PORT, STREAM_DEFAULT_PORT


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_local_ip() -> str:
    """Return the machine's LAN IP address for display purposes.

    Opens a UDP socket (no data sent) to determine which interface the
    OS would use to reach the internet, then reads the local address.
    Falls back to 127.0.0.1 if anything goes wrong.
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def _print_server_box(title: str, urls: dict[str, str], notes: list[str] | None = None) -> None:
    """Print a bordered info box with URLs and optional notes.

    Args:
        title:  Header line inside the box.
        urls:   Ordered dict of label → URL to display.
        notes:  Optional list of tip/note lines shown after the URLs.
    """
    # Reconfigure stdout to UTF-8 so box-drawing characters render on
    # Windows terminals that default to cp1252.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    width = 54  # inner width (between the │ characters)

    def row(text: str = "") -> str:
        return f"  │  {text:<{width - 4}}│"

    lines = [
        f"  ╭{'─' * width}╮",
        row(click.style(f"pyst v{__version__} — {title}", bold=True)),
        row(),
    ]
    for label, url in urls.items():
        lines.append(row(f"{label:<18}{click.style(url, fg='cyan')}"))
    if notes:
        lines.append(row())
        for note in notes:
            lines.append(row(click.style(note, fg='yellow')))
    lines.append(f"  ╰{'─' * width}╯")

    click.echo("\n" + "\n".join(lines) + "\n")



# ---------------------------------------------------------------------------
# Top-level group
# ---------------------------------------------------------------------------

@click.group()
@click.version_option(__version__, prog_name="pyst")
def main() -> None:
    """pyst — A local media streaming and download toolkit.

    \b
    Browse, stream, sync-play, upload, download, and torrent
    media files from a single CLI tool with a built-in web server.

    \b
    Quick start:
      pyst serve              # start the full web UI
      pyst stream video.mp4   # quick-stream one file
      pyst download <url>     # download via yt-dlp
      pyst torrent <magnet>   # download via BitTorrent
    """


# ---------------------------------------------------------------------------
# pyst serve
# ---------------------------------------------------------------------------

@main.command()
@click.option(
    "-p", "--port",
    default=DEFAULT_PORT,
    show_default=True,
    help="Port for the web server.",
)
@click.option(
    "--host",
    default="0.0.0.0",
    show_default=True,
    help="Network interface to bind to. Use 0.0.0.0 to accept connections from other devices on the LAN.",
)
@click.option(
    "--no-browser",
    is_flag=True,
    default=False,
    help="Don't automatically open a browser tab on startup.",
)
def serve(port: int, host: str, no_browser: bool) -> None:
    """Start the unified web server with all features.

    \b
    Launches a single server exposing:
      • File browser  (/browse)
      • Video player  (/stream)
      • Sync player   (/sync)
      • File upload   (/upload)

    \b
    Files are read from ./downloads and uploads go to ./uploads.
    Press Ctrl+C to stop.
    """
    lan_ip = _get_local_ip()

    _print_server_box(
        title="Media Server",
        urls={
            "Dashboard:":    f"http://localhost:{port}/",
            "File Browser:": f"http://localhost:{port}/browse",
            "Sync Player:":  f"http://localhost:{port}/sync",
            "Upload:":       f"http://localhost:{port}/upload",
            "On LAN:":       f"http://{lan_ip}:{port}/",
        },
        notes=[
            "Serving files from: ./downloads",
            "Uploads go to:      ./uploads",
            "Press Ctrl+C to stop.",
        ],
    )

    if not no_browser:
        import threading
        import webbrowser
        threading.Timer(1.0, lambda: webbrowser.open(f"http://localhost:{port}/")).start()

    from pyst.server.app import create_app
    app = create_app()
    app.run(host=host, port=port, debug=False, threaded=True)


# ---------------------------------------------------------------------------
# pyst stream
# ---------------------------------------------------------------------------

@main.command()
@click.argument("file", type=click.Path(exists=True, dir_okay=False))
@click.option(
    "-p", "--port",
    default=STREAM_DEFAULT_PORT,
    show_default=True,
    help="Port for the stream server.",
)
def stream(file: str, port: int) -> None:
    """Quick-stream a single video file over HTTP.

    \b
    Starts a lightweight server for FILE only — no full browser UI.
    Open the Player URL in a browser, or paste the Raw URL into VLC.

    \b
    Example:
      pyst stream ./downloads/movie.mkv
      pyst stream ./movie.mkv --port 9000
    """
    from pathlib import Path
    from pyst.utils import get_size

    path = Path(file)
    size = get_size(path)

    _print_server_box(
        title=f"Streaming: {path.name}",
        urls={
            "Player:": f"http://localhost:{port}/",
            "Raw URL:": f"http://localhost:{port}/movie",
        },
        notes=[
            f"File: {path.name} ({size})",
            "Paste Raw URL into VLC: Media → Open Network Stream.",
            "Press Ctrl+C to stop.",
        ],
    )

    import mimetypes
    from flask import Flask, render_template
    from pyst.server.streaming import streaming_bp

    app = Flask(__name__, template_folder=Path(__file__).parent / "server" / "templates")
    app.config["VIDEO_PATH"] = str(path.resolve())
    app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0
    app.register_blueprint(streaming_bp)

    @app.route("/")
    def index():
        mime = mimetypes.guess_type(path.name)[0] or "video/mp4"
        return render_template(
            "stream.html",
            filename=path.name,
            rel_path="",
            parent=None,
            size=size,
            mime_type=mime,
        )

    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)


# ---------------------------------------------------------------------------
# pyst download
# ---------------------------------------------------------------------------

@main.command()
@click.argument("url")
@click.option(
    "-o", "--output",
    default="./downloads",
    show_default=True,
    type=click.Path(file_okay=False),
    help="Directory to save the downloaded file.",
)
def download(url: str, output: str) -> None:
    """Download a video from a URL using yt-dlp.

    \b
    Supports YouTube, Vimeo, Twitter, and hundreds of other sites.
    Downloaded files are saved to ./downloads and marked as completed.

    \b
    Example:
      pyst download "https://www.youtube.com/watch?v=..."
      pyst download "https://vimeo.com/..." --output ./movies
    """
    click.echo(f"\n  {click.style('⏳', fg='yellow')} Downloading: {url}")
    click.echo(f"  {click.style('📁', fg='cyan')} Saving to: {output}\n")

    from pyst.downloader import download_video
    try:
        download_video(url, output_dir=output)
    except Exception as exc:
        click.echo(f"  {click.style('❌ Download failed:', fg='red', bold=True)} {exc}", err=True)
        raise SystemExit(1)


# ---------------------------------------------------------------------------
# pyst torrent
# ---------------------------------------------------------------------------

@main.command()
@click.argument("link")
@click.option(
    "-p", "--port",
    default=None,
    help="Last two digits of the libtorrent port range (e.g. --port 01 uses 6701–6751).",
)
@click.option(
    "-o", "--output",
    default="./downloads",
    show_default=True,
    type=click.Path(file_okay=False),
    help="Directory to save downloaded files.",
)
def torrent(link: str, port: str | None, output: str) -> None:
    """Download a torrent from a magnet link or .torrent URL.

    \b
    Supports magnet links and direct URLs to .torrent files.
    Shows a live progress bar with speed, peers, and ETA.
    Files are saved to ./downloads and marked as completed when done.

    \b
    Examples:
      pyst torrent "magnet:?xt=urn:btih:..."
      pyst torrent "https://example.com/file.torrent"
      pyst torrent "magnet:?xt=urn:btih:..." --port 01
    """
    link_type = "Magnet link" if link.startswith("magnet:") else ".torrent URL"
    click.echo(f"\n  {click.style('🔗', fg='cyan')} {link_type} detected")
    click.echo(f"  {click.style('📁', fg='cyan')} Saving to: {output}\n")

    from pyst.torrent import download_torrent
    try:
        download_torrent(link, port_suffix=port, output_dir=output)
    except Exception as exc:
        click.echo(f"  {click.style('❌ Torrent failed:', fg='red', bold=True)} {exc}", err=True)
        raise SystemExit(1)


# ---------------------------------------------------------------------------
# pyst zip
# ---------------------------------------------------------------------------

@main.command(name="zip")
@click.argument("folder", type=click.Path(exists=True, file_okay=False))
@click.option(
    "-o", "--output",
    default=None,
    help="Output .zip file path. Defaults to <folder>.zip in the same directory.",
)
def zip_cmd(folder: str, output: str | None) -> None:
    """Zip a folder with a live progress indicator.

    \b
    Example:
      pyst zip ./downloads/my-show
      pyst zip ./downloads/my-show --output ./archives/my-show.zip
    """
    from pyst.zipper import zip_folder
    try:
        zip_folder(folder, output_path=output)
    except Exception as exc:
        click.echo(f"  {click.style('❌ Zip failed:', fg='red', bold=True)} {exc}", err=True)
        raise SystemExit(1)


# ---------------------------------------------------------------------------
# pyst convert (audio fix for web browsers)
# ---------------------------------------------------------------------------

@main.command(name="convert")
@click.argument("file", type=click.Path(exists=True, dir_okay=False))
@click.option("-o", "--output", default=None, help="Output file path. Defaults to <name>.aac.mkv.")
@click.option("-a", "--track", default="0:a:0", show_default=True, help="Audio track to convert (e.g. 0:a:0 for first, 0:a:1 for second).")
def convert_cmd(file: str, output: str | None, track: str) -> None:
    """Convert video audio to AAC for universal browser playback.

    \b
    Web browsers do not support AC3/EAC3/DTS audio codecs.
    This command copies video without re-encoding (-c:v copy)
    and converts audio to AAC (-c:a aac) in seconds.

    \b
    Example:
      pyst convert ./downloads/movie.mkv
      pyst convert ./downloads/movie.mkv -a 0:a:1
    """
    import shutil
    import subprocess
    from pathlib import Path

    if not shutil.which("ffmpeg"):
        click.echo(click.style("  ❌ ffmpeg is not installed or not in PATH.", fg="red", bold=True))
        click.echo("  Install ffmpeg using winget (Windows), brew (macOS), or apt (Ubuntu).")
        raise SystemExit(1)

    in_path = Path(file).resolve()
    if output:
        out_path = Path(output).resolve()
    else:
        out_path = in_path.parent / f"{in_path.stem}.aac{in_path.suffix}"

    click.echo(f"  {click.style('🎬', fg='cyan')} Converting audio for: {in_path.name}")
    click.echo(f"  {click.style('🔊', fg='yellow')} Audio track: {track} -> AAC 192k")
    click.echo(f"  {click.style('📁', fg='cyan')} Output: {out_path}")

    cmd = [
        "ffmpeg", "-y",
        "-i", str(in_path),
        "-map", "0:v",
        "-map", track,
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        str(out_path),
    ]

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            click.echo(click.style(f"  ❌ ffmpeg conversion failed:\n{proc.stderr}", fg="red"))
            raise SystemExit(1)
        click.echo(click.style(f"  ✅ Audio converted successfully! Saved to: {out_path}", fg="green", bold=True))
    except Exception as exc:
        click.echo(click.style(f"  ❌ Conversion error: {exc}", fg="red"))
        raise SystemExit(1)

