#!/usr/bin/env bash
set -e

# Upgrade pip to latest version
python3 -m pip install --upgrade pip

# Install required Python packages
pip install libtorrent flask yt_dlp
