"""Synchronized multi-client video playback blueprint for pyst.

Allows one user (Host) to select and control video playback while other
connected browsers (Clients) automatically follow play, pause, and seek actions
in real time via long-polling.
"""

import math
import mimetypes
from pathlib import Path
import threading
import time
from typing import Any
from flask import Blueprint, abort, current_app, jsonify, redirect, render_template, request, send_file

from pyst import config
from pyst.config import VIDEO_EXTENSIONS
from pyst.utils import safe_path

sync_bp = Blueprint("sync", __name__, url_prefix="/sync", template_folder="templates")

STATE_WAIT_SECONDS = 20
state_changed = threading.Condition()

playback: dict[str, Any] = {
    "file": None,
    "position": 0.0,
    "playing": False,
    "updated_at": time.monotonic(),
    "revision": 0,
}


def _get_downloads_dir() -> Path:
    return Path(current_app.config.get("DOWNLOADS_DIR", config.DOWNLOADS_DIR))


def _list_videos() -> list[dict[str, str]]:
    """Scan the downloads directory recursively for playable video files."""
    downloads_dir = _get_downloads_dir()
    if not downloads_dir.is_dir():
        return []
    files = []
    for path in sorted(downloads_dir.rglob("*")):
        if not path.is_symlink() and path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS:
            rel = path.relative_to(downloads_dir).as_posix()
            files.append({
                "path": rel,
                "name": rel,
            })
    return files


def _snapshot() -> dict[str, Any]:
    """Calculate the estimated current playback position based on elapsed time."""
    with state_changed:
        position = playback["position"]
        if playback["playing"]:
            position += time.monotonic() - playback["updated_at"]
        return {
            "file": playback["file"],
            "name": Path(playback["file"]).name if playback["file"] else None,
            "position": max(0.0, position),
            "playing": playback["playing"],
            "revision": playback["revision"],
        }


@sync_bp.route("/")
def index():
    """Default redirect to the client watch page."""
    return redirect("/sync/watch")


@sync_bp.route("/host")
def host():
    """Host control page with video selector dropdown."""
    return render_template(
        "sync.html",
        title="Host",
        description="Choose a video and control playback. All connected browsers will stay in sync.",
        role="host",
        files=_list_videos(),
    )


@sync_bp.route("/watch")
def watch():
    """Client watcher page following the shared host controls."""
    return render_template(
        "sync.html",
        title="Client",
        description="This player automatically synchronizes with the host's playback controls.",
        role="client",
        files=[],
    )


@sync_bp.route("/api/state")
def get_state():
    """Long-polling endpoint that returns the current synchronized playback state."""
    after = request.args.get("after", type=int)
    with state_changed:
        if after is not None and after == playback["revision"]:
            state_changed.wait(timeout=STATE_WAIT_SECONDS)
        state = _snapshot()
    return jsonify(state)


@sync_bp.route("/api/control", methods=["POST"])
def control():
    """Receive playback control commands (select, play, pause) from a player."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        abort(400, "Invalid JSON body")

    action = data.get("action")
    if action not in {"select", "play", "pause"}:
        abort(400, "Unknown playback action")

    position = data.get("position", 0)
    if (
        isinstance(position, bool)
        or not isinstance(position, (int, float))
        or not math.isfinite(position)
    ):
        abort(400, "Playback position must be a number")
    position = max(0.0, float(position))

    selected_file = None
    if action == "select":
        selected_file = data.get("file")
        if not isinstance(selected_file, str) or not selected_file:
            abort(400, "A video file must be selected")
        downloads_dir = _get_downloads_dir()
        safe_path(downloads_dir, selected_file)

    now = time.monotonic()
    with state_changed:
        if action == "select":
            playback.update(file=selected_file, position=0.0, playing=True, updated_at=now)
        elif not playback["file"]:
            abort(409, "Select a video before controlling playback")
        else:
            playback["position"] = position
            playback["updated_at"] = now
            playback["playing"] = (action == "play")
        playback["revision"] += 1
        state_changed.notify_all()

    return jsonify(_snapshot())


@sync_bp.route("/video")
def video():
    """Serve the active video file to browser players."""
    rel_path = request.args.get("path", "").strip()
    if not rel_path:
        abort(400, "A video path is required")

    downloads_dir = _get_downloads_dir()
    file_path = safe_path(downloads_dir, rel_path)

    if not file_path.is_file():
        abort(404, "Video file not found")

    mime = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
    return send_file(
        file_path,
        mimetype=mime,
        conditional=True,
    )
