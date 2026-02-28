import libtorrent as lt
import time
import os

# Replace with your magnet link
magnet_link = ""

# Create a session
ses = lt.session()
ses.listen_on(6881, 6891)

# Add the magnet link
params = {
    'save_path': './downloads',  # folder where files will be saved
    'storage_mode': lt.storage_mode_t.storage_mode_sparse
}
handle = lt.add_magnet_uri(ses, magnet_link, params)

print("Fetching metadata...")
while not handle.has_metadata():
    time.sleep(1)
print("Metadata retrieved, starting download...")

# Get torrent info
info = handle.get_torrent_info()

# Torrent name (folder name or single file name)
torrent_name = info.name()
print("Starting download:", torrent_name)

# Download loop
while handle.status().state != lt.torrent_status.seeding:
    s = handle.status()
    print(f"Progress: {s.progress * 100:.2f}%, "
          f"Download: {s.download_rate / 1000:.2f} kB/s, "
          f"Upload: {s.upload_rate / 1000:.2f} kB/s, "
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
