#!/usr/bin/env python3
import math
import mimetypes
import threading
import time
from pathlib import Path
from typing import Any

from flask import Flask, abort, jsonify, render_template_string, request, send_file


DOWNLOADS_DIR = Path(__file__).resolve().parent / "downloads"
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
STATE_WAIT_SECONDS = 20

app = Flask(__name__)
state_changed = threading.Condition()
playback: dict[str, Any] = {
    "file": None,
    "position": 0.0,
    "playing": False,
    "updated_at": time.monotonic(),
    "revision": 0,
}

PAGE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{{ title }} - Synchronized Stream</title>
  <style>
    :root { color-scheme: dark; font-family: system-ui, sans-serif; }
    body { max-width: 1000px; margin: 2rem auto; padding: 0 1rem; background: #111; color: #eee; }
    h1 { margin-bottom: .25rem; }
    p { color: #bbb; }
    video { display: block; width: 100%; max-height: 75vh; margin-top: 1.5rem; background: #000; }
    select, button { font: inherit; padding: .55rem .8rem; }
    #status { min-height: 1.5em; color: #9ed0ff; }
    #join { display: none; }
  </style>
</head>
<body data-role="{{ role }}">
  <h1>{{ title }}</h1>
  <p>{{ description }}</p>
  {% if role == "host" %}
  <label for="file-picker">Video from downloads: </label>
  <select id="file-picker">
    <option value="">Choose a video...</option>
    {% for file in files %}
    <option value="{{ file.path }}">{{ file.name }}</option>
    {% endfor %}
  </select>
  {% endif %}
  <p id="status">Waiting for a video selection...</p>
  <button id="join" type="button">Enable playback</button>
  <video id="player" controls playsinline></video>
  <script>
    const player = document.getElementById("player");
    const status = document.getElementById("status");
    const joinButton = document.getElementById("join");
    const picker = document.getElementById("file-picker");
    let currentFile = null;
    let lastSeenRevision = -1;
    let appliedRevision = -1;
    let latestState = null;
    let remotePlaybackEvent = null;
    let remoteSeekPosition = null;
    let remoteSeekTimeout = null;

    async function sendControl(action, position = player.currentTime) {
      try {
        const response = await fetch("/api/control", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ action, position })
        });
        if (!response.ok) {
          status.textContent = `Control update failed (${response.status}).`;
        }
      } catch (error) {
        status.textContent = `Control update failed: ${error.message}`;
      }
    }

    player.addEventListener("play", () => {
      if (remotePlaybackEvent === "play") {
        remotePlaybackEvent = null;
        return;
      }
      sendControl("play");
    });
    player.addEventListener("pause", () => {
      if (remotePlaybackEvent === "pause") {
        remotePlaybackEvent = null;
        return;
      }
      if (!player.ended) sendControl("pause");
    });
    player.addEventListener("ended", () => sendControl("pause", player.currentTime));
    player.addEventListener("seeked", () => {
      if (remoteSeekPosition !== null) {
        const isRemoteSeek = Math.abs(player.currentTime - remoteSeekPosition) < 0.05;
        remoteSeekPosition = null;
        clearTimeout(remoteSeekTimeout);
        if (isRemoteSeek) return;
      }
      if (!player.paused) {
        remotePlaybackEvent = "pause";
        player.pause();
      }
      sendControl("pause");
    });
    player.addEventListener("error", () => {
      if (currentFile) status.textContent = "This browser could not play the selected video.";
    });

    if (picker) {
      picker.addEventListener("change", async () => {
        if (!picker.value) return;
        try {
          const response = await fetch("/api/control", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ action: "select", file: picker.value })
          });
          if (!response.ok) status.textContent = `Could not select video (${response.status}).`;
        } catch (error) {
          status.textContent = `Could not select video: ${error.message}`;
        }
      });
    }

    joinButton.addEventListener("click", async () => {
      joinButton.style.display = "none";
      try {
        await player.play();
      } catch (error) {
        status.textContent = "Playback could not start. Use the video controls to try again.";
      }
    });

    async function applyState(state) {
      latestState = state;
      if (state.file !== currentFile) {
        currentFile = state.file;
        appliedRevision = -1;
        if (!player.paused) {
          remotePlaybackEvent = "pause";
          player.pause();
        }
        player.removeAttribute("src");
        player.load();
        if (currentFile) {
          player.src = `/video?path=${encodeURIComponent(currentFile)}`;
          player.load();
          if (picker) picker.value = currentFile;
          status.textContent = `Selected: ${state.name}`;
        } else {
          if (picker) picker.value = "";
          status.textContent = "Waiting for a video selection...";
        }
      }
      if (!currentFile || player.readyState < 1 || appliedRevision === state.revision) return;

      appliedRevision = state.revision;
      const targetPosition = Number.isFinite(player.duration)
        ? Math.min(state.position, player.duration)
        : state.position;
      if (Math.abs(player.currentTime - targetPosition) > 0.05) {
        remoteSeekPosition = targetPosition;
        clearTimeout(remoteSeekTimeout);
        remoteSeekTimeout = setTimeout(() => { remoteSeekPosition = null; }, 1000);
        player.currentTime = targetPosition;
      }

      if (state.playing && player.paused) {
        remotePlaybackEvent = "play";
        try {
          await player.play();
          joinButton.style.display = "none";
        } catch (error) {
          remotePlaybackEvent = null;
          joinButton.style.display = "inline-block";
          status.textContent = "Playback is ready. Click Enable playback to allow this browser to play.";
        }
      } else if (!state.playing && !player.paused) {
        remotePlaybackEvent = "pause";
        player.pause();
      }
    }

    async function listenForUpdates() {
      while (true) {
        try {
          const response = await fetch(`/api/state?after=${lastSeenRevision}`, { cache: "no-store" });
          if (!response.ok) throw new Error(`State request failed (${response.status})`);
          const state = await response.json();
          lastSeenRevision = state.revision;
          await applyState(state);
        } catch (error) {
          status.textContent = error.message;
          await new Promise(resolve => setTimeout(resolve, 1000));
        }
      }
    }

    player.addEventListener("loadedmetadata", () => {
      if (latestState) applyState(latestState);
    });
    listenForUpdates();
  </script>
