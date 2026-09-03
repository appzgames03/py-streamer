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

### Download via torrent

```bash
tor "magnet:..." -p 1
```
