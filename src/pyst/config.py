"""Shared configuration constants.

All directory paths, default ports, and tunable constants live here.
Every other module imports from this file instead of hardcoding values.
That way changing a path or port number here automatically updates
everything that uses it.
"""

from pathlib import Path

# ---------------------------------------------------------------------------
# Runtime directories
# These are relative to wherever you run `pyst` from — typically the
# project root. Using Path() means we can do path arithmetic safely
# (e.g. DOWNLOADS_DIR / "subfolder") instead of string concatenation.
# ---------------------------------------------------------------------------

DOWNLOADS_DIR = Path("./downloads")
COMPLETED_DIR = Path("./completed")
UPLOADS_DIR = Path("./uploads")
TORRENT_FILES_DIR = Path("./files")

# ---------------------------------------------------------------------------
# Networking
# ---------------------------------------------------------------------------

# Default port for `pyst serve` (the full web UI)
DEFAULT_PORT = 8080

# Default port for `pyst stream <file>` (quick single-file stream)
STREAM_DEFAULT_PORT = 8000

# How many bytes to read at a time when streaming video
CHUNK_SIZE = 4096

# libtorrent port range defaults
TORRENT_DEFAULT_START_PORT = 6701
TORRENT_RANGE_SIZE = 50
TORRENT_SEARCH_RANGE_START = 6800
TORRENT_SEARCH_RANGE_END = 6900

# ---------------------------------------------------------------------------
# Media
# ---------------------------------------------------------------------------

# File extensions the sync player and browser treat as video files
VIDEO_EXTENSIONS = {
    ".avi",
    ".m4v",
    ".mkv",
    ".mov",
    ".mp4",
    ".mpeg",
    ".mpg",
    ".ogv",
    ".webm",
    ".wmv",
}
