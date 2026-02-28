import yt_dlp
import os

video_url = ""

def download_video(url):
    with yt_dlp.YoutubeDL({'outtmpl': 'downloads/%(title)s.%(ext)s'}) as ydl:
        info = ydl.extract_info(url, download=True)
        video_filename = os.path.basename(ydl.prepare_filename(info))

    os.makedirs("completed", exist_ok=True)
    marker_path = f"completed/{video_filename}.completed"
    open(marker_path, "w").close()

    print(f"Marked completed: {marker_path}")

download_video(video_url)
