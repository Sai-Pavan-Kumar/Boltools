"""The media pack: the video/audio engine (FFmpeg), downloaded once on first use.

It never ships in the installer: 7 of 10 tools don't need it, and it is 75 MB.
The signed tools list carries its url, size and sha256 under "media_pack", so a
swapped file fails the check before anything is unpacked. Inside the zip,
pack.json lists a sha256 for every file, and only those exact flat names are
accepted.

Engines find the media engine through PATH. Putting the pack folder first on
this process's PATH means every engine, quick action and the Tool Store check
pick it up with no engine change, and a user's own FFmpeg still works as before.
"""

import hashlib
import json
import os
import re
import shutil
import threading
import urllib.request
import uuid
import zipfile
from typing import Any, Callable, Dict, Optional

from src._build import IS_RELEASE

MEDIA_DIR = os.path.join(os.path.expanduser("~"), ".boltools", "media")
POINTER_FILE = "current.json"
ENTRY = "ffmpeg.exe"
FILE_NAME = re.compile(r"^[A-Za-z0-9._-]{1,64}$")
VERSION = re.compile(r"^\d+(\.\d+){1,3}$")
MAX_UNPACKED_BYTES = 400 * 1024 * 1024
CHUNK = 256 * 1024
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Boltools"

Progress = Callable[[float, str], None]


class PackError(Exception):
    """A failure the user can read as is."""


def _sha256_file(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(CHUNK), b""):
            digest.update(block)
    return digest.hexdigest()


def valid_spec(spec: Any) -> Optional[Dict[str, Any]]:
    """The tools list entry, or None when it is missing or malformed."""
    if not isinstance(spec, dict):
        return None
    url, sha, version, size = spec.get("url"), spec.get("sha256"), spec.get("version"), spec.get("size_bytes")
    # Dev builds may test against a pack served from this PC; release builds never accept plain http.
    local_test = not IS_RELEASE and os.environ.get("BOLTOOLS_DEV") == "1" and str(url).startswith("http://127.0.0.1:")
    if not (isinstance(url, str) and (url.startswith("https://") or local_test)):
        return None
    if not (isinstance(sha, str) and re.fullmatch(r"[0-9a-f]{64}", sha)):
        return None
    if not (isinstance(version, str) and VERSION.match(version) and isinstance(size, int) and size > 0):
        return None
    return spec


def active_dir(media_dir: str = MEDIA_DIR) -> Optional[str]:
    """Folder of the installed pack, or None. A folder missing its engine counts as not installed."""
    try:
        with open(os.path.join(media_dir, POINTER_FILE), encoding="utf-8") as f:
            version = json.load(f).get("version", "")
    except (OSError, ValueError, AttributeError):
        return None
    if not VERSION.match(str(version)):
        return None
    folder = os.path.join(media_dir, version)
    return folder if os.path.isfile(os.path.join(folder, ENTRY)) else None


def installed_version(media_dir: str = MEDIA_DIR) -> Optional[str]:
    folder = active_dir(media_dir)
    return os.path.basename(folder) if folder else None


def activate(media_dir: str = MEDIA_DIR) -> bool:
    """Puts the installed pack first on PATH for this process and every engine it starts."""
    folder = active_dir(media_dir)
    if not folder:
        return False
    parts = [p for p in os.environ.get("PATH", "").split(os.pathsep) if p and os.path.normcase(p) != os.path.normcase(folder)]
    os.environ["PATH"] = os.pathsep.join([folder] + parts)
    return True


def _download(spec: Dict[str, Any], dest: str, on_progress: Progress, cancel: threading.Event) -> None:
    total = spec["size_bytes"]
    digest, done = hashlib.sha256(), 0
    request = urllib.request.Request(spec["url"], headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=30) as resp, open(dest, "wb") as out:
            while True:
                if cancel.is_set():
                    raise PackError("Download cancelled.")
                block = resp.read(CHUNK)
                if not block:
                    break
                done += len(block)
                if done > total:
                    raise PackError("The download was bigger than expected, so it was stopped.")
                digest.update(block)
                out.write(block)
                on_progress(done * 90.0 / total, "Downloading")
    except PackError:
        raise
    except OSError as err:
        raise PackError("Could not download the media pack. Check your internet and try again.") from err
    if done != total or digest.hexdigest() != spec["sha256"]:
        raise PackError("The downloaded file did not pass the safety check, so it was not used.")


def _read_pack_list(zf: zipfile.ZipFile, version: str) -> Dict[str, str]:
    try:
        pack = json.loads(zf.read("pack.json"))
    except (KeyError, ValueError) as err:
        raise PackError("The media pack is damaged.") from err
    files = pack.get("files") if isinstance(pack, dict) else None
    if pack.get("version") != version or not isinstance(files, dict) or ENTRY not in files:
        raise PackError("The media pack does not match the tools list.")
    for name, sha in files.items():
        if not FILE_NAME.match(name) or not re.fullmatch(r"[0-9a-f]{64}", str(sha)):
            raise PackError("The media pack is damaged.")
    return files


def _unpack(zip_path: str, staging: str, version: str, on_progress: Progress) -> None:
    with zipfile.ZipFile(zip_path) as zf:
        files = _read_pack_list(zf, version)
        names = {info.filename for info in zf.infolist()}
        if names != set(files) | {"pack.json"}:
            raise PackError("The media pack has unexpected or missing files.")
        os.makedirs(staging)
        written = 0
        for index, (name, expected) in enumerate(sorted(files.items())):
            digest = hashlib.sha256()
            with zf.open(name) as src, open(os.path.join(staging, name), "wb") as dst:
                for block in iter(lambda: src.read(CHUNK), b""):
                    written += len(block)
                    if written > MAX_UNPACKED_BYTES:
                        raise PackError("The media pack is damaged.")
                    digest.update(block)
                    dst.write(block)
            if digest.hexdigest() != expected:
                raise PackError("A file in the media pack did not pass the safety check.")
            on_progress(90.0 + 9.0 * (index + 1) / len(files), "Checking files")


def _write_pointer(media_dir: str, version: str) -> None:
    tmp = os.path.join(media_dir, f".{POINTER_FILE}.{uuid.uuid4().hex}")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"version": version}, f)
    os.replace(tmp, os.path.join(media_dir, POINTER_FILE))


def install(spec: Any, on_progress: Progress, cancel: threading.Event, media_dir: str = MEDIA_DIR) -> str:
    """Downloads, checks and unpacks the pack, then switches to it. Returns the version.

    Work happens in temporary names; the live pack only changes in the last two
    renames, so a cut-off download or a crash never leaves a half pack in use.
    """
    spec = valid_spec(spec)
    if not spec:
        raise PackError("The media pack is not available yet. Try again after the next tools list update.")
    version = spec["version"]
    if installed_version(media_dir) == version:
        return version
    os.makedirs(media_dir, exist_ok=True)
    tag = uuid.uuid4().hex
    zip_path = os.path.join(media_dir, f".download-{tag}.zip")
    staging = os.path.join(media_dir, f".staging-{tag}")
    target = os.path.join(media_dir, version)
    try:
        _download(spec, zip_path, on_progress, cancel)
        _unpack(zip_path, staging, version, on_progress)
        if os.path.isdir(target):
            shutil.rmtree(target)  # a folder with this version but no valid pointer is a broken earlier try
        os.replace(staging, target)
        _write_pointer(media_dir, version)
    finally:
        if os.path.exists(zip_path):
            os.remove(zip_path)
        shutil.rmtree(staging, ignore_errors=True)
    activate(media_dir)
    on_progress(100.0, "Ready")
    return version
