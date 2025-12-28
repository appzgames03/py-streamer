import libtorrent as lt
import time
import os

# Path to your .torrent file
torrent_file = ""

# Folder to save the downloaded content
save_path = "./downloads"
os.makedirs(save_path, exist_ok=True)

# Create a session
ses = lt.session()
ses.listen_on(6881, 6891)

# Read the .torrent file
info = lt.torrent_info(torrent_file)
handle = ses.add_torrent({'ti': info, 'save_path': save_path})

print(f"Starting download: {info.name()}")

# Download loop
while handle.status().state != lt.torrent_status.seeding:
    s = handle.status()
    print(f"Progress: {s.progress * 100:.2f}% | "
          f"Download: {s.download_rate / 1000:.2f} kB/s | "
          f"Upload: {s.upload_rate / 1000:.2f} kB/s | "
          f"Peers: {s.num_peers}")
    time.sleep(1)

print(f"Download complete! => {torrent_file[:150]}")
