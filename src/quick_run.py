"""Right-click quick actions: do the job right where the user is.

No main window opens. A small card appears in the corner, the engine runs with
the action's fixed settings, and the result is saved next to the original file
(engines never overwrite). The card closes itself shortly after success.
"""

import ctypes
import json
import os
from typing import Any, Dict, List

import webview

from src.core.output_stats import with_file_sizes
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


def _push(window, method: str, payload: Dict[str, Any]):
    try:
        window.evaluate_js(f"window.Quick && window.Quick.{method}({json.dumps(payload)})")
    except Exception:
        pass


def _start_engine(window, tool: Dict, action: Dict, files: List[str]):
    _push(window, "start", {"label": action["label"], "files": files})
    target = tool_store_service.get_engine_target(tool["id"]) or ""
    if not target or not os.path.exists(target):
        _push(window, "failed", {"message": "This tool is not installed yet. Open Boltools to install it."})
        return

    def on_complete(outputs: Any):
        stats = None
        if isinstance(outputs, dict) and "outputs" in outputs:
            stats, outputs = outputs.get("stats"), outputs.get("outputs")
        output_list = outputs if isinstance(outputs, list) else [outputs]
        _push(window, "done", {"outputs": output_list, "stats": with_file_sizes(stats, files, output_list)})

    def on_error(err: Any):
        _push(window, "failed", {"message": err.get("message") if isinstance(err, dict) else str(err)})

    engine_runner.run_engine(
        tool_id=tool["id"],
        engine_type=tool.get("engine_type", "python"),
        executable_target=target,
        input_files=files,
        options=dict(action.get("options") or {}),
        output_dir=os.path.dirname(os.path.abspath(files[0])),
        on_progress=lambda pct, status: _push(window, "progress", {"percent": pct, "status": status}),
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
    window.events.loaded += lambda: _start_engine(window, tool, action, files)

    storage_dir = os.path.join(os.path.expanduser("~"), ".boltools", "quick_webview2")
    os.makedirs(storage_dir, exist_ok=True)
    webview.start(gui="edgechromium", icon=icon_path, private_mode=False, storage_path=storage_dir)
