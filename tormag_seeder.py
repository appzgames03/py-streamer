import libtorrent as lt
import time


# Replace with your magnet link
magnet_link = "magnet:?xt=urn:btih:3761370BCC46F33F94E2DD9D9976FDC1A0130532&dn=%5BBitsearch.to%5D%20Dark%20-%20Season%203%20(2020)%20%5B1080p%5D&tr=udp%3A%2F%2Ftracker2.dler.com%3A80%2Fannounce&tr=udp%3A%2F%2Fwww.torrent.eu.org%3A451%2Fannounce&tr=udp%3A%2F%2Ftracker.torrent.eu.org%3A451%2Fannounce&tr=udp%3A%2F%2Ftracker.opentrackr.org%3A1337%2Fannounce&tr=udp%3A%2F%2Fpow7.com%3A80%2Fannounce&tr=udp%3A%2F%2Ftracker.bitsearch.to%3A1337%2Fannounce"

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

print("Download complete!")
