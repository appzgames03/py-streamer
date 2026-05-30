from urllib.parse import urlparse

from flask import Flask, request, jsonify, render_template_string
import requests

app = Flask(__name__)

HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Internal Browser</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
        }

        .toolbar {
            display: flex;
            gap: 10px;
            margin-bottom: 10px;
        }

        input {
            flex: 1;
            padding: 10px;
            font-size: 16px;
        }

        button {
            padding: 10px 16px;
            cursor: pointer;
        }

        iframe {
            width: 100%;
            height: 85vh;
            border: 1px solid #ccc;
        }
    </style>
</head>
<body>
    <h2>Internal Browser</h2>

    <div class="toolbar">
        <input
            id="urlInput"
            type="text"
            placeholder="http://localhost:8080"
        />
        <button onclick="openUrl()">Open</button>
    </div>

    <iframe id="browserFrame"></iframe>

    <script>
        async function openUrl() {
            const url = document.getElementById("urlInput").value;

            if (!url) {
                alert("Enter URL");
                return;
            }

            const response = await fetch("/browse", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ url })
            });

            const result = await response.text();

            const iframe =
                document.getElementById("browserFrame");

            iframe.srcdoc = result;
        }
    </script>
</body>
</html>
"""


def validate_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
        return parsed.scheme in ("http", "https")
    except Exception:
        return False


@app.route("/")
def home():
    return render_template_string(HTML_PAGE)


@app.route("/browse", methods=["POST"])
def browse():
    data = request.json
    url = data.get("url", "").strip()

    if not validate_url(url):
        return "Invalid URL", 400

    try:
        response = requests.get(
            url,
            timeout=15,
            headers={
                "User-Agent": "InternalBrowser/1.0"
            }
        )

        return response.text

    except requests.RequestException as e:
        return f"<h3>Request failed</h3><pre>{str(e)}</pre>", 500


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )