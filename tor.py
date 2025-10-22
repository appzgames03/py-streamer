import libtorrent as lt
import time

# Replace with your magnet link
magnet_link = "magnet:?xt=urn:btih:E6868E3A4A933214731316C5F3D149B7C508E955&dn=South+Park+S27E06-HDTV-X264&tr=udp%3A%2F%2Fopen.stealth.si%3A80%2Fannounce&tr=udp%3A%2F%2Fexodus.desync.com%3A6969%2Fannounce&tr=udp%3A%2F%2Ftracker.cyberia.is%3A6969%2Fannounce&tr=udp%3A%2F%2Ftracker.opentrackr.org%3A1337%2Fannounce&tr=udp%3A%2F%2Ftracker.torrent.eu.org%3A451%2Fannounce&tr=udp%3A%2F%2Fexplodie.org%3A6969%2Fannounce&tr=udp%3A%2F%2Ftracker.birkenwald.de%3A6969%2Fannounce&tr=udp%3A%2F%2Ftracker.moeking.me%3A6969%2Fannounce&tr=udp%3A%2F%2Fipv4.tracker.harry.lu%3A80%2Fannounce&tr=udp%3A%2F%2Fodd-hd.fr%3A6969%2Fannounce&tr=udp%3A%2F%2Ftracker.jamesthebard.net%3A6969%2Fannounce&tr=udp%3A%2F%2Ftracker.picotorrent.one%3A6969%2Fannounce&tr=udp%3A%2F%2Ftracker.0x7c0.com%3A6969%2Fannounce&tr=udp%3A%2F%2Foh.fuuuuuck.com%3A6969%2Fannounce&tr=udp%3A%2F%2Ftracker.opentrackr.org%3A1337%2Fannounce&tr=http%3A%2F%2Ftracker.openbittorrent.com%3A80%2Fannounce&tr=udp%3A%2F%2Fopentracker.i2p.rocks%3A6969%2Fannounce&tr=udp%3A%2F%2Ftracker.internetwarriors.net%3A1337%2Fannounce&tr=udp%3A%2F%2Ftracker.leechers-paradise.org%3A6969%2Fannounce&tr=udp%3A%2F%2Fcoppersurfer.tk%3A6969%2Fannounce&tr=udp%3A%2F%2Ftracker.zer0day.to%3A1337%2Fannounce"

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

# Download loop
while handle.status().state != lt.torrent_status.seeding:
    s = handle.status()
    print(f"Progress: {s.progress * 100:.2f}%, "
          f"Download: {s.download_rate / 1000:.2f} kB/s, "
          f"Upload: {s.upload_rate / 1000:.2f} kB/s, "
          f"Peers: {s.num_peers}")
    time.sleep(5)

print("Download complete!")
