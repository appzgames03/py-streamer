import os
import zipfile

folder_path = ""

def zip_folder_with_progress(folder_path):
    if not os.path.isdir(folder_path):
        print("Error: not a directory")
        return

    folder_path = os.path.abspath(folder_path)
    parent = os.path.dirname(folder_path)
    name = os.path.basename(folder_path.rstrip(os.sep))
    zip_path = os.path.join(parent, f"{name}.zip")

    files = []
    for root, _, filenames in os.walk(folder_path):
        for f in filenames:
            files.append(os.path.join(root, f))

    total = len(files)
    print(f"Zipping folder: {folder_path}")
    print(f"Output ZIP:    {zip_path}")
    print(f"Total files:   {total}")

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_STORED) as zipf:
        for i, file in enumerate(files, start=1):
            arcname = os.path.relpath(file, parent)
            zipf.write(file, arcname)

            percent = int((i / total) * 100) if total else 100
            print(f"[{percent:3}%] {i}/{total} - {arcname}")

    print("ZIP completed successfully.")

if __name__ == "__main__":
    zip_folder_with_progress(folder_path)
