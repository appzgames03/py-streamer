from flask import Flask, send_file, render_template_string
import os

app = Flask(__name__)

# Folder containing your files
FOLDER_PATH = ""

# Get all files (sorted for consistent numbering)
FILES = [f for f in sorted(os.listdir(FOLDER_PATH)) if os.path.isfile(os.path.join(FOLDER_PATH, f))]

@app.route('/')
def index():
    """Show an index page with numbered download links."""
    html = "<h2>Available Files</h2><ul>"
    for i, filename in enumerate(FILES, start=1):
        html += f'<li><a href="/{i}">File {i}: {filename}</a></li>'
    html += "</ul>"
    return render_template_string(html)

@app.route('/<int:file_number>')
def download(file_number):
    """Serve the file corresponding to its number."""
    if 1 <= file_number <= len(FILES):
        filename = FILES[file_number - 1]
        file_path = os.path.join(FOLDER_PATH, filename)
        return send_file(file_path, as_attachment=True)
    return "Invalid file number", 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
