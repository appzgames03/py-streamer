from flask import Flask, send_file, render_template_string, abort
import os

app = Flask(__name__)

# Base directory you allow browsing (LOCK THIS DOWN)
BASE_DIR = os.path.abspath("./")

TEMPLATE = """
<h2>Browsing: /{{ current_path }}</h2>
<ul>
  {% if parent_path %}
    <li><a href="/browse/{{ parent_path }}">⬅️ .. (up)</a></li>
  {% endif %}
  {% for item in items %}
    {% if item.is_dir %}
      <li>📁 <a href="/browse/{{ item.path }}">{{ item.name }}</a></li>
    {% else %}
      <li>📄 {{ item.name }} —
          <a href="/download/{{ item.path }}">Download</a>
      </li>
    {% endif %}
  {% endfor %}
</ul>
"""

def safe_path(rel_path):
    """Prevent directory traversal."""
    full_path = os.path.abspath(os.path.join(BASE_DIR, rel_path))
    if not full_path.startswith(BASE_DIR):
        abort(403)
    return full_path

@app.route("/")
def root():
    return browse("")

@app.route("/browse/<path:subpath>")
def browse(subpath):
    directory = safe_path(subpath)

    if not os.path.isdir(directory):
        abort(404)

    items = []
    for name in sorted(os.listdir(directory)):
        full = os.path.join(directory, name)
        items.append({
            "name": name,
            "path": os.path.join(subpath, name),
            "is_dir": os.path.isdir(full)
        })

    parent_path = os.path.dirname(subpath) if subpath else None

    return render_template_string(
        TEMPLATE,
        items=items,
        current_path=subpath,
        parent_path=parent_path
    )

@app.route("/download/<path:filepath>")
def download(filepath):
    file_path = safe_path(filepath)

    if not os.path.isfile(file_path):
        abort(404)

    return send_file(file_path, as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
