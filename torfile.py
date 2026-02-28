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

# Torrent name (folder name or single file name)
torrent_name = info.name()
print("Starting download:", torrent_name)

# Download loop
while handle.status().state != lt.torrent_status.seeding:
    s = handle.status()
    print(f"Progress: {s.progress * 100:.2f}% | "
          f"Download: {s.download_rate / 1000:.2f} kB/s | "
          f"Upload: {s.upload_rate / 1000:.2f} kB/s | "
          f"Peers: {s.num_peers}")
    time.sleep(1)

# Green bold text
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"

print(f"Download complete => {GREEN}{BOLD}{torrent_name}{RESET}")

marker = os.path.join("./completed", torrent_name + ".completed")

os.makedirs(os.path.dirname(marker), exist_ok=True)
open(marker, "w").close()

print(f"{CYAN}Marked completed{RESET}")
