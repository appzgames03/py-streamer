from flask import Flask, request, Response, abort, render_template_string, send_file
import os

BASE_DIR = "./downloads"
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
  }
  a {
    color: #4da3ff;
    text-decoration: none;
  }
  a:hover {
    text-decoration: underline;
  }
  ul {
    list-style-type: none;
    padding-left: 0;
  }
  li {
    margin: 8px 0;
  }
  video {
    display: block;
    margin: 20px auto;
    background: black;
  }
</style>
"""


@app.route("/")
def browse():
    rel_path = request.args.get("path", "")
    current_path = safe_path(rel_path)

    if not os.path.isdir(current_path):
        abort(404)

    entries = []
    for name in sorted(os.listdir(current_path)):
        full = os.path.join(current_path, name)
        entries.append({
            "name": name,
            "is_dir": os.path.isdir(full),
            "rel": os.path.join(rel_path, name)
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
              {% else %}
                🎬 {{ e.name }}
                [<a href="/stream?path={{ e.rel }}">Stream</a>]
                [<a href="/download?path={{ e.rel }}">Download</a>]
              {% endif %}
            </li>
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
          <source src="/video?path={{ rel_path }}" type="video/mp4">
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


@app.route("/video")
def video_stream():
    rel_path = request.args.get("path")
    full_path = safe_path(rel_path)

    if not os.path.isfile(full_path):
        abort(404)

    file_size = os.path.getsize(full_path)
    range_header = request.headers.get("Range")

    start = 0
    end = file_size - 1

    if range_header:
        bytes_range = range_header.replace("bytes=", "").split("-")
        start = int(bytes_range[0])
        if bytes_range[1]:
            end = int(bytes_range[1])

    length = end - start + 1

    def generate():
        with open(full_path, "rb") as f:
            f.seek(start)
            remaining = length
            while remaining > 0:
                data = f.read(min(CHUNK_SIZE, remaining))
                if not data:
                    break
                remaining -= len(data)
                yield data

    response = Response(generate(), status=206, mimetype="video/mp4")
    response.headers.add("Content-Range", f"bytes {start}-{end}/{file_size}")
    response.headers.add("Accept-Ranges", "bytes")
    response.headers.add("Content-Length", str(length))
    return response


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
    app.run(host="0.0.0.0", port=8010, debug=False)
