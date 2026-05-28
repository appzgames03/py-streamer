import argparse
import os
import subprocess
import time
import urllib.parse

import libtorrent as lt


DEFAULT_START_PORT = 6701
SAVE_PATH = "./downloads"
TORFILES_PATH = "./torfiles"


def parse_args():
    parser = argparse.ArgumentParser(
        description="Download a torrent from a magnet link or torrent-file URL using a shared port suffix argument."
    )
    parser.add_argument('link', help='Magnet link or HTTP(s) torrent file URL')
    parser.add_argument('--port', '-p', help='Last two digits of the start port (e.g. 01)', default=None)
    return parser.parse_args()


def build_start_port(port_suffix):
    if port_suffix is None:
        return DEFAULT_START_PORT

    prefix = str(DEFAULT_START_PORT)[:-2]
    suffix = str(port_suffix).zfill(2)
    return int(prefix + suffix)


def create_session(start_port):
    session = lt.session()
    session.listen_on(start_port, start_port + 50)
    return session


def download_torrent_file(torrent_link):
    os.makedirs(TORFILES_PATH, exist_ok=True)
    filename = urllib.parse.unquote(torrent_link.split('/')[-1])
    if not filename.lower().endswith('.torrent'):
        filename += '.torrent'

    target_path = os.path.join(TORFILES_PATH, filename)
    print(f"Downloading torrent file from {torrent_link} to {target_path}...")
    subprocess.run(['wget', torrent_link, '-O', target_path], check=True)
    print(f"Torrent file saved to {target_path}")
    return target_path


def run_download_loop(handle):
    while handle.status().state != lt.torrent_status.seeding:
        s = handle.status()
        print(
            f"Progress: {s.progress * 100:.2f}% | "
            f"Download: {s.download_rate / 1000:.2f} kB/s | "
            f"Upload: {s.upload_rate / 1000:.2f} kB/s | "
            f"Peers: {s.num_peers}"
        )
        time.sleep(1)


def mark_completed(torrent_name):
    marker = os.path.join("./completed", torrent_name + ".completed")
    os.makedirs(os.path.dirname(marker), exist_ok=True)
    open(marker, "w").close()
    print(f"\033[96mMarked completed\033[0m")


def run_magnet_mode(link, start_port):
    session = create_session(start_port)
    params = {
        'save_path': SAVE_PATH,
        'storage_mode': lt.storage_mode_t.storage_mode_sparse,
    }
    handle = lt.add_magnet_uri(session, link, params)

    print("Fetching metadata...")
    while not handle.has_metadata():
        time.sleep(1)
    print("Metadata retrieved, starting download...")

    info = handle.get_torrent_info()
    torrent_name = info.name()
    print("Starting download:", torrent_name)

    run_download_loop(handle)
    print(f"Download complete => \033[92m\033[1m{torrent_name}\033[0m")
    mark_completed(torrent_name)


def run_torrent_file_mode(link, start_port):
    torrent_file = download_torrent_file(link)
    os.makedirs(SAVE_PATH, exist_ok=True)
    session = create_session(start_port)

    info = lt.torrent_info(torrent_file)
    handle = session.add_torrent({'ti': info, 'save_path': SAVE_PATH})

    torrent_name = info.name()
    print("Starting download:", torrent_name)

    run_download_loop(handle)
    print(f"Download complete => \033[92m\033[1m{torrent_name}\033[0m")
    mark_completed(torrent_name)


def main():
    args = parse_args()
    start_port = build_start_port(args.port)
    link = args.link.strip()

    if link.startswith('magnet:'):
        run_magnet_mode(link, start_port)
    else:
        run_torrent_file_mode(link, start_port)


if __name__ == '__main__':
    main()
