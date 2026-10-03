# py-streamer

A collection of streaming and downloading utilities.

## Install

```bash
sh ./install.sh
```

Installs dependencies and adds three commands to PATH:

- **`tor`** – Torrent downloader (wraps `tor.py`)
- **`str`** – Video streaming server (wraps `stream.py`)
- **`main`** – File browser & downloader (wraps `main.py`)

## Usage

### Stream a video with VLC

```bash
str "/path/to/video.mp4"
```

Access at: `http://localhost:8000/movie`

### Browse and download files

```bash
main
```

Access at: `http://localhost:8080` (file browser with stream & download options)

### Synchronized video playback

```bash
python3 sync-stream.py
```

Choose a video from `downloads/` at `http://localhost:8080/host` to start
playback, then open `http://localhost:8080/client` in any number of browsers.

### convert selected audio to AAC to make MKV compatible (use 0:a:1 for second audio)
```bash
ffmpeg -i <file-path> -map 0:v -map 0:a:0 -c:v copy -c:a aac -b:a 192k output.mkv
```

### See kmv details
```bash
mkvmerge -i <file-path>
```

### Download via torrent

```bash
tor "magnet:..." -p 1
```
