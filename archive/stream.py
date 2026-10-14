#!/usr/bin/env python3
import os
import sys
import subprocess

try:
  from flask import Flask, request, Response, send_file, abort
except ImportError:
  subprocess.check_call([sys.executable, "-m", "pip", "install", "flask"])
  from flask import Flask, request, Response, send_file, abort

import mimetypes

app = Flask(__name__)


def _stream_generator(path, start, end, chunk_size=4096):
  with open(path, "rb") as f:
    f.seek(start)
    bytes_left = end - start + 1
    while bytes_left > 0:
      read_len = min(chunk_size, bytes_left)
      data = f.read(read_len)
      if not data:
        break
      bytes_left -= len(data)
      yield data


@app.route("/")
def index():
  return "Stream server running. Use /movie to stream the configured file."


@app.route("/movie")
def movie():
  path = app.config.get("VIDEO_PATH")
  if not path or not os.path.isfile(path):
    abort(404)

  file_size = os.path.getsize(path)
  range_header = request.headers.get("Range", None)

  mime = mimetypes.guess_type(path)[0] or "application/octet-stream"

  if range_header:
    # Range header format: "bytes=start-end"
    try:
      range_val = range_header.strip().split("=")[-1]
      start_str, end_str = range_val.split("-")
      start = int(start_str) if start_str else 0
      end = int(end_str) if end_str else file_size - 1
    except Exception:
      start = 0
      end = file_size - 1

    end = min(end, file_size - 1)
    chunk_len = end - start + 1

    resp = Response(_stream_generator(path, start, end), status=206, mimetype=mime)
    resp.headers.add("Content-Range", f"bytes {start}-{end}/{file_size}")
    resp.headers.add("Accept-Ranges", "bytes")
    resp.headers.add("Content-Length", str(chunk_len))
    return resp

  # No Range header; return full file (Flask will handle conditional requests)
  return send_file(path, mimetype=mime, conditional=True)


def main(argv=None):
  argv = argv if argv is not None else sys.argv[1:]
  if not argv:
    print("Usage: stream.py \"/path/to/video/file\" [port]")
    sys.exit(2)

  video_path = argv[0]
  try:
    port = int(argv[1]) if len(argv) > 1 else 8000
  except Exception:
    port = 8000

  if not os.path.isfile(video_path):
    print(f"File not found: {video_path}")
    sys.exit(1)

  app.config["VIDEO_PATH"] = os.path.abspath(video_path)

  # Run the Flask server
  app.run(host="0.0.0.0", port=port, debug=False, threaded=True)


if __name__ == "__main__":
  main()
