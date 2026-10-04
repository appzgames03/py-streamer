# Py-Streamer Script Details

This repository contains a collection of small Python and shell utilities for browsing/downloading media, streaming video files, synchronizing playback across browsers, and downloading torrents.

The scripts are organized around a few core themes:
- Local file browser and media streaming
- Synchronized playback for multiple clients
- Download automation via `yt-dlp` and `libtorrent`
- Uploading files to a local server
- Shell wrappers for installing helpers into PATH

---

## Files at a glance

| File | Type | Main purpose |
| --- | --- | --- |
| [README.md](./README.md) | Documentation | Repo usage summary and installation notes |
| [main.py](./main.py) | Python Flask app | Local file browser, stream links, and file download UI |
| [sync-stream.py](./sync-stream.py) | Python Flask app | Host/client synchronized video playback for multiple browsers |
| [stream.py](./stream.py) | Python Flask app | Simple HTTP video stream server with range requests |
| [downloader.py](./downloader.py) | Python script | Download a video URL using `yt-dlp` and mark it as completed |
| [vidscraper.py](./vidscraper.py) | Python Flask app | Internal browser/proxy that fetches a URL and displays its HTML inside an iframe |
| [browse.py](./browse.py) | Python Flask app | Upload files or a whole folder to the local `uploads/` directory |
| [zipper.py](./zipper.py) | Python script | ZIP a folder with a progress indicator |
| [upload_to_server.py](./upload_to_server.py) | Python Flask app | Upload single or nested files to `uploads/` |
| [tor](./tor) | Python script | Torrent downloader using `libtorrent` |
| [install.sh](./install.sh) | Shell script | Install Python dependencies and package helpers |
| [main.sh](./main.sh) | Shell wrapper | Install the `main` executable |
| [str.sh](./str.sh) | Shell wrapper | Install the `str` executable |
| [tor.sh](./tor.sh) | Shell wrapper | Install the `tor` executable |

---

## 1) [README.md](./README.md)

Purpose:
- High-level project overview.
- Explains the intended commands and usage patterns.

Included instructions:
- Install the toolset with: `sh ./install.sh`
- Installs commands into `~/.local/bin`:
  - `tor` -> torrent downloader wrapper
  - `str` -> video streaming server wrapper
  - `main` -> file browser/downloader wrapper
- Example commands:
  - `str "/path/to/video.mp4"`
  - `main`
  - `python3 sync-stream.py`
  - `tor "magnet:..." -p 1`
- Notes on converting MKV audio streams and checking media metadata with `mkvmerge`.

Significance:
- README is the main user-facing map of how the repo is meant to be used.

---

## 2) [main.py](./main.py)

Purpose:
- Local file browser that lists files in `./downloads`.
- Lets the user stream or download media files from the browse UI.
- Runs a Flask web page on port `8080`.

Key features:
- Restricts browsing to the `./downloads` folder using a path-safety check.
- Lists directory contents and indicates:
  - whether an item is a directory
  - whether a `.zip` archive exists for a directory
  - whether it was previously marked as downloaded (`*.completed`)
- Builds a basic HTML interface with:
  - directory navigation
  - stream links and direct download links
  - an inline video view for local files
- Uses `send_file()` for direct streaming or download.

Routes:
- `/` -> list the current directory under `downloads`
- `/stream` -> show a page with an HTML5 video player for a selected file
- `/vlc` -> serve the file with a guessed MIME type for browser playback
- `/download` -> download the selected file as an attachment

Security handling:
- `safe_path()` prevents directory traversal outside `BASE_DIR` by restricting paths to the allowed root.

Notes:
- The interface is lightweight and focused on browsing local media libraries.
- This script is primarily a local media browser rather than a downloader on its own.

---

## 3) [sync-stream.py](./sync-stream.py)

Purpose:
- Creates a synchronized multi-browser video playback experience.
- One browser acts as the host and selects a video; clients follow the same playback state.

Key features:
- Uses Flask + a thread-safe shared `playback` state dictionary.
- Tracks:
  - selected file
  - current playhead position
  - paused/playing state
  - revision counter for change notifications
- Exposes two roles in the same page:
  - `/host` -> browser that selects a video and controls the shared stream
  - `/watch` -> client browser that mirrors the host playback state
- Clients poll `/api/state` using `after=<revision>` and wait updates when no state change occurs.
- Video file access is limited to files under `downloads/` and only for supported extensions.

Main endpoints:
- `/` -> redirects to `/watch`
- `/host` -> host page with video selector
- `/watch` -> client page with no selector
- `/api/state` -> returns the current synchronized playback state
- `/api/control` -> receives actions (`select`, `play`, `pause`) and updates the host state
- `/video` -> serves the selected video file to the browser

