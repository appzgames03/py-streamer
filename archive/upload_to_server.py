from flask import Flask, request, render_template_string
import os

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

HTML_PAGE = """
<!doctype html>
<title>Upload Files or Folder</title>
<h2>Upload files or an entire folder</h2>

<!-- Buttons for choosing mode -->
<p>
  <button onclick="document.getElementById('fileInput').click()">Select Files</button>
  <button onclick="document.getElementById('folderInput').click()">Select Folder</button>
</p>

<!-- Hidden file inputs -->
<input type="file" id="fileInput" multiple style="display:none" onchange="uploadFiles(this.files)">
<input type="file" id="folderInput" webkitdirectory directory multiple style="display:none" onchange="uploadFiles(this.files)">

<div id="progressContainer"></div>
<p id="status"></p>

<script>
function uploadFiles(files) {
    if (!files.length) {
        alert("No files selected.");
        return;
    }

    document.getElementById("progressContainer").innerHTML = "";
    document.getElementById("status").textContent = "Uploading...";

    for (let i = 0; i < files.length; i++) {
        const file = files[i];
        const relPath = file.webkitRelativePath || file.name;

        const div = document.createElement("div");
        div.innerHTML = `<p>${relPath}</p>
                         <progress id="progress${i}" value="0" max="100" style="width:300px;"></progress>`;
        document.getElementById("progressContainer").appendChild(div);

        const xhr = new XMLHttpRequest();
        xhr.open("POST", "/upload", true);

        xhr.upload.onprogress = function(event) {
            if (event.lengthComputable) {
                const percent = (event.loaded / event.total) * 100;
                document.getElementById("progress" + i).value = percent;
            }
        };

        xhr.onload = function() {
            if (xhr.status === 200) {
                div.innerHTML += " ✅ Uploaded";
            } else {
                div.innerHTML += " ❌ Failed";
            }
        };

        const formData = new FormData();
        formData.append("file", file);
        formData.append("relpath", relPath);  // send relative path for folder reconstruction
        xhr.send(formData);
    }
}
</script>
"""

@app.route("/")
def index():
    return render_template_string(HTML_PAGE)

@app.route("/upload", methods=["POST"])
def upload_file():
    file = request.files.get("file")
    rel_path = request.form.get("relpath", file.filename if file else None)
    if file and rel_path:
        save_path = os.path.join(UPLOAD_FOLDER, rel_path)
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        file.save(save_path)
        return f"Uploaded: {rel_path}"
    return "No file uploaded.", 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
