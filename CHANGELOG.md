# Changelog

All notable changes to pyst are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versions follow [Semantic Versioning](https://semver.org/).

---

## [1.0.0] — Unreleased

### Added
- `pyst serve` — unified web server (file browser, streaming, sync, upload)
- `pyst stream <file>` — quick single-file HTTP stream with Range support
- `pyst download <url>` — video download via yt-dlp
- `pyst torrent <link>` — torrent download via libtorrent
- `pyst zip <folder>` — folder archiver with progress bar
- `src/` package layout following Python packaging best practices
- Flask Blueprint architecture (browse, streaming, sync, upload)
- Shared `config.py` for all constants and paths
- Shared `utils.py` with consolidated `safe_path()`, `get_size()`, `mark_completed()`
- Rich CLI output: URL boxes, progress bars, status messages for every command

### Changed
- Replaced 6 standalone Flask apps on 5 different ports with a single unified server
- Replaced `main.sh`, `str.sh`, `tor.sh` shell wrappers with a proper `pyst` CLI entry point
- Extracted all inline HTML strings into Jinja2 template files
- Consolidated 3 duplicate `safe_path()` implementations into one

### Removed
- `downloader.py` (was a duplicate file browser, not a downloader)
- `browse.py` (URL proxy — niche, security-adjacent utility)
- `install.sh`, `main.sh`, `str.sh`, `tor.sh` (replaced by `pip install -e .`)
