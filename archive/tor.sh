#!/usr/bin/env bash

set -e

SCRIPT_NAME="tor"
TARGET_DIR="$HOME/.local/bin"

# Verify file exists
if [ ! -f "$SCRIPT_NAME" ]; then
    echo "Error: '$SCRIPT_NAME' file not found in current directory"
    exit 1
fi

# Create local bin if missing
mkdir -p "$TARGET_DIR"

# Add execute permission
chmod +x "$SCRIPT_NAME"

# Move script to PATH
cp "$SCRIPT_NAME" "$TARGET_DIR/$SCRIPT_NAME"

# Ensure ~/.local/bin is in PATH
if ! grep -q 'export PATH="$HOME/.local/bin:$PATH"' "$HOME/.bashrc"; then
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
fi

# Reload shell config for current session
export PATH="$HOME/.local/bin:$PATH"

echo "tor installed successfully."