Playback logic:
- When the host selects a file, the app stores the path and resets the playback position to `0`.
- Client browsers open the selected file and sync position and play/pause state.
- A revision number ensures every client updates only when the stream state changes.
- Accepts numeric playhead values and validates them before applying to the shared state.

Port:
- Runs on `0.0.0.0:8085` by default.

Use case:
- Useful for showing the same video to multiple devices or browser tabs at once.

---

## 4) [stream.py](./stream.py)

Purpose:
- Simple streaming server for a single video file.
- Designed to serve media over HTTP with support for `Range` requests.

Key features:
- Accepts a file path as the first command-line argument.
- Optionally accepts a port as the second argument; defaults to `8000`.
- Uses Flask and `send_file` for efficient file serving.
- Implements partial content support (`206 Partial Content`) for seeking and playback in browsers/VLC.
- Generates a byte-range stream with `_stream_generator()`.

CLI usage:
```bash
python3 stream.py "/path/to/video.mp4"
python3 stream.py "/path/to/video.mp4" 9000
```

Endpoints:
- `/` -> informational page
- `/movie` -> streams the configured file

Behavior:
- Reads `Range` headers from clients to resume or seek in the video.
- Adds headers such as `Content-Range`, `Accept-Ranges`, and `Content-Length` when partial data is served.
- If no range header is supplied, it streams the full file normally.

Use case:
- Simple media-serving utility for local playback in browser or VLC.

---

## 5) [downloader.py](./downloader.py)

Purpose:
- Downloads a media file from a URL using `yt-dlp`.
- Creates a `.completed` marker in the `completed/` directory after a successful download.

Key features:
- Uses `argparse` for a single positional URL argument.
- Invokes `yt_dlp.YoutubeDL` with an output template of:
  - `downloads/%(title)s.%(ext)s`
- Creates the `completed/` folder if needed.
- Writes an empty marker file like:
  - `completed/<video_filename>.completed`

Behavior:
- `download_video(url)` calls `ydl.extract_info(..., download=True)`.
- It then saves the final filename and marks it complete.

CLI usage:
```bash
python3 downloader.py "https://example.com/video"
```

Notes:
- Useful for one-off media fetching from a URL source without complex configuration.

---

## 6) [vidscraper.py](./vidscraper.py)

Purpose:
- Simple local web proxy/browser used to fetch a page from another URL and display it inside an iframe.

Key features:
- Provides a form with an input for a URL and an iframe panel.
- Accepts a POST to `/browse` with JSON payload: `{ "url": "..." }`.
- Validates URL scheme to permit only `http` and `https`.
- Uses `requests.get()` to fetch the target page.
- Returns the response HTML inside the iframe.

Validation:
- The `validate_url()` helper ensures the URL is properly formatted and uses an allowed scheme.

Routes:
- `/` -> main page with URL field and iframe
- `/browse` -> POST endpoint for fetching the target page and echoing its HTML

Use case:
- Lightweight internal browsing/proxy tool for testing or viewing remote pages locally.

---

## 7) [browse.py](./browse.py)

Purpose:
- Upload local files or a full folder tree to the server.
- Stores uploaded data under the `uploads/` directory.

Key features:
- HTML page has two upload options:
  - files
  - whole folder via `webkitdirectory` input
- JavaScript uses `XMLHttpRequest` to send each file as `FormData`.
- Each upload includes:
  - `file`
  - `relpath` (used to reconstruct a directory structure)
- Creates directories as needed using `os.makedirs(...)`.
- Displays upload progress using a `<progress>` bar.

Routes:
- `/` -> upload UI
- `/upload` -> receives file uploads and saves them under `uploads/`

Behavior:
- For folder uploads, the browser sends `webkitRelativePath`, which is used to preserve the nested directory layout.
- The server writes each file to the matching path inside the upload folder.

Use case:
- Quick local file transfer to a server directory.

---

## 8) [zipper.py](./zipper.py)

Purpose:
- ZIPs a folder into a `.zip` file and prints progress to the console.

Key features:
- Uses `zipfile.ZipFile`.
- Walks the folder tree with `os.walk()` to collect all files.
- Prints the total number of files and the current progress.
- Writes each file with a relative path inside the zip archive.

Global variables:
- `folder_path` is expected to be set before running the script.

Main flow:
- Verify the path is a directory.
- Determine the parent directory and zip filename.
- Iterate through all files and compress them in place.

Use case:
- Archive a directory with a simple terminal progress view.

---

