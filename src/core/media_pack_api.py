"""Bridge calls for the media pack, mixed into DesktopBridge (kept apart: that file is over its size limit).

install runs on its own thread and reports through window.onMediaPackProgress,
so the 75 MB download never blocks the UI or a bridge timeout.
"""

import shutil
import threading
from typing import Any, Dict

from src.core import media_pack
from src.core.tool_store import tool_store_service
from src.core.ui_dispatcher import ui_dispatcher


class MediaPackApi:
    _pack_lock = threading.Lock()
    _pack_cancel = threading.Event()
    _pack_busy = False

    def get_media_pack_status(self) -> Dict[str, Any]:
        spec = media_pack.valid_spec((tool_store_service.cached_manifest or {}).get("media_pack"))
        installed = media_pack.installed_version()
        return {
            "installed": bool(installed),
            "version": installed,
            # A user's own FFmpeg on PATH also lets the media tools run.
            "ready": bool(installed) or bool(shutil.which("ffmpeg")),
            "available": bool(spec),
            "size_bytes": spec["size_bytes"] if spec else 0,
            "busy": MediaPackApi._pack_busy,
        }

    def install_media_pack(self) -> bool:
        with MediaPackApi._pack_lock:
            if MediaPackApi._pack_busy:
                return False
            MediaPackApi._pack_busy = True
            MediaPackApi._pack_cancel.clear()
        spec = (tool_store_service.cached_manifest or {}).get("media_pack")
        threading.Thread(target=self._install_media_pack, args=(spec,), daemon=True, name="media-pack").start()
        return True

    def cancel_media_pack(self) -> bool:
        MediaPackApi._pack_cancel.set()
        return MediaPackApi._pack_busy

    def _install_media_pack(self, spec: Any) -> None:
        def report(percent: float, status: str) -> None:
            ui_dispatcher.send("onMediaPackProgress", {"percent": round(percent, 1), "status": status})

        try:
            version = media_pack.install(spec, report, MediaPackApi._pack_cancel)
            tool_store_service.invalidate_cache()  # Tool Store cards now show the engine as on this PC
            ui_dispatcher.send("onMediaPackDone", {"ok": True, "version": version})
        except media_pack.PackError as err:
            ui_dispatcher.send("onMediaPackDone", {"ok": False, "error": str(err)})
        except Exception:
            ui_dispatcher.send("onMediaPackDone", {"ok": False, "error": "The media pack could not be installed. Please try again."})
        finally:
            MediaPackApi._pack_busy = False
