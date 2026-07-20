#!/usr/bin/env bash

set -e

SCRIPT_NAME="str"
SOURCE_FILE="stream.py"
TARGET_DIR="$HOME/.local/bin"

if [ ! -f "$SOURCE_FILE" ]; then
    echo "Error: '$SOURCE_FILE' file not found in current directory"
    exit 1
fi

mkdir -p "$TARGET_DIR"

chmod +x "$SOURCE_FILE"
cp "$SOURCE_FILE" "$TARGET_DIR/$SCRIPT_NAME"

if ! grep -q 'export PATH="$HOME/.local/bin:$PATH"' "$HOME/.bashrc" 2>/dev/null; then
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
fi

export PATH="$HOME/.local/bin:$PATH"

echo "Installed 'str' to $TARGET_DIR as a wrapper for stream.py"