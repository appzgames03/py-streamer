"""File and directory upload blueprint for pyst.

Supports uploading single or multiple files, as well as preserving whole
directory hierarchies uploaded through webkitdirectory.
"""

from pathlib import Path
from flask import Blueprint, abort, current_app, jsonify, render_template, request

from pyst import config
from pyst.utils import safe_path

upload_bp = Blueprint("upload", __name__, url_prefix="/upload", template_folder="templates")


def _get_uploads_dir() -> Path:
    return Path(current_app.config.get("UPLOADS_DIR", config.UPLOADS_DIR))


@upload_bp.route("", methods=["GET"])
def upload_page():
    """Render the file and directory upload interface."""
    uploads_dir = _get_uploads_dir()
    uploads_dir.mkdir(parents=True, exist_ok=True)
    return render_template("upload.html")


@upload_bp.route("", methods=["POST"])
def handle_upload():
    """Handle incoming multipart file uploads with directory preservation."""
    file = request.files.get("file")
    if not file or not file.filename:
        abort(400, "No file provided")

    rel_path = request.form.get("relpath", file.filename).strip().lstrip("/\\")
    if not rel_path:
        rel_path = file.filename

    uploads_dir = _get_uploads_dir()
    uploads_dir.mkdir(parents=True, exist_ok=True)

    # Prevent directory traversal attacks using safe_path
    save_path = safe_path(uploads_dir, rel_path)

    # Create any missing nested subdirectories
    save_path.parent.mkdir(parents=True, exist_ok=True)

    file.save(save_path)

    return jsonify({
        "status": "ok",
        "path": rel_path,
        "size": save_path.stat().st_size,
    })
