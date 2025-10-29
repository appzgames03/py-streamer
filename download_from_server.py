from flask import Flask, send_file

app = Flask(__name__)

# Hardcoded file path
file_path = "<file path>"  # replace with your file

@app.route('/')
def download():
    """Serve the file as a downloadable attachment"""
    return send_file(file_path, as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
