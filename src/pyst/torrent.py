"""BitTorrent downloader utility powered by libtorrent.

Supports downloading via magnet links or .torrent HTTP(S) URLs, automatic
port selection, live terminal progress display, and completion marking.
"""

from pathlib import Path
import socket
import time
import urllib.parse
import urllib.request

import click
import libtorrent as lt

from pyst import config
from pyst.utils import mark_completed


def ports_free(start: int, end: int) -> bool:
    """Check if the given start and end TCP ports are available to bind."""
    s1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s1.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s2.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s1.bind(("", start))
        s2.bind(("", end))
        return True
    except OSError:
        return False
    finally:
        try:
            s1.close()
            s2.close()
        except Exception:
            pass


def find_available_port_range(range_size: int = config.TORRENT_RANGE_SIZE) -> tuple[int, int]:
    """Find an available port window within the configured search bounds."""
    start_min = config.TORRENT_SEARCH_RANGE_START
    start_max = config.TORRENT_SEARCH_RANGE_END - range_size
    for start in range(start_min, start_max + 1):
        end = start + range_size
        if ports_free(start, end):
            return start, end
    raise RuntimeError(f"Could not find a free port range in {start_min}-{config.TORRENT_SEARCH_RANGE_END}")


def build_start_port(port_suffix: str | None) -> tuple[int, int]:
    """Calculate port range from an optional 2-digit suffix or auto-select."""
    if port_suffix is None:
        return config.TORRENT_DEFAULT_START_PORT, config.TORRENT_DEFAULT_START_PORT + config.TORRENT_RANGE_SIZE

    prefix = str(config.TORRENT_DEFAULT_START_PORT)[:-2]
    suffix = str(port_suffix).zfill(2)
    start = int(prefix + suffix)
    end = start + config.TORRENT_RANGE_SIZE
    if ports_free(start, end):
        return start, end
    click.echo(f"  Requested port range ({start},{end}) is in use — selecting an automatic free range")
    return find_available_port_range()


def create_session(start_port: int, end_port: int) -> lt.session:
    """Initialize a libtorrent session listening on the specified port range."""
    session = lt.session()
    session.listen_on(start_port, end_port)
    return session


def download_torrent_file(torrent_link: str, target_dir: Path) -> Path:
    """Download a .torrent file from an HTTP(S) URL portably without external wget."""
    target_dir.mkdir(parents=True, exist_ok=True)
    filename = urllib.parse.unquote(torrent_link.split("/")[-1].split("?")[0])
    if not filename.lower().endswith(".torrent"):
        filename += ".torrent"

    target_path = target_dir / filename
    click.echo(f"  Fetching .torrent file from {torrent_link}...")

    req = urllib.request.Request(
        torrent_link,
        headers={"User-Agent": "Mozilla/5.0 (pyst torrent downloader)"},
    )
    with urllib.request.urlopen(req) as resp, open(target_path, "wb") as out_f:
        out_f.write(resp.read())

    click.echo(f"  Saved torrent file to {target_path}")
    return target_path


def run_download_loop(handle) -> None:
    """Run interactive terminal progress display until torrent completes."""
    bar_length = 36

    while handle.status().state != lt.torrent_status.seeding:
        s = handle.status()
        progress = s.progress * 100

        filled = int(bar_length * s.progress)
        bar = "█" * filled + "-" * (bar_length - filled)

        line1 = (
            f"\rProgress: {progress:5.2f}% | "
            f"Down: {s.download_rate / 1024:6.1f} kB/s | "
            f"Up: {s.upload_rate / 1024:6.1f} kB/s | "
            f"Peers: {s.num_peers:<3}"
        )
        line2 = f"[{bar}] {progress:5.2f}%"

        click.echo(f"{line1}\n{line2}", nl=False)
        click.echo("\033[F", nl=False)
        time.sleep(1)

    full_bar = "█" * bar_length
    click.echo("\r" + " " * 80)
    click.echo(f"[{full_bar}] 100.00%")


def download_torrent(
    link: str,
    port_suffix: str | None = None,
    output_dir: Path | str = config.DOWNLOADS_DIR,
    completed_dir: Path | str = config.COMPLETED_DIR,
) -> str:
    """Download torrent content from a magnet link or .torrent URL.

    Args:
        link: Magnet link (magnet:?...) or HTTP(S) URL to a .torrent file.
        port_suffix: Optional 2-digit port range suffix.
        output_dir: Destination directory for downloaded data.
        completed_dir: Directory where .completed markers are created.

    Returns:
        The name of the downloaded torrent.
    """
    out_dir = Path(output_dir)
    comp_dir = Path(completed_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    comp_dir.mkdir(parents=True, exist_ok=True)

    if port_suffix is not None:
        start_port, end_port = build_start_port(port_suffix)
    else:
        start_port, end_port = find_available_port_range()

    click.echo(f"  {click.style('📡', fg='cyan')} Port range: {start_port}–{end_port}")
    session = create_session(start_port, end_port)

    if link.startswith("magnet:"):
        click.echo(f"  {click.style('⏳', fg='yellow')} Fetching torrent metadata from peers...")
        params = {
            "save_path": str(out_dir),
            "storage_mode": lt.storage_mode_t.storage_mode_sparse,
        }
        handle = lt.add_magnet_uri(session, link, params)
        while not handle.has_metadata():
            time.sleep(1)
        click.echo(f"  {click.style('📦', fg='green')} Metadata retrieved!")
        info = handle.get_torrent_info()
    else:
        torrent_file = download_torrent_file(link, config.TORRENT_FILES_DIR)
        info = lt.torrent_info(str(torrent_file))
        handle = session.add_torrent({"ti": info, "save_path": str(out_dir)})

    torrent_name = info.name()
    click.echo(f"  {click.style('📥', fg='cyan')} Downloading: {click.style(torrent_name, bold=True)}")

    run_download_loop(handle)

    marker = mark_completed(torrent_name, comp_dir)
    click.echo(f"  {click.style('✅', fg='green')} Torrent download complete!")
    click.echo(f"  {click.style('📋', fg='cyan')} Marked completed: {marker.name}")
    return torrent_name
