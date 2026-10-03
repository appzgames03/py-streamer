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
Play and pause actions are synchronized across browsers, with the position at
the time of each action. Seeking pauses playback and synchronizes the seek
position on every browser; press play to resume from that point. Clients wait
for playback changes instead of repeatedly polling or correcting their
playback position. A browser may require one click on **Enable playback**
before it allows playback to start.

### Download via torrent

```bash
tor "magnet:..." -p 1
```
