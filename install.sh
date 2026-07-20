#!/usr/bin/env bash
set -e

# Upgrade pip to latest version
python3 -m pip install --upgrade pip

# Install required Python packages
pip install libtorrent flask yt_dlp

sudo apt update

sudo apt install ffmpeg -y

# Optionally install the `str` command (stream.py) into ~/.local/bin
TARGET_DIR="$HOME/.local/bin"
mkdir -p "$TARGET_DIR"
if [ -f "stream.py" ]; then
	chmod +x "stream.py"
	cp "stream.py" "$TARGET_DIR/str"
	echo "Installed 'str' to $TARGET_DIR"
	if ! grep -q 'export PATH="$HOME/.local/bin:$PATH"' "$HOME/.bashrc" 2>/dev/null; then
		echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
	fi
	export PATH="$HOME/.local/bin:$PATH"
fi
