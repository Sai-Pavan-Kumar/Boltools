"""Small preview images for the file grid.

The WebView may not read local files (CSP allows only 'self' and data: images),
so the shell decodes each picked image once and hands back a tiny JPEG data URL
plus the facts the grid shows (size on disk, pixel dimensions).
"""

import base64
import io
import os
from typing import Any, Dict, List

from PIL import Image, ImageOps

THUMB_EDGE_PX = 240
THUMB_QUALITY = 72
MAX_FILES_PER_CALL = 60
MAX_SOURCE_BYTES = 200 * 1024 * 1024


def _thumbnail(path: str) -> Dict[str, Any]:
    size_bytes = os.path.getsize(path)
    if size_bytes > MAX_SOURCE_BYTES:
        return {"file": path, "size_bytes": size_bytes}
    with Image.open(path) as img:
        img = ImageOps.exif_transpose(img)
        width, height = img.size
        img.thumbnail((THUMB_EDGE_PX, THUMB_EDGE_PX), Image.Resampling.LANCZOS)
        buffer = io.BytesIO()
        img.convert("RGB").save(buffer, format="JPEG", quality=THUMB_QUALITY)
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return {
        "file": path,
        "size_bytes": size_bytes,
        "width": width,
        "height": height,
        "thumb": f"data:image/jpeg;base64,{encoded}",
    }


def make_thumbnails(paths: List[str]) -> List[Dict[str, Any]]:
    results = []
    for path in list(paths or [])[:MAX_FILES_PER_CALL]:
        if not isinstance(path, str) or not os.path.isfile(path):
            continue
        try:
            results.append(_thumbnail(path))
        except Exception:
            # Unreadable images still get a tile; the engine reports the real error later.
            results.append({"file": path, "size_bytes": os.path.getsize(path), "unreadable": True})
    return results
