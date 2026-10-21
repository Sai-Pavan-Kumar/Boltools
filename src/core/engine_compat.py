"""Stops a run before it starts when the installed engine is too old for this app.

Engines before 1.1.0 read their job until stdin closes, but the runner keeps
stdin open for Cancel, so they wait forever at "Initializing engine...". The
tools list marks such cut-offs with "min_engine_version"; below it, the user
gets a clear "update first" message instead of a frozen run.
"""

import os
import shutil
from typing import Optional

from src._build import IS_RELEASE
from src.core.tool_store import is_newer_version, tool_store_service

UPDATE_FIRST_MESSAGE = "This tool has a free update that it needs before it can run. Open Tool Store and press Update."
# Starts with a fixed marker so the tool screen can offer the download button instead of a plain error.
MEDIA_PACK_MESSAGE = "MEDIA_PACK_NEEDED: This tool needs the media pack. Download it once from Boltools and the tool is ready."


def run_blocker(tool_id: str) -> Optional[str]:
    """A message for the user when this tool must be updated first, else None."""
    meta = tool_store_service.get_tool_meta(tool_id) or {}
    # The media pack check also runs in dev: it is about this PC, not the engine copy.
    if "media_engine" in (meta.get("needs") or []) and not shutil.which("ffmpeg"):
        return MEDIA_PACK_MESSAGE
    # Dev runs use the engine straight from the repo, never the installed copy.
    if not IS_RELEASE and os.environ.get("BOLTOOLS_DEV") == "1":
        return None
    minimum = meta.get("min_engine_version")
    if not minimum:
        return None
    folder = meta.get("engine_folder") or tool_id
    pointer = tool_store_service.get_active_pointer(tool_id) or tool_store_service.get_active_pointer(folder)
    installed = (pointer or {}).get("version")
    if installed and is_newer_version(minimum, installed):
        return UPDATE_FIRST_MESSAGE
    return None
