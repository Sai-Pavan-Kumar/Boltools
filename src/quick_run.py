"""Right-click quick actions: do the job right where the user is.

No main window opens. A small card appears in the corner, the engine runs with
the action's fixed settings, and the result is saved next to the original file
(engines never overwrite). The card closes itself shortly after success.
"""

import ctypes
import json
import os
import threading
from typing import Any, Dict, List, Tuple

import webview

from src.core.engine_compat import run_blocker
from src.core.output_stats import with_file_sizes
from src.core.ui_port import free_port
from src.core.tool_store import tool_store_service
from src.engine_runner import engine_runner

CARD_WIDTH = 380
CARD_HEIGHT = 224
SCREEN_MARGIN = 16


def _card_position():
    """Bottom-right of the work area (above the taskbar), in logical pixels."""
    try:
        rect = (ctypes.c_long * 4)()
        ctypes.windll.user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(rect), 0)  # SPI_GETWORKAREA
        scale = ctypes.windll.user32.GetDpiForSystem() / 96.0
        right, bottom = rect[2] / scale, rect[3] / scale
        return int(right - CARD_WIDTH - SCREEN_MARGIN), int(bottom - CARD_HEIGHT - SCREEN_MARGIN)
    except Exception:
        return None, None


class QuickCardApi:
    """Called from ui/js/quick.js."""

    def __init__(self, bridge):
        self._bridge = bridge
        self._window = None

    def show_file(self, path: str):
        self._bridge.reveal_file(path)
        self.close()

    def close(self):
        if self._window:
            self._window.destroy()

    def cancel_and_close(self):
        engine_runner.cancel_active()
        self.close()


class CardChannel:
    """Messages for the card. The engine starts before the card has loaded (WebView2
    needs ~2 s to open), so early messages wait here and are replayed on load."""

    def __init__(self, window):
        self._window = window
        self._lock = threading.Lock()
        self._waiting: List[Tuple[str, Dict[str, Any]]] = []
        self._ready = False

    def send(self, method: str, payload: Dict[str, Any]):
        with self._lock:
            if not self._ready:
                self._waiting.append((method, payload))
                return
        self._deliver(method, payload)

    def page_loaded(self):
        with self._lock:
            self._ready = True
            waiting, self._waiting = self._waiting, []
        for method, payload in waiting:
            self._deliver(method, payload)

    def _deliver(self, method: str, payload: Dict[str, Any]):
        try:
            self._window.evaluate_js(f"window.Quick && window.Quick.{method}({json.dumps(payload)})")
        except Exception:
            pass


def _start_engine(card: CardChannel, tool: Dict, action: Dict, files: List[str]):
    card.send("start", {"label": action["label"], "files": files})
    blocker = run_blocker(tool["id"])
    if blocker:
        card.send("failed", {"message": blocker})
        return
    target = tool_store_service.get_engine_target(tool["id"]) or ""
    if not target or not os.path.exists(target):
        card.send("failed", {"message": "This tool is not installed yet. Open Boltools to install it."})
        return

    def on_complete(outputs: Any):
        stats = None
        if isinstance(outputs, dict) and "outputs" in outputs:
            stats, outputs = outputs.get("stats"), outputs.get("outputs")
        output_list = outputs if isinstance(outputs, list) else [outputs]
        card.send("done", {"outputs": output_list, "stats": with_file_sizes(stats, files, output_list)})

    def on_error(err: Any):
        card.send("failed", {"message": err.get("message") if isinstance(err, dict) else str(err)})

    engine_runner.run_engine(
        tool_id=tool["id"],
        engine_type=tool.get("engine_type", "python"),
        executable_target=target,
        input_files=files,
        options=dict(action.get("options") or {}),
        output_dir=os.path.dirname(os.path.abspath(files[0])),
        on_progress=lambda pct, status: card.send("progress", {"percent": pct, "status": status}),
        on_log=lambda _msg: None,
        on_complete=on_complete,
        on_error=on_error,
    )


def run_quick(tool: Dict, action: Dict, files: List[str], root_dir: str, bridge, icon_path=None):
    api = QuickCardApi(bridge)
    x, y = _card_position()
    window = webview.create_window(
        title="Boltools",
        url=os.path.join(root_dir, "ui", "quick.html"),
        width=CARD_WIDTH,
        height=CARD_HEIGHT,
        x=x,
        y=y,
        resizable=False,
        frameless=True,
        easy_drag=False,
        on_top=True,
        js_api=api,
        text_select=False,
    )
    api._window = window
    card = CardChannel(window)
    window.events.loaded += card.page_loaded
    _start_engine(card, tool, action, files)

    storage_dir = os.path.join(os.path.expanduser("~"), ".boltools", "quick_webview2")
    os.makedirs(storage_dir, exist_ok=True)
    # Its own port: on the shared one it could load the open main window's (maybe older) files.
    webview.start(gui="edgechromium", icon=icon_path, private_mode=False, storage_path=storage_dir,
                  http_port=free_port())
