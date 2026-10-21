"""Builds the media pack zip from one pinned BtbN FFmpeg release zip.

Usage:
  python tools_dev/build_media_pack.py <btbn.zip> <checksums.sha256> <out_dir>

The BtbN zip is checked against its published checksums first. Only ffmpeg.exe,
the DLLs it loads and the licence go into the pack: ffplay, ffprobe, headers and
docs would add ~20 MB that no engine uses. pack.json lists a sha256 for every
file, so the app can prove each unpacked file before the first run.
"""

import hashlib
import json
import os
import re
import sys
import zipfile

KEEP = re.compile(r"^(ffmpeg\.exe|[a-z]+-\d+\.dll|LICENSE\.txt)$")
VERSION = re.compile(rb"\bn(\d+\.\d+\.\d+)-\d+-g[0-9a-f]{7,}")


def sha256_of(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def check_source(zip_path: str, checksums_path: str) -> None:
    name = os.path.basename(zip_path)
    with open(checksums_path, encoding="utf-8") as f:
        expected = next((line.split()[0] for line in f if line.strip().endswith(name)), None)
    if not expected:
        sys.exit(f"{name} is not listed in {checksums_path}")
    with open(zip_path, "rb") as f:
        if sha256_of(f.read()) != expected:
            sys.exit(f"{name} does not match its published checksum")


def pick_files(src: zipfile.ZipFile) -> dict:
    picked = {}
    for info in src.infolist():
        base = info.filename.rsplit("/", 1)[-1]
        in_bin = "/bin/" in info.filename
        if KEEP.match(base) and (in_bin or base == "LICENSE.txt"):
            picked[base] = src.read(info)
    if "ffmpeg.exe" not in picked or "LICENSE.txt" not in picked:
        sys.exit("ffmpeg.exe or LICENSE.txt missing from the source zip")
    return picked


def main() -> None:
    zip_path, checksums_path, out_dir = sys.argv[1:4]
    check_source(zip_path, checksums_path)
    with zipfile.ZipFile(zip_path) as src:
        files = pick_files(src)

    # The build's own version string (stored in the libraries) names the pack, so it can never be mislabelled.
    match = next((m for data in files.values() for m in [VERSION.search(data)] if m), None)
    version = match.group(1).decode() if match else sys.exit("Could not read the FFmpeg version from the build")
    pack = {"id": "media_pack", "version": version, "entry": "ffmpeg.exe",
            "source": os.path.basename(zip_path),
            "files": {name: sha256_of(data) for name, data in sorted(files.items())}}

    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"media-pack-{version}.zip")
    with zipfile.ZipFile(out_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as out:
        out.writestr("pack.json", json.dumps(pack, indent=2))
        for name, data in sorted(files.items()):
            out.writestr(name, data)

    with open(out_path, "rb") as f:
        packed = f.read()
    print(json.dumps({"version": version, "path": out_path, "size_bytes": len(packed),
                      "sha256": sha256_of(packed), "unpacked_bytes": sum(len(d) for d in files.values())}, indent=2))


if __name__ == "__main__":
    main()
