"""Synchronized multi-client video playback blueprint for pyst.

Allows one user (Host) to select and control video playback while other
connected browsers (Clients) automatically follow play, pause, and seek actions
in real time via long-polling.

Exact match to the archived sync-streamer design:
- No interval-based polling or periodic playhead seeking.
- Seeking triggers a pause action and sends the seeked position.
- Playing/pausing syncs the playhead and coordinates playback.
- Automatically detects AC3/DTS audio codecs that web browsers cannot decode.
"""

import json
import math
import mimetypes
from pathlib import Path
import shutil
import subprocess
import threading
import time
from typing import Any
from flask import Blueprint, abort, current_app, jsonify, redirect, render_template, request, send_file

from pyst import config
from pyst.config import VIDEO_EXTENSIONS
from pyst.utils import safe_path

sync_bp = Blueprint("sync", __name__, url_prefix="/sync", template_folder="templates")
root_sync_bp = Blueprint("root_sync", __name__, template_folder="templates")

STATE_WAIT_SECONDS = 20
UNSUPPORTED_BROWSER_AUDIO = {"ac3", "eac3", "dts", "dca", "truehd", "mlp"}

state_changed = threading.Condition()

playback: dict[str, Any] = {
    "file": None,
    "position": 0.0,
    "playing": False,
    "updated_at": time.monotonic(),
    "revision": 0,
    "audio_codec": None,
    "unsupported_audio": False,
}


def _get_downloads_dir() -> Path:
    return Path(current_app.config.get("DOWNLOADS_DIR", config.DOWNLOADS_DIR))


def detect_audio_codec(file_path: Path) -> str | None:
    """Inspect primary audio stream codec using ffprobe if available."""
    try:
        if not shutil.which("ffprobe"):
            return None
        cmd = [
            "ffprobe", "-v", "error",
            "-select_streams", "a:0",
            "-show_entries", "stream=codec_name",
            "-of", "json",
            str(file_path)
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        if res.returncode == 0:
            data = json.loads(res.stdout)
            streams = data.get("streams", [])
            if streams:
                return streams[0].get("codec_name", "").lower()
    except Exception:
        pass
    return None


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
            "audio_codec": playback.get("audio_codec"),
            "unsupported_audio": playback.get("unsupported_audio", False),
        }


@sync_bp.route("/")
def sync_index():
    """Default redirect to the client watch page."""
    return redirect("/sync/watch")


def _render_host():
    """Host control page with video selector dropdown."""
    return render_template(
        "sync.html",
        title="Host",
        description="Choose a video and use the player controls. All connected browsers share playback.",
        role="host",
        files=_list_videos(),
    )


def _render_watch():
    """Client watcher page following the shared host controls."""
    return render_template(
        "sync.html",
        title="Client",
        description="This player follows the shared video and playback controls.",
        role="client",
        files=[],
    )


def _get_state_impl():
    """Long-polling endpoint that returns the current synchronized playback state."""
    after = request.args.get("after", type=int)
    with state_changed:
        if after is not None and after == playback["revision"]:
            state_changed.wait(timeout=STATE_WAIT_SECONDS)
        state = _snapshot()
    return jsonify(state)


def _control_impl():
    """Receive playback control commands (select, play, pause) from player."""
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
    audio_codec = None
    if action == "select":
        selected_file = data.get("file")
        if not isinstance(selected_file, str) or not selected_file:
            abort(400, "A video file must be selected")
        downloads_dir = _get_downloads_dir()
        resolved_path = safe_path(downloads_dir, selected_file)
        audio_codec = detect_audio_codec(resolved_path)

    now = time.monotonic()
    with state_changed:
        if action == "select":
            playback.update(
                file=selected_file,
                position=0.0,
                playing=True,
                updated_at=now,
                audio_codec=audio_codec,
                unsupported_audio=audio_codec in UNSUPPORTED_BROWSER_AUDIO if audio_codec else False,
            )
        elif not playback["file"]:
            abort(409, "Select a video before controlling playback")
        else:
            playback["position"] = position
            playback["updated_at"] = now
            playback["playing"] = (action == "play")
        playback["revision"] += 1
        state_changed.notify_all()

    return jsonify(_snapshot())


def _video_impl():
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


# Register routes for /sync prefix
sync_bp.route("/host")(_render_host)
sync_bp.route("/watch")(_render_watch)
sync_bp.route("/client")(_render_watch)
sync_bp.route("/api/state")(_get_state_impl)
sync_bp.route("/api/control", methods=["POST"])(_control_impl)
sync_bp.route("/video")(_video_impl)

# Register routes for root endpoints (exact compatibility with original sync-stream.py)
root_sync_bp.route("/host")(_render_host)
root_sync_bp.route("/watch")(_render_watch)
root_sync_bp.route("/client")(_render_watch)
root_sync_bp.route("/api/state")(_get_state_impl)
root_sync_bp.route("/api/control", methods=["POST"])(_control_impl)
root_sync_bp.route("/video")(_video_impl)
