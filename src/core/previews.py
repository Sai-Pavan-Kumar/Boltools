"""Preview tools: results to look at first, saved only when the user asks.

A tool marked "output": "preview" in the tools list runs into a private folder
under ~/.boltools/previews. The app shows the images from there; Save copies
them to the user's folder. Reads and copies are limited to that folder, so the
screen can never be used to read other files on the PC.
"""

import base64
import os
import shutil
import time
import uuid
from typing import Dict, List, Optional

PREVIEW_ROOT = os.path.join(os.path.expanduser("~"), ".boltools", "previews")
KEEP_SECONDS = 24 * 60 * 60
IMAGE_TYPES = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}


def _inside_root(path: str) -> bool:
    root = os.path.realpath(PREVIEW_ROOT)
    target = os.path.realpath(path)
    return os.path.commonpath([root, target]) == root and target != root


def _prune_old() -> None:
    """Previews nobody saved are only a cache; yesterday's are removed."""
    if not os.path.isdir(PREVIEW_ROOT):
        return
    cutoff = time.time() - KEEP_SECONDS
    for name in os.listdir(PREVIEW_ROOT):
        folder = os.path.join(PREVIEW_ROOT, name)
        try:
            if os.path.isdir(folder) and os.path.getmtime(folder) < cutoff:
                shutil.rmtree(folder, ignore_errors=True)
        except OSError:
            continue


def new_preview_dir() -> str:
    _prune_old()
    folder = os.path.join(PREVIEW_ROOT, uuid.uuid4().hex)
    os.makedirs(folder, exist_ok=True)
    return folder


def read_image(path: str) -> Optional[str]:
    """A data URL for one preview image, or None for anything outside the preview folder."""
    mime = IMAGE_TYPES.get(os.path.splitext(str(path))[1].lower())
    if not mime or not _inside_root(path) or not os.path.isfile(path):
        return None
    with open(path, "rb") as f:
        return f"data:{mime};base64,{base64.b64encode(f.read()).decode('ascii')}"


def _unique_path(folder: str, name: str) -> str:
    stem, ext = os.path.splitext(name)
    candidate, counter = os.path.join(folder, name), 1
    while os.path.exists(candidate):
        candidate = os.path.join(folder, f"{stem} ({counter}){ext}")
        counter += 1
    return candidate


def save(paths: List[str], dest_dir: str) -> Dict[str, object]:
    """Copies previews to dest_dir without overwriting anything."""
    if not dest_dir or not os.path.isdir(dest_dir):
        return {"saved": [], "error": "Choose a folder that exists to save the previews."}
    saved = []
    for path in paths or []:
        if _inside_root(path) and os.path.isfile(path):
            target = _unique_path(dest_dir, os.path.basename(path))
            shutil.copyfile(path, target)
            saved.append(target)
    return {"saved": saved, "error": None if saved else "Nothing to save."}
