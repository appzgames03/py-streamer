from flask import *
import os
import zipfile

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

        entries.append({
            "name": name,
            "is_dir": is_dir,
            "rel": os.path.join(rel_path, name),
            "zip_exists": is_dir and os.path.isfile(zip_path)
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
                  {% if e.zip_exists %}
                    [<span style="color:#4CAF50;">Zipped</span>]
                  {% else %}
                    [<a href="/start-zip?path={{ e.rel }}">ZIP</a>]
                  {% endif %}
              {% else %}
                🎬 {{ e.name }}
                  {% if not e.name.endswith('.zip') %}
                    [<a href="/stream?path={{ e.rel }}">Stream</a>]
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

@app.route("/start-zip")
def start_zip():
    rel_path = request.args.get("path")
    if not rel_path:
        abort(400)

    folder_path = safe_path(rel_path)
    if not os.path.isdir(folder_path):
        abort(404)

    zip_folder_with_progress(folder_path)

    return "ZIP completed. Check server terminal and filesystem.", 200


def zip_folder_with_progress(folder_path):
    folder_path = os.path.abspath(folder_path)
    parent = os.path.dirname(folder_path)
    name = os.path.basename(folder_path.rstrip(os.sep))
    zip_path = os.path.join(parent, f"{name}.zip")

    files = []
    for root, _, filenames in os.walk(folder_path):
        for f in filenames:
            files.append(os.path.join(root, f))

    total = len(files)
    print(f"[ZIP] Zipping {folder_path}")
    print(f"[ZIP] Output: {zip_path}")
    print(f"[ZIP] Total files: {total}")

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_STORED) as zipf:
        for i, file in enumerate(files, start=1):
            arcname = os.path.relpath(file, parent)
            zipf.write(file, arcname)

            percent = int((i / total) * 100) if total else 100
            print(f"[ZIP] {percent}% ({i}/{total}) - {arcname}")

    print("[ZIP] Completed")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)
