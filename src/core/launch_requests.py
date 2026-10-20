"""Right-click requests ("open this tool with these files") on their way to the UI.

The first request waits until the page asks for it (the catalog must be loaded
before a tool can open). Later ones come from a second process through
single_instance and are pushed straight to the open window.
"""

import os
import re
from typing import Dict, Optional

from src.core.ui_dispatcher import ui_dispatcher

_TOOL_ID = re.compile(r"^[a-z0-9_]{1,64}$")


def _clean(request: Optional[Dict]) -> Optional[Dict]:
    if not request or not _TOOL_ID.match(str(request.get("tool_id", ""))):
        return None
    files = [os.path.abspath(f) for f in request.get("files", []) if isinstance(f, str) and os.path.isfile(f)]
    return {"tool_id": request["tool_id"], "files": files} if files else None


class LaunchRequests:
    def __init__(self):
        self._pending: Optional[Dict] = None
        self._window = None

    def set_window(self, window) -> None:
        self._window = window

    def set_initial(self, request: Optional[Dict]) -> None:
        self._pending = _clean(request)

    def take_initial(self) -> Optional[Dict]:
        request, self._pending = self._pending, None
        return request

    def deliver(self, request: Dict) -> None:
        """A second launch handed this over: show the window, then open the tool."""
        if self._window:
            try:
                self._window.restore()
                self._window.show()
            except Exception:
                pass
        cleaned = _clean(request)
        if cleaned:
            ui_dispatcher.send("handleOpenRequest", cleaned)


launch_requests = LaunchRequests()
