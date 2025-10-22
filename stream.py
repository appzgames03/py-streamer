# video_server.py
from flask import Flask, request, Response, send_file
import os

VIDEO_PATH = "The Amazing Spiderman (2012)/The.Amazing.Spiderman.2012.720p.BrRip.x264.YIFY.mp4"
app = Flask(__name__)


@app.route('/')
def stream_video():
  range_header = request.headers.get('Range', None)
  file_size = os.path.getsize(VIDEO_PATH)
  start = 0
  end = file_size - 1

  if range_header:
    # Example: "bytes=0-1023"
    range_match = range_header.replace('bytes=', '').split('-')
    start = int(range_match[0])
    if range_match[1]:
      end = int(range_match[1])
    chunk_size = end - start + 1

    def generate():
      with open(VIDEO_PATH, 'rb') as f:
        f.seek(start)
        bytes_left = chunk_size
        while bytes_left > 0:
          read_len = min(4096, bytes_left)
          data = f.read(read_len)
          if not data:
            break
          bytes_left -= len(data)
          yield data

    rv = Response(generate(), status=206, mimetype='video/mp4')
    rv.headers.add('Content-Range', f'bytes {start}-{end}/{file_size}')
    rv.headers.add('Accept-Ranges', 'bytes')
    rv.headers.add('Content-Length', str(chunk_size))
    return rv
  else:
    return send_file(VIDEO_PATH, mimetype='video/mp4')


if __name__ == "__main__":
  app.run(host="0.0.0.0", port=8000, debug=False)