</body>
</html>
"""


def safe_video_path(relative_path: str) -> Path:
    candidate = (DOWNLOADS_DIR / relative_path).resolve()
    try:
        candidate.relative_to(DOWNLOADS_DIR.resolve())
    except ValueError:
        abort(403)
    if not candidate.is_file() or candidate.suffix.lower() not in VIDEO_EXTENSIONS:
        abort(404)
    return candidate


def list_videos() -> list[dict[str, str]]:
    if not DOWNLOADS_DIR.is_dir():
        return []
    files = []
    for path in sorted(DOWNLOADS_DIR.rglob("*")):
        if not path.is_symlink() and path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS:
            files.append({
                "path": path.relative_to(DOWNLOADS_DIR).as_posix(),
                "name": path.relative_to(DOWNLOADS_DIR).as_posix(),
            })
    return files


def snapshot() -> dict[str, Any]:
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


@app.get("/")
def index():
    return '<!doctype html><html><meta http-equiv="refresh" content="0;url=/host"></html>'


@app.get("/host")
def host():
    return render_template_string(
        PAGE,
        title="Host",
        description="Choose a video and use the player controls. All connected browsers share playback.",
        role="host",
        files=list_videos(),
    )


@app.get("/watch")
def client():
    return render_template_string(
        PAGE,
        title="Client",
        description="This player follows the shared video and playback controls.",
        role="client",
        files=[],
    )


@app.get("/api/state")
def get_state():
    after = request.args.get("after", type=int)
    with state_changed:
        if after is not None and after == playback["revision"]:
            state_changed.wait(timeout=STATE_WAIT_SECONDS)
        state = snapshot()
    return jsonify(state)


@app.post("/api/control")
def control():
    data = request.get_json()
    action = data.get("action") if isinstance(data, dict) else None
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
        safe_video_path(selected_file)

    now = time.monotonic()
    with state_changed:
        if action == "select":
            playback.update(file=selected_file, position=0.0, playing=True, updated_at=now)
        elif not playback["file"]:
            abort(409, "Select a video before controlling playback")
        else:
            playback["position"] = position
            playback["updated_at"] = now
            playback["playing"] = action == "play"
        playback["revision"] += 1
        state_changed.notify_all()

    return jsonify(snapshot())


@app.get("/video")
def video():
    relative_path = request.args.get("path")
    if not relative_path:
        abort(400, "A video path is required")
    path = safe_video_path(relative_path)
    return send_file(
        path,
        mimetype=mimetypes.guess_type(path.name)[0] or "application/octet-stream",
        conditional=True,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False, threaded=True)
