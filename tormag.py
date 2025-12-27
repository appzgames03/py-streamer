import libtorrent as lt
import time


# Replace with your magnet link
magnet_link = ""

# Create a session
ses = lt.session()
ses.listen_on(6881, 6891)

# Add the magnet link
params = {
    'save_path': './',  # folder where files will be saved
    'storage_mode': lt.storage_mode_t.storage_mode_sparse
}
handle = lt.add_magnet_uri(ses, magnet_link, params)

print("Fetching metadata...")
while not handle.has_metadata():
    time.sleep(1)
print("Metadata retrieved, starting download...")

# Download loop
while handle.status().state != lt.torrent_status.seeding:
    s = handle.status()
    print(f"Progress: {s.progress * 100:.2f}%, "
          f"Download: {s.download_rate / 1000:.2f} kB/s, "
          f"Upload: {s.upload_rate / 1000:.2f} kB/s, "
          f"Peers: {s.num_peers}")
    time.sleep(1)

print(f"Download complete! => {magnet_link[:150]}")
