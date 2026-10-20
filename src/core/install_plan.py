"""What installing a tool actually puts on this PC, shown before the user installs.

Parts come from the tools list: the tool's own engine (size_bytes) and shared
parts it needs ("needs": ["media_engine"]). Shared parts already on the PC are
reported as such, so nothing is downloaded twice. Names stay plain: no library
or program names reach the screen.
"""

import os
import shutil
from typing import Dict, List

# Shared parts tools can rely on. "built_in" ships inside the Boltools app.
SHARED_PARTS = {
    "picture_pdf_core": {"name": "Picture and PDF engine", "built_in": True},
    "media_engine": {
        "name": "Media engine",
        "built_in": False,
        "missing_hint": "Not on this PC yet. Install it once with: winget install Gyan.FFmpeg",
    },
}


def _media_engine_present() -> bool:
    found = shutil.which("ffmpeg")
    if not found:
        return False
    try:
        if os.path.islink(found):
            target = os.readlink(found)
            target = target[4:] if target.startswith("\\\\?\\") else target
            return os.path.isfile(target)
    except OSError:
        return False
    return os.path.isfile(found)


PRESENCE_CHECKS = {"media_engine": _media_engine_present}


def plan_for(tool: Dict, engine_on_pc: bool = False) -> Dict:
    """{download_bytes, parts: [{name, bytes?, status: download|present|missing|built_in, hint?}]}

    engine_on_pc: another installed tool already brought this engine (Merge and Split share one).
    """
    engine_bytes = int(tool.get("size_bytes") or 0)
    if engine_on_pc:
        parts: List[Dict] = [{"name": "Tool engine", "bytes": engine_bytes, "status": "present"}]
        engine_bytes = 0
    else:
        parts = [{"name": "Tool engine", "bytes": engine_bytes, "status": "download"}]
    for key in tool.get("needs") or []:
        spec = SHARED_PARTS.get(key)
        if not spec:
            continue
        if spec["built_in"]:
            parts.append({"name": spec["name"], "status": "built_in"})
        elif PRESENCE_CHECKS.get(key, lambda: False)():
            parts.append({"name": spec["name"], "status": "present"})
        else:
            parts.append({"name": spec["name"], "status": "missing", "hint": spec.get("missing_hint", "")})
    return {"download_bytes": engine_bytes, "parts": parts}
