import os
import sys
import subprocess
import argparse

try:
    import yt_dlp
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "yt_dlp"])
    import yt_dlp

def parse_args():
    parser = argparse.ArgumentParser(description="Download a video from a URL using yt-dlp")
    parser.add_argument('url', help='Video URL to download')
    return parser.parse_args()

def download_video(url):
    with yt_dlp.YoutubeDL({'outtmpl': 'downloads/%(title)s.%(ext)s'}) as ydl:
        info = ydl.extract_info(url, download=True)
        video_filename = os.path.basename(ydl.prepare_filename(info))

    os.makedirs("completed", exist_ok=True)
    marker_path = f"completed/{video_filename}.completed"
    open(marker_path, "w").close()

    print(f"Marked completed: {marker_path}")


if __name__ == '__main__':
    args = parse_args()
    download_video(args.url)
