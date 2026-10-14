"""File browser blueprint for pyst.

Handles the root dashboard, file browsing in the downloads directory,
and direct file downloads.
"""

import os
from pathlib import Path
from flask import Blueprint, abort, current_app, render_template, request, send_file

from pyst import config
from pyst.config import VIDEO_EXTENSIONS
from pyst.utils import get_size, safe_path

browse_bp = Blueprint("browse", __name__, template_folder="templates")


def _get_downloads_dir() -> Path:
    return Path(current_app.config.get("DOWNLOADS_DIR", config.DOWNLOADS_DIR))


def _get_completed_dir() -> Path:
    return Path(current_app.config.get("COMPLETED_DIR", config.COMPLETED_DIR))


@browse_bp.route("/")
def dashboard():
    """Server dashboard with library stats and quick navigation."""
    downloads_dir = _get_downloads_dir()
    completed_dir = _get_completed_dir()

    downloads_dir.mkdir(parents=True, exist_ok=True)
    completed_dir.mkdir(parents=True, exist_ok=True)

    downloads_size = get_size(downloads_dir)

    video_count = 0
    for root, _, files in os.walk(downloads_dir):
        for f in files:
            if Path(f).suffix.lower() in VIDEO_EXTENSIONS:
                video_count += 1

    completed_count = 0
    if completed_dir.is_dir():
        completed_count = len([f for f in completed_dir.iterdir() if f.is_file()])

    return render_template(
        "dashboard.html",
        downloads_dir=str(downloads_dir),
        downloads_size=downloads_size,
        video_count=video_count,
        completed_count=completed_count,
    )


@browse_bp.route("/browse")
def browse():
    """Browse files and folders inside the downloads directory."""
    downloads_dir = _get_downloads_dir()
    completed_dir = _get_completed_dir()

    downloads_dir.mkdir(parents=True, exist_ok=True)
    rel_path = request.args.get("path", "").strip().lstrip("/\\")

    current_path = safe_path(downloads_dir, rel_path)

    if not current_path.is_dir():
        abort(404, "Directory not found")

    entries = []
    try:
        items = sorted(os.listdir(current_path))
    except OSError:
        abort(500, "Unable to read directory")

    for name in items:
        full = current_path / name
        is_dir = full.is_dir()
        child_rel = os.path.join(rel_path, name).replace("\\", "/") if rel_path else name

        zip_path = current_path / f"{name}.zip"
        marker = completed_dir / f"{child_rel}.completed"

        is_video = not is_dir and full.suffix.lower() in VIDEO_EXTENSIONS

        entries.append({
            "name": name,
            "is_dir": is_dir,
            "is_video": is_video,
            "rel": child_rel,
            "zip_exists": is_dir and zip_path.is_file(),
            "size": get_size(full),
            "downloaded": marker.exists(),
        })

    # Sort directories first, then files alphabetically
    entries.sort(key=lambda x: (not x["is_dir"], x["name"].lower()))

    parent = None
    if rel_path:
        parent_parts = Path(rel_path).parent.as_posix()
        parent = "" if parent_parts == "." else parent_parts

    return render_template(
        "browse.html",
        entries=entries,
        rel_path=rel_path,
        parent=parent,
    )


@browse_bp.route("/download")
def download():
    """Download a requested file as an attachment."""
    rel_path = request.args.get("path", "").strip()
    if not rel_path:
        abort(400, "Missing path parameter")

    downloads_dir = _get_downloads_dir()
    file_path = safe_path(downloads_dir, rel_path)

    if not file_path.is_file():
        abort(404, "File not found")

    return send_file(
        file_path,
        as_attachment=True,
        download_name=file_path.name,
    )
