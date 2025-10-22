import libtorrent as lt
import time


# Replace with your magnet link
magnet_link = "magnet:?xt=urn:btih:CA10982EF0698923A008B60F8CC28EAEF5E8881D&dn=The+Amazing+SpiderMan+%282012%29+720p+BrRip+x264+-+YIFY&tr=udp%3A%2F%2Ftracker.yify-torrents.com%2Fannounce&tr=udp%3A%2F%2Ftwig.gs%3A6969&tr=udp%3A%2F%2Ftracker.publichd.eu%2Fannounce&tr=http%3A%2F%2Ftracker.publichd.eu%2Fannounce&tr=udp%3A%2F%2Ftracker.police.maori.nz%2Fannounce&tr=udp%3A%2F%2Ftracker.1337x.org%3A80%2Fannounce&tr=udp%3A%2F%2Fexodus.desync.com%3A6969&tr=udp%3A%2F%2Ftracker.istole.it%3A80&tr=udp%3A%2F%2Ftracker.ccc.de%3A80%2Fannounce&tr=http%3A%2F%2Ftracker.yify-torrents.com%2Fannounce&tr=udp%3A%2F%2F9.rarbg.com%3A2710%2Fannounce&tr=http%3A%2F%2Ffr33dom.h33t.com%3A3310%2Fannounce&tr=http%3A%2F%2Ftracker.ex.ua%2Fannounce&tr=http%3A%2F%2Fcoppersurfer.tk%3A6969%2Fannounce&tr=udp%3A%2F%2Ftracker.opentrackr.org%3A1337%2Fannounce&tr=http%3A%2F%2Ftracker.openbittorrent.com%3A80%2Fannounce&tr=udp%3A%2F%2Fopentracker.i2p.rocks%3A6969%2Fannounce&tr=udp%3A%2F%2Ftracker.internetwarriors.net%3A1337%2Fannounce&tr=udp%3A%2F%2Ftracker.leechers-paradise.org%3A6969%2Fannounce&tr=udp%3A%2F%2Fcoppersurfer.tk%3A6969%2Fannounce&tr=udp%3A%2F%2Ftracker.zer0day.to%3A1337%2Fannounce"

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
