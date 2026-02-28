from flask import *
import os
import zipfile

BASE_DIR = "./downloads"
COMPLETED_DIR = "./completed"
CHUNK_SIZE = 4096

app = Flask(__name__)


def safe_path(rel_path):
    full_path = os.path.abspath(os.path.join(BASE_DIR, rel_path))
    if not full_path.startswith(os.path.abspath(BASE_DIR)):
        abort(403)
    return full_path


BASE_STYLE = """
<style>
  body {
    background-color: #000;
    color: #ddd;
    font-family: Arial, sans-serif;
    font-size: 2em;
    line-height: 1.6;
  }
  a {
    color: #4da3ff;
    text-decoration: none;
    font-size: 1em;
  }
  a:hover {
    text-decoration: underline;
  }
  ul {
    list-style-type: none;
    padding-left: 0;
  }
  li {
    margin: 10px 0;
    font-size: 1em;
  }
  video {
    display: block;
    margin: 20px auto;
    background: black;
  }
</style>
"""

def get_size(path):
    """Return human readable size for file or directory."""
    if os.path.isfile(path):
        size = os.path.getsize(path)
    else:
        size = 0
        for root, dirs, files in os.walk(path):
            for f in files:
                fp = os.path.join(root, f)
                if os.path.exists(fp):
                    size += os.path.getsize(fp)

    # convert to readable format
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} PB"

@app.route("/")
def browse():
    rel_path = request.args.get("path", "")
    current_path = safe_path(rel_path)

    if not os.path.isdir(current_path):
        abort(404)

    entries = []
    for name in sorted(os.listdir(current_path)):
        full = os.path.join(current_path, name)

        is_dir = os.path.isdir(full)
        zip_path = os.path.join(current_path, f"{name}.zip")

        marker = os.path.join(COMPLETED_DIR, os.path.join(rel_path, name) + ".completed")

        entries.append({
            "name": name,
            "is_dir": is_dir,
            "rel": os.path.join(rel_path, name),
            "zip_exists": is_dir and os.path.isfile(zip_path),
            "size": get_size(full),
            "downloaded": os.path.exists(marker)
        })

    parent = os.path.dirname(rel_path) if rel_path else None

    html = """
    <html>
      <head>{{ style|safe }}</head>
      <body>
        <h2>Browsing: /{{ rel_path }}</h2>

        {% if parent is not none %}
          <p><a href="/?path={{ parent }}">⬅ Back</a></p>
        {% endif %}

        <ul>
          {% for e in entries %}
            <li>
              {% if e.is_dir %}
                📁 <a href="/?path={{ e.rel }}">{{ e.name }}</a>
                <small style="color:#888;">({{ e.size }})</small>
                  {% if e.downloaded %}
                    <span style="color:#00ff00;">●</span>
                  {% endif %}
                  {% if e.zip_exists %}
                    [<span style="color:#4CAF50;">Zipped</span>]
                  {% endif %}
              {% else %}
                🎬 {{ e.name }}
                <small style="color:#888;">({{ e.size }})</small>
                  {% if e.downloaded %}
                    <span style="color:#00ff00;">●</span>
                  {% endif %}
                  {% if not e.name.endswith('.zip') %}
                    [<a href="/stream?path={{ e.rel }}">Stream</a>]
                    [<a href="/vlc?path={{ e.rel }}">vlc</a>]
                  {% endif %}
                [<a href="/download?path={{ e.rel }}">Download</a>]
              {% endif %}
            </li>
            <hr>
          {% endfor %}
        </ul>
      </body>
    </html>
    """

    return render_template_string(
        html,
        style=BASE_STYLE,
        entries=entries,
        rel_path=rel_path,
        parent=parent
    )


@app.route("/stream")
def stream_page():
    rel_path = request.args.get("path")
    if not rel_path:
        abort(400)

    full_path = safe_path(rel_path)

    if not os.path.isfile(full_path):
        abort(404)

    html = """
    <html>
      <head>{{ style|safe }}</head>
      <body>
        <h2>{{ filename }}</h2>
        <p><a href="/?path={{ parent }}">⬅ Back</a></p>

        <video width="720" controls autoplay>
          <source src="/vlc?path={{ rel_path }}" type="video/mp4">
        </video>
      </body>
    </html>
    """

    return render_template_string(
        html,
        style=BASE_STYLE,
        filename=os.path.basename(full_path),
        rel_path=rel_path,
        parent=os.path.dirname(rel_path)
    )


@app.route("/vlc")
def video_stream():
    import mimetypes

    rel_path = request.args.get("path")
    full_path = safe_path(rel_path)

    if not os.path.isfile(full_path):
        abort(404)

    mime = mimetypes.guess_type(full_path)[0] or "application/octet-stream"

    return send_file(
        full_path,
        mimetype=mime,
        conditional=True
    )


@app.route("/download")
def download_file():
    rel_path = request.args.get("path")
    if not rel_path:
        abort(400)

    full_path = safe_path(rel_path)

    if not os.path.isfile(full_path):
        abort(404)

    return send_file(
        full_path,
        as_attachment=True,
        download_name=os.path.basename(full_path)
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)
