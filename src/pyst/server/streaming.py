"""Video streaming blueprint for pyst.

Provides HTTP Range-based streaming (206 Partial Content) for seeking,
an HTML5 browser player interface, and compatibility with external players
like VLC.
"""

import mimetypes
import os
from pathlib import Path
from flask import Blueprint, Response, abort, current_app, render_template, request, send_file

from pyst import config
from pyst.config import CHUNK_SIZE
from pyst.utils import get_size, safe_path

streaming_bp = Blueprint("streaming", __name__, template_folder="templates")


def _get_downloads_dir() -> Path:
    return Path(current_app.config.get("DOWNLOADS_DIR", config.DOWNLOADS_DIR))


def _stream_generator(path: Path, start: int, end: int, chunk_size: int = CHUNK_SIZE):
    """Yield file chunks from byte offset start to end."""
    with open(path, "rb") as f:
        f.seek(start)
        bytes_left = end - start + 1
        while bytes_left > 0:
            read_len = min(chunk_size, bytes_left)
            data = f.read(read_len)
            if not data:
                break
            bytes_left -= len(data)
            yield data


def _serve_range_stream(file_path: Path):
    """Serve a file with full HTTP Range request (206 Partial Content) support."""
    if not file_path.is_file():
        abort(404, "File not found")

    file_size = file_path.stat().st_size
    mime_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
    range_header = request.headers.get("Range")

    if range_header:
        # Format: "bytes=start-end"
        try:
            range_val = range_header.strip().split("=")[-1]
            start_str, end_str = range_val.split("-")
            start = int(start_str) if start_str else 0
            end = int(end_str) if end_str else file_size - 1
        except Exception:
            start = 0
            end = file_size - 1

        end = min(end, file_size - 1)
        chunk_len = max(0, end - start + 1)

        resp = Response(
            _stream_generator(file_path, start, end),
            status=206,
            mimetype=mime_type,
        )
        resp.headers.add("Content-Range", f"bytes {start}-{end}/{file_size}")
        resp.headers.add("Accept-Ranges", "bytes")
        resp.headers.add("Content-Length", str(chunk_len))
        return resp

    # No range header requested; Flask handles conditional caching/full file
    return send_file(file_path, mimetype=mime_type, conditional=True)


@streaming_bp.route("/stream")
def stream_page():
    """HTML5 video player page for a selected video file."""
    rel_path = request.args.get("path", "").strip()
    if not rel_path:
        abort(400, "Missing path parameter")

    downloads_dir = _get_downloads_dir()
    file_path = safe_path(downloads_dir, rel_path)

    if not file_path.is_file():
        abort(404, "Video file not found")

    parent = Path(rel_path).parent.as_posix()
    parent_rel = "" if parent == "." else parent

    mime_type = mimetypes.guess_type(file_path.name)[0] or "video/mp4"

    return render_template(
        "stream.html",
        filename=file_path.name,
        rel_path=rel_path,
        parent=parent_rel,
        size=get_size(file_path),
        mime_type=mime_type,
    )


@streaming_bp.route("/play")
def play_video():
    """Stream raw video content with HTTP Range request support."""
    rel_path = request.args.get("path", "").strip()
    if not rel_path:
        abort(400, "Missing path parameter")

    downloads_dir = _get_downloads_dir()
    file_path = safe_path(downloads_dir, rel_path)

    return _serve_range_stream(file_path)


@streaming_bp.route("/movie")
def movie():
    """Stream endpoint used by standalone pyst stream command or direct queries."""
    single_path = current_app.config.get("VIDEO_PATH")
    if single_path and Path(single_path).is_file():
        return _serve_range_stream(Path(single_path))

    # Fallback to query param if provided
    rel_path = request.args.get("path", "").strip()
    if rel_path:
        downloads_dir = _get_downloads_dir()
        file_path = safe_path(downloads_dir, rel_path)
        return _serve_range_stream(file_path)

    abort(404, "No video configured to stream")