## 9) [upload_to_server.py](./upload_to_server.py)

Purpose:
- Similar to a simple upload endpoint for direct file transfers.
- Saves files to a local `uploads/` directory via Flask.

Key features:
- Has a minimal HTML upload form, though the more elaborate folder uploader lives in [browse.py](./browse.py).
- Accepts `POST` uploads to `/upload`.
- Uses a `relpath` from the request to recreate nested folders.
- Saves the file with `file.save(save_path)`.

Routes:
- `/` -> page with upload form
- `/upload` -> handles the actual file input

Use case:
- Basic upload server for one-off file transfer to a local directory.

---

## 10) [tor](./tor)

Purpose:
- Torrent downloader using the `libtorrent` library.
- Supports both magnet links and `.torrent` files.

Key features:
- Accepts a link as the first argument and optional `--port/-p` as the last two digits of the chosen port range.
- Uses a port-range strategy to avoid conflicts.
- Creates a libtorrent session and listens on a chosen port window.
- For magnet downloads, it waits until metadata is available before starting the download loop.
- Tracks download progress and prints a live ASCII progress bar.
- Marks downloads as complete by creating a marker file in `./completed`.

Important directories:
- `./downloads` -> final save folder
- `./files` -> downloaded torrent files stored when the input is a torrent URL
- `./completed` -> completion marker directory

CLI usage:
```bash
./tor "magnet:?xt=urn:btih:..."
./tor "https://example.com/file.torrent"
./tor "magnet:?xt=urn:btih:..." -p 1
```

Important behaviors:
- Checks for available port ranges before starting.
- Uses `lt.add_magnet_uri()` or `session.add_torrent()` depending on the source.
- Keeps a progress display in the terminal until the torrent finishes seeding.

---

## 11) [install.sh](./install.sh)

Purpose:
- System setup script for installing the project dependencies and command wrappers.

What it does:
- Upgrades `pip`
- Installs the required packages:
  - `libtorrent`
  - `flask`
  - `yt_dlp`
- Runs `apt update`
- Installs:
  - `ffmpeg`
  - `mkvtoolnix`
- Creates `$HOME/.local/bin` if needed
- Copies wrappers for `str` and `main` into the PATH
- Appends `export PATH="$HOME/.local/bin:$PATH"` to `~/.bashrc` if missing

Notes:
- This is the repo's main environment bootstrap script.
- It also prepares the local command environment for media-related tasks.

---

## 12) [main.sh](./main.sh)

Purpose:
- Shell wrapper that installs the `main` command to `~/.local/bin`.

Behavior:
- Checks for [main.py](./main.py)
- Makes it executable
- Copies it to `~/.local/bin/main`
- Ensures `~/.local/bin` is in PATH

Result:
- Running `main` in the shell will invoke the file browser/downloader script.

---

## 13) [str.sh](./str.sh)

Purpose:
- Shell wrapper that installs the `str` command to `~/.local/bin`.

Behavior:
- Checks for [stream.py](./stream.py)
- Makes it executable
- Copies it to `~/.local/bin/str`
- Ensures the PATH includes `~/.local/bin`

Result:
- Running `str` launches the stream server command.

---

## 14) [tor.sh](./tor.sh)

Purpose:
- Shell wrapper that installs the `tor` command to `~/.local/bin`.

Behavior:
- Checks for a `tor` file in the current directory
- Makes it executable
- Copies it to `~/.local/bin/tor`
- Adds `~/.local/bin` to PATH if needed

Result:
- Running `tor` launches the libtorrent download utility.

---

## Common patterns across the repo

A few patterns repeat throughout the project:
- Flask is the central web framework used by nearly every server script.
- Local directories like `downloads/`, `completed/`, and `uploads/` are treated as runtime storage.
- Many scripts assume a Unix-like environment with `bash`, `pip`, and `apt` available.
- The repo is built for local media workflows rather than a packaged app.

## Quick command map

```bash
# Install dependencies and command shims
sh ./install.sh

# Stream one file through an HTTP server
str "/path/to/video.mp4"

# Run the local media browser / downloader UI
main

# Run the synchronized multi-client viewer
python3 sync-stream.py

# Download a video URL with yt-dlp
ython3 downloader.py "https://example.com/video"

# Use the torrent downloader
./tor "magnet:?xt=urn:btih:..."
```

---

## Summary

This repository is essentially a toolkit for local multimedia handling:
- browsing local files and downloads,
- streaming videos,
- synchronizing playback across clients,
- uploading files,
- downloading torrents,
- and fetching media links from the web.

The project is intentionally lightweight and script-oriented rather than packaged as a full application.
