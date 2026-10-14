# pyst (py-streamer)

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests: Pytest](https://img.shields.io/badge/tests-passing-brightgreen.svg)]()

A unified local media streaming, synchronized playback, and downloading toolkit.

`pyst` consolidates media browsing, HTTP Range video streaming, synchronized multi-device watch parties, file uploads, BitTorrent downloading, and web video extraction into **a single CLI tool that starts a web server**.

---

## Features

- 🌐 **Unified Web Server**: Browse, stream, watch together, and upload files from a single server on one port (`http://localhost:8080`).
- 🎬 **HTTP Range Video Streaming**: Stream media with full seeking support (`206 Partial Content`) in modern browsers and media players like VLC.
- 👥 **Synchronized Watch Party**: Host and client playback synchronized in real time across multiple browsers and devices on your LAN.
- 📥 **BitTorrent Downloader**: Built-in CLI torrent client using `libtorrent` with automatic port selection and live progress bars.
- 📹 **Web Video Extraction**: High-speed video downloader powered by `yt-dlp`.
- 📦 **Directory Archiver**: Zip directories with live progress tracking in the terminal.

---

## Installation

Clone the repository and install in editable mode:

```bash
git clone https://github.com/your-username/py-streamer.git
cd py-streamer
pip install -e .
```

### System Dependencies

For optimal video format compatibility and MKV audio stream conversion, install `ffmpeg` and `mkvtoolnix`:

**Ubuntu / Debian:**
```bash
sudo apt update && sudo apt install ffmpeg mkvtoolnix -y
```

**macOS (Homebrew):**
```bash
brew install ffmpeg mkvtoolnix
```

**Windows (Winget / Chocolatey):**
```powershell
winget install Gyan.FFmpeg
winget install MoritzBunkus.MKVToolNix
```

---

## Quick Start

### 1. Start the Full Web Server
Launches the web UI with file browsing, synchronized playback, and upload capabilities:

```bash
pyst serve
```

```text
  ╭──────────────────────────────────────────────────────╮
  │  pyst v1.0.0 — Media Server                          │
  │                                                      │
  │  Dashboard:        http://localhost:8080/            │
  │  File Browser:     http://localhost:8080/browse      │
  │  Sync Player:      http://localhost:8080/sync        │
  │  Upload:           http://localhost:8080/upload      │
  │  On LAN:           http://192.168.1.100:8080/        │
  │                                                      │
  │  Serving files from: ./downloads                     │
  │  Uploads go to:      ./uploads                       │
  │  Press Ctrl+C to stop.                               │
  ╰──────────────────────────────────────────────────────╯
```

Options:
- `-p, --port <int>`: Port for the web server (default: `8080`).
- `--host <str>`: Bind interface (default: `0.0.0.0` to allow local network devices).
- `--no-browser`: Do not automatically open a browser window on startup.

---

### 2. Quick Stream a Single Video
Stream a specific video file without loading the full browser UI:

```bash
pyst stream "/path/to/movie.mp4"
```

- Open in browser: `http://localhost:8000/`
- Open in VLC: `Media` → `Open Network Stream...` → enter `http://localhost:8000/movie`

---

### 3. Download Web Videos
Download videos from YouTube, Vimeo, Twitter, Archive.org, and hundreds of sites:

```bash
pyst download "https://archive.org/details/BigBuckBunny_124"
```

Downloads are saved to `./downloads` and marked as completed.

---

### 4. Download BitTorrents
Download torrents directly in your terminal using a magnet link or `.torrent` file URL:

```bash
# Magnet link
pyst torrent "magnet:?xt=urn:btih:..."

# Torrent file URL
pyst torrent "https://example.com/movie.torrent"

# Specify custom port range suffix (e.g. 01 for ports 6701-6751)
pyst torrent "magnet:?xt=urn:btih:..." -p 01
```

---

### 5. Zip a Folder
Create a compressed archive with live progress in the terminal:

```bash
pyst zip ./downloads/my-tv-show
pyst zip ./downloads/my-tv-show -o ./backup.zip
```

---

## Web Server URL Map

| Route | Description |
|---|---|
| `/` | **Dashboard**: System overview, library statistics, and quick navigation |
| `/browse` | **File Browser**: Directory navigator for `./downloads` with search and stream buttons |
| `/browse?path=subfolder` | Subdirectory browsing with directory traversal protection |
| `/stream?path=movie.mp4` | HTML5 video player with seek bar and player controls |
| `/play?path=movie.mp4` | Raw video stream supporting HTTP `Range` requests (`206 Partial Content`) |
| `/download?path=file.ext` | Direct file download as an attachment |
| `/sync/host` | Host view for synchronized watch parties (select and control playback) |
| `/sync/watch` | Client view for synchronized watch parties (automatically follows host) |
| `/upload` | File & directory upload center with drag-and-drop and progress tracking |

---

## Project Structure

Following standard Python packaging best practices (`src` layout):

```
py-streamer/
├── pyproject.toml              # Project metadata, dependencies, and CLI entry point
├── README.md                   # Project documentation
├── CHANGELOG.md                # Version history
├── LICENSE                     # MIT License
├── src/
│   └── pyst/
│       ├── __init__.py         # Package version
│       ├── __main__.py         # python -m pyst support
│       ├── cli.py              # Click CLI definition and subcommand routing
│       ├── config.py           # Shared paths, ports, and constants
│       ├── utils.py            # safe_path, get_size, mark_completed
│       ├── downloader.py       # yt-dlp video downloader module
│       ├── torrent.py          # libtorrent BitTorrent download module
│       ├── zipper.py           # Directory compression utility
│       └── server/
│           ├── __init__.py
│           ├── app.py          # Flask application factory (create_app)
│           ├── browse.py       # File browsing and dashboard Blueprint
│           ├── streaming.py    # HTTP Range video streaming Blueprint
│           ├── sync.py         # Multi-client synchronized playback Blueprint
│           ├── upload.py       # File and directory upload Blueprint
│           └── templates/      # Jinja2 HTML templates
│               ├── base.html
│               ├── dashboard.html
│               ├── browse.html
│               ├── stream.html
│               ├── sync.html
│               └── upload.html
├── tests/                      # Unit test suite (31 tests)
│   ├── test_cli.py
│   ├── test_browse.py
│   ├── test_streaming.py
│   ├── test_sync.py
│   ├── test_upload.py
│   ├── test_utils.py
│   └── test_zipper.py
└── archive/                    # Archived legacy scripts for historical reference
```

---

## Useful FFmpeg Commands

Convert audio to AAC for universal browser playback compatibility:

```bash
ffmpeg -i input.mkv -map 0:v -map 0:a:0 -c:v copy -c:a aac -b:a 192k output.mkv
```

Inspect MKV tracks and metadata:

```bash
mkvmerge -i input.mkv
```

---

## Running Tests

Run the complete test suite with `pytest`:

```bash
pytest -v
```

---

## License

This project is licensed under the [MIT License](LICENSE).
