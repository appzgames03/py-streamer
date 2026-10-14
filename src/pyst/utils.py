"""Shared utility functions used by both CLI and server code.

Nothing in here should be specific to Flask or Click — these are
pure Python helpers that work anywhere.
"""

from pathlib import Path

from flask import abort


def safe_path(base_dir: Path, rel_path: str) -> Path:
    """Resolve *rel_path* under *base_dir*, blocking directory traversal.

    A user could craft a request like ``?path=../../etc/passwd`` to escape
    the downloads directory. This function resolves the full path and then
    checks that it still sits inside *base_dir*. If not, it aborts with 403.

    Args:
        base_dir: The allowed root directory (e.g. ``config.DOWNLOADS_DIR``).
        rel_path: A relative path string from a query parameter or form field.

    Returns:
        The resolved absolute :class:`~pathlib.Path`.

    Raises:
        werkzeug.exceptions.Forbidden: (HTTP 403) if the path escapes base_dir.
    """
    candidate = (base_dir / rel_path).resolve()
    try:
        candidate.relative_to(base_dir.resolve())
    except ValueError:
        abort(403)
    return candidate


def get_size(path: Path) -> str:
    """Return a human-readable file or directory size string.

    For directories, sums all files recursively.

    Examples::

        get_size(Path("./video.mp4"))  # "2.4 GB"
        get_size(Path("./downloads"))  # "18.3 GB"
    """
    if path.is_file():
        size = path.stat().st_size
    else:
        size = sum(
            f.stat().st_size
            for f in path.rglob("*")
            if f.is_file()
        )

    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024

    return f"{size:.1f} PB"


def mark_completed(name: str, completed_dir: Path) -> Path:
    """Create a ``.completed`` marker file for a finished download.

    Both the torrent downloader and the yt-dlp downloader call this
    after a successful download. The file browser shows a green dot
    next to entries that have a corresponding marker file.

    Args:
        name: The torrent or video filename (without the ``.completed`` suffix).
        completed_dir: Directory where markers are stored.

    Returns:
        Path to the created marker file.
    """
    completed_dir.mkdir(parents=True, exist_ok=True)
    marker = completed_dir / f"{name}.completed"
    marker.touch()
    return marker